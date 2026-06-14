"""Pydantic request models for the API.

The `/chat` request carries the full conversation history (the Messages API is
stateless — we resend it each turn). We keep the message shape minimal and
Anthropic-compatible: a role plus string content, which the agent loop passes
straight through. Card payloads going *out* are plain dicts serialized to NDJSON
by the route, so they need no model here.
"""

from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[Message] = Field(..., min_length=1)
