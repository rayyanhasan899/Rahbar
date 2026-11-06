"""Page-at-a-time extraction, OCRing pages without a usable text layer."""

from __future__ import annotations
import re
import os
from html.parser import HTMLParser
from pathlib import Path
from .models import Document, Page


class TextHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "nav"}:
            self.hidden += 1
        if tag in {"p", "div", "tr", "h1", "h2", "h3", "li", "br"}:
            self.parts.append("\n")
        if tag in {"td", "th"}:
            self.parts.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav"}:
            self.hidden = max(0, self.hidden - 1)
        if tag in {"p", "tr", "h1", "h2", "h3", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def extract(path: str, doc_version: str, superseded: bool) -> Document:
    file = Path(path)
    doc = Document(file.name, doc_version, superseded)
    if file.suffix.lower() == ".pdf":
        import pdfplumber
        import pytesseract
        from pdf2image import convert_from_path

        with pdfplumber.open(file) as pdf:
            for number, page in enumerate(pdf.pages, 1):
                text = page.extract_text(layout=False) or ""
                if len(page.edges) >= 4:
                    tables = page.extract_tables()
                    for table in tables:
                        rows = [
                            " | ".join((cell or "").replace("\n", " ") for cell in row)
                            for row in table
                            if any(cell for cell in row)
                        ]
                        if rows:
                            text += f"\n\n## Table on page {number}\n" + "\n".join(rows)
                ocr = len(re.sub(r"\W", "", text)) < 10
                if ocr:
                    os.environ.setdefault("OMP_THREAD_LIMIT", "1")
                    images = convert_from_path(
                        file, dpi=200, first_page=number, last_page=number, thread_count=1
                    )
                    try:
                        text = pytesseract.image_to_string(images[0], timeout=120)
                    finally:
                        for image in images:
                            image.close()
                doc.pages.append(Page(file.name, number, text, ocr))
    elif file.suffix.lower() in {".html", ".htm"}:
        parser = TextHTML()
        parser.feed(file.read_text(encoding="utf-8"))
        doc.pages.append(Page(file.name, 1, "".join(parser.parts)))
    elif file.suffix.lower() in {".md", ".txt"}:
        text = file.read_text(encoding="utf-8")
        if file.suffix.lower() == ".md":
            text = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.S)
        doc.pages.append(Page(file.name, 1, text))
    else:
        raise ValueError(f"unsupported document type: {file.suffix}")
    return doc
