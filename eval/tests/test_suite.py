"""Part B suite code with fakes: no API, no model, no cluster."""

import json
import math
import sys
from pathlib import Path

import pytest

EVAL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EVAL))

import common  # noqa: E402
import convert_golden  # noqa: E402
import end_to_end  # noqa: E402
import golden_check  # noqa: E402
import suite  # noqa: E402

A = {"source": "rules.pdf", "page": 7, "section": "1.1"}
B = {"source": "rules.pdf", "page": 20, "section": "4.25"}
OTHER = {"source": "fees.pdf", "page": 1, "section": "1"}


def test_recall_mrr_ndcg_on_a_known_ranking():
    retrieved = [OTHER, A, A, OTHER, B]
    relevant = [A, B]
    assert common.recall_at_k(retrieved, relevant, 3) == 0.5
    assert common.recall_at_k(retrieved, relevant, 5) == 1.0
    assert common.reciprocal_rank(retrieved, relevant) == 0.5
    ideal = 1 + 1 / math.log2(3)
    assert common.ndcg_at_k(retrieved, relevant, 5) == pytest.approx(
        (1 / math.log2(3) + 1 / math.log2(6)) / ideal
    )
    assert common.recall_at_k(retrieved, [], 5) is None


def test_page_or_section_match_but_never_another_source():
    assert common.matches({**A, "page": 8}, A)  # same section, chunk starts a page later
    assert common.matches({**A, "section": "Document"}, A)  # same page
    assert not common.matches({**A, "source": "x.pdf"}, A)
    assert not common.matches({**A, "page": 8, "section": "2"}, A)


def test_typos_are_deterministic_and_change_the_query():
    q = "What minimum cumulative GPA is required for graduation?"
    assert common.with_typos(q, "q04", 42, rate=1.0) == common.with_typos(q, "q04", 42, rate=1.0)
    assert common.with_typos(q, "q04", 42, rate=1.0) != q
    assert common.with_typos(q, "q04", 42, rate=0.0) == q


def test_percentile_is_nearest_rank():
    assert common.percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 95) == 10
    assert common.percentile([1, 2, 3, 4], 50) == 2
    assert common.percentile([], 50) is None


def golden(n_human=8, n_syn=8, n_un=5, n_hard=5, extra=0):
    rows = []
    kinds = ["unanswerable"] * n_un + ["hard"] * n_hard
    kinds += ["answerable"] * (n_human + n_syn + extra - len(kinds))
    for i, kind in enumerate(kinds):
        rows.append({
            "id": f"g{i}", "question": "q", "kind": kind,
            "origin": "human" if i < n_human else "synthetic", "reviewed": True,
            "hard_reason": "paraphrase" if kind == "hard" else None,
            "relevant": [] if kind == "unanswerable" else [A],
        })
    return rows


def test_golden_check_minimums():
    assert golden_check.problems(golden(extra=9)) == []
    issues = golden_check.problems(golden(n_human=7, extra=9))
    assert any("human-written: 7" in i for i in issues)
    missing_page = golden(extra=9)
    missing_page[-1]["relevant"] = [{"source": "rules.pdf", "page": None}]
    assert any("physical page" in i for i in golden_check.problems(missing_page))


def test_convert_golden_keeps_ids_and_leaves_pages_to_a_person():
    import yaml

    data = yaml.safe_load((EVAL / "golden.yaml").read_text())
    results = json.loads((EVAL / "results.json").read_text())
    rows = convert_golden.convert(data, results)
    assert [r["id"] for r in rows] == [q["id"] for q in data["questions"]]
    assert all(r["origin"] == "unset" for r in rows)
    answerable = [r for r in rows if r["kind"] == "answerable"]
    assert all(rel["page"] is None for r in answerable for rel in r["relevant"])
    assert any(rel["page_candidates"] for r in answerable for rel in r["relevant"])
    assert sum(r["kind"] == "unanswerable" for r in rows) == 2


def row(qid, kind, answered, retrieved, cites=(), seconds=1.0, verdict=None, cache="MISS"):
    r = {
        "id": qid, "kind": kind, "question": "q",
        "relevant": [] if kind == "unanswerable" else [A],
        "response": {"answered_from_context": answered, "answer": "x", "retrieved": retrieved,
                     "citations": list(cites)},
        "seconds": seconds, "cache": cache,
    }
    if verdict:
        r["judge"] = {"verdict": verdict}
    return r


def sample_rows():
    return [
        row("a", "answerable", True, [A], [A], 2.0, "supported"),
        row("b", "answerable", True, [OTHER, A], [OTHER], 4.0, "partial"),
        row("c", "answerable", False, [OTHER], [], 1.0),
        row("u", "unanswerable", False, [OTHER], [], 0.5),
        row("v", "unanswerable", True, [OTHER], [{"source": "nope"}], 3.0, "unsupported"),
    ]


def test_end_to_end_scores():
    s = end_to_end.score(sample_rows())
    assert s["faithfulness"] == pytest.approx(0.5)
    assert s["unsupported_rate"] == pytest.approx(1 / 3)
    assert s["abstention_correctness"] == 0.5
    assert s["false_abstention_rate"] == pytest.approx(1 / 3)
    assert s["citation_validity"] == pytest.approx(2 / 3)
    assert s["latency_p95_seconds"] == 4.0 and s["cache_hits"] == 0


def test_component_metrics_skip_unanswerable():
    c = suite.component(sample_rows())
    assert c["questions"] == 3
    assert c["recall_at_5"] == pytest.approx(2 / 3)
    assert c["mrr"] == pytest.approx((1 + 0.5 + 0) / 3)


def test_judge_agreement_counts_and_confusion():
    rows = sample_rows()
    labels = [{"id": "a", "verdict": "supported"}, {"id": "b", "verdict": "unsupported"},
              {"id": "zz", "verdict": "supported"}]
    report = end_to_end.agreement(rows, labels)
    assert report["labelled"] == 2 and report["agreement"] == 0.5
    assert report["confusion_human_by_judge"]["unsupported"]["partial"] == 1
    assert report["unmatched_labels"] == ["zz"]


class FakeServices:
    def __init__(self):
        self.asked = []

    def ask(self, question):
        self.asked.append(question)
        import hashlib
        messages = [{"role": "user", "content": "1.1 English is the medium."}]
        hashed = hashlib.sha256(json.dumps(messages, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        retrieved = [{"chunk_id": "c1", **A, "score": 0.8}]
        return ({"request_id": "t" + str(len(self.asked)), "answer": "Yes [rules.pdf / 1.1].",
                 "answered_from_context": True, "citations": [A], "retrieved": retrieved,
                 "evidence": {"attempts": [{"messages": messages, "prompt_sha256": hashed, "context": [{"text": "1.1 English is the medium."}]}]}},
                0.5, "MISS")

    def chunk_texts(self, ids):
        return {i: "1.1 English is the medium." for i in ids}

    def chat_json(self, model, messages, schema, seed):
        assert "English is the medium" in messages[1]["content"]
        return {"verdict": "supported", "reason": "stated"}


def test_suite_rows_carry_trace_ids_and_judgements():
    services = FakeServices()
    question = {"id": "q1", "question": "Which language?", "kind": "answerable", "relevant": [A]}
    rows = suite.ask_all(services, [question])
    suite.add_judgements(services, rows, "judge", 42)
    assert rows[0]["trace_id"] == "t1" and rows[0]["judge"]["verdict"] == "supported"
    assert rows[0]["judge"]["passages_found"] == 1
    typo = suite.ask_all(services, [{"id": "q1", "question": "Which language is used?"}], 42)
    assert typo[0]["question"] == common.with_typos("Which language is used?", "q1", 42)


def test_compare_and_markdown():
    module = {"similarity": {"gap": 0.3, "paraphrase_mean_cosine": 0.8,
                             "unrelated_mean_cosine": 0.5},
              "speed": {"ms_per_chunk_mean": 12.0}, "determinism": {"max_abs_difference": 0.0}}
    rows = sample_rows()
    a = {"label": "a", "stamp": "s", "module": module, "component": suite.component(rows),
         "end_to_end": end_to_end.score(rows),
         "settings": {"golden": "g", "questions": 5, "seed": 42, "api": "x", "collection": "c"}}
    b = json.loads(json.dumps(a))
    b["component"]["recall_at_5"] = 0.5
    diff = dict((k, d) for k, _, _, d in suite.compare(a, b))
    assert diff["component.recall_at_5"] == pytest.approx(0.5 - 2 / 3)
    assert diff["module.gap"] == 0
    text = suite.markdown(a)
    assert "| component (retrieval) | ndcg_at_5 |" in text
    assert "| end-to-end | faithfulness |" in text

def test_golden_preflight_precedes_network_calls(tmp_path, monkeypatch):
    path = tmp_path / 'invalid.jsonl'
    path.write_text('{"id":"invalid","question":"example"}\n')
    monkeypatch.setattr(sys, 'argv', ['suite.py', '--golden', str(path)])
    monkeypatch.setattr(suite, 'Services', lambda *args: pytest.fail('network initialized before validation'))
    assert suite.main() == 2


def test_module_sampling_can_pin_the_request_time_generation(monkeypatch):
    services = object.__new__(common.Services)
    services._active = None
    resolved = []
    monkeypatch.setattr(services, '_collection_id', lambda name: resolved.append(name) or 'immutable-id')
    services.pin_collection('served-generation')
    assert services.active_collection() == 'immutable-id'
    assert resolved == ['served-generation']
