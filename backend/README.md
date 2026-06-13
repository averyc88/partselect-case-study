# PartSelect Chat Agent — Backend

FastAPI backend running a Claude tool-calling agent for PartSelect refrigerator
and dishwasher parts. See the root `PLAN.md` for full architecture.

## Setup

```bash
# from backend/
cp .env.example .env             # then put your real ANTHROPIC_API_KEY in .env
uv sync                          # install deps into .venv from uv.lock
uv run python -m scripts.ingest  # build the Chroma index (first run downloads the embedding model)
```

> Run scripts with the `-m` module form (`python -m scripts.ingest`), not
> `python scripts/ingest.py` — the module form puts the backend root on the
> import path so `from app import ...` resolves. (We use namespace packages, no
> `__init__.py`.)

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Then check it's up:

```bash
curl localhost:8000/health
# {"status":"ok","model":"claude-sonnet-4-6","api_key_set":true}
```

## Tests

```bash
uv run pytest -v   # 95 tests; retrieval tests skip if .chroma isn't built yet
```

## Layout

```
app/
  main.py         FastAPI app, CORS, /health (and /chat, in progress)
  config.py       env / .env loading
  data_access.py  deterministic exact lookups over the JSON catalog
  embedder.py     swappable embedding interface (local MiniLM default)
  retrieval.py    Chroma semantic search over the repair corpus
  tools.py        tool registry: schema + handler + card, with dispatch()
  guardrail.py    cheap off-topic pre-check
  prompts.py      system prompt              (in progress)
  agent.py        Claude tool-calling loop   (in progress)
data/             curated parts/repairs/models/orders JSON (committed)
scripts/
  ingest.py       seed the Chroma index from repairs.json
tests/            pytest — data integrity, data access, retrieval, tools, guardrail
```
