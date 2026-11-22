"""Count actual published chunks per verified document, including deleted zero rows."""
from __future__ import annotations
import json

from .config import get_settings
from .datalake import Lake
from .incremental import document_counts, read_ledger
from .snapshots import ChromaSnapshots


def main() -> None:
    settings = get_settings()
    backend = ChromaSnapshots(settings)
    ledger = read_ledger(Lake(settings.datalake_dir, settings.collection), backend)
    if ledger is None:
        raise SystemExit("no published A3 ledger")
    actual = backend.counts(ledger["active_collection"])
    expected = {r["doc_key"]: r["chunks"] for r in document_counts(ledger) if r["chunks"]}
    if actual != expected:
        raise SystemExit("orphan/missing chunks: published store differs from ledger")
    print(json.dumps({"collection": ledger["active_collection"],
                      "generation": ledger["generation"], "orphan_chunks": 0,
                      "documents": [{**r, "actual_chunks": actual.get(r["doc_key"], 0)}
                                    for r in document_counts(ledger)]}))


if __name__ == "__main__":
    main()
