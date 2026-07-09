import sententia.graph.nodes as nodes_module
from sententia.retrieval.corpus import CorpusDocument


def test_search_stores_full_body_not_truncated_snippet(monkeypatch):
    """Regression test: search() used to truncate doc.body to 300 chars,
    silently hiding any content past that cutoff (e.g. a case's actual
    holding, buried after a long Facts section) from assess/generate."""
    long_body = ("Facts: " + "filler procedural history. " * 20) + (
        "Held: reasonable wear and tear means fair use consistent with age."
    )
    assert len(long_body) > 300
    assert "Held: reasonable wear and tear" not in long_body[:300]

    fake_doc = CorpusDocument(
        doc_id="test_doc",
        citation="Test v Case [2025] NSWCATCD 1",
        source_url="https://example.com",
        topic="wear and tear",
        court="NSWCATCD",
        kind="case",
        body=long_body,
    )
    monkeypatch.setattr(nodes_module, "hybrid_search", lambda **kwargs: [fake_doc])
    monkeypatch.setattr(nodes_module, "get_collection", lambda persist_dir: None)

    result = nodes_module.search({"query": "wear and tear", "attempts": 0, "results": []})

    assert len(result["results"]) == 1
    stored_text = result["results"][0]["text"]
    assert stored_text == long_body
    assert "Held: reasonable wear and tear" in stored_text
