from sententia.graph.build import build_graph

if __name__ == "__main__":
    app = build_graph()
    result = app.invoke(
        {
            "query": "can a landlord end a residential lease early for renovations in NSW",
            "attempts": 0,
            "results": [],
            "sufficient": False,
            "answer": None,
        }
    )
    print(f"Attempts: {result['attempts']}")
    print(f"Sufficient: {result['sufficient']}")
    print(f"Results: {result['results']}")
    print(f"Answer: {result['answer']}")
