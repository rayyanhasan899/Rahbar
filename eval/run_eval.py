#!/usr/bin/env python3
"""Score a running RAHBAR against a golden set, and gate CI on the result (section 5).

    python eval/run_eval.py --api http://<ingress>                 # your corpus
    python eval/run_eval.py --api ... --golden eval/fixtures/golden.fixture.yaml
    python eval/run_eval.py --api ... --update-baseline            # after a deliberate improvement

Exit code 0 when every gate passes, 1 when any fails. CI relies on that exit code.

Scores exact source/section references, micro-averages citation validity and
fails closed on missing measurements. Unit tests cover gate boundaries.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import httpx
import yaml

HERE = Path(__file__).resolve().parent

# The gate from section 5.4. Change these only with a reason written in docs/PIPELINE.md.
MAX_RECALL5_DROP = 0.05  # recall@5 may fall at most 5 points below the baseline
MIN_CITATION_VALIDITY = 0.95  # at least 95% of citations must match retrieved passages
REQUIRED_ABSTENTION = 1.0  # every must-abstain question must be declined


def load_golden(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    questions = data.get("questions") or []
    if not questions:
        sys.exit(f"no questions in {path}")
    return questions


def ask(client: httpx.Client, api: str, question: str) -> dict:
    """POST one question and return the AskResponse as a dict (see api/app/schemas.py)."""
    response = client.post(f"{api.rstrip('/')}/api/ask", json={"question": question})
    response.raise_for_status()
    return response.json()


def recall_at_k(relevant: list[dict], retrieved: list[dict], k: int) -> float | None:
    """Fraction of the relevant (source, section) pairs found in the top k retrieved.
    Return None when the question has no relevant passages (must-abstain questions)."""
    if k < 1:
        raise ValueError("k must be positive")
    if not relevant:
        return None

    def key(item):
        return (str(item.get("source", "")), str(item.get("section", "")))

    wanted = {key(r) for r in relevant}
    found = {key(r) for r in retrieved[:k]}
    return len(wanted & found) / len(wanted)


def citation_validity(response: dict) -> float | None:
    """Fraction of the response's citations that match a passage in response['retrieved'].
    Return None when there are no citations."""
    citations = response.get("citations") or []
    if not citations:
        return None
    retrieved = response.get("retrieved") or []

    def matches(c):
        return any(
            c.get("source") == r.get("source")
            and c.get("section") == r.get("section")
            and (c.get("page") is None or c.get("page") == r.get("page"))
            for r in retrieved
        )

    return sum(matches(c) for c in citations) / len(citations)


def summarise(rows: list[dict]) -> dict:
    """Overall recall@3, recall@5, citation validity and abstention correctness, plus
    recall@5 broken down by question type. This dict becomes results.json."""
    if not rows:
        raise ValueError("cannot evaluate an empty run")
    scored = []
    valid, total = 0, 0
    missing = 0
    abstain_total, abstain_correct = 0, 0
    for row in rows:
        response = row["response"]
        citations = response.get("citations") or []
        validity = citation_validity(response)
        total += len(citations)
        valid += round((validity or 0) * len(citations))
        missing += int(response.get("answered_from_context") is True and not citations)
        if row.get("must_abstain"):
            abstain_total += 1
            abstain_correct += int(response.get("answered_from_context") is False)
        scored.append(
            {
                **row,
                "recall_at_3": recall_at_k(
                    row["relevant"], response.get("retrieved", []), 3
                ),
                "recall_at_5": recall_at_k(
                    row["relevant"], response.get("retrieved", []), 5
                ),
                "citation_validity": validity,
            }
        )

    def mean(group, key):
        values = [r[key] for r in group if r[key] is not None]
        return sum(values) / len(values) if values else None

    by_type = {
        kind: {
            "recall_at_3": mean(
                [r for r in scored if r["type"] == kind], "recall_at_3"
            ),
            "recall_at_5": mean(
                [r for r in scored if r["type"] == kind], "recall_at_5"
            ),
        }
        for kind in sorted({r["type"] for r in scored})
    }
    return {
        "recall_at_3": mean(scored, "recall_at_3"),
        "recall_at_5": mean(scored, "recall_at_5"),
        "by_type": by_type,
        "citation_validity": valid / total if total else None,
        "citation_count": total,
        "missing_citations": missing,
        "abstention_correctness": abstain_correct / abstain_total
        if abstain_total
        else None,
        "must_abstain_count": abstain_total,
        "must_abstain_failures": abstain_total - abstain_correct,
        "rows": scored,
    }


def gate(results: dict, baseline: dict | None) -> list[str]:
    """Return one message per failed gate (section 5.4); an empty list means pass."""
    failures = []
    recall = results.get("recall_at_5")
    citation = results.get("citation_validity")
    if not isinstance(recall, (float, int)) or not math.isfinite(recall):
        failures.append("recall@5 is missing or nonfinite")
    if baseline is None:
        failures.append("baseline is missing; establish one explicitly")
    elif isinstance(recall, (float, int)):
        old = baseline.get("recall_at_5")
        if not isinstance(old, (float, int)) or not math.isfinite(old):
            failures.append("baseline recall@5 is invalid")
        elif recall + MAX_RECALL5_DROP + 1e-12 < old:
            failures.append("recall@5 fell more than five percentage points")
    if (
        not isinstance(citation, (float, int))
        or not math.isfinite(citation)
        or citation < 0.95
    ):
        failures.append("citation validity is missing or below 95%")
    if results.get("missing_citations", 0):
        failures.append("an answered response has no citations")
    if (
        not results.get("must_abstain_count")
        or results.get("abstention_correctness") != 1.0
    ):
        failures.append("must-abstain cases missing or not all refused")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate RAHBAR against a golden set."
    )
    parser.add_argument(
        "--api", required=True, help="base URL, e.g. http://192.168.49.2"
    )
    parser.add_argument(
        "--host", help="Host header, when your Ingress rule names a host"
    )
    parser.add_argument("--golden", type=Path, default=HERE / "golden.yaml")
    parser.add_argument("--baseline", type=Path, default=HERE / "baseline.json")
    parser.add_argument("--out", type=Path, default=HERE / "results.json")
    parser.add_argument("--timeout", type=float, default=300.0, help="bounded per-request timeout in seconds")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="write these results as the new baseline",
    )
    args = parser.parse_args()

    questions = load_golden(args.golden)
    rows = []
    headers = {"Host": args.host} if args.host else {}
    with httpx.Client(timeout=args.timeout, headers=headers) as client:
        for q in questions:
            started = time.perf_counter()
            response = ask(client, args.api, q["question"])
            rows.append(
                {
                    "id": q["id"],
                    "type": q.get("type", "ordinary"),
                    "must_abstain": bool(q.get("must_abstain", False)),
                    "relevant": q.get("relevant") or [],
                    "expect": q.get("expect"),
                    "response": response,
                    "seconds": round(time.perf_counter() - started, 2),
                }
            )
            print(f"  {q['id']:<5} {rows[-1]['seconds']:>6.2f}s  {q['question'][:60]}")

    try:
        results = summarise(rows)
        baseline = (
            json.loads(args.baseline.read_text()) if args.baseline.exists() else None
        )
        failures = gate(results, results if args.update_baseline else baseline)
    except NotImplementedError as exc:
        print(f"\nnot implemented yet: {exc}")
        return 2

    results["golden"] = str(args.golden)
    results["questions"] = len(rows)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nresults written to {args.out}")
    if args.update_baseline and not failures:
        args.baseline.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"baseline updated: {args.baseline}")

    if failures:
        print("\nGATE FAILED")
        for message in failures:
            print(f"  - {message}")
        return 1
    print("\ngate passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
