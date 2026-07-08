from sententia.config import CHROMA_PERSIST_DIR
from sententia.graph.state import GraphState, SearchResult
from sententia.retrieval.hybrid_search import get_collection, hybrid_search

# Kept small deliberately: assess (below) fires once results has >= 2 items, and
# results accumulates via operator.add across passes (see state.py). With top_k=1,
# a query needs two search passes to cross that threshold, so the loop-back edge
# keeps getting exercised end-to-end with real data, not just single-shot retrieval
# quality. Revisit once assess becomes a real LLM judgment (phase 3) and this
# coupling to a raw result count goes away.
SEARCH_TOP_K = 1


def search(state: GraphState) -> dict:
    """Real (phase 2): Chroma hybrid (vector + BM25, fused via RRF) search over the
    fixed corpus. Excludes citations already retrieved in prior passes so a second
    pass, if triggered, surfaces different results instead of repeats.

    Always returns a well-formed (possibly empty) list for "results" -- never omits
    the key or returns None -- so the operator.add reducer on GraphState.results
    always has a valid list to concatenate against, even if retrieval finds nothing."""
    attempt = state["attempts"] + 1
    already_seen = {r["source"] for r in state["results"]}
    collection = get_collection(CHROMA_PERSIST_DIR)
    docs = hybrid_search(
        collection=collection,
        query=state["query"],
        top_k=SEARCH_TOP_K,
        exclude_citations=already_seen,
    )
    new_results: list[SearchResult] = [
        {
            "source": doc.citation,
            "snippet": doc.body[:300].strip() + ("..." if len(doc.body) > 300 else ""),
            "kind": doc.kind,
        }
        for doc in docs
    ]
    return {"attempts": attempt, "results": new_results}


def assess(state: GraphState) -> dict:
    """Stub: heuristic on result count only (no LLM call). Intentionally never
    touches "results" -- LangGraph only applies a field's reducer when a node's
    returned dict includes that key, so omitting it here correctly means "no
    change to results", not "reduce with nothing".
    Real version (phase 3) asks Claude to judge sufficiency."""
    return {"sufficient": len(state["results"]) >= 2}


def generate(state: GraphState) -> dict:
    """Stub: string concatenation of accumulated results, no LLM call. Also never
    touches "results" -- see note in assess() above.
    Real version (phase 4) streams a cited answer from Claude."""
    citations = "; ".join(r["source"] for r in state["results"])
    if state["sufficient"]:
        answer = f"[STUB ANSWER] Based on {citations}: <placeholder answer text>."
    else:
        answer = (
            f"[STUB ANSWER - REDUCED CONFIDENCE, step cap reached] "
            f"Best available from {citations}: <placeholder answer text>."
        )
    return {"answer": answer}
