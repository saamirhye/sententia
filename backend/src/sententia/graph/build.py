from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from sententia.graph.edges import (
    route_after_assess,
    route_after_check_relevance,
    route_after_human_review,
)
from sententia.graph.nodes import assess, check_relevance, generate, human_review, search, suggest_followups
from sententia.graph.state import GraphState


def build_graph():
    """Compiles with an InMemorySaver checkpointer -- required as of phase 6
    because human_review calls interrupt(), which needs checkpointed state to
    pause/resume. Every caller must now pass a config with a "thread_id",
    even on runs that never reach human_review (LangGraph raises ValueError
    on any call with no thread_id once a checkpointer is present at all).
    Callers that need to resume a paused run (the API, run_stub.py) must
    reuse the same compiled graph object -- and thus the same checkpointer
    instance -- across the initial call and the resume call."""
    graph = StateGraph(GraphState)

    graph.add_node("check_relevance", check_relevance)
    graph.add_node("search", search)
    graph.add_node("assess", assess)
    graph.add_node("human_review", human_review)
    graph.add_node("generate", generate)
    graph.add_node("suggest_followups", suggest_followups)

    graph.add_edge(START, "check_relevance")
    graph.add_conditional_edges(
        "check_relevance",
        route_after_check_relevance,
        {"search": "search", "not_relevant": END},
    )
    graph.add_edge("search", "assess")
    graph.add_conditional_edges(
        "assess",
        route_after_assess,
        {"search": "search", "generate": "generate", "human_review": "human_review"},
    )
    graph.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {"generate": "generate", "declined": END},
    )
    graph.add_edge("generate", "suggest_followups")
    graph.add_edge("suggest_followups", END)

    return graph.compile(checkpointer=InMemorySaver())
