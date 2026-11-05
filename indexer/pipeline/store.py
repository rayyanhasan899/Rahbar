"""Publish a complete staged collection without deleting the live index."""

from __future__ import annotations
import hashlib
import uuid
from typing import Any
from .config import IndexerSettings
from .models import Chunk


def get_client(settings: IndexerSettings) -> Any:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def store(chunks: list[Chunk], vectors: list[list[float]], settings: IndexerSettings) -> int:
    if not chunks or len(chunks) != len(vectors):
        raise ValueError("a nonempty index needs one vector per chunk")
    dim = len(vectors[0])
    if not dim or any(len(v) != dim for v in vectors):
        raise ValueError("inconsistent vector dimensions")
    if len({c.id for c in chunks}) != len(chunks):
        raise ValueError("duplicate chunk IDs")
    client = get_client(settings)
    generation = uuid.uuid4().hex
    name = f"{settings.collection}-{generation}"
    collection = client.create_collection(
        name,
        metadata={
            "hnsw:space": "cosine",
            "embed_model": settings.embed_model,
            "dimension": dim,
            "generation": generation,
        },
    )
    for start in range(0, len(chunks), 128):
        batch = chunks[start : start + 128]
        collection.add(
            ids=[c.id for c in batch],
            documents=[c.text for c in batch],
            metadatas=[c.metadata() for c in batch],
            embeddings=vectors[start : start + 128],
        )
    count = int(collection.count())
    if count != len(chunks):
        raise RuntimeError("staged count mismatch; active index unchanged")
    digest = hashlib.sha256("".join(c.id for c in chunks).encode()).hexdigest()
    control = client.get_or_create_collection(f"{settings.collection}-control")
    control.upsert(
        ids=["active"],
        embeddings=[[1.0]],
        documents=["active index"],
        metadatas=[
            {
                "active_collection": name,
                "generation": generation,
                "embed_model": settings.embed_model,
                "dimension": dim,
                "chunks": count,
                "content_sha256": digest,
                "versions": "|".join(sorted({c.doc_version for c in chunks})),
            }
        ],
    )
    return count
