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


def test_check_relevance_defaults_to_relevant_on_llm_failure(monkeypatch, chroma_persist_dir):
    """check_relevance() calls get_stream_writer(), which requires a real
    LangGraph runtime context -- it can no longer be exercised by calling
    nodes_module.check_relevance({...}) as a bare function outside any graph
    run (that raises RuntimeError, same issue generate()/human_review() hit
    in earlier phases). Instead, drive it through build_graph().invoke() and
    confirm the fail-open default lets a real query reach search/assess
    normally rather than testing the bare return value in isolation."""
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)

    def _raise(*args, **kwargs):
        raise RuntimeError("simulated API failure")

    monkeypatch.setattr(nodes_module, "judge_relevance", _raise)
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (True, "enough"))
    monkeypatch.setattr(nodes_module, "generate_answer_stream", lambda *a, **kw: iter(["MOCKED ANSWER"]))
    monkeypatch.setattr(nodes_module, "generate_follow_up_questions", lambda *a, **kw: ["stub question"])

    from sententia.graph.build import build_graph

    app = build_graph()
    config = {"configurable": {"thread_id": "test-relevance-failure-fallback"}}
    final_state = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW"), config
    )

    assert final_state["relevant"] is True
    assert final_state["answer"] == "MOCKED ANSWER"


def test_relevant_query_proceeds_to_search_and_never_short_circuits(monkeypatch, chroma_persist_dir):
    """Relevant query: check_relevance passes through, search/assess run for
    real (assess mocked at the LLM boundary, matching this project's existing
    convention), and the graph reaches generate normally."""
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (True, "on-topic"))
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (True, "enough"))
    monkeypatch.setattr(nodes_module, "generate_answer_stream", lambda *a, **kw: iter(["MOCKED ANSWER"]))
    monkeypatch.setattr(nodes_module, "generate_follow_up_questions", lambda *a, **kw: ["stub question"])

    from sententia.graph.build import build_graph

    app = build_graph()
    config = {"configurable": {"thread_id": "test-relevant-proceeds"}}
    final_state = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW"), config
    )

    assert final_state["relevant"] is True
    assert final_state["attempts"] == 1
    assert final_state["answer"] == "MOCKED ANSWER"


def test_irrelevant_query_streams_message_and_ends_without_ever_searching(monkeypatch):
    """Irrelevant query: search/judge_sufficiency must NEVER be called -- this
    is the core cost-savings guarantee of the pre-filter. Raising if either is
    called proves the short-circuit actually skips the loop, not just that it
    produces the right final answer."""
    monkeypatch.setattr(nodes_module, "judge_relevance", lambda query: (False, "off-topic"))

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("search/assess must not run for an irrelevant query")

    monkeypatch.setattr(nodes_module, "hybrid_search", _fail_if_called)
    monkeypatch.setattr(nodes_module, "judge_sufficiency", _fail_if_called)

    from sententia.graph.build import build_graph

    app = build_graph()
    config = {"configurable": {"thread_id": "test-irrelevant-short-circuits"}}
    final_state = app.invoke(_initial_state("what's the weather"), config)

    assert final_state["relevant"] is False
    assert final_state["attempts"] == 0
    assert final_state["results"] == []
    assert final_state["answer"] == nodes_module.NOT_RELEVANT_MESSAGE
    assert "__interrupt__" not in final_state
