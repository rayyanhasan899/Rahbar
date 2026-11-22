"""Bounded Chroma snapshot publication; readers only observe a validated generation."""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any

from .config import IndexerSettings
from .store import get_client


class ChromaSnapshots:
    def __init__(self, settings: IndexerSettings) -> None:
        self.settings = settings
        self.client = get_client(settings)

    def active(self) -> dict[str, Any] | None:
        from chromadb.errors import NotFoundError
        try:
            result = self.client.get_collection(self.settings.collection + "-control").get(
                ids=["active"], include=["metadatas"])
        except NotFoundError:
            return None
        return result["metadatas"][0] if result["metadatas"] else None

    def counts(self, name: str) -> dict[str, int]:
        collection = self.client.get_collection(name)
        counts: Counter[str] = Counter()
        for start in range(0, collection.count(), 128):
            page = collection.get(limit=128, offset=start, include=["metadatas"])
            counts.update(str(m["doc_key"]) for m in page["metadatas"])
        return dict(counts)

    def valid(self, ledger: dict) -> bool:
        collection = self.client.get_collection(ledger["active_collection"])
        expected = {cid: (key, record) for key, record in ledger["documents"].items()
                    if record["status"] != "deleted" for cid in record["chunk_ids"]}
        seen = set()
        for start in range(0, collection.count(), 128):
            page = collection.get(limit=128, offset=start, include=["metadatas"])
            for cid, meta in zip(page["ids"], page["metadatas"]):
                if cid not in expected:
                    return False
                key, record = expected[cid]
                archived = record["status"] == "archived"
                if (meta.get("doc_key") != key or meta.get("doc_id") != record["doc_id"]
                        or meta.get("doc_sha256") != record["sha256"]
                        or meta.get("archived") != archived
                        or meta.get("superseded") != archived):
                    return False
                seen.add(cid)
        return seen == set(expected) and collection.count() == len(expected)

    def publish(self, ledger: dict, rows: Iterable[dict]) -> None:
        collection = self.client.create_collection(ledger["active_collection"], metadata={
            "hnsw:space": "cosine", "embed_model": ledger["embed_model"],
            "dimension": ledger["dimension"], "generation": ledger["generation"],
            "embed_model_digest": ledger["embed_model_digest"],
            "fingerprint": ledger["fingerprint"],
        })
        batch: list[dict] = []

        def flush() -> None:
            if not batch:
                return
            collection.add(ids=[r["id"] for r in batch],
                           documents=[r["text"] for r in batch],
                           metadatas=[r["metadata"] for r in batch],
                           embeddings=[r["vector"] for r in batch])
            batch.clear()

        for row in rows:
            batch.append(row)
            if len(batch) == 128:
                flush()
        flush()
        expected = {key: len(r["chunk_ids"]) for key, r in ledger["documents"].items()
                    if r["status"] != "deleted" and r["chunk_ids"]}
        if self.counts(ledger["active_collection"]) != expected:
            raise RuntimeError("staged per-document counts mismatch; active index retained")
        if collection.count() != ledger["chunks"]:
            raise RuntimeError("staged total count mismatch; active index retained")
        if not self.valid(ledger):
            raise RuntimeError("staged IDs/metadata mismatch; active index retained")
        meta = {k: ledger[k] for k in (
            "active_collection", "generation", "embed_model", "embed_model_digest",
            "dimension", "chunks", "content_sha256", "versions", "fingerprint",
            "ledger_revision", "chunk_size", "chunk_overlap")}
        self.client.get_or_create_collection(self.settings.collection + "-control").upsert(
            ids=["active"], embeddings=[[1.0]], documents=["active index"], metadatas=[meta])
