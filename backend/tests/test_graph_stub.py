from sententia.graph.build import build_graph


def _initial_state(query: str) -> dict:
    return {
        "query": query,
        "attempts": 0,
        "results": [],
        "sufficient": False,
        "answer": None,
    }


def test_stub_graph_two_passes_then_terminates():
    """Acceptance bar from the brief: two search passes, correct loop,
    correct termination — verified against fixed stub data only."""
    app = build_graph()

    final_state = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW")
    )

    assert final_state["attempts"] == 2
    assert len(final_state["results"]) == 2
    assert final_state["sufficient"] is True
    assert final_state["answer"] is not None
    assert "STUB ANSWER" in final_state["answer"]
    assert "REDUCED CONFIDENCE" not in final_state["answer"]
