"""Part C release gate rules."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gate  # noqa: E402


def result(recall5, faith, p95, abst, cites, label="x"):
    return {"label": label, "component": {"recall_at_5": recall5},
            "end_to_end": {"faithfulness": faith, "latency_p95_seconds": p95,
                           "abstention_correctness": abst, "citation_validity": cites}}


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
    assert failed == ["faithfulness"]
