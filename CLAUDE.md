# Sententia — operating notes

**Current phase:** The full `search → assess → generate` loop is real end to end — `search` (Chroma hybrid retrieval), `assess` (Claude Haiku, forced tool use sufficiency judgment), and `generate` (Claude Sonnet 5, non-streaming, grounded/cited answer synthesis) — sequencing steps 1-4 complete. Verified live: correct citations, honest hedging when the step cap is hit. See `backend/src/sententia/llm/`. Next up: add streaming (Claude streaming → FastAPI `StreamingResponse` → frontend SSE consumer, step 5), only after non-streaming (this phase) is solid. Update this line at the start of each new phase.

## What this is

An agentic legal research assistant that decides at runtime how many search passes it needs before answering, instead of a fixed one-shot RAG call. It searches legislation and case law, assesses whether it has enough to answer confidently, and either loops back to search or generates a cited answer — capped at `MAX_ATTEMPTS`, with a reduced-confidence note if it hits the cap without being sure.

Personal learning project. The point is defensible understanding of agentic AI architecture (LangGraph, multi-step reasoning loops, human-in-the-loop), explainable in detail for job interviews — not just a working demo. See `docs/brief.md` for the full "why agent vs. workflow" rationale (Ledgify comparison) if that context is ever needed; it's not repeated here because it doesn't change any code decision.

## Tech stack (fixed — do not substitute)

- **Backend:** Python, LangGraph, FastAPI.
- **Retrieval:** Chroma (local vector store), hybrid search (keyword + vector) over a small fixed corpus — NSW/Commonwealth statutes + ~10 NCAT/tribunal judgments, manually curated, not scraped.
- **Generation:** Claude API (Anthropic), streamed.
- **Frontend:** Next.js (App Router), Tailwind, shadcn/ui. Font: Google Fonts only (OFL-licensed) — Space Grotesk / IBM Plex Sans / Public Sans family. No paid/commercial fonts.

## Architecture

```
START -> search -> assess --sufficient?--> generate -> END
            ^                  |
            |__________________| (insufficient, attempts remain)
```

- `search`: retrieves from the corpus (stub: fixed fake results; real: Chroma hybrid search).
- `assess`: decides if there's enough to answer confidently (stub: heuristic on result count; real: LLM call judging sufficiency).
- `route_after_assess`: conditional edge — loops back to `search`, or moves to `generate` if sufficient OR the step cap (`MAX_ATTEMPTS`) is hit.
- `generate`: produces the final cited answer (stub: string concatenation; real: streamed Claude call).

Planned: a human-in-the-loop checkpoint (LangGraph `interrupt`) before treating a step-capped, reduced-confidence answer as final.

## Build methodology — stub first, real second

Always verify orchestration logic against fixed, fake data before introducing a real (non-deterministic) retrieval or generation layer. This isolates two independent risks — control flow correctness vs. retrieval/generation quality — so a bad run points at one layer, not both. Swap **one node at a time** (stub → real), never all at once.

## Sequencing

1. Corpus: finalize the fixed statute/judgment set (plain text, manually sourced from AustLII — no scraper).
2. Swap `search` to real Chroma retrieval. Keep `assess`/`generate` stub. Verify retrieval quality in isolation.
3. Swap `assess` to a real Claude sufficiency call. Verify the loop still behaves correctly.
4. Swap `generate` to a real, non-streaming Claude call. Verify.
5. Add streaming (Claude streaming -> FastAPI `StreamingResponse` -> frontend SSE consumer) — only after step 4 works non-streaming.
6. Add the human-in-the-loop checkpoint on the step-cap path.
7. Minimal Next.js frontend: chat UI, SSE streaming consumption, pre-generated starter-prompt chips (generated once from the corpus, not at runtime), citation chips per answer.

**Out of scope for this pass:** cross-jurisdiction equivalence mapping, working-paper/export features, auth, multi-user accounts.

## Working style

- Use Plan Mode (or an equivalent review step) for architectural decisions — review and understand the proposed approach before approving, don't just accept the first diff.
- After each stub → real swap, do a short teach-back: explain in your own words why the swap works before moving to the next node.
- Commit after each verified working step, not in one large commit at the end.
