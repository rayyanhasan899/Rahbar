"""Part C release gate rules."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gate  # noqa: E402


def result(recall5, faith, p95, abst, cites, label="x"):
    return {"label": label, "component": {"recall_at_5": recall5},
            "end_to_end": {"faithfulness": faith, "latency_p95_seconds": p95,
                           "abstention_correctness": abst, "citation_validity": cites, "answered_without_citation": 0}}


THRESHOLDS = {"max_recall5_drop": 0.02, "min_faithfulness": 0.8,
              "max_p95_latency_seconds": 30, "abstention_not_below_baseline": True,
              "min_citation_validity": 0.95}


def test_gate_passes_at_the_boundaries():
    base = result(0.80, 0.9, 20, 1.0, 1.0)
    cand = result(0.78, 0.8, 30, 1.0, 0.95)
    assert all(ok for _, ok, _ in gate.rules(base, cand, THRESHOLDS))


@pytest.mark.parametrize("cand,failing", [
    (result(0.77, 0.9, 20, 1.0, 1.0), "recall@5"),
    (result(0.80, 0.79, 20, 1.0, 1.0), "faithfulness"),
    (result(0.80, 0.9, 31, 1.0, 1.0), "p95 latency"),
    (result(0.80, 0.9, 20, 0.8, 1.0), "abstention"),
    (result(0.80, 0.9, 20, 1.0, 0.9), "citation validity"),
    (result(None, 0.9, 20, 1.0, 1.0), "recall@5"),
])
def test_gate_fails_each_rule(cand, failing):
    base = result(0.80, 0.9, 20, 1.0, 1.0)
    failed = [name for name, ok, _ in gate.rules(base, cand, THRESHOLDS) if not ok]
    assert failed == [failing]


def test_gate_fails_when_a_threshold_is_not_set():
    base = result(0.80, 0.9, 20, 1.0, 1.0)
    unset = {**THRESHOLDS, "min_faithfulness": None}
    failed = [name for name, ok, _ in gate.rules(base, base, unset) if not ok]
    assert set(failed) == {"faithfulness", "bounded min_faithfulness"}


@pytest.mark.parametrize("value", [float('nan'), float('inf'), -1, 2])
def test_nonfinite_and_out_of_range_thresholds_fail(value):
    base = result(.8, .9, 20, 1., 1.)
    assert not all(ok for _, ok, _ in gate.rules(base, base, {**THRESHOLDS, 'min_faithfulness': value}))


def test_missing_uncited_measurement_fails_closed():
    base = result(.8, .9, 20, 1., 1.)
    del base['end_to_end']['answered_without_citation']
    assert not all(ok for _, ok, _ in gate.rules(base, base, THRESHOLDS))

def test_comparability_rejects_missing_or_different_corpus():
    assert not all(ok for _, ok, _ in gate.comparable({}, {}))
    provenance = {'golden_sha256': 'g', 'pairs_sha256': 'p', 'seed': 42,
                  'corpus_sha256': 'c', 'embedding_digest': 'e', 'judge_model': 'j',
                  'pipeline': {'seed': 42}}
    assert all(ok for _, ok, _ in gate.comparable({'provenance': provenance}, {'provenance': provenance}))
    changed = {**provenance, 'corpus_sha256': 'different'}
    assert not all(ok for _, ok, _ in gate.comparable({'provenance': provenance}, {'provenance': changed}))


def test_candidate_cannot_create_its_own_missing_baseline(tmp_path, monkeypatch):
    import job
    monkeypatch.setenv('RESULTS_DIR', str(tmp_path))
    monkeypatch.setenv('LABEL', 'candidate')
    monkeypatch.setenv('CREATE_BASELINE', 'true')
    monkeypatch.setattr(job.subprocess, 'call', lambda *args: pytest.fail('should refuse before model calls'))
    assert job.main() == 2
    assert not (tmp_path / 'latest-baseline.json').exists()


def test_all_levels_are_required_for_release():
    assert gate.measured({}) is False
    assert gate.measured({'module': None, 'component': {'recall_at_5': 1}}) is False


def test_measured_rate_values_cannot_exceed_one():
    record = {'module': {'similarity': {'gap': .5}, 'speed': {'ms_per_chunk_mean': 2},
                         'determinism': {'max_abs_difference': 0}},
              'component': {'recall_at_3': 1, 'recall_at_5': 1, 'mrr': 1, 'ndcg_at_5': 1},
              'end_to_end': {'faithfulness': 1, 'citation_validity': 1,
                            'abstention_correctness': 1, 'latency_p95_seconds': 2}}
    assert gate.measured(record)
    record['component']['mrr'] = 2
    assert not gate.measured(record)
