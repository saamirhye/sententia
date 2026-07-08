import json
from collections.abc import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from sententia.api.schemas import ChatRequest
from sententia.graph.build import build_graph
from sententia.graph.state import GraphState

router = APIRouter()


def _initial_state(query: str) -> GraphState:
    return {"query": query, "attempts": 0, "results": [], "sufficient": False, "answer": None}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _stream_chat_events(query: str) -> Iterator[str]:
    graph = build_graph()
    final_state: GraphState | None = None
    for mode, chunk in graph.stream(_initial_state(query), stream_mode=["custom", "values"]):
        if mode == "custom" and chunk.get("type") == "answer_delta":
            yield _sse("answer_delta", {"text": chunk["text"]})
        elif mode == "values":
            final_state = chunk

    yield _sse(
        "done",
        {
            "results": final_state["results"],
            "sufficient": final_state["sufficient"],
            "attempts": final_state["attempts"],
        },
    )


@router.post("/api/chat")
def chat(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(_stream_chat_events(request.query), media_type="text/event-stream")
