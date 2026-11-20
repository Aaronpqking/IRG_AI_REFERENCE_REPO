import re
from dataclasses import dataclass, field
from typing import Any

from src.models import Chunk
from src.ports import EmbeddingPort, VectorStorePort
from src.retrieval_policy import path_quality_score, year_score
from src.technical_text import (
    extract_query_terms,
    extract_query_tokens,
    normalize_technical_token,
    score_keyword_match,
)


class RetrievalStageError(RuntimeError):
    def __init__(self, stage: str, cause: Exception) -> None:
        super().__init__(f"{stage.upper()}_FAILED")
        self.stage = stage
        self.cause = cause


@dataclass(frozen=True)
class RankedChunk:
    chunk: Chunk
    rank: int
    vector_score: float
    identifier_score: float
    keyword_score: float
    year_score: float
    path_quality_score: float
    final_score: float
    matched_identifiers: tuple[str, ...] = ()
    matched_lexical_terms: tuple[str, ...] = ()
    channel_provenance: tuple[dict[str, Any], ...] = ()
    fusion_score: float | None = None


@dataclass(frozen=True)
class RankedRetrieval:
    query: str
    chunks: tuple[RankedChunk, ...]
    low_confidence: bool
    low_confidence_reason: str | None = None
    candidates: tuple[RankedChunk, ...] = ()
    diagnostics: dict[str, Any] = field(default_factory=dict)


def _metadata(chunk: Chunk) -> dict[str, Any]:
    return {
        "filename": chunk.filename,
        "relative_path": chunk.relative_path,
        "manufacturer": chunk.manufacturer,
        "brand": chunk.brand,
        "series": chunk.series,
        "product": chunk.product,
        "content_type": chunk.content_type,
        "technical_tokens_normalized": chunk.technical_tokens_normalized,
        "model_numbers": chunk.model_numbers,
        "part_numbers": chunk.part_numbers,
    }


def _normalized_values(chunk: Chunk) -> tuple[set[str], str]:
    structured = {
        normalize_technical_token(str(value))
        for value in (
            *chunk.technical_tokens_normalized,
            *chunk.model_numbers,
            *chunk.part_numbers,
            chunk.filename or "",
            chunk.relative_path or "",
            chunk.product or "",
            chunk.series or "",
            chunk.brand or "",
        )
        if value
    }
    return structured, normalize_technical_token(chunk.text)


def _identifier_matches(chunk: Chunk, query_tokens: list[str]) -> tuple[tuple[str, ...], float]:
    structured, normalized_text = _normalized_values(chunk)
    matched: list[str] = []
    score = 0.0
    for token in query_tokens:
        if any(token == value or token in value for value in structured):
            matched.append(token)
            score += 8.0
        elif token in normalized_text:
            matched.append(token)
            score += 4.0
    return tuple(matched), score


def _text_term_score(text: str, question_terms: list[str]) -> float:
    normalized_text = normalize_technical_token(text)
    score = 0.0
    for term in question_terms:
        normalized = normalize_technical_token(term)
        if len(normalized) >= 3 and normalized in normalized_text:
            score += 4.0
    return min(score, 24.0)


def _rank_candidates(
    chunks: tuple[Any, ...],
    query_tokens: list[str],
    question_terms: list[str],
    query_year: int | None,
    prefer_catalog: bool,
) -> list[RankedChunk]:
    ranked: list[RankedChunk] = []
    for retrieved in chunks:
        matched, identifier_score = _identifier_matches(retrieved.chunk, query_tokens)
        keyword_score = float(
            score_keyword_match(
                retrieved.chunk.text,
                _metadata(retrieved.chunk),
                question_terms,
                query_tokens,
            )
        ) + _text_term_score(retrieved.chunk.text, question_terms)
        vector_score = float(retrieved.score)
        candidate_year_score = year_score(
            retrieved.chunk,
            query_year,
            bool(matched) or keyword_score >= 4,
            prefer_catalog,
        )
        candidate_path_score = path_quality_score(
            retrieved.chunk,
            query_tokens,
            prefer_catalog,
            question_terms,
            query_year,
        )
        ranked.append(
            RankedChunk(
                chunk=retrieved.chunk,
                rank=0,
                vector_score=vector_score,
                identifier_score=identifier_score,
                keyword_score=keyword_score,
                year_score=candidate_year_score,
                path_quality_score=candidate_path_score,
                final_score=(
                    vector_score
                    + identifier_score
                    + (keyword_score * 0.1)
                    + candidate_year_score
                    + candidate_path_score
                ),
                matched_identifiers=matched,
            )
        )
    ranked.sort(key=lambda item: (item.final_score, item.vector_score), reverse=True)
    return ranked


def retrieve_ranked_chunks(
    question: str,
    embedding: EmbeddingPort,
    vector_store: VectorStorePort,
    limit: int = 5,
    candidate_limit: int | None = None,
) -> RankedRetrieval:
    query = question.strip()
    if not query:
        raise ValueError("question is required")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    search_limit = candidate_limit or max(20, limit * 5)
    if search_limit < limit:
        raise ValueError("candidate_limit must be at least limit")

    query_tokens = extract_query_tokens(query)
    question_terms = extract_query_terms(query)
    year_match = re.search(r"\b((?:19|20)\d{2})\b", query)
    query_year = int(year_match.group(1)) if year_match else None
    prefer_catalog = bool(
        re.search(r"\b(?:catalog|current|latest)\b", query, re.I)
    )
    try:
        vector = embedding.embed_query(query)
    except Exception as exc:
        raise RetrievalStageError("embedding", exc) from exc
    try:
        vector_result = vector_store.search(vector, limit=search_limit)
    except Exception as exc:
        raise RetrievalStageError("retrieval", exc) from exc
    ranked = _rank_candidates(
        vector_result.chunks,
        query_tokens,
        question_terms,
        query_year,
        prefer_catalog,
    )
    candidates = tuple(
        RankedChunk(**{**item.__dict__, "rank": rank})
        for rank, item in enumerate(ranked, 1)
    )
    selected = candidates[:limit]
    if not selected:
        return RankedRetrieval(query=query, chunks=(), low_confidence=True, low_confidence_reason="NO_RESULTS")
    top = selected[0]
    low_confidence = (
        top.identifier_score == 0
        and top.keyword_score < 2
        and top.vector_score < 0.35
    )
    return RankedRetrieval(
        query=query,
        chunks=selected,
        low_confidence=low_confidence,
        low_confidence_reason="WEAK_MATCH" if low_confidence else None,
        candidates=candidates,
    )
