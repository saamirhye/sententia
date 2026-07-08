from unittest.mock import MagicMock

import pytest

import sententia.llm.generate as generate_module
from sententia.llm.generate import generate_answer_stream

_RESULTS = [
    {"source": "RTA 2010 s 87F", "snippet": "renovation ground...", "kind": "legislation"},
]


def _fake_stream_manager(text_stream):
    manager = MagicMock()
    stream_obj = MagicMock()
    stream_obj.text_stream = text_stream
    manager.__enter__.return_value = stream_obj
    manager.__exit__.return_value = False
    return manager


def test_generate_answer_stream_yields_chunks_in_order(monkeypatch):
    fake_client = MagicMock()
    fake_client.messages.stream.return_value = _fake_stream_manager(
        iter(["Under ", "s 87F, ", "a landlord may..."])
    )
    monkeypatch.setattr(generate_module, "get_client", lambda: fake_client)

    chunks = list(generate_answer_stream("query", _RESULTS, sufficient=True))

    assert chunks == ["Under ", "s 87F, ", "a landlord may..."]
    assert "".join(chunks) == "Under s 87F, a landlord may..."


def test_generate_answer_stream_propagates_mid_stream_error(monkeypatch):
    def _raising_iter():
        yield "partial answer chunk "
        raise RuntimeError("simulated mid-stream network failure")

    fake_client = MagicMock()
    fake_client.messages.stream.return_value = _fake_stream_manager(_raising_iter())
    monkeypatch.setattr(generate_module, "get_client", lambda: fake_client)

    gen = generate_answer_stream("query", _RESULTS, sufficient=True)

    assert next(gen) == "partial answer chunk "
    with pytest.raises(RuntimeError):
        next(gen)
