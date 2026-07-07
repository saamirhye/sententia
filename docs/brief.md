# Sententia — project brief

Hand this file to any tool (Claude Code, Cursor, etc.) at the start of a
session so it has full context without re-explaining from scratch. It
doubles as the seed content for `CLAUDE.md`.

## What this is

An agentic legal research assistant that decides at runtime how many
search passes it needs before answering, instead of a fixed one-shot RAG
call. Given a query (e.g. "can a landlord end a residential lease early
for renovations in NSW"), it searches legislation and case law, assesses
whether it has enough to answer confidently, and either loops back to
search again or generates a cited answer — capped at a fixed number of
attempts, with a note flagging reduced confidence if it hits the cap
without being sure.

This is a personal learning project, not a client deliverable. The goal
is genuine, defensible understanding of agentic AI architecture (LangGraph,
multi-step reasoning loops, human-in-the-loop patterns) — buildable and
explainable in detail for job interviews, not just a working demo.

## Why this shape, specifically

Modelled in part on a friend's project (Ledgify, an audit-standards
research tool) which deliberately chose a **fixed, code-orchestrated
pipeline over an agent**, because auditing demands reproducibility.
Sententia makes the opposite, equally deliberate choice: legal research
genuinely needs a runtime decision ("do I have enough, or is there a gap
worth another search pass?") that can't be hardcoded — so an agent loop is
justified here, capped and observable rather than open-ended.

Being able to articulate *why* agent vs. workflow was chosen, for this
specific problem, is the actual point of the project.

## Tech stack

- **Backend:** Python, LangGraph, FastAPI. Python chosen deliberately over
  Node/TypeScript (the author's usual stack) because LangGraph's Python
  implementation has more mature checkpointing/interrupt support for
  human-in-the-loop, and because most agentic-AI hiring/tooling content
  assumes Python — this project is also meant to close that gap.
- **Retrieval:** Chroma (local vector store), hybrid search (keyword +
  vector) over a small fixed corpus — a handful of NSW/Commonwealth
  statutes plus ~10 NCAT/tribunal judgments, manually curated, not
  scraped.
- **Generation:** Claude API (Anthropic), streamed.
- **Frontend:** Next.js (App Router), Tailwind, shadcn/ui. React chosen
  deliberately as a skills gap-filler (author's background is Angular).
  Font: Google Fonts only (OFL-licensed), something in the Space
  Grotesk / IBM Plex Sans / Public Sans family — not a paid/commercial
  font, for both licensing-cleanliness and self-hosting reasons.

## Architecture

```
START -> search -> assess --sufficient?--> generate -> END
            ^                  |
            |__________________| (insufficient, attempts remain)
```

- `search` node: retrieves from the corpus (stub: fixed fake results;
  real: Chroma hybrid search)
- `assess` node: decides if there's enough to answer confidently (stub:
  heuristic on result count; real: an LLM call judging sufficiency)
- `route_after_assess`: conditional edge — loops back to `search`, or
  moves to `generate` if sufficient OR if the step cap (`MAX_ATTEMPTS`)
  is hit
- `generate` node: produces the final cited answer (stub: string
  concatenation; real: streamed Claude call)

Planned addition: a human-in-the-loop checkpoint (LangGraph `interrupt`)
before treating a step-capped, reduced-confidence answer as final —
rather than silently showing it to the user as authoritative.

## Build methodology — stub first, real second

Always verify orchestration logic against fixed, fake data before
introducing a real (non-deterministic) retrieval or generation layer.
This isolates two independent risks — is the control flow correct, vs.
is the retrieval/generation quality good — so a bad run points at one
layer, not both at once. Swap one node at a time (stub → real), never
all at once.

Working stub version already exists (see `/legal_agent` in repo history
if migrated, or ask the author for the original files) — verified
running end-to-end: two search passes, correct loop, correct termination,
before any API key or vector store was involved.

## Sequencing (weekend plan)

1. Corpus: finalize the fixed statute/judgment set (plain text files,
   manually sourced from AustLII — no scraper).
2. Swap `search` node from stub to real Chroma retrieval. Keep
   `assess`/`generate` on stub. Verify retrieval quality in isolation.
3. Swap `assess` to a real Claude call judging sufficiency. Verify the
   loop still behaves correctly with real judgment in the mix.
4. Swap `generate` to a real, non-streaming Claude call. Verify.
5. Add streaming (Claude API streaming -> FastAPI `StreamingResponse` ->
   frontend SSE consumer). Do this only after step 4 works
   non-streaming.
6. Add the human-in-the-loop checkpoint on the step-cap path.
7. Minimal Next.js frontend: chat UI, SSE streaming consumption, a
   handful of pre-generated starter-prompt chips (generated once from the
   corpus, not at runtime), citation chips per answer.

Explicitly out of scope for this pass: cross-jurisdiction equivalence
mapping, working-paper/export features, auth, multi-user accounts.

## Working style / tool-use notes

- Use Plan Mode (or equivalent review step) for architectural decisions —
  review and understand the proposed approach before approving, don't
  just accept the first diff.
- After each stub→real swap, do a short teach-back: explain in your own
  words why the swap works before moving to the next node.
- Commit after each verified working step, not in one large commit at
  the end.
