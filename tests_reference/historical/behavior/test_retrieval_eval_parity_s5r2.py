import json
from pathlib import Path

import pytest

from src.golden_policy import accepted_source_match, answer_term_status, page_matches, source_matches
from src.hybrid_retrieval import (
    HybridRetrievalConfig,
    LocalChunkLexicalRetriever,
    RetrievalChannelCandidate,
    build_hybrid_request,
    extract_product_scope_terms,
    fuse_candidates,
    hybrid_config_from_values,
)
from src.models import Chunk
from src.product_discovery import build_retrieval_query
from src.source_identity import canonical_corpus_path, sources_match


def chunk(chunk_id="chunk-1", **overrides):
    values = {
        "chunk_id": chunk_id,
        "document_id": f"doc-{chunk_id}",
        "filename": "l_series.pdf",
        "relative_path": "grills/l_series/24/builtin/2024/om/l_series.pdf",
        "page_start": 25,
        "page_end": 25,
        "chunk_index": 0,
        "text": "Stainless cooking grid and cutout dimensions for built-in grill.",
        "technical_tokens_normalized": ("24B11A",),
        "model_numbers": (),
        "part_numbers": ("24-B-11A",),
        "section_title": "Replacement Parts",
    }
    values.update(overrides)
    return Chunk(**values)


def test_exact_canonical_source_identity():
    assert canonical_corpus_path("grills/l_series/24/builtin/2024/om/l_series.pdf") == "grills/l_series/24/builtin/2024/om/l_series.pdf"
    assert sources_match(
        "grills/l_series/24/builtin/2024/om/l_series.pdf",
        "grills/l_series/24/builtin/2024/om/l_series.pdf",
    ).matched


@pytest.mark.skipif(
    not Path("data/approved_pdfs.jsonl").exists(),
    reason="local approved-source registry artifact is not present",
)
def test_canonical_path_is_authoritative_and_legacy_path_is_superseded():
    canonical = "american_outdoor_grill/grills/l_series/24/builtin/2024/om/l_series.pdf"
    legacy = "grills/l_series/24/builtin/2024/om/l_series.pdf"
    canonicalization = [
        json.loads(line)
        for line in Path(
            "reports/V2_S2B_BRAND_ROOT_CANONICALIZATION.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert any(
        row.get("old_relative_path") == legacy
        and row.get("new_relative_path") == canonical
        for row in canonicalization
    )
    assert sources_match(canonical, canonical).method == "canonical_path"
    assert not sources_match(canonical, legacy).matched


def test_arbitrary_suffix_rejected():
    assert not sources_match(
        "other_root/grills/l_series/24/builtin/2024/om/l_series.pdf",
        "grills/l_series/24/builtin/2024/om/l_series.pdf",
    ).matched


def test_basename_only_match_rejected():
    assert not sources_match(
        "accessories/vent_hoods/vhd-36/2024/om/vhd-36.pdf",
        "other/path/vhd-36.pdf",
    ).matched


@pytest.mark.skipif(
    not Path("data/approved_pdfs.jsonl").exists(),
    reason="local approved-source registry artifact is not present",
)
def test_accepted_source_parity_uses_canonical_path_only():
    question = {
        "expected_source": "not/the/source.pdf",
        "accepted_sources": [
            {
                "source": "american_outdoor_grill/grills/l_series/24/builtin/2024/om/l_series.pdf",
                "acceptance_note": "same canonical corpus document",
            }
        ],
    }

    canonical = "american_outdoor_grill/grills/l_series/24/builtin/2024/om/l_series.pdf"
    legacy = "grills/l_series/24/builtin/2024/om/l_series.pdf"
    matched, note = accepted_source_match(question, canonical)

    assert matched
    assert note == "same canonical corpus document"
    assert accepted_source_match(question, legacy) == (False, None)


def test_accepted_page_parity():
    question = {"expected_page": 1, "accepted_pages": [7]}
    ranked = type("Ranked", (), {"chunk": chunk(page_start=7, page_end=7)})()

    assert page_matches(question, ranked)


def test_metric_layer_separation_keys_are_present():
    report = json.loads(Path("reports/evaluation_runs/MS6-S5R1-HYBRID-EVAL/hybrid_retrieval_eval_latest.json").read_text(encoding="utf-8"))

    assert "hybrid_expected_document_recall_by_k" in report["metrics"]
    assert "hybrid_expected_page_chunk_recall_by_k" in report["metrics"]
    assert "hybrid_expected_evidence_recall_at_top_k" in report["metrics"]


def test_lexical_index_builds_once():
    retriever = LocalChunkLexicalRetriever((chunk("a"), chunk("b")))

    first_index = retriever.index
    retriever.lexical_candidates(
        build_hybrid_request(
            build_retrieval_query(
                "What cooking grids fit a 24 inch built-in grill?"
            )
        )
    )

    assert retriever.index is first_index
    assert retriever.index.build_duration_ms >= 0


def test_lexical_query_uses_bounded_postings():
    retriever = LocalChunkLexicalRetriever(tuple(chunk(f"c{i}") for i in range(50)), lexical_candidate_limit=7)

    result = retriever.lexical_candidates(
        build_hybrid_request(
            build_retrieval_query(
                "What cooking grids fit a 24 inch built-in grill?"
            )
        )
    )

    assert len(result) <= 7
    assert len(result) < len(retriever.chunks)


def test_exact_identifier_postings():
    retriever = LocalChunkLexicalRetriever((chunk("part"),))

    assert "24B11A" in retriever.index.exact_identifier_postings
    request = build_hybrid_request(
        build_retrieval_query("What is 24-B-11A?")
    )
    assert retriever.exact_identifier_candidates(request)[0].chunk.chunk_id == "part"


def test_phrase_postings_and_match_class():
    retriever = LocalChunkLexicalRetriever((chunk("phrase", text="The cooking grids are stainless steel."),))

    result = retriever.lexical_candidates(
        build_hybrid_request(
            build_retrieval_query("What cooking grids fit?")
        )
    )

    assert "EXACT_PHRASE" in result[0].match_classes


def test_registered_brand_alias_qualifies_while_generic_terms_do_not():
    retriever = LocalChunkLexicalRetriever(
        (
            chunk("brand", text="AOG grill model information."),
            chunk("generic", text="Generic grill model information."),
        )
    )

    results = retriever.lexical_candidates(
        build_hybrid_request(
            build_retrieval_query("AOG grill model")
        )
    )

    assert [item.chunk.chunk_id for item in results] == ["brand"]
    assert results[0].matched_lexical_terms == ("aog",)


def test_normalized_substring_fallback_is_bounded():
    retriever = LocalChunkLexicalRetriever((chunk("fallback", text="Connector 1234567890 appears in the table."),), lexical_candidate_limit=1)

    result = retriever.lexical_candidates(
        build_hybrid_request(build_retrieval_query("1234567890"))
    )

    assert len(result) <= 1


def test_24_30_36_inch_scope_extraction():
    scope = extract_product_scope_terms("Compare 24 inch, 30 inch, and 36 inch AOG grills.")

    assert scope.sizes_inches == (24, 30, 36)


def test_built_in_post_cart_scope_extraction():
    scope = extract_product_scope_terms("Need a built-in, post, or cart L Series natural gas grill.")

    assert set(scope.mount_styles) == {"built-in", "post", "cart"}
    assert scope.series == ("L",)
    assert scope.fuel_types == ("natural_gas",)


def test_bounded_exact_diversity():
    candidates = tuple(
        RetrievalChannelCandidate(
            chunk(f"exact-{index}", relative_path="manuals/a.pdf", page_start=index, page_end=index),
            "exact_identifier",
            index,
            10,
            1,
            matched_identifiers=("24B11A",),
        )
        for index in range(1, 8)
    )

    fused = fuse_candidates(candidates, max_per_document=1, max_per_page_neighborhood=1, exact_max_per_document=3, exact_max_per_page_neighborhood=2, limit=10)

    assert len(fused) == 3


def test_invalid_configuration_handling():
    config = hybrid_config_from_values(
        {
            "HYBRID_CANDIDATE_LIMIT": "bad",
            "HYBRID_FINAL_LIMIT": "999",
            "HYBRID_RRF_K": "0",
        }
    )

    assert config == HybridRetrievalConfig(validation_reasons=config.validation_reasons)
    assert set(config.validation_reasons) >= {
        "HYBRID_CANDIDATE_LIMIT_INVALID_INT_DEFAULTED",
        "HYBRID_FINAL_LIMIT_ABOVE_MAX_DEFAULTED",
        "HYBRID_RRF_K_BELOW_MIN_DEFAULTED",
    }


def test_all_six_misses_classified_report_artifact():
    path = Path("reports/evaluation_runs/MS6-S5R1-HYBRID-EVAL/hybrid_retrieval_eval_latest.json")
    report = json.loads(path.read_text(encoding="utf-8"))
    missing = {"GQ-022", "GQ-023", "GQ-024", "GQ-026", "GQ-027", "GQ-030"}
    present = {row["id"] for row in report["results"] if row["id"] in missing}

    assert present == missing
