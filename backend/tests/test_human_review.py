from langgraph.types import Command

import sententia.graph.nodes as nodes_module
from sententia.graph.build import build_graph


def _initial_state(query: str) -> dict:
    return {
        "query": query,
        "attempts": 0,
        "results": [],
        "relevant": None,
        "sufficient": False,
        "answer": None,
        "human_approved": None,
    }


def test_interrupt_fires_exactly_at_step_cap(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (True, "on-topic"))
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (False, "never enough"))

    app = build_graph()
    config = {"configurable": {"thread_id": "test-interrupt-fires"}}
    query = "can a landlord end a residential lease early for renovations in NSW"
    result = app.invoke(_initial_state(query), config)

    assert result["attempts"] == 3
    assert "__interrupt__" in result
    interrupt_obj = result["__interrupt__"][0]
    assert interrupt_obj.value["attempts"] == 3
    assert interrupt_obj.value["query"] == query


def test_resume_approved_reaches_generate_with_correct_state(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (True, "on-topic"))
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (False, "never enough"))
    monkeypatch.setattr(nodes_module, "generate_answer_stream", lambda *a, **kw: iter(["OK ANSWER"]))

    app = build_graph()
    config = {"configurable": {"thread_id": "test-resume-approve"}}
    query = "can a landlord end a residential lease early for renovations in NSW"
    app.invoke(_initial_state(query), config)

    final_state = app.invoke(Command(resume=True), config)

    assert final_state["human_approved"] is True
    assert final_state["answer"] == "OK ANSWER"
    assert final_state["attempts"] == 3
    assert "__interrupt__" not in final_state


def test_resume_declined_ends_with_fixed_message_and_never_generates(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (True, "on-topic"))
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (False, "never enough"))

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("generate_answer_stream must not be called on decline")

    monkeypatch.setattr(nodes_module, "generate_answer_stream", _fail_if_called)

    app = build_graph()
    config = {"configurable": {"thread_id": "test-resume-decline"}}
    query = "can a landlord end a residential lease early for renovations in NSW"
    app.invoke(_initial_state(query), config)

    final_state = app.invoke(Command(resume=False), config)

    assert final_state["human_approved"] is False
    assert final_state["answer"] == nodes_module.DECLINE_MESSAGE
    assert "__interrupt__" not in final_state
