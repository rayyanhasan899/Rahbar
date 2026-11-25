"""Immutable trace behavior with fake transport/storage only."""

import importlib.util
import json
import sys
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch

import httpx
import pytest
from app.config import Settings
from app.providers.llm.ollama import OllamaProvider
from app.services.answer import answer_question, RetrievalUnavailable
from app.services.trace import Trace, current
from app.services.cache import SemanticCache
from tests.fakes import FakeRetriever, FakeRedis, POLICY, good_answer


def module(name):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).resolve().parents[2] / "scripts" / (name + ".py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_actual_retry_prompt_is_replayed_after_source_changes(tmp_path):
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        text = "invalid" if len(calls) == 1 else good_answer().model_dump_json()
        return httpx.Response(200, json={"message": {"content": text}})

    settings = Settings(trace_dir=str(tmp_path), relevance_floor=0.45)
    provider = OllamaProvider(settings, httpx.Client(transport=httpx.MockTransport(handler)))
    response = answer_question(
        "What attendance?", FakeRetriever([POLICY]), provider, settings
    ).response
    assert len(response.evidence["attempts"]) == 2
    records = [json.loads(x) for x in next(tmp_path.glob("*.jsonl")).read_text().splitlines()]
    source = tmp_path / "original-source.txt"
    source.write_text(POLICY.text)
    source.unlink()
    replay = module("trace_tool").reconstruct(records[0])
    assert replay["attempts"][0]["messages"] == calls[0]["messages"]
    assert replay["prompt"] == calls[1]["messages"]
    assert "previous reply was rejected" in replay["prompt"][-1]["content"]
    records[0]["attempts"][0]["messages"][0]["content"] = "tampered"
    with pytest.raises(ValueError, match="hash"):
        module("trace_tool").reconstruct(records[0])


def test_cache_hit_retains_original_evidence_without_fresh_model_call(tmp_path):
    settings = Settings(trace_dir=str(tmp_path), relevance_floor=0.45, cache_threshold=0.95)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"message": {"content": good_answer().model_dump_json()}})

    provider = OllamaProvider(settings, httpx.Client(transport=httpx.MockTransport(handler)))
    cache = SemanticCache(settings, FakeRedis())
    first = answer_question(
        "Attendance rules please", FakeRetriever([POLICY]), provider, settings, cache=cache
    )
    second = answer_question(
        "Attendance requirement?", FakeRetriever([POLICY]), provider, settings, cache=cache
    )
    assert second.cache == "hit" and len(calls) == 1
    records = [json.loads(x) for x in next(tmp_path.glob("*.jsonl")).read_text().splitlines()]
    assert records[1]["attempts"] == []
    assert records[1]["provenance"]["trace_id"] == first.response.request_id
    assert module("trace_tool").reconstruct(records[1])["hashes_verified"] == 1


def test_writer_failure_does_not_break_answer_and_error_is_observable(caplog):
    caplog.set_level("INFO")
    trace = Trace(Settings(trace_dir="/not-used"))
    with patch("app.services.trace.persist", side_effect=OSError("disk full")):
        trace.finish()
        trace.finish()
    records = [r for r in caplog.records if r.name == "rahbar.trace"]
    assert len(records) == 1
    assert records[0].persistence["written"] is False
    assert records[0].persistence["error"] == "OSError"


def test_refusal_error_and_window_denominators(tmp_path, monkeypatch):
    settings = Settings(trace_dir=str(tmp_path))
    from tests.fakes import ScriptedProvider

    answer_question("Absent topic?", FakeRetriever([]), ScriptedProvider(), settings)
    broken = FakeRetriever([])
    broken.fail = True
    with pytest.raises(RetrievalUnavailable):
        answer_question("Absent topic?", broken, ScriptedProvider(), settings)
    tool = module("trace_tool")
    monkeypatch.setattr(tool.safe_paths, "ALLOWED_ROOTS", (*tool.safe_paths.ALLOWED_ROOTS, tmp_path))
    rows = list(tool.read_traces([str(tmp_path)]))
    summary = module("trace_summary").summarize(rows)
    assert summary["queries"] == 2 and summary["errors"] == 1
    assert summary["abstention_rate"] == 1
    assert summary["cache"]["hit_rate"] is None
    assert summary["latency_ms"]["total"]["count"] == 2


def test_valid_owned_injection_is_neutralised_in_actual_model_evidence(tmp_path):
    from app.schemas import Passage

    path = Path(__file__).resolve().parents[2] / "corpus/batch-b/injected-policy.md"
    passage = Passage(
        chunk_id="owned-injected",
        text=path.read_text(),
        source=POLICY.source,
        section=POLICY.section,
        page=POLICY.page,
        score=0.9,
        doc_id="a3-injected",
    )
    settings = Settings(relevance_floor=0.45, trace_dir=str(tmp_path))
    provider = OllamaProvider(
        settings,
        httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200, json={"message": {"content": good_answer().model_dump_json()}}
                )
            )
        ),
    )
    response = answer_question(
        "What safety rule?", FakeRetriever([passage]), provider, settings
    ).response
    context = response.evidence["attempts"][0]["context"][0]["text"]
    assert "Ignore previous instructions" not in context
    record = json.loads(next(tmp_path.glob("*.jsonl")).read_text())
    assert record["guardrails"]["passages_neutralised"] > 0


def test_secret_is_redacted_before_actual_transport():
    settings = replace(Settings(), llm_api_key="private-key-123")
    trace = Trace(settings)
    token = current.set(trace)
    try:
        from app.providers.llm.prompt import build_messages

        assert "private-key-123" not in str(build_messages("private-key-123", []))
    finally:
        current.reset(token)


def test_invalid_requests_still_emit_one_terminal_trace(tmp_path, monkeypatch):
    monkeypatch.setenv("TRACE_DIR", str(tmp_path))
    monkeypatch.setenv("RETRIEVER", "stub")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        assert client.post("/api/ask", json={"question": "x"}).status_code == 422
        assert (
            client.post(
                "/api/ask", content="{broken", headers={"Content-Type": "application/json"}
            ).status_code
            == 422
        )
    records = [json.loads(line) for line in next(tmp_path.glob("*.jsonl")).read_text().splitlines()]
    assert len(records) == 2
    assert all(r["status"] == "error" and r["http_status"] == 422 for r in records)


def test_summary_window_is_half_open_and_missing_stage_is_not_zero():
    summary = module("trace_summary")
    rows = [
        {
            "ts": "2026-11-22T10:00:00Z",
            "cache": {"result": "bypass"},
            "response": {"answered_from_context": False},
            "latency_ms": {"total": 20},
        },
        {
            "ts": "2026-11-22T11:00:00Z",
            "cache": {"result": "hit"},
            "response": {"answered_from_context": True},
            "latency_ms": {"total": 30},
        },
    ]
    report = summary.summarize(rows, "2026-11-22T10:00:00Z", "2026-11-22T11:00:00Z")
    assert report["queries"] == 1 and report["abstention_rate"] == 1
    assert "generate" not in report["latency_ms"]
    assert report["cache"]["bypass"] == 1


def test_query_context_freezes_generation_across_publication():
    from app.retrieval.chroma import ChromaRetriever
    from unittest.mock import MagicMock
    retriever = ChromaRetriever(Settings())
    collection = MagicMock()
    collection.query.return_value = {'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
    retriever.active = MagicMock(return_value=(collection, {'dimension': 2, 'generation': 'original', 'versions': '2026'}))
    retriever.embed = lambda question: [1., 0.]
    trace = Trace(Settings())
    token = current.set(trace)
    try:
        vector, generation = retriever.query_context('Current policy?')
        retriever.retrieve('Current policy?', 5, vector)
        assert generation == trace.record['collection']['generation'] == 'original'
        assert retriever.active.call_count == 1
    finally:
        current.reset(token)


def test_replaced_embedding_artifact_fails_before_embedding_transport():
    from app.retrieval.chroma import ChromaRetriever
    calls = []
    def handler(request):
        calls.append(request.method)
        return httpx.Response(200, json={'models': [{'name': 'nomic-embed-text:latest', 'digest': 'b'*64}]})
    trace = Trace(Settings())
    trace.snapshot = (None, {'embed_model_digest': 'a'*64})
    token = current.set(trace)
    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        with patch('app.retrieval.chroma.httpx.Client', return_value=client):
            with pytest.raises(ValueError, match='digest mismatch'):
                ChromaRetriever(Settings()).embed('Current policy?')
        assert calls == ['GET']
    finally:
        current.reset(token)


def test_stdout_envelope_and_persisted_trace_deduplicate(tmp_path, monkeypatch):
    record = {'trace_id': 'one', 'ts': '2026-11-22T10:00:00Z', 'cache': {'result': 'bypass'}}
    (tmp_path / 'file.jsonl').write_text(json.dumps(record) + '\n')
    stdout = {**record, 'logger': 'rahbar.trace', 'level': 'INFO', 'msg': 'query trace', 'request_id': 'one'}
    (tmp_path / 'stdout.log').write_text(json.dumps(stdout) + '\n')
    tool = module('trace_tool')
    monkeypatch.setattr(tool.safe_paths, 'ALLOWED_ROOTS', (*tool.safe_paths.ALLOWED_ROOTS, tmp_path))
    assert len(list(tool.read_traces([str(tmp_path)]))) == 1
