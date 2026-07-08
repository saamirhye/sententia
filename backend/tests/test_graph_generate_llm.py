import sententia.graph.nodes as nodes_module


def _initial_state(query: str) -> dict:
    return {
        "query": query,
        "attempts": 0,
        "results": [],
        "sufficient": False,
        "answer": None,
        "human_approved": None,
    }


def test_generate_node_falls_back_on_llm_failure(monkeypatch, chroma_persist_dir):
    """generate() now calls get_stream_writer(), which requires a real LangGraph
    runtime context -- it can no longer be exercised by calling
    nodes_module.generate({...}) as a bare function outside any graph run (that
    raises RuntimeError). Instead, drive it through build_graph().invoke(),
    mocking judge_sufficiency to reach generate on the first pass and
    generate_answer_stream to raise."""
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (True, "stub reasoning"))

    def _raise(*args, **kwargs):
        raise RuntimeError("simulated API failure")

    monkeypatch.setattr(nodes_module, "generate_answer_stream", _raise)

    from sententia.graph.build import build_graph

    app = build_graph()
    config = {"configurable": {"thread_id": "test-generate-failure-fallback"}}
    final_state = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW"), config
    )

    assert "answer" in final_state
    assert isinstance(final_state["answer"], str)
    assert len(final_state["answer"]) > 0


def test_graph_sufficient_path_uses_real_generate_answer(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)

    calls = {"n": 0}

    def _fake_judge(query, results):
        calls["n"] += 1
        return (calls["n"] >= 2), "stub reasoning"

    monkeypatch.setattr(nodes_module, "judge_sufficiency", _fake_judge)

    generate_calls = []

    def _fake_generate_stream(query, results, sufficient):
        generate_calls.append(sufficient)
        return iter(["MOCKED ANSWER: ", "because reasons"])

    monkeypatch.setattr(nodes_module, "generate_answer_stream", _fake_generate_stream)

    from sententia.graph.build import build_graph

    app = build_graph()
    config = {"configurable": {"thread_id": "test-sufficient-path"}}
    final_state = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW"), config
    )

    assert final_state["answer"] == "MOCKED ANSWER: because reasons"
    assert generate_calls == [True]


def test_graph_step_cap_path_uses_real_generate_answer(monkeypatch, chroma_persist_dir):
    """Step cap now pauses at human_review (phase 6) before reaching generate.
    This test resumes with approval to prove generate still runs for real
    (mocked at the LLM call boundary, as before) once approved."""
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (False, "never enough"))

    generate_calls = []

    def _fake_generate_stream(query, results, sufficient):
        generate_calls.append(sufficient)
        return iter(["MOCKED REDUCED-CONFIDENCE ANSWER"])

    monkeypatch.setattr(nodes_module, "generate_answer_stream", _fake_generate_stream)

    from langgraph.types import Command

    from sententia.graph.build import build_graph

    app = build_graph()
    config = {"configurable": {"thread_id": "test-step-cap-approve"}}
    paused = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW"), config
    )
    assert "__interrupt__" in paused

    final_state = app.invoke(Command(resume=True), config)

    assert final_state["answer"] == "MOCKED REDUCED-CONFIDENCE ANSWER"
    assert generate_calls == [False]
