# Sententia

An agentic legal research assistant that decides at runtime how many search passes it needs before answering, instead of a fixed one-shot RAG call. Given a query about NSW residential tenancy law, it searches legislation and case law, assesses whether it has enough to answer confidently, and either loops back to search or generates a cited answer — capped at a fixed number of attempts, with a human-in-the-loop checkpoint before a reduced-confidence answer is ever treated as final.

Personal learning project. The goal is genuine, defensible understanding of agentic AI architecture (LangGraph, multi-step reasoning loops, human-in-the-loop, streaming) — explainable in detail, not just a working demo. See [`docs/brief.md`](docs/brief.md) for the full "why an agent, not a fixed pipeline" rationale.

## Status

All 7 phases complete — the graph is real end to end, the API streams over SSE, and a Next.js frontend consumes it.

```
START -> search -> assess --sufficient?--> generate -> END
            ^            |
            |            └--insufficient, step cap hit--> human_review --approved?--> generate -> END
            |                                                  |
            └──────────────insufficient, attempts remain───────┘                  (declined -> END)
```

- **`search`** — Chroma hybrid retrieval (BM25 + dense, fused with RRF) over a small, fixed, manually-curated corpus (legislation + NCAT case law).
- **`assess`** — Claude (forced tool use) judges whether the accumulated results are sufficient to answer confidently.
- **`human_review`** — only on the step-cap path: a LangGraph `interrupt()` pauses the run and asks a human to approve or decline a reduced-confidence answer before it's generated.
- **`generate`** — Claude streams a cited answer grounded only in the retrieved sources, honestly hedged if confidence was reduced.

See [`CLAUDE.md`](CLAUDE.md) for the phase-by-phase build log and current operating notes.

## Tech stack

- **Backend:** Python, LangGraph, FastAPI, Chroma.
- **Generation:** Claude API (Anthropic), streamed via SSE.
- **Frontend:** Next.js (App Router), Tailwind, shadcn/ui.

## Running it

Two servers, from the repo root:

```bash
# backend
cd backend
uv run uvicorn sententia.api.main:app --reload --port 8000

# frontend (separate terminal)
cd frontend
npm run dev
```

Open `http://localhost:3000`. Requires a real `ANTHROPIC_API_KEY` in `backend/.env` (copy `.env.example`) — without it, `assess`/`generate`/`human_review` fall back to their degraded/error paths.

## Project structure

```
backend/
  src/sententia/graph/     # LangGraph nodes, edges, state, build
  src/sententia/llm/       # Claude calls (assess, generate)
  src/sententia/retrieval/ # corpus loading, Chroma hybrid search
  src/sententia/api/       # FastAPI app, SSE endpoints
  scripts/                 # run_stub.py (CLI harness), generate_starter_prompts.py
  tests/
frontend/
  app/, components/, lib/  # Next.js chat UI, SSE consumer, useChat hook
corpus/
  legislation/, cases/     # manually sourced NSW RTA sections + NCAT judgments
docs/brief.md              # full project rationale
```
