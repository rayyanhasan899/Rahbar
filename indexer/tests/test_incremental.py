"""Lifecycle acceptance tests with actual Markdown extraction and no external services."""
from __future__ import annotations

from collections import Counter
from contextlib import redirect_stdout
from copy import deepcopy
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline.config import get_settings
from pipeline.datalake import Lake, discover_inputs, identifier, load_json
from pipeline.extract import extract
from pipeline.incremental import ingest, read_ledger, rollback


class MemorySnapshots:
    def __init__(self):
        self.pointer = None
        self.collections = {}
        self.fail = False

    def active(self):
        return deepcopy(self.pointer)

    def counts(self, name):
        return dict(Counter(r["metadata"]["doc_key"] for r in self.collections[name]))

    def publish(self, ledger, rows):
        self.collections[ledger["active_collection"]] = list(rows)
        if self.fail:
            raise RuntimeError("interrupted before publication")
        self.pointer = deepcopy(ledger)


class Embeddings:
    def __init__(self):
        self.calls = []

    def __call__(self, texts):
        self.calls.extend(texts)
        return [[(x + 1) / 256 for x in hashlib.sha256(t.encode()).digest()] for t in texts]


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.incoming = self.root / "incoming"
        self.incoming.mkdir()
        self.settings = replace(get_settings(), corpus_dir=str(self.incoming),
                                datalake_dir=str(self.root / "lake"), collection="test-index",
                                chunk_size=90, chunk_overlap=10)
        self.backend, self.embed = MemorySnapshots(), Embeddings()
        self.digest = "a" * 64

    def write(self, name="rules.md", family="rules", version="2026", text=None):
        body = text or ("Students must attend the practical session and submit assessed work. " * 4)
        path = self.incoming / name
        path.write_text("---\ntitle: University test policy\ndoc_id: " + family
                        + "\ndoc_version: '" + version + "'\n---\n# Policy\n" + body,
                        encoding="utf-8")
        return path

    def run_ingest(self, **kwargs):
        with redirect_stdout(io.StringIO()):
            return ingest(self.settings, self.backend, self.embed, extract, self.digest, **kwargs)

    def ledger(self):
        return read_ledger(Lake(self.settings.datalake_dir, self.settings.collection), self.backend)

    def test_unchanged_run_skips_all_embedding_and_extraction(self):
        self.write()
        first = self.run_ingest()
        self.assertGreater(first["chunks_embedded"], 0)
        self.embed.calls.clear()
        def forbidden(*args):
            raise AssertionError("unchanged input must reuse extraction")
        with redirect_stdout(io.StringIO()):
            second = ingest(self.settings, self.backend, self.embed, forbidden, self.digest)
        self.assertEqual(self.embed.calls, [])
        self.assertEqual(second["chunks_embedded"], 0)
        self.assertEqual(second["document_embeddings"], 0)
        self.assertEqual(second["generation"], first["generation"])
        self.assertFalse(second["published"])

    def test_changed_document_preserves_other_ids_and_vectors(self):
        self.write()
        self.write("fees.md", "fees", text="Tuition is paid at the designated bank. " * 5)
        self.run_ingest()
        old = self.ledger()
        key = identifier("fees\0" + "2026")
        before = [r for r in self.backend.collections[old["active_collection"]]
                  if r["metadata"]["doc_key"] == key]
        self.write(text="Updated policy permits one documented attendance exception. " * 5)
        result = self.run_ingest()
        after = [r for r in self.backend.collections[self.ledger()["active_collection"]]
                 if r["metadata"]["doc_key"] == key]
        self.assertEqual(before, after)
        self.assertEqual(result["document_embeddings"], 1)

    def test_deleted_document_has_no_current_orphan_chunks(self):
        path = self.write()
        self.run_ingest()
        path.unlink()
        result = self.run_ingest()
        self.assertEqual(result["counts"][0]["status"], "deleted")
        self.assertEqual(result["counts"][0]["chunks"], 0)
        self.assertEqual(self.backend.counts(self.ledger()["active_collection"]), {})
        self.assertEqual(result["chunks_embedded"], 0)

    def test_invalid_change_preserves_last_verified_version(self):
        path = self.write()
        self.run_ingest()
        before = self.ledger()["generation"]
        path.write_text("broken input", encoding="utf-8")
        result = self.run_ingest()
        self.assertEqual(before, self.ledger()["generation"])
        self.assertEqual(result["documents"][0]["outcome"], "quarantined")
        self.assertEqual(len(result["documents"][0]["checks"]), 4)
        self.assertTrue(list((self.root / "lake/quarantine").rglob("reason.json")))

    def test_versions_archive_and_rollback_without_embedding(self):
        self.write("old.md", version="2023")
        self.write("new.md", version="2026", text="Current policy permits two extensions. " * 5)
        self.run_ingest()
        ledger = self.ledger()
        self.assertEqual({r["version"]: r["status"] for r in ledger["documents"].values()},
                         {"2023": "archived", "2026": "active"})
        self.embed.calls.clear()
        result = rollback(self.settings, self.backend, "rules", "2023", self.digest)
        self.assertEqual(result["chunks_embedded"], 0)
        self.assertEqual(self.embed.calls, [])
        self.assertEqual(self.ledger()["documents"][identifier("rules\0" + "2023")]["status"],
                         "active")
        rollback(self.settings, self.backend, "rules", None, self.digest)
        self.assertEqual(self.ledger()["documents"][identifier("rules\0" + "2026")]["status"],
                         "active")

    def test_failed_publication_preserves_active_and_recovers_cached_vectors(self):
        self.write()
        self.run_ingest()
        original = self.backend.active()
        self.write(text="Changed rules require the dean's written approval. " * 5)
        self.backend.fail = True
        with self.assertRaises(RuntimeError):
            self.run_ingest()
        self.assertEqual(self.backend.active(), original)
        self.backend.fail = False
        self.embed.calls.clear()
        result = self.run_ingest()
        self.assertTrue(result["published"])
        self.assertEqual(self.embed.calls, [])

    def test_same_collection_refuses_incompatible_chunking_or_model_artifact(self):
        self.write()
        self.run_ingest()
        with self.assertRaisesRegex(ValueError, "new collection"):
            with redirect_stdout(io.StringIO()):
                ingest(replace(self.settings, chunk_size=120), self.backend,
                       self.embed, extract, self.digest)
        with self.assertRaisesRegex(ValueError, "new collection"):
            with redirect_stdout(io.StringIO()):
                ingest(self.settings, self.backend, self.embed, extract, "b" * 64)

    def test_scanning_another_scope_does_not_delete_original_batch(self):
        self.write()
        self.run_ingest()
        other = self.root / "batch-b"
        other.mkdir()
        self.settings = replace(self.settings, incoming_dirs=(str(other),))
        self.run_ingest()
        self.assertEqual(next(iter(self.ledger()["documents"].values()))["status"], "active")

    def test_missing_scope_fails_without_deleting_current_documents(self):
        self.write()
        self.run_ingest()
        original = self.backend.active()
        self.settings = replace(self.settings, incoming_dirs=(str(self.root / "missing"),))
        with self.assertRaises(FileNotFoundError):
            self.run_ingest()
        self.assertEqual(self.backend.active(), original)

    def test_exact_and_near_duplicates_are_quarantined(self):
        self.write()
        duplicate = self.write("duplicate.md", "unrelated")
        duplicate.write_bytes((self.incoming / "rules.md").read_bytes())
        # A manifest deliberately gives the exact bytes a distinct family identity.
        (self.incoming / "_index.json").write_text(json.dumps([
            {"file": "rules.md", "doc_id": "rules"},
            {"file": "duplicate.md", "doc_id": "copy"}]))
        result = self.run_ingest()
        self.assertFalse(result["documents"][1]["checks"]["uniqueness"]["passed"])
        (self.incoming / "_index.json").unlink()
        duplicate.write_text("---\ntitle: Near policy\ndoc_id: other\ndoc_version: 2026\n---\n"
                             + "Similar content is retained as a controlled duplicate. " * 4)
        self.embed = lambda texts: [load_json(next((self.root / "lake/cache").glob("*.json")))
                                   ["document_vector"] for _ in texts]
        result = self.run_ingest()
        self.assertTrue(any(not r["checks"]["uniqueness"]["passed"]
                            for r in result["documents"]))

    def test_verify_only_never_publishes_or_writes_ledger(self):
        self.write()
        self.write("fees.md", "fees", text="Fees are settled through the bank. " * 5)
        result = self.run_ingest(verify_only=True)
        self.assertEqual(result["chunks_embedded"], 0)
        self.assertIsNone(self.backend.active())
        self.assertFalse((self.root / "lake/state/test-index/ledger.json").exists())

    def test_traversal_manifest_never_reads_outside_root(self):
        secret = self.root / "outside.txt"
        secret.write_text("private content")
        (self.incoming / "_index.json").write_text(json.dumps([{"file": "../outside.txt"}]))
        self.assertTrue(discover_inputs([self.incoming])[0].error)
        result = self.run_ingest()
        self.assertFalse(result["documents"][0]["checks"]["quality"]["passed"])
        self.assertFalse(any(p.name == "outside.txt" for p in
                             (self.root / "lake/quarantine").rglob("*")))

    def test_counts_repair_orphan_current_snapshot_without_reembedding(self):
        self.write()
        self.run_ingest()
        name = self.ledger()["active_collection"]
        self.backend.collections[name].append({"metadata": {"doc_key": "orphan"}})
        self.embed.calls.clear()
        result = self.run_ingest()
        self.assertTrue(result["published"])
        self.assertEqual(self.embed.calls, [])
        self.assertNotIn("orphan", self.backend.counts(self.ledger()["active_collection"]))

    def test_recovery_uses_published_revision_not_interrupted_convenience_ledger(self):
        self.write()
        self.run_ingest()
        self.write(text="The amended process needs departmental approval. " * 5)
        with patch("pipeline.incremental.materialize", side_effect=OSError("disk interrupted")):
            with self.assertRaises(OSError):
                self.run_ingest()
        published = self.backend.active()["generation"]
        self.embed.calls.clear()
        result = self.run_ingest()
        self.assertEqual(result["generation"], published)
        self.assertEqual(self.embed.calls, [])
        convenience = load_json(self.root / "lake/state/test-index/ledger.json")
        self.assertEqual(convenience["generation"], published)

    def test_owned_batch_generator_is_repeatable_and_all_inputs_get_four_checks(self):
        import importlib.util
        location = Path(__file__).resolve().parents[2] / "corpus/generate_batch_b.py"
        spec = importlib.util.spec_from_file_location("generate_batch_b", location)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.generate(self.root)
        first_hash = hashlib.sha256((self.root / "batch-b/_index.json").read_bytes()).hexdigest()
        module.generate(self.root)
        self.assertEqual(first_hash, hashlib.sha256(
            (self.root / "batch-b/_index.json").read_bytes()).hexdigest())
        self.settings = replace(self.settings, incoming_dirs=(str(self.root / "batch-a"),))
        self.run_ingest()
        self.settings = replace(self.settings, incoming_dirs=(
            str(self.root / "batch-a"), str(self.root / "batch-b")))
        report = self.run_ingest()
        rows = {r["source"]: r for r in report["documents"]}
        self.assertGreaterEqual(len(rows), 11)
        self.assertTrue(all(len(r["checks"]) == 4 for r in rows.values()))
        for name in ("duplicate-1.md", "duplicate-2.md"):
            self.assertFalse(rows[name]["checks"]["uniqueness"]["passed"])
        self.assertFalse(rows["missing-metadata.txt"]["checks"]["completeness"]["passed"])
        self.assertFalse(rows["truncated.txt"]["checks"]["completeness"]["passed"])
        self.assertFalse(rows["garbled.txt"]["checks"]["quality"]["passed"])
        self.assertNotEqual(rows["injected-policy.md"]["outcome"], "quarantined")
        self.assertTrue(rows["control-policy.md"]["archived"])

    def test_bad_manifest_hash_does_not_replace_verified_content(self):
        self.write()
        self.run_ingest()
        generation = self.ledger()["generation"]
        (self.incoming / "_index.json").write_text(json.dumps([
            {"file": "rules.md", "sha256": "0" * 64}]))
        result = self.run_ingest()
        self.assertEqual(self.ledger()["generation"], generation)
        self.assertFalse(result["documents"][0]["checks"]["completeness"]["passed"])


if __name__ == "__main__":
    unittest.main()
