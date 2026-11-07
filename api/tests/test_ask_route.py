"""POST /api/ask through FastAPI: history in the request, X-Cache, and 503 on retrieval."""

from __future__ import annotations

import pytest
from app.services.cache import SemanticCache
from fastapi.testclient import TestClient
from tests.fakes import POLICY, FakeRedis, FakeRetriever, ScriptedProvider, good_answer


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RETRIEVER", "stub")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    from app.main import app

    with TestClient(app) as c:
        yield c


def test_stub_mode_sends_no_cache_header(client):
    r = client.post("/api/ask", json={"question": "What is the attendance requirement?"})
    assert r.status_code == 200
    assert "X-Cache" not in r.headers


def test_cache_header_reports_miss_then_hit(client):
    state = client.app.state
    state.retriever = FakeRetriever([POLICY])
    state.provider = ScriptedProvider(good_answer())
    state.cache = SemanticCache(state.settings, client=FakeRedis())
    first = client.post("/api/ask", json={"question": "Attendance rules please"})
    second = client.post("/api/ask", json={"question": "Attendance requirement?"},
                         headers={"X-Request-ID": "second"})
    assert (first.headers["X-Cache"], second.headers["X-Cache"]) == ("MISS", "HIT")
    assert second.json()["request_id"] == "second"


def test_history_is_accepted_and_bounded(client):
    turn = {"question": "What does clause 1.21 say?", "answer": "Attendance."}
    ok = client.post("/api/ask", json={"question": "And the condoned part?", "history": [turn]})
    assert ok.status_code == 200
    too_many = client.post("/api/ask", json={"question": "And then?", "history": [turn] * 11})
    assert too_many.status_code == 422


def test_retrieval_outage_returns_503(client):
    retriever = FakeRetriever([POLICY])
    retriever.fail = True
    client.app.state.retriever = retriever
    r = client.post("/api/ask", json={"question": "What attendance is required?"})
    assert r.status_code == 503
    assert r.json()["detail"] == "retrieval is unavailable"


def test_new_metrics_are_exported(client):
    client.post("/api/ask", json={"question": "Count this request"})
    text = client.get("/metrics").text
    for name in ("rahbar_retrieval_seconds", "rahbar_abstentions_total", "rahbar_cache_total"):
        assert name in text
