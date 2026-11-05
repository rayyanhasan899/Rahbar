"""Liveness and readiness (section 4.3). They answer different questions."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
import os
import logging

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Is the process alive? Must never touch Chroma, Redis or the LLM."""
    return {"status": "alive"}


@router.get("/readyz")
def readyz(request: Request, response: Response) -> dict[str, object]:
    checks = {}
    try:
        from ..retrieval.chroma import ChromaRetriever

        retriever = request.app.state.retriever
        if isinstance(retriever, ChromaRetriever):
            _, meta = retriever.active()
            checks["chroma"] = str(meta["generation"])
        else:
            import chromadb

            client = chromadb.HttpClient(
                host=request.app.state.settings.chroma_host,
                port=request.app.state.settings.chroma_port,
            )
            col = client.get_collection(request.app.state.settings.collection)
            if (
                not col.count()
                or col.metadata.get("embed_model") != request.app.state.settings.embed_model
            ):
                raise ValueError("empty collection or embedding model mismatch")
            checks["chroma"] = "dummy index; stub mode"
    except Exception as exc:
        checks["chroma"] = str(exc)
        response.status_code = 503
        logging.getLogger("rahbar.readiness").warning("chroma readiness failed: %s", exc)
    try:
        import redis

        cache = redis.Redis(
            host=os.environ.get("REDIS_HOST", "redis"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        cache.ping()
        cache.close()
        checks["redis"] = "reachable"
    except Exception as exc:
        checks["redis"] = str(exc)
        response.status_code = 503
    return {"status": "ready" if response.status_code != 503 else "not ready", "checks": checks}
