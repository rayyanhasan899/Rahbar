#!/usr/bin/env python3
"""Choose RELEVANCE_FLOOR from a real evaluation run (section 3.4).

    python eval/run_eval.py --api ... --out eval/results.json
    python scripts/score_margins.py eval/results.json

Prints the best retrieval score for every question. The floor must sit above every
must-abstain question's top score and below the answerable ones; the gap between
the two groups is the margin you have.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main(path: str) -> int:
    root = Path(__file__).resolve().parents[1]
    source = Path(path).resolve()
    if not source.is_relative_to(root) or source.suffix != ".json":
        raise ValueError("measurement input must be a JSON file inside this project")
    rows = json.loads(source.read_text(encoding="utf-8"))["rows"]
    answerable, abstain = [], []
    print(f"{'id':<6}{'type':<11}{'top':>8}  answered")
    for row in rows:
        scores = [r["score"] for r in row["response"].get("retrieved", [])]
        top = max(scores, default=0.0)
        (abstain if row.get("must_abstain") else answerable).append(top)
        answered = row["response"].get("answered_from_context")
        print(f"{row['id']:<6}{row['type']:<11}{top:>8.4f}  {answered}")
    if not answerable or not abstain:
        print("\nneed both answerable and must-abstain questions to suggest a floor")
        return 1
    low, high = min(answerable), max(abstain)
    print(f"\nlowest answerable top score : {low:.4f}")
    print(f"highest must-abstain score  : {high:.4f}")
    if high < low:
        print(f"a floor between them separates the groups, e.g. {(low + high) / 2:.2f}")
    else:
        print("the groups overlap: no floor separates them; record this in PIPELINE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "eval/results.json"))
