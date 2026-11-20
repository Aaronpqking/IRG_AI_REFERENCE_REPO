from pathlib import Path

from src.models import Chunk
from src.retrieval_policy import (
    infer_document_type,
    path_quality_score,
    year_score,
)
from src.technical_text import extract_query_terms, extract_query_tokens


def chunk(**overrides: object) -> Chunk:
    values: dict[str, object] = {
        "chunk_id": "chunk-1",
        "filename": "manual.pdf",
        "relative_path": "brand/family/model-x/2021/om/manual.pdf",
        "page_start": 1,
        "page_end": 1,
        "text": "Model-X installation details.",
        "year": "2021",
    }
    values.update(overrides)
    return Chunk(**values)


def test_exact_year_strongly_prefers_exact_year_over_newer_wrong_year() -> None:
    exact = chunk(year="2016", relative_path="brand/model-x/2016/om/manual.pdf")
    newer = chunk(year="2023", relative_path="brand/model-x/2023/om/manual.pdf")

    assert year_score(exact, query_year=2016, strong_match=True) > 0
    assert year_score(newer, query_year=2016, strong_match=True) < 0
    assert (
        year_score(exact, query_year=2016, strong_match=True)
        - year_score(newer, query_year=2016, strong_match=True)
    ) >= 10


def test_latest_prefers_newer_only_when_scope_matches() -> None:
    query = "What does the latest catalog say for MX-100?"
    terms = extract_query_terms(query)
    tokens = extract_query_tokens(query)
    scoped_newer = chunk(
        chunk_id="newer",
        filename="catalog.pdf",
        relative_path="brand/mx-100/2025/catalog/catalog.pdf",
        text="MX-100 catalog listing.",
        year="2025",
    )
    unscoped_newer = chunk(
        chunk_id="generic",
        filename="catalog.pdf",
        relative_path="brand/general/2026/catalog/catalog.pdf",
        text="General catalog listing.",
        year="2026",
    )

    assert path_quality_score(scoped_newer, tokens, True, terms, None) > (
        path_quality_score(unscoped_newer, tokens, True, terms, None)
        + year_score(unscoped_newer, None, strong_match=False, prefer_latest=True)
    )


def test_no_year_does_not_let_generic_newer_catalog_beat_exact_manual() -> None:
    query = "Which replacement part is listed for MX-100?"
    terms = extract_query_terms(query)
    tokens = extract_query_tokens(query)
    manual = chunk(
        filename="manual.pdf",
        relative_path="brand/mx-100/2021/om/manual.pdf",
        text="MX-100 replacement part list.",
        year="2021",
    )
    catalog = chunk(
        filename="catalog.pdf",
        relative_path="brand/general/2026/catalog/catalog.pdf",
        text="General replacement part list.",
        year="2026",
    )

    manual_score = path_quality_score(manual, tokens, False, terms, None) + year_score(
        manual, None, strong_match=True
    )
    catalog_score = path_quality_score(catalog, tokens, False, terms, None) + year_score(
        catalog, None, strong_match=False
    )

    assert manual_score > catalog_score


def test_document_type_preference_uses_generic_intent_terms() -> None:
    query = "What installation warning applies to MX-100?"
    terms = extract_query_terms(query)
    tokens = extract_query_tokens(query)
    owner_manual = chunk(
        relative_path="brand/mx-100/2021/om/manual.pdf",
        text="MX-100 installation warning.",
    )
    catalog = chunk(
        filename="catalog.pdf",
        relative_path="brand/mx-100/2021/catalog/catalog.pdf",
        text="MX-100 catalog listing.",
    )
    quick_start = chunk(
        filename="qsg.pdf",
        relative_path="brand/mx-100/2021/qsg/qsg.pdf",
        text="MX-100 quick start.",
    )

    assert infer_document_type(owner_manual) == "owner_manual"
    assert path_quality_score(owner_manual, tokens, False, terms, None) > path_quality_score(
        catalog, tokens, False, terms, None
    )
    assert path_quality_score(owner_manual, tokens, False, terms, None) > path_quality_score(
        quick_start, tokens, False, terms, None
    )


def test_governed_path_type_precedes_chunk_content_heuristics() -> None:
    dimensional_manual = chunk(
        relative_path="brand/model/2024/om/manual.pdf",
        text="Dimensions and specifications: width 24 inches.",
        content_type="spec_table",
        has_dimensions=True,
    )
    specification = chunk(
        relative_path="brand/model/2024/spec/model.pdf",
        text="Installation notes are included for reference.",
    )

    assert infer_document_type(dimensional_manual) == "owner_manual"
    assert infer_document_type(specification) == "specification"


def test_catalog_current_question_prefers_catalog_when_scope_matches() -> None:
    query = "What does the current catalog list for MX-100?"
    terms = extract_query_terms(query)
    tokens = extract_query_tokens(query)
    catalog = chunk(
        filename="catalog.pdf",
        relative_path="brand/mx-100/2024/catalog/catalog.pdf",
        text="MX-100 current listing.",
    )
    manual = chunk(
        relative_path="brand/mx-100/2024/om/manual.pdf",
        text="MX-100 owner manual.",
    )

    assert path_quality_score(catalog, tokens, True, terms, None) > path_quality_score(
        manual, tokens, True, terms, None
    )


def test_cover_fitment_prefers_catalog_over_cad_like_specification() -> None:
    query = "What cover fits a 30 inch built-in grill?"
    terms = extract_query_terms(query)
    tokens = extract_query_tokens(query)
    catalog = chunk(
        filename="catalog.pdf",
        relative_path="brand/accessories/2024/catalog/catalog.pdf",
        text="30 inch cover for built-in grill.",
    )
    cad = chunk(
        filename="30bi.pdf",
        relative_path="brand/grills/30/built-in/2024/cad/30bi.pdf",
        text="30 inch built-in grill dimensions.",
        content_type="spec_table",
    )

    assert path_quality_score(catalog, tokens, False, terms, None) > path_quality_score(
        cad, tokens, False, terms, None
    )


def test_cutout_dimension_prefers_scoped_manual_over_broad_spec_by_default() -> None:
    query = "What is the cutout dimension for a 24 inch built-in grill?"
    terms = extract_query_terms(query)
    tokens = extract_query_tokens(query)
    manual = chunk(
        relative_path="brand/grills/24/built-in/2024/om/manual.pdf",
        text="Table 1 cutout dimensions 24 inch built-in grill.",
    )
    broad_spec = chunk(
        filename="spec_guide.pdf",
        relative_path="brand/misc/2018/spec_guide/spec_guide.pdf",
        text="Generic cutout dimension guide.",
        content_type="spec_table",
    )

    assert path_quality_score(manual, tokens, False, terms, None) > path_quality_score(
        broad_spec, tokens, False, terms, None
    )


def test_scope_terms_promote_matching_source_over_conflicting_source() -> None:
    query = "What installation warning applies to alpha line 30 built-in MX-100?"
    terms = extract_query_terms(query)
    tokens = extract_query_tokens(query)
    matching = chunk(
        relative_path="brand/alpha-line/30/built-in/mx-100/2022/om/manual.pdf",
        text="MX-100 installation warning.",
    )
    conflicting = chunk(
        relative_path="brand/beta-line/42/free-standing/mx-100/2022/om/manual.pdf",
        text="MX-100 installation warning.",
    )

    assert path_quality_score(matching, tokens, False, terms, None) > path_quality_score(
        conflicting, tokens, False, terms, None
    )


def test_production_policy_modules_do_not_contain_smoke_specific_constants() -> None:
    banned = (
        "american outdoor grill",
        "aog",
        "gr18a",
        "l-series",
        "t-series",
        "gq-0",
        "technical_pdf_chunks_v1_smoke/",
    )
    modules = (
        "src/retrieval.py",
        "src/retrieval_policy.py",
        "src/query_intent.py",
        "src/evidence_context.py",
        "src/golden_policy.py",
    )
    hits: list[str] = []
    for module in modules:
        text = Path(module).read_text(encoding="utf-8").casefold()
        for item in banned:
            if item in text:
                hits.append(f"{module}: {item}")

    assert hits == []
