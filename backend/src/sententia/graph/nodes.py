from langgraph.config import get_stream_writer
from langgraph.types import interrupt

from sententia.config import CHROMA_PERSIST_DIR
from sententia.graph.state import GraphState, SearchResult
from sententia.llm.assess import judge_sufficiency
from sententia.llm.generate import generate_answer_stream
from sententia.retrieval.hybrid_search import get_collection, hybrid_search

DECLINE_MESSAGE = (
    "No answer was generated. The available research did not reach a confident "
    "conclusion within the search step limit, and the reduced-confidence answer "
    "was declined at the human review checkpoint."
)

# Was 1 during phase 2, to keep the loop exercised while assess was still a dumb
# len(results) >= 2 stub. Now that assess (phase 3) is a real Claude judgment, that
# coupling is gone -- bumped to 2 so real retrieval gets more candidates per pass
# and has a genuine shot at surfacing the correct provision within MAX_ATTEMPTS,
# rather than being structurally capped at the first couple of ranked results.
SEARCH_TOP_K = 2


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
    """Real (phase 3): asks Claude (forced tool use) whether accumulated results
    are sufficient. On any failure (missing/invalid key, network error, timeout,
    malformed response), defaults to sufficient=False rather than raising --
    MAX_ATTEMPTS/route_after_assess already exists to cap the loop, so "give up
    gracefully" is safer than crashing the graph. Intentionally never touches
    "results" -- LangGraph only applies a field's reducer when a node's
    returned dict includes that key, so omitting it here correctly means "no
    change to results", not "reduce with nothing"."""
    try:
        sufficient, reasoning = judge_sufficiency(state["query"], state["results"])
    except Exception as exc:
        print(f"[assess] Claude sufficiency judgment failed, defaulting to sufficient=False: {exc!r}")
        return {"sufficient": False}
    print(f"[assess] sufficient={sufficient} reasoning={reasoning!r}")
    return {"sufficient": sufficient}


def human_review(state: GraphState) -> dict:
    """Real (phase 6): the step-cap path's human-in-the-loop checkpoint.
    Reached only via route_after_assess's step-cap branch -- the sufficient
    path goes straight from assess to generate, untouched.

    LangGraph re-executes this whole function from the top when the graph is
    resumed (confirmed: only the interrupted node re-runs, not the nodes
    before it), so nothing before the interrupt() call may have an
    observable effect -- no print(), no LLM call. get_stream_writer() itself
    is safe to call early (it doesn't write anything until invoked with a
    payload), matching generate()'s existing structure.

    On approve: only sets human_approved -- "answer" stays None, generate
    sets it for real next. On decline: streams the fixed decline message as
    an answer_delta chunk (the same channel generate() uses -- there's no
    separate "the answer arrived via a different field" case for callers to
    handle) and sets "answer" directly, since generate/generate_answer_stream
    must never run in this branch."""
    writer = get_stream_writer()
    decision = interrupt(
        {
            "question": (
                "Search hit the step limit without reaching a confident answer. "
                "Proceed with a reduced-confidence, hedged answer anyway?"
            ),
            "query": state["query"],
            "attempts": state["attempts"],
            "results": state["results"],
        }
    )
    if decision:
        print("[human_review] approved -- proceeding to generate")
        return {"human_approved": True}
    writer({"type": "answer_delta", "text": DECLINE_MESSAGE})
    print("[human_review] declined -- ending without generating")
    return {"human_approved": False, "answer": DECLINE_MESSAGE}


def generate(state: GraphState) -> dict:
    """Real (phase 4), streaming (phase 5): asks Claude to synthesize a cited answer,
    honest about reduced confidence when the step cap was hit, relaying each token
    chunk out through LangGraph's stream writer as it arrives. Under plain .invoke()
    (e.g. run_stub.py, most tests), get_stream_writer() resolves to LangGraph's
    built-in no-op writer, so this call is inert and behavior is identical to phase 4;
    under the FastAPI endpoint's graph.stream(..., stream_mode="custom"), each chunk
    is relayed live to the client. On any failure, falls back to a clear, honest
    degraded-answer string rather than raising -- generate is the terminal node
    before END, so there's no "loop again" recovery path; crashing the whole
    invocation on an API hiccup would be worse than a visibly-labeled fallback.
    If some chunks already streamed before the failure, they've already reached
    the client and can't be un-sent, so the fallback is appended as a visible
    continuation rather than replacing the whole answer. Never touches "results"
    -- see note in assess()."""
    writer = get_stream_writer()
    chunks: list[str] = []
    try:
        for chunk in generate_answer_stream(state["query"], state["results"], state["sufficient"]):
            chunks.append(chunk)
            writer({"type": "answer_delta", "text": chunk})
        answer = "".join(chunks)
    except Exception as exc:
        print(f"[generate] Claude answer synthesis failed, falling back to a degraded answer: {exc!r}")
        citations = "; ".join(r["source"] for r in state["results"]) or "no sources retrieved"
        fallback = (
            "I wasn't able to generate a full answer due to a technical issue "
            "(the answer-writing step failed). Based on the research gathered so far, "
            f"the following sources may be relevant: {citations}. Please try again, "
            "or consult a legal professional directly."
        )
        writer({"type": "answer_delta", "text": fallback})
        answer = "".join(chunks) + (" " if chunks else "") + fallback
    return {"answer": answer}
