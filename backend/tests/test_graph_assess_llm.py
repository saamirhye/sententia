import sententia.graph.nodes as nodes_module


def _initial_state(query: str) -> dict:
    return {
        "query": query,
        "attempts": 0,
        "results": [],
        "sufficient": False,
        "answer": None,
    }


def test_assess_node_defaults_to_insufficient_on_llm_failure(monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("simulated API failure")

    monkeypatch.setattr(nodes_module, "judge_sufficiency", _raise)

    result = nodes_module.assess({"query": "q", "results": []})

    assert result == {"sufficient": False}


def test_graph_loop_with_mocked_assess_two_passes_then_terminates(monkeypatch, chroma_persist_dir):
    """Simulates insufficient on pass 1, sufficient on pass 2 -- loop runs
    twice and terminates via the sufficient path, not the step cap."""
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)

    calls = {"n": 0}

    def _fake_judge(query, results):
        calls["n"] += 1
        return (calls["n"] >= 2), "stub reasoning"

    monkeypatch.setattr(nodes_module, "judge_sufficiency", _fake_judge)

    from sententia.graph.build import build_graph

    app = build_graph()
    final_state = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW")
    )

    assert final_state["attempts"] == 2
    assert final_state["sufficient"] is True
    assert "STUB ANSWER" in final_state["answer"]
    assert "REDUCED CONFIDENCE" not in final_state["answer"]


def test_graph_loop_hits_step_cap_when_always_insufficient(monkeypatch, chroma_persist_dir):
    """Simulates insufficient for all MAX_ATTEMPTS passes -- step cap still
    terminates the loop and generate's reduced-confidence stub path fires."""
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (False, "never enough"))

    from sententia.graph.build import build_graph

    app = build_graph()
    final_state = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW")
    )

    assert final_state["attempts"] == 3  # MAX_ATTEMPTS
    assert final_state["sufficient"] is False
    assert "REDUCED CONFIDENCE" in final_state["answer"]
