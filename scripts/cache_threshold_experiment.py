#!/usr/bin/env python3
"""Measure candidate CACHE_THRESHOLD values on eval/cache-pairs.yaml (section 3.3).

    OLLAMA_URL=http://localhost:11434 python scripts/cache_threshold_experiment.py

Embeds every pair with the pinned EMBED_MODEL, exactly as the API embeds questions,
then reports for each threshold how many paraphrases would hit and how many
different-answer pairs would hit falsely. Ship the lowest threshold with zero false
hits, and write the false hit that ruled out a lower one into docs/PIPELINE.md.
Results go to eval/cache-threshold-experiment.json.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = (0.85, 0.90, 0.93, 0.95, 0.97)


def embed(client: httpx.Client, url: str, model: str, texts: list[str]) -> list[list[float]]:
    prefix = "search_query: " if model.startswith("nomic-embed-text") else ""
    r = client.post(f"{url}/api/embed",
                    json={"model": model, "input": [prefix + t for t in texts], "truncate": False})
    r.raise_for_status()
    return r.json()["embeddings"]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def main() -> int:
    url = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    model = os.environ.get("EMBED_MODEL", "nomic-embed-text")
    pairs = yaml.safe_load((ROOT / "eval/cache-pairs.yaml").read_text(encoding="utf-8"))["pairs"]
    with httpx.Client(timeout=120) as client:
        vectors = embed(client, url, model, [p[k] for p in pairs for k in ("a", "b")])
    scored = [
        {**p, "similarity": round(cosine(vectors[2 * i], vectors[2 * i + 1]), 4)}
        for i, p in enumerate(pairs)
    ]
    for row in sorted(scored, key=lambda r: -r["similarity"]):
        tag = "same" if row["same"] else "DIFF"
        print(f"{row['similarity']:.4f}  {tag}  {row['a'][:45]} | {row['b'][:45]}")
    summary = []
    print("\nthreshold  true_hits  false_hits")
    for t in THRESHOLDS:
        true_hits = sum(r["similarity"] >= t for r in scored if r["same"])
        false = [r for r in scored if not r["same"] and r["similarity"] >= t]
        summary.append({"threshold": t, "true_hits": true_hits, "false_hits": len(false),
                        "false_hit_pairs": [[r["a"], r["b"]] for r in false]})
        print(f"{t:<10} {true_hits:<10} {len(false)}")
    out = ROOT / "eval/cache-threshold-experiment.json"
    out.write_text(json.dumps({"embed_model": model, "pairs": scored, "thresholds": summary},
                              indent=2), encoding="utf-8")
    print(f"\nwritten to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
