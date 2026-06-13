"""Data-integrity tests over the curated JSON catalog.

These don't test code so much as the *data* — they guard against the kind of
drift that's impossible to eyeball across 31 parts / 10 models / 5 orders:
dangling references, one-sided compatibility links, arithmetic that doesn't
reconcile. They're the safety net for every future hand-edit of `data/*.json`.
"""

from app import data_access as da

PARTS = da.PARTS
MODELS = da.MODELS
ORDERS = da.ORDERS
REPAIRS = da._load("repairs.json")

PART_PS = {p["ps_number"] for p in PARTS}
FILTER_PS = {p["ps_number"] for p in PARTS if p["category"] == "Water & Ice" and "Filter" in p["name"]}


# --- Uniqueness ------------------------------------------------------------


def test_no_duplicate_part_numbers():
    ps = [p["ps_number"] for p in PARTS]
    assert len(ps) == len(set(ps))


def test_no_duplicate_model_numbers():
    nums = [m["model_number"] for m in MODELS]
    assert len(nums) == len(set(nums))


def test_no_duplicate_order_ids():
    ids = [o["order_id"] for o in ORDERS]
    assert len(ids) == len(set(ids))


def test_no_duplicate_repair_ids():
    ids = [r["id"] for r in REPAIRS]
    assert len(ids) == len(set(ids))


# --- No dangling references ------------------------------------------------


def test_model_compatible_parts_all_exist():
    for m in MODELS:
        for ps in m["compatible_parts"]:
            assert ps in PART_PS, f"{m['model_number']} references unknown part {ps}"


def test_part_compatible_models_all_exist():
    model_nums = {m["model_number"] for m in MODELS}
    for p in PARTS:
        for model in p["compatible_models"]:
            assert model in model_nums, f"{p['ps_number']} references unknown model {model}"


def test_repair_related_parts_all_exist():
    for r in REPAIRS:
        for ps in r["related_parts"]:
            assert ps in PART_PS, f"repair {r['id']} references unknown part {ps}"


def test_order_items_all_exist_and_reconcile_with_catalog():
    for o in ORDERS:
        for item in o["items"]:
            assert item["ps_number"] in PART_PS, f"{o['order_id']} has unknown part {item['ps_number']}"
            part = da.get_part(item["ps_number"])
            assert item["name"] == part["name"], f"{o['order_id']} name mismatch for {item['ps_number']}"
            assert item["price"] == part["price"], f"{o['order_id']} price mismatch for {item['ps_number']}"


# --- The mirror: parts.json <-> models.json agree both ways ----------------


def test_compatibility_is_a_perfect_mirror():
    """Every link in one file must have its twin in the other.

    If model M lists part P as compatible, part P must list model M — and vice
    versa. This is the single most valuable integrity check: denormalized
    compatibility data drifts silently otherwise.
    """
    part_by_ps = {p["ps_number"]: p for p in PARTS}
    model_by_num = {m["model_number"]: m for m in MODELS}

    for m in MODELS:
        for ps in m["compatible_parts"]:
            assert m["model_number"] in part_by_ps[ps]["compatible_models"], (
                f"{m['model_number']} lists {ps}, but {ps} doesn't list {m['model_number']}"
            )
    for p in PARTS:
        for model in p["compatible_models"]:
            assert p["ps_number"] in model_by_num[model]["compatible_parts"], (
                f"{p['ps_number']} lists {model}, but {model} doesn't list {p['ps_number']}"
            )


# --- Order arithmetic ------------------------------------------------------


def test_order_totals_reconcile():
    for o in ORDERS:
        line_sum = round(sum(i["price"] * i["quantity"] for i in o["items"]), 2)
        assert line_sum == o["subtotal"], f"{o['order_id']} subtotal != line items"
        assert round(o["subtotal"] + o["shipping_cost"], 2) == o["total"], (
            f"{o['order_id']} subtotal + shipping != total"
        )


# --- Water filters ---------------------------------------------------------


def test_model_water_filters_exist_and_are_filters():
    for m in MODELS:
        wf = m.get("water_filter_ps")
        if wf is None:
            continue
        assert wf in PART_PS, f"{m['model_number']} references unknown filter {wf}"
        assert wf in FILTER_PS, f"{m['model_number']} water_filter_ps {wf} isn't a water filter"


def test_dishwashers_have_no_water_filter():
    for m in MODELS:
        if m["appliance"] == "dishwasher":
            assert m.get("water_filter_ps") is None, f"{m['model_number']} (dishwasher) has a filter set"


# --- Shape sanity ----------------------------------------------------------


def test_every_part_has_install_steps():
    for p in PARTS:
        assert p["install"]["steps"], f"{p['ps_number']} has no install steps"
        assert p["install"]["difficulty"]
        assert p["install"]["time"]


def test_appliances_are_in_scope():
    allowed = {"refrigerator", "dishwasher"}
    for p in PARTS:
        assert p["appliance"] in allowed
    for m in MODELS:
        assert m["appliance"] in allowed
