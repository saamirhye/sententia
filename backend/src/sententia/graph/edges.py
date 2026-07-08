from sententia.config import MAX_ATTEMPTS
from sententia.graph.state import GraphState


def route_after_assess(state: GraphState) -> str:
    """Loop back to search if insufficient and attempts remain; move to
    generate if sufficient; move to human_review if the step cap was hit
    without ever becoming sufficient -- a step-capped, reduced-confidence
    answer is no longer final without a human approving it first (phase 6)."""
    if state["sufficient"]:
        return "generate"
    if state["attempts"] >= MAX_ATTEMPTS:
        return "human_review"
    return "search"


def route_after_human_review(state: GraphState) -> str:
    """Approve -> generate, writing the real reduced-confidence answer as
    before. Decline -> end immediately; human_review has already streamed
    and set the fixed decline message itself, so generate has nothing left
    to do."""
    if state["human_approved"]:
        return "generate"
    return "declined"
