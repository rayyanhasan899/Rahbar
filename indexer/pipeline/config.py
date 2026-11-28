"""Indexer configuration, from the same ConfigMap the API reads (section 4.1)."""

from __future__ import annotations

import os
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class IndexerSettings:
    embed_model: str  # EMBED_MODEL: must equal the API's value (section 4.4)
    chroma_host: str
    chroma_port: int
    collection: str
    corpus_dir: str  # where the documents and _index.json sit inside the Job's pod
    chunk_size: int
    chunk_overlap: int
    ollama_url: str
    embed_batch_size: int = 16
    index_lock_path: str = "/tmp/rahbar-index.lock"
    datalake_dir: str = "/datalake"
    incoming_dirs: tuple[str, ...] = ()
    min_text_chars: int = 64
    near_dup_threshold: float = .995
    document_embed_chars: int = 4000

    def __post_init__(self) -> None:
        if not math.isfinite(self.near_dup_threshold) or not 0 < self.near_dup_threshold <= 1:
            raise ValueError("NEAR_DUP_THRESHOLD must be finite and in (0,1]")
        if self.min_text_chars < 1 or not 64 <= self.document_embed_chars <= 16000:
            raise ValueError("invalid document verification text limits")


def get_settings() -> IndexerSettings:
    return IndexerSettings(
        embed_model=os.environ.get("EMBED_MODEL", "nomic-embed-text"),
        chroma_host=os.environ.get("CHROMA_HOST", "chroma"),
        chroma_port=int(os.environ.get("CHROMA_PORT", 8000)),
        collection=os.environ.get("CHROMA_COLLECTION", "rahbar"),
        corpus_dir=os.environ.get("CORPUS_DIR", "/corpus"),
        chunk_size=int(os.environ.get("CHUNK_SIZE", 400)),
        chunk_overlap=int(os.environ.get("CHUNK_OVERLAP", 50)),
        ollama_url=os.environ.get("OLLAMA_URL", "http://host.minikube.internal:11434"),
        embed_batch_size=max(1, int(os.environ.get("EMBED_BATCH_SIZE", "16"))),
        index_lock_path=os.environ.get("INDEX_LOCK_PATH", "/tmp/rahbar-index.lock"),
        datalake_dir=os.environ.get("DATALAKE_DIR", "/datalake"),
        incoming_dirs=tuple(p.strip() for p in os.environ.get("INCOMING_DIRS", "").split(",")
                            if p.strip()),
        min_text_chars=int(os.environ.get("MIN_TEXT_CHARS", "64")),
        near_dup_threshold=float(os.environ.get("NEAR_DUP_THRESHOLD", ".995")),
        document_embed_chars=int(os.environ.get("DOCUMENT_EMBED_CHARS", "4000")),
    )
