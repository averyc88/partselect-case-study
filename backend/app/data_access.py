"""Deterministic lookups over the curated JSON catalog.

This is the *exact-fact* half of the hybrid-retrieval design: every product
fact the agent states — price, stock, compatibility, order status — is computed
here against `data/*.json`, never by the model. Fuzzy symptom discovery lives in
`retrieval.py` (Chroma); this module is pure dict/set work.

Data is loaded once at import and indexed by key. Lookups are case-insensitive
because users type part and model numbers in any case ("ps11752778",
"wdt780saem1"). Functions return plain dicts (the raw records, or small result
dicts for the order flows); `tools.py` shapes them into card payloads.
"""

import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(name: str) -> list[dict]:
    with open(_DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


# Raw records (source of truth for this process).
PARTS: list[dict] = _load("parts.json")
MODELS: list[dict] = _load("models.json")
ORDERS: list[dict] = _load("orders.json")

# Indexes keyed by uppercased identifier for case-insensitive exact lookup.
_PARTS_BY_PS = {p["ps_number"].upper(): p for p in PARTS}
_MODELS_BY_NUMBER = {m["model_number"].upper(): m for m in MODELS}
_ORDERS_BY_ID = {o["order_id"].upper(): o for o in ORDERS}


# --- Parts -----------------------------------------------------------------


def get_part(ps_number: str) -> dict | None:
    """Return the part record for an exact PS number, or None if unknown."""
    return _PARTS_BY_PS.get(ps_number.strip().upper())


def search_parts(query: str, appliance: str | None = None, limit: int = 5) -> list[dict]:
    """Keyword search over the catalog for when there's no exact PS number.

    Matches the query against name, manufacturer number, brand, and category.
    This is a deterministic substring/token match — fuzzy *symptom* discovery
    goes through `retrieval.py`, not here. Results are scored so the best
    name/mfr matches surface first.
    """
    q = query.strip().lower()
    if not q:
        return []
    tokens = q.split()
    appliance = appliance.lower() if appliance else None

    scored: list[tuple[int, dict]] = []
    for part in PARTS:
        if appliance and part["appliance"] != appliance:
            continue
        haystacks = {
            "name": part["name"].lower(),
            "mfr": part["manufacturer_number"].lower(),
            "brand": part["brand"].lower(),
            "category": part["category"].lower(),
        }
        score = 0
        # Strong signal: the full query appears in the name or mfr number.
        if q in haystacks["name"]:
            score += 10
        if q in haystacks["mfr"]:
            score += 8
        # Per-token matches across all fields.
        for tok in tokens:
            if tok in haystacks["name"]:
                score += 3
            if tok in haystacks["brand"]:
                score += 2
            if tok in haystacks["category"]:
                score += 2
        if score:
            scored.append((score, part))

    scored.sort(key=lambda s: s[0], reverse=True)
    return [part for _, part in scored[:limit]]


def get_install_guide(ps_number: str) -> dict | None:
    """Return install info plus identifying fields for a part, or None.

    Pulls the `install` block out alongside the part's name/PS#/url so the
    InstallGuide card has everything it needs without a second lookup.
    """
    part = get_part(ps_number)
    if not part:
        return None
    return {
        "ps_number": part["ps_number"],
        "name": part["name"],
        "part_url": part["part_url"],
        "difficulty": part["install"]["difficulty"],
        "time": part["install"]["time"],
        "steps": part["install"]["steps"],
    }


# --- Compatibility ---------------------------------------------------------


def check_compatibility(ps_number: str, model_number: str) -> dict:
    """Determine whether a part fits a model via set membership both ways.

    Authoritative because `parts.json` and `models.json` are a maintained
    mirror (asserted by the Phase 9 integrity test). We check the model's
    `compatible_parts` and the part's `compatible_models` and treat a hit in
    either direction as compatible, so a one-sided drift never yields a false
    "incompatible". The result dict carries enough context for the card and
    for the agent to explain unknown parts/models gracefully.
    """
    part = get_part(ps_number)
    model = get_model(model_number)

    result: dict = {
        "ps_number": part["ps_number"] if part else ps_number.strip().upper(),
        "model_number": model["model_number"] if model else model_number.strip().upper(),
        "part_known": part is not None,
        "model_known": model is not None,
        "compatible": False,
    }
    if part:
        result["part_name"] = part["name"]
    if model:
        result["model_description"] = model["description"]

    # Can't assert compatibility for an unknown part or model.
    if not part or not model:
        return result

    by_model = result["ps_number"] in {p.upper() for p in model["compatible_parts"]}
    by_part = result["model_number"] in {m.upper() for m in part["compatible_models"]}
    result["compatible"] = by_model or by_part
    return result


# --- Models ----------------------------------------------------------------


def get_model(model_number: str) -> dict | None:
    """Return the model record for an exact model number, or None."""
    return _MODELS_BY_NUMBER.get(model_number.strip().upper())


def list_parts_for_model(model_number: str) -> dict | None:
    """Return a model's full compatible-parts records, or None if unknown.

    Mirrors PartSelect's `/Models/{MODEL}/` page: the model header plus every
    in-catalog part that fits it.
    """
    model = get_model(model_number)
    if not model:
        return None
    parts = [get_part(ps) for ps in model["compatible_parts"]]
    return {
        "model_number": model["model_number"],
        "brand": model["brand"],
        "appliance": model["appliance"],
        "type": model["type"],
        "description": model["description"],
        "parts": [p for p in parts if p],
    }


def find_water_filter(model_number: str) -> dict | None:
    """Return the recommended water-filter part for a model.

    Mirrors PartSelect's Water-Filter-Finder. Returns None for an unknown
    model; returns a result with `filter=None` for a model that takes no filter
    (e.g. every dishwasher) so the caller can distinguish "no such model" from
    "this model has no filter".
    """
    model = get_model(model_number)
    if not model:
        return None
    filter_ps = model.get("water_filter_ps")
    return {
        "model_number": model["model_number"],
        "appliance": model["appliance"],
        "filter": get_part(filter_ps) if filter_ps else None,
    }


# --- Browse ----------------------------------------------------------------


def browse_parts(
    appliance: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
    in_stock_only: bool = False,
    limit: int = 10,
) -> list[dict]:
    """Filter the catalog by any combination of facets (catalog browse).

    All filters are ANDed; omitted filters don't constrain. String facets match
    case-insensitively. Results are sorted by price ascending for a sensible
    default browse order.
    """
    appliance = appliance.lower() if appliance else None
    brand = brand.lower() if brand else None
    category = category.lower() if category else None

    matches = []
    for part in PARTS:
        if appliance and part["appliance"] != appliance:
            continue
        if brand and part["brand"].lower() != brand:
            continue
        if category and part["category"].lower() != category:
            continue
        if max_price is not None and part["price"] > max_price:
            continue
        if in_stock_only and not part["in_stock"]:
            continue
        matches.append(part)

    matches.sort(key=lambda p: p["price"])
    return matches[:limit]


# --- Orders ----------------------------------------------------------------


def get_order(order_id: str) -> dict | None:
    """Return the order record for an exact order id, or None."""
    return _ORDERS_BY_ID.get(order_id.strip().upper())


def start_return(order_id: str) -> dict:
    """Initiate a return on an order, honoring the hardcoded eligibility flag.

    `return_eligible` is a fixed boolean in the data (deterministic and
    testable) rather than date-computed; see PLAN.md. On success we flip the
    order's status to "Return Initiated" in the in-memory mock so a subsequent
    status check reflects it. The result dict tells the caller what happened so
    the agent can phrase eligible / not-eligible / unknown distinctly.
    """
    order = get_order(order_id)
    if not order:
        return {"ok": False, "reason": "not_found", "order_id": order_id.strip().upper()}
    if not order["return_eligible"]:
        return {
            "ok": False,
            "reason": "not_eligible",
            "order_id": order["order_id"],
            "status": order["status"],
            "order": order,
        }
    order["status"] = "Return Initiated"
    order["return_eligible"] = False  # can't initiate twice
    return {"ok": True, "action": "return", "order_id": order["order_id"], "order": order}


def cancel_order(order_id: str) -> dict:
    """Cancel an order if it's still cancellable, mutating the in-memory mock.

    Like returns, `cancellable` is a hardcoded flag (typically true only while
    an order is still Processing). On success the status becomes "Cancelled".
    """
    order = get_order(order_id)
    if not order:
        return {"ok": False, "reason": "not_found", "order_id": order_id.strip().upper()}
    if not order["cancellable"]:
        return {
            "ok": False,
            "reason": "not_cancellable",
            "order_id": order["order_id"],
            "status": order["status"],
            "order": order,
        }
    order["status"] = "Cancelled"
    order["cancellable"] = False
    return {"ok": True, "action": "cancel", "order_id": order["order_id"], "order": order}
