from src.identifier_inventory import audit_identifier_inventory
from src.product_discovery import (
    MULTIPLE_PLAUSIBLE_CANDIDATES,
    build_discovery_query,
    candidate_from_row,
    resolve_candidates,
)


def test_identifier_inventory_reports_required_collision_dimensions() -> None:
    inventory = audit_identifier_inventory(
        [
            {
                "product_id": 1,
                "brand": "Maker A",
                "model": "AOG24-GA",
                "aliases": ["AOG 24 GA", "---"],
            },
            {
                "product_id": 2,
                "brand": "Maker A",
                "model": "AOG24GA",
                "aliases": ["AOG 24 GA"],
            },
            {
                "product_id": 3,
                "brand": "Maker B",
                "mpn": "AOG/24/GA",
            },
        ]
    )

    assert inventory["total_raw_identifiers"] == 6
    assert inventory["unique_raw_identifiers"] == 5
    assert inventory["unique_normalized_identifiers"] == 1
    assert inventory["normalization_collision_count"] == 1
    assert inventory["manufacturer_specific_collision_count"] == 1
    assert "AOG24-GA" in inventory["punctuation_dependent_identifiers"]
    assert inventory["empty_normalized_identifiers"][0]["raw"] == "---"
    assert "AOG24GA" in inventory["aliases_mapping_to_multiple_products"]


def test_normalized_identifier_collision_fails_closed() -> None:
    query = build_discovery_query("Find AOG24-GA")
    rows = (
        {
            "product_id": 1,
            "model": "AOG24-GA",
            "mpn": "AOG24-GA",
        },
        {
            "product_id": 2,
            "model": "AOG 24 GA",
            "mpn": "AOG 24 GA",
        },
    )
    candidates = tuple(candidate_from_row(row, query) for row in rows)

    resolution = resolve_candidates(candidates, query)

    assert resolution.state == MULTIPLE_PLAUSIBLE_CANDIDATES
    assert resolution.selected is None


def test_exact_identifier_query_is_separate_from_semantic_text() -> None:
    question = "What cutout dimensions apply to AOG24-GA?"
    query = build_discovery_query(question)

    assert query.retrieval_query.exact_identifier_queries == ("AOG24GA",)
    assert query.retrieval_query.semantic_query_text == question
    assert (
        query.retrieval_query.semantic_query_text
        != query.retrieval_query.exact_identifier_queries[0]
    )
