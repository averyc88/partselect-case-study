# PartSelect Chat Agent — Backend

FastAPI backend running a Claude tool-calling agent for PartSelect refrigerator
and dishwasher parts. See the root `PLAN.md` for full architecture.

## Setup

```bash
# from backend/
cp .env.example .env          # then put your real ANTHROPIC_API_KEY in .env
uv sync                       # install deps into .venv from uv.lock
```

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Then check it's up:

```bash
curl localhost:8000/health
# {"status":"ok","model":"claude-sonnet-4-6","api_key_set":true}
```

## Layout

```
app/
  main.py        FastAPI app, CORS, /health (and /chat, added later)
  config.py      env / .env loading
  ...            agent.py, tools.py, retrieval.py, etc. (added in later phases)
data/            curated parts.json, repairs.json, orders.json (added later)
tests/           pytest tool tests (added later)
```
