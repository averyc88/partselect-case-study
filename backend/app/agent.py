"""The Claude tool-calling loop — the orchestrator.

Claude is the *router*: given the conversation and our tool schemas, it decides
which tool to call and with what arguments. We run the tool deterministically
(`tools.dispatch`), feed the result back, and repeat until Claude produces a
final text answer. Every fact in that answer therefore traces to a tool result,
never to the model — see `prompts.py`.

This module exposes a non-streaming `run()` that returns the final text plus the
cards emitted along the way. Phase 6 adds a streaming variant on top of the same
loop for the `/chat` endpoint; keeping the core loop here means both share one
implementation.

`temperature=0` makes routing near-deterministic. Valid on Sonnet 4.6 (the
configured model); note it would 400 on Opus 4.7+/Fable 5, where sampling params
are removed — swap the model and drop `temperature` together if upgrading.
"""

import json
from collections.abc import Iterator

import anthropic

from app import config, tools

# Safety cap on the agentic loop. Real turns use 1–3 tool calls; this only
# guards against a pathological back-and-forth, never normal use.
MAX_ITERATIONS = 8

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def run(messages: list[dict], system: str) -> dict:
    """Run the tool-use loop to completion (non-streaming).

    `messages` is the conversation so far (Anthropic message dicts; the first
    must be a user turn). Returns `{"text": <final answer>, "cards": [...]}`
    where cards are the `{"kind", "payload"}` objects emitted by the tools the
    model chose this turn, in call order.
    """
    # Work on a copy — we append assistant/tool turns as the loop runs.
    convo = list(messages)
    cards: list[dict] = []

    for _ in range(MAX_ITERATIONS):
        response = _client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1024,
            temperature=0,
            system=system,
            tools=tools.SCHEMAS,
            messages=convo,
        )

        if response.stop_reason != "tool_use":
            # Claude is done — return its final text.
            text = "".join(b.text for b in response.content if b.type == "text")
            return {"text": text, "cards": cards}

        # Preserve the assistant turn verbatim (it carries the tool_use blocks).
        convo.append({"role": "assistant", "content": response.content})

        # Run every tool the model asked for; collect results + cards.
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result, card = tools.dispatch(block.name, dict(block.input))
            if card:
                cards.append(card)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                    "is_error": "error" in result,
                }
            )

        # Feed all results back in a single user turn, then loop.
        convo.append({"role": "user", "content": tool_results})

    # Hit the iteration cap without a final answer — degrade gracefully rather
    # than loop forever.
    return {
        "text": "Sorry — I wasn't able to finish that. Could you rephrase or give "
        "me the part or model number?",
        "cards": cards,
    }


# Event shapes yielded by stream():
#   {"type": "text", "delta": str}          — a chunk of the final answer
#   {"type": "card", "kind": str, "payload": ...}  — a structured card to render
_FALLBACK_TEXT = (
    "Sorry — I wasn't able to finish that. Could you rephrase or give me the "
    "part or model number?"
)


def stream(messages: list[dict], system: str) -> Iterator[dict]:
    """Run the tool-use loop, yielding text deltas and cards as they happen.

    Same orchestration as `run()`, but each API call is streamed so the final
    answer reaches the UI token-by-token. Tool-calling turns produce no
    user-visible text deltas (the model is just routing); when it runs a tool we
    emit the card immediately, then loop. The last turn — Claude's actual answer
    — streams its text. `main.py` serializes each yielded event to one NDJSON
    line.
    """
    convo = list(messages)

    for _ in range(MAX_ITERATIONS):
        with _client.messages.stream(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1024,
            temperature=0,
            system=system,
            tools=tools.SCHEMAS,
            messages=convo,
        ) as stream_ctx:
            # Stream text as it arrives. On a tool-use turn there's usually none.
            for delta in stream_ctx.text_stream:
                yield {"type": "text", "delta": delta}
            response = stream_ctx.get_final_message()

        if response.stop_reason != "tool_use":
            return  # text already streamed above; we're done

        convo.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result, card = tools.dispatch(block.name, dict(block.input))
            if card:
                yield {"type": "card", "kind": card["kind"], "payload": card["payload"]}
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                    "is_error": "error" in result,
                }
            )

        convo.append({"role": "user", "content": tool_results})

    yield {"type": "text", "delta": _FALLBACK_TEXT}
