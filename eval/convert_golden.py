#!/usr/bin/env python3
"""Convert the Assignment 2 golden set (golden.yaml) to Part B's golden.jsonl.

    python eval/convert_golden.py            # writes eval/golden.jsonl if it does not exist
    python eval/convert_golden.py --force    # overwrite

The physical page is left empty on purpose. `page_candidates` lists the pages of the
chunks that the stored real run (results.json) retrieved for the same source and
section; a person opens the PDF, writes the correct page into `page` and deletes the
candidates. `origin` is "unset" until a person records who wrote each question.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HERE, write_jsonl  # noqa: E402


def candidates(results: dict, qid: str, relevant: dict) -> list[int]:
    row = next((r for r in results.get("rows", []) if r["id"] == qid), None)
    if row is None:
        return []
    pages = {
        int(r["page"])
        for r in row["response"].get("retrieved", [])
        if r.get("source") == relevant.get("source")
        and r.get("section") == relevant.get("section")
        and r.get("page") is not None
    }
    pages |= {
        int(c["page"])
        for c in row["response"].get("citations", [])
        if c.get("source") == relevant.get("source")
        and c.get("section") == relevant.get("section")
        and c.get("page") is not None
    }
    return sorted(pages)


def convert(golden: dict, results: dict) -> list[dict]:
    rows = []
    for q in golden["questions"]:
        unanswerable = bool(q.get("must_abstain"))
        relevant = [
            {
                "source": r["source"],
                "section": str(r["section"]),
                "page": None,
                "page_candidates": candidates(results, q["id"], r),
            }
            for r in q.get("relevant") or []
        ]
        rows.append(
            {
                "id": q["id"],
                "question": q["question"],
                "origin": "unset",
                "reviewed": False,
                "kind": "unanswerable" if unanswerable else "answerable",
                "hard_reason": None,
                "a2_type": q.get("type", "ordinary"),
                "relevant": [] if unanswerable else relevant,
                "expect": q.get("expect"),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--golden", type=Path, default=HERE / "golden.yaml")
    parser.add_argument("--results", type=Path, default=HERE / "results.json")
    parser.add_argument("--out", type=Path, default=HERE / "golden.jsonl")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.out.exists() and not args.force:
        print("exists, not overwritten:", args.out)
        return 1
    golden = yaml.safe_load(args.golden.read_text(encoding="utf-8"))
    results = json.loads(args.results.read_text()) if args.results.exists() else {}
    rows = convert(golden, results)
    write_jsonl(args.out, rows)
    print("wrote", len(rows), "questions to", args.out)
    print("next: set page, origin and reviewed by hand, then run eval/golden_check.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
