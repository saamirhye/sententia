from sententia.graph.edges import route_after_assess


def test_sufficient_routes_to_generate_regardless_of_attempts():
    assert route_after_assess({"sufficient": True, "attempts": 1}) == "generate"
    assert route_after_assess({"sufficient": True, "attempts": 3}) == "generate"


def test_insufficient_with_attempts_remaining_routes_to_search():
    assert route_after_assess({"sufficient": False, "attempts": 1}) == "search"


def test_insufficient_at_step_cap_routes_to_generate():
    assert route_after_assess({"sufficient": False, "attempts": 3}) == "generate"
