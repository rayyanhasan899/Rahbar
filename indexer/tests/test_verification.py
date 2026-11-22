from __future__ import annotations
from dataclasses import replace
import math
import unittest
from unittest.mock import patch

from pipeline.config import get_settings
from pipeline.models import Document, Page
from pipeline.snapshots import ChromaSnapshots
from pipeline.verify import cosine, initial_checks


class VerificationTests(unittest.TestCase):
    def checks(self, text="A complete, readable policy sentence. " * 5, **metadata):
        meta = {"source": "rules.md", "title": "Policy", "doc_version": "2026", **metadata}
        doc = Document(meta["source"], "2026", False, [Page(meta["source"], 1, text)])
        return initial_checks(meta, doc, b"fake input", "", 64)

    def test_missing_metadata_and_truncation_report_independent_reasons(self):
        results = self.checks(title="")
        self.assertFalse(results["completeness"]["passed"])
        self.assertIn("title", results["completeness"]["reason"])
        self.assertFalse(self.checks(text="Sentence left unfinished " * 5)
                         ["completeness"]["passed"])

    def test_page_count_and_pdf_tail_checks(self):
        self.assertFalse(self.checks(pages=2)["completeness"]["passed"])
        self.assertFalse(self.checks(pages="invalid")["completeness"]["passed"])
        self.assertFalse(self.checks(source="rules.pdf")["completeness"]["passed"])

    def test_garbled_short_and_failed_extraction_do_not_pass(self):
        self.assertFalse(self.checks(text="\ufffd" * 100)["quality"]["passed"])
        self.assertFalse(self.checks(text="Short.")["quality"]["passed"])
        failed = initial_checks({}, None, b"corrupt", "extraction failed", 64)
        self.assertEqual(set(failed), {"quality", "completeness", "recency", "uniqueness"})
        self.assertFalse(failed["quality"]["passed"])

    def test_version_must_be_orderable(self):
        self.assertFalse(self.checks(doc_version="unknown")["recency"]["passed"])
        self.assertFalse(self.checks(doc_version="spring")["recency"]["passed"])

    def test_invalid_similarity_inputs_and_configuration_fail_closed(self):
        for value in ([0.0, 0.0], [math.nan, 1], [math.inf, 1]):
            with self.assertRaises(ValueError):
                cosine(value, [1., 0.])
        for threshold in (math.nan, math.inf, 0, 1.01):
            with self.assertRaises(ValueError):
                replace(get_settings(), near_dup_threshold=threshold)


class Collection:
    def __init__(self):
        self.rows = {}

    def add(self, ids, documents, metadatas, embeddings):
        for key, meta in zip(ids, metadatas):
            if key in self.rows:
                raise ValueError("duplicate chunk")
            self.rows[key] = meta

    def count(self):
        return len(self.rows)

    def get(self, limit, offset, include):
        return {"ids": list(self.rows)[offset:offset + limit],
                "metadatas": list(self.rows.values())[offset:offset + limit]}


class Client:
    def __init__(self):
        from unittest.mock import MagicMock
        self.collection = Collection()
        self.get_or_create_collection = MagicMock()

    def create_collection(self, *args, **kwargs):
        return self.collection

    def get_collection(self, name):
        return self.collection


class SnapshotAdapterTests(unittest.TestCase):
    def test_real_adapter_checks_document_counts_before_pointer(self):
        client = Client()
        settings = get_settings()
        with patch("pipeline.snapshots.get_client", return_value=client):
            backend = ChromaSnapshots(settings)
        ledger = {"active_collection": "snapshot", "embed_model": "model", "dimension": 2,
                  "generation": "g", "embed_model_digest": "a" * 64, "fingerprint": "f",
                  "documents": {"doc": {"chunk_ids": ["one"], "status": "active"}},
                  "chunks": 1, "content_sha256": "hash", "versions": "2026",
                  "ledger_revision": "revision", "chunk_size": 100, "chunk_overlap": 10}
        wrong = [{"id": "one", "text": "text", "vector": [1., 0.],
                  "metadata": {"doc_key": "wrong"}}]
        with self.assertRaisesRegex(RuntimeError, "per-document"):
            backend.publish(ledger, wrong)
        client.get_or_create_collection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
