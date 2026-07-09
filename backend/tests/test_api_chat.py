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
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (True, "on-topic"))
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (True, "enough"))
    monkeypatch.setattr(nodes_module, "generate_answer_stream", lambda *a, **kw: iter(["Hello ", "world."]))
    monkeypatch.setattr(nodes_module, "generate_follow_up_questions", lambda *a, **kw: ["stub question"])

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
    assert _extract_event_data(body, "done")["follow_up_questions"] == ["stub question"]


def test_chat_step_cap_surfaces_human_review_required_event(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (True, "on-topic"))
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
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (True, "on-topic"))
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (False, "never enough"))
    monkeypatch.setattr(nodes_module, "generate_answer_stream", lambda *a, **kw: iter(["Hedged ", "answer."]))
    monkeypatch.setattr(nodes_module, "generate_follow_up_questions", lambda *a, **kw: ["stub question"])

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
    assert _extract_event_data(resume_body, "done")["follow_up_questions"] == ["stub question"]


def test_chat_resume_declined_streams_decline_message(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (True, "on-topic"))
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
    assert _extract_event_data(resume_body, "done")["follow_up_questions"] == []


def test_chat_irrelevant_query_streams_message_and_done_without_search(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (False, "off-topic"))

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("search must not run for an irrelevant query")

    monkeypatch.setattr(nodes_module, "hybrid_search", _fail_if_called)

    client = TestClient(app)
    with client.stream("POST", "/api/chat", json={"query": "what's the weather"}) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert "event: answer_delta" in body
    assert _extract_event_data(body, "answer_delta")["text"] == nodes_module.NOT_RELEVANT_MESSAGE
    assert "event: done" in body
    assert "event: human_review_required" not in body
    assert _extract_event_data(body, "done")["follow_up_questions"] == []
