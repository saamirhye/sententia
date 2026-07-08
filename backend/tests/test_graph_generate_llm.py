import sententia.graph.nodes as nodes_module


def _initial_state(query: str) -> dict:
    return {
        "query": query,
        "attempts": 0,
        "results": [],
        "sufficient": False,
        "answer": None,
    }


def test_generate_node_falls_back_on_llm_failure(monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("simulated API failure")

    monkeypatch.setattr(nodes_module, "generate_answer", _raise)

    result = nodes_module.generate({"query": "q", "results": [], "sufficient": True})

    assert "answer" in result
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0


def test_graph_sufficient_path_uses_real_generate_answer(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)

    calls = {"n": 0}

    def _fake_judge(query, results):
        calls["n"] += 1
        return (calls["n"] >= 2), "stub reasoning"

    monkeypatch.setattr(nodes_module, "judge_sufficiency", _fake_judge)

    generate_calls = []

    def _fake_generate(query, results, sufficient):
        generate_calls.append(sufficient)
        return "MOCKED ANSWER: because reasons"

    monkeypatch.setattr(nodes_module, "generate_answer", _fake_generate)

    from sententia.graph.build import build_graph

    app = build_graph()
    final_state = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW")
    )

    assert final_state["answer"] == "MOCKED ANSWER: because reasons"
    assert generate_calls == [True]


def test_graph_step_cap_path_uses_real_generate_answer(monkeypatch, chroma_persist_dir):
    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "judge_sufficiency", lambda query, results: (False, "never enough"))

    generate_calls = []

    def _fake_generate(query, results, sufficient):
        generate_calls.append(sufficient)
        return "MOCKED REDUCED-CONFIDENCE ANSWER"

    monkeypatch.setattr(nodes_module, "generate_answer", _fake_generate)

    from sententia.graph.build import build_graph

    app = build_graph()
    final_state = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW")
    )

    assert final_state["answer"] == "MOCKED REDUCED-CONFIDENCE ANSWER"
    assert generate_calls == [False]
