"""Bounded embedding batches using the pinned Ollama model."""

from __future__ import annotations
import math
import re
import httpx
from .config import IndexerSettings


def model_digest(settings: IndexerSettings) -> str:
    """Pin the actual installed embedding artifact, not only a mutable model name."""
    with httpx.Client(timeout=httpx.Timeout(15, connect=5)) as client:
        response = client.get(settings.ollama_url.rstrip("/") + "/api/tags")
        response.raise_for_status()
        requested = settings.embed_model
        if ":" not in requested.rsplit("/", 1)[-1]:
            requested += ":latest"
        for model in response.json()["models"]:
            if model.get("name") == requested or model.get("model") == requested:
                value = str(model.get("digest", "")).removeprefix("sha256:")
                if re.fullmatch(r"[0-9a-f]{64}", value):
                    return value
        raise ValueError("installed embedding artifact digest is missing")


def embed(
    texts: list[str], settings: IndexerSettings, purpose: str = "document"
) -> list[list[float]]:
    vectors: list[list[float]] = []
    dimension = 0
    with httpx.Client(timeout=httpx.Timeout(120, connect=10)) as client:
        for start in range(0, len(texts), settings.embed_batch_size):
            batch = texts[start : start + settings.embed_batch_size]
            if settings.embed_model.startswith("nomic-embed-text"):
                prefix = "search_query: " if purpose == "query" else "search_document: "
                batch = [prefix + text for text in batch]
            response = client.post(
                f"{settings.ollama_url.rstrip('/')}/api/embed",
                json={
                    "model": settings.embed_model,
                    "input": batch,
                    "truncate": False,
                    "keep_alive": "5m",
                },
            )
            response.raise_for_status()
            data = response.json()["embeddings"]
            if len(data) != len(batch):
                raise ValueError("embedding count differs from text count")
            for vector in data:
                if not vector or not all(math.isfinite(v) for v in vector):
                    raise ValueError("empty or nonfinite embedding")
                dimension = dimension or len(vector)
                if len(vector) != dimension:
                    raise ValueError("embedding dimension changed")
                vectors.append(vector)
    return vectors
