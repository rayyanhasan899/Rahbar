"""Four explicit verification results; classification never hides a failed check."""
from __future__ import annotations

import math
import re
from typing import Any

from .models import Document


def check(passed: bool, reason: str) -> dict[str, Any]:
    return {"passed": bool(passed), "reason": reason}


def version_order(value: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", value)
    if not numbers:
        raise ValueError("version/date needs an orderable numeric component")
    return tuple(int(n) for n in numbers)


def initial_checks(meta: dict, doc: Document | None, raw: bytes, error: str,
                   minimum: int) -> dict[str, dict[str, Any]]:
    text = "\n".join(p.text for p in doc.pages) if doc else ""
    meaningful = sum(c.isalnum() for c in text)
    quality = (not error and meaningful >= minimum and bool(text)
               and sum(c.isprintable() or c.isspace() for c in text) / len(text) >= .95
               and text.count("\ufffd") / len(text) < .01
               and meaningful / len(text) >= .35)
    missing = [k for k in ("source", "title", "doc_version")
               if not str(meta.get(k, "")).strip() or str(meta.get(k)).lower() == "unknown"]
    pages = len(doc.pages) if doc else 0
    complete = not missing and pages > 0
    reason = "required metadata and extracted page count present"
    if missing:
        reason = "missing metadata: " + ", ".join(missing)
    elif not pages:
        reason = "no extracted pages"
    declared = meta.get("pages", meta.get("page_count"))
    if declared is not None:
        try:
            if int(declared) != pages:
                complete, reason = False, "declared and extracted page counts differ"
        except (TypeError, ValueError):
            complete, reason = False, "invalid declared page count"
    source = str(meta.get("source", ""))
    if source.lower().endswith(".pdf") and b"%%EOF" not in raw[-1024:]:
        complete, reason = False, "PDF has no terminal EOF marker"
    if source.lower().endswith((".md", ".txt")):
        ending = text.rstrip().rstrip("*_`) ")
        if ending and ending[-1] not in ".!?;:|":
            complete, reason = False, "text ends mid-sentence or without a closing delimiter"
    try:
        version_order(str(meta.get("doc_version", "")))
        recency = check(True, "version is orderable; family recency evaluated after verification")
    except ValueError as exc:
        recency = check(False, str(exc))
    return {
        "quality": check(quality, error or (
            "usable extracted text" if quality else "empty, short, garbled or failed extraction")),
        "completeness": check(complete, reason),
        "recency": recency,
        "uniqueness": check(False, "not evaluated: earlier verification must pass"),
    }


def cosine(a: list[float], b: list[float]) -> float:
    if not a or len(a) != len(b) or any(not math.isfinite(x) for x in a + b):
        raise ValueError("invalid document embedding")
    norm = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
    if not norm:
        raise ValueError("zero document embedding")
    return sum(x*y for x, y in zip(a, b)) / norm
