"""Unit tests for the deterministic data-access layer.

Deterministic lookups are trivially testable — that's a deliberate design
payoff. We anchor on the brief's real identifiers (PS11752778, WDT780SAEM1)
so the tests double as a check that the headline queries resolve.
"""

import pytest

from app import data_access as da


# --- get_part --------------------------------------------------------------


def test_get_part_exact():
    part = da.get_part("PS11752778")
    assert part is not None
    assert part["name"] == "Refrigerator Door Shelf Bin"
    assert part["price"] == 36.98


def test_get_part_is_case_insensitive_and_trims():
    assert da.get_part("  ps11752778  ") is da.get_part("PS11752778")


def test_get_part_unknown_returns_none():
    assert da.get_part("PS00000000") is None


# --- search_parts ----------------------------------------------------------


def test_search_parts_by_name():
    results = da.search_parts("ice maker")
    assert any(p["ps_number"] == "PS11739123" for p in results)


def test_search_parts_filters_by_appliance():
    results = da.search_parts("door", appliance="dishwasher")
    assert all(p["appliance"] == "dishwasher" for p in results)


def test_search_parts_empty_query():
    assert da.search_parts("") == []


# --- get_install_guide -----------------------------------------------------


def test_get_install_guide():
    guide = da.get_install_guide("PS11752778")
    assert guide["difficulty"] == "Easy"
    assert len(guide["steps"]) >= 1
    assert guide["name"] == "Refrigerator Door Shelf Bin"


def test_get_install_guide_unknown_returns_none():
    assert da.get_install_guide("PS00000000") is None


# --- check_compatibility ---------------------------------------------------


def test_compatible_pair():
    # PS11746337 (upper rack adjuster) fits the brief's WDT780SAEM1 dishwasher.
    result = da.check_compatibility("PS11746337", "WDT780SAEM1")
    assert result["compatible"] is True
    assert result["part_known"] and result["model_known"]


def test_incompatible_pair():
    # A Bosch dishwasher part vs. the Whirlpool dishwasher model.
    result = da.check_compatibility("PS11689058", "WDT780SAEM1")
    assert result["compatible"] is False
    assert result["part_known"] and result["model_known"]


def test_compatibility_case_insensitive():
    result = da.check_compatibility("ps11746337", "wdt780saem1")
    assert result["compatible"] is True


def test_compatibility_unknown_part():
    result = da.check_compatibility("PS00000000", "WDT780SAEM1")
    assert result["compatible"] is False
    assert result["part_known"] is False
    assert result["model_known"] is True


def test_compatibility_unknown_model():
    result = da.check_compatibility("PS11746337", "BOGUSMODEL")
    assert result["compatible"] is False
    assert result["model_known"] is False


# --- models ----------------------------------------------------------------


def test_get_model():
    m = da.get_model("WDT780SAEM1")
    assert m["brand"] == "Whirlpool"
    assert m["appliance"] == "dishwasher"


def test_list_parts_for_model():
    result = da.list_parts_for_model("WDT780SAEM1")
    assert result["brand"] == "Whirlpool"
    ps_numbers = {p["ps_number"] for p in result["parts"]}
    assert "PS11746337" in ps_numbers
    # Every returned part is a full record, not just a PS#.
    assert all("price" in p for p in result["parts"])


def test_list_parts_for_unknown_model():
    assert da.list_parts_for_model("BOGUS") is None


def test_find_water_filter_for_fridge():
    result = da.find_water_filter("WRS321SDHZ")
    assert result["filter"] is not None
    assert result["filter"]["ps_number"] == "PS10065695"


def test_find_water_filter_for_dishwasher_is_none_filter():
    # Known model, but dishwashers take no filter — distinct from unknown model.
    result = da.find_water_filter("WDT780SAEM1")
    assert result is not None
    assert result["filter"] is None


def test_find_water_filter_unknown_model():
    assert da.find_water_filter("BOGUS") is None


# --- browse_parts ----------------------------------------------------------


def test_browse_by_appliance():
    results = da.browse_parts(appliance="dishwasher", limit=100)
    assert results
    assert all(p["appliance"] == "dishwasher" for p in results)


def test_browse_by_brand_and_price():
    results = da.browse_parts(brand="Whirlpool", max_price=50.0, limit=100)
    assert all(p["brand"] == "Whirlpool" and p["price"] <= 50.0 for p in results)


def test_browse_in_stock_only():
    results = da.browse_parts(in_stock_only=True, limit=100)
    assert all(p["in_stock"] for p in results)


def test_browse_sorted_by_price_ascending():
    results = da.browse_parts(limit=100)
    prices = [p["price"] for p in results]
    assert prices == sorted(prices)


# --- orders ----------------------------------------------------------------


def test_get_order():
    o = da.get_order("PS-100234")
    assert o["status"] == "Delivered"


def test_get_order_unknown():
    assert da.get_order("PS-999999") is None


# Order mutations mutate the in-memory mock, so isolate each in its own state
# by operating on different orders / restoring as needed.


def test_start_return_eligible():
    result = da.start_return("PS-100355")
    assert result["ok"] is True
    assert result["order"]["status"] == "Return Initiated"
    # Restore for any other test that might touch this order.
    da.get_order("PS-100355")["status"] = "Delivered"
    da.get_order("PS-100355")["return_eligible"] = True


def test_start_return_not_eligible():
    result = da.start_return("PS-100571")  # Shipped, not return-eligible
    assert result["ok"] is False
    assert result["reason"] == "not_eligible"


def test_start_return_unknown():
    result = da.start_return("PS-000000")
    assert result["ok"] is False
    assert result["reason"] == "not_found"


def test_cancel_order_cancellable():
    result = da.cancel_order("PS-100698")  # Processing, cancellable
    assert result["ok"] is True
    assert result["order"]["status"] == "Cancelled"
    # Restore.
    da.get_order("PS-100698")["status"] = "Processing"
    da.get_order("PS-100698")["cancellable"] = True


def test_cancel_order_not_cancellable():
    result = da.cancel_order("PS-100234")  # Delivered, not cancellable
    assert result["ok"] is False
    assert result["reason"] == "not_cancellable"


def test_cancel_order_unknown():
    result = da.cancel_order("PS-000000")
    assert result["ok"] is False
    assert result["reason"] == "not_found"
