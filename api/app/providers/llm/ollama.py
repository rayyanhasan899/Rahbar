"""Ollama provider: ollama-host or ollama-incluster (section 3.5).

POST {ollama_url}/api/chat with the Answer JSON schema as `format`, so the model is
constrained to the contract. Temperature comes from the ConfigMap; see ADR 0003.
"""

from __future__ import annotations

import time
from collections.abc import Sequence

import httpx

from ...config import Settings
from ...routes.metrics import GENERATION_SECONDS, TOKENS
from ...schemas import Answer, Passage, Turn
from .prompt import ANSWER_SCHEMA, ProviderUnavailable, build_messages, parse_answer


class OllamaProvider:
    name = "ollama"

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings  # ollama_url, llm_model, temperature
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(settings.llm_timeout, connect=5)
        )

    def generate(
        self,
        question: str,
        passages: list[Passage],
        history: Sequence[Turn] = (),
        feedback: str | None = None,
    ) -> Answer:
        body = {
            "model": self.settings.llm_model,
            "messages": build_messages(question, passages, history, feedback),
            "format": ANSWER_SCHEMA,
            "stream": False,
            "options": {"temperature": self.settings.temperature},
        }
        start = time.perf_counter()
        try:
            response = self.client.post(
                f"{self.settings.ollama_url.rstrip('/')}/api/chat", json=body
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderUnavailable(f"ollama: {type(exc).__name__}: {exc}") from exc
        finally:
            GENERATION_SECONDS.labels(provider=self.name).observe(time.perf_counter() - start)
        TOKENS.labels(kind="prompt").inc(int(data.get("prompt_eval_count") or 0))
        TOKENS.labels(kind="completion").inc(int(data.get("eval_count") or 0))
        return parse_answer(str((data.get("message") or {}).get("content", "")))
