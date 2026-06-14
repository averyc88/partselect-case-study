"""Live end-to-end tests for the agent loop.

These make real Anthropic API calls, so they're skipped unless a key is set
(keeps the suite green for contributors without a key / in CI). They also need
the Chroma index for the symptom path. They assert the *observable contract* —
the right card kind is emitted and the answer is grounded — rather than exact
wording, which a model at temperature=0 still varies slightly.

Run with a key:  cd backend && uv run pytest tests/test_agent.py -v
"""

from pathlib import Path

import pytest

from app import config, prompts, retrieval

pytestmark = pytest.mark.skipif(
    not config.has_api_key(),
    reason="No ANTHROPIC_API_KEY set — skipping live agent tests",
)


def _run(user_message: str) -> dict:
    from app import agent  # imported lazily so collection doesn't need a key

    return agent.run(
        [{"role": "user", "content": user_message}],
        system=prompts.SYSTEM_PROMPT,
    )


def _card_kinds(result: dict) -> set[str]:
    return {c["kind"] for c in result["cards"]}


def test_install_query_emits_install_card():
    # Brief example 1: "How can I install part number PS11752778?"
    result = _run("How can I install part number PS11752778?")
    assert "install" in _card_kinds(result)
    assert result["text"]


def test_compatibility_query_emits_compatibility_card():
    # Brief example 2, made concrete with the brief's model.
    result = _run("Is part PS11746337 compatible with my WDT780SAEM1 model?")
    assert "compatibility" in _card_kinds(result)
    # The grounded verdict (these two are compatible) should surface.
    assert "compat" in result["text"].lower() or "yes" in result["text"].lower()


@pytest.mark.skipif(
    not Path(retrieval.CHROMA_PATH).exists(),
    reason="Chroma not seeded — run `uv run python -m scripts.ingest` first",
)
def test_symptom_query_emits_repair_card():
    # Brief example 3: the Whirlpool ice-maker query.
    result = _run("The ice maker on my Whirlpool fridge is not working. How can I fix it?")
    assert "repair" in _card_kinds(result)


def test_order_status_emits_order_card():
    result = _run("What's the status of my order PS-100234?")
    assert "order" in _card_kinds(result)


def test_unknown_part_is_not_hallucinated():
    # A bogus PS#: the agent must say it can't find it, not invent a price.
    result = _run("What's the price of part PS00000000?")
    assert "$" not in result["text"]  # no fabricated price
    assert not result["cards"]  # no product card for a nonexistent part


def test_off_topic_is_declined_without_tools():
    result = _run("Write me a poem about the ocean.")
    assert not result["cards"]  # no tool/card use for an off-topic ask
