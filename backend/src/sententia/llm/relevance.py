from sententia.config import ANTHROPIC_MODEL_ASSESS
from sententia.llm.client import get_client

_RELEVANCE_TOOL = {
    "name": "record_relevance_judgment",
    "description": (
        "Record whether a user's legal research query is plausibly relevant to "
        "a fixed corpus covering NSW residential tenancy law."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "relevant": {
                "type": "boolean",
                "description": (
                    "True if the query is plausibly answerable from the corpus, or "
                    "genuinely ambiguous/borderline. False only if the query is "
                    "clearly and obviously unrelated to NSW residential tenancy law."
                ),
            },
            "reasoning": {
                "type": "string",
                "description": "Brief explanation of the judgment (1-2 sentences).",
            },
        },
        "required": ["relevant", "reasoning"],
        "additionalProperties": False,
    },
}

_CORPUS_TOPICS = (
    "1. Rent increases (notice requirements; challenging excessive increases)\n"
    "2. Repairs (landlord's repair obligations; habitability)\n"
    "3. Bonds (payment, release, deductions, \"fair wear and tear\")\n"
    "4. Tenant-initiated early termination of a lease\n"
    "5. Landlord termination of a lease for renovations or demolition\n"
    "6. Renovation disruption, quiet enjoyment, and retaliatory termination notices"
)


def _build_prompt(query: str) -> str:
    return (
        "You are a coarse relevance pre-filter for a legal research assistant "
        "whose corpus covers ONLY these six NSW (New South Wales, Australia) "
        f"residential tenancy law topics:\n\n{_CORPUS_TOPICS}\n\n"
        "Your ONLY job is to catch queries that are OBVIOUSLY unrelated to this "
        "corpus -- general trivia, casual conversation, other areas of law "
        "entirely, other countries' or other Australian states' tenancy law, "
        "or anything with no plausible connection to NSW residential tenancy. "
        "You are NOT a strict topic gate: genuine tenancy questions that are "
        "ambiguous, oddly phrased, or on the margins of these six topics should "
        "still be marked relevant -- a downstream search/assessment step already "
        "handles that nuance and has its own human-review safety net.\n\n"
        "When in doubt, mark relevant=True. A false rejection (blocking a "
        "legitimate tenancy question) is a worse failure than a false "
        "acceptance (letting an unrelated-seeming query through, since the "
        "downstream step will correctly flag it as insufficient anyway).\n\n"
        f"QUERY:\n{query}\n\n"
        "Call record_relevance_judgment with your determination."
    )


def judge_relevance(query: str) -> tuple[bool, str]:
    """Calls Claude with forced tool use to get a reliable {relevant, reasoning}
    judgment about whether a raw query is even plausibly in-scope for this
    corpus, before any search has run. Unlike judge_sufficiency, this only ever
    sees the query -- there are no accumulated results yet, by design (this
    runs before search).

    Raises on any API/parsing failure -- callers (check_relevance() in
    nodes.py) are responsible for catching and applying the fail-safe default,
    exactly like judge_sufficiency/assess()."""
    client = get_client()
    response = client.messages.create(
        model=ANTHROPIC_MODEL_ASSESS,
        max_tokens=512,
        tools=[_RELEVANCE_TOOL],
        tool_choice={"type": "tool", "name": "record_relevance_judgment"},
        messages=[{"role": "user", "content": _build_prompt(query)}],
    )
    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    tool_input = tool_use_block.input
    return bool(tool_input["relevant"]), str(tool_input["reasoning"])
