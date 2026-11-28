#!/usr/bin/env python3
"""End-to-end level: faithfulness, abstention, citations, latency (Part B3).

suite.py calls judge() and score(). On its own:

    python eval/end_to_end.py --agreement eval/results/suite-<stamp>-baseline.json

compares the judge's verdicts with eval/hand_labels.jsonl ({"id": ..., "verdict": ...},
labelled by a person before looking at the judge) and prints the agreement rate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HERE, citation_validity, mean, percentile, read_jsonl  # noqa: E402

VERDICTS = ("supported", "partial", "unsupported")
SCORE = {"supported": 1.0, "partial": 0.5, "unsupported": 0.0}
SCHEMA = {
    "type": "object",
    "properties": {"verdict": {"type": "string", "enum": list(VERDICTS)},
                   "reason": {"type": "string"}},
    "required": ["verdict", "reason"],
}


def judge(services, model: str, seed: int, question: str, answer: str,
          passages: list[str]) -> dict:
    evidence = "\n\n".join(
        f"BEGIN PASSAGE {n}\n{text}\nEND PASSAGE {n}" for n, text in enumerate(passages, 1)
    )
    messages = [
        {"role": "system", "content": (HERE / "judge_prompt.txt").read_text(encoding="utf-8")},
        {"role": "user",
         "content": f"Passages:\n{evidence or '(none)'}\n\nQuestion: {question}"
                    f"\n\nAnswer: {answer}"},
    ]
    reply = services.chat_json(model, messages, SCHEMA, seed)
    verdict = reply.get("verdict") if reply.get("verdict") in VERDICTS else "unsupported"
    return {"verdict": verdict, "reason": str(reply.get("reason", ""))}


def score(rows: list[dict]) -> dict:
    """rows: one per golden question with response, seconds, cache and (if answered) judge."""
    answered = [r for r in rows if r["response"].get("answered_from_context")]
    judged = [r for r in answered if r.get("judge")]
    unanswerable = [r for r in rows if r["kind"] == "unanswerable"]
    answerable = [r for r in rows if r["kind"] != "unanswerable"]
    cites = [c for r in rows for c in (r["response"].get("citations") or [])]
    valid = sum(
        round((citation_validity(r["response"]) or 0) * len(r["response"].get("citations") or []))
        for r in rows
    )
    seconds = [r["seconds"] for r in rows]
    misses = [r["seconds"] for r in rows if r.get("cache") != "HIT"]
    return {
        "faithfulness": mean(SCORE[r["judge"]["verdict"]] for r in judged),
        "judged_answers": len(judged),
        "unsupported_rate": (
            sum(r["judge"]["verdict"] == "unsupported" for r in judged) / len(judged)
            if judged else None
        ),
        "abstention_correctness": (
            sum(not r["response"].get("answered_from_context") for r in unanswerable)
            / len(unanswerable) if unanswerable else None
        ),
        "unanswerable_questions": len(unanswerable),
        "false_abstention_rate": (
            sum(not r["response"].get("answered_from_context") for r in answerable)
            / len(answerable) if answerable else None
        ),
        "citation_validity": valid / len(cites) if cites else None,
        "citations": len(cites),
        "answered_without_citation": sum(not r["response"].get("citations") for r in answered),
        "latency_p50_seconds": percentile(seconds, 50),
        "latency_p95_seconds": percentile(seconds, 95),
        "latency_p95_seconds_cache_misses": percentile(misses, 95),
        "cache_hits": sum(r.get("cache") == "HIT" for r in rows),
    }


def agreement(rows: list[dict], labels: list[dict]) -> dict:
    by_id = {r["id"]: r for r in rows if r.get("judge")}
    pairs = [(lab["verdict"], by_id[lab["id"]]["judge"]["verdict"])
             for lab in labels if lab["id"] in by_id]
    confusion = {h: {j: 0 for j in VERDICTS} for h in VERDICTS}
    for human, machine in pairs:
        confusion[human][machine] += 1
    return {
        "labelled": len(pairs),
        "agreement": sum(h == m for h, m in pairs) / len(pairs) if pairs else None,
        "confusion_human_by_judge": confusion,
        "unmatched_labels": [lab["id"] for lab in labels if lab["id"] not in by_id],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--agreement", type=Path, required=True, help="a suite result file")
    parser.add_argument("--labels", type=Path, default=HERE / "hand_labels.jsonl")
    args = parser.parse_args()
    result = json.loads(args.agreement.read_text(encoding="utf-8"))
    report = agreement(result["rows"], read_jsonl(args.labels))
    print("labelled answers:", report["labelled"], "agreement:", report["agreement"])
    for human, row in report["confusion_human_by_judge"].items():
        print("  human", human.ljust(11), "judge:", row)
    if report["unmatched_labels"]:
        print("labels without a judged answer:", report["unmatched_labels"])
    out = args.agreement.with_name(args.agreement.stem + "-agreement.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("written:", out)
    return 0 if report["labelled"] >= 8 else 1


if __name__ == "__main__":
    sys.exit(main())
