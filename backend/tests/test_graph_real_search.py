from sententia.retrieval.corpus import load_corpus
from sententia.retrieval.hybrid_search import CORPUS_DIR


def _initial_state(query: str) -> dict:
    return {
        "query": query,
        "attempts": 0,
        "results": [],
        "sufficient": False,
        "answer": None,
        "human_approved": None,
    }


def test_graph_two_passes_then_terminates_with_real_search(monkeypatch, chroma_persist_dir):
    """End-to-end acceptance bar carried over from phase 1, now with real
    retrieval: two search passes, correct loop, correct termination. Assertions
    are anchored to real corpus citations (proving fake stub data is gone)
    rather than to a specific expected top result, since hybrid search over
    this small corpus doesn't guarantee any single document ranks first for
    every query -- see test_retrieval.py for the actual ranking-quality
    assertions.

    assess and generate are both real now (phases 3-4) -- to keep this test
    scoped to search (its original phase 2 purpose) rather than depending on a
    live API key, judge_sufficiency is monkeypatched back to the old
    count-based heuristic it replaced, and generate_answer is mocked to a
    fixed string. Real assess/generate + real search together are covered by
    test_graph_assess_llm.py and test_graph_generate_llm.py's mocked tests.

    SEARCH_TOP_K is separately pinned to 1 here (production default is now 2,
    tuned once assess became real) so this test keeps exercising exactly two
    passes regardless of future production tuning -- its point is proving the
    loop/accumulation/exclusion machinery works with real search, not pinning
    down a specific top_k value."""
    import sententia.graph.nodes as nodes_module

    monkeypatch.setattr(nodes_module, "CHROMA_PERSIST_DIR", chroma_persist_dir)
    monkeypatch.setattr(nodes_module, "SEARCH_TOP_K", 1)
    monkeypatch.setattr(
        nodes_module, "judge_sufficiency", lambda query, results: (len(results) >= 2, "stub heuristic")
    )
    monkeypatch.setattr(nodes_module, "generate_answer_stream", lambda *a, **kw: iter(["MOCKED ANSWER"]))

    from sententia.graph.build import build_graph

    app = build_graph()
    config = {"configurable": {"thread_id": "test-real-search-two-passes"}}
    final_state = app.invoke(
        _initial_state("can a landlord end a residential lease early for renovations in NSW"), config
    )

    assert final_state["attempts"] == 2
    assert len(final_state["results"]) == 2
    assert final_state["sufficient"] is True
    assert final_state["answer"] == "MOCKED ANSWER"

    # Prove real retrieval, not the old fake stub data: every returned citation
    # must be a genuine corpus citation, and the two results must be distinct
    # (no duplicate across the two passes).
    real_citations = {doc.citation for doc in load_corpus(CORPUS_DIR)}
    result_citations = [r["source"] for r in final_state["results"]]
    assert all(citation in real_citations for citation in result_citations)
    assert len(set(result_citations)) == 2
