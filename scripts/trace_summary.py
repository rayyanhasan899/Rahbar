"""Summarize unique query traces within an optional UTC [since, until) window.

Rates use completed boolean answer outcomes for abstention, hit/(hit+miss) for
cache lookups, and all selected queries for flagged-injection rate. Errors and
cache bypass/unknown outcomes are separate. Missing stages/scores never become
zero samples. Millisecond stage p50/p95 use nearest-rank percentiles (ceil(p*N)).
All stage values must be finite/nonnegative. Input bounds and JSONL rules are
shared with trace_tool; this performs no model/service calls.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import datetime, timezone
import json
import math
import sys

try:
    from .trace_tool import read_traces
except ImportError:  # Direct `python scripts/trace_summary.py` execution.
    from trace_tool import read_traces


def timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValueError("timestamp must be ISO8601 with an explicit timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def numeric(value, name: str, *, nonnegative: bool = False) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or (nonnegative and value < 0)):
        raise ValueError("invalid finite numeric " + name)
    return float(value)


def distribution(values: list[float]) -> dict:
    ordered = sorted(values)
    size = len(ordered)
    return {"count": size, "min": ordered[0] if size else None,
            "max": ordered[-1] if size else None,
            "mean": math.fsum(ordered) / size if size else None,
            "p50": ordered[max(0, math.ceil(.50 * size) - 1)] if size else None,
            "p95": ordered[max(0, math.ceil(.95 * size) - 1)] if size else None}


def summarize(records: Iterable[dict], since: str | None = None,
              until: str | None = None) -> dict:
    start = timestamp(since) if since else None
    end = timestamp(until) if until else None
    if start and end and start >= end:
        raise ValueError("since must be earlier than until")
    cache: Counter[str] = Counter()
    stages: dict[str, list[float]] = defaultdict(list)
    scores: list[float] = []
    score_bins: Counter[str] = Counter()
    total = errors = completed = abstained = unknown = flagged = question_flags = 0
    passage_flags = neutralisations = 0
    reasons: Counter[str] = Counter()
    for record in records:
        when = timestamp(record.get("ts", ""))
        if (start and when < start) or (end and when >= end):
            continue
        total += 1
        result = (record.get("cache") or {}).get("result", "unknown")
        cache[result if result in {"hit", "miss", "bypass"} else "unknown"] += 1
        response = record.get("response")
        status = record.get("http_status", 200)
        failed = record.get("status") == "error" or (
            isinstance(status, int) and status >= 400)
        if failed:
            errors += 1
        elif (isinstance(response, dict)
              and isinstance(response.get("answered_from_context"), bool)):
            completed += 1
            if not response["answered_from_context"]:
                abstained += 1
                rails = record.get("guardrails") or {}
                reason = "below_floor" if rails.get("below_relevance_floor") else (
                    str(rails.get("fallback")) if rails.get("fallback") else "declined")
                reasons[reason] += 1
        else:
            unknown += 1
        rails = record.get("guardrails") or {}
        question_flag = rails.get("question_flagged") is True
        passages = numeric(rails.get("passages_neutralised", 0),
                           "passages_neutralised", nonnegative=True)
        if not passages.is_integer():
            raise ValueError("passages_neutralised must be an integer")
        question_flags += int(question_flag)
        passage_flags += int(passages > 0)
        neutralisations += int(passages)
        flagged += int(question_flag or passages > 0)
        retrieved = record.get("retrieved") or []
        if retrieved:
            score = numeric(retrieved[0].get("score"), "top-1 score")
            scores.append(score)
            bucket = ("<0" if score < 0 else "[0,.25)" if score < .25 else
                      "[.25,.5)" if score < .5 else "[.5,.75)" if score < .75 else
                      "[.75,1]" if score <= 1 else ">1")
            score_bins[bucket] += 1
        times = record.get("latency_ms") or {}
        if not isinstance(times, dict) or len(times) > 64:
            raise ValueError("invalid/excessive latency stages")
        for stage, value in times.items():
            if value is None:
                continue
            if stage not in stages and len(stages) >= 64:
                raise ValueError("trace window has more than 64 distinct latency stages")
            stages[stage].append(numeric(value, "latency_ms." + stage, nonnegative=True))
    lookups = cache["hit"] + cache["miss"]
    return {
        "window": {"since": start.isoformat() if start else None,
                   "until": end.isoformat() if end else None, "boundaries": "[since,until) UTC"},
        "queries": total, "completed_answers": completed, "errors": errors,
        "unknown_outcomes": unknown, "abstained": abstained,
        "abstention_rate": abstained / completed if completed else None,
        "abstention_reasons": dict(reasons),
        "cache": {**{key: cache[key] for key in ("hit", "miss", "bypass", "unknown")},
                  "lookups": lookups, "hit_rate": cache["hit"] / lookups if lookups else None},
        "injection": {"flagged_queries": flagged, "question_flagged": question_flags,
                      "queries_with_neutralised_passages": passage_flags,
                      "passage_neutralisations": neutralisations,
                      "flagged_query_rate": flagged / total if total else None},
        "top1_similarity": {**distribution(scores), "histogram": dict(score_bins)},
        "latency_ms": {stage: distribution(values) for stage, values in sorted(stages.items())},
        "aggregation": {"abstention": "false / completed boolean answer outcomes; errors excluded",
                        "cache": "hit / (hit+miss); bypass and unknown excluded",
                        "injection": "flagged unique queries / all selected queries",
                        "percentiles": "nearest rank ceil(p*N), observed samples only",
                        "retrieval": "first retrieved row, not max(score); no cache-origin resampling"},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--since")
    parser.add_argument("--until")
    args = parser.parse_args(argv)
    try:
        result = summarize(read_traces(args.paths), args.since, args.until)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print("trace_summary: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
