"""Turns a question into an AskResponse. This is where the query pipeline lives.

Order of the steps (sections 3.2 to 3.4):

1. flag an instruction-like question (guard.py)
2. build the retrieval query; a follow-up also carries the previous question
3. semantic cache lookup, first questions only (cache.py)
4. retrieve the top k passages
5. replace instruction-like sentences inside passages (guard.py)
6. relevance floor: below it, decline without calling the model
7. generate, validate the reply and its citations, retry once with the reason
8. on a second failure or an unreachable model, return a safe fallback
9. store the response in the cache when it is safe to reuse
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass

from ..config import Settings
from ..logjson import request_id_var
from ..providers.llm.base import LLMProvider
from ..providers.llm.prompt import ProviderOutputError, ProviderUnavailable
from ..retrieval.base import Retriever
from ..routes.metrics import ABSTENTIONS, CACHE, FALLBACKS, INJECTION, RETRIES, RETRIEVAL_SECONDS
from ..schemas import Answer, AskResponse, Passage, RetrievedRef, Turn
from . import citations, guard
from .cache import SemanticCache

log = logging.getLogger("rahbar.answer")

NOT_COVERED = (
    "The documents I can search do not cover this question, so I cannot answer it "
    "reliably. Please check with the relevant university office."
)
FALLBACK = (
    "I could not produce a verified answer from the documents just now. "
    "Please try again in a moment."
)


class RetrievalUnavailable(RuntimeError):
    """The vector store or the embedding model could not be reached."""


@dataclass
class Result:
    response: AskResponse
    cache: str  # "hit", "miss" or "bypass"


def _declined(text: str) -> Answer:
    return Answer(
        reasoning="declined",
        answer=text,
        citations=[],
        answered_from_context=False,
        confidence="low",
    )


def _generate(
    question: str,
    passages: list[Passage],
    history: Sequence[Turn],
    provider: LLMProvider,
) -> tuple[Answer, str | None]:
    """Up to two model calls. Returns the answer and a fallback reason, or None."""
    feedback: str | None = None
    for attempt in (1, 2):
        if attempt == 2:
            RETRIES.inc()
        try:
            answer = provider.generate(question, passages, history, feedback)
        except ProviderUnavailable as exc:
            log.warning("provider unavailable", extra={"error": str(exc)})
            return _declined(FALLBACK), "unavailable"
        except ProviderOutputError as exc:
            feedback = f"it was not valid JSON for the schema ({exc})."
            log.warning("invalid model output", extra={"attempt": attempt, "error": str(exc)})
            continue
        answer, problem = citations.check(answer, passages)
        if problem is None:
            if not answer.answered_from_context:
                # A model's false flag is not permission to expose uncited claims.
                return _declined(NOT_COVERED), None
            return answer, None
        feedback = problem
        log.warning("rejected citations", extra={"attempt": attempt, "error": problem})
    return _declined(FALLBACK), "invalid_output"


def _response(answer: Answer, passages: list[Passage], provider: LLMProvider) -> AskResponse:
    return AskResponse(
        request_id=request_id_var.get(),
        answer=answer.answer,
        citations=answer.citations,
        answered_from_context=answer.answered_from_context,
        confidence=answer.confidence,
        retrieved=[
            RetrievedRef(
                chunk_id=p.chunk_id, source=p.source, section=p.section, page=p.page, score=p.score
            )
            for p in passages
        ],
        provider=provider.name,
    )


def answer_question(
    question: str,
    retriever: Retriever,
    provider: LLMProvider,
    settings: Settings,
    history: Sequence[Turn] = (),
    cache: SemanticCache | None = None,
) -> Result:
    history = list(history)[-settings.max_history_turns :] if settings.max_history_turns else []
    flagged = guard.looks_like_injection(question)
    if flagged:
        INJECTION.labels(where="question").inc()
    query = f"{history[-1].question}\n{question}" if history else question

    vector: list[float] | None = None
    generation = ""
    cache_state = "bypass"
    query_context = getattr(retriever, "query_context", None)
    start = time.perf_counter()
    try:
        if cache is not None and not history and not flagged and query_context is not None:
            query_vector, generation = query_context(query)
            vector = query_vector
            found = cache.lookup(generation, query_vector, query)
            if found is not None:
                cached, similarity = found
                CACHE.labels(result="hit").inc()
                log.info("cache hit", extra={
                    "similarity": round(similarity, 4), "top_k": settings.top_k,
                    "chunk_ids": [r.chunk_id for r in cached.retrieved],
                    "scores": [r.score for r in cached.retrieved],
                    "answered_from_context": cached.answered_from_context,
                    "generation": generation,
                })
                response = cached.model_copy(update={"request_id": request_id_var.get()})
                return Result(response, "hit")
            CACHE.labels(result="miss").inc()
            cache_state = "miss"
        passages = retriever.retrieve(query, k=settings.top_k, vector=vector)
    except Exception as exc:
        log.error("retrieval failed", extra={"error": f"{type(exc).__name__}: {exc}"})
        raise RetrievalUnavailable("retrieval is unavailable") from exc
    finally:
        RETRIEVAL_SECONDS.observe(time.perf_counter() - start)

    passages, removed = guard.neutralise(passages)
    if removed:
        INJECTION.labels(where="passage").inc(removed)

    top = max((p.score for p in passages), default=0.0)
    fallback: str | None = None
    if not passages or top < settings.relevance_floor:
        answer = _declined(NOT_COVERED)
        ABSTENTIONS.labels(reason="below_floor").inc()
    else:
        answer, fallback = _generate(question, passages, history, provider)
        if fallback:
            FALLBACKS.labels(reason=fallback).inc()
        elif not answer.answered_from_context:
            ABSTENTIONS.labels(reason="model").inc()

    response = _response(answer, passages, provider)
    log.info(
        "answered",
        extra={
            "retriever": retriever.name,
            "provider": provider.name,
            "top_k": settings.top_k,
            "chunk_ids": [p.chunk_id for p in passages],
            "scores": [round(p.score, 4) for p in passages],
            "top_score": round(top, 4),
            "answered_from_context": answer.answered_from_context,
            "fallback": fallback,
            "follow_up": bool(history),
            "injection_flag": flagged,
            "passage_sentences_removed": removed,
            "cache": cache_state,
        },
    )
    if (
        cache is not None
        and cache_state == "miss"
        and vector is not None
        and answer.answered_from_context
        and fallback is None
        and not flagged
    ):
        cache.store(generation, vector, question, response)
    return Result(response, cache_state)
