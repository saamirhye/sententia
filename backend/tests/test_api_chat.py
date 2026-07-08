import json

from fastapi.testclient import TestClient

import sententia.graph.nodes as nodes_module
from sententia.api.main import app


def _extract_event_data(body: str, event_name: str) -> dict:
    for block in body.split("\n\n"):
        if f"event: {event_name}" in block:
            data_line = next(line for line in block.split("\n") if line.startswith("data: "))
            return json.loads(data_line[len("data: ") :])
    raise AssertionError(f"event: {event_name} not found in SSE body: {body!r}")


def test_chat_streams_answer_deltas_and_done_event(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (True, "enough"))
    monkeypatch.setattr(nodes_module, "generate_answer_stream", lambda *a, **kw: iter(["Hello ", "world."]))

    client = TestClient(app)
    with client.stream("POST", "/api/chat", json={"query": "test query"}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())

    assert "event: answer_delta" in body
    assert '"text": "Hello "' in body
    assert '"text": "world."' in body
    assert "event: done" in body
    assert '"sufficient": true' in body


def test_chat_step_cap_surfaces_human_review_required_event(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (False, "never enough"))

    client = TestClient(app)
    with client.stream("POST", "/api/chat", json={"query": "test query"}) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert "event: human_review_required" in body
    assert "event: done" not in body
    data = _extract_event_data(body, "human_review_required")
    assert "thread_id" in data
    assert data["attempts"] == 3


def test_chat_resume_approved_continues_stream_and_returns_done(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (False, "never enough"))
    monkeypatch.setattr(nodes_module, "generate_answer_stream", lambda *a, **kw: iter(["Hedged ", "answer."]))

    client = TestClient(app)
    with client.stream("POST", "/api/chat", json={"query": "test query"}) as response:
        body = "".join(response.iter_text())
    thread_id = _extract_event_data(body, "human_review_required")["thread_id"]

    with client.stream(
        "POST", "/api/chat/resume", json={"thread_id": thread_id, "approved": True}
    ) as response:
        assert response.status_code == 200
        resume_body = "".join(response.iter_text())

    assert "event: answer_delta" in resume_body
    assert '"text": "Hedged "' in resume_body
    assert "event: done" in resume_body
    assert '"sufficient": false' in resume_body


def test_chat_resume_declined_streams_decline_message(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (False, "never enough"))

    client = TestClient(app)
    with client.stream("POST", "/api/chat", json={"query": "test query"}) as response:
        body = "".join(response.iter_text())
    thread_id = _extract_event_data(body, "human_review_required")["thread_id"]

    with client.stream(
        "POST", "/api/chat/resume", json={"thread_id": thread_id, "approved": False}
    ) as response:
        assert response.status_code == 200
        resume_body = "".join(response.iter_text())

    assert "event: answer_delta" in resume_body
    assert nodes_module.DECLINE_MESSAGE in resume_body
    assert "event: done" in resume_body
