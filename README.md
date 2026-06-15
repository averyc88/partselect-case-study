# PartSelect Chat Agent

A scoped chat agent for the **PartSelect** site, focused on **refrigerator and
dishwasher parts**. It looks up parts, checks part↔model compatibility, gives
install guidance, troubleshoots symptoms, and handles basic order flows (status /
return / cancel) — and it stays in scope, politely declining anything off-topic.

## Stack

- **Frontend:** Next.js + TypeScript + Tailwind v4
- **Backend:** Python + FastAPI (managed with [`uv`](https://docs.astral.sh/uv/))
- **LLM:** Anthropic Claude, via a tool-calling agent loop
- **Vector store:** Chroma (local, in-process)
- **Embeddings:** local `sentence-transformers/all-MiniLM-L6-v2` (no API key)

The only credential you need is an `ANTHROPIC_API_KEY` — embeddings run locally.

## Setup

Prereqs: `uv`, Node 18+, and an `ANTHROPIC_API_KEY`.

**Backend** (terminal 1):
```bash
cd backend
cp .env.example .env                # paste your ANTHROPIC_API_KEY into .env
uv sync                             # install dependencies
uv run python -m scripts.ingest     # build the Chroma index (first run downloads the ~80MB embedding model)
uv run uvicorn app.main:app --reload --port 8000
```

**Frontend** (terminal 2):
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**.

## Try it

- *"How can I install part number PS11752778?"*
- *"Is PS11746337 compatible with my WDT780SAEM1 model?"*
- *"The ice maker on my Whirlpool fridge is not working."*
- *"What's the status of order PS-100234?"*
- *"Write me a poem."* → politely declined (out of scope)

## A note on the data

The catalog is **curated mock JSON** (`backend/data/`), committed so nothing is
fetched at runtime. It's anchored on mostly **real identifiers**. Prices, stock, 
and the orders are fabricated but internally consistent — the orders demonstrate 
the transaction flows across every status and eligibility case. The data layer 
sits behind a single module, so swapping in a real catalog API or database is a 
one-file change.

Card links point to `partselect.com`.
