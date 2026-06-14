"""FastAPI app entrypoint. Run with: uvicorn app.main:app --reload --port 8000

Exposes `GET /health` and `POST /chat`. `/chat` streams NDJSON — one JSON object
per line, each either `{"type":"text","delta":...}` or
`{"type":"card","kind":...,"payload":...}` — consumed by the frontend via
fetch + ReadableStream. Plain `StreamingResponse` (no SSE library): fewer deps,
fits interleaved text+cards, and lets us POST the message history.
"""

import json
from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app import agent, config, guardrail, prompts
from app.models import ChatRequest

app = FastAPI(title="PartSelect Chat Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Liveness check. Reports whether an Anthropic key is configured."""
    return {"status": "ok", "model": config.ANTHROPIC_MODEL, "api_key_set": config.has_api_key()}


def _ndjson_line(event: dict) -> str:
    return json.dumps(event) + "\n"


def _chat_events(messages: list[dict]) -> Iterator[str]:
    """Yield NDJSON lines for a chat turn.

    Cheap guardrail first: if the latest user message is blatantly off-topic,
    return a canned refusal without spending an LLM call. Otherwise hand the
    full history to the streaming agent loop and relay its events.
    """
    latest_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    if guardrail.is_off_topic(latest_user):
        yield _ndjson_line({"type": "text", "delta": guardrail.REFUSAL})
        return

    for event in agent.stream(messages, system=prompts.SYSTEM_PROMPT):
        yield _ndjson_line(event)


@app.post("/chat")
def chat(req: ChatRequest) -> StreamingResponse:
    """Stream the assistant's reply (text + cards) as NDJSON."""
    messages = [m.model_dump() for m in req.messages]
    return StreamingResponse(_chat_events(messages), media_type="application/x-ndjson")
