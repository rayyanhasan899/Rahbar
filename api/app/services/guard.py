"""Prompt-injection handling (section 3.4).

Two layers. The prompt tells the model that passages and questions are data (see
providers/llm/prompt.py). This module is the second layer: sentences in retrieved
passages that read like instructions to an assistant are replaced before the model
sees them, so a poisoned chunk cannot steer the answer even if the model is weak.
A question that contains such text is only flagged, because the user may still have
a real question in it, and flagged answers are never cached.
"""

from __future__ import annotations

import re

from ..schemas import Passage

REMOVED = "[instruction-like text removed from source]"

# Kept narrow on purpose: handbook text says things like "you are now eligible" or
# "students who ignore the rules", and removing real policy text is worse than
# missing an unusual phrasing, which the prompt layer still covers.
_PATTERNS = [
    r"\b(ignore|disregard|forget|override)\b[^.!?\n]{0,40}\b(instructions?|prompts?)\b",
    r"\b(previous|prior|above|earlier|system)\s+(instructions?|prompts?)\b",
]
_INJECTION = re.compile("|".join(_PATTERNS), re.IGNORECASE)
_SENTENCES = re.compile(r"(?<=[.!?])\s+|\n+")


def looks_like_injection(text: str) -> bool:
    return bool(_INJECTION.search(text))


def neutralise(passages: list[Passage]) -> tuple[list[Passage], int]:
    """Return copies of the passages with instruction-like sentences replaced, and how
    many sentences were replaced. Source, section, page and score are unchanged, so
    citations and recall still line up with what was retrieved."""
    cleaned: list[Passage] = []
    removed = 0
    for passage in passages:
        if not looks_like_injection(passage.text):
            cleaned.append(passage)
            continue
        parts = []
        for sentence in _SENTENCES.split(passage.text):
            if looks_like_injection(sentence):
                parts.append(REMOVED)
                removed += 1
            elif sentence:
                parts.append(sentence)
        cleaned.append(passage.model_copy(update={"text": " ".join(parts)}))
    return cleaned, removed
