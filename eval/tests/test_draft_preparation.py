"""Dataset preparation cannot overwrite human work or attach stale source labels."""

import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "prepare_drafts",
    Path(__file__).resolve().parents[2] / "scripts/prepare_assignment3_drafts.py",
)
drafts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drafts)


def test_existing_data_is_preserved_before_any_output(tmp_path, monkeypatch):
    monkeypatch.setattr(drafts, "ROOT", tmp_path)
    folder = tmp_path / "eval"
    folder.mkdir()
    existing = folder / "live_queries.jsonl"
    existing.write_text("human work")
    with pytest.raises(SystemExit, match="Refusing to overwrite"):
        drafts.main()
    assert existing.read_text() == "human work"
    assert not (folder / "golden.synthetic-draft.jsonl").exists()


def test_changed_source_cannot_silently_reuse_page_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(drafts, "ROOT", tmp_path)
    folder = tmp_path / "corpus/raw"
    folder.mkdir(parents=True)
    (folder / drafts.SOURCE).write_bytes(b"changed source")
    with pytest.raises(SystemExit, match="Source PDF changed"):
        drafts.main()
    assert not (tmp_path / "eval/golden.synthetic-draft.jsonl").exists()
