from langgraph.graph import END, START, StateGraph

from sententia.graph.edges import route_after_assess
from sententia.graph.nodes import assess, generate, search
from sententia.graph.state import GraphState


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("search", search)
    graph.add_node("assess", assess)
    graph.add_node("generate", generate)

    graph.add_edge(START, "search")
    graph.add_edge("search", "assess")
    graph.add_conditional_edges(
        "assess",
        route_after_assess,
        {"search": "search", "generate": "generate"},
    )
    graph.add_edge("generate", END)

    return graph.compile()
