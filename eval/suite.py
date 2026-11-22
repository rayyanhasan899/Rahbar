#!/usr/bin/env python3
"""The Part B suite in one command: module, component and end-to-end levels.

    python eval/suite.py --label baseline
    python eval/suite.py --label typo-noise --typos
    python eval/suite.py --compare eval/results/A.json eval/results/B.json

Writes eval/results/suite-<UTC stamp>-<label>.json, the same name with .md (the summary
table) and latest-<label>.json. Every setting comes from a flag or an environment
variable, so the Kubernetes Job (k8s/eval-job.yaml) runs the same code.

Requests bypass the answer cache without clearing shared Redis; cached answers make latency
and the stochasticity comparison meaningless, and the result counts them.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import end_to_end  # noqa: E402
import module_embedding  # noqa: E402
from common import (  # noqa: E402
    HERE,
    RESULTS,
    Services,
    mean,
    ndcg_at_k,
    read_jsonl,
    recall_at_k,
    reciprocal_rank,
    stamp,
    with_typos,
)

COMPONENT = ("recall_at_3", "recall_at_5", "mrr", "ndcg_at_5")


def ask_all(services: Services, golden: list[dict], typos_seed: int | None = None) -> list[dict]:
    rows = []
    for q in golden:
        question = q["question"]
        if typos_seed is not None:
            question = with_typos(question, q["id"], typos_seed)
        response, seconds, cache = services.ask(question)
        rows.append(
            {
                "id": q["id"],
                "kind": q.get("kind", "answerable"),
                "origin": q.get("origin"),
                "question": question,
                "relevant": q.get("relevant") or [],
                "expect": q.get("expect"),
                "trace_id": response.get("request_id"),
                "response": response,
                "seconds": round(seconds, 3),
                "cache": cache,
            }
        )
        print(" ", q["id"].ljust(6), str(round(seconds, 2)).rjust(7), "s", cache.ljust(4),
              "answered" if response.get("answered_from_context") else "declined", "|",
              question[:60], flush=True)
    return rows


def component(rows: list[dict]) -> dict:
    scored = []
    for r in rows:
        if r["kind"] == "unanswerable":
            continue
        retrieved = r["response"].get("retrieved") or []
        r["recall_at_3"] = recall_at_k(retrieved, r["relevant"], 3)
        r["recall_at_5"] = recall_at_k(retrieved, r["relevant"], 5)
        r["mrr"] = reciprocal_rank(retrieved, r["relevant"])
        r["ndcg_at_5"] = ndcg_at_k(retrieved, r["relevant"], 5)
        scored.append(r)
    result: dict = {m: mean(r[m] for r in scored) for m in COMPONENT}
    result["questions"] = len(scored)
    result["by_kind"] = {
        kind: {m: mean(r[m] for r in scored if r["kind"] == kind) for m in COMPONENT}
        for kind in sorted({r["kind"] for r in scored})
    }
    return result


def add_judgements(services: Services, rows: list[dict], model: str, seed: int) -> None:
    for r in rows:
        if not r["response"].get("answered_from_context"):
            continue
        import hashlib
        evidence = r["response"].get("evidence") or {}
        attempts = evidence.get("attempts") or []
        if not attempts:
            raise ValueError("answer lacks immutable request-time model evidence")
        attempt = attempts[-1]
        raw = json.dumps(attempt["messages"], sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        if hashlib.sha256(raw.encode()).hexdigest() != attempt["prompt_sha256"]:
            raise ValueError("request-time prompt hash mismatch")
        texts = [p["text"] for p in attempt["context"]]
        r["judge"] = end_to_end.judge(services, model, seed, r["question"],
                                       r["response"]["answer"], texts)
        r["judge"]["passages_found"] = len(texts)



def fmt(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def markdown(result: dict) -> str:
    m, c, e = result["module"], result["component"], result["end_to_end"]
    lines = [
        f"# Suite {result['label']} ({result['stamp']})",
        "",
        f"Golden set: {result['settings']['golden']} ({result['settings']['questions']} "
        f"questions), seed {result['settings']['seed']}, API {result['settings']['api']}, "
        f"collection {result['settings']['collection']}.",
        "",
        "| Level | Metric | Value |",
        "|---|---|---|",
    ]
    if m:
        s, sp, d = m["similarity"], m["speed"], m["determinism"]
        for name, value in (
            ("paraphrase mean cosine", s["paraphrase_mean_cosine"]),
            ("unrelated mean cosine", s["unrelated_mean_cosine"]),
            ("gap", s["gap"]),
            ("ms per chunk (mean)", sp["ms_per_chunk_mean"]),
            ("determinism max abs difference", d["max_abs_difference"]),
        ):
            lines.append(f"| module (embedding) | {name} | {fmt(value)} |")
    for name in COMPONENT:
        lines.append(f"| component (retrieval) | {name} | {fmt(c[name])} |")
    if result.get("component_typos"):
        for name in COMPONENT:
            lines.append(
                f"| component, typo queries | {name} | {fmt(result['component_typos'][name])} |"
            )
    for name in (
        "faithfulness", "judged_answers", "abstention_correctness", "false_abstention_rate",
        "citation_validity", "latency_p50_seconds", "latency_p95_seconds", "cache_hits",
    ):
        lines.append(f"| end-to-end | {name} | {fmt(e[name])} |")
    return "\n".join(lines) + "\n"


def flatten(result: dict) -> dict[str, float]:
    flat: dict[str, float] = {}
    m = result.get("module") or {}
    if m:
        flat["module.gap"] = m["similarity"]["gap"]
        flat["module.paraphrase_mean_cosine"] = m["similarity"]["paraphrase_mean_cosine"]
        flat["module.unrelated_mean_cosine"] = m["similarity"]["unrelated_mean_cosine"]
        flat["module.ms_per_chunk"] = m["speed"]["ms_per_chunk_mean"]
        flat["module.determinism_max_diff"] = m["determinism"]["max_abs_difference"]
    for key in COMPONENT:
        flat["component." + key] = result["component"][key]
    for key, value in result["end_to_end"].items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            flat["end_to_end." + key] = value
    return flat


def compare(a: dict, b: dict) -> list[tuple[str, float | None, float | None, float | None]]:
    fa, fb = flatten(a), flatten(b)
    rows = []
    for key in sorted(set(fa) | set(fb)):
        x, y = fa.get(key), fb.get(key)
        rows.append((key, x, y, None if x is None or y is None else y - x))
    return rows


def main() -> int:
    env = os.environ.get
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--compare", nargs=2, type=Path, metavar=("A", "B"))
    parser.add_argument("--label", default=env("LABEL", "run"))
    parser.add_argument("--golden", type=Path, default=Path(env("GOLDEN", HERE / "golden.jsonl")))
    parser.add_argument("--pairs", type=Path, default=HERE / "embedding-pairs.jsonl")
    parser.add_argument("--results-dir", type=Path, default=Path(env("RESULTS_DIR", RESULTS)))
    parser.add_argument("--api", default=env("API_URL", "http://localhost:8000"))
    parser.add_argument("--host", default=env("API_HOST", ""), help="Host header for an Ingress")
    parser.add_argument("--ollama", default=env("OLLAMA_URL", "http://localhost:11434"))
    parser.add_argument("--chroma", default=env("CHROMA_URL", "http://localhost:8001"))
    parser.add_argument("--collection", default=env("CHROMA_COLLECTION", "rahbar"))
    parser.add_argument("--embed-model", default=env("EMBED_MODEL", "nomic-embed-text"))
    judge = env("JUDGE_MODEL", env("LLM_MODEL", "llama3.2:3b"))
    parser.add_argument("--judge-model", default=judge)
    parser.add_argument("--seed", type=int, default=int(env("SEED", "42")))
    parser.add_argument("--typos", action="store_true", help="also run seeded typo queries")
    parser.add_argument("--skip-module", action="store_true")
    parser.add_argument("--chunk-sample", type=int, default=48)
    args = parser.parse_args()

    if args.compare:
        a, b = (json.loads(p.read_text(encoding="utf-8")) for p in args.compare)
        head = [a["label"][:14].rjust(14), b["label"][:14].rjust(14), "diff".rjust(10)]
        print("metric".ljust(44), *head)
        for key, x, y, d in compare(a, b):
            print(key.ljust(44), fmt(x).rjust(14), fmt(y).rjust(14), fmt(d).rjust(10))
        return 0

    golden = read_jsonl(args.golden)
    from golden_check import problems
    errors = problems(golden)
    if errors:
        print("Golden preflight failed:", *errors, sep="\n")
        return 2
    services = Services(args.api, args.ollama, args.chroma, args.collection, args.host)
    print("asking", len(golden), "questions at", args.api)
    rows = ask_all(services, golden)
    add_judgements(services, rows, args.judge_model, args.seed)
    import hashlib
    evidence = [r['response'].get('evidence', {}) for r in rows]
    indexes = [e.get('collection', {}) for e in evidence]
    pins = {json.dumps(i, sort_keys=True) for i in indexes}
    if len(pins) != 1 or not indexes or not indexes[0].get('corpus_sha256'):
        raise ValueError('missing or changing request-time index provenance; rerun after verified ingestion')
    index = indexes[0]
    if not evidence[0].get('embedding', {}).get('digest'):
        raise ValueError('embedding digest missing')
    provenance = {'golden_sha256': hashlib.sha256(args.golden.read_bytes()).hexdigest(),
                  'pairs_sha256': hashlib.sha256(args.pairs.read_bytes()).hexdigest(),
                  'seed': args.seed, 'corpus_sha256': index['corpus_sha256'],
                  'embedding_digest': evidence[0]['embedding']['digest'],
                  'judge_model': args.judge_model, 'index': index,
                  'pipeline': evidence[0].get('pipeline', {})}
    result = {
        "provenance": provenance,
        "label": args.label,
        "stamp": stamp(),
        "settings": {
            "golden": str(args.golden),
            "questions": len(golden),
            "seed": args.seed,
            "api": args.api,
            "collection": args.collection,
            "embed_model": args.embed_model,
            "judge_model": args.judge_model,
        },
        "module": None if args.skip_module else module_embedding.run(
            services, args.embed_model, args.pairs, args.chunk_sample, args.seed
        ),
        "component": component(rows),
        "end_to_end": end_to_end.score(rows),
        "rows": rows,
    }
    if args.typos:
        print("asking again with seeded typos")
        typo_rows = ask_all(services, golden, typos_seed=args.seed)
        result["component_typos"] = component(typo_rows)
        result["typo_rows"] = typo_rows
    if result["end_to_end"]["cache_hits"]:
        print("WARNING:", result["end_to_end"]["cache_hits"], "unexpected cache hits; check bypass header")

    args.results_dir.mkdir(parents=True, exist_ok=True)
    base = args.results_dir / f"suite-{result['stamp']}-{args.label}"
    base.with_suffix(".json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    base.with_suffix(".md").write_text(markdown(result), encoding="utf-8")
    latest = "baseline-candidate" if args.label == "baseline" else args.label
    shutil.copyfile(base.with_suffix(".json"), args.results_dir / f"latest-{latest}.json")
    print()
    print(markdown(result))
    print("written:", base.with_suffix(".json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
