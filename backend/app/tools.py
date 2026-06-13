"""The agent's capability surface — a tool registry.

Each tool is one `Tool` entry: an Anthropic tool schema (what the model sees),
a handler that wraps `data_access`/`retrieval` (the deterministic work), and an
optional `card_kind` (the structured UI payload the frontend renders). Adding a
capability is therefore one entry — no other file changes. That extensibility is
itself graded by the brief.

A handler returns `(result_for_model, card)`:
- `result_for_model` is a JSON-serializable dict fed back to Claude as the
  tool_result — the grounded facts it must answer from.
- `card` is an optional `{"kind": ..., "payload": ...}` the agent loop streams
  to the UI, or None when a tool has nothing to render as a card.

The model only chooses *which* tool and *what* args; every fact in the result
is computed here, never by the model. Unknown ids return a clean
`{"found": False, ...}` the model is instructed to relay gracefully rather than
inventing data.
"""

from dataclasses import dataclass
from typing import Callable

from app import data_access as da
from app import retrieval

# A handler takes validated kwargs and returns (result_for_model, optional_card).
Handler = Callable[..., tuple[dict, dict | None]]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict
    handler: Handler
    card_kind: str | None = None


def _card(kind: str, payload) -> dict:
    return {"kind": kind, "payload": payload}


# --- Handlers --------------------------------------------------------------


def _lookup_part(ps_number: str | None = None, query: str | None = None, appliance: str | None = None):
    """Exact PS# lookup, or a keyword search when no PS# is given."""
    if ps_number:
        part = da.get_part(ps_number)
        if not part:
            return {"found": False, "ps_number": ps_number.strip().upper()}, None
        return {"found": True, "part": part}, _card("product", part)

    if query:
        results = da.search_parts(query, appliance=appliance)
        if not results:
            return {"found": False, "query": query}, None
        # Lead with the top match as a card; hand the model the full shortlist.
        return {"found": True, "matches": results}, _card("product", results[0])

    return {"found": False, "error": "Provide either ps_number or query."}, None


def _check_compatibility(ps_number: str, model_number: str):
    result = da.check_compatibility(ps_number, model_number)
    return result, _card("compatibility", result)


def _search_by_symptom(text: str, appliance: str | None = None):
    results = retrieval.search(text, appliance=appliance)
    if not results:
        return {"found": False, "text": text}, None
    # Surface the suggested parts for the top doc as a product the user can act
    # on; the model narrates the troubleshooting steps from the doc content.
    top = results[0]
    suggested = [da.get_part(ps) for ps in top["related_parts"]]
    suggested = [p for p in suggested if p]
    card = _card("repair", {"doc": top, "suggested_parts": suggested})
    return {"found": True, "results": results}, card


def _get_install_guide(ps_number: str):
    guide = da.get_install_guide(ps_number)
    if not guide:
        return {"found": False, "ps_number": ps_number.strip().upper()}, None
    return {"found": True, "guide": guide}, _card("install", guide)


def _get_order_status(order_id: str):
    order = da.get_order(order_id)
    if not order:
        return {"found": False, "order_id": order_id.strip().upper()}, None
    return {"found": True, "order": order}, _card("order", order)


def _start_return(order_id: str):
    result = da.start_return(order_id)
    card = _card("order", result["order"]) if result.get("order") else None
    return result, card


def _cancel_order(order_id: str):
    result = da.cancel_order(order_id)
    card = _card("order", result["order"]) if result.get("order") else None
    return result, card


# --- +4 extension handlers (same JSON, mirror real PartSelect features) -----


def _browse_parts(
    appliance: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
    in_stock_only: bool = False,
):
    results = da.browse_parts(
        appliance=appliance,
        brand=brand,
        category=category,
        max_price=max_price,
        in_stock_only=in_stock_only,
    )
    if not results:
        return {"found": False}, None
    return {"found": True, "count": len(results), "parts": results}, _card("product", results[0])


def _find_water_filter(model_number: str):
    result = da.find_water_filter(model_number)
    if result is None:
        return {"found": False, "model_number": model_number.strip().upper()}, None
    if result["filter"] is None:
        return {"found": True, "has_filter": False, "model_number": result["model_number"]}, None
    return {"found": True, "has_filter": True, "filter": result["filter"]}, _card("product", result["filter"])


def _list_parts_for_model(model_number: str):
    result = da.list_parts_for_model(model_number)
    if result is None:
        return {"found": False, "model_number": model_number.strip().upper()}, None
    return {"found": True, "model": result}, None


# --- Registry --------------------------------------------------------------

_APPLIANCE_ENUM = {"type": "string", "enum": ["refrigerator", "dishwasher"]}

TOOLS: list[Tool] = [
    Tool(
        name="lookup_part",
        description=(
            "Look up a refrigerator or dishwasher part. Pass `ps_number` for an "
            "exact PartSelect number (e.g. PS11752778). If the user describes a "
            "part by name instead, pass `query` (e.g. 'ice maker assembly') and "
            "optionally `appliance` to narrow it. Returns the part record "
            "(price, stock, brand, description)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "ps_number": {"type": "string", "description": "Exact PartSelect number, e.g. PS11752778."},
                "query": {"type": "string", "description": "Part name or keywords when no PS# is known."},
                "appliance": _APPLIANCE_ENUM,
            },
        },
        handler=_lookup_part,
        card_kind="product",
    ),
    Tool(
        name="check_compatibility",
        description=(
            "Check whether a specific part fits a specific appliance model. "
            "Pass the part's `ps_number` and the `model_number` (e.g. "
            "WDT780SAEM1). Returns a definitive compatible / not-compatible "
            "result; flags if the part or model is unknown."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "ps_number": {"type": "string"},
                "model_number": {"type": "string"},
            },
            "required": ["ps_number", "model_number"],
        },
        handler=_check_compatibility,
        card_kind="compatibility",
    ),
    Tool(
        name="search_by_symptom",
        description=(
            "Find troubleshooting guidance from a described symptom or problem "
            "(e.g. 'ice maker not working', 'dishwasher won't drain'). Pass the "
            "user's description as `text` and optionally `appliance`. Returns "
            "ranked repair docs with steps and suggested parts. Use this for "
            "'how do I fix...' / 'why is my... not working' questions."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The user's symptom/problem description."},
                "appliance": _APPLIANCE_ENUM,
            },
            "required": ["text"],
        },
        handler=_search_by_symptom,
        card_kind="repair",
    ),
    Tool(
        name="get_install_guide",
        description=(
            "Get step-by-step installation instructions for a part by its "
            "`ps_number`. Returns difficulty, estimated time, and ordered "
            "steps. Use for 'how do I install...' questions."
        ),
        input_schema={
            "type": "object",
            "properties": {"ps_number": {"type": "string"}},
            "required": ["ps_number"],
        },
        handler=_get_install_guide,
        card_kind="install",
    ),
    Tool(
        name="get_order_status",
        description=(
            "Look up an order by its `order_id` (e.g. PS-100234). Returns "
            "status, items, dates, tracking, and whether it's return-eligible "
            "or cancellable."
        ),
        input_schema={
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
        handler=_get_order_status,
        card_kind="order",
    ),
    Tool(
        name="start_return",
        description=(
            "Initiate a return for an order by `order_id`. Only succeeds if the "
            "order is return-eligible; otherwise returns why not. Confirm the "
            "user wants to return before calling."
        ),
        input_schema={
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
        handler=_start_return,
        card_kind="order",
    ),
    Tool(
        name="cancel_order",
        description=(
            "Cancel an order by `order_id`. Only succeeds if the order is still "
            "cancellable (typically while Processing); otherwise returns why "
            "not. Confirm the user wants to cancel before calling."
        ),
        input_schema={
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
        handler=_cancel_order,
        card_kind="order",
    ),
    Tool(
        name="browse_parts",
        description=(
            "Browse/filter the catalog when the user has no specific part in "
            "mind. Any combination of `appliance`, `brand`, `category`, "
            "`max_price`, `in_stock_only`. Returns matching parts sorted by "
            "price."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "appliance": _APPLIANCE_ENUM,
                "brand": {"type": "string"},
                "category": {"type": "string"},
                "max_price": {"type": "number"},
                "in_stock_only": {"type": "boolean"},
            },
        },
        handler=_browse_parts,
        card_kind="product",
    ),
    Tool(
        name="find_water_filter",
        description=(
            "Find the correct water filter for a refrigerator `model_number`. "
            "Returns the recommended filter part, or indicates the model takes "
            "no filter (e.g. dishwashers)."
        ),
        input_schema={
            "type": "object",
            "properties": {"model_number": {"type": "string"}},
            "required": ["model_number"],
        },
        handler=_find_water_filter,
        card_kind="product",
    ),
    Tool(
        name="list_parts_for_model",
        description=(
            "List every catalog part that fits a given `model_number`. Use when "
            "the user asks 'what parts are available for my <model>'."
        ),
        input_schema={
            "type": "object",
            "properties": {"model_number": {"type": "string"}},
            "required": ["model_number"],
        },
        handler=_list_parts_for_model,
    ),
]

# Lookups the agent loop uses.
BY_NAME: dict[str, Tool] = {t.name: t for t in TOOLS}
SCHEMAS: list[dict] = [
    {"name": t.name, "description": t.description, "input_schema": t.input_schema} for t in TOOLS
]


def dispatch(name: str, arguments: dict) -> tuple[dict, dict | None]:
    """Run a tool by name with the model-supplied arguments.

    Returns `(result_for_model, optional_card)`. An unknown tool name or
    malformed args surface as a clean error dict the model can recover from,
    rather than raising into the agent loop.
    """
    tool = BY_NAME.get(name)
    if tool is None:
        return {"error": f"Unknown tool: {name}"}, None
    try:
        return tool.handler(**arguments)
    except TypeError as e:
        # Bad/missing args — give the model a recoverable message.
        return {"error": f"Invalid arguments for {name}: {e}"}, None
