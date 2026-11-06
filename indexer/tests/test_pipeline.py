from dataclasses import replace
from unittest.mock import MagicMock

import pytest

from pipeline.chunk import chunk, token_count
from pipeline.clean import clean
from pipeline.config import get_settings
from pipeline.extract import extract
from pipeline.models import Document, Page
from pipeline.store import store


def document(text):
    return Document("test.md", "2026", False, [Page("test.md", 1, text)])


def test_chunk_preserves_sections_pages_and_exact_budget():
    doc = document(
        "## 1. Attendance\n\n"
        + "A complete policy sentence. " * 50
        + "\n## 2. Fees\n\nFee is 10000 PKR."
    )
    pieces = chunk(doc, 30, 5)
    assert len(pieces) > 3
    assert all(token_count(p.text) <= 30 for p in pieces)
    assert pieces[-1].section == "2. Fees"
    assert all(p.page == 1 and p.doc_version == "2026" for p in pieces)
    assert [p.id for p in pieces] == [p.id for p in chunk(doc, 30, 5)]
    assert len({p.id for p in pieces}) == len(pieces)


def test_overlap_and_no_cross_section_leak():
    pieces = chunk(document("## Heading\n" + " ".join(f"word{i}" for i in range(80))), 20, 4)
    assert pieces[0].text.split()[-4:] == pieces[1].text.split()[:4]


@pytest.mark.parametrize("size,overlap", [(1, 0), (10, 10), (10, -1)])
def test_invalid_chunk_settings(size, overlap):
    with pytest.raises(ValueError):
        chunk(document("some text"), size, overlap)


def test_markdown_clauses_stay_under_fixture_heading(tmp_path):
    path = tmp_path / "fixture.md"
    path.write_text("---\ndoc_version: 2026\n---\n## 1. Attendance\n1.1 Attend 80 percent.")
    doc = extract(str(path), "2026", False)
    assert "doc_version" not in doc.pages[0].text
    assert chunk(doc, 100, 10)[0].section == "1. Attendance"


def test_html_keeps_table_values_but_removes_script(tmp_path):
    path = tmp_path / "fees.html"
    path.write_text(
        "<h1>Fees</h1><table><tr><td>BS</td><td>10000</td></tr></table><script>steal()</script>"
    )
    text = extract(str(path), "2026", False).pages[0].text
    assert "BS | 10000" in text and "steal" not in text


def test_clean_does_not_mutate_and_preserves_clauses():
    doc = Document(
        "a.pdf",
        "2026",
        False,
        [Page("a.pdf", n, f"University\n1.21 Attend.\n{n}") for n in [1, 2, 3]],
    )
    result = clean(doc)
    assert all("University" not in p.text and "1.21 Attend." in p.text for p in result.pages)
    assert "University" in doc.pages[0].text


def test_pdf_ocr_only_when_text_layer_missing(monkeypatch, tmp_path):
    import pdfplumber
    import pytesseract
    import pdf2image

    pdf = MagicMock()
    pdf.__enter__.return_value.pages = [MagicMock(), MagicMock()]
    pdf.__enter__.return_value.pages[0].extract_text.return_value = "Real readable policy text"
    pdf.__enter__.return_value.pages[1].extract_text.return_value = ""
    monkeypatch.setattr(pdfplumber, "open", lambda _: pdf)
    render = MagicMock(return_value=[MagicMock()])
    monkeypatch.setattr(pdf2image, "convert_from_path", render)
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *a, **kw: "Recovered scan")
    result = extract(str(tmp_path / "scan.pdf"), "2023", True)
    assert [p.ocr for p in result.pages] == [False, True]
    assert result.pages[1].text == "Recovered scan"
    assert render.call_args.kwargs["first_page"] == 2


def test_ruled_pdf_table_preserves_column_associations(monkeypatch, tmp_path):
    import pdfplumber

    pdf = MagicMock()
    page = MagicMock()
    page.extract_text.return_value = "Grade points in a real table"
    page.edges = [1, 2, 3, 4]
    page.extract_tables.return_value = [[["Grade", "Points"], ["A+", "4.00"]]]
    pdf.__enter__.return_value.pages = [page]
    monkeypatch.setattr(pdfplumber, "open", lambda _: pdf)
    result = extract(str(tmp_path / "table.pdf"), "2026", False)
    assert "Grade | Points\nA+ | 4.00" in result.pages[0].text
    assert result.pages[0].ocr is False


def test_staging_failure_never_publishes(monkeypatch):
    from pipeline import store as module

    client = MagicMock()
    client.create_collection.return_value.add.side_effect = RuntimeError("disk full")
    monkeypatch.setattr(module, "get_client", lambda _: client)
    pieces = chunk(document("## Policy\nA valid policy."), 100, 10)
    with pytest.raises(RuntimeError, match="disk full"):
        store(pieces, [[0.1, 0.2]] * len(pieces), get_settings())
    client.get_or_create_collection.assert_not_called()


def test_publish_records_pin_dimension_and_generation(monkeypatch):
    from pipeline import store as module

    client = MagicMock()
    client.create_collection.return_value.count.return_value = 1
    monkeypatch.setattr(module, "get_client", lambda _: client)
    pieces = chunk(document("## Policy\nA valid policy."), 100, 10)
    assert store(pieces, [[0.1, 0.2]], get_settings()) == 1
    meta = client.get_or_create_collection.return_value.upsert.call_args.kwargs["metadatas"][0]
    assert meta["dimension"] == 2 and meta["embed_model"] == "nomic-embed-text"
    assert meta["active_collection"].startswith("rahbar-") and meta["generation"]


def test_embedding_batches_and_validation(monkeypatch):
    import httpx
    from pipeline.embed import embed

    client_class = httpx.Client
    calls = []

    def handler(request):
        import json

        data = json.loads(request.content)
        calls.append(data)
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2] for _ in data["input"]]})

    monkeypatch.setattr(
        httpx, "Client", lambda **kw: client_class(transport=httpx.MockTransport(handler))
    )
    settings = replace(get_settings(), embed_batch_size=2, ollama_url="http://fake")
    assert len(embed(["a", "b", "c"], settings)) == 3
    assert [len(c["input"]) for c in calls] == [2, 1]
    assert all(c["model"] == settings.embed_model and c["truncate"] is False for c in calls)


def test_writer_lock_excludes_another_process_and_releases(tmp_path):
    import subprocess
    import sys
    from pipeline.run import writer_lock

    lock_path = str(tmp_path / "shared.lock")
    code = """import fcntl,sys
with open(sys.argv[1], 'a') as handle:
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit(75)
"""
    with writer_lock(lock_path):
        assert subprocess.run([sys.executable, "-c", code, lock_path]).returncode == 75
    assert subprocess.run([sys.executable, "-c", code, lock_path]).returncode == 0
