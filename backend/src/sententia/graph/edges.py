from sententia.config import MAX_ATTEMPTS
from sententia.graph.state import GraphState


def route_after_assess(state: GraphState) -> str:
    """Loop back to search if insufficient and attempts remain;
    otherwise move to generate (sufficient, OR step cap hit)."""
    if state["sufficient"]:
        return "generate"
    if state["attempts"] >= MAX_ATTEMPTS:
        return "generate"
    return "search"
