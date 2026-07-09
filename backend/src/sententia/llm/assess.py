from sententia.config import ANTHROPIC_MODEL_ASSESS
from sententia.graph.state import SearchResult
from sententia.llm.client import get_client

_SUFFICIENCY_TOOL = {
    "name": "record_sufficiency_judgment",
    "description": (
        "Record whether the accumulated search results are sufficient to "
        "confidently answer the legal query."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "sufficient": {
                "type": "boolean",
                "description": "True if the results are enough to answer confidently.",
            },
            "reasoning": {
                "type": "string",
                "description": "Brief explanation of the judgment (1-3 sentences).",
            },
        },
        "required": ["sufficient", "reasoning"],
        "additionalProperties": False,
    },
}


def _build_prompt(query: str, results: list[SearchResult]) -> str:
    if not results:
        results_block = "(no results retrieved yet)"
    else:
        results_block = "\n\n".join(
            f"[{i + 1}] ({r['kind']}) {r['source']}\n{r['text']}"
            for i, r in enumerate(results)
        )
    return (
        "You are assessing whether accumulated legal search results are "
        "sufficient to confidently answer a user's legal research query, "
        "or whether another search pass is genuinely needed.\n\n"
        f"QUERY:\n{query}\n\n"
        f"ACCUMULATED RESULTS ({len(results)} so far):\n{results_block}\n\n"
        "Judge sufficiency by weighing:\n"
        "- Topical coverage: do the results address the substance of the query, "
        "not just keyword overlap?\n"
        "- Source diversity: for questions that turn on both a statutory rule and "
        "its judicial interpretation, are both legislation AND case law "
        "represented? A single legislative section with no case law (or vice "
        "versa) may be sufficient for a narrow factual question, but insufficient "
        "for a question likely to be contested or interpreted.\n"
        "- Sub-question coverage: if the query has multiple parts (e.g. "
        "'can X happen, and what notice period applies'), are all parts "
        "addressed, or is there a genuine gap?\n"
        "- Do not default to 'insufficient' out of caution alone -- if the "
        "results genuinely answer the query, say so.\n\n"
        "Call record_sufficiency_judgment with your determination."
    )


def judge_sufficiency(query: str, results: list[SearchResult]) -> tuple[bool, str]:
    """Calls Claude with forced tool use to get a reliable {sufficient, reasoning}
    judgment. Raises on any API/parsing failure -- callers (assess() in
    nodes.py) are responsible for catching and applying the fail-safe default."""
    client = get_client()
    response = client.messages.create(
        model=ANTHROPIC_MODEL_ASSESS,
        max_tokens=512,
        tools=[_SUFFICIENCY_TOOL],
        tool_choice={"type": "tool", "name": "record_sufficiency_judgment"},
        messages=[{"role": "user", "content": _build_prompt(query, results)}],
    )
    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    tool_input = tool_use_block.input
    return bool(tool_input["sufficient"]), str(tool_input["reasoning"])
