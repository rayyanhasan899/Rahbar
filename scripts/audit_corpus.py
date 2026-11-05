"""Cache inspected extraction without committing third-party document text."""

from __future__ import annotations
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "indexer"))
from pipeline.extract import extract  # noqa: E402
from pipeline.clean import clean  # noqa: E402


def main() -> None:
    cache = ROOT / ".venv/extracted"
    cache.mkdir(parents=True, exist_ok=True)
    rows = []
    for entry in json.loads((ROOT / "corpus/raw/_index.json").read_text()):
        path = ROOT / "corpus/raw" / entry["file"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise ValueError(f"checksum mismatch: {path.name}")
        dest = cache / (entry["file"] + ".json")
        fingerprint = cache / (entry["file"] + ".sha256")
        extraction_key = hashlib.sha256(
            actual.encode()
            + (ROOT / "indexer/pipeline/extract.py").read_bytes()
            + (ROOT / "indexer/pipeline/clean.py").read_bytes()
        ).hexdigest()
        if (
            not dest.exists()
            or not fingerprint.exists()
            or fingerprint.read_text() != extraction_key
        ):
            print("Extracting", path.name, flush=True)
            doc = clean(extract(str(path), entry["doc_version"], entry["superseded"]))
            dest.write_text(json.dumps(asdict(doc), ensure_ascii=False))
            fingerprint.write_text(extraction_key)
        data = json.loads(dest.read_text())
        rows.append(
            {
                "file": path.name,
                "sha256": actual,
                "pages": len(data["pages"]),
                "ocr_pages": [p["page"] for p in data["pages"] if p["ocr"]],
                "empty_after_extraction": [
                    p["page"] for p in data["pages"] if not p["text"].strip()
                ],
            }
        )
    target = ROOT / "docs/evidence/extraction-audit.json"
    target.write_text(json.dumps(rows, indent=2) + "\n")
    print(f"Audited {len(rows)} selected documents")


if __name__ == "__main__":
    main()
