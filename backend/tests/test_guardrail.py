"""Tests for the off-topic pre-check.

The design is intentionally conservative: false *passes* (borderline input
reaching the scoped model) are acceptable; false *blocks* (refusing a real
appliance question) are not. These tests pin that asymmetry.
"""

import pytest

from app import guardrail


@pytest.mark.parametrize(
    "msg",
    [
        "write me a poem",
        "what's the best stock to buy?",
        "tell me a joke",
        "what's the capital of France",
        "can you help me with my python homework",
        "what's the weather today",
    ],
)
def test_blatantly_off_topic_is_blocked(msg):
    assert guardrail.is_off_topic(msg) is True


@pytest.mark.parametrize(
    "msg",
    [
        "how do I install PS11752778",
        "is this part compatible with my WDT780SAEM1",
        "the ice maker on my Whirlpool fridge is not working",
        "my dishwasher won't drain",
        "I need a water filter for my refrigerator",
        "what's the status of my order PS-100234",
        "I want to return my order",
        "can I cancel and get a refund",
        "where is my shipment, tracking please",
        "is this covered under warranty",
        "what's in my cart, ready to checkout",
        "when will my part be delivered",
    ],
)
def test_in_domain_is_never_blocked(msg):
    assert guardrail.is_off_topic(msg) is False


def test_off_topic_word_with_in_domain_signal_passes():
    # "recipe" is off-topic, but the appliance context means let the model handle it.
    assert guardrail.is_off_topic("does my dishwasher have a recipe mode") is False


def test_empty_is_not_off_topic():
    assert guardrail.is_off_topic("") is False
    assert guardrail.is_off_topic("   ") is False


def test_bare_ge_does_not_falsely_pass_as_in_domain():
    # "ge" alone is no longer an in-domain term; an off-topic ask with a stray
    # "ge" should still be blocked. (We only treat "general electric" as a brand.)
    assert guardrail.is_off_topic("ge me a poem") is True


def test_general_electric_is_in_domain():
    assert guardrail.is_off_topic("general electric stock price") is False
