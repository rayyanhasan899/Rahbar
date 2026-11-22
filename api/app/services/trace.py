"""Request-local immutable evidence, bounded JSONL persistence and safe diagnostics."""
from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import threading
import time
from typing import Any
import uuid

from ..config import Settings
from ..logjson import request_id_var
from ..routes.metrics import STAGE_SECONDS, TRACE_WRITES

current: ContextVar[Trace | None] = ContextVar("trace", default=None)
_write_lock = threading.Lock()
log = logging.getLogger("rahbar.trace")


def prompt_hash(messages: list[dict]) -> str:
    return hashlib.sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True,
                                   separators=(",", ":")).encode()).hexdigest()


def safe(value: Any, secrets: tuple[str, ...] = ()) -> Any:
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return re.sub(r"(?i)\bBearer\s+[A-Za-z0-9_.-]+", "Bearer [REDACTED]", value)
    if isinstance(value, list):
        return [safe(v, secrets) for v in value]
    if isinstance(value, dict):
        return {k: safe(v, secrets) for k, v in value.items()
                if k.lower() not in {"authorization", "api_key", "llm_api_key", "reasoning"}}
    return value


class Trace:
    def __init__(self, settings: Settings, question: str = "") -> None:
        self.settings = settings
        self.secrets = (settings.llm_api_key,)
        self.started = time.perf_counter()
        self.finished = False
        self.snapshot: Any = None
        rid = request_id_var.get()
        self.record: dict[str, Any] = {
            "schema_version": 1, "trace_id": rid if rid != "-" else uuid.uuid4().hex,
            "ts": datetime.now(timezone.utc).isoformat(), "query": safe(question, self.secrets),
            "rewritten_query": safe(question, self.secrets),
            "embedding": {"model": settings.embed_model, "digest": None},
            "collection": {"name": settings.collection, "active_collection": None,
                           "generation": None}, "retrieved": [], "filters": None,
            "reranked_order": [], "reranker": "not_applied", "attempts": [],
            "prompt": None, "prompt_sha256": None, "response": None, "citations": [],
            "model": {"provider": settings.llm_provider, "name": settings.llm_model,
                      "temperature": settings.temperature, "seed": settings.seed},
            "guardrails": {"question_flagged": False, "passages_neutralised": 0, "actions": []},
            "latency_ms": {}, "cache": {"result": "bypass"}, "status": "pending",
        }

    def action(self, name: str, **fields: Any) -> None:
        self.record["guardrails"]["actions"].append({"action": name, **safe(fields, self.secrets)})

    def stage(self, name: str, start: float) -> None:
        elapsed = time.perf_counter() - start
        self.record["latency_ms"][name] = self.record["latency_ms"].get(name, 0.) + elapsed * 1000
        STAGE_SECONDS.labels(stage=name).observe(elapsed)

    def attempt(self, messages: list[dict], context: list[dict], provider: str,
                parameters: dict) -> None:
        # Providers call this with the actual payload immediately before transport.
        self.record["attempts"].append({"messages": messages, "context": context,
                                       "prompt_sha256": prompt_hash(messages),
                                       "provider": provider, "parameters": parameters})
        self.record["prompt"] = messages
        self.record["prompt_sha256"] = prompt_hash(messages)

    def evidence(self) -> dict:
        from ..providers.llm.prompt import SYSTEM, ANSWER_SCHEMA
        template = prompt_hash([{"system": SYSTEM, "schema": ANSWER_SCHEMA}])
        return {k: self.record[k] for k in ("trace_id", "embedding", "collection", "attempts")} | {
            "execution": self.record.get("execution"),
            "pipeline": {"top_k": self.settings.top_k,
                         "relevance_floor": self.settings.relevance_floor,
                         "provider": self.settings.llm_provider, "llm_model": self.settings.llm_model,
                         "temperature": self.settings.temperature, "seed": self.settings.seed,
                         "prompt_template_sha256": template}}

    def finish(self, status: int = 200) -> None:
        if self.finished:
            return
        self.finished = True
        self.record["http_status"] = status
        self.record["status"] = "error" if status >= 400 else "completed"
        self.stage("total", self.started)
        record = safe(self.record, self.secrets)
        # stdout always retains a record even if the configured volume is full/unavailable.
        record["persistence"] = {"configured": bool(self.settings.trace_dir), "written": False}
        try:
            if self.settings.trace_dir:
                persist(record, self.settings)
                record["persistence"]["written"] = True
                TRACE_WRITES.labels(result="written").inc()
        except (OSError, ValueError, TimeoutError) as exc:
            record["persistence"]["error"] = type(exc).__name__
            TRACE_WRITES.labels(result="error").inc()
        log.info("query trace", extra={k: v for k, v in record.items() if k != "ts"} | {
            "ts": record["ts"]})


def persist(record: dict, settings: Settings) -> None:
    import fcntl
    pod = re.sub(r"[^A-Za-z0-9_.-]", "_", os.environ.get("HOSTNAME", "local"))[:128]
    folder = Path(settings.trace_dir)
    folder.mkdir(parents=True, exist_ok=True)
    record["persistence"]["written"] = True
    data = (json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n").encode()
    record["persistence"]["written"] = False
    if len(data) > settings.trace_max_record_bytes:
        raise ValueError("trace record exceeds configured limit")
    if not _write_lock.acquire(timeout=.1):
        raise TimeoutError("trace writer busy")
    try:
        with (folder / ("traces-" + pod + ".jsonl")).open("ab", buffering=0) as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise TimeoutError("trace process writer busy") from exc
            if os.fstat(handle.fileno()).st_size + len(data) > settings.trace_max_file_bytes:
                raise OSError("trace file budget exhausted; export before rotating")
            if handle.write(data) != len(data):
                raise OSError("short trace write")
            os.fsync(handle.fileno())
    finally:
        _write_lock.release()


def capture_attempt(messages: list[dict], passages: list, provider: str, parameters: dict) -> None:
    trace = current.get()
    if trace is not None:
        trace.attempt(messages, [p.model_dump() for p in passages], provider, parameters)
