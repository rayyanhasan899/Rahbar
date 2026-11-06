import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "runner", Path(__file__).parents[1] / "run_eval.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
ref = {"source": "policy.pdf", "section": "1.21", "page": 2}


def test_recall_deduplicates_and_obeys_rank():
    other = {"source": "fees.pdf", "section": "2"}
    assert runner.recall_at_k([ref, ref, other], [ref, ref], 5) == 0.5
    assert runner.recall_at_k([ref], [other, ref], 1) == 0
    assert runner.recall_at_k([], [], 5) is None


def test_citation_page_forgery_is_invalid():
    assert (
        runner.citation_validity(
            {"citations": [{**ref, "page": 9}], "retrieved": [ref]}
        )
        == 0
    )
    assert runner.citation_validity({"citations": [ref], "retrieved": [ref]}) == 1
    assert runner.citation_validity({"citations": [], "retrieved": [ref]}) is None


def test_summary_excludes_abstain_from_recall_and_weights_citations():
    rows = [
        {
            "type": "ordinary",
            "relevant": [ref],
            "response": {
                "retrieved": [ref],
                "citations": [ref],
                "answered_from_context": True,
            },
        },
        {
            "type": "abstain",
            "must_abstain": True,
            "relevant": [],
            "response": {
                "retrieved": [],
                "citations": [],
                "answered_from_context": False,
            },
        },
    ]
    result = runner.summarise(rows)
    assert result["recall_at_5"] == 1 and result["abstention_correctness"] == 1
    assert result["by_type"]["abstain"]["recall_at_5"] is None
    assert runner.gate(result, {"recall_at_5": 1}) == []


@pytest.mark.parametrize(
    "recall,citation,abstain,passes",
    [
        (0.75, 0.95, 1.0, True),
        (0.749, 0.95, 1.0, False),
        (0.8, 0.949, 1.0, False),
        (0.8, 1.0, 0.5, False),
    ],
)
def test_gate_boundaries(recall, citation, abstain, passes):
    result = {
        "recall_at_5": recall,
        "citation_validity": citation,
        "abstention_correctness": abstain,
        "must_abstain_count": 2,
    }
    assert (not runner.gate(result, {"recall_at_5": 0.8})) is passes


def test_missing_measurements_fail_closed():
    assert runner.gate({"recall_at_5": None, "citation_validity": None}, None)
    with pytest.raises(ValueError):
        runner.summarise([])
