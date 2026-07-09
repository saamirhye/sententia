from sententia.config import ANTHROPIC_MODEL_ASSESS
from sententia.graph.state import SearchResult
from sententia.llm.client import get_client

_FOLLOWUPS_TOOL = {
    "name": "record_follow_up_questions",
    "description": (
        "Record 2-3 follow-up questions a user might naturally want to ask "
        "next, based on the answer just given."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "description": (
                    "2-3 follow-up questions, each a fully self-contained "
                    "question with no reference to 'the above answer' or "
                    "similar -- see prompt for why."
                ),
                "items": {"type": "string"},
            },
        },
        "required": ["questions"],
        "additionalProperties": False,
    },
}


def _build_prompt(query: str, answer: str, results: list[SearchResult]) -> str:
    if not results:
        citations_block = "(no sources cited)"
    else:
        citations_block = "\n".join(f"- ({r['kind']}) {r['source']}" for r in results)
    return (
        "A user asked a legal research question and received the answer "
        "below. Suggest 2-3 natural follow-up questions this user might "
        "want to ask next.\n\n"
        "CRITICAL CONSTRAINT: each follow-up question MUST be fully "
        "self-contained. The system that will receive a follow-up click has "
        "ZERO memory of this conversation -- each question is sent as a "
        "brand-new, independent request with no prior context attached. "
        "Never phrase a follow-up as a continuation (e.g. 'What about the "
        "notice period?' or 'Does that apply to periodic leases too?'). "
        "Instead, restate enough of the original context that the question "
        "reads naturally on its own (e.g. 'What notice period applies when "
        "a landlord ends a lease for renovations in NSW?').\n\n"
        f"ORIGINAL QUERY:\n{query}\n\n"
        f"ANSWER GIVEN:\n{answer}\n\n"
        f"SOURCES CITED:\n{citations_block}\n\n"
        "Choose follow-ups that explore a genuinely different angle (a "
        "related right, an exception, a procedural next step) rather than "
        "rephrasing the same question. Call record_follow_up_questions with "
        "your choices."
    )


def generate_follow_up_questions(query: str, answer: str, results: list[SearchResult]) -> list[str]:
    """Calls Claude with forced tool use to get 2-3 self-contained follow-up
    questions grounded in the answer just given. Raises on any API/parsing
    failure -- callers (suggest_followups() node in nodes.py) are
    responsible for catching and applying the fail-safe default (empty
    list -- see that node's docstring for why an empty list, not raising,
    is correct here)."""
    client = get_client()
    response = client.messages.create(
        model=ANTHROPIC_MODEL_ASSESS,
        max_tokens=512,
        tools=[_FOLLOWUPS_TOOL],
        tool_choice={"type": "tool", "name": "record_follow_up_questions"},
        messages=[{"role": "user", "content": _build_prompt(query, answer, results)}],
    )
    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    return [str(q) for q in tool_use_block.input["questions"]]
