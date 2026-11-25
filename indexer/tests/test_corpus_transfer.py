"""Exercise the existing deployment caller and batch transfer without Kubernetes."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "corpus_transfer", Path(__file__).resolve().parents[2] / "scripts" / "corpus_transfer.py")
assert spec is not None and spec.loader is not None
transfer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "corpus" / "raw"
        self.source.mkdir(parents=True)
        allowed = patch.object(transfer.safe_paths, "ALLOWED_ROOTS", (*transfer.safe_paths.ALLOWED_ROOTS, self.root))
        allowed.start()
        self.addCleanup(allowed.stop)
        self.content = b"A complete owned document."
        (self.source / "rules.md").write_bytes(self.content)
        self.index = [{"file": "rules.md", "sha256": hashlib.sha256(self.content).hexdigest()}]
        self.write_index()

    def write_index(self):
        (self.source / "_index.json").write_text(json.dumps(self.index), encoding="utf-8")

    def capture(self, args, **kwargs):
        if "stdin" in kwargs:
            with tarfile.open(fileobj=kwargs["stdin"], mode="r") as archive:
                self.assertEqual(archive.getnames(), ["_index.json", "rules.md"])
                self.assertEqual(archive.extractfile("rules.md").read(), self.content)

    def test_zero_argument_deployment_contract_ignores_callers_arguments(self):
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with patch("sys.argv", ["deploy_local.py", "--tag", "abc"]), patch.object(
                    transfer.subprocess, "run", side_effect=self.capture) as run:
                transfer.main()
        finally:
            os.chdir(previous)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertIn(["kubectl", "-n", "rahbar", "exec", "corpus-transfer", "--", "mkdir",
                       "-p", "/corpus"], commands)
        self.assertEqual(commands[-1][-2:], ["pod/corpus-transfer", "--wait=true"])

    def test_explicit_batch_stays_inside_selected_destination(self):
        with patch.object(transfer.subprocess, "run", side_effect=self.capture) as run:
            transfer.main(self.source, "batch-b")
        commands = [call.args[0] for call in run.call_args_list]
        unpack = next(command for command in commands if "tar" in command)
        self.assertEqual(unpack[-2:], ["-C", "/corpus/batch-b"])

    def test_invalid_destination_hash_and_source_are_rejected_before_cluster_calls(self):
        with patch.object(transfer.subprocess, "run") as run:
            for destination in ("../escape", "/tmp", "batch;evil"):
                with self.assertRaises(ValueError):
                    transfer.main(self.source, destination)
            self.index[0]["sha256"] = "b" * 64
            self.write_index()
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                transfer.main(self.source)
            self.index[0]["file"] = "../outside.md"
            self.write_index()
            with self.assertRaisesRegex(ValueError, "plain supported"):
                transfer.main(self.source)
        run.assert_not_called()
