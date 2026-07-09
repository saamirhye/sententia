import sententia.graph.nodes as nodes_module


def _initial_state(query: str) -> dict:
    return {
        "query": query,
        "attempts": 0,
        "results": [],
        "relevant": None,
        "sufficient": False,
        "answer": None,
        "human_approved": None,
        "follow_up_questions": [],
    }


def test_assess_node_defaults_to_insufficient_on_llm_failure(monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("simulated API failure")

    monkeypatch.setattr(nodes_module, "judge_sufficiency", _raise)

    result = nodes_module.assess({"query": "q", "results": []})

    assert result == {"sufficient": False}


def test_graph_loop_with_mocked_assess_two_passes_then_terminates(monkeypatch, chroma_persist_dir):
    """Simulates insufficient on pass 1, sufficient on pass 2 -- loop runs
    twice and terminates via the sufficient path, not the step cap.

    generate is real as of phase 4, so generate_answer_stream is mocked here
    too -- this test is about assess/the loop, not generate's own behavior
    (see test_graph_generate_llm.py for that)."""
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (True, "on-topic"))
    monkeypatch.setattr(nodes_module, "generate_answer_stream", lambda *a, **kw: iter(["MOCKED ANSWER"]))
    monkeypatch.setattr(nodes_module, "generate_follow_up_questions", lambda *a, **kw: ["stub question"])

    calls = {"n": 0}

    def _fake_judge(query, results):
        calls["n"] += 1
        return (calls["n"] >= 2), "stub reasoning"

    monkeypatch.setattr(nodes_module, "judge_sufficiency", _fake_judge)

    from sententia.graph.build import build_graph

    app = build_graph()
    config = {"configurable": {"thread_id": "test-loop-two-passes"}}
    final_state = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW"), config
    )

    assert final_state["attempts"] == 2
    assert final_state["sufficient"] is True
    assert final_state["answer"] == "MOCKED ANSWER"


def test_graph_loop_hits_step_cap_when_always_insufficient(monkeypatch, chroma_persist_dir):
    """Simulates insufficient for all MAX_ATTEMPTS passes -- step cap now
    routes to human_review first (phase 6), which pauses via interrupt()
    rather than running generate immediately. This test only asserts the
    pause itself (attempts, sufficient, and that generate has NOT run yet);
    the post-approval continuation into generate is covered by
    test_human_review.py."""
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (True, "on-topic"))
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (False, "never enough"))

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("generate_answer_stream must not run before human_review approves")

    monkeypatch.setattr(nodes_module, "generate_answer_stream", _fail_if_called)

    from sententia.graph.build import build_graph

    app = build_graph()
    config = {"configurable": {"thread_id": "test-step-cap-pause"}}
    result = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW"), config
    )

    assert result["attempts"] == 3  # MAX_ATTEMPTS
    assert result["sufficient"] is False
    assert "__interrupt__" in result
    assert result["answer"] is None
