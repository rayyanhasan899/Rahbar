import json
import pytest
from pipeline.run import discover


def test_manifest_cannot_import_a_file_outside_the_selected_corpus(tmp_path):
    root = tmp_path / "corpus"
    root.mkdir()
    (tmp_path / "outside.txt").write_text("not selected")
    (root / "_index.json").write_text(json.dumps([{"file": "../outside.txt"}]))
    with pytest.raises(ValueError, match="escapes"):
        discover(str(root))
