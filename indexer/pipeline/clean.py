"""Conservative cleaning that retains headings, tables and policy structure."""

from __future__ import annotations
import re
import unicodedata
from collections import Counter
from dataclasses import replace
from .models import Document


def clean(doc: Document) -> Document:
    margins: Counter[str] = Counter()
    for page in doc.pages:
        lines = [line.strip() for line in page.text.splitlines() if line.strip()]
        margins.update(set(lines[:2] + lines[-2:]))
    repeated = {
        line
        for line, count in margins.items()
        if len(doc.pages) >= 3
        and count >= max(3, len(doc.pages) * 0.7)
        and not re.match(r"^(#|\d+\.)", line)
    }
    pages = []
    for page in doc.pages:
        lines = []
        for line in unicodedata.normalize("NFKC", page.text).splitlines():
            line = re.sub(r"[^\S\n]+", " ", line).strip()
            if line in repeated or re.fullmatch(r"(?:Page\s+)?\d+(?:\s+of\s+\d+)?", line):
                continue
            lines.append(line)
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
        pages.append(replace(page, text=text))
    return replace(doc, pages=pages)
