from unittest.mock import MagicMock
import httpx
import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "chroma_ok,redis_ok,expected", [(True, True, 200), (False, True, 503), (True, False, 503)]
)
def test_readiness_checks_dependencies_with_offline_fakes(
    monkeypatch, chroma_ok, redis_ok, expected
):
    import redis
    from app.main import app

    original_client = httpx.Client

    def handler(request):
        if not chroma_ok:
            raise httpx.ConnectError("chroma unavailable", request=request)
        if request.url.path.endswith("/heartbeat"):
            return httpx.Response(200, json={"nanosecond heartbeat": 1})
        if request.url.path.endswith("/count"):
            return httpx.Response(200, json=3)
        return httpx.Response(
            200, json={"id": "collection-id", "metadata": {"embed_model": "dummy-768"}}
        )

    factory = MagicMock(
        side_effect=lambda **kw: original_client(transport=httpx.MockTransport(handler), **kw)
    )
    monkeypatch.setattr(httpx, "Client", factory)
    cache = MagicMock()
    if not redis_ok:
        cache.ping.side_effect = RuntimeError("redis unavailable")
    monkeypatch.setattr(redis, "Redis", lambda **kw: cache)
    monkeypatch.setenv("EMBED_MODEL", "dummy-768")
    monkeypatch.setenv("RETRIEVER", "stub")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    with TestClient(app) as client:
        assert client.get("/readyz").status_code == expected
        assert client.get("/readyz").status_code == expected
        assert factory.call_count == 1
        assert client.get("/healthz").json() == {"status": "alive"}


@pytest.mark.parametrize(
    "matching,nonempty,expected", [(True, True, 200), (False, True, 503), (True, False, 503)]
)
def test_real_publication_pin_and_empty_index(monkeypatch, matching, nonempty, expected):
    from types import SimpleNamespace
    import redis
    from fastapi import Response
    from app.config import Settings
    from app.routes.health import readyz

    original_client = httpx.Client

    def handler(request):
        url = request.url.path
        if url.endswith("/heartbeat"):
            data = {}
        elif url.endswith("/get"):
            data = {
                "metadatas": [
                    {
                        "active_collection": "generation",
                        "embed_model": "nomic-embed-text" if matching else "wrong-model",
                        "dimension": 768,
                    }
                ]
            }
        elif url.endswith("/count"):
            data = int(nonempty)
        elif url.endswith("-control"):
            data = {"id": "control-id"}
        else:
            data = {
                "id": "generation-id",
                "metadata": {"embed_model": "nomic-embed-text", "dimension": 768},
            }
        return httpx.Response(200, json=data)

    monkeypatch.setattr(
        httpx, "Client", lambda **kw: original_client(transport=httpx.MockTransport(handler), **kw)
    )
    monkeypatch.setattr(redis, "Redis", lambda **kw: MagicMock())
    state = SimpleNamespace(settings=Settings(retriever="chroma"), readiness_chroma=None)
    response = Response()
    result = readyz(SimpleNamespace(app=SimpleNamespace(state=state)), response)
    assert response.status_code == expected
    assert (result["status"] == "ready") == (expected == 200)
