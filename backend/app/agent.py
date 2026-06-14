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
