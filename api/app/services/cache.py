"""Semantic cache shared by every API replica (section 3.3).

A new question is embedded once (the retriever needs that vector anyway) and compared
with the questions already answered. At or above CACHE_THRESHOLD cosine similarity the
stored response is returned and retrieval and generation are skipped.

Entries live under a namespace built from the published index generation, the
embedding model, the provider and the LLM model. A reindex publishes a new generation,
so old answers stop matching without the indexer ever touching Redis.

A hit also needs the same numbers in both questions. "2023 rules" and "2026 rules",
or "clause 1.21" and "clause 1.12", embed almost identically but have different answers.

What is never stored (answer.py decides): follow-ups, declined answers, fallbacks
and questions flagged as instruction-like.

Redis trouble is logged and treated as a miss; readiness already reports Redis.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import struct
import time
from typing import Any

from ..config import Settings
from ..schemas import AskResponse

log = logging.getLogger("rahbar.cache")


def _pack(vector: list[float]) -> bytes:
    return struct.pack(f"<{len(vector)}f", *vector)


def _unpack(blob: bytes) -> list[float]:
    return list(struct.unpack(f"<{len(blob) // 4}f", blob))


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else -1.0


def numbers(question: str) -> list[str]:
    """Years, clause numbers and amounts in a question, in order."""
    return re.findall(r"\d+(?:\.\d+)*", question)


def intent(question: str) -> tuple[bool, tuple[tuple[str, str], ...]]:
    """Protect direction-sensitive policies that embeddings often conflate.

    A conservative mismatch costs a cache miss, never a different policy answer.
    Numbers protect versions/clauses; this protects repeat versus take and which
    component was passed/failed. It is a guard, not a semantic correctness proof.
    """
    text = question.casefold()
    outcomes = re.findall(
        r"\b(fail|pass)(?:ed|ing|es)?\s+(?:(?:its|the|associated)\s+)*(theory|lab)\b",
        text,
    )
    return bool(re.search(r"\brepeat(?:ing|ed|s)?\b", text)), tuple(sorted(outcomes))


def namespace(generation: str, settings: Settings) -> str:
    parts = (
        f"v2|{generation}|{settings.embed_model}|{settings.llm_provider}|{settings.llm_model}"
        f"|{settings.relevance_floor}|{settings.temperature}|{settings.top_k}"
    )
    return "rahbar:cache:" + hashlib.sha256(parts.encode()).hexdigest()[:16]


class SemanticCache:
    def __init__(self, settings: Settings, client: Any = None) -> None:
        self.settings = settings
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            import redis

            self._client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
        return self._client

    def lookup(
        self, generation: str, vector: list[float], question: str
    ) -> tuple[AskResponse, float] | None:
        ns = namespace(generation, self.settings)
        try:
            vectors = self.client.hgetall(ns + ":vec")
            scored = sorted(
                ((cosine(vector, _unpack(blob)), key) for key, blob in vectors.items()),
                reverse=True,
            )
            for score, key in scored:
                if score < self.settings.cache_threshold:
                    return None
                raw = self.client.hget(ns + ":resp", key)
                if raw is None:
                    continue
                entry = json.loads(raw)
                if time.time() - entry.get("stored", 0) >= self.settings.cache_ttl:
                    continue
                if numbers(entry.get("question", "")) != numbers(question):
                    continue
                if intent(entry.get("question", "")) != intent(question):
                    continue
                return AskResponse.model_validate(entry["response"]), score
            return None
        except Exception as exc:  # cache is an optimisation, never a reason to fail
            log.warning("cache lookup failed: %s", exc)
            return None

    def store(
        self, generation: str, vector: list[float], question: str, response: AskResponse
    ) -> None:
        ns = namespace(generation, self.settings)
        key = hashlib.sha256(" ".join(question.lower().split()).encode()).hexdigest()[:24]
        entry = {"question": question, "stored": time.time(), "response": response.model_dump()}
        try:
            if self.client.hlen(ns + ":vec") >= self.settings.cache_max_entries:
                self._evict_oldest(ns)
            pipe = self.client.pipeline()
            pipe.hset(ns + ":vec", key, _pack(vector))
            pipe.hset(ns + ":resp", key, json.dumps(entry))
            pipe.expire(ns + ":vec", self.settings.cache_ttl)
            pipe.expire(ns + ":resp", self.settings.cache_ttl)
            pipe.execute()
        except Exception as exc:
            log.warning("cache store failed: %s", exc)

    def _evict_oldest(self, ns: str) -> None:
        entries = self.client.hgetall(ns + ":resp")
        if not entries:
            return
        oldest = min(entries, key=lambda k: json.loads(entries[k]).get("stored", 0))
        self.client.hdel(ns + ":vec", oldest)
        self.client.hdel(ns + ":resp", oldest)
