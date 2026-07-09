from unittest.mock import MagicMock

import sententia.llm.generate as generate_module
from sententia.llm.generate import _build_prompt, generate_answer

_RESULTS = [
    {"source": "RTA 2010 s 87F", "text": "renovation ground...", "kind": "legislation"},
    {"source": "Smith v Jones [2020] NCAT 1", "text": "tribunal held...", "kind": "case"},
]


def test_prompt_includes_query_and_all_accumulated_results():
    prompt = _build_prompt("can a landlord end a lease for renovations", _RESULTS, sufficient=True)

    assert "can a landlord end a lease for renovations" in prompt
    assert "RTA 2010 s 87F" in prompt
    assert "renovation ground..." in prompt
    assert "Smith v Jones [2020] NCAT 1" in prompt
    assert "tribunal held..." in prompt


def test_prompt_handles_empty_results():
    prompt = _build_prompt("some query", [], sufficient=True)
    assert "(no results retrieved)" in prompt


def test_prompt_sufficient_true_vs_false_differ():
    confident_prompt = _build_prompt("query", _RESULTS, sufficient=True)
    hedged_prompt = _build_prompt("query", _RESULTS, sufficient=False)

    assert "judged sufficient to answer confidently" in confident_prompt
    assert "judged sufficient to answer confidently" not in hedged_prompt

    assert "step cap" in hedged_prompt
    assert "MUST NOT present the answer as fully confident" in hedged_prompt
    assert "step cap" not in confident_prompt
    assert "MUST NOT present the answer as fully confident" not in confident_prompt


def test_prompt_includes_grounding_instruction():
    prompt = _build_prompt("query", _RESULTS, sufficient=True)
    assert "ONLY in the sources provided" in prompt
    assert "training" in prompt


def _fake_response(text: str):
    text_block = MagicMock(type="text", text=text)
    return MagicMock(content=[text_block])


def test_generate_answer_parses_text_response(monkeypatch):
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(
        "Under s 87F, a landlord may terminate for renovations."
    )
    monkeypatch.setattr(generate_module, "get_client", lambda: fake_client)

    answer = generate_answer("query", _RESULTS, sufficient=True)

    assert answer == "Under s 87F, a landlord may terminate for renovations."
