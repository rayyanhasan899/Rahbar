#!/usr/bin/env python3
"""Check that eval/golden.jsonl meets Part B's minimums (exit 1 when it does not).

    python eval/golden_check.py [eval/golden.jsonl]

Minimums: 25 questions; 15 answerable with a source and a physical page; 5 unanswerable;
5 hard; 8 written by hand (origin human); 8 synthetic that were reviewed by hand.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HERE, read_jsonl  # noqa: E402

KINDS = {"answerable", "unanswerable", "hard"}
ORIGINS = {"human", "synthetic"}
HARD = {"paraphrase", "multi_chunk", "batch_b"}


def problems(rows: list[dict]) -> list[str]:
    found = []
    ids = Counter(r.get("id") for r in rows)
    found += [f"duplicate id {i}" for i, n in ids.items() if n > 1]
    for r in rows:
        rid = r.get("id", "?")
        if r.get("kind") not in KINDS:
            found.append(f"{rid}: kind must be one of {sorted(KINDS)}")
        if r.get("origin") not in ORIGINS:
            found.append(f"{rid}: origin must be human or synthetic, not {r.get('origin')!r}")
        if r.get("kind") == "hard" and r.get("hard_reason") not in HARD:
            found.append(f"{rid}: hard questions need hard_reason in {sorted(HARD)}")
        if r.get("kind") in {"answerable", "hard"}:
            rel = r.get("relevant") or []
            if not rel or any(not x.get("source") or x.get("page") is None for x in rel):
                found.append(f"{rid}: every relevant entry needs a source and a physical page")
        if r.get("kind") == "unanswerable" and r.get("relevant"):
            found.append(f"{rid}: an unanswerable question has no relevant entries")
    kinds = Counter(r.get("kind") for r in rows)
    human = sum(r.get("origin") == "human" for r in rows)
    synthetic = sum(r.get("origin") == "synthetic" and r.get("reviewed") is True for r in rows)
    for label, have, need in (
        ("questions", len(rows), 25),
        ("answerable", kinds["answerable"], 15),
        ("unanswerable", kinds["unanswerable"], 5),
        ("hard", kinds["hard"], 5),
        ("human-written", human, 8),
        ("reviewed synthetic", synthetic, 8),
    ):
        if have < need:
            found.append(f"{label}: {have} of at least {need}")
    return found


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "golden.jsonl"
    rows = read_jsonl(path)
    issues = problems(rows)
    kinds = Counter(r.get("kind") for r in rows)
    print("questions", len(rows), "answerable", kinds["answerable"], "unanswerable",
          kinds["unanswerable"], "hard", kinds["hard"])
    for issue in issues:
        print("  -", issue)
    print("golden set OK" if not issues else "golden set INCOMPLETE")
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
