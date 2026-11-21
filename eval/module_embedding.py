#!/usr/bin/env python3
"""Module level: embedding quality, speed and determinism (Part B1, paper Table 1).

    python eval/module_embedding.py            # prints the result; suite.py calls run()

Paraphrase pairs should score clearly higher than unrelated pairs; the gap is the
margin retrieval works with. Time per chunk is measured on real chunks from the active
collection. Determinism embeds the same text twice and reports the largest difference.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HERE, Services, cosine, mean, percentile, read_jsonl  # noqa: E402


def pair_scores(services: Services, pairs: list[dict], model: str) -> dict:
    texts = [p["a"] for p in pairs] + [p["b"] for p in pairs]
    vectors = services.embed(texts, model)
    half = len(pairs)
    scored = [
        {**p, "cosine": round(cosine(vectors[i], vectors[half + i]), 4)}
        for i, p in enumerate(pairs)
    ]
    para = [s["cosine"] for s in scored if s["kind"] == "paraphrase"]
    other = [s["cosine"] for s in scored if s["kind"] == "unrelated"]
    return {
        "paraphrase_pairs": len(para),
        "unrelated_pairs": len(other),
        "paraphrase_mean_cosine": mean(para),
        "unrelated_mean_cosine": mean(other),
        "gap": (mean(para) or 0) - (mean(other) or 0) if para and other else None,
        "lowest_paraphrase": min(para) if para else None,
        "highest_unrelated": max(other) if other else None,
        "pairs": scored,
    }


def timing(services: Services, model: str, chunks: list[str], batch: int = 16) -> dict:
    per_batch = []
    for start in range(0, len(chunks), batch):
        part = chunks[start : start + batch]
        started = time.perf_counter()
        services.embed(part, model)
        per_batch.append((time.perf_counter() - started) * 1000 / len(part))
    return {
        "chunks": len(chunks),
        "batch_size": batch,
        "ms_per_chunk_mean": mean(per_batch),
        "ms_per_chunk_p95": percentile(per_batch, 95),
    }


def determinism(services: Services, model: str, text: str) -> dict:
    first, second = services.embed([text], model)[0], services.embed([text], model)[0]
    return {
        "max_abs_difference": max(abs(a - b) for a, b in zip(first, second)),
        "dimension": len(first),
    }


def run(services: Services, model: str, pairs_path: Path, sample: int, seed: int) -> dict:
    pairs = read_jsonl(pairs_path)
    chunks = [c["text"] for c in services.sample_chunks(sample, seed)]
    return {
        "model": model,
        "similarity": pair_scores(services, pairs, model),
        "speed": timing(services, model, chunks),
        "determinism": determinism(services, model, chunks[0] if chunks else pairs[0]["a"]),
    }


if __name__ == "__main__":
    services = Services(
        "", os.environ.get("OLLAMA_URL", "http://localhost:11434"),
        os.environ.get("CHROMA_URL", "http://localhost:8001"),
        os.environ.get("CHROMA_COLLECTION", "rahbar"),
    )
    result = run(services, os.environ.get("EMBED_MODEL", "nomic-embed-text"),
                 HERE / "embedding-pairs.jsonl", 48, int(os.environ.get("SEED", "42")))
    print(json.dumps({k: v for k, v in result.items()}, indent=2)[:4000])
