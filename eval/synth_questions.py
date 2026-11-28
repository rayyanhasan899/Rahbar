#!/usr/bin/env python3
"""Propose synthetic golden questions from chunks of the active collection (Part B0).

    python eval/synth_questions.py --n 20 [--seed 7]

Writes eval/synthetic-candidates.jsonl with reviewed=false. Nothing goes into the
golden set until a person has checked the question against its PDF page, fixed it,
set reviewed=true and copied it into eval/golden.jsonl.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HERE, Services, write_jsonl  # noqa: E402

SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string"},
        "answer": {"type": "string"},
        "answerable_from_passage": {"type": "boolean"},
    },
    "required": ["question", "answer", "answerable_from_passage"],
}
PROMPT = (
    "You write test questions for a university policy assistant. Read the passage and "
    "write ONE question a student might ask that this passage alone answers, and the short "
    "answer. Use the student's own words, not the passage's wording. If the passage has no "
    "answerable policy fact (a table of contents, a heading), set answerable_from_passage "
    "to false. Reply with JSON only."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--seed", type=int, default=int(os.environ.get("SEED", "42")))
    parser.add_argument("--out", type=Path, default=HERE / "synthetic-candidates.jsonl")
    parser.add_argument("--chroma", default=os.environ.get("CHROMA_URL", "http://localhost:8001"))
    parser.add_argument("--ollama", default=os.environ.get("OLLAMA_URL", "http://localhost:11434"))
    parser.add_argument("--collection", default=os.environ.get("CHROMA_COLLECTION", "rahbar"))
    parser.add_argument("--model", default=os.environ.get("LLM_MODEL", "llama3.2:3b"))
    args = parser.parse_args()
    services = Services("", args.ollama, args.chroma, args.collection)
    rows = []
    for number, chunk in enumerate(services.sample_chunks(args.n, args.seed), 1):
        reply = services.chat_json(
            args.model,
            [{"role": "system", "content": PROMPT},
             {"role": "user", "content": "Passage:\n" + chunk["text"]}],
            SCHEMA,
            args.seed,
        )
        if not reply.get("answerable_from_passage"):
            print("skipped (no fact):", chunk["chunk_id"])
            continue
        rows.append(
            {
                "id": f"s{number:02d}",
                "question": reply["question"],
                "origin": "synthetic",
                "reviewed": False,
                "kind": "answerable",
                "hard_reason": None,
                "relevant": [
                    {"source": chunk.get("source"), "section": chunk.get("section"),
                     "page": chunk.get("page")}
                ],
                "expect": reply["answer"],
                "generated_from_chunk": chunk["chunk_id"],
                "generator": {"model": args.model, "seed": args.seed},
            }
        )
        print("proposed", rows[-1]["id"], "|", reply["question"])
    write_jsonl(args.out, rows)
    print("wrote", len(rows), "candidates to", args.out, "(reviewed=false)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
