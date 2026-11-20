from src.evidence_context import build_evidence_package
from src.eval_result_details import evidence_context
from src.models import Chunk
from src.retrieval import RankedChunk, RankedRetrieval


def chunk(chunk_id: str, text: str, **overrides: object) -> Chunk:
    values = {
        "chunk_id": chunk_id,
        "document_id": f"doc-{chunk_id}",
        "filename": "manual.pdf",
        "relative_path": "brand/model/manual.pdf",
        "page_start": 1,
        "page_end": 1,
        "chunk_index": 1,
    }
    values.update(overrides)
    return Chunk(text=text, **values)


def ranked(
    chunk_id: str,
    text: str,
    *,
    rank: int,
    final_score: float = 1.0,
    identifier_score: float = 0.0,
    keyword_score: float = 0.0,
    matched_identifiers: tuple[str, ...] = (),
    **overrides: object,
) -> RankedChunk:
    return RankedChunk(
        chunk=chunk(chunk_id, text, **overrides),
        rank=rank,
        vector_score=final_score,
        identifier_score=identifier_score,
        keyword_score=keyword_score,
        year_score=0.0,
        path_quality_score=0.0,
        final_score=final_score,
        matched_identifiers=matched_identifiers,
    )


def retrieval(items: tuple[RankedChunk, ...]) -> RankedRetrieval:
    return RankedRetrieval(
        query="What are the cutout dimensions for AOG-24-B?",
        chunks=items[:3],
        candidates=items,
        low_confidence=False,
    )


def selected_ids(question: str, items: tuple[RankedChunk, ...]) -> list[str]:
    package = build_evidence_package(question, retrieval(items))
    return [item.chunk.chunk_id for item in package.selected]


def test_selects_same_source_same_page_adjacent_chunks() -> None:
    items = (
        ranked("anchor", "Width is 10 inches.", rank=1, chunk_index=2),
        ranked("before", "CUTOUT DIMENSIONS", rank=2, chunk_index=1),
        ranked("after", "Depth is 8 inches.", rank=3, chunk_index=3),
    )

    assert selected_ids("What are the cutout dimensions?", items) == [
        "before", "anchor", "after",
    ]


def test_excludes_different_source_chunks() -> None:
    items = (
        ranked("anchor", "Width is 10 inches.", rank=1, chunk_index=1),
        ranked(
            "other",
            "Depth is 8 inches.",
            rank=2,
            chunk_index=2,
            relative_path="other/manual.pdf",
        ),
    )

    assert selected_ids("What are the cutout dimensions?", items) == ["anchor"]


def test_excludes_different_page_by_default() -> None:
    items = (
        ranked("anchor", "Model AOG-24-B overview.", rank=1, chunk_index=1),
        ranked(
            "other-page",
            "More model AOG-24-B details.",
            rank=2,
            page_start=2,
            page_end=2,
            chunk_index=2,
        ),
    )

    assert selected_ids("Tell me about model AOG-24-B", items) == ["anchor"]


def test_allows_controlled_cross_page_expansion_for_dimensions() -> None:
    items = (
        ranked("anchor", "CUTOUT DIMENSIONS", rank=1, chunk_index=1),
        ranked(
            "next-page",
            "Width is 10 inches.",
            rank=2,
            page_start=2,
            page_end=2,
            chunk_index=2,
        ),
    )

    assert selected_ids("What are the cutout dimensions?", items) == [
        "anchor", "next-page",
    ]


def test_allows_nearby_two_page_expansion_for_installation_context() -> None:
    items = (
        ranked(
            "anchor",
            "Attach the bracket using the listed wrench.",
            rank=1,
            page_start=7,
            page_end=7,
            chunk_index=7,
        ),
        ranked(
            "warning",
            "WARNING: position approved parts before assembly.",
            rank=2,
            page_start=5,
            page_end=5,
            chunk_index=4,
        ),
    )

    assert selected_ids("What warning applies during installation?", items) == [
        "warning", "anchor",
    ]


def test_excludes_non_adjacent_chunks_by_default() -> None:
    items = (
        ranked("anchor", "Model AOG-24-B overview.", rank=1, chunk_index=1),
        ranked("far", "Far away text.", rank=2, chunk_index=5),
    )

    assert selected_ids("Tell me about model AOG-24-B", items) == ["anchor"]


def test_deduplicates_chunk_ids() -> None:
    duplicate_a = ranked("dup", "Width is 10 inches.", rank=1, chunk_index=1)
    duplicate_b = ranked("dup", "Width is 10 inches.", rank=2, chunk_index=1)

    assert selected_ids("What are the dimensions?", (duplicate_a, duplicate_b)) == ["dup"]


def test_preserves_ranked_score_and_rank_metadata() -> None:
    item = ranked("anchor", "Width is 10 inches.", rank=7, final_score=3.5)
    package = build_evidence_package("What are the dimensions?", retrieval((item,)))

    assert package.selected[0].rank == 7
    assert package.selected[0].final_score == 3.5


def test_exact_model_rank_three_can_beat_generic_rank_one() -> None:
    generic = ranked(
        "generic",
        "General grill information.",
        rank=1,
        final_score=4.0,
        relative_path="brand/generic/manual.pdf",
    )
    weak = ranked(
        "weak",
        "Other text.",
        rank=2,
        final_score=3.0,
        relative_path="brand/weak/manual.pdf",
    )
    exact = ranked(
        "exact",
        "Model AOG-24-B installation.",
        rank=3,
        final_score=1.0,
        identifier_score=8.0,
        technical_tokens_normalized=("AOG24B",),
    )

    assert selected_ids("Tell me about model AOG-24-B", (generic, weak, exact)) == [
        "exact",
    ]


def test_newer_same_scope_group_can_win_when_no_exact_year_requested() -> None:
    older = ranked(
        "older",
        "Replacement part details.",
        rank=1,
        final_score=4.0,
        keyword_score=5.0,
        relative_path="brand/same-scope/2018/om/manual.pdf",
    )
    newer = ranked(
        "newer",
        "Replacement part details.",
        rank=2,
        final_score=3.7,
        keyword_score=5.0,
        relative_path="brand/same-scope/2024/om/manual.pdf",
    )

    assert selected_ids("What same-scope replacement part is listed?", (older, newer)) == [
        "newer",
    ]


def test_newer_broad_group_without_scope_overlap_does_not_get_recency_bonus() -> None:
    scoped = ranked(
        "scoped",
        "Accessory details.",
        rank=2,
        final_score=4.0,
        keyword_score=5.0,
        relative_path="brand/widget-accessory/2020/om/manual.pdf",
    )
    broad = ranked(
        "broad",
        "Accessory details.",
        rank=1,
        final_score=3.9,
        keyword_score=5.0,
        relative_path="brand/general/2024/om/manual.pdf",
    )

    assert selected_ids("Will the widget accessory work?", (broad, scoped)) == [
        "scoped",
    ]


def test_exact_year_group_preference_overrides_newer_same_scope_group() -> None:
    exact_year = ranked(
        "exact-year",
        "Replacement part details.",
        rank=2,
        final_score=3.0,
        keyword_score=5.0,
        relative_path="brand/same-scope/2018/om/manual.pdf",
    )
    newer = ranked(
        "newer",
        "Replacement part details.",
        rank=1,
        final_score=4.0,
        keyword_score=5.0,
        relative_path="brand/same-scope/2024/om/manual.pdf",
    )

    assert selected_ids(
        "In the 2018 manual, what replacement part is listed?",
        (newer, exact_year),
    ) == ["exact-year"]


def test_rank_one_group_wins_near_tie_over_lower_rank_group() -> None:
    rank_one = ranked(
        "rank-one",
        "Current warning details.",
        rank=1,
        final_score=10.0,
        keyword_score=4.0,
        relative_path="brand/same-scope/2024/om/manual.pdf",
    )
    lower_rank = ranked(
        "lower-rank",
        "Older warning details.",
        rank=2,
        final_score=10.01,
        keyword_score=4.0,
        relative_path="brand/same-scope/2020/om/manual.pdf",
    )

    assert selected_ids("What warning details are listed?", (rank_one, lower_rank)) == [
        "rank-one",
    ]


def test_top_value_with_adjacent_table_heading_selects_both() -> None:
    items = (
        ranked("value", "Width 10 inches.", rank=1, chunk_index=2),
        ranked("heading", "TABLE 1 CUTOUT DIMENSIONS", rank=2, chunk_index=1),
    )

    assert selected_ids("What cutout dimension is listed?", items) == [
        "heading", "value",
    ]


def test_adjacent_warning_for_safe_answer_is_selected() -> None:
    items = (
        ranked("step", "Connect the wiring harness.", rank=1, chunk_index=2),
        ranked("warning", "WARNING: shut off gas first.", rank=2, chunk_index=1),
    )

    assert selected_ids("What warning applies before wiring install?", items) == [
        "warning", "step",
    ]


def test_eval_parity_uses_same_evidence_selection() -> None:
    items = (
        ranked("value", "Width 10 inches.", rank=1, chunk_index=2),
        ranked("heading", "TABLE 1 CUTOUT DIMENSIONS", rank=2, chunk_index=1),
    )
    fake_retrieval = retrieval(items)

    production = build_evidence_package("What cutout dimension is listed?", fake_retrieval)
    eval_package = evidence_context("What cutout dimension is listed?", fake_retrieval)

    assert [item.chunk.chunk_id for item in eval_package.selected] == [
        item.chunk.chunk_id for item in production.selected
    ]
