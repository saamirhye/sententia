# sententia (backend)

See the repo root [README](../README.md) and [CLAUDE.md](../CLAUDE.md) for project overview and architecture.

```
uv sync
uv run python scripts/index_corpus.py   # builds the Chroma index (run once, re-run after corpus edits)
uv run pytest -v
uv run python scripts/run_stub.py
```
