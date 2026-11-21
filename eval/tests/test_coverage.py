"""Part E coverage with toy vectors."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import coverage  # noqa: E402


def test_coverage_share_and_topics():
    golden_rows = [{"id": "g1", "question": "attendance rule"},
                   {"id": "g2", "question": "gpa rule"}]
    live = [{"query": "attendance needed"}, {"query": "gpa needed"},
            {"query": "wifi password reset"}, {"query": "wifi router reset"}]
    gv = [[1, 0, 0], [0, 1, 0]]
    lv = [[0.95, 0.1, 0], [0.1, 0.95, 0], [0, 0, 1], [0.05, 0, 1]]
    r = coverage.analyse(live, golden_rows, lv, gv, threshold=0.9, group_threshold=0.9)
    assert r["covered"] == 2 and r["coverage"] == 0.5
    assert len(r["uncovered_topics"]) == 1
    assert "wifi" in r["uncovered_topics"][0]["topic"]
    assert r["rows"][0]["nearest_golden"] == "g1"
