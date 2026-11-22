"""Replay immutable request-time model evidence without querying the current index.

Usage: python scripts/trace_tool.py show TRACE_ID [files-or-directories ... | -]
Directories contribute *.jsonl and *.log files. With no paths, read ./traces.
JSONL is streamed, each line is limited to 8 MiB and 100,000 unique records are
allowed. Non-trace JSON log entries are ignored; malformed JSON fails visibly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterator, TextIO

MAX_LINE_BYTES = 8 * 1024 * 1024
MAX_RECORDS = 100_000


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False)


def prompt_hash(messages: list[dict]) -> str:
    return hashlib.sha256(canonical(messages).encode("utf-8")).hexdigest()


def _lines(handle: TextIO, source: str) -> Iterator[tuple[int, str]]:
    number = 0
    while line := handle.readline(MAX_LINE_BYTES + 1):
        number += 1
        if len(line.encode("utf-8")) > MAX_LINE_BYTES:
            raise ValueError(f"{source}:{number}: trace line exceeds 8 MiB")
        yield number, line


def read_traces(paths: list[str] | None = None, stdin: TextIO | None = None) -> Iterator[dict]:
    """Yield unique traces; a reused ID with different recorded evidence is an error."""
    selected = paths or ["traces"]
    sources: list[Path | None] = []
    for name in selected:
        if name == "-":
            if None in sources:
                raise ValueError("stdin may only be supplied once")
            sources.append(None)
            continue
        path = Path(name)
        if path.is_dir():
            sources.extend(sorted({*path.rglob("*.jsonl"), *path.rglob("*.log")}))
        elif path.is_file():
            sources.append(path)
        else:
            raise ValueError("trace input does not exist: " + name)
    seen: dict[str, str] = {}
    for path in sources:
        handle = path.open(encoding="utf-8") if path is not None else (stdin or sys.stdin)
        source = str(path) if path is not None else "stdin"
        try:
            for number, line in _lines(handle, source):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line, parse_constant=lambda token: (_ for _ in ()).throw(
                        ValueError("nonfinite JSON value " + token)))
                except (json.JSONDecodeError, ValueError) as exc:
                    raise ValueError(f"{source}:{number}: malformed JSON: {exc}") from exc
                if not isinstance(value, dict):
                    raise ValueError(f"{source}:{number}: JSON log entry must be an object")
                record = value.get("trace", value)
                if not isinstance(record, dict):
                    raise ValueError(f"{source}:{number}: trace must be an object")
                if "trace_id" not in record:
                    if value.get("logger") == "rahbar.trace":
                        raise ValueError(f"{source}:{number}: trace log is missing trace_id")
                    continue
                record = {k: v for k, v in record.items() if k not in {"logger", "level", "msg", "request_id"}}
                trace_id = record["trace_id"]
                if not isinstance(trace_id, str) or not trace_id or len(trace_id) > 512:
                    raise ValueError(f"{source}:{number}: invalid trace_id")
                fingerprint = hashlib.sha256(canonical(record).encode("utf-8")).hexdigest()
                if trace_id in seen:
                    if seen[trace_id] != fingerprint:
                        raise ValueError("conflicting records for trace_id " + trace_id)
                    continue
                if len(seen) >= MAX_RECORDS:
                    raise ValueError("trace input exceeds 100,000 unique records; split the input")
                seen[trace_id] = fingerprint
                yield record
        finally:
            if path is not None:
                handle.close()


def reconstruct(record: dict) -> dict:
    """Verify every attempt's exact messages; no generation is invented on cache hits."""
    cache = record.get("cache", {})
    evidence = record
    if cache.get("result") == "hit":
        evidence = record.get("provenance")
        if not isinstance(evidence, dict):
            raise ValueError("cache hit has no original immutable model evidence")
        evidence = evidence.get("evidence", evidence)
        if not isinstance(evidence, dict):
            raise ValueError("invalid cache provenance evidence")
    attempts = evidence.get("attempts", [])
    if not isinstance(attempts, list) or len(attempts) > 16:
        raise ValueError("invalid or excessive model attempts")
    for index, attempt in enumerate(attempts, 1):
        if not isinstance(attempt, dict):
            raise ValueError("invalid attempt " + str(index))
        messages = attempt.get("messages")
        if (not isinstance(messages, list) or not messages
                or any(not isinstance(m, dict) or not isinstance(m.get("role"), str)
                       or not isinstance(m.get("content"), str) for m in messages)):
            raise ValueError("missing exact messages for attempt " + str(index))
        if attempt.get("prompt_sha256") != prompt_hash(messages):
            raise ValueError("prompt hash mismatch for attempt " + str(index))
        if not isinstance(attempt.get("context"), list):
            raise ValueError("missing sanitized context for attempt " + str(index))
    response = record.get("response") or {}
    execution = evidence.get("execution") or {}
    if not attempts and response.get("answered_from_context") is True and execution.get("kind") != "stub":
        raise ValueError("answered trace has no reconstructable model attempt")
    if attempts and evidence.get("prompt_sha256") is not None:
        if (evidence["prompt_sha256"] != attempts[-1]["prompt_sha256"]
                or evidence.get("prompt") != attempts[-1]["messages"]):
            raise ValueError("last prompt and attempt evidence disagree")
    return {
        "trace_id": record["trace_id"], "cache": cache,
        "origin_trace_id": evidence.get("trace_id", record["trace_id"]),
        "embedding": evidence.get("embedding"), "collection": evidence.get("collection"),
        "attempts": attempts,
        "context": attempts[-1]["context"] if attempts else execution.get("context", []),
        "prompt": attempts[-1]["messages"] if attempts else None,
        "prompt_sha256": attempts[-1]["prompt_sha256"] if attempts else None,
        "hashes_verified": len(attempts),
        "model_invocation": "recorded_original" if attempts else execution.get("kind", "none_recorded"),
        "response": record.get("response"), "guardrails": record.get("guardrails"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    show = sub.add_parser("show", help="verify and print exact recorded model context/prompts")
    show.add_argument("trace_id")
    show.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    try:
        found = None
        for record in read_traces(args.paths):
            if record["trace_id"] == args.trace_id:
                found = record
        if found is None:
            raise ValueError("trace_id not found: " + args.trace_id)
        print(json.dumps(reconstruct(found), ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, TypeError) as exc:
        print("trace_tool: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
