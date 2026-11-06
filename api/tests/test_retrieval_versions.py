"""Current/historical selection using a fake Chroma collection, no services."""
from unittest.mock import MagicMock
import pytest
from app.config import Settings
from app.retrieval.chroma import ChromaRetriever


@pytest.mark.parametrize("question,version", [
    ("What do the 2023 rules say?", "2023-08"),
    ("According to the 2023 edition, withdrawal?", "2023-08"),
    ("Under 2023 rules?\nAnd under the 2026 rules?", "2026-06"),
    ("Current withdrawal deadline?", None),
])
def test_explicit_year_and_current_filter(question, version):
    retriever = ChromaRetriever(Settings())
    collection = MagicMock()
    collection.query.return_value = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    retriever.active = lambda: (collection, {"dimension": 2, "versions": "2023-08|2026-06"})
    assert retriever.retrieve(question, 5, [1.0, 0.0]) == []
    where = collection.query.call_args.kwargs["where"]
    assert where == ({"doc_version": {"$in": [version]}} if version else {"superseded": False})


def test_missing_historical_version_does_not_fall_back_to_current():
    r = ChromaRetriever(Settings())
    collection = MagicMock()
    r.active = lambda: (collection, {"dimension": 1, "versions": "2026-06"})
    assert r.retrieve("Under 2022 rules?", 5, [1.0]) == []
    collection.query.assert_not_called()
