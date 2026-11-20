from src.document_applicability import (
    assess_document_applicability,
    chunk_applicability_diagnostics,
)
from src.corpus_neighbors import CorpusNeighborIndex
from src.information_needs import classify_information_needs
from src.models import Chunk
from src.product_applicability import ProductApplicabilityContext


TECHNICAL_NEEDS = classify_information_needs("How do I install this product?")


def context(**overrides) -> ProductApplicabilityContext:
    values = {
        "read_model_product_id": 100,
        "brand": "American Outdoor Grill",
        "model": "AOG24-GA",
        "mpn": "AOG24-GA",
        "product_type": "post base",
    }
    values.update(overrides)
    return ProductApplicabilityContext(**values)


def manual(**overrides) -> Chunk:
    values = {
        "chunk_id": "exact",
        "document_id": "aog24",
        "filename": "AOG24.pdf",
        "relative_path": "manuals/AOG24.pdf",
        "page_start": 1,
        "page_end": 1,
        "text": "AOG24-GA installation instructions.",
        "brand": "American Outdoor Grill",
        "model_numbers": ("AOG24-GA",),
        "technical_tokens_normalized": ("AOG24GA",),
        "metadata_source": "manifest",
        "metadata_confidence": "approved",
    }
    values.update(overrides)
    return Chunk(**values)


def test_aog_alias_normalizes_without_blocking_exact_identity() -> None:
    result = assess_document_applicability(
        manual(brand="AOG"),
        context(),
        TECHNICAL_NEEDS,
    )

    assert result.brand_match is True
    assert result.conflict_class == "ALIAS_NORMALIZATION_WARNING"
    assert "BRAND_ALIAS_NORMALIZED" in result.diagnostic_reason_codes
    assert {"model", "mpn", "brand"} <= set(result.matched_fields)
    assert result.conflicting_fields == ()
    assert result.applicable is True


def test_firemagic_alias_normalizes_to_fire_magic() -> None:
    result = assess_document_applicability(
        manual(
            brand="FireMagic",
            model_numbers=("A430S-8",),
            technical_tokens_normalized=("A430S8",),
            text="A430S-8 installation instructions.",
        ),
        context(
            brand="Fire Magic",
            model="A430S-8",
            mpn="A430S-8",
            product_type="grill",
        ),
        TECHNICAL_NEEDS,
    )

    assert result.brand_match is True
    assert result.conflict_class == "ALIAS_NORMALIZATION_WARNING"


def test_true_cross_brand_mismatch_blocks_even_with_exact_model_and_mpn() -> None:
    result = assess_document_applicability(
        manual(brand="Fire Magic"),
        context(),
        TECHNICAL_NEEDS,
    )

    assert {"model", "mpn"} <= set(result.matched_fields)
    assert result.conflict_class == "HARD_CONFLICT"
    assert result.conflicting_fields == ("brand",)
    assert "WRONG_BRAND" in result.exclusion_reasons
    assert result.applicable is False


def test_missing_brand_remains_visible_but_exact_identity_is_applicable() -> None:
    result = assess_document_applicability(
        manual(brand=None),
        context(),
        TECHNICAL_NEEDS,
    )

    assert result.conflict_class == "MISSING_METADATA"
    assert result.missing_fields == ("brand",)
    assert "BRAND_METADATA_MISSING" in result.diagnostic_reason_codes
    assert result.applicable is True


def test_series_mismatch_is_soft_when_exact_identity_agrees() -> None:
    result = assess_document_applicability(
        manual(series="Echelon"),
        context(series="Aurora"),
        TECHNICAL_NEEDS,
    )

    assert result.conflict_class == "SOFT_METADATA_CONFLICT"
    assert result.conflicting_fields == ("series",)
    assert result.applicable is True


def test_year_mismatch_is_diagnostic_only() -> None:
    result = assess_document_applicability(
        manual(year="2020"),
        context(production_start_year=2025, production_end_year=2026),
        TECHNICAL_NEEDS,
    )

    assert result.conflict_class == "SOFT_METADATA_CONFLICT"
    assert "YEAR_METADATA_MISMATCH_OBSERVED" in (
        result.diagnostic_reason_codes
    )
    assert result.exclusion_reasons == ()
    assert result.applicable is True


def test_unproven_variant_mismatch_is_observed_without_rejection() -> None:
    result = assess_document_applicability(
        manual(text="Variant: right-hand\nAOG24-GA installation instructions."),
        context(variant="left-hand"),
        TECHNICAL_NEEDS,
    )

    assert result.conflict_class == "SOFT_METADATA_CONFLICT"
    assert "WRONG_PRODUCT_VARIANT" not in result.exclusion_reasons
    assert result.applicable is True
    assert result.configuration_applicability is not None
    assert result.configuration_applicability["mode"] == "observe"
    assert result.configuration_applicability["actual_admission_changed"] is False


def test_explicit_document_exclusion_blocks_exact_identity() -> None:
    result = assess_document_applicability(
        manual(text="AOG24-GA is not covered by this installation document."),
        context(),
        TECHNICAL_NEEDS,
    )

    assert result.conflict_class == "HARD_CONFLICT"
    assert "EXPLICIT_PRODUCT_EXCLUSION" in result.exclusion_reasons
    assert result.applicable is False


def test_inferred_path_mismatch_is_soft_when_exact_identity_agrees() -> None:
    chunk = manual(
        brand="l_series",
        manufacturer="grills",
        series="24",
        product="builtin",
        metadata_source="path",
        metadata_confidence="inferred",
    )
    result = assess_document_applicability(chunk, context(), TECHNICAL_NEEDS)
    diagnostics = chunk_applicability_diagnostics(chunk, context(), result)

    assert result.conflict_class == "SOFT_METADATA_CONFLICT"
    assert "INFERRED_PATH_BRAND_MISMATCH" in result.diagnostic_reason_codes
    assert "INFERRED_PATH_PRODUCT_TYPE_MISMATCH" in (
        result.diagnostic_reason_codes
    )
    assert result.exclusion_reasons == ()
    assert result.applicable is True
    assert diagnostics["raw_values"]["brand"] == {
        "expected": "American Outdoor Grill",
        "actual": "l_series",
    }
    assert diagnostics["normalized_values"]["brand"] == {
        "expected": "AMERICANOUTDOORGRILL",
        "actual": "LSERIES",
    }


def test_inferred_path_metadata_cannot_establish_applicability_alone() -> None:
    result = assess_document_applicability(
        manual(
            text="General installation information.",
            brand="l_series",
            product="builtin",
            model_numbers=(),
            technical_tokens_normalized=(),
            metadata_source="path",
            metadata_confidence="inferred",
        ),
        context(),
        TECHNICAL_NEEDS,
    )

    assert result.classification == "UNPROVEN"
    assert result.applicable is False


def test_explicit_query_scope_can_establish_document_applicability() -> None:
    result = assess_document_applicability(
        manual(
            document_id="annual-document",
            filename="catalog.pdf",
            relative_path="documents/2016/catalog/catalog.pdf",
            year="2016",
            text="AOG outdoor cooking products and available configurations.",
            brand=None,
            model_numbers=(),
            technical_tokens_normalized=(),
        ),
        None,
        TECHNICAL_NEEDS,
        query_text="What AOG grill models are listed in the 2016 catalog?",
    )

    assert result.classification == "QUERY_SCOPED"
    assert result.eligibility == "APPLICABLE"
    assert result.applicable is True
    assert result.year_overlap is True
    assert result.document_type_match is True
    assert result.diagnostic_reason_codes == (
        "QUERY_YEAR_MATCH",
        "QUERY_DOCUMENT_TYPE_MATCH",
        "QUERY_LEXICAL_SCOPE_MATCH",
    )


def test_query_scope_observes_a_different_document_year_without_rejecting() -> None:
    result = assess_document_applicability(
        manual(
            document_id="unrelated-document",
            filename="catalog.pdf",
            relative_path="documents/2017/catalog/catalog.pdf",
            year="2017",
            text="AOG outdoor cooking products.",
            brand=None,
            model_numbers=(),
            technical_tokens_normalized=(),
        ),
        None,
        TECHNICAL_NEEDS,
        query_text="What AOG grill models are listed in the 2016 catalog?",
    )

    assert result.classification == "QUERY_SCOPED"
    assert result.applicable is True
    assert "YEAR_PATH_MISMATCH_OBSERVED" in (
        result.diagnostic_reason_codes
    )


def test_query_scope_requires_lexical_subject_overlap() -> None:
    result = assess_document_applicability(
        manual(
            document_id="unrelated-document",
            filename="catalog.pdf",
            relative_path="documents/2016/catalog/catalog.pdf",
            year="2016",
            text="Unrelated equipment documentation.",
            brand=None,
            model_numbers=(),
            technical_tokens_normalized=(),
        ),
        None,
        TECHNICAL_NEEDS,
        query_text="What AOG grill models are listed in the 2016 catalog?",
    )

    assert result.classification == "UNPROVEN"
    assert result.applicable is False
    assert result.diagnostic_reason_codes == ("NO_PRODUCT_CONTEXT",)


def test_document_level_models_apply_to_later_technical_chunks() -> None:
    cover = manual(
        chunk_id="cover",
        document_id="shared-document",
        page_start=1,
        page_end=1,
        text=(
            "INSTALLATION, USE AND CARE MANUAL\n"
            "MODELS:\n"
            "UNIT30G-C\n"
            "UNIT36G-C\n"
            "P/N: 10000A"
        ),
        brand=None,
        model_numbers=("UNIT30G-C", "UNIT36G-C", "10000A"),
        technical_tokens_normalized=(
            "UNIT30GC",
            "UNIT36GC",
            "10000A",
        ),
        metadata_source="path",
        metadata_confidence="inferred",
    )
    technical = manual(
        chunk_id="technical",
        document_id="shared-document",
        page_start=30,
        page_end=30,
        text=(
            "TROUBLESHOOTING GUIDE\n"
            "Verify 120V power and then see Pg 22."
        ),
        brand=None,
        model_numbers=("120V", "Pg 22"),
        technical_tokens_normalized=("120V", "PG22"),
        metadata_source="path",
        metadata_confidence="inferred",
    )
    index = CorpusNeighborIndex((cover, technical))
    enriched = index.with_document_identity(technical)

    result = assess_document_applicability(
        enriched,
        context(
            brand=None,
            model="UNIT30",
            mpn="UNIT30G-CN",
            product_type=None,
        ),
        classify_information_needs("Why will it not start?"),
    )

    assert enriched.document_model_numbers == (
        "UNIT30G-C",
        "UNIT36G-C",
    )
    assert result.exact_model_match is True
    assert "EXACT_PRODUCT_IDENTIFIER_CONFLICT" not in (
        result.diagnostic_reason_codes
    )
    assert result.classification == "DIRECT"
    assert result.applicable is True


def test_inferred_chunk_tokens_are_not_authoritative_model_conflicts() -> None:
    result = assess_document_applicability(
        manual(
            text="Verify 120V power and then see Pg 22.",
            brand=None,
            model_numbers=("120V", "Pg 22"),
            technical_tokens_normalized=("120V", "PG22"),
            metadata_source="path",
            metadata_confidence="inferred",
        ),
        context(
            brand=None,
            model="UNIT30",
            mpn="UNIT30G-CN",
            product_type=None,
        ),
        classify_information_needs("Why will it not start?"),
    )

    assert "EXACT_PRODUCT_IDENTIFIER_CONFLICT" not in (
        result.diagnostic_reason_codes
    )
    assert "WRONG_EXACT_PRODUCT" not in result.exclusion_reasons


def test_authoritative_document_models_can_still_reject_wrong_product() -> None:
    result = assess_document_applicability(
        manual(
            text="Troubleshooting instructions.",
            brand=None,
            model_numbers=("120V",),
            document_model_numbers=("OTHER100",),
            technical_tokens_normalized=("120V",),
            metadata_source="path",
            metadata_confidence="inferred",
        ),
        context(
            brand=None,
            model="UNIT30",
            mpn="UNIT30G-CN",
            product_type=None,
        ),
        classify_information_needs("Why will it not start?"),
    )

    assert result.classification == "CONFLICTING"
    assert "EXACT_PRODUCT_IDENTIFIER_CONFLICT" in (
        result.diagnostic_reason_codes
    )
    assert "WRONG_EXACT_PRODUCT" in result.exclusion_reasons


def test_specific_technical_topic_outranks_generic_step_metadata() -> None:
    product = context(
        brand=None,
        model="UNIT30",
        mpn="UNIT30-A",
        product_type=None,
    )
    query = (
        "What troubleshooting steps apply if UNIT30-A "
        "will not start?"
    )
    needs = classify_information_needs(query)
    generic = assess_document_applicability(
        manual(
            text="General installation instructions.",
            brand=None,
            document_model_numbers=("UNIT30-A",),
            content_type="installation_step",
            chunk_kind="installation_steps",
            metadata_source="path",
            metadata_confidence="inferred",
        ),
        product,
        needs,
        query_text=query,
    )
    specific = assess_document_applicability(
        manual(
            text="Troubleshooting instructions.",
            brand=None,
            document_model_numbers=("UNIT30-A",),
            content_type="troubleshooting",
            chunk_kind="narrative",
            section_title="TROUBLESHOOTING GUIDE",
            metadata_source="path",
            metadata_confidence="inferred",
        ),
        product,
        needs,
        query_text=query,
    )

    assert "TECHNICAL_TOPIC_MATCH" in generic.diagnostic_reason_codes
    assert "TECHNICAL_TOPIC_MATCH" in specific.diagnostic_reason_codes
    assert specific.applicability_score > generic.applicability_score
