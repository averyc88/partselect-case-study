"""Cheap off-topic pre-check — belt-and-suspenders before the model.

The system prompt already scopes the agent to refrigerator/dishwasher parts.
This is a fast keyword gate in front of it: blatantly off-topic input gets a
canned refusal without spending an LLM call. It is deliberately *conservative* —
a false block (refusing a real appliance question) is worse than a false pass
(letting a borderline case reach the already-scoped model). So we only refuse
when there's a clear off-topic signal AND no in-domain signal at all. Anything
ambiguous falls through to the agent, which can scope-check with full context.
"""

import re

# Canned reply when we're confident the request is out of scope.
REFUSAL = (
    "I'm the PartSelect assistant for refrigerator and dishwasher parts — "
    "I can help you find parts, check compatibility with your model, walk "
    "through installs and repairs, or look up an order. What can I help you "
    "with on your fridge or dishwasher?"
)

# In-domain signals: if any appear, never block — let the agent handle it.
_IN_DOMAIN = re.compile(
    r"\b(fridge|refrigerator|freezer|dishwasher|ice\s?maker|water\s?filter|"
    r"compressor|defrost|evaporator|condenser|gasket|door\s?bin|crisper|"
    r"spray\s?arm|rack|drain|pump|inlet\s?valve|heating\s?element|thermostat|"
    r"control\s?board|latch|part|model|order|return|refund|cancel|install|"
    r"compatible|shipping|ship|tracking|track|warranty|cart|checkout|delivery|"
    r"delivered|invoice|receipt|ps\d{4,}|appliance|whirlpool|frigidaire|bosch|"
    r"samsung|maytag|kitchenaid|general\s+electric)\b",
    re.IGNORECASE,
)

# Clear off-topic signals: general-purpose-assistant asks that have nothing to
# do with appliance parts. Only triggers a refusal when no in-domain term is
# present alongside them.
# NOTE: deliberately omits e-commerce-colliding words. "stock" was removed —
# "is it in stock?" is a core availability question (finance intent is covered by
# crypto|bitcoin). "code" was removed — "error code E24" is standard
# appliance-repair vocab (coding intent is covered by python|javascript|homework).
# These collisions are dangerous precisely because the gate is stateless per
# message: a follow-up like "is it in stock?" carries no appliance noun, so a
# colliding word would false-block it.
_OFF_TOPIC = re.compile(
    r"\b(poem|haiku|joke|story|essay|recipe|cook|weather|crypto|bitcoin|"
    r"president|election|sports|movie|song|translate|python|javascript|"
    r"homework|math|capital\s+of|meaning\s+of\s+life|who\s+are\s+you\s+really)\b",
    re.IGNORECASE,
)


def is_off_topic(message: str) -> bool:
    """True only when clearly off-topic with no in-domain signal.

    Empty/whitespace input isn't off-topic (let the agent prompt for detail).
    """
    text = message.strip()
    if not text:
        return False
    if _IN_DOMAIN.search(text):
        return False
    return bool(_OFF_TOPIC.search(text))
