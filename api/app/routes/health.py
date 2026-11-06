"""Bounded readiness I/O; process liveness remains independent."""

from __future__ import annotations
import os
import logging
import httpx
from fastapi import APIRouter, Request, Response

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/readyz")
def readyz(request: Request, response: Response) -> dict[str, object]:
    checks = {}
    settings = request.app.state.settings
    try:
        client = request.app.state.readiness_chroma
        if client is None:
            client = httpx.Client(timeout=httpx.Timeout(2, connect=2))
            request.app.state.readiness_chroma = client
        root = f"http://{settings.chroma_host}:{settings.chroma_port}/api/v2"
        collections = root + "/tenants/default_tenant/databases/default_database/collections"

        def get(url):
            result = client.get(url)
            result.raise_for_status()
            return result.json()

        get(root + "/heartbeat")
        if settings.retriever == "chroma":
            control = get(collections + f"/{settings.collection}-control")
            pointer = client.post(
                collections + f"/{control['id']}/get",
                json={"ids": ["active"], "include": ["metadatas"]},
            )
            pointer.raise_for_status()
            meta = pointer.json()["metadatas"][0]
            if meta["embed_model"] != settings.embed_model:
                raise ValueError("published embedding model mismatch")
            collection = get(collections + "/" + meta["active_collection"])
            if collection["metadata"]["dimension"] != meta["dimension"]:
                raise ValueError("embedding dimension mismatch")
        else:
            collection = get(collections + "/" + settings.collection)
        if collection["metadata"]["embed_model"] != settings.embed_model:
            raise ValueError(
                f"embedding model mismatch: index={collection['metadata']['embed_model']} "
                f"api={settings.embed_model}"
            )
        if not get(collections + f"/{collection['id']}/count"):
            raise ValueError("collection is empty")
        checks["chroma"] = "reachable, nonempty, embedding pin matches"
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
