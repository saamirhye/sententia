from sententia.graph.state import GraphState, SearchResult

# Fixed fake corpus hits, keyed by attempt number, so a second pass visibly
# returns additional results rather than repeating the first.
_STUB_RESULTS_BY_ATTEMPT: dict[int, list[SearchResult]] = {
    1: [
        {
            "source": "Residential Tenancies Act 2010 (NSW) s 100",
            "snippet": "A landlord may give a termination notice for renovations...",
            "kind": "legislation",
        },
    ],
    2: [
        {
            "source": "Cives Property Group v Tenant [2019] NSWCATCD 12",
            "snippet": "The Tribunal considered what constitutes genuine renovation intent...",
            "kind": "case",
        },
    ],
}


def search(state: GraphState) -> dict:
    """Stub: returns fixed fake results keyed by attempt number.
    Real version (phase 2) queries Chroma hybrid search instead."""
    attempt = state["attempts"] + 1
    new_results = _STUB_RESULTS_BY_ATTEMPT.get(attempt, [])
    return {"attempts": attempt, "results": new_results}


def assess(state: GraphState) -> dict:
    """Stub: heuristic on result count only (no LLM call).
    Real version (phase 3) asks Claude to judge sufficiency."""
    return {"sufficient": len(state["results"]) >= 2}


def generate(state: GraphState) -> dict:
    """Stub: string concatenation of accumulated results, no LLM call.
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
