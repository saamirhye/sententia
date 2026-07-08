from fastapi.testclient import TestClient

import sententia.graph.nodes as nodes_module
from sententia.api.main import app


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
