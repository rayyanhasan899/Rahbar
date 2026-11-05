"""Section-aware chunks under a reproducible lexical-token budget."""

from __future__ import annotations
import hashlib
import re
from .models import Chunk, Document

TOKEN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def token_count(text: str) -> int:
    return len(TOKEN.findall(text))


def heading(line: str) -> str | None:
    markdown = re.match(r"^#{1,6}\s+(.+?)\s*#*$", line)
    if markdown:
        return markdown[1].strip()
    clause = re.match(r"^(\d+(?:\.\d+)+)\.?\s+\S", line)
    if clause:
        return clause[1]
    title = re.match(r"^(\d+)\.\s+([A-Z][A-Za-z /&-]{2,80})$", line)
    return f"{title[1]}. {title[2]}" if title else None


def chunk(doc: Document, size: int, overlap: int) -> list[Chunk]:
    if size < 2 or not 0 <= overlap < size:
        raise ValueError("size >=2 and 0 <= overlap < size required")
    sections: list[tuple[str, list[tuple[int, str]]]] = []
    section = "Document"
    for page_obj in doc.pages:
        for line in page_obj.text.splitlines():
            found = (
                heading(line.strip())
                if not doc.source.endswith(".md")
                else (heading(line.strip()) if line.lstrip().startswith("#") else None)
            )
            if found:
                section = found
            if not sections or sections[-1][0] != section:
                sections.append((section, []))
            sections[-1][1].append((page_obj.page, line))
    chunks = []
    for section, lines in sections:
        text = "\n".join(line for _, line in lines)
        spans = list(TOKEN.finditer(text))
        if not spans:
            continue
        boundaries = [m.end() for m in re.finditer(r"\n\s*\n|[.!?](?:\s+|$)", text)]
        page_offsets, offset = [], 0
        for page, line in lines:
            page_offsets.append((offset, page))
            offset += len(line) + 1
        start = 0
        while start < len(spans):
            end = min(start + size, len(spans))
            if end < len(spans):
                candidates = [
                    i
                    for i in range(start + max(overlap + 1, size // 2), end + 1)
                    if any(spans[i - 1].end() <= b <= spans[i].start() for b in boundaries)
                ]
                if candidates:
                    end = candidates[-1]
            begin, finish = spans[start].start(), spans[end - 1].end()
            page = next((p for o, p in reversed(page_offsets) if o <= begin), lines[0][0])
            body = text[begin:finish]
            identity = f"{doc.source}|{doc.doc_version}|{section}|{page}|{start}|{body}"
            cid = hashlib.sha256(identity.encode()).hexdigest()[:32]
            chunks.append(
                Chunk(cid, body, doc.source, section, page, doc.doc_version, doc.superseded)
            )
            if end == len(spans):
                break
            start = max(start + 1, end - overlap)
    return chunks
