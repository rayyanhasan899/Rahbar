"""Hosted free-tier provider (Groq, Google AI Studio, OpenRouter).

The key arrives as LLM_API_KEY from a Kubernetes Secret created on the command
line. It never appears in a file you commit, and never in a log line.

Uses the OpenAI-compatible POST {hosted_base_url}/chat/completions. JSON mode
(`response_format: json_object`) is the most widely supported option; the schema
itself travels in the system message and the reply is validated afterwards.
"""

from __future__ import annotations

import time
import logging
from collections.abc import Sequence

import httpx

from ...config import Settings
from ...routes.metrics import GENERATION_SECONDS, TOKENS
from ...schemas import Answer, Passage, Turn
from .prompt import ProviderOutputError, ProviderUnavailable, build_messages, parse_answer

log = logging.getLogger("rahbar.provider")


class HostedProvider:
    name = "hosted"

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        if not settings.hosted_base_url:
            raise ValueError("LLM_PROVIDER=hosted needs HOSTED_BASE_URL")
        if httpx.URL(settings.hosted_base_url).scheme != "https":
            raise ValueError("hosted provider requires HTTPS")
        self.settings = settings  # hosted_base_url, llm_model, llm_api_key, temperature
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
            "temperature": self.settings.temperature,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        start = time.perf_counter()
        try:
            response = self.client.post(
                f"{self.settings.hosted_base_url.rstrip('/')}/chat/completions",
                json=body,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            # The status code is enough; the response body can echo request details.
            raise ProviderUnavailable(f"hosted: HTTP {exc.response.status_code}") from exc
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderUnavailable(f"hosted: {type(exc).__name__}") from exc
        finally:
            GENERATION_SECONDS.labels(provider=self.name).observe(time.perf_counter() - start)
        try:
            usage = data.get("usage") or {}
            prompt_tokens = max(0, int(usage.get("prompt_tokens") or 0))
            completion_tokens = max(0, int(usage.get("completion_tokens") or 0))
        except (AttributeError, TypeError, ValueError) as exc:
            raise ProviderOutputError("invalid hosted usage envelope") from exc
        TOKENS.labels(kind="prompt").inc(prompt_tokens)
        TOKENS.labels(kind="completion").inc(completion_tokens)
        log.info("model usage", extra={"provider": self.name, "tokens_in": prompt_tokens, "tokens_out": completion_tokens})
        return parse_answer(str(content or ""))
