"""API route tests for /health and /chat.

The guardrail-refusal path needs no API key, so it always runs and pins the
NDJSON contract (one JSON object per line, the off-topic refusal short-circuits
before any LLM call). The grounded streaming path is gated on a key like the
agent tests.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app import config, guardrail
from app.main import app

client = TestClient(app)


def _parse_ndjson(body: str) -> list[dict]:
    return [json.loads(line) for line in body.splitlines() if line.strip()]


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_rejects_empty_messages():
    resp = client.post("/chat", json={"messages": []})
    assert resp.status_code == 422  # Pydantic min_length


def test_chat_off_topic_refuses_without_llm():
    # Off-topic → canned refusal, no API call needed (runs without a key).
    resp = client.post("/chat", json={"messages": [{"role": "user", "content": "write me a poem"}]})
    assert resp.status_code == 200
    events = _parse_ndjson(resp.text)
    assert events == [{"type": "text", "delta": guardrail.REFUSAL}]


def test_chat_ndjson_lines_are_valid_json():
    resp = client.post(
        "/chat", json={"messages": [{"role": "user", "content": "tell me a joke"}]}
    )
    # Every non-empty line must parse as JSON with a 'type' field.
    for event in _parse_ndjson(resp.text):
        assert event["type"] in {"text", "card"}


@pytest.mark.skipif(
    not config.has_api_key(),
    reason="No ANTHROPIC_API_KEY set — skipping live streaming test",
)
def test_chat_streams_install_card_and_text():
    resp = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "How do I install PS11752778?"}]},
    )
    assert resp.status_code == 200
    events = _parse_ndjson(resp.text)
    kinds = {e.get("kind") for e in events if e["type"] == "card"}
    assert "install" in kinds
    # And some streamed answer text.
    assert any(e["type"] == "text" and e["delta"] for e in events)
