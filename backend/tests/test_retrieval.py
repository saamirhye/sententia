from sententia.retrieval.corpus import load_corpus
from sententia.retrieval.hybrid_search import CORPUS_DIR, get_collection, hybrid_search


def test_corpus_loads_all_twelve_documents():
    docs = load_corpus(CORPUS_DIR)
    assert len(docs) == 12
    assert sum(1 for d in docs if d.kind == "legislation") == 6
    assert sum(1 for d in docs if d.kind == "case") == 6
    for doc in docs:
        assert doc.citation
        assert doc.body


def test_distractor_query_prefers_s87f_over_s100(chroma_persist_dir):
    """Acceptance bar documented in corpus/README.md: for the running example query,
    hybrid retrieval must rank the real landlord-renovation termination ground
    (s 87F) ahead of the superficially similar but wrong tenant-termination
    section (s 100), which is kept in the corpus deliberately as a near-miss."""
    collection = get_collection(chroma_persist_dir)
    query = "can a landlord end a residential lease early for renovations in NSW"
    docs = hybrid_search(collection=collection, query=query, top_k=12)
    doc_ids = [doc.doc_id for doc in docs]

    assert "rta2010_s87f_87g_termination_renovation_demolition" in doc_ids
    assert "rta2010_s100_tenant_early_termination" in doc_ids
    assert doc_ids.index("rta2010_s87f_87g_termination_renovation_demolition") < doc_ids.index(
        "rta2010_s100_tenant_early_termination"
    )


def test_exclude_citations_returns_different_results_on_second_call(chroma_persist_dir):
    collection = get_collection(chroma_persist_dir)
    query = "can a landlord end a residential lease early for renovations in NSW"
    first = hybrid_search(collection=collection, query=query, top_k=1)
    assert len(first) == 1

    second = hybrid_search(
        collection=collection,
        query=query,
        top_k=1,
        exclude_citations={first[0].citation},
    )
    assert len(second) == 1
    assert second[0].citation != first[0].citation


def test_hybrid_search_returns_empty_list_when_all_candidates_excluded(chroma_persist_dir):
    collection = get_collection(chroma_persist_dir)
    docs = load_corpus(CORPUS_DIR)
    all_citations = {doc.citation for doc in docs}
    query = "can a landlord end a residential lease early for renovations in NSW"

    results = hybrid_search(
        collection=collection,
        query=query,
        top_k=1,
        exclude_citations=all_citations,
    )
    assert results == []


def test_search_node_handles_empty_retrieval_gracefully(monkeypatch):
    """search() must always return a well-formed (possibly empty) list for
    "results" -- never omit the key or return None -- so the operator.add
    reducer on GraphState.results always has a valid list to merge against,
    even when hybrid_search legitimately finds nothing."""
    import sententia.graph.nodes as nodes_module

    monkeypatch.setattr(nodes_module, "hybrid_search", lambda **kwargs: [])
    monkeypatch.setattr(nodes_module, "get_collection", lambda persist_dir: None)

    result = nodes_module.search({"query": "irrelevant query", "attempts": 0, "results": []})

    assert result["results"] == []
    assert result["attempts"] == 1
