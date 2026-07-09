import json
import uuid
from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from sententia.api.schemas import ChatRequest, ResumeRequest
from sententia.graph.build import build_graph
from sententia.graph.state import GraphState

router = APIRouter()

# Module-level singleton: the InMemorySaver checkpointer lives on this
# specific compiled object. Building a fresh graph per request (the phase 5
# behavior) would mean /api/chat/resume could never find the state saved by
# the /api/chat call before it, since they'd be different checkpointers.
_graph = build_graph()


def _initial_state(query: str) -> GraphState:
    return {
        "query": query,
        "attempts": 0,
        "results": [],
        "relevant": None,
        "sufficient": False,
        "answer": None,
        "human_approved": None,
        "follow_up_questions": [],
    }


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _stream_events(stream_input: Any, thread_id: str) -> Iterator[str]:
    """Shared by /api/chat and /api/chat/resume -- they only differ in what
    they pass as stream_input (an initial state dict vs. a Command(resume=...)),
    the event-conversion logic is otherwise identical. A pause is detected via
    the "__interrupt__" key on a "values" chunk and turned into a
    human_review_required event carrying the thread_id needed for the
    matching /resume call, instead of the usual done event."""
    config = {"configurable": {"thread_id": thread_id}}
    final_state: GraphState | None = None
    interrupt_payload = None

    for mode, chunk in _graph.stream(stream_input, config, stream_mode=["custom", "values"]):
        if mode == "custom" and chunk.get("type") == "answer_delta":
            yield _sse("answer_delta", {"text": chunk["text"]})
        elif mode == "values":
            if "__interrupt__" in chunk:
                interrupt_payload = chunk["__interrupt__"][0].value
            else:
                final_state = chunk

    if interrupt_payload is not None:
        yield _sse("human_review_required", {"thread_id": thread_id, **interrupt_payload})
        return

    yield _sse(
        "done",
        {
            "results": final_state["results"],
            "sufficient": final_state["sufficient"],
            "attempts": final_state["attempts"],
            "follow_up_questions": final_state["follow_up_questions"],
        },
    )


@router.post("/api/chat")
def chat(request: ChatRequest) -> StreamingResponse:
    thread_id = str(uuid.uuid4())
    return StreamingResponse(
        _stream_events(_initial_state(request.query), thread_id), media_type="text/event-stream"
    )


@router.post("/api/chat/resume")
def resume(request: ResumeRequest) -> StreamingResponse:
    return StreamingResponse(
        _stream_events(Command(resume=request.approved), request.thread_id), media_type="text/event-stream"
    )
