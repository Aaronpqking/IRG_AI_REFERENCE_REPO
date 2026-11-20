from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from types import MappingProxyType
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

from src.runtime_contracts import PdfEvidenceResult, RetrievalQuery
from src.information_needs import classify_information_needs
from src.models import Chunk, RetrievedChunk, RetrievalResult, chunk_from_record
from src.product_applicability import ProductApplicabilityContext
from src.product_taxonomy import DEFAULT_PRODUCT_TAXONOMY
from src.query_identity import parse_query_identity as _parse_corpus_identity
from src.retrieval import RankedChunk, RankedRetrieval
from src.retrieval_policy import infer_document_type
from src.technical_tokens import extract_query_terms, normalize_technical_token


TECHNICAL_INTENT_TERMS = {
    "clearances": ("clearance", "clearances", "combustible"),
    "cutout": ("cutout", "cut-out", "opening"),
    "dimensions": ("dimension", "dimensions", "height", "width", "depth"),
    "warnings": ("warning", "warnings", "caution"),
    "cautions": ("caution", "warning"),
    "installation": ("install", "installation", "mount", "mounting"),
    "wiring": ("wiring", "wire", "electrical"),
    "parts": ("part", "parts", "replacement", "component"),
    "compatibility": ("fit", "fits", "compatible", "compatibility"),
}
WEAK_LEXICAL_TERMS = {
    "grill", "grills", "model", "models", "what", "which", "with",
    "that", "this", "have", "does", "need", "listed", "inch", "inches",
}
MOUNT_STYLE_TERMS = {
    "built-in": ("built in", "built-in", "builtin"),
    "post": ("post", "in-ground", "in ground"),
    "cart": ("cart",),
}
FUEL_TERMS = {
    "natural_gas": ("natural gas", "nat gas", "nat"),
    "propane": ("propane", "lp"),
}


@dataclass(frozen=True)
class ProductScopeTerms:
    sizes_inches: tuple[int, ...] = ()
    mount_styles: tuple[str, ...] = ()
    series: tuple[str, ...] = ()
    fuel_types: tuple[str, ...] = ()
    approximate_cutout_widths: tuple[int, ...] = ()


@dataclass(frozen=True)
class HybridRetrievalConfig:
    candidate_limit: int = 50
    final_limit: int = 5
    rrf_k: int = 60
    max_candidates_per_document: int = 8
    max_candidates_per_page_neighborhood: int = 3
    exact_max_candidates_per_document: int = 12
    exact_max_candidates_per_page_neighborhood: int = 6
    lexical_query_candidate_limit: int = 120
    validation_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class HybridRetrievalRequest:
    retrieval_query: RetrievalQuery
    normalized_question: str
    lexical_terms: tuple[str, ...]
    technical_intent_terms: tuple[str, ...]
    product_context: ProductApplicabilityContext | None = None
    preferred_document_ids: tuple[str, ...] = ()
    preferred_filenames: tuple[str, ...] = ()
    preferred_paths: tuple[str, ...] = ()
    preferred_brand: str | None = None
    preferred_manufacturer: str | None = None
    preferred_series: str | None = None
    preferred_model: str | None = None
    document_type_preference: str | None = None
    document_type_explicit: bool = False
    requested_year: int | None = None
    scope_terms: ProductScopeTerms = ProductScopeTerms()
    candidate_limit: int = 50
    final_limit: int = 5

    @property
    def raw_question(self) -> str:
        return self.retrieval_query.semantic_query_text

    @property
    def exact_identifier_queries(self) -> tuple[str, ...]:
        return self.retrieval_query.exact_identifier_queries

    @property
    def identifier_variants(self) -> tuple[str, ...]:
        return self.retrieval_query.identifier_variants


@dataclass(frozen=True)
class RetrievalChannelCandidate:
    chunk: Chunk
    channel_name: str
    channel_rank: int
    channel_native_score: float
    normalized_score: float
    matched_identifiers: tuple[str, ...] = ()
    matched_lexical_terms: tuple[str, ...] = ()
    metadata_filter_basis: tuple[str, ...] = ()
    source_identity: str = ""
    channel_latency_ms: int = 0
    match_classes: tuple[str, ...] = ()


@dataclass(frozen=True)
class FusedCandidate:
    chunk: Chunk
    rank: int
    fusion_score: float
    channel_candidates: tuple[RetrievalChannelCandidate, ...]
    matched_identifiers: tuple[str, ...]
    matched_lexical_terms: tuple[str, ...]
    metadata_filter_basis: tuple[str, ...]


@dataclass(frozen=True)
class LexicalIndex:
    chunk_by_id: MappingProxyType
    chunk_identifiers: MappingProxyType
    exact_identifier_postings: MappingProxyType
    normalized_term_postings: MappingProxyType
    phrase_section_postings: MappingProxyType
    filename_path_postings: MappingProxyType
    document_type_postings: MappingProxyType
    year_postings: MappingProxyType
    build_duration_ms: int
    memory_estimate_bytes: int


def build_hybrid_request(
    query: RetrievalQuery,
    *,
    product_context: ProductApplicabilityContext | None = None,
    candidate_limit: int = 50,
    final_limit: int = 5,
) -> HybridRetrievalRequest:
    text = query.semantic_query_text
    needs = classify_information_needs(text)
    technical_terms = []
    for need in needs.technical:
        technical_terms.extend(TECHNICAL_INTENT_TERMS.get(need, (need,)))
    lexical_terms = extract_query_terms(text)
    lexical = _dedupe(
        [
            *lexical_terms,
            *technical_terms,
            *query.identifier_variants,
        ]
    )
    preferred_ids: tuple[str, ...] = ()
    preferred_files: tuple[str, ...] = ()
    preferred_paths: tuple[str, ...] = ()
    if product_context is not None:
        preferred_ids = product_context.source_document_ids
        preferred_files = product_context.source_filenames
        preferred_paths = (*product_context.source_paths, *product_context.source_urls)
    facets = {
        str(name).casefold(): str(value)
        for name, value in query.product_facets
    }
    detected_brand = DEFAULT_PRODUCT_TAXONOMY.resolve_brand(text)
    detected_series = DEFAULT_PRODUCT_TAXONOMY.resolve_series(
        text,
        brand=detected_brand,
    )
    identity_brand = (
        detected_brand.definition
        if detected_brand
        else detected_series.brand if detected_series else None
    )
    if identity_brand:
        brand_components = {
            word.casefold()
            for word in re.findall(r"[a-z0-9]+", identity_brand.canonical_name, re.I)
        }
        lexical = _dedupe(
            [
                term
                for term in lexical
                if str(term).casefold() not in brand_components
            ]
            + [identity_brand.canonical_name]
        )
    preferred_brand = (
        product_context.brand
        if product_context and product_context.brand
        else facets.get("brand")
        or (identity_brand.canonical_name if identity_brand else None)
    )
    preferred_manufacturer = facets.get("manufacturer")
    if (
        not preferred_manufacturer
        and identity_brand
        and len(identity_brand.corpus_namespaces) == 1
    ):
        preferred_manufacturer = identity_brand.corpus_namespaces[0]
    preferred_series = (
        product_context.series
        if product_context and product_context.series
        else facets.get("series")
        or (detected_series.canonical_name if detected_series else None)
    )
    preferred_model = (
        product_context.model
        if product_context and product_context.model
        else facets.get("model")
        or facets.get("mpn")
    )
    return HybridRetrievalRequest(
        retrieval_query=query,
        normalized_question=normalize_technical_token(text),
        lexical_terms=tuple(lexical),
        technical_intent_terms=tuple(_dedupe(technical_terms)),
        product_context=product_context,
        preferred_document_ids=preferred_ids,
        preferred_filenames=preferred_files,
        preferred_paths=preferred_paths,
        preferred_brand=preferred_brand,
        preferred_manufacturer=preferred_manufacturer,
        preferred_series=preferred_series,
        preferred_model=preferred_model,
        document_type_preference=_document_type_preference(tuple(needs.technical)),
        document_type_explicit=_explicit_document_type_request(text),
        requested_year=_query_year(text),
        scope_terms=extract_product_scope_terms(text),
        candidate_limit=candidate_limit,
        final_limit=final_limit,
    )


class LocalChunkLexicalRetriever:
    def __init__(self, chunks: tuple[Chunk, ...], *, lexical_candidate_limit: int = 120) -> None:
        started = perf_counter()
        self.chunks = chunks
        self.lexical_candidate_limit = max(1, lexical_candidate_limit)
        self.index = _build_lexical_index(chunks, started)

    @classmethod
    def from_jsonl(cls, path: str | Path, *, lexical_candidate_limit: int = 120) -> "LocalChunkLexicalRetriever":
        rows = []
        source = Path(path)
        if source.exists():
            for line in source.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(chunk_from_record(json.loads(line)))
        return cls(tuple(rows), lexical_candidate_limit=lexical_candidate_limit)

    def exact_identifier_candidates(self, request: HybridRetrievalRequest) -> tuple[RetrievalChannelCandidate, ...]:
        started = perf_counter()
        identifiers = request.exact_identifier_queries
        if not identifiers:
            return ()
        found = []
        chunk_ids = _ordered_posting_union(self.index.exact_identifier_postings, identifiers)
        for chunk_id in chunk_ids:
            chunk = self.index.chunk_by_id[chunk_id]
            matched = tuple(identifier for identifier in identifiers if identifier in self.index.chunk_identifiers.get(chunk_id, ()))
            if not matched:
                continue
            found.append(
                RetrievalChannelCandidate(
                    chunk=chunk,
                    channel_name="exact_identifier",
                    channel_rank=0,
                    channel_native_score=float(len(matched)),
                    normalized_score=1.0,
                    matched_identifiers=matched,
                    source_identity=_source_identity(chunk),
                    match_classes=("EXACT_IDENTIFIER",),
                )
            )
        return _rank_channel(found, started)

    def lexical_candidates(self, request: HybridRetrievalRequest) -> tuple[RetrievalChannelCandidate, ...]:
        started = perf_counter()
        terms = tuple(term for term in request.lexical_terms if _strong_lexical_term(term))
        variants = tuple(
            variant
            for variant in request.identifier_variants
            if _strong_lexical_term(variant)
        )
        phrases = _query_phrases(request.raw_question)
        if request.preferred_brand:
            phrases = tuple(
                _dedupe([*phrases, request.preferred_brand])
            )
        weak_exact_phrase = _weak_exact_query_phrase(
            request.raw_question
        )
        if weak_exact_phrase:
            phrases = tuple(
                _dedupe([*phrases, weak_exact_phrase])
            )
        scope_terms = _scope_query_terms(request.scope_terms)
        lookup_terms = _dedupe([*terms, *scope_terms, *variants])
        if not lookup_terms and not weak_exact_phrase:
            return ()
        candidate_scores: dict[str, float] = {}
        _add_posting_scores(candidate_scores, self.index.normalized_term_postings, lookup_terms, 1.0)
        _add_posting_scores(candidate_scores, self.index.filename_path_postings, lookup_terms, 1.5)
        for index, variant in enumerate(variants):
            _add_posting_scores(
                candidate_scores,
                self.index.normalized_term_postings,
                (variant,),
                _identifier_variant_weight(request, index),
            )
            _add_posting_scores(
                candidate_scores,
                self.index.filename_path_postings,
                (variant,),
                _identifier_variant_weight(request, index) + 1.0,
            )
        _add_posting_scores(candidate_scores, self.index.phrase_section_postings, phrases, 3.0)
        if request.preferred_brand:
            for chunk_id, chunk in self.index.chunk_by_id.items():
                if _phrase_match(
                    request.preferred_brand,
                    _chunk_search_text(chunk),
                ):
                    candidate_scores[chunk_id] = (
                        candidate_scores.get(chunk_id, 0.0) + 4.0
                    )
        for document_type in (request.document_type_preference,):
            if document_type:
                _add_ids(candidate_scores, self.index.document_type_postings.get(document_type, ()), 0.75)
        if request.requested_year:
            _add_ids(candidate_scores, self.index.year_postings.get(str(request.requested_year), ()), 0.5)
        if weak_exact_phrase:
            for chunk_id, chunk in self.index.chunk_by_id.items():
                if _phrase_match(
                    weak_exact_phrase,
                    _chunk_search_text(chunk),
                ):
                    candidate_scores[chunk_id] = (
                        candidate_scores.get(chunk_id, 0.0) + 3.0
                    )
        if request.preferred_manufacturer:
            candidate_scores = {
                chunk_id: score
                for chunk_id, score in candidate_scores.items()
                if not _has_conflicting_manufacturer(
                    self.index.chunk_by_id[chunk_id],
                    request,
                )
            }
        candidate_ids = tuple(
            chunk_id
            for chunk_id, _ in sorted(
                candidate_scores.items(),
                key=lambda item: (-item[1], _source_identity(self.index.chunk_by_id[item[0]]), self.index.chunk_by_id[item[0]].page_start, item[0]),
            )[: self.lexical_candidate_limit]
        )
        found = []
        for chunk_id in candidate_ids:
            chunk = self.index.chunk_by_id[chunk_id]
            searchable = _chunk_search_text(chunk)
            matched = tuple(term for term in lookup_terms if _term_match(term, searchable))
            match_classes = _match_classes(chunk, lookup_terms, phrases)
            strong_matches = tuple(term for term in matched if _strong_lexical_term(term))
            if (
                weak_exact_phrase
                and _phrase_match(
                    weak_exact_phrase,
                    searchable,
                )
            ):
                strong_matches = tuple(
                    _dedupe(
                        [*strong_matches, weak_exact_phrase]
                    )
                )
            matched_variants = tuple(
                variant
                for variant in variants
                if _term_match(variant, searchable)
            )
            if not strong_matches or not match_classes:
                continue
            text_hits = sum(1 for term in strong_matches if _term_match(term, chunk.text or ""))
            exact_phrase_hits = sum(1 for phrase in phrases if _phrase_match(phrase, chunk.text or ""))
            scope_score = _scope_score(chunk, request.scope_terms)
            attribute_score = _requested_attribute_score(chunk, request)
            entity_weight = sum(_lexical_term_weight(term) for term in strong_matches)
            variant_weight = sum(
                _identifier_variant_weight(
                    request,
                    variants.index(variant),
                )
                for variant in matched_variants
            )
            score = float((text_hits * 2) + entity_weight + variant_weight + (exact_phrase_hits * 5) + scope_score + attribute_score)
            found.append(
                RetrievalChannelCandidate(
                    chunk=chunk,
                    channel_name="lexical",
                    channel_rank=0,
                    channel_native_score=score,
                    normalized_score=min(1.0, score / 24.0),
                    matched_identifiers=tuple(
                        dict.fromkeys(
                            normalize_technical_token(variant).upper()
                            for variant in matched_variants
                            if normalize_technical_token(variant)
                        )
                    ),
                    matched_lexical_terms=strong_matches,
                    source_identity=_source_identity(chunk),
                    match_classes=match_classes,
                )
            )
        ranked = _rank_channel(found, started)
        return ranked[: self.lexical_candidate_limit]

    def metadata_candidates(self, request: HybridRetrievalRequest) -> tuple[RetrievalChannelCandidate, ...]:
        started = perf_counter()
        if not _has_metadata_constraints(request):
            return ()
        found = []
        for chunk in self.chunks:
            basis = _metadata_basis(chunk, request)
            if not basis:
                continue
            score = float(len(basis))
            found.append(
                RetrievalChannelCandidate(
                    chunk=chunk,
                    channel_name="metadata_filter",
                    channel_rank=0,
                    channel_native_score=score,
                    normalized_score=min(1.0, score / 5.0),
                    metadata_filter_basis=tuple(basis),
                    source_identity=_source_identity(chunk),
                    match_classes=("METADATA_MATCH",),
                )
            )
        return _rank_channel(found, started)


class SemanticVectorChannel:
    def __init__(self, embedding: Any, vector_store: Any) -> None:
        self.embedding = embedding
        self.vector_store = vector_store

    def retrieve(self, request: HybridRetrievalRequest) -> tuple[RetrievalChannelCandidate, ...]:
        started = perf_counter()
        vector = self.embedding.embed_query(request.raw_question)
        filters = _semantic_filters(request)
        filtered_search = getattr(self.vector_store, "search_filtered", None)
        if filters and callable(filtered_search):
            result = filtered_search(
                vector,
                limit=request.candidate_limit,
                filters=filters,
            )
        else:
            result = self.vector_store.search(vector, limit=request.candidate_limit)
        candidates = []
        for item in result.chunks:
            candidates.append(
                RetrievalChannelCandidate(
                    chunk=item.chunk,
                    channel_name="semantic_vector",
                    channel_rank=int(item.rank),
                    channel_native_score=float(item.score),
                    normalized_score=max(0.0, min(1.0, float(item.score))),
                    source_identity=_source_identity(item.chunk),
                )
            )
        latency = int((perf_counter() - started) * 1000)
        return tuple(
            RetrievalChannelCandidate(**{**candidate.__dict__, "channel_latency_ms": latency})
            for candidate in candidates
        )


class HybridPdfEvidenceAdapter:
    def __init__(
        self,
        embedding: Any,
        vector_store: Any,
        lexical_retriever: LocalChunkLexicalRetriever,
        config: HybridRetrievalConfig | None = None,
    ) -> None:
        self.embedding = embedding
        self.vector_store = vector_store
        self.lexical_retriever = lexical_retriever
        self.config = config or HybridRetrievalConfig()
        self.semantic_channel = SemanticVectorChannel(embedding, vector_store)

    def retrieve(
        self,
        query: RetrievalQuery,
        *,
        top_k: int = 5,
        product_context: ProductApplicabilityContext | None = None,
    ) -> PdfEvidenceResult:
        started = perf_counter()
        request = build_hybrid_request(
            query,
            product_context=product_context,
            candidate_limit=self.config.candidate_limit,
            final_limit=top_k or self.config.final_limit,
        )
        channels = (
            self.lexical_retriever.exact_identifier_candidates(request),
            self.lexical_retriever.lexical_candidates(request),
            self.lexical_retriever.metadata_candidates(request),
            self.semantic_channel.retrieve(request),
        )
        fused = fuse_candidates(
            tuple(candidate for channel in channels for candidate in channel),
            rrf_k=self.config.rrf_k,
            limit=request.candidate_limit,
            max_per_document=self.config.max_candidates_per_document,
            max_per_page_neighborhood=self.config.max_candidates_per_page_neighborhood,
            exact_max_per_document=self.config.exact_max_candidates_per_document,
            exact_max_per_page_neighborhood=self.config.exact_max_candidates_per_page_neighborhood,
            request=request,
        )
        ranked = _ranked_retrieval(
            query.semantic_query_text,
            fused,
            top_k,
            request,
        )
        diagnostics = _diagnostics(request, channels, fused, started, self.config.rrf_k)
        diagnostics["lexical_index"] = {
            "chunks": len(self.lexical_retriever.index.chunk_by_id),
            "build_duration_ms": self.lexical_retriever.index.build_duration_ms,
            "memory_estimate_bytes": self.lexical_retriever.index.memory_estimate_bytes,
            "query_candidate_limit": self.lexical_retriever.lexical_candidate_limit,
        }
        diagnostics["config_validation_reasons"] = list(self.config.validation_reasons)
        ranked = RankedRetrieval(**{**ranked.__dict__, "diagnostics": diagnostics})
        return PdfEvidenceResult(query=query, retrieval=ranked, duration_ms=int((perf_counter() - started) * 1000), diagnostics=diagnostics)


def fuse_candidates(
    candidates: tuple[RetrievalChannelCandidate, ...],
    *,
    rrf_k: int = 60,
    limit: int = 50,
    max_per_document: int = 8,
    max_per_page_neighborhood: int = 3,
    exact_max_per_document: int = 12,
    exact_max_per_page_neighborhood: int = 6,
    request: HybridRetrievalRequest | None = None,
) -> tuple[FusedCandidate, ...]:
    grouped: dict[str, list[RetrievalChannelCandidate]] = {}
    for candidate in candidates:
        if request and _has_conflicting_manufacturer(candidate.chunk, request):
            continue
        grouped.setdefault(_canonical_chunk_identity(candidate.chunk), []).append(candidate)
    fused = []
    for key, items in grouped.items():
        score = sum(1.0 / (rrf_k + max(1, item.channel_rank)) for item in items)
        chunk = sorted((item.chunk for item in items), key=lambda chunk: _canonical_chunk_identity(chunk))[0]
        fused.append(
            FusedCandidate(
                chunk=chunk,
                rank=0,
                fusion_score=score,
                channel_candidates=tuple(sorted(items, key=lambda item: (item.channel_name, item.channel_rank))),
                matched_identifiers=tuple(
                    sorted(
                        {
                            normalized
                            for item in items
                            for value in item.matched_identifiers
                            if (
                                normalized
                                := normalize_technical_token(value).upper()
                            )
                        }
                    )
                ),
                matched_lexical_terms=tuple(sorted({value for item in items for value in item.matched_lexical_terms})),
                metadata_filter_basis=tuple(sorted({value for item in items for value in item.metadata_filter_basis})),
            )
        )
    exact_sources = {
        _source_identity(item.chunk)
        for item in fused
        if any(
            candidate.channel_name == "exact_identifier"
            for candidate in item.channel_candidates
        )
    }
    ordered = sorted(
        fused,
        key=lambda item: (
            *tuple(
                -value
                for value in _identity_precedence(
                    item,
                    request,
                    exact_sources,
                )
            ),
            -item.fusion_score,
            _source_identity(item.chunk),
            item.chunk.page_start,
            item.chunk.chunk_id,
        ),
    )
    diversified = _diversify(
        ordered,
        max_per_document,
        max_per_page_neighborhood,
        exact_max_per_document,
        exact_max_per_page_neighborhood,
        limit,
    )
    return tuple(
        FusedCandidate(**{**item.__dict__, "rank": index})
        for index, item in enumerate(diversified, 1)
    )


def _ranked_retrieval(
    query: str,
    fused: tuple[FusedCandidate, ...],
    top_k: int,
    request: HybridRetrievalRequest,
) -> RankedRetrieval:
    ranked = tuple(
        RankedChunk(
            chunk=item.chunk,
            rank=item.rank,
            vector_score=_channel_score(item, "semantic_vector"),
            identifier_score=8.0 * len(item.matched_identifiers),
            keyword_score=sum(
                _lexical_term_weight(term)
                for term in item.matched_lexical_terms
            ),
            year_score=0.0,
            path_quality_score=0.0,
            final_score=item.fusion_score,
            matched_identifiers=item.matched_identifiers,
            matched_lexical_terms=item.matched_lexical_terms,
            channel_provenance=tuple(_candidate_provenance(candidate) for candidate in item.channel_candidates),
            fusion_score=item.fusion_score,
        )
        for item in fused
    )
    selected = ranked[:top_k]
    low_confidence = not selected or (
        bool(request.exact_identifier_queries)
        and not any(item.matched_identifiers for item in selected)
        and not request.product_context
    )
    return RankedRetrieval(
        query=query,
        chunks=selected,
        low_confidence=low_confidence,
        low_confidence_reason="NO_HYBRID_CANDIDATES" if not selected else "NO_EXACT_IDENTIFIER_CANDIDATE" if low_confidence else None,
        candidates=ranked,
    )


def _rank_channel(
    candidates: list[RetrievalChannelCandidate],
    started: float,
) -> tuple[RetrievalChannelCandidate, ...]:
    ordered = sorted(
        candidates,
        key=lambda item: (-item.channel_native_score, _source_identity(item.chunk), item.chunk.page_start, item.chunk.chunk_id),
    )
    latency = int((perf_counter() - started) * 1000)
    return tuple(
        RetrievalChannelCandidate(**{**item.__dict__, "channel_rank": index, "channel_latency_ms": latency})
        for index, item in enumerate(ordered, 1)
    )


def _diversify(
    ordered: list[FusedCandidate],
    max_per_document: int,
    max_per_page_neighborhood: int,
    exact_max_per_document: int,
    exact_max_per_page_neighborhood: int,
    limit: int,
) -> list[FusedCandidate]:
    kept: list[FusedCandidate] = []
    doc_counts: dict[str, int] = {}
    page_counts: dict[tuple[str, int], int] = {}
    for item in ordered:
        source = _source_identity(item.chunk)
        neighborhood = (source, max(1, int(item.chunk.page_start or 1)) // 2)
        exact = any(candidate.channel_name == "exact_identifier" for candidate in item.channel_candidates)
        doc_cap = exact_max_per_document if exact else max_per_document
        page_cap = exact_max_per_page_neighborhood if exact else max_per_page_neighborhood
        if doc_counts.get(source, 0) >= doc_cap:
            continue
        if page_counts.get(neighborhood, 0) >= page_cap:
            continue
        kept.append(item)
        doc_counts[source] = doc_counts.get(source, 0) + 1
        page_counts[neighborhood] = page_counts.get(neighborhood, 0) + 1
        if len(kept) >= limit:
            break
    return kept


def _build_lexical_index(chunks: tuple[Chunk, ...], started: float) -> LexicalIndex:
    chunk_by_id: dict[str, Chunk] = {}
    chunk_identifiers: dict[str, tuple[str, ...]] = {}
    exact_identifier_postings: dict[str, set[str]] = defaultdict(set)
    normalized_term_postings: dict[str, set[str]] = defaultdict(set)
    phrase_section_postings: dict[str, set[str]] = defaultdict(set)
    filename_path_postings: dict[str, set[str]] = defaultdict(set)
    document_type_postings: dict[str, set[str]] = defaultdict(set)
    year_postings: dict[str, set[str]] = defaultdict(set)

    for chunk in chunks:
        chunk_by_id[chunk.chunk_id] = chunk
        identifiers = tuple(sorted(_chunk_identifier_set(chunk)))
        chunk_identifiers[chunk.chunk_id] = identifiers
        for identifier in identifiers:
            exact_identifier_postings[identifier].add(chunk.chunk_id)
        chunk_search_text = _chunk_search_text(chunk)
        for term in _tokenize(chunk_search_text):
            if _strong_lexical_term(term):
                normalized_term_postings[term].add(chunk.chunk_id)
        section_text = " ".join(value for value in (chunk.section_title, chunk.section_path) if value)
        for term in _tokenize(section_text):
            if _strong_lexical_term(term):
                phrase_section_postings[term].add(chunk.chunk_id)
        for phrase in _section_phrases(section_text):
            phrase_section_postings[phrase].add(chunk.chunk_id)
        source_text = " ".join(
            value
            for value in (
                chunk.filename,
                chunk.relative_path,
                chunk.source_path,
                *chunk.catalog_path_aliases,
            )
            if value
        )
        for term in _tokenize(source_text):
            if _strong_lexical_term(term):
                filename_path_postings[term].add(chunk.chunk_id)
        document_type_postings[infer_document_type(chunk)].add(chunk.chunk_id)
        if chunk.year:
            year_postings[str(chunk.year)].add(chunk.chunk_id)

    postings = (
        exact_identifier_postings,
        normalized_term_postings,
        phrase_section_postings,
        filename_path_postings,
        document_type_postings,
        year_postings,
    )
    return LexicalIndex(
        chunk_by_id=MappingProxyType(chunk_by_id),
        chunk_identifiers=MappingProxyType(chunk_identifiers),
        exact_identifier_postings=_freeze_postings(exact_identifier_postings),
        normalized_term_postings=_freeze_postings(normalized_term_postings),
        phrase_section_postings=_freeze_postings(phrase_section_postings),
        filename_path_postings=_freeze_postings(filename_path_postings),
        document_type_postings=_freeze_postings(document_type_postings),
        year_postings=_freeze_postings(year_postings),
        build_duration_ms=int((perf_counter() - started) * 1000),
        memory_estimate_bytes=sum(sys.getsizeof(posting) + sum(sys.getsizeof(value) for value in posting) for table in postings for posting in table.values()),
    )


def _freeze_postings(postings: dict[str, set[str]]) -> MappingProxyType:
    return MappingProxyType(
        {
            key: tuple(sorted(values))
            for key, values in postings.items()
        }
    )


def _ordered_posting_union(postings: MappingProxyType, terms: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen = set()
    ordered = []
    for term in terms:
        for chunk_id in postings.get(term, ()):
            if chunk_id not in seen:
                seen.add(chunk_id)
                ordered.append(chunk_id)
    return tuple(ordered)


def _add_posting_scores(
    scores: dict[str, float],
    postings: MappingProxyType,
    terms: tuple[str, ...] | list[str],
    weight: float,
) -> None:
    for term in terms:
        _add_ids(scores, postings.get(_posting_key(term), ()), weight)


def _add_ids(scores: dict[str, float], chunk_ids: tuple[str, ...], weight: float) -> None:
    for chunk_id in chunk_ids:
        scores[chunk_id] = scores.get(chunk_id, 0.0) + weight


def _chunk_identifier_set(chunk: Chunk) -> set[str]:
    values = set()
    for item in (
        *chunk.technical_tokens_normalized,
        *chunk.model_numbers,
        *chunk.document_model_numbers,
        *chunk.part_numbers,
    ):
        normalized = normalize_technical_token(str(item))
        if normalized:
            values.add(normalized)
    structured_product = normalize_technical_token(chunk.product or "")
    if (
        2 <= len(structured_product) <= 32
        and any(char.isalpha() for char in structured_product)
        and any(char.isdigit() for char in structured_product)
    ):
        values.add(structured_product)
    for field in (
        chunk.filename,
        chunk.relative_path,
        *chunk.catalog_path_aliases,
        chunk.product,
        chunk.series,
    ):
        for identifier in _parse_corpus_identity(str(field or "")).identifiers:
            values.add(identifier.normalized)
    return values


def _chunk_search_text(chunk: Chunk) -> str:
    return " ".join(
        str(value)
        for value in (
            chunk.text,
            chunk.section_title,
            chunk.section_path,
            chunk.filename,
            chunk.relative_path,
            " ".join(chunk.catalog_path_aliases),
            " ".join(chunk.document_configurations),
            chunk.product,
            chunk.series,
            chunk.brand,
            chunk.content_type,
            chunk.chunk_kind,
            " ".join(chunk.technical_tokens_normalized),
            " ".join(chunk.model_numbers),
            " ".join(chunk.document_model_numbers),
            " ".join(chunk.part_numbers),
        )
        if value
    )


def _term_match(term: str, text: str) -> bool:
    lowered = text.casefold()
    escaped = re.escape(term.casefold())
    if re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", lowered):
        return True
    return normalize_technical_token(term) in normalize_technical_token(text)


def _phrase_match(phrase: str, text: str) -> bool:
    cleaned = re.sub(r"\s+", " ", phrase.casefold()).strip()
    return bool(cleaned) and cleaned in re.sub(r"\s+", " ", text.casefold())


def _tokenize(text: str) -> tuple[str, ...]:
    values = []
    for raw in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-_/]{1,}", text or ""):
        for token in {raw.casefold(), normalize_technical_token(raw)}:
            if token:
                values.append(token)
    return tuple(_dedupe(values))


def _strong_lexical_term(term: str) -> bool:
    return _lexical_term_weight(term) > 0


def _lexical_term_weight(term: str) -> float:
    cleaned = str(term or "").casefold().strip()
    normalized = normalize_technical_token(cleaned)
    if len(normalized) < 3:
        return 0.0
    words = re.findall(r"[a-z0-9]+", cleaned)
    if len(words) > 1:
        return min(4.0, float(len(words) * 2))
    if cleaned in WEAK_LEXICAL_TERMS or normalized in WEAK_LEXICAL_TERMS:
        return 0.0
    return 1.0


def _weak_exact_query_phrase(text: str) -> str | None:
    terms = tuple(extract_query_terms(text))
    if (
        len(terms) < 2
        or len(terms) > 6
        or any(_strong_lexical_term(term) for term in terms)
    ):
        return None
    return " ".join(terms)


def _identifier_variant_weight(
    request: HybridRetrievalRequest,
    index: int,
) -> float:
    authoritative_prefix = len(request.exact_identifier_queries)
    return 8.0 if index < authoritative_prefix else 4.0


def _posting_key(term: str) -> str:
    return re.sub(r"\s+", " ", str(term or "").casefold()).strip()


def _query_phrases(text: str) -> tuple[str, ...]:
    lowered = re.sub(r"\s+", " ", text.casefold()).strip()
    phrases = []
    phrase_patterns = (
        r"\bmain burner\b",
        r"\bcooking grids?\b",
        r"\bflavou?r grids?\b",
        r"\bcut-?out dimensions?\b",
        r"\bvent hood\b",
        r"\bbuilt-?in grill\b",
        r"\bpressure testing\b",
        r"\bcompatibility chart\b",
    )
    for pattern in phrase_patterns:
        match = re.search(pattern, lowered)
        if match:
            phrases.append(match.group(0))
    return tuple(_dedupe(phrases))


def _section_phrases(text: str) -> tuple[str, ...]:
    cleaned = re.sub(r"\s+", " ", text.casefold()).strip()
    if not cleaned:
        return ()
    return tuple(_dedupe([cleaned, *re.findall(r"[a-z][a-z\-]+ [a-z][a-z\-]+", cleaned)]))


def _match_classes(chunk: Chunk, terms: list[str], phrases: tuple[str, ...]) -> tuple[str, ...]:
    classes = []
    searchable = _chunk_search_text(chunk)
    metadata = " ".join(
        value
        for value in (
            chunk.filename or "",
            chunk.relative_path or "",
            chunk.product or "",
            chunk.series or "",
            chunk.brand or "",
            " ".join(chunk.model_numbers),
            " ".join(chunk.part_numbers),
        )
        if value
    )
    section = " ".join(value for value in (chunk.section_title, chunk.section_path) if value)
    if any(_phrase_match(phrase, chunk.text or "") for phrase in phrases):
        classes.append("EXACT_PHRASE")
    if any(_term_match(term, chunk.text or "") for term in terms):
        classes.append("EXACT_TERM")
    if section and any(_term_match(term, section) for term in terms):
        classes.append("SECTION_HEADING")
    if metadata and any(_term_match(term, metadata) for term in terms):
        classes.append("METADATA_MATCH")
    if not classes and any(len(normalize_technical_token(term)) >= 6 and normalize_technical_token(term) in normalize_technical_token(searchable) for term in terms):
        classes.append("NORMALIZED_SUBSTRING_FALLBACK")
    return tuple(dict.fromkeys(classes))


def extract_product_scope_terms(text: str) -> ProductScopeTerms:
    lowered = re.sub(r"\s+", " ", text.casefold())
    sizes = tuple(
        sorted(
            {
                int(match.group(1))
                for match in re.finditer(
                    r"\b(\d{1,3})\s*(?:inch|inches|in\.?|\")\b",
                    lowered,
                )
                if 1 <= int(match.group(1)) <= 999
            }
        )
    )
    cutout_widths = tuple(
        sorted(
            {
                int(match.group(1))
                for match in re.finditer(
                    r"\b(?:around|about|approximately|approx\.?)\s+"
                    r"(\d{1,3})\s*(?:inch|inches|in\.?|\"|wide)\b",
                    lowered,
                )
                if 1 <= int(match.group(1)) <= 999
            }
        )
    )
    mounts = tuple(label for label, variants in MOUNT_STYLE_TERMS.items() if any(variant in lowered for variant in variants))
    fuels = tuple(label for label, variants in FUEL_TERMS.items() if any(re.search(rf"\b{re.escape(variant)}\b", lowered) for variant in variants))
    series = tuple(
        match.upper()
        for match in re.findall(
            r"\b([a-z0-9][a-z0-9-]{0,15})\s+series\b",
            lowered,
        )
    )
    return ProductScopeTerms(
        sizes_inches=sizes,
        mount_styles=mounts,
        series=tuple(dict.fromkeys(series)),
        fuel_types=fuels,
        approximate_cutout_widths=cutout_widths,
    )


def _scope_query_terms(scope: ProductScopeTerms) -> list[str]:
    terms = []
    for size in scope.sizes_inches:
        terms.extend((str(size), f"{size} inch", f"{size}in"))
    for width in scope.approximate_cutout_widths:
        terms.extend((str(width), f"{width} inch", "cutout", "width"))
    terms.extend(scope.mount_styles)
    terms.extend(scope.series)
    terms.extend(scope.fuel_types)
    return terms


def _scope_score(chunk: Chunk, scope: ProductScopeTerms) -> float:
    source = " ".join(
        value
        for value in (
            chunk.relative_path or "",
            chunk.filename or "",
            chunk.product or "",
            chunk.series or "",
            chunk.text[:1200],
        )
        if value
    ).casefold()
    score = 0.0
    for size in scope.sizes_inches:
        if re.search(rf"\b{size}\s*(?:inch|inches|in\.?|\"|built|builtin|/)", source) or f"/{size}/" in source:
            score += 4.0
    for width in scope.approximate_cutout_widths:
        if str(width) in source and ("cutout" in source or "cut-out" in source):
            score += 3.0
    for mount in scope.mount_styles:
        if mount.replace("-", "") in normalize_technical_token(source) or mount in source:
            score += 3.0
    for series in scope.series:
        if f"{series.casefold()} series" in source or f"/{series.casefold()}_series/" in source:
            score += 2.0
    return score


def _requested_attribute_score(chunk: Chunk, request: HybridRetrievalRequest) -> float:
    text = chunk.text.casefold()
    score = 0.0
    terms = set(request.lexical_terms)
    if {"cooking", "grid"}.intersection(terms) and "cooking grid" in text:
        score += 8.0
    if {"flavor", "flavour", "grid"}.intersection(terms) and ("vaporizer panel" in text or "flavor grid" in text):
        score += 8.0
    if "igniter" in terms and ("igniter" in text or "electrode" in text):
        score += 8.0
    if {"cutout", "cut-out", "dimension", "dimensions"}.intersection(terms) and ("cutout" in text or "cut-out" in text):
        score += 6.0
    if "cfm" in terms and "cfm" in text:
        score += 6.0
    return score



def _metadata_basis(chunk: Chunk, request: HybridRetrievalRequest) -> list[str]:
    basis = []
    source_values = {
        normalize_technical_token(value)
        for value in (
            chunk.document_id,
            chunk.filename,
            chunk.relative_path,
            chunk.source_path,
            *chunk.catalog_path_aliases,
        )
        if value
    }
    for label, values in (
        ("document_id", request.preferred_document_ids),
        ("filename", request.preferred_filenames),
        ("path", request.preferred_paths),
    ):
        if any(normalize_technical_token(value) in source_values for value in values if value):
            basis.append(label)
    for label, wanted, actual in (
        ("manufacturer", request.preferred_manufacturer, chunk.manufacturer),
        ("brand", request.preferred_brand, chunk.brand),
        ("series", request.preferred_series, chunk.series),
        (
            "model",
            request.preferred_model,
            " ".join(
                (
                    *chunk.model_numbers,
                    *chunk.document_model_numbers,
                    chunk.product or "",
                    chunk.relative_path or "",
                    *chunk.catalog_path_aliases,
                )
            ),
        ),
    ):
        if wanted and normalize_technical_token(wanted) in normalize_technical_token(actual or ""):
            basis.append(label)
    if request.document_type_preference and infer_document_type(chunk) == request.document_type_preference:
        basis.append("document_type")
    if request.requested_year and str(request.requested_year) == str(chunk.year or ""):
        basis.append("year")
    return basis


def _has_metadata_constraints(request: HybridRetrievalRequest) -> bool:
    return any(
        (
            request.preferred_document_ids,
            request.preferred_filenames,
            request.preferred_paths,
            request.preferred_manufacturer,
            request.preferred_brand,
            request.preferred_series,
            request.preferred_model,
            request.document_type_preference,
            request.requested_year,
            request.product_context,
        )
    )


def _semantic_filters(request: HybridRetrievalRequest) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    if request.preferred_manufacturer:
        filters["manufacturer"] = request.preferred_manufacturer
    if request.exact_identifier_queries:
        filters["exact_identifiers"] = request.exact_identifier_queries
        filters["identifier_variants"] = request.identifier_variants
    return filters


def _has_conflicting_manufacturer(
    chunk: Chunk,
    request: HybridRetrievalRequest,
) -> bool:
    wanted = normalize_technical_token(request.preferred_manufacturer or "")
    actual = normalize_technical_token(chunk.manufacturer or chunk.brand or "")
    return bool(wanted and actual and wanted != actual)


def _identity_precedence(
    item: FusedCandidate,
    request: HybridRetrievalRequest | None,
    exact_sources: set[str],
) -> tuple[int, int, int, int, int, int, int, int]:
    if request is None:
        return (0, 0, 0, 0, 0, 0, 0, 0)
    chunk = item.chunk
    exact_source = int(_source_identity(chunk) in exact_sources)
    direct_exact = int(
        any(
            identifier in normalize_technical_token(_chunk_search_text(chunk))
            for identifier in request.exact_identifier_queries
        )
    )
    manufacturer = int(
        bool(request.preferred_manufacturer)
        and normalize_technical_token(request.preferred_manufacturer or "")
        == normalize_technical_token(chunk.manufacturer or chunk.brand or "")
    )
    model = int(
        bool(request.preferred_model)
        and normalize_technical_token(request.preferred_model or "")
        in normalize_technical_token(
            " ".join(
                (
                    *chunk.model_numbers,
                    *chunk.document_model_numbers,
                    chunk.product or "",
                    chunk.relative_path or "",
                )
            )
        )
    )
    year = int(
        bool(request.requested_year)
        and str(request.requested_year) == str(chunk.year or "")
    )
    document_type = int(
        bool(request.document_type_preference)
        and infer_document_type(chunk) == request.document_type_preference
    )
    identity_constrained = bool(
        request.preferred_manufacturer or request.exact_identifier_queries
    )
    series = int(
        bool(request.preferred_series)
        and normalize_technical_token(request.preferred_series or "")
        == normalize_technical_token(chunk.series or "")
    )
    return (
        manufacturer,
        direct_exact,
        model,
        document_type if request.document_type_explicit else 0,
        series,
        document_type
        if identity_constrained and not request.document_type_explicit
        else 0,
        year if identity_constrained else 0,
        exact_source,
    )


def _diagnostics(
    request: HybridRetrievalRequest,
    channels: tuple[tuple[RetrievalChannelCandidate, ...], ...],
    fused: tuple[FusedCandidate, ...],
    started: float,
    rrf_k: int,
) -> dict[str, Any]:
    channel_counts = {channel[0].channel_name if channel else name: len(channel) for name, channel in zip(("exact_identifier", "lexical", "metadata_filter", "semantic_vector"), channels)}
    return {
        "mode": "hybrid_pdf_candidate_retrieval",
        "rrf_k": rrf_k,
        "candidate_limit": request.candidate_limit,
        "final_limit": request.final_limit,
        "semantic_query_text": request.retrieval_query.semantic_query_text,
        "exact_identifier_queries": list(
            request.retrieval_query.exact_identifier_queries
        ),
        "identifier_variants": list(
            request.retrieval_query.identifier_variants
        ),
        "vector_query_text": request.retrieval_query.semantic_query_text,
        "lexical_terms": list(request.lexical_terms),
        "technical_intent_terms": list(request.technical_intent_terms),
        "scope_terms": {
            "sizes_inches": list(request.scope_terms.sizes_inches),
            "mount_styles": list(request.scope_terms.mount_styles),
            "series": list(request.scope_terms.series),
            "fuel_types": list(request.scope_terms.fuel_types),
            "approximate_cutout_widths": list(request.scope_terms.approximate_cutout_widths),
        },
        "channel_counts": channel_counts,
        "channel_latency_ms": {
            name: max((candidate.channel_latency_ms for candidate in channel), default=0)
            for name, channel in zip(("exact_identifier", "lexical", "metadata_filter", "semantic_vector"), channels)
        },
        "total_latency_ms": int((perf_counter() - started) * 1000),
        "fused_candidates": [_fused_diagnostic(item) for item in fused],
    }


def _fused_diagnostic(item: FusedCandidate) -> dict[str, Any]:
    return {
        "rank": item.rank,
        "chunk_id": item.chunk.chunk_id,
        "source": _source_identity(item.chunk),
        "page_start": item.chunk.page_start,
        "fusion_score": item.fusion_score,
        "channels": [_candidate_provenance(candidate) for candidate in item.channel_candidates],
        "matched_identifiers": list(item.matched_identifiers),
        "matched_lexical_terms": list(item.matched_lexical_terms),
        "metadata_filter_basis": list(item.metadata_filter_basis),
    }


def _candidate_provenance(candidate: RetrievalChannelCandidate) -> dict[str, Any]:
    return {
        "channel": candidate.channel_name,
        "rank": candidate.channel_rank,
        "native_score": candidate.channel_native_score,
        "normalized_score": candidate.normalized_score,
        "matched_identifiers": list(candidate.matched_identifiers),
        "matched_lexical_terms": list(candidate.matched_lexical_terms),
        "metadata_filter_basis": list(candidate.metadata_filter_basis),
        "latency_ms": candidate.channel_latency_ms,
        "match_classes": list(candidate.match_classes),
    }


def _channel_score(item: FusedCandidate, channel_name: str) -> float:
    return max(
        (candidate.channel_native_score for candidate in item.channel_candidates if candidate.channel_name == channel_name),
        default=0.0,
    )


def _canonical_chunk_identity(chunk: Chunk) -> str:
    return chunk.chunk_id or f"{_source_identity(chunk)}:{chunk.page_start}:{chunk.chunk_index}"


def _source_identity(chunk: Chunk) -> str:
    return (chunk.relative_path or chunk.filename or chunk.document_id or "").replace("\\", "/")


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = str(value or "").strip().casefold()
        if cleaned and cleaned not in seen:
            result.append(cleaned)
            seen.add(cleaned)
    return result


def _document_type_preference(technical_needs: tuple[str, ...]) -> str | None:
    needs = set(technical_needs)
    if needs & {"parts"}:
        return "parts"
    if needs & {"dimensions", "technical_specification"}:
        return "specification"
    if needs & {"installation", "clearances", "cutout", "wiring", "warnings", "cautions"}:
        return "owner_manual"
    return None


def _explicit_document_type_request(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:cad|catalog|drawing|installation manual|owner(?:'s)? manual|"
            r"parts manual|quick start|service manual|spec(?:ification)? sheet|"
            r"specification|specifications)\b",
            text,
            re.I,
        )
    )


def _query_year(text: str) -> int | None:
    match = re.search(r"\b((?:19|20)\d{2})\b", text)
    return int(match.group(1)) if match else None


def hybrid_config_from_values(
    values: Mapping[str, str | None],
) -> HybridRetrievalConfig:
    reasons: list[str] = []
    candidate_limit = _config_int(values, "HYBRID_CANDIDATE_LIMIT", 50, minimum=5, maximum=200, reasons=reasons)
    final_limit = _config_int(values, "HYBRID_FINAL_LIMIT", 5, minimum=1, maximum=20, reasons=reasons)
    if final_limit > candidate_limit:
        reasons.append("HYBRID_FINAL_LIMIT_GT_CANDIDATE_LIMIT_DEFAULTED")
        final_limit = 5
    normal_doc = _config_int(values, "HYBRID_MAX_CANDIDATES_PER_DOCUMENT", 8, minimum=1, maximum=50, reasons=reasons)
    normal_page = _config_int(values, "HYBRID_MAX_CANDIDATES_PER_PAGE_NEIGHBORHOOD", 3, minimum=1, maximum=20, reasons=reasons)
    exact_doc = _config_int(values, "HYBRID_EXACT_MAX_CANDIDATES_PER_DOCUMENT", 12, minimum=1, maximum=80, reasons=reasons)
    exact_page = _config_int(values, "HYBRID_EXACT_MAX_CANDIDATES_PER_PAGE_NEIGHBORHOOD", 6, minimum=1, maximum=30, reasons=reasons)
    lexical_limit = _config_int(values, "HYBRID_LEXICAL_QUERY_CANDIDATE_LIMIT", 120, minimum=20, maximum=500, reasons=reasons)
    return HybridRetrievalConfig(
        candidate_limit=candidate_limit,
        final_limit=final_limit,
        rrf_k=_config_int(values, "HYBRID_RRF_K", 60, minimum=1, maximum=200, reasons=reasons),
        max_candidates_per_document=normal_doc,
        max_candidates_per_page_neighborhood=normal_page,
        exact_max_candidates_per_document=exact_doc,
        exact_max_candidates_per_page_neighborhood=exact_page,
        lexical_query_candidate_limit=lexical_limit,
        validation_reasons=tuple(reasons),
    )


def _config_int(
    values: Mapping[str, str | None],
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
    reasons: list[str],
) -> int:
    raw = values.get(name)
    if raw in (None, ""):
        return default
    try:
        value = int(str(raw).strip())
    except ValueError:
        reasons.append(f"{name}_INVALID_INT_DEFAULTED")
        return default
    if value < minimum:
        reasons.append(f"{name}_BELOW_MIN_DEFAULTED")
        return default
    if value > maximum:
        reasons.append(f"{name}_ABOVE_MAX_DEFAULTED")
        return default
    return value
