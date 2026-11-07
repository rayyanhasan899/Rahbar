"""Prometheus metrics at /metrics (section 4.8).

Request count and latency are wired up already. Add your own the same way:
retrieval latency, generation latency, cache hits, abstentions, fallbacks, tokens.
"""

from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

router = APIRouter()

REQUESTS = Counter("rahbar_requests_total", "HTTP requests", ["path", "status"])
LATENCY = Histogram(
    "rahbar_request_seconds",
    "HTTP request latency",
    ["path"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60),
)
RETRIEVAL_SECONDS = Histogram(
    "rahbar_retrieval_seconds",
    "Question embedding plus vector search",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
GENERATION_SECONDS = Histogram(
    "rahbar_generation_seconds",
    "One model call",
    ["provider"],
    buckets=(0.5, 1, 2, 5, 10, 20, 30, 60, 120),
)
CACHE = Counter("rahbar_cache_total", "Semantic cache lookups", ["result"])
ABSTENTIONS = Counter("rahbar_abstentions_total", "Questions declined", ["reason"])
FALLBACKS = Counter("rahbar_fallbacks_total", "Safe fallback answers", ["reason"])
RETRIES = Counter("rahbar_generation_retries_total", "Second model calls after a bad reply")
TOKENS = Counter("rahbar_llm_tokens_total", "Tokens reported by the provider", ["kind"])
INJECTION = Counter(
    "rahbar_injection_flags_total", "Instruction-like text found", ["where"]
)


@router.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
