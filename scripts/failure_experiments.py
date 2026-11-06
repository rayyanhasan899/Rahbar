"""Reversible A/B/C/E ablations on separate collections; never alter live data."""
from __future__ import annotations
import hashlib
import json
import os
import sys
from bisect import bisect_right
from dataclasses import replace
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "indexer"), str(ROOT / "api"), str(ROOT / "eval")]
from pipeline.chunk import TOKEN, heading  # noqa: E402
from pipeline.config import get_settings  # noqa: E402
from pipeline.embed import embed  # noqa: E402
from pipeline.extract import extract  # noqa: E402
from pipeline.models import Chunk, Document, Page  # noqa: E402
from pipeline.store import get_client, store  # noqa: E402
from app.retrieval.chroma import version_filter  # noqa: E402
from run_eval import recall_at_k  # noqa: E402


def fixed_chunks(doc: Document) -> list[Chunk]:
    """A deliberately bad flat 100-token/zero-overlap chunker.

    Attribute a window to its starting section/page, even when it crosses a
    boundary. This is the realistic defect, not invented relevance labels.
    """
    text, pages, sections = "", [(0, 1)], [(0, "Document")]
    for page in doc.pages:
        pages.append((len(text), page.page))
        for line in page.text.splitlines(keepends=True):
            found = heading(line.strip())
            if found:
                sections.append((len(text), found))
            text += line
        text += "\n"
    spans = list(TOKEN.finditer(text))
    chunks = []
    for start in range(0, len(spans), 100):
        first, last = spans[start].start(), spans[min(start + 99, len(spans) - 1)].end()
        section = sections[bisect_right([x[0] for x in sections], first) - 1][1]
        page = pages[bisect_right([x[0] for x in pages], first) - 1][1]
        key = hashlib.sha256(f"failure-b|{doc.source}|{start}|{text[first:last]}".encode()).hexdigest()[:32]
        chunks.append(Chunk(key, text[first:last], doc.source, section, page, doc.doc_version, doc.superseded))
    return chunks


def main() -> None:
    import pdfplumber
    settings = get_settings()
    out = ROOT / ".venv" / "acceptance" / "failures.json"
    golden = yaml.safe_load((ROOT / "eval/golden.yaml").read_text())["questions"]
    docs = []
    for entry in json.loads((ROOT / "corpus/raw/_index.json").read_text()):
        data = json.loads((ROOT / ".venv/extracted" / (entry["file"] + ".json")).read_text())
        docs.append(Document(data["source"], data["doc_version"], data["superseded"], [Page(**p) for p in data["pages"]]))
    result: dict = {"commit": os.environ.get("IMAGE_TAG"), "scope": "isolated ablation collections; live publication is unchanged"}
    scan = ROOT / "corpus/raw/faculty-entrepreneurship-and-technical-start-ups-policy.pdf"
    with pdfplumber.open(scan) as pdf:
        broken = [len((p.extract_text() or "").strip()) for p in pdf.pages]
    restored = extract(str(scan), "2022-05", False)
    result["A-extraction"] = {"broken_no_ocr_characters": broken, "restored_ocr_characters": [len(p.text.strip()) for p in restored.pages], "restored_ocr_pages": sum(p.ocr for p in restored.pages)}
    out.write_text(json.dumps(result, indent=2))
    client = get_client(settings)
    meta = client.get_collection(settings.collection + "-control").get(ids=["active"])["metadatas"][0]
    reference = client.get_collection(meta["active_collection"])
    probes = yaml.safe_load((ROOT / "eval/failure-probes.yaml").read_text())["questions"]
    texts = [q["question"] for q in golden + probes]
    vectors = dict(zip(texts, embed(texts, settings, purpose="query")))

    def measure(collection, k=5, filtered=True, questions=golden):
        rows = []
        for q in questions:
            vector = vectors[q["question"]]
            where = version_filter(q["question"], str(meta["versions"])) if filtered else None
            hits = collection.query(query_embeddings=[vector], n_results=k, where=where, include=["metadatas", "distances"])
            refs = [dict(m, chunk_id=cid, score=1 - distance) for m, cid, distance in zip(hits["metadatas"][0], hits["ids"][0], hits["distances"][0])]
            rows.append({"id": q["id"], "type": q["type"], "retrieved": refs, "recall": recall_at_k(q["relevant"], refs, k)})
        scored = [r["recall"] for r in rows if r["recall"] is not None]
        return {"k": k, "macro_recall": sum(scored) / len(scored), "rows": rows}

    baseline = measure(reference)
    result["restored-reference"] = {"generation": meta["generation"], "measurement": baseline}
    result["C-top-k"] = {"broken": measure(reference, 1), "restored": baseline}
    # The original golden labels mostly require one clause. Do not pretend k=1
    # degraded their recall when it did not; measure a separate two-clause need.
    result["C-top-k"]["additional_diagnostic"] = {
        "broken": measure(reference, 1, questions=probes),
        "restored": measure(reference, questions=probes),
    }
    result["E-source-filter"] = {"broken_unfiltered": measure(reference, filtered=False), "restored": baseline}
    out.write_text(json.dumps(result, indent=2))
    pieces = [c for doc in docs for c in fixed_chunks(doc)]
    broken_settings = replace(settings, collection="rahbar-failure-b")
    store(pieces, embed([c.text for c in pieces], settings), broken_settings)
    pointer = client.get_collection(broken_settings.collection + "-control").get(ids=["active"])["metadatas"][0]
    bad = client.get_collection(pointer["active_collection"])
    result["B-fixed-chunks"] = {"size": 100, "overlap": 0, "chunks": len(pieces), "broken": measure(bad), "restored": baseline}
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps({"A_pages_lost": sum(n == 0 for n in broken), "restored_recall5": baseline["macro_recall"], "broken_fixed_recall5": result["B-fixed-chunks"]["broken"]["macro_recall"], "broken_top1_recall": result["C-top-k"]["broken"]["macro_recall"]}), flush=True)


if __name__ == "__main__":
    main()
