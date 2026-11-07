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
import hashlib
import math
import os
import sys
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
from app.services.cache import intent, numbers  # noqa: E402
from app.services.guard import looks_like_injection  # noqa: E402
THRESHOLDS = (0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)


def embed(client: httpx.Client, url: str, model: str, texts: list[str]) -> list[list[float]]:
    prefix = "search_query: " if model.startswith("nomic-embed-text") else ""
    vectors = []
    for start in range(0, len(texts), 16):
        r = client.post(f"{url}/api/embed",
                        json={"model": model, "input": [prefix + t for t in texts[start:start + 16]], "truncate": False})
        r.raise_for_status()
        vectors.extend(r.json()["embeddings"])
    return vectors


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def main() -> int:
    url = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    model = os.environ.get("EMBED_MODEL", "nomic-embed-text")
    pairs = yaml.safe_load((ROOT / "eval/cache-pairs.yaml").read_text(encoding="utf-8"))["pairs"]
    # Independent negative pairs from pre-existing document-derived labels, not
    # from similarity/retrieval results. Include absent topics as lookup probes.
    golden = yaml.safe_load((ROOT / "eval/golden.yaml").read_text())["questions"]
    for i, a in enumerate(golden):
        for b in golden[i + 1:]:
            a_refs = {(r['source'], str(r['section'])) for r in a['relevant']}
            b_refs = {(r['source'], str(r['section'])) for r in b['relevant']}
            if a_refs != b_refs and (a_refs or b_refs):
                pairs.append({"a": a["question"], "b": b["question"], "same": False, "origin": f"golden:{a['id']}/{b['id']}"})
    texts = list(dict.fromkeys(p[k] for p in pairs for k in ("a", "b")))
    with httpx.Client(timeout=120) as client:
        vectors = dict(zip(texts, embed(client, url, model, texts)))
        tags = client.get(f"{url}/api/tags")
        tags.raise_for_status()
        digest = next(m['digest'] for m in tags.json()['models'] if m['name'] in {model, model + ':latest'})
    scored = [
        {**p, "similarity": cosine(vectors[p['a']], vectors[p['b']]),
         "guard_compatible": numbers(p['a']) == numbers(p['b']) and intent(p['a']) == intent(p['b']) and not looks_like_injection(p['a']) and not looks_like_injection(p['b'])}
        for p in pairs
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
                        "guarded_true_hits": sum(r["similarity"] >= t and r['guard_compatible'] for r in scored if r["same"]),
                        "guarded_false_hits": sum(r["similarity"] >= t and r['guard_compatible'] for r in scored if not r["same"]),
                        "false_hit_pairs": [[r["a"], r["b"]] for r in false]})
        print(f"{t:<10} {true_hits:<10} {len(false)}")
    out = ROOT / "eval/cache-threshold-experiment.json"
    out.write_text(json.dumps({"embed_model": model, "model_digest": digest, "dimension": len(next(iter(vectors.values()))),
                              "golden_sha256": hashlib.sha256((ROOT / 'eval/golden.yaml').read_bytes()).hexdigest(),
                              "cache_pairs_sha256": hashlib.sha256((ROOT / 'eval/cache-pairs.yaml').read_bytes()).hexdigest(),
                              "embedding_protocol": "nomic search_query; truncate=false; batches<=16", "pairs": scored, "thresholds": summary},
                              indent=2), encoding="utf-8")
    print(f"\nwritten to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
