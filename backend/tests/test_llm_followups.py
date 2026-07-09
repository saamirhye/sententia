from unittest.mock import MagicMock

import sententia.llm.followups as followups_module
from sententia.llm.followups import _FOLLOWUPS_TOOL, _build_prompt, generate_follow_up_questions


def test_prompt_includes_query_answer_citations_and_self_containment_instruction():
    results = [
        {"source": "RTA 2010 s 87F", "text": "renovation ground...", "kind": "legislation"},
        {"source": "Smith v Jones [2020] NCAT 1", "text": "tribunal held...", "kind": "case"},
    ]
    prompt = _build_prompt(
        "can a landlord end a lease for renovations",
        "Yes, under s 87F of the RTA 2010...",
        results,
    )

    assert "can a landlord end a lease for renovations" in prompt
    assert "Yes, under s 87F of the RTA 2010..." in prompt
    assert "RTA 2010 s 87F" in prompt
    assert "Smith v Jones [2020] NCAT 1" in prompt
    assert "ZERO memory" in prompt
    assert "self-contained" in prompt


def test_prompt_handles_empty_results():
    prompt = _build_prompt("some query", "some answer", [])
    assert "no sources cited" in prompt


def test_followups_tool_schema_has_no_min_or_max_items():
    # Regression guard: Anthropic's strict tool schema validation rejects
    # minItems/maxItems values other than 0 or 1 on array properties (400
    # Bad Request) -- see generate_starter_prompts.py's earlier live failure.
    questions_schema = _FOLLOWUPS_TOOL["input_schema"]["properties"]["questions"]
    assert "minItems" not in questions_schema
    assert "maxItems" not in questions_schema


def _fake_response(tool_input: dict):
    tool_use_block = MagicMock(type="tool_use", input=tool_input)
    return MagicMock(content=[tool_use_block])


def test_generate_follow_up_questions_parses_response(monkeypatch):
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(
        {"questions": ["What notice period applies for renovations?", "Can a tenant challenge the notice?"]}
    )
    monkeypatch.setattr(followups_module, "get_client", lambda: fake_client)

    questions = generate_follow_up_questions("query", "answer", [])

    assert questions == [
        "What notice period applies for renovations?",
        "Can a tenant challenge the notice?",
    ]
