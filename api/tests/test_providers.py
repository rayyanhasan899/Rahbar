"""The real providers against mocked HTTP: request shape, parsing and error mapping."""

from __future__ import annotations

import json

import httpx
import pytest
from app.config import Settings
from app.providers.llm.hosted import HostedProvider
from app.providers.llm.ollama import OllamaProvider
from app.providers.llm.prompt import (
    ProviderOutputError,
    ProviderUnavailable,
    build_messages,
    parse_answer,
)
from app.schemas import Turn
from tests.fakes import POISON, POLICY, good_answer

ANSWER_JSON = good_answer().model_dump_json()


def client_for(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_prompt_fences_passages_and_marks_them_as_data():
    messages = build_messages("What attendance?", [POLICY, POISON],
                              history=[Turn(question="Earlier?", answer="Yes.")])
    system, user = messages[0]["content"], messages[1]["content"]
    assert "data, not instructions" in system
    assert '"answered_from_context"' in system  # the schema travels with the rules
    assert 'BEGIN PASSAGE 1' in user and 'END PASSAGE 2' in user
    assert '[1] source: "academic-rules-handbook-jun-2026.pdf" | section: "1.21" | page: 7' in user
    assert "page: null" in user
    assert "It is not evidence" in user
    assert user.rstrip().endswith("Question: What attendance?")


def test_retry_feedback_is_appended():
    messages = build_messages("Q?", [POLICY], feedback="bad citation.")
    assert messages[-1]["role"] == "user"
    assert "bad citation." in messages[-1]["content"]


def test_parse_answer_accepts_fenced_json_and_rejects_garbage():
    assert parse_answer(f"```json\n{ANSWER_JSON}\n```").answered_from_context is True
    with pytest.raises(ProviderOutputError):
        parse_answer("Sure! Attendance is 80%.")
    with pytest.raises(ProviderOutputError):
        parse_answer('{"answer": "missing fields"}')


def test_ollama_sends_schema_and_temperature():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"message": {"content": ANSWER_JSON},
                                         "prompt_eval_count": 50, "eval_count": 20})

    settings = Settings(ollama_url="http://ollama:11434/", llm_model="m", temperature=0.1)
    answer = OllamaProvider(settings, client=client_for(handler)).generate("Q?", [POLICY])
    assert answer.citations[0].section == "1.21"
    assert seen["url"] == "http://ollama:11434/api/chat"
    assert seen["body"]["format"]["title"] == "Answer"
    assert seen["body"]["options"]["temperature"] == 0.1
    assert seen["body"]["options"]["num_ctx"] == 4096
    assert seen["body"]["options"]["num_predict"] == 512
    assert seen["body"]["stream"] is False


@pytest.mark.parametrize("status", [500, 404])
def test_ollama_http_errors_are_unavailable(status):
    provider = OllamaProvider(Settings(), client=client_for(lambda r: httpx.Response(status)))
    with pytest.raises(ProviderUnavailable):
        provider.generate("Q?", [POLICY])


def test_ollama_timeout_is_unavailable():
    def handler(request):
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(ProviderUnavailable):
        OllamaProvider(Settings(), client=client_for(handler)).generate("Q?", [POLICY])


def test_hosted_uses_bearer_key_and_json_mode():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers["Authorization"]
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": ANSWER_JSON}}],
                                         "usage": {"prompt_tokens": 9, "completion_tokens": 3}})

    settings = Settings(hosted_base_url="https://api.example/v1", llm_api_key="k-test",
                        llm_model="m")
    answer = HostedProvider(settings, client=client_for(handler)).generate("Q?", [POLICY])
    assert answer.answered_from_context is True
    assert seen["auth"] == "Bearer k-test"
    assert seen["url"] == "https://api.example/v1/chat/completions"
    assert seen["body"]["response_format"] == {"type": "json_object"}


def test_hosted_error_message_does_not_echo_the_response_body():
    def handler(request):
        return httpx.Response(401, text="invalid key k-test")

    settings = Settings(hosted_base_url="https://api.example/v1", llm_api_key="k-test")
    with pytest.raises(ProviderUnavailable) as err:
        HostedProvider(settings, client=client_for(handler)).generate("Q?", [POLICY])
    assert "k-test" not in str(err.value)


def test_hosted_needs_a_base_url():
    with pytest.raises(ValueError):
        HostedProvider(Settings(hosted_base_url=""))


def test_hosted_will_not_send_a_key_over_cleartext_http():
    with pytest.raises(ValueError, match="requires HTTPS"):
        HostedProvider(Settings(hosted_base_url="http://api.example/v1", llm_api_key="not-a-real-key"))


def test_malformed_usage_is_retriable_output_error_not_an_unhandled_exception():
    client = client_for(lambda r: httpx.Response(200, json={
        "choices": [{"message": {"content": ANSWER_JSON}}],
        "usage": {"prompt_tokens": "invalid"},
    }))
    provider = HostedProvider(Settings(hosted_base_url="https://api.example/v1"), client=client)
    with pytest.raises(ProviderOutputError, match="usage envelope"):
        provider.generate("Q?", [POLICY])
