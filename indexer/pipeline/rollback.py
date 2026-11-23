"""Locked rollback of one verified document family; invocation never reembeds."""
from __future__ import annotations
import argparse
import json

from .config import get_settings
from .embed import model_digest
from .incremental import rollback
from .run import writer_lock
from .snapshots import ChromaSnapshots


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--doc-id")
    group.add_argument("--unpin", metavar="DOC_ID")
    parser.add_argument("--version")
    args = parser.parse_args()
    if bool(args.doc_id) != bool(args.version):
        parser.error("--doc-id requires --version; --unpin does not accept --version")
    settings = get_settings()
    with writer_lock(settings.index_lock_path):
        result = rollback(settings, ChromaSnapshots(settings), args.doc_id or args.unpin,
                          args.version, model_digest(settings))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
