from collections.abc import Iterator

from sententia.config import ANTHROPIC_MODEL_GENERATE
from sententia.graph.state import SearchResult
from sententia.llm.client import get_client


def _build_prompt(query: str, results: list[SearchResult], sufficient: bool) -> str:
    if not results:
        results_block = "(no results retrieved)"
    else:
        results_block = "\n\n".join(
            f"[{i + 1}] ({r['kind']}) {r['source']}\n{r['text']}"
            for i, r in enumerate(results)
        )

    if sufficient:
        confidence_instruction = (
            "The accumulated results were judged sufficient to answer confidently. "
            "Write a direct, well-supported answer."
        )
    else:
        confidence_instruction = (
            "The available research may be incomplete -- the search process reached "
            "its step cap without a judged-sufficient set of results. You MUST NOT "
            "present the answer as fully confident or complete. Explicitly flag, in "
            "the answer itself, that the research may not cover the full picture and "
            "that the reader should treat this as a partial/best-effort answer rather "
            "than a definitive one. Do not soften this into a throwaway disclaimer -- "
            "make the limitation genuinely legible to the reader."
        )

    return (
        "You are a legal research assistant writing an answer to the user's query, "
        "grounded ONLY in the sources provided below. Do not use any legal knowledge "
        "from your training -- if the provided sources do not cover something, say so "
        "rather than filling the gap from general knowledge. This is a retrieval-"
        "augmented system; an answer that isn't grounded in the retrieved sources "
        "defeats the point.\n\n"
        f"QUERY:\n{query}\n\n"
        f"RETRIEVED SOURCES ({len(results)}):\n{results_block}\n\n"
        f"{confidence_instruction}\n\n"
        "Formatting requirements:\n"
        "- Cite specific sources inline, by their exact citation string (e.g. "
        '"Residential Tenancies Act 2010 (NSW) ss 87F, 87G" or "Stewart v Wang '
        '[2024] NSWCATCD 70"), at the point in the answer where each source supports '
        "a claim -- not just listed at the end.\n"
        "- Write in plain prose paragraphs, not a bulleted source dump.\n"
        "- End with a brief, one-sentence note that this is general information, not "
        "legal advice, and the reader should seek advice for their specific situation.\n\n"
        "Write the answer now."
    )


def generate_answer(query: str, results: list[SearchResult], sufficient: bool) -> str:
    """Calls Claude (plain messages.create, no tools) to synthesize a cited answer
    grounded in the accumulated search results. Raises on any API/parsing failure --
    generate() in nodes.py is responsible for catching and applying a fail-safe
    fallback answer."""
    client = get_client()
    response = client.messages.create(
        model=ANTHROPIC_MODEL_GENERATE,
        max_tokens=1024,
        messages=[{"role": "user", "content": _build_prompt(query, results, sufficient)}],
    )
    text_block = next(b for b in response.content if b.type == "text")
    return text_block.text


def generate_answer_stream(query: str, results: list[SearchResult], sufficient: bool) -> Iterator[str]:
    """Calls Claude (client.messages.stream, no tools) and yields text deltas as they
    arrive. Reuses _build_prompt -- same prompt as generate_answer, only the transport
    differs. Lets mid-stream errors propagate after any chunks already yielded, rather
    than swallowing them here -- generate() in nodes.py has already relayed those chunks
    to the caller by the time an error surfaces, so it appends a failure note to the
    partial answer instead of replacing it."""
    client = get_client()
    with client.messages.stream(
        model=ANTHROPIC_MODEL_GENERATE,
        max_tokens=1024,
        messages=[{"role": "user", "content": _build_prompt(query, results, sufficient)}],
    ) as stream:
        yield from stream.text_stream
