#!/usr/bin/env python3
"""Release gate (Part C2): compare a candidate suite result with the baseline.

    python eval/gate.py --baseline eval/results/latest-baseline.json \\
        --candidate eval/results/latest-candidate.json --thresholds eval/gate.yaml

Prints one line per rule and exits 0 when every rule passes, 1 otherwise. A missing
measurement or an unset threshold fails, so the gate never passes by accident.
"""

from __future__ import annotations

import argparse
import math
import json
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import confined  # noqa: E402


def number(value) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def rules(baseline: dict, candidate: dict, t: dict) -> list[tuple[str, bool, str]]:
    bc, cc = baseline["component"], candidate["component"]
    be, ce = baseline["end_to_end"], candidate["end_to_end"]
    out: list[tuple[str, bool, str]] = []

    def rule(name: str, values: dict[str, object], test) -> None:
        nums = {k: number(v) for k, v in values.items()}
        missing = [k for k, v in nums.items() if v is None]
        if missing:
            out.append((name, False, "missing: " + ", ".join(missing)))
        elif any(v is not None and (v < 0 or (name != "p95 latency" and v > 1)) for v in nums.values()):
            out.append((name, False, "measurement or threshold outside valid range"))
        else:
            ok, detail = test(**nums)
            out.append((name, bool(ok), detail))

    rule("recall@5",
         {"drop": t.get("max_recall5_drop"), "old": bc.get("recall_at_5"),
          "new": cc.get("recall_at_5")},
         lambda drop, old, new: (new + drop + 1e-12 >= old,
                                 f"candidate {new:.4f} vs baseline {old:.4f}, allowed drop {drop}"))
    rule("faithfulness",
         {"floor": t.get("min_faithfulness"), "value": ce.get("faithfulness")},
         lambda floor, value: (value >= floor, f"candidate {value:.4f}, minimum {floor}"))
    rule("p95 latency",
         {"limit": t.get("max_p95_latency_seconds"), "value": ce.get("latency_p95_seconds")},
         lambda limit, value: (value <= limit, f"candidate {value:.2f} s, maximum {limit} s"))
    if t.get("abstention_not_below_baseline"):
        rule("abstention",
             {"old": be.get("abstention_correctness"), "new": ce.get("abstention_correctness")},
             lambda old, new: (new + 1e-12 >= old, f"candidate {new:.4f} vs baseline {old:.4f}"))
    rule("citation validity",
         {"floor": t.get("min_citation_validity"), "value": ce.get("citation_validity")},
         lambda floor, value: (value >= floor, f"candidate {value:.4f}, minimum {floor}"))
    for key in ("max_recall5_drop", "min_faithfulness", "min_citation_validity"):
        value = number(t.get(key))
        out.append(("bounded " + key, value is not None and 0 <= value <= 1, "must be finite in [0,1]"))
    latency = number(t.get("max_p95_latency_seconds"))
    out.append(("positive latency limit", latency is not None and latency > 0, "finite positive seconds required"))
    out.append(("no uncited answers", ce.get("answered_without_citation") == 0, "must explicitly measure zero uncited answers"))
    return out



def comparable(baseline: dict, candidate: dict) -> list[tuple[str, bool, str]]:
    old, new = baseline.get('provenance', {}), candidate.get('provenance', {})
    checks = []
    for key in ('golden_sha256', 'pairs_sha256', 'seed', 'corpus_sha256', 'embedding_digest', 'judge_model'):
        ok = key in old and old[key] is not None and old.get(key) == new.get(key)
        checks.append(('comparable ' + key, ok, 'identical non-missing provenance required'))
    checks.append(('comparable pipeline', bool(old.get('pipeline')) and old.get('pipeline') == new.get('pipeline'),
                   'this release supports chunking-only changes; other changes need a reviewed comparison contract'))
    return checks



def measured(result: dict) -> bool:
    paths = [('module', 'similarity', 'gap'), ('module', 'speed', 'ms_per_chunk_mean'),
             ('module', 'determinism', 'max_abs_difference'),
             ('component', 'recall_at_3'), ('component', 'recall_at_5'),
             ('component', 'mrr'), ('component', 'ndcg_at_5'),
             ('end_to_end', 'faithfulness'), ('end_to_end', 'citation_validity'),
             ('end_to_end', 'abstention_correctness'), ('end_to_end', 'latency_p95_seconds')]
    for path in paths:
        value = result
        for key in path:
            if not isinstance(value, dict) or key not in value:
                return False
            value = value[key]
        numeric = number(value)
        if numeric is None:
            return False
        if path[-1] in {"recall_at_3", "recall_at_5", "mrr", "ndcg_at_5", "faithfulness", "citation_validity", "abstention_correctness"} and not 0 <= numeric <= 1:
            return False
        if path[-1] in {"ms_per_chunk_mean", "max_abs_difference", "latency_p95_seconds"} and numeric < 0:
            return False
        if path[-1] == "gap" and not -2 <= numeric <= 2:
            return False
    return True


def main() -> int:
    env = os.environ.get
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--baseline", type=Path, default=env("BASELINE"))
    parser.add_argument("--candidate", type=Path, default=env("CANDIDATE"))
    default_gate = env("GATE_FILE", "eval/gate.yaml")
    parser.add_argument("--thresholds", type=Path, default=Path(default_gate))
    parser.add_argument("--out", type=Path, help="write the decision as JSON")
    args = parser.parse_args()
    if args.baseline is None or args.candidate is None:
        parser.error("--baseline and --candidate are required")
    baseline = json.loads(confined(args.baseline).read_text(encoding="utf-8"))
    candidate = json.loads(confined(args.candidate).read_text(encoding="utf-8"))
    thresholds = yaml.safe_load(confined(args.thresholds).read_text(encoding="utf-8")) or {}
    results = rules(baseline, candidate, thresholds) + comparable(baseline, candidate)
    results.append(("all three levels measured", measured(baseline) and measured(candidate), "missing/nonfinite module/component measurements fail"))
    print("gate:", candidate["label"], "against", baseline["label"], "with", args.thresholds)
    for name, ok, detail in results:
        print("  PASS" if ok else "  FAIL", name.ljust(18), detail)
    passed = all(ok for _, ok, _ in results)
    print("GATE PASSED" if passed else "GATE FAILED")
    if args.out:
        confined(args.out).write_text(json.dumps({
            "baseline": str(args.baseline), "candidate": str(args.candidate),
            "thresholds": thresholds, "passed": passed,
            "rules": [{"rule": n, "passed": ok, "detail": d} for n, ok, d in results],
        }, indent=2), encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
