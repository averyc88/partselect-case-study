"""Semantic-retrieval tests against the seeded Chroma store.

These require the index to be built first:

    cd backend && uv run python -m scripts.ingest

They're skipped (not failed) if `.chroma` is missing, so the suite stays green
on a fresh checkout before ingest has run. The headline assertion is the
brief's anchor query — a messy real-world phrasing must surface the right
repair doc as the top hit, which is the whole payoff of embedding
`user_phrasings` rather than the polished `content`.
"""

from pathlib import Path

import pytest

from app import retrieval

pytestmark = pytest.mark.skipif(
    not Path(retrieval.CHROMA_PATH).exists(),
    reason="Chroma not seeded — run `uv run python -m scripts.ingest` first",
)


def test_anchor_query_ranks_ice_maker_doc_first():
    # The brief's example, phrased naturally — not matching the title verbatim.
    results = retrieval.search("the ice maker on my Whirlpool fridge is not working")
    assert results
    assert results[0]["id"] == "fridge-ice-maker-not-working"
    # Suggested parts come along for the UI.
    assert "PS429725" in results[0]["related_parts"]


def test_paraphrase_still_matches():
    # A phrasing that shares almost no words with the title.
    results = retrieval.search("my freezer keeps icing up with thick frost")
    assert results[0]["id"] == "fridge-frost-buildup"


def test_dishwasher_drain_query():
    results = retrieval.search("standing water left in the bottom after a cycle")
    assert results[0]["id"] == "dishwasher-not-draining"


def test_appliance_filter_excludes_other_appliance():
    # A drainage query filtered to dishwasher must not return a fridge doc.
    results = retrieval.search("won't drain water", appliance="dishwasher")
    assert results
    assert all(r["appliance"] == "dishwasher" for r in results)


def test_results_carry_displayed_content_and_score():
    results = retrieval.search("dishwasher smells bad")
    top = results[0]
    assert top["content"]  # polished prose for display
    assert 0.0 <= top["score"] <= 1.0


def test_empty_query_returns_nothing():
    assert retrieval.search("") == []
