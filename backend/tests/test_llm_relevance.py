from unittest.mock import MagicMock

import sententia.llm.relevance as relevance_module
from sententia.llm.relevance import _build_prompt, judge_relevance


def test_prompt_includes_query_and_corpus_topics():
    prompt = _build_prompt("what's the weather")
    assert "what's the weather" in prompt
    assert "Rent increases" in prompt
    assert "Bonds" in prompt
    assert "renovation" in prompt.lower()


def _fake_response(tool_input: dict):
    tool_use_block = MagicMock(type="tool_use", input=tool_input)
    return MagicMock(content=[tool_use_block])


def test_judge_relevance_parses_relevant_response(monkeypatch):
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(
        {"relevant": True, "reasoning": "Concerns rent increase notice periods."}
    )
    monkeypatch.setattr(relevance_module, "get_client", lambda: fake_client)

    relevant, reasoning = judge_relevance("can my landlord raise my rent without notice")

    assert relevant is True
    assert reasoning == "Concerns rent increase notice periods."


def test_judge_relevance_parses_not_relevant_response(monkeypatch):
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(
        {"relevant": False, "reasoning": "Unrelated to tenancy law."}
    )
    monkeypatch.setattr(relevance_module, "get_client", lambda: fake_client)

    relevant, reasoning = judge_relevance("what's the weather")

    assert relevant is False
    assert reasoning == "Unrelated to tenancy law."
