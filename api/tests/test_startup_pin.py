from unittest.mock import MagicMock
import httpx
import pytest
from app.config import Settings
from app.retrieval.chroma import ChromaRetriever


def test_collection_model_cannot_silently_disagree_with_pointer():
    r = ChromaRetriever(Settings())
    control, collection = MagicMock(), MagicMock()
    control.get.return_value = {"metadatas": [{"embed_model": "nomic-embed-text", "active_collection": "staged", "dimension": 2}]}
    collection.metadata = {"embed_model": "different-model", "dimension": 2}
    r._client = MagicMock()
    r._client.get_collection.side_effect = [control, collection]
    with pytest.raises(ValueError, match="collection=different-model"):
        r.active()


@pytest.mark.parametrize("model", ["nomic-embed-text", "other-model"])
def test_startup_pin_check_is_bounded_and_does_not_construct_sdk(monkeypatch, model):
    def respond(request):
        if request.method == "GET":
            return httpx.Response(200, json={"id": "control-id"})
        return httpx.Response(200, json={"metadatas": [{"embed_model": model}]})
    client = httpx.Client(transport=httpx.MockTransport(respond))
    observed = {}
    def factory(**kwargs):
        observed.update(kwargs)
        return client
    monkeypatch.setattr("app.retrieval.chroma.httpx.Client", factory)
    r = ChromaRetriever(Settings())
    if model == "nomic-embed-text":
        r.check_startup()
    else:
        with pytest.raises(ValueError, match="index=other-model api=nomic-embed-text"):
            r.check_startup()
    assert observed["timeout"].connect == 2
    assert r._client is None
