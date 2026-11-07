"""Reproducible retrieval-only experiment; never presents stub generation scores.

Run after scripts/audit_corpus.py, with Ollama and a Chroma 1.0.12 server reachable.
Reads golden labels written before tuning; keeps per-question results and fingerprints.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "indexer"))
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "eval"))

import yaml  # noqa: E402
import httpx  # noqa: E402
from pipeline.chunk import chunk, token_count  # noqa: E402
from pipeline.config import get_settings  # noqa: E402
from pipeline.embed import embed  # noqa: E402
from pipeline.models import Document, Page  # noqa: E402
from pipeline.store import store  # noqa: E402
from run_eval import recall_at_k  # noqa: E402
from app.retrieval.chroma import version_filter  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=ROOT / ".venv/extracted")
    parser.add_argument(
        "--out", type=Path, default=ROOT / "eval/chunk-experiments.json"
    )
    args = parser.parse_args()
    settings = get_settings()
    golden_path = ROOT / "eval/golden.yaml"
    golden = yaml.safe_load(golden_path.read_text())["questions"]
    manifest = json.loads((ROOT / "corpus/raw/_index.json").read_text())
    documents = []
    inputs = []
    for entry in manifest:
        cache_path = args.cache / (entry["file"] + ".json")
        data = json.loads(cache_path.read_text())
        inputs.append(
            {
                "file": entry["file"],
                "source_sha256": entry["sha256"],
                "cleaned_cache_sha256": hashlib.sha256(
                    cache_path.read_bytes()
                ).hexdigest(),
            }
        )
        documents.append(
            Document(
                data["source"],
                data["doc_version"],
                data["superseded"],
                [
                    Page(p["source"], p["page"], p["text"], p["ocr"])
                    for p in data["pages"]
                ],
            )
        )
    original = sum(token_count(p.text) for d in documents for p in d.pages)
    query_vectors = embed([q["question"] for q in golden], settings, purpose="query")
    tags = httpx.get(settings.ollama_url.rstrip("/") + "/api/tags", timeout=10)
    tags.raise_for_status()
    model_digest = next(
        m["digest"]
        for m in tags.json()["models"]
        if m["name"] in {settings.embed_model, settings.embed_model + ":latest"}
    )
    output = {
        "kind": "retrieval-only; not generation evaluation",
        "golden_sha256": hashlib.sha256(golden_path.read_bytes()).hexdigest(),
        "embed_model": settings.embed_model,
        "dimension": len(query_vectors[0]),
        "runs": [],
        "inputs": inputs,
        "model_digest": model_digest,
        "embedding_protocol": "nomic search_document/search_query; truncate=false",
    }
    lock = Path(settings.index_lock_path)
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        for size, overlap in [(300, 40), (500, 75), (700, 100)]:
            pieces = [c for d in documents for c in chunk(d, size, overlap)]
            texts = [c.text for c in pieces]
            # Reuse embeddings of identical text across configurations, not labels/results.
            cached = []
            cache = ROOT / ".venv/embedding-cache"
            cache.mkdir(exist_ok=True)
            for text in texts:
                key = hashlib.sha256(
                    (
                        settings.embed_model
                        + "\0"
                        + model_digest
                        + "\0search_document-v1\0"
                        + text
                    ).encode()
                ).hexdigest()
                cached.append(cache / (key + ".json"))
            missing = [i for i, p in enumerate(cached) if not p.exists()]
            for start in range(0, len(missing), 16):
                indices = missing[start : start + 16]
                vectors = embed([texts[i] for i in indices], settings)
                for i, vector in zip(indices, vectors):
                    cached[i].write_text(json.dumps(vector))
            vectors = [json.loads(p.read_text()) for p in cached]
            store(
                pieces,
                vectors,
                replace(settings, chunk_size=size, chunk_overlap=overlap),
            )
            from pipeline.store import get_client

            client = get_client(settings)
            meta = client.get_collection(settings.collection + "-control").get(
                ids=["active"]
            )["metadatas"][0]
            collection = client.get_collection(meta["active_collection"])
            rows = []
            for q, vector in zip(golden, query_vectors):
                where = version_filter(q["question"], str(meta.get("versions", "")))
                if where is None:
                    raise ValueError("golden requests a version absent from the experiment")
                hits = collection.query(
                    query_embeddings=[vector],
                    n_results=5,
                    where=where,
                    include=["metadatas", "distances"],
                )
                refs = [
                    dict(m, chunk_id=cid, score=1 - dist)
                    for m, cid, dist in zip(
                        hits["metadatas"][0], hits["ids"][0], hits["distances"][0]
                    )
                ]
                rows.append(
                    {
                        "id": q["id"],
                        "type": q["type"],
                        "retrieved": refs,
                        "recall_at_3": recall_at_k(q["relevant"], refs, 3),
                        "recall_at_5": recall_at_k(q["relevant"], refs, 5),
                    }
                )
            valid = [r for r in rows if r["recall_at_5"] is not None]
            record = {
                "size": size,
                "overlap": overlap,
                "chunks": len(pieces),
                "original_tokens": original,
                "stored_tokens": sum(token_count(t) for t in texts),
                "storage_amplification": sum(token_count(t) for t in texts) / original,
                "recall_at_3": sum(r["recall_at_3"] for r in valid) / len(valid),
                "recall_at_5": sum(r["recall_at_5"] for r in valid) / len(valid),
                "rows": rows,
            }
            output["runs"].append(record)
            args.out.write_text(json.dumps(output, indent=2) + "\n")
            print(
                json.dumps({k: v for k, v in record.items() if k != "rows"}), flush=True
            )


if __name__ == "__main__":
    main()
