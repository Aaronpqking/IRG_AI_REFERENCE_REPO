import pytest

from src.citation_validation import (
    MALFORMED_CITATION,
    MISSING_CITATION,
    PAGE_MISMATCH,
    PARTIALLY_SUPPORTED,
    PASS,
    SUPPORTED,
    UNSUPPORTED,
    UNKNOWN_SOURCE,
    validate_answer_citations,
)


def pdf_source(
    *,
    filename: str = "manual.pdf",
    relative_path: str = "manuals/manual.pdf",
    document_id: str = "doc-1",
    page_start: int = 2,
    page_end: int = 3,
    evidence_text: str | None = None,
) -> dict[str, object]:
    source = {
        "type": "pdf",
        "chunk_id": "pdf-1",
        "document_id": document_id,
        "filename": filename,
        "relative_path": relative_path,
        "page_start": page_start,
        "page_end": page_end,
    }
    if evidence_text is not None:
        source["evidence_text"] = evidence_text
    return source


def database_source(
    product_id: int = 123,
    *,
    evidence_text: str | None = None,
) -> dict[str, object]:
    source = {
        "type": "database_candidate",
        "source_system": "Flamy Product Read Model",
        "object": "product_details",
        "product_id": product_id,
    }
    if evidence_text is not None:
        source["evidence_text"] = evidence_text
    return source


def test_nonempty_sources_without_in_answer_citation_fail() -> None:
    result = validate_answer_citations("The clearance is 12 inches.", [pdf_source()])

    assert result.status == MISSING_CITATION
    assert result.missing_required_citations is True


@pytest.mark.parametrize(
    "answer",
    (
        "Text [source: manual.pdf]",
        "Text [source: manual.pdf, page two]",
        "Text [source: manual.pdf, page 2",
    ),
)
def test_malformed_citations_fail(answer: str) -> None:
    assert validate_answer_citations(answer, [pdf_source()]).status == MALFORMED_CITATION


def test_unknown_pdf_citation_fails() -> None:
    result = validate_answer_citations(
        "Text [source: other.pdf, page 2]",
        [pdf_source()],
    )

    assert result.status == UNKNOWN_SOURCE
    assert result.unmatched_citations == ("[source: other.pdf, page 2]",)


def test_wrong_pdf_page_fails() -> None:
    result = validate_answer_citations(
        "Text [source: manual.pdf, page 8]",
        [pdf_source()],
    )

    assert result.status == PAGE_MISMATCH


def test_valid_pdf_citation_passes_with_case_and_path_normalization() -> None:
    result = validate_answer_citations(
        r"Text [source: MANUALS\MANUAL.PDF, page 3]",
        [pdf_source()],
    )

    assert result.status == PASS
    assert result.matched_source_ids == (
        "pdf:doc-1:pages:2-3",
    )


def test_expanded_model_visible_page_is_a_valid_citation_target() -> None:
    source = {
        **pdf_source(),
        "page_start": 3,
        "page_end": 4,
        "evidence_id": "pdf:doc-1:pages:3-4",
    }

    result = validate_answer_citations(
        "Continued fact [source: manual.pdf, page 4]",
        [source],
    )

    assert result.status == PASS
    assert result.matched_source_ids == (
        "pdf:doc-1:pages:3-4",
    )


def test_claim_support_uses_full_internal_evidence_not_bounded_preview() -> None:
    source = pdf_source(page_start=1, page_end=1)
    source["text_preview"] = "Introductory safety text. " * 20
    source["evidence_text"] = (
        f"{source['text_preview']} Model GR18A supports 24, 30, and 36 inch "
        "grills with a 17 by 12.5 inch cooking area."
    )

    result = validate_answer_citations(
        "Model GR18A supports 24, 30, and 36 inch grills with a 17 by "
        "12.5 inch cooking area. [source: manual.pdf, page 1]",
        [source],
    )

    assert result.status == PASS
    assert result.grounding_status == SUPPORTED


def test_claim_support_can_use_governed_path_year_metadata() -> None:
    source = pdf_source(
        filename="tebq30g-c_specs.pdf",
        relative_path="twin_eagles/grills/c_series/tebq30g-c/2024/specification/tebq30g-c_specs.pdf",
        page_start=1,
        page_end=1,
    )
    source["evidence_text"] = "The specification lists model TEBQ30G-C."

    result = validate_answer_citations(
        "The 2024 specification lists model TEBQ30G-C. "
        "[source: tebq30g-c_specs.pdf, page 1]",
        [source],
    )

    assert result.status == PASS
    assert result.grounding_status == SUPPORTED


def test_path_metadata_does_not_support_unrelated_numeric_claim() -> None:
    source = pdf_source(
        relative_path="manuals/2024/manual.pdf",
        page_start=1,
        page_end=1,
    )
    source["evidence_text"] = "The manual lists the supported model."

    result = validate_answer_citations(
        "The output is 9999 watts. [source: manual.pdf, page 1]",
        [source],
    )

    assert result.grounding_status != SUPPORTED


def test_valid_database_citation_passes() -> None:
    result = validate_answer_citations(
        "Text [source: Flamy Product Read Model, product ID 123]",
        [database_source()],
    )

    assert result.status == PASS
    assert result.matched_source_ids == (
        "db:product:123",
    )


def test_mixed_pdf_and_database_citations_pass() -> None:
    result = validate_answer_citations(
        "Fact one [source: manual.pdf, page 2] "
        "and fact two [source: product database, product_id 123].",
        [pdf_source(), database_source()],
    )

    assert result.status == PASS
    assert len(result.matched_source_ids) == 2


def test_duplicate_valid_citations_pass_once_per_source() -> None:
    result = validate_answer_citations(
        "Fact [source: manual.pdf, page 2] "
        "again [source: manual.pdf, page 2].",
        [pdf_source()],
    )

    assert result.status == PASS
    assert result.matched_source_ids == (
        "pdf:doc-1:pages:2-3",
    )
    assert "DUPLICATE_CITATION_IGNORED" in result.reason_codes


def test_multiple_valid_pdf_sources_pass() -> None:
    result = validate_answer_citations(
        "One [source: manual.pdf, page 2] "
        "two [source: second.pdf, page 5].",
        [
            pdf_source(),
            pdf_source(
                filename="second.pdf",
                relative_path="manuals/second.pdf",
                document_id="doc-2",
                page_start=5,
                page_end=5,
            ),
        ],
    )

    assert result.status == PASS
    assert len(result.matched_source_ids) == 2


def test_citation_cannot_bind_to_candidate_basis() -> None:
    selected = database_source(123)
    candidate_basis = database_source(999)

    result = validate_answer_citations(
        "Candidate [source: product database, product_id 999].",
        [selected],
    )

    assert candidate_basis["product_id"] == 999
    assert result.status == UNKNOWN_SOURCE


def test_cross_product_pdf_citation_is_visible_as_grounding_failure() -> None:
    sources = [
        {
            "source_type": "technical_pdf",
            "evidence_id": "pdf:a:pages:1-1",
            "filename": "a.pdf",
            "relative_path": "manuals/a.pdf",
            "page_start": 1,
            "page_end": 1,
            "product_ref_id": "product_ref_a",
            "product_display_identity": "ZX24-A",
            "evidence_text": "The documented clearance is 4 inches.",
        },
        {
            "source_type": "technical_pdf",
            "evidence_id": "pdf:b:pages:1-1",
            "filename": "b.pdf",
            "relative_path": "manuals/b.pdf",
            "page_start": 1,
            "page_end": 1,
            "product_ref_id": "product_ref_b",
            "product_display_identity": "QX30-B",
            "evidence_text": "QX30-B has a different documented clearance.",
        },
    ]

    result = validate_answer_citations(
        "QX30-B requires 4 inches. [source: manuals/a.pdf, page 1]",
        sources,
    )

    assert result.status == "PASS"
    assert result.grounding_status == "UNSUPPORTED"
    assert "CROSS_PRODUCT_CITATION" in result.reason_codes
    assert result.support_results[0]["product_owner_status"] == "MISMATCH"


def test_pdf_only_claim_uses_only_supporting_pdf_citation() -> None:
    answer = "The cooking area is 17 by 12.5 inches. [source: manual.pdf, page 2]"
    result = validate_answer_citations(
        answer,
        [
            pdf_source(evidence_text="The cooking area is 17 by 12.5 inches."),
            database_source(evidence_text="The product name is Stainless Steel Griddle."),
        ],
    )

    assert result.status == PASS
    assert result.grounding_status == SUPPORTED
    assert result.matched_source_ids == ("pdf:doc-1:pages:2-3",)


def test_database_only_claim_uses_only_supporting_database_citation() -> None:
    answer = (
        "The product name is Stainless Steel Griddle. "
        "[source: Flamy Product Read Model, product ID 123]"
    )
    result = validate_answer_citations(
        answer,
        [
            pdf_source(evidence_text="The cooking area is 17 by 12.5 inches."),
            database_source(evidence_text="The product name is Stainless Steel Griddle."),
        ],
    )

    assert result.status == PASS
    assert result.grounding_status == SUPPORTED
    assert result.matched_source_ids == ("db:product:123",)


def test_cross_source_reconciliation_claim_retains_both_citations_in_stable_order() -> None:
    claim = (
        "The database scalar of 100000 BTU is contained within the manual "
        "range of 100000 to 128000 BTU."
    )
    answer = (
        f"{claim} [source: Flamy Product Read Model, product ID 123] "
        "[source: manual.pdf, page 2]"
    )
    result = validate_answer_citations(
        answer,
        [
            database_source(evidence_text=claim),
            pdf_source(evidence_text=claim),
        ],
    )

    assert result.status == PASS
    assert result.grounding_status == SUPPORTED
    assert result.matched_source_ids == (
        "db:product:123",
        "pdf:doc-1:pages:2-3",
    )


def test_irrelevant_extra_citation_is_not_treated_as_supporting_the_claim() -> None:
    claim = "The cooking area is 17 by 12.5 inches."
    answer = (
        f"{claim} [source: manual.pdf, page 2] "
        "[source: Flamy Product Read Model, product ID 123]"
    )
    result = validate_answer_citations(
        answer,
        [
            pdf_source(evidence_text=claim),
            database_source(evidence_text="The product name is Stainless Steel Griddle."),
        ],
    )

    assert result.status == PASS
    assert result.grounding_status != SUPPORTED


_COOKING_AREA_DB_EVIDENCE = (
    "Cooking Surface - 432 sq. in. Total Cooking Area "
    "(Includes Warming Rack) - 548 sq. in."
)


@pytest.mark.parametrize(
    "formatted_value",
    (
        "432 square inches",
        "432 sq. in.",
        "432 sq in",
        "432-square-inch",
    ),
)
def test_database_scalar_and_square_inch_formatting_are_grounded(
    formatted_value: str,
) -> None:
    result = validate_answer_citations(
        f"The cooking surface is {formatted_value}. "
        "[source: Flamy Product Read Model, product ID 123]",
        [database_source(evidence_text=_COOKING_AREA_DB_EVIDENCE)],
    )

    assert result.status == PASS
    assert result.grounding_status == SUPPORTED
    support = result.support_results[0]
    assert support["claim_numbers"] == ["432"]
    assert support["claim_units"] == ["squareinch"]
    assert support["decision_rule"] == "CANONICAL_VALUE_AND_CONTEXT_MATCH"


def test_database_second_scalar_is_grounded() -> None:
    result = validate_answer_citations(
        "The total cooking area is 548 square inches. "
        "[source: Flamy Product Read Model, product ID 123]",
        [database_source(evidence_text=_COOKING_AREA_DB_EVIDENCE)],
    )

    assert result.grounding_status == SUPPORTED
    assert result.support_results[0]["claim_numbers"] == ["548"]


def test_database_combined_scalar_claim_is_grounded() -> None:
    result = validate_answer_citations(
        "The cooking surface is 432 square inches; the total cooking area "
        "is 548 square inches. "
        "[source: Flamy Product Read Model, product ID 123]",
        [database_source(evidence_text=_COOKING_AREA_DB_EVIDENCE)],
    )

    assert result.grounding_status == SUPPORTED
    assert result.support_results[0]["claim_numbers"] == ["432", "548"]


def test_comma_formatted_numeric_value_is_equivalent() -> None:
    result = validate_answer_citations(
        "The listed capacity is 1200 cubic inches. "
        "[source: Flamy Product Read Model, product ID 123]",
        [database_source(evidence_text="Listed capacity - 1,200 cubic inches.")],
    )

    assert result.grounding_status == SUPPORTED
    assert result.support_results[0]["claim_numbers"] == ["1200"]


def test_matching_number_with_unrelated_unit_remains_unsupported() -> None:
    result = validate_answer_citations(
        "The electrical output is 432 watts. "
        "[source: Flamy Product Read Model, product ID 123]",
        [database_source(evidence_text="The cooking area is 432 square inches.")],
    )

    assert result.status == PASS
    assert result.grounding_status == UNSUPPORTED
    assert result.support_results[0]["decision_rule"] == "UNITS_UNSUPPORTED"


def test_database_claim_for_another_product_fails_ownership() -> None:
    cited = database_source(
        123,
        evidence_text="ALPHA cooking area is 432 square inches.",
    )
    cited.update(
        product_ref_id="product_ref_alpha",
        product_display_identity="ALPHA",
    )
    other = database_source(
        456,
        evidence_text="BETA cooking area is 432 square inches.",
    )
    other.update(
        product_ref_id="product_ref_beta",
        product_display_identity="BETA",
    )

    result = validate_answer_citations(
        "BETA cooking area is 432 square inches. "
        "[source: Flamy Product Read Model, product ID 123]",
        [cited, other],
    )

    assert result.status == PASS
    assert result.grounding_status == UNSUPPORTED
    assert result.support_results[0]["product_owner_status"] == "MISMATCH"
    assert result.support_results[0]["decision_rule"] == "PRODUCT_OWNER_MISMATCH"


def test_mixed_database_and_pdf_claims_bind_to_their_own_citations() -> None:
    result = validate_answer_citations(
        "The cooking surface is 432 square inches. "
        "[source: Flamy Product Read Model, product ID 123] "
        "The installation clearance is 6 inches. "
        "[source: manual.pdf, page 2]",
        [
            database_source(evidence_text="Cooking Surface - 432 sq. in."),
            pdf_source(evidence_text="Installation clearance is 6 in."),
        ],
    )

    assert result.status == PASS
    assert result.grounding_status == SUPPORTED
    assert [item["status"] for item in result.support_results] == [
        SUPPORTED,
        SUPPORTED,
    ]


def test_supported_pdf_path_remains_canonical() -> None:
    result = validate_answer_citations(
        "The installation clearance is 6 inches. "
        "[source: manual.pdf, page 2]",
        [pdf_source(evidence_text="Installation clearance is 6 in.")],
    )

    assert result.grounding_status == SUPPORTED


def test_resolved_citation_with_unsupported_evidence_stays_unsupported() -> None:
    result = validate_answer_citations(
        "The cooking surface is 432 square inches. "
        "[source: Flamy Product Read Model, product ID 123]",
        [database_source(evidence_text="The product weighs 75 pounds.")],
    )

    assert result.status == PASS
    assert result.grounding_status == UNSUPPORTED


def test_matching_uncited_evidence_does_not_create_support() -> None:
    result = validate_answer_citations(
        "The cooking surface is 432 square inches.",
        [database_source(evidence_text=_COOKING_AREA_DB_EVIDENCE)],
        citations_required=True,
    )

    assert result.status == MISSING_CITATION
    assert result.grounding_status == UNSUPPORTED
    assert result.support_results == ()


def owned_database_source(
    product_id: int,
    identity: str,
    evidence_text: str,
) -> dict[str, object]:
    source = database_source(product_id, evidence_text=evidence_text)
    source.update(
        product_ref_id=f"product_ref_{identity.casefold()}",
        product_display_identity=identity,
    )
    return source


def owned_pdf_source(
    identity: str,
    evidence_text: str,
    *,
    filename: str = "manual.pdf",
    document_id: str = "doc-owned",
) -> dict[str, object]:
    source = pdf_source(
        filename=filename,
        relative_path=f"manuals/{filename}",
        document_id=document_id,
        page_start=1,
        page_end=1,
        evidence_text=evidence_text,
    )
    source.update(
        product_ref_id=f"product_ref_{identity.casefold()}",
        product_display_identity=identity,
    )
    return source


def test_two_product_compound_claim_uses_collective_citation_support() -> None:
    result = validate_answer_citations(
        "ALPHA has a 432 square inch cooking surface and BETA has a 500 "
        "square inch cooking surface. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(
                101,
                "ALPHA",
                "ALPHA cooking surface is 432 square inches.",
            ),
            owned_database_source(
                202,
                "BETA",
                "BETA cooking surface is 500 square inches.",
            ),
        ],
    )

    assert result.status == PASS
    assert result.grounding_status == SUPPORTED
    assert all(
        item["collective_claim_status"] == SUPPORTED
        for item in result.support_results
    )
    assert all(item["supported_element_ids"] for item in result.support_results)


def test_comparative_arithmetic_uses_supported_cited_premises() -> None:
    result = validate_answer_citations(
        "ALPHA is 10 inches long and BETA is 12 inches long, so BETA is "
        "2 inches longer. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(101, "ALPHA", "ALPHA is 10 inches long."),
            owned_database_source(202, "BETA", "BETA is 12 inches long."),
        ],
    )

    assert result.grounding_status == SUPPORTED
    elements = result.support_results[0]["claim_elements"]
    derived = [
        element
        for element in elements
        if element["element_type"] == "derived_comparison"
    ]
    assert len(derived) == 1
    assert derived[0]["required_numbers"] == ["2"]
    assert derived[0]["status"] == SUPPORTED
    assert len(derived[0]["supporting_citation_ids"]) == 2


def test_missing_product_citation_leaves_compound_claim_partial() -> None:
    result = validate_answer_citations(
        "ALPHA is 10 inches long and BETA is 12 inches long. "
        "[source: Flamy Product Read Model, product ID 101]",
        [
            owned_database_source(101, "ALPHA", "ALPHA is 10 inches long."),
            owned_database_source(202, "BETA", "BETA is 12 inches long."),
        ],
    )

    assert result.status == PASS
    assert result.grounding_status == PARTIALLY_SUPPORTED


def test_irrelevant_citation_cannot_ride_on_collective_coverage() -> None:
    result = validate_answer_citations(
        "ALPHA has a 432 square inch cooking surface. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(
                101,
                "ALPHA",
                "ALPHA cooking surface is 432 square inches.",
            ),
            owned_database_source(
                202,
                "BETA",
                "BETA product weight is 75 pounds.",
            ),
        ],
    )

    assert result.grounding_status == PARTIALLY_SUPPORTED
    assert result.support_results[0]["status"] == SUPPORTED
    assert result.support_results[1]["status"] == UNSUPPORTED
    assert result.support_results[1]["decision_rule"] == "IRRELEVANT_CITATION"


def test_number_unsupported_by_all_eligible_sources_remains_partial() -> None:
    result = validate_answer_citations(
        "ALPHA has a 432 square inch cooking surface and BETA has a 999 "
        "square inch cooking surface. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(
                101,
                "ALPHA",
                "ALPHA cooking surface is 432 square inches.",
            ),
            owned_database_source(
                202,
                "BETA",
                "BETA cooking surface is 500 square inches.",
            ),
        ],
    )

    assert result.grounding_status == PARTIALLY_SUPPORTED
    elements = result.support_results[0]["claim_elements"]
    unsupported = [
        element for element in elements if element["required_numbers"] == ["999"]
    ]
    assert unsupported[0]["status"] == UNSUPPORTED


def test_wrong_product_number_cannot_support_owned_element() -> None:
    result = validate_answer_citations(
        "ALPHA has a 432 square inch cooking surface and BETA has a 500 "
        "square inch cooking surface. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(
                101,
                "ALPHA",
                "ALPHA cooking surface is 500 square inches.",
            ),
            owned_database_source(
                202,
                "BETA",
                "BETA cooking surface is 700 square inches.",
            ),
        ],
    )

    assert result.grounding_status == UNSUPPORTED


def test_shared_manual_requires_canonical_multi_product_applicability() -> None:
    source = owned_pdf_source(
        "SHARED-MANUAL",
        "ALPHA clearance is 6 inches. BETA clearance is 8 inches.",
    )
    source["applicable_product_ref_ids"] = [
        "product_ref_alpha",
        "product_ref_beta",
    ]

    result = validate_answer_citations(
        "ALPHA requires 6 inches clearance and BETA requires 8 inches "
        "clearance. [source: manual.pdf, page 1]",
        [
            owned_database_source(101, "ALPHA", "ALPHA product record."),
            owned_database_source(202, "BETA", "BETA product record."),
            source,
        ],
    )

    assert result.grounding_status == SUPPORTED
    elements = result.support_results[0]["claim_elements"]
    assert {element["product_owner"] for element in elements} == {
        "alpha",
        "beta",
    }


def test_single_source_claim_does_not_enter_collective_path() -> None:
    result = validate_answer_citations(
        "ALPHA has a 432 square inch cooking surface. "
        "[source: Flamy Product Read Model, product ID 101]",
        [
            owned_database_source(
                101,
                "ALPHA",
                "ALPHA cooking surface is 432 square inches.",
            )
        ],
    )

    assert result.grounding_status == SUPPORTED
    assert "collective_claim_status" not in result.support_results[0]
    assert result.support_results[0]["decision_rule"] == (
        "CANONICAL_VALUE_AND_CONTEXT_MATCH"
    )


def test_mixed_database_pdf_compound_claim_uses_each_source() -> None:
    result = validate_answer_citations(
        "ALPHA output is 10 watts and installation clearance is 6 inches. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: manual.pdf, page 1]",
        [
            owned_database_source(101, "ALPHA", "ALPHA output is 10 watts."),
            owned_pdf_source(
                "ALPHA",
                "ALPHA installation clearance is 6 inches.",
            ),
        ],
    )

    assert result.grounding_status == SUPPORTED
    assert all(item["supported_element_ids"] for item in result.support_results)


def test_each_citation_may_independently_support_entire_claim() -> None:
    evidence = "ALPHA cooking surface is 432 square inches."
    result = validate_answer_citations(
        "ALPHA cooking surface is 432 square inches. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: manual.pdf, page 1]",
        [
            owned_database_source(101, "ALPHA", evidence),
            owned_pdf_source("ALPHA", evidence),
        ],
    )

    assert result.grounding_status == SUPPORTED
    assert all(item["status"] == SUPPORTED for item in result.support_results)


def test_collective_support_is_stable_when_citation_order_changes() -> None:
    sources = [
        owned_database_source(101, "ALPHA", "ALPHA length is 10 inches."),
        owned_database_source(202, "BETA", "BETA length is 12 inches."),
    ]
    claim = "ALPHA is 10 inches long and BETA is 12 inches long."
    first = validate_answer_citations(
        f"{claim} [source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        sources,
    )
    second = validate_answer_citations(
        f"{claim} [source: Flamy Product Read Model, product ID 202] "
        "[source: Flamy Product Read Model, product ID 101]",
        sources,
    )

    assert first.grounding_status == SUPPORTED
    assert second.grounding_status == SUPPORTED


def test_stage1_abbreviation_safe_claim_span_is_preserved() -> None:
    result = validate_answer_citations(
        "The cooking surface is 432 sq. in.; the total cooking area is "
        "548 sq. in. [source: Flamy Product Read Model, product ID 123]",
        [database_source(evidence_text=_COOKING_AREA_DB_EVIDENCE)],
    )

    assert result.grounding_status == SUPPORTED
    assert result.support_results[0]["claim_text"].startswith(
        "The cooking surface is 432 sq. in."
    )
    assert result.support_results[0]["claim_numbers"] == ["432", "548"]


@pytest.mark.parametrize(
    "claim",
    (
        "ALPHA and BETA are both 432 square inches.",
        "Both ALPHA and BETA have a 432-square-inch cooking surface.",
        "The cooking surface for ALPHA and BETA is 432 square inches.",
    ),
)
def test_two_owner_shared_scalar_expands_owner_bound_premises(
    claim: str,
) -> None:
    result = validate_answer_citations(
        f"{claim} [source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(
                101,
                "ALPHA",
                "ALPHA cooking surface is 432 square inches.",
            ),
            owned_database_source(
                202,
                "BETA",
                "BETA cooking surface is 432 square inches.",
            ),
        ],
    )

    assert result.grounding_status == SUPPORTED
    group = result.support_results[0]["claim_elements"][0]
    assert group["element_type"] == "owner_group_fact"
    assert group["product_owners"] == ["alpha", "beta"]
    assert [premise["status"] for premise in group["owner_premises"]] == [
        SUPPORTED,
        SUPPORTED,
    ]
    assert len(group["supporting_citation_ids"]) == 2


def test_owner_group_same_size_relation_requires_both_premises() -> None:
    result = validate_answer_citations(
        "ALPHA and BETA are the same size at 432 sq. in. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(
                101,
                "ALPHA",
                "ALPHA cooking surface is 432 square inches.",
            ),
            owned_database_source(
                202,
                "BETA",
                "BETA cooking surface is 432 square inches.",
            ),
        ],
    )

    assert result.grounding_status == SUPPORTED
    elements = result.support_results[0]["claim_elements"]
    relation = [
        element
        for element in elements
        if element["element_type"] == "comparative_relation"
    ][0]
    assert relation["status"] == SUPPORTED
    assert len(relation["supporting_citation_ids"]) == 2


def test_three_owner_shared_scalar_requires_three_owner_premises() -> None:
    result = validate_answer_citations(
        "ALPHA, BETA, and GAMMA each have a 432 square inch cooking surface. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202] "
        "[source: Flamy Product Read Model, product ID 303]",
        [
            owned_database_source(101, "ALPHA", "ALPHA surface is 432 sq. in."),
            owned_database_source(202, "BETA", "BETA surface is 432 sq. in."),
            owned_database_source(303, "GAMMA", "GAMMA surface is 432 sq. in."),
        ],
    )

    assert result.grounding_status == SUPPORTED
    group = result.support_results[0]["claim_elements"][0]
    assert group["product_owners"] == ["alpha", "beta", "gamma"]
    assert len(group["owner_premises"]) == 3
    assert len(group["supporting_citation_ids"]) == 3


def test_owner_group_with_one_missing_scalar_is_partial() -> None:
    result = validate_answer_citations(
        "ALPHA and BETA are both 432 square inches. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(101, "ALPHA", "ALPHA is 432 square inches."),
            owned_database_source(202, "BETA", "BETA is 500 square inches."),
        ],
    )

    assert result.grounding_status == PARTIALLY_SUPPORTED
    premises = result.support_results[0]["claim_elements"][0]["owner_premises"]
    assert [premise["status"] for premise in premises] == [
        SUPPORTED,
        UNSUPPORTED,
    ]


def test_owner_group_with_one_missing_citation_is_partial() -> None:
    result = validate_answer_citations(
        "ALPHA and BETA are both 432 square inches. "
        "[source: Flamy Product Read Model, product ID 101]",
        [
            owned_database_source(101, "ALPHA", "ALPHA is 432 square inches."),
            owned_database_source(202, "BETA", "BETA is 432 square inches."),
        ],
    )

    assert result.status == PASS
    assert result.grounding_status == PARTIALLY_SUPPORTED


def test_owner_group_does_not_borrow_same_scalar_from_wrong_owner() -> None:
    result = validate_answer_citations(
        "ALPHA and BETA are both 432 square inches. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(
                101,
                "ALPHA",
                "ALPHA repeats 432 square inches twice: 432 square inches.",
            ),
            owned_database_source(202, "BETA", "BETA is 500 square inches."),
        ],
    )

    assert result.grounding_status == PARTIALLY_SUPPORTED
    beta_premise = result.support_results[0]["claim_elements"][0][
        "owner_premises"
    ][1]
    assert beta_premise["status"] == UNSUPPORTED
    assert beta_premise["supporting_citation_ids"] == []


def test_disjunction_does_not_create_owner_group_fact() -> None:
    result = validate_answer_citations(
        "ALPHA or BETA has a 432 square inch cooking surface. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(101, "ALPHA", "ALPHA surface is 432 sq. in."),
            owned_database_source(202, "BETA", "BETA surface is 432 sq. in."),
        ],
    )

    assert result.grounding_status != SUPPORTED
    elements = result.support_results[0]["claim_elements"]
    assert all(element["element_type"] != "owner_group_fact" for element in elements)


@pytest.mark.parametrize(
    "claim",
    (
        "ALPHA and BETA are compared with a 432 square inch panel.",
        "ALPHA is 432 square inches, unlike BETA.",
        "ALPHA and BETA were reviewed, and the panel is 432 square inches.",
    ),
)
def test_unclear_multi_owner_mentions_do_not_propagate_value(claim: str) -> None:
    result = validate_answer_citations(
        f"{claim} [source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(101, "ALPHA", "ALPHA panel is 432 sq. in."),
            owned_database_source(202, "BETA", "BETA panel is 432 sq. in."),
        ],
    )

    assert result.grounding_status != SUPPORTED
    elements = result.support_results[0]["claim_elements"]
    assert all(element["element_type"] != "owner_group_fact" for element in elements)


def test_separate_owner_values_remain_individually_bound() -> None:
    result = validate_answer_citations(
        "ALPHA has 432 square inches and BETA has 500 square inches. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(101, "ALPHA", "ALPHA has 432 square inches."),
            owned_database_source(202, "BETA", "BETA has 500 square inches."),
        ],
    )

    assert result.grounding_status == SUPPORTED
    factual = [
        element
        for element in result.support_results[0]["claim_elements"]
        if element["element_type"] == "factual_value"
    ]
    assert [element["product_owner"] for element in factual] == ["alpha", "beta"]
    assert [element["required_numbers"] for element in factual] == [["432"], ["500"]]


def test_respectively_pairs_values_without_owner_group_propagation() -> None:
    result = validate_answer_citations(
        "The cooking surface values for ALPHA and BETA are 432 and 500 "
        "square inches, respectively. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(
                101,
                "ALPHA",
                "ALPHA cooking surface value is 432 square inches.",
            ),
            owned_database_source(
                202,
                "BETA",
                "BETA cooking surface value is 500 square inches.",
            ),
        ],
    )

    assert result.grounding_status == SUPPORTED
    factual = [
        element
        for element in result.support_results[0]["claim_elements"]
        if element["element_type"] == "factual_value"
    ]
    assert [element["product_owner"] for element in factual] == ["alpha", "beta"]
    assert all(
        element["element_type"] != "owner_group_fact"
        for element in result.support_results[0]["claim_elements"]
    )


def test_nonshared_wider_than_claim_does_not_propagate_one_value() -> None:
    result = validate_answer_citations(
        "ALPHA is 18 inches wider than BETA. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(101, "ALPHA", "ALPHA width is 18 inches."),
            owned_database_source(202, "BETA", "BETA width is 12 inches."),
        ],
    )

    assert result.grounding_status != SUPPORTED
    elements = result.support_results[0]["claim_elements"]
    assert all(element["element_type"] != "owner_group_fact" for element in elements)


def test_irrelevant_third_citation_still_prevents_full_group_support() -> None:
    result = validate_answer_citations(
        "ALPHA and BETA are both 432 square inches. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202] "
        "[source: Flamy Product Read Model, product ID 303]",
        [
            owned_database_source(101, "ALPHA", "ALPHA is 432 square inches."),
            owned_database_source(202, "BETA", "BETA is 432 square inches."),
            owned_database_source(303, "GAMMA", "GAMMA weighs 75 pounds."),
        ],
    )

    assert result.grounding_status == PARTIALLY_SUPPORTED
    assert result.support_results[2]["decision_rule"] == "IRRELEVANT_CITATION"


def test_owner_group_keeps_square_inch_abbreviation_intact() -> None:
    result = validate_answer_citations(
        "ALPHA and BETA are both 432 sq. in. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]",
        [
            owned_database_source(101, "ALPHA", "ALPHA is 432 square inches."),
            owned_database_source(202, "BETA", "BETA is 432 square inches."),
        ],
    )

    assert result.grounding_status == SUPPORTED
    group = result.support_results[0]["claim_elements"][0]
    assert group["required_numbers"] == ["432"]
    assert group["required_units"] == ["squareinch"]


def _comparison_sources(
    alpha_value: int = 432,
    beta_value: int = 432,
) -> list[dict[str, object]]:
    return [
        owned_database_source(
            101,
            "ALPHA",
            f"ALPHA cooking surface is {alpha_value} square inches.",
        ),
        owned_database_source(
            202,
            "BETA",
            f"BETA cooking surface is {beta_value} square inches.",
        ),
    ]


def _two_database_citations() -> str:
    return (
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 202]"
    )


def test_equal_canonical_owner_scalars_support_same_relation() -> None:
    result = validate_answer_citations(
        "ALPHA and BETA have the same cooking-surface area. "
        + _two_database_citations(),
        _comparison_sources(),
    )

    assert result.grounding_status == SUPPORTED
    relation = result.support_results[0]["claim_elements"][-1]
    assert relation["element_type"] == "comparative_relation"
    assert relation["status"] == SUPPORTED
    assert [
        premise["required_numbers"]
        for premise in relation["canonical_premises"]
    ] == [["432"], ["432"]]


def test_equal_canonical_owner_scalars_support_neither_larger_relation() -> None:
    result = validate_answer_citations(
        "Neither ALPHA nor BETA has a larger cooking-surface area. "
        + _two_database_citations(),
        _comparison_sources(),
    )

    assert result.grounding_status == SUPPORTED
    assert all(item["status"] == SUPPORTED for item in result.support_results)


def test_equal_owner_scalars_reject_positive_larger_relation() -> None:
    result = validate_answer_citations(
        "ALPHA has a larger cooking-surface area than BETA. "
        + _two_database_citations(),
        _comparison_sources(),
    )

    assert result.grounding_status != SUPPORTED


def test_greater_canonical_owner_scalar_supports_larger_relation() -> None:
    result = validate_answer_citations(
        "BETA has the larger cooking-surface area. "
        + _two_database_citations(),
        _comparison_sources(beta_value=500),
    )

    assert result.grounding_status == SUPPORTED
    assert all(item["status"] == SUPPORTED for item in result.support_results)


def test_canonical_owner_scalars_support_numeric_difference() -> None:
    result = validate_answer_citations(
        "ALPHA has a 432 sq. in. cooking surface and BETA has a 500 sq. in. "
        "cooking surface, so BETA is 68 sq. in. larger. "
        + _two_database_citations(),
        _comparison_sources(beta_value=500),
    )

    assert result.grounding_status == SUPPORTED
    derived = [
        element
        for element in result.support_results[0]["claim_elements"]
        if element["element_type"] == "derived_comparison"
        and element["required_numbers"] == ["68"]
    ]
    assert len(derived) == 1
    assert derived[0]["required_numbers"] == ["68"]
    assert len(derived[0]["supporting_citation_ids"]) == 2


def test_equal_values_for_different_attributes_do_not_support_equality() -> None:
    result = validate_answer_citations(
        "ALPHA and BETA have the same cooking-surface area. "
        + _two_database_citations(),
        [
            owned_database_source(
                101,
                "ALPHA",
                "ALPHA cooking surface is 432 square inches.",
            ),
            owned_database_source(
                202,
                "BETA",
                "BETA total cooking area is 432 square inches.",
            ),
        ],
    )

    assert result.grounding_status != SUPPORTED


def test_wrong_product_citation_does_not_support_comparison() -> None:
    sources = [
        *_comparison_sources(),
        owned_database_source(
            303,
            "GAMMA",
            "GAMMA cooking surface is 432 square inches.",
        ),
    ]
    result = validate_answer_citations(
        "ALPHA and BETA have the same cooking-surface area. "
        "[source: Flamy Product Read Model, product ID 101] "
        "[source: Flamy Product Read Model, product ID 303]",
        sources,
    )

    assert result.grounding_status != SUPPORTED


def test_missing_owner_evidence_does_not_fully_support_comparison() -> None:
    result = validate_answer_citations(
        "ALPHA and BETA have the same cooking-surface area. "
        "[source: Flamy Product Read Model, product ID 101]",
        _comparison_sources(),
    )

    assert result.grounding_status != SUPPORTED


@pytest.mark.parametrize(
    "claim",
    (
        "ALPHA and BETA have the same total cooking area.",
        "ALPHA and BETA have the same overall size.",
    ),
)
def test_equal_primary_surface_does_not_imply_other_attribute_equality(
    claim: str,
) -> None:
    result = validate_answer_citations(
        f"{claim} {_two_database_citations()}",
        _comparison_sources(),
    )

    assert result.grounding_status != SUPPORTED


def test_stage2_supported_wording_remains_supported() -> None:
    result = validate_answer_citations(
        "The listed Cooking Surface is the same for both models: "
        "24NGL-00SP and 24NGT are each listed at 432 sq. in. "
        "[source: Flamy Product Read Model, product ID 63] "
        "[source: Flamy Product Read Model, product ID 57]",
        [
            owned_database_source(
                63,
                "24NGL-00SP",
                "24NGL-00SP Cooking Surface is 432 sq. in.",
            ),
            owned_database_source(
                57,
                "24NGT",
                "24NGT Cooking Surface is 432 sq. inches.",
            ),
        ],
    )

    assert result.grounding_status == SUPPORTED


def test_exact_stage3_artifact_neither_larger_becomes_supported() -> None:
    result = validate_answer_citations(
        "Neither has the larger listed **Cooking Surface**: "
        "**24NGL-00SP** is listed at **432 sq. in.**, and **24NGT** is "
        "listed at **432 sq. inches (24\" x 18\")**. "
        "[source: Flamy Product Read Model, product ID 63] "
        "[source: Flamy Product Read Model, product ID 57]",
        [
            owned_database_source(
                63,
                "24NGL-00SP",
                "24NGL-00SP Cooking Surface is 432 sq. in.",
            ),
            owned_database_source(
                57,
                "24NGT",
                '24NGT Cooking Surface is 432 sq. inches (24" x 18").',
            ),
        ],
    )

    assert result.status == PASS
    assert result.grounding_status == SUPPORTED
    relation = result.support_results[0]["claim_elements"][-1]
    assert relation["element_type"] == "comparative_relation"
    assert relation["status"] == SUPPORTED
    assert len(relation["supporting_citation_ids"]) == 2
