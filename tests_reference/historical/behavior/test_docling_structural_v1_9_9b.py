from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.docling_structural.canonical_ir_v1_9_6 import GenericTechnicalDocumentCompiler
from src.docling_structural.model import DocumentGraph, Node, NodeType
from src.docling_structural.scoped_evidence_v1_5 import EvidenceType
from src.docling_structural.table_relation_resolver_v1_9_9b import (
    CanonicalTableRelationResolver,
    CONFLICT,
    MATCH,
    UNKNOWN,
    compare_relation,
    parse_table_query_relation,
    select_canonical_candidate,
)


def _field(value: str, status: str = "EXPLICIT", confidence: str = "HIGH") -> dict[str, str]:
    return {"value": value, "status": status, "provenance": "test", "confidence_class": confidence}


def test_conservative_parser_matches_frozen_literal_contract() -> None:
    parsed = parse_table_query_relation(
        "In the Example Maker 2024 table for family-x, what value is listed for BTU Rating for Model 30 with configuration Natural Gas?",
        ["Example Maker"],
    )
    assert parsed["requested_subject"]["value"] == "Model 30"
    assert parsed["requested_attribute"]["value"] == "BTU Rating"
    assert parsed["requested_configuration"]["value"] == "Natural Gas"
    assert parsed["requested_unit"]["value"] == "BTU"
    assert parsed["document_type"]["value"] == UNKNOWN
    assert parsed["parser_provenance"]["generic_ir_substring_promotion"] is False


def test_unknown_is_not_coerced_to_conflict() -> None:
    query = _field(UNKNOWN, status="UNKNOWN", confidence="NONE")
    candidate = {**_field("Model 30"), "alternatives": []}
    result = compare_relation(query, candidate, query_name="requested_subject", candidate_name="subject")
    assert result["state"] == UNKNOWN


def test_explicit_match_and_conflict_remain_three_state() -> None:
    query = _field("Model 30")
    matching = {**_field("Model 30"), "alternatives": []}
    wrong = {**_field("Model 36"), "alternatives": []}
    assert compare_relation(query, matching, query_name="requested_subject", candidate_name="subject")["state"] == MATCH
    assert compare_relation(query, wrong, query_name="requested_subject", candidate_name="subject")["state"] == CONFLICT


def test_non_table_dispatch_bypasses_resolver_exactly() -> None:
    result = select_canonical_candidate(
        evidence_type=EvidenceType.PROCEDURE,
        query="How do I start it?",
        candidate_ids=["a", "b"],
        existing_selected_candidate="b",
    )
    assert result == {
        "resolver_executed": False,
        "selection_path": "NON_TABLE_UNCHANGED",
        "final_selected_candidate": "b",
        "input_candidate_ids": ["a", "b"],
    }


def test_table_resolver_rejects_non_table_direct_execution() -> None:
    resolver = object.__new__(CanonicalTableRelationResolver)
    with pytest.raises(ValueError, match="TABLE_SPEC"):
        resolver.select(
            query="anything",
            evidence_type=EvidenceType.NARRATIVE,
            candidate_ids=[],
            neural_scores={},
        )
