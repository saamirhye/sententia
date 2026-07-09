import sys
import uuid

from langgraph.types import Command

from sententia.graph.build import build_graph


def _initial_state(query: str) -> dict:
    return {
        "query": query,
        "attempts": 0,
        "results": [],
        "relevant": None,
        "sufficient": False,
        "answer": None,
        "human_approved": None,
    }


def _print_result(result: dict) -> None:
    print(f"Attempts: {result['attempts']}")
    print(f"Sufficient: {result['sufficient']}")
    print(f"Results: {result['results']}")
    print(f"Answer: {result['answer']}")


if __name__ == "__main__":
    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "can a landlord end a residential lease early for renovations in NSW"
    )

    app = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = app.invoke(_initial_state(query), config)

    if "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        print("\n--- Human review required ---")
        print(payload["question"])
        print(f"(attempts={payload['attempts']}, results so far: {len(payload['results'])})")
        raw = input("Approve reduced-confidence answer? [y/N]: ").strip().lower()
        result = app.invoke(Command(resume=raw in ("y", "yes")), config)

    _print_result(result)
