"""The real retriever. Yours to build (sections 3.2 and 4.4).

Connection details are already here; the query is not.
"""

from __future__ import annotations

from ..config import Settings
from ..schemas import Passage
import httpx
import re
from typing import Any


def version_filter(question: str, versions: str) -> dict[str, Any] | None:
    years = re.findall(r"\b(20\d{2})\b", question)
    if not years:
        return {"superseded": False}
    matching = [v for v in versions.split("|") if v.startswith(years[-1])]
    return {"doc_version": {"$in": matching}} if matching else None


class ChromaRetriever:
    name = "chroma"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Any = None

    def check_startup(self) -> None:
        """Check the pin with bounded REST I/O before accepting traffic.

        Do not construct the heavier SDK client on the event loop at boot.
        Queries lazily construct it; no indexing happens in this process.
        """
        root = (
            f"http://{self.settings.chroma_host}:{self.settings.chroma_port}/api/v2"
            "/tenants/default_tenant/databases/default_database/collections"
        )
        with httpx.Client(timeout=httpx.Timeout(2, connect=2)) as client:
            control = client.get(f"{root}/{self.settings.collection}-control")
            control.raise_for_status()
            pointer = client.post(
                f"{root}/{control.json()['id']}/get",
                json={"ids": ["active"], "include": ["metadatas"]},
            )
            pointer.raise_for_status()
            meta = pointer.json()["metadatas"][0]
            if meta["embed_model"] != self.settings.embed_model:
                raise ValueError(
                    f"embedding model mismatch: index={meta['embed_model']} "
                    f"api={self.settings.embed_model}"
                )

    @property
    def client(self) -> Any:
        import chromadb  # the thin client, from chromadb-client in requirements.txt
        from chromadb.config import Settings as ChromaSettings

        if self._client is None:
            self._client = chromadb.HttpClient(
                host=self.settings.chroma_host,
                port=self.settings.chroma_port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def active(self):
        control = self.client.get_collection(f"{self.settings.collection}-control")
        result = control.get(ids=["active"], include=["metadatas"])
        if not result["metadatas"]:
            raise ValueError("no published index")
        meta = result["metadatas"][0]
        if meta["embed_model"] != self.settings.embed_model:
            raise ValueError(
                f"embedding model mismatch: index={meta['embed_model']} "
                f"api={self.settings.embed_model}"
            )
        col = self.client.get_collection(meta["active_collection"])
        if col.metadata["embed_model"] != self.settings.embed_model:
            raise ValueError(
                f"embedding model mismatch: collection={col.metadata['embed_model']} "
                f"api={self.settings.embed_model}"
            )
        if col.metadata["dimension"] != meta["dimension"] or col.count() == 0:
            raise ValueError("empty index or dimension mismatch")
        return col, meta

    def embed(self, question: str) -> list[float]:
        with httpx.Client(timeout=120) as client:
            response = client.post(
                f"{self.settings.ollama_url.rstrip('/')}/api/embed",
                json={
                    "model": self.settings.embed_model,
                    "input": [
                        (
                            "search_query: "
                            if self.settings.embed_model.startswith("nomic-embed-text")
                            else ""
                        )
                        + question
                    ],
                    "truncate": False,
                },
            )
            response.raise_for_status()
            return [float(x) for x in response.json()["embeddings"][0]]

    def query_context(self, question: str) -> tuple[list[float], str]:
        """The question's embedding and the published index generation, for the cache."""
        _, meta = self.active()
        return self.embed(question), str(meta["generation"])

    def retrieve(self, question: str, k: int, vector: list[float] | None = None) -> list[Passage]:
        collection, meta = self.active()
        if vector is None:
            vector = self.embed(question)
        if len(vector) != meta["dimension"]:
            raise ValueError("query embedding dimension mismatch")
        where = version_filter(question, str(meta.get("versions", "")))
        if where is None:
            return []
        hits = collection.query(
            query_embeddings=[vector],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        return [
            Passage(
                chunk_id=cid,
                text=text,
                score=1 - distance,
                source=m["source"],
                section=m["section"],
                page=m["page"],
                doc_version=m.get("doc_version", "unknown"),
                superseded=m.get("superseded", False),
            )
            for cid, text, m, distance in zip(
                hits["ids"][0], hits["documents"][0], hits["metadatas"][0], hits["distances"][0]
            )
        ]
