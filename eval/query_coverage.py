#!/usr/bin/env python3
"""Query coverage (Part E2, paper 4.2.7): do the golden questions resemble real usage?

    python eval/coverage.py --threshold T --min-share S
        [--live eval/live_queries.jsonl] [--golden eval/golden.jsonl]

For each live query, the most similar golden question (cosine of the pinned embedding
model, query prefix). The share at or above T is the coverage. Uncovered queries are
grouped into topics (single-link clustering at --group-threshold) and each topic is
named by its most frequent words. Exit 1 when coverage is below S. T and S have no
defaults: choose them from the score distribution and justify them in the report.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HERE, RESULTS, Services, confined, cosine, percentile, read_jsonl, stamp  # noqa: E402

STOP = set(
    "a an and are as at be by can do does for from how i if in is it my of on or the to "
    "what when where which who will with you your me we our there this that than get".split()
)


def nearest(live_vecs, golden_vecs) -> list[tuple[int, float]]:
    out = []
    for vector in live_vecs:
        scores = [cosine(vector, g) for g in golden_vecs]
        best = max(range(len(scores)), key=scores.__getitem__)
        out.append((best, scores[best]))
    return out


def group(indices: list[int], vectors, threshold: float) -> list[list[int]]:
    """Single-link clustering: two queries share a topic when a chain of pairs at or
    above the threshold connects them."""
    parent = {i: i for i in indices}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for x, i in enumerate(indices):
        for j in indices[x + 1 :]:
            if cosine(vectors[i], vectors[j]) >= threshold:
                parent[find(i)] = find(j)
    groups: dict[int, list[int]] = {}
    for i in indices:
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=len, reverse=True)


def topic_name(texts: list[str]) -> str:
    words = Counter(
        w for t in texts for w in set(re.findall(r"[a-z][a-z-]+", t.lower())) if w not in STOP
    )
    return " ".join(w for w, _ in words.most_common(3)) or "misc"


def analyse(live: list[dict], golden: list[dict], live_vecs, golden_vecs,
            threshold: float, group_threshold: float) -> dict:
    pairs = nearest(live_vecs, golden_vecs)
    rows = [
        {"id": q.get("id"), "query": q["query"], "expected_topic": q.get("expected_topic"),
         "nearest_golden": golden[g]["id"], "nearest_question": golden[g]["question"],
         "score": round(s, 4), "covered": s >= threshold}
        for q, (g, s) in zip(live, pairs)
    ]
    uncovered = [i for i, r in enumerate(rows) if not r["covered"]]
    topics = [
        {"topic": topic_name([rows[i]["query"] for i in members]),
         "queries": [rows[i]["query"] for i in members]}
        for members in group(uncovered, live_vecs, group_threshold)
    ]
    scores = [r["score"] for r in rows]
    return {
        "threshold": threshold,
        "group_threshold": group_threshold,
        "live_queries": len(rows),
        "golden_questions": len(golden),
        "covered": len(rows) - len(uncovered),
        "coverage": (len(rows) - len(uncovered)) / len(rows) if rows else None,
        "score_distribution": {
            "min": min(scores, default=None), "p25": percentile(scores, 25),
            "median": percentile(scores, 50), "p75": percentile(scores, 75),
            "max": max(scores, default=None),
        },
        "uncovered_topics": topics,
        "rows": rows,
    }


def main() -> int:
    env = os.environ.get
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--live", type=Path, default=HERE / "live_queries.jsonl")
    parser.add_argument("--golden", type=Path, default=Path(env("GOLDEN", HERE / "golden.jsonl")))
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--min-share", type=float, required=True)
    parser.add_argument("--group-threshold", type=float, default=0.7)
    parser.add_argument("--ollama", default=env("OLLAMA_URL", "http://localhost:11434"))
    parser.add_argument("--embed-model", default=env("EMBED_MODEL", "nomic-embed-text"))
    parser.add_argument("--results-dir", type=Path, default=Path(env("RESULTS_DIR", RESULTS)))
    parser.add_argument("--label", default="coverage")
    args = parser.parse_args()
    live, golden = read_jsonl(confined(args.live)), read_jsonl(confined(args.golden))
    results_dir = confined(args.results_dir)
    services = Services("", args.ollama)
    live_vecs = services.embed([q["query"] for q in live], args.embed_model, "query")
    golden_vecs = services.embed([q["question"] for q in golden], args.embed_model, "query")
    result = analyse(live, golden, live_vecs, golden_vecs, args.threshold, args.group_threshold)
    result["label"], result["stamp"] = args.label, stamp()
    results_dir.mkdir(parents=True, exist_ok=True)
    out = results_dir / f"coverage-{result['stamp']}-{args.label}.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("live queries:", result["live_queries"], "golden questions:", result["golden_questions"])
    print("coverage at threshold", args.threshold, ":", result["covered"], "/",
          result["live_queries"], "=", round(result["coverage"], 4))
    print("score distribution:", result["score_distribution"])
    for topic in result["uncovered_topics"]:
        print("uncovered topic:", topic["topic"], "(", len(topic["queries"]), "queries )")
        for query in topic["queries"]:
            print("    -", query)
    print("written:", out)
    ok = result["coverage"] is not None and result["coverage"] >= args.min_share
    print("COVERAGE OK" if ok else "COVERAGE BELOW " + str(args.min_share))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
