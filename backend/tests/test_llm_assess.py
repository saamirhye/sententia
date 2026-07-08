from unittest.mock import MagicMock

import sententia.llm.assess as assess_module
from sententia.llm.assess import _build_prompt, judge_sufficiency


def test_prompt_includes_query_and_all_accumulated_results():
    results = [
        {"source": "RTA 2010 s 87F", "snippet": "renovation ground...", "kind": "legislation"},
        {"source": "Smith v Jones [2020] NCAT 1", "snippet": "tribunal held...", "kind": "case"},
    ]
    prompt = _build_prompt("can a landlord end a lease for renovations", results)

    assert "can a landlord end a lease for renovations" in prompt
    assert "RTA 2010 s 87F" in prompt
    assert "renovation ground..." in prompt
    assert "Smith v Jones [2020] NCAT 1" in prompt
    assert "tribunal held..." in prompt
    assert "(2 so far)" in prompt  # proves accumulation, not just the latest pass


def test_prompt_handles_empty_results():
    prompt = _build_prompt("some query", [])
    assert "no results retrieved yet" in prompt
    assert "(0 so far)" in prompt


def _fake_response(tool_input: dict):
    tool_use_block = MagicMock(type="tool_use", input=tool_input)
    return MagicMock(content=[tool_use_block])


def test_judge_sufficiency_parses_sufficient_response(monkeypatch):
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(
        {"sufficient": True, "reasoning": "Both statute and case law present."}
    )
    monkeypatch.setattr(assess_module, "get_client", lambda: fake_client)

    sufficient, reasoning = judge_sufficiency("query", [])

    assert sufficient is True
    assert reasoning == "Both statute and case law present."


def test_judge_sufficiency_parses_insufficient_response(monkeypatch):
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(
        {"sufficient": False, "reasoning": "No case law found yet."}
    )
    monkeypatch.setattr(assess_module, "get_client", lambda: fake_client)

    sufficient, reasoning = judge_sufficiency("query", [])

    assert sufficient is False
    assert reasoning == "No case law found yet."
