# PartSelect Chat Agent

A scoped chat agent for the **PartSelect** e-commerce site, focused on
**refrigerator and dishwasher parts**. It looks up parts, checks part↔model
compatibility, gives install guidance, troubleshoots symptoms, and handles basic
order flows (status / return / cancel) — and it stays in scope, politely
declining anything off-topic.

> **Status:** backend foundation complete and fully tested (data layer, hybrid
> retrieval, tool registry, guardrail — **95 passing tests**). The Claude
> tool-calling loop + streaming API and the Next.js frontend are in progress.
> See [`PLAN.md`](../PLAN.md) for the full architecture, every design decision,
> and the phase-by-phase progress tracker.

## Architecture

```
Next.js frontend  ──fetch/NDJSON──▶  FastAPI backend
  chat + cards                          │
                                        ├─ guardrail.py   cheap off-topic pre-check
                                        ├─ agent.py       Claude tool-calling loop (temp=0)
                                        │     │
                                        │     ├─ tools.py        registry: schema + handler + card
                                        │     ├─ data_access.py  EXACT facts over JSON  (deterministic)
                                        │     └─ retrieval.py    FUZZY symptom search   (Chroma + MiniLM)
                                        └─ data/*.json    curated catalog (committed)
```

**The model is the router, not the source of truth.** Claude only chooses
*which* tool to call and *what* arguments to pass. Every fact it states — price,
stock, compatibility yes/no, order status — is computed by deterministic Python
against `data/*.json`. `temperature=0` keeps routing near-deterministic; typed
tool schemas mean malformed args return a clean error the model recovers from.

### Hybrid retrieval — the key design idea

Exact lookups and fuzzy discovery have opposite requirements, so we split them:

| Need | Path | Why |
|---|---|---|
| Part #, compatibility, orders | `data_access.py` — dict/set ops over JSON | Precision. You must **never** embed a part number — semantic search returns "close" matches, which is wrong for facts. |
| "my ice maker isn't working" | `retrieval.py` — Chroma semantic search | Recall. Messy real-world phrasings need fuzzy matching. |

Only the troubleshooting corpus (`repairs.json`) is embedded. The highest-leverage
data choice: each repair doc has **`user_phrasings[]`** (messy ways a user
describes the problem) and **`content`** (polished prose). We **embed the
phrasings** so real queries match, but **display the content**. A query like
*"my freezer keeps icing up with thick frost"* — which shares almost no words
with the doc title — still ranks the right doc #1.

## Setup

Prereqs: [`uv`](https://docs.astral.sh/uv/) (Python), an `ANTHROPIC_API_KEY`.

```bash
cd backend
cp .env.example .env            # put your real ANTHROPIC_API_KEY in .env
uv sync                         # install deps from uv.lock into .venv
uv run python -m scripts.ingest # build the Chroma index (first run downloads the ~80MB embedding model)
```

The `.chroma/` vector index is a **build artifact** — gitignored and rebuilt
locally by `ingest.py`. The raw `data/*.json` is the committed source of truth,
so the reviewer never fetches anything dynamically.

## Tests

```bash
cd backend && uv run pytest -v
```

95 tests across four layers:
- **`test_data_integrity.py`** — the JSON is internally consistent: no dangling
  refs, parts↔models is a *perfect bidirectional mirror*, order arithmetic
  reconciles. (These caught a real data bug during the build.)
- **`test_data_access.py`** — every deterministic lookup + the order mutations.
- **`test_retrieval.py`** — semantic search ranks the right repair doc #1,
  including a near-zero-word-overlap paraphrase. (Skips if `.chroma` is unbuilt.)
- **`test_tools.py`** / **`test_guardrail.py`** — tool dispatch + the off-topic
  gate, no API key needed.

## Extensibility & scalability

- **Vector store** is behind `retrieval.py` — swap Chroma for
  pgvector/Pinecone/Turbopuffer without touching the agent.
- **Embeddings** are behind `embedder.py` — local MiniLM today; swap in a hosted
  model (Voyage / OpenAI) by changing one function + setting a key. Same model
  embeds the corpus and the queries, by construction.
- **Tools** are a registry — adding a capability is one `Tool` entry (schema +
  handler + optional card), no other file changes.
- **Data layer** is behind `data_access.py` — JSON today, a real
  Postgres/PartSelect API tomorrow, same interface.
- **New appliance categories** = more data + tag updates; architecture unchanged.

Out of scope for this case study (but natural next steps): auth, rate limiting,
persistent conversation history, an eval/observability harness.
```
