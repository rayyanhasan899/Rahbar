from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "chroma_ok,redis_ok,expected", [(True, True, 200), (False, True, 503), (True, False, 503)]
)
def test_readiness_checks_real_dependencies_with_offline_fakes(
    monkeypatch, chroma_ok, redis_ok, expected
):
    import chromadb
    import redis
    from app.main import app

    collection = SimpleNamespace(metadata={"embed_model": "dummy-768"}, count=lambda: 3)
    chroma = MagicMock()
    chroma.get_collection.return_value = collection
    if not chroma_ok:
        chroma.get_collection.side_effect = RuntimeError("chroma unavailable")
    cache = MagicMock()
    if not redis_ok:
        cache.ping.side_effect = RuntimeError("redis unavailable")
    monkeypatch.setattr(chromadb, "HttpClient", lambda **kw: chroma)
    monkeypatch.setattr(redis, "Redis", lambda **kw: cache)
    monkeypatch.setenv("EMBED_MODEL", "dummy-768")
    monkeypatch.setenv("RETRIEVER", "stub")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    with TestClient(app) as client:
        result = client.get("/readyz")
        assert result.status_code == expected
        assert client.get("/healthz").json() == {"status": "alive"}
