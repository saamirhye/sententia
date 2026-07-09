Next.js frontend for Sententia — see the [repo root README](../README.md) for the full project overview, architecture, and how to run both servers together.

Scaffolded with `create-next-app` (App Router, Tailwind v4) + `shadcn` (Base preset). Font is self-hosted IBM Plex Sans via `next/font/google` (not Geist — CLAUDE.md restricts fonts to Google Fonts only).

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Requires the backend running on `:8000` (see root README) and, optionally, `frontend/.env.local` (copy `.env.local.example`) if the backend isn't on the default port.
