"""Tests for the tool registry and dispatch.

Tools are deterministic wrappers over data_access/retrieval, so we can verify
dispatch routing, the (result, card) contract, and graceful handling of
unknown ids / bad args — all without the LLM. The registry shape itself
(schemas well-formed, names unique) is also asserted, since the agent loop and
the brief's extensibility story both depend on it.
"""

from pathlib import Path

import pytest

from app import retrieval, tools


# --- Registry shape --------------------------------------------------------


def test_tool_names_unique():
    names = [t.name for t in tools.TOOLS]
    assert len(names) == len(set(names))


def test_schemas_well_formed():
    for schema in tools.SCHEMAS:
        assert schema["name"]
        assert schema["description"]
        assert schema["input_schema"]["type"] == "object"
        assert "properties" in schema["input_schema"]


def test_by_name_covers_all_tools():
    assert set(tools.BY_NAME) == {t.name for t in tools.TOOLS}


# --- dispatch contract -----------------------------------------------------


def test_dispatch_unknown_tool():
    result, card = tools.dispatch("does_not_exist", {})
    assert "error" in result
    assert card is None


def test_dispatch_bad_args_is_recoverable():
    # Missing the required model_number.
    result, card = tools.dispatch("check_compatibility", {"ps_number": "PS11752778"})
    assert "error" in result
    assert card is None


# --- lookup_part -----------------------------------------------------------


def test_lookup_part_by_ps():
    result, card = tools.dispatch("lookup_part", {"ps_number": "PS11752778"})
    assert result["found"] is True
    assert card["kind"] == "product"
    assert card["payload"]["ps_number"] == "PS11752778"


def test_lookup_part_by_query():
    result, card = tools.dispatch("lookup_part", {"query": "ice maker"})
    assert result["found"] is True
    assert "matches" in result
    assert card["kind"] == "product"


def test_lookup_part_unknown_ps_no_card():
    result, card = tools.dispatch("lookup_part", {"ps_number": "PS00000000"})
    assert result["found"] is False
    assert card is None


def test_lookup_part_requires_some_arg():
    result, card = tools.dispatch("lookup_part", {})
    assert result["found"] is False


# --- check_compatibility ---------------------------------------------------


def test_check_compatibility_true():
    result, card = tools.dispatch(
        "check_compatibility", {"ps_number": "PS11746337", "model_number": "WDT780SAEM1"}
    )
    assert result["compatible"] is True
    assert card["kind"] == "compatibility"


def test_check_compatibility_false():
    result, card = tools.dispatch(
        "check_compatibility", {"ps_number": "PS11689058", "model_number": "WDT780SAEM1"}
    )
    assert result["compatible"] is False
    assert card["kind"] == "compatibility"


# --- get_install_guide -----------------------------------------------------


def test_get_install_guide():
    result, card = tools.dispatch("get_install_guide", {"ps_number": "PS11752778"})
    assert result["found"] is True
    assert card["kind"] == "install"
    assert card["payload"]["steps"]


def test_get_install_guide_unknown():
    result, card = tools.dispatch("get_install_guide", {"ps_number": "PS00000000"})
    assert result["found"] is False
    assert card is None


# --- orders ----------------------------------------------------------------


def test_get_order_status():
    result, card = tools.dispatch("get_order_status", {"order_id": "PS-100234"})
    assert result["found"] is True
    assert card["kind"] == "order"


def test_start_return_eligible_emits_card():
    result, card = tools.dispatch("start_return", {"order_id": "PS-100355"})
    assert result["ok"] is True
    assert card["kind"] == "order"
    # Restore mutated mock state.
    from app import data_access as da

    da.get_order("PS-100355")["status"] = "Delivered"
    da.get_order("PS-100355")["return_eligible"] = True


def test_start_return_not_eligible_still_cards_the_order():
    result, card = tools.dispatch("start_return", {"order_id": "PS-100571"})
    assert result["ok"] is False
    assert card["kind"] == "order"  # we still show the order so the user sees why


def test_cancel_order_unknown_no_card():
    result, card = tools.dispatch("cancel_order", {"order_id": "PS-000000"})
    assert result["ok"] is False
    assert card is None


# --- extensions ------------------------------------------------------------


def test_browse_parts():
    result, card = tools.dispatch("browse_parts", {"appliance": "dishwasher", "max_price": 50})
    assert result["found"] is True
    assert result["count"] >= 1
    assert card["kind"] == "product"


def test_find_water_filter_fridge():
    result, card = tools.dispatch("find_water_filter", {"model_number": "WRS321SDHZ"})
    assert result["has_filter"] is True
    assert card["kind"] == "product"


def test_find_water_filter_dishwasher_no_card():
    result, card = tools.dispatch("find_water_filter", {"model_number": "WDT780SAEM1"})
    assert result["found"] is True
    assert result["has_filter"] is False
    assert card is None


def test_list_parts_for_model():
    result, card = tools.dispatch("list_parts_for_model", {"model_number": "WDT780SAEM1"})
    assert result["found"] is True
    assert result["model"]["parts"]
    assert card is None  # no single card for a list view


# --- search_by_symptom (needs Chroma) --------------------------------------


@pytest.mark.skipif(
    not Path(retrieval.CHROMA_PATH).exists(),
    reason="Chroma not seeded — run `uv run python -m scripts.ingest` first",
)
def test_search_by_symptom():
    result, card = tools.dispatch(
        "search_by_symptom", {"text": "ice maker on my whirlpool fridge not working"}
    )
    assert result["found"] is True
    assert result["results"][0]["id"] == "fridge-ice-maker-not-working"
    assert card["kind"] == "repair"
    assert card["payload"]["suggested_parts"]
