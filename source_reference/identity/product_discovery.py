from __future__ import annotations

import re
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.product_fields import (
    approved_product_facts,
    database_field_values,
    source_metadata_values,
)
from src.product_db_contract import validate_procedure_name
from src.product_taxonomy import DEFAULT_PRODUCT_TAXONOMY
from src.query_identity import QueryIdentifier, QueryIdentity, normalize_identifier, parse_query_identity
from src.runtime_contracts import (
    MAX_IDENTIFIER_VARIANTS_PER_IDENTIFIER,
    RetrievalQuery,
)
from src.technical_tokens import extract_query_terms, extract_query_tokens, normalize_technical_token


APPROVED_DISCOVERY_FIELDS = (
    "product_id",
    "product_name",
    "brand",
    "model",
    "mpn",
    "sku",
    "upc",
    "product_status",
    "stock_status",
    "score",
    "match_lane",
    "matched_field",
    "matched_identifier",
    "normalized_identifier",
    "match_reason",
    "description_excerpt",
)
DISCOVERY_LIMITATIONS = (
    "candidate discovery only",
    "identity_scope=flamy_read_model_only",
    "upstream identity not proven",
    "freshness not proven",
    "store scope unknown",
    "language scope unknown",
    "variant scope unknown",
)
UNSUPPORTED_TERMS = {
    "price", "cost", "inventory", "stock", "available", "availability",
    "delivery", "ship", "shipping", "store", "variant", "option",
}
TECHNICAL_TERMS = {
    "install", "installation", "warning", "caution", "clearance", "clearances",
    "wiring", "wire", "service", "parts", "part", "dimensions", "dimension",
    "fit", "fits", "fitment", "compatible", "compatibility", "works with",
    "burner", "manual", "procedure",
}
IDENTIFICATION_TERMS = {
    "what", "which", "identify", "lookup", "find", "model", "mpn", "upc",
    "product", "name", "brand", "strongest", "match", "candidate",
}
STOP_TERMS = {
    "about", "does", "for", "from", "have", "how", "into", "list", "need",
    "find", "identify", "lookup", "show", "that", "the", "this", "with", "what", "when", "where", "which",
    "will", "you", "your", "product", "part", "parts", "manual", "install",
    "installation", "fit", "fits", "work", "works", "compatible", "model",
    "mpn", "sku", "upc", "alias", "aka", "number",
}
PRODUCT_TYPE_TERMS = {
    "grill", "burner", "griddle", "cover", "cart", "drawer", "door", "refrigerator",
    "sideburner", "rotisserie", "island", "kit", "panel", "shelf", "hose", "regulator",
    "fireplace",
}
PRODUCT_DB_PROCEDURES = ("usp_search_products", "usp_search_products_v2")

EXACT_PRODUCT = "EXACT_PRODUCT"
ELEVATED_PRODUCT = "ELEVATED_PRODUCT"
PRODUCT_FAMILY = "PRODUCT_FAMILY"
CANDIDATE_SET = "CANDIDATE_SET"
NO_DB_MATCH = "NO_DB_MATCH"

# Import compatibility for callers that used the pre-repair names. Resolution
# results themselves use the graded state values above.
EXACT_IDENTIFIER_MATCH = EXACT_PRODUCT
NO_CANDIDATE = NO_DB_MATCH
CONFLICTING_IDENTIFIERS = CANDIDATE_SET
MODEL_FAMILY_MATCH = PRODUCT_FAMILY
MULTIPLE_PLAUSIBLE_CANDIDATES = CANDIDATE_SET
IDENTITY_UNRESOLVED = CANDIDATE_SET

PRODUCTION_RESOLUTION_STATES = frozenset(
    {EXACT_PRODUCT, ELEVATED_PRODUCT, PRODUCT_FAMILY, CANDIDATE_SET, NO_DB_MATCH}
)
RESOLVED_RESOLUTION_STATES = frozenset(
    {EXACT_IDENTIFIER_MATCH, ELEVATED_PRODUCT}
)
AMBIGUOUS_RESOLUTION_STATES = frozenset(
    {PRODUCT_FAMILY, CANDIDATE_SET}
)
UNRESOLVED_RESOLUTION_STATES = frozenset({NO_DB_MATCH})


def resolution_state_disposition(state: str | None) -> str:
    if state in RESOLVED_RESOLUTION_STATES:
        return "RESOLVED"
    if state in AMBIGUOUS_RESOLUTION_STATES:
        return "AMBIGUOUS"
    if state in UNRESOLVED_RESOLUTION_STATES:
        return "UNRESOLVED"
    return "UNKNOWN"


@dataclass(frozen=True)
class DiscoveryQuery:
    original_query: str
    retrieval_query: RetrievalQuery
    boolean_query: str
    legacy_boolean_query: str
    original_terms: tuple[str, ...]
    normalized_terms: tuple[str, ...]
    detected_identifiers: tuple[str, ...]
    identifiers: tuple[QueryIdentifier, ...]
    descriptive_terms: tuple[str, ...]
    detected_brand: str | None
    detected_product_type: str | None
    detected_brand_alias: str | None = None
    detected_series: str | None = None
    identity: QueryIdentity | None = None


@dataclass(frozen=True)
class ProductCandidate:
    product_id: int
    product_name: str | None = None
    brand: str | None = None
    model: str | None = None
    mpn: str | None = None
    sku: str | None = None
    upc: str | None = None
    product_status: str | None = None
    stock_status: str | None = None
    score: float | None = None
    match_lane: str | None = None
    matched_field: str | None = None
    matched_identifier: str | None = None
    normalized_identifier: str | None = None
    match_reason: str | None = None
    query_method: str = "usp_search_products"
    description_excerpt: str | None = None
    authoritative_aliases: tuple[str, ...] = ()
    database_fields: tuple[tuple[str, Any], ...] = ()
    approved_general_facts: tuple[tuple[str, str], ...] = ()
    source_metadata_fields: tuple[tuple[str, str], ...] = ()
    matched_identifiers: tuple[str, ...] = ()
    query_terms: tuple[str, ...] = ()
    raw_query: str | None = None
    raw_identifiers: tuple[str, ...] = ()
    normalized_query_variants: tuple[str, ...] = ()
    raw_db_values: tuple[tuple[str, str], ...] = ()
    normalized_db_values: tuple[tuple[str, str], ...] = ()
    matched_value: str | None = None
    match_type: str | None = None
    search_layer: str | None = None
    search_depth: int | None = None
    score_components: tuple[tuple[str, float], ...] = ()
    supporting_match_reasons: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    match_strength: float = 0.0
    query_token_coverage: float = 0.0
    retrieved_at: str | None = None
    limitations: tuple[str, ...] = DISCOVERY_LIMITATIONS

    @property
    def identity_scope(self) -> str:
        return "flamy_read_model_only"

    def evidence(self) -> dict[str, Any]:
        fields = {
            key: value
            for key, value in {
                "product_name": self.product_name,
                "brand": self.brand,
                "model": self.model,
                "mpn": self.mpn,
                "sku": self.sku,
                "upc": self.upc,
                "product_status": self.product_status,
                "stock_status": self.stock_status,
            }.items()
            if value not in (None, "")
        }
        return {
            "source_type": "database",
            "authority": "discovery_only",
            "source_system": "Flamy Product Read Model",
            "object": "product_details",
            "row_key": {"product_id": self.product_id},
            "identity_scope": self.identity_scope,
            "fields": fields,
            "approved_general_facts": [
                {"column": column, "value": value}
                for column, value in self.approved_general_facts
            ],
            "database_fields": [
                {"column": column, "value": value}
                for column, value in self.database_fields
            ],
            "source_metadata_fields": [
                {"column": column, "value": value}
                for column, value in self.source_metadata_fields
            ],
            "score": self.score,
            "match_lane": self.match_lane,
            "matched_field": self.matched_field,
            "matched_identifier": self.matched_identifier,
            "normalized_identifier": self.normalized_identifier,
            "match_reason": self.match_reason,
            "match_type": self.match_type,
            "search_layer": self.search_layer,
            "search_depth": self.search_depth,
            "score_components": dict(self.score_components),
            "supporting_match_reasons": list(self.supporting_match_reasons),
            "conflicts": list(self.conflicts),
            "match_strength": self.match_strength,
            "query_token_coverage": self.query_token_coverage,
            "raw_query": self.raw_query,
            "raw_identifiers": list(self.raw_identifiers),
            "normalized_query_variants": list(
                self.normalized_query_variants
            ),
            "raw_db_values": dict(self.raw_db_values),
            "normalized_db_values": dict(self.normalized_db_values),
            "query_method": self.query_method,
            "retrieved_at": self.retrieved_at,
            "freshness": "unknown",
            "store_scope": "unknown",
            "language_scope": "unknown",
            "variant_scope": "unknown",
            "limitations": list(self.limitations),
        }

    def source_ref(self, rank: int) -> dict[str, Any]:
        return self._database_source_ref(rank, authority="discovery_only")

    def answer_source_ref(self, rank: int) -> dict[str, Any]:
        return self._database_source_ref(rank, authority="answer_evidence")

    def _database_source_ref(
        self,
        rank: int,
        *,
        authority: str,
    ) -> dict[str, Any]:
        import json

        fields = self.evidence()["fields"]
        payload = {
            "source_type": "database_candidate",
            "source_system": "Flamy Product Read Model",
            "object": "product_details",
            "product_id": self.product_id,
            "identity_scope": self.identity_scope,
            "fields": fields,
            "approved_general_fields": dict(self.approved_general_facts),
            "source_metadata_fields": [column for column, _ in self.source_metadata_fields],
            "authority": authority,
            "selected": authority == "answer_evidence",
            "freshness": "unknown",
            "store_scope": "unknown",
            "language_scope": "unknown",
            "variant_scope": "unknown",
            "matched_identifiers": list(self.matched_identifiers),
            "query_terms": list(self.query_terms),
            "match_lane": self.match_lane,
            "matched_field": self.matched_field,
            "matched_identifier": self.matched_identifier,
            "normalized_identifier": self.normalized_identifier,
            "match_reason": self.match_reason,
            "match_type": self.match_type,
            "search_layer": self.search_layer,
            "search_depth": self.search_depth,
            "score_components": dict(self.score_components),
            "supporting_match_reasons": list(
                self.supporting_match_reasons
            ),
            "conflicts": list(self.conflicts),
            "query_method": self.query_method,
        }
        return {
            "chunk_id": f"product_details:{self.product_id}",
            "document_id": "flamy_ai_db.product_details",
            "filename": "Flamy Product Read Model",
            "relative_path": f"database/product_details/{self.product_id}",
            "page_start": None,
            "page_end": None,
            "score": self.score,
            "rank": rank,
            "text_preview": json.dumps(payload, sort_keys=True),
        }


@dataclass(frozen=True)
class CandidateResolution:
    state: str
    selected: ProductCandidate | None
    candidates: tuple[ProductCandidate, ...]
    reason: str
    canonical_model: str | None = None
    canonical_mpn: str | None = None
    resolution_basis: tuple[str, ...] = ()
    ambiguity_reason: str | None = None
    missing_disambiguators: tuple[str, ...] = ()
    selected_candidates: tuple[ProductCandidate, ...] = ()

    @property
    def selected_product_id(self) -> int | None:
        return self.selected.product_id if self.selected else None


def build_discovery_query(question: str) -> DiscoveryQuery:
    text = re.sub(r"\s+", " ", question or "").strip()
    if not text:
        raise ValueError("question is required")
    identity = parse_query_identity(text)
    raw_identifiers = tuple(
        _dedupe([item.raw for item in identity.identifiers])
    )
    identifiers = tuple(
        _dedupe([item.normalized for item in identity.identifiers])
    )
    brand = DEFAULT_PRODUCT_TAXONOMY.resolve_brand(text)
    series = DEFAULT_PRODUCT_TAXONOMY.resolve_series(text, brand=brand)
    product_type = _detected_product_type(text)
    descriptive_text = _without_identifier_spans(text, identity.identifiers)
    descriptive_terms: list[str] = []
    if brand:
        descriptive_terms.extend(brand.search_terms)
    if series:
        descriptive_terms.append(series.canonical_name)
    if product_type:
        descriptive_terms.append(product_type)
    excluded = []
    if brand:
        excluded.extend(brand.search_terms)
    if series:
        excluded.append(series.canonical_name)
    descriptive_terms.extend(
        _entity_terms(descriptive_text, excluded_phrases=tuple(excluded))
    )
    descriptive_terms = _dedupe(
        [term for term in descriptive_terms if term]
    )
    terms = _dedupe([*raw_identifiers, *descriptive_terms])
    terms = _dedupe([term for term in terms if term])
    normalized = tuple(_dedupe([normalize_technical_token(term) for term in terms if term]))
    required_terms = {
        _boolean_term_key(term)
        for term in (
            *((series.canonical_name,) if series else ()),
            *((product_type,) if product_type else ()),
        )
        if term
    }
    brand_term_keys = {
        _boolean_term_key(term)
        for term in (brand.search_terms if brand else ())
    }
    boolean_terms = _boolean_terms(
        [
            term
            for term in descriptive_terms
            if _boolean_term_key(term) not in brand_term_keys
        ],
        require_product_types=True,
        required_terms=required_terms,
    )
    if brand:
        boolean_terms.insert(0, _boolean_brand_group(brand))
    if not boolean_terms and not identifiers:
        boolean_terms = _boolean_terms(
            extract_query_terms(descriptive_text)[:4],
            require_product_types=True,
        )
    legacy_boolean_query = _legacy_boolean_query(
        raw_identifiers,
        descriptive_terms,
        brand=brand,
        series=series,
        product_type=product_type,
    )
    return DiscoveryQuery(
        original_query=text,
        retrieval_query=build_retrieval_query(text, identity=identity),
        boolean_query=" ".join(boolean_terms),
        legacy_boolean_query=legacy_boolean_query,
        original_terms=tuple(terms),
        normalized_terms=normalized,
        detected_identifiers=identifiers,
        identifiers=identity.identifiers,
        descriptive_terms=tuple(descriptive_terms),
        detected_brand=brand.canonical_name if brand else None,
        detected_product_type=product_type,
        detected_brand_alias=brand.matched_text if brand else None,
        detected_series=series.canonical_name if series else None,
        identity=identity,
    )


def build_retrieval_query(
    question: str,
    *,
    identity: QueryIdentity | None = None,
) -> RetrievalQuery:
    text = re.sub(r"\s+", " ", question or "").strip()
    if not text:
        raise ValueError("question is required")
    parsed = identity or parse_query_identity(text)
    exact_queries = tuple(
        _dedupe(
            [
                identifier.normalized
                for identifier in parsed.identifiers
                if identifier.normalized
            ]
        )
    )
    variants: list[str] = []
    for identifier in parsed.identifiers:
        variants.extend(
            _bounded_identifier_variants(
                identifier.raw,
                identifier.normalized,
            )
        )
    return RetrievalQuery(
        semantic_query_text=text,
        exact_identifier_queries=exact_queries,
        identifier_variants=tuple(_dedupe_casefold(variants)),
    )


def validate_product_db_procedure(name: str) -> None:
    validate_procedure_name(name, PRODUCT_DB_PROCEDURES)


def candidate_from_row(
    row: dict[str, Any],
    query: DiscoveryQuery,
    *,
    max_description_chars: int = 180,
    context_description_max_chars: int | None = None,
    retrieved_at: str | None = None,
    query_method: str = "usp_search_products",
) -> ProductCandidate:
    product_id = row.get("product_id")
    if product_id is None:
        raise ValueError("PRODUCT_ID_REQUIRED")
    description = _clean_text(row.get("product_description"))
    excerpt = description[:max_description_chars] if description else None
    normalized_evidence = _normalized_candidate_evidence(
        row,
        query,
        query_method=query_method,
    )
    candidate = ProductCandidate(
        product_id=int(product_id),
        product_name=_clean_text(row.get("product_name")),
        brand=_clean_text(row.get("brand")),
        model=_clean_text(row.get("model")),
        mpn=_clean_text(row.get("mpn")),
        sku=_clean_text(row.get("sku")),
        upc=_clean_text(row.get("upc")),
        product_status=_clean_text(row.get("product_status")),
        stock_status=_clean_text(row.get("stock_status")),
        score=_float_or_none(
            row.get("discovery_score")
            if row.get("discovery_score") is not None
            else row.get("score")
            if row.get("score") is not None
            else row.get("relevance")
        ),
        match_lane=normalized_evidence["match_lane"],
        matched_field=normalized_evidence["matched_field"],
        matched_identifier=normalized_evidence["matched_value"],
        normalized_identifier=normalized_evidence[
            "normalized_identifier"
        ],
        match_reason=normalized_evidence["match_reason"],
        query_method=query_method,
        description_excerpt=excerpt,
        authoritative_aliases=_authoritative_aliases(row.get("aka")),
        approved_general_facts=tuple(
            approved_product_facts(
                row,
                description_max_chars=context_description_max_chars,
            ).items()
        ),
        database_fields=tuple(database_field_values(row).items()),
        source_metadata_fields=tuple(source_metadata_values(row).items()),
        matched_identifiers=normalized_evidence["matched_identifiers"],
        query_terms=query.original_terms,
        raw_query=query.original_query,
        raw_identifiers=tuple(
            identifier.raw for identifier in query.identifiers
        ),
        normalized_query_variants=tuple(
            _dedupe_casefold(
                [
                    *query.retrieval_query.exact_identifier_queries,
                    *query.retrieval_query.identifier_variants,
                ]
            )
        ),
        raw_db_values=normalized_evidence["raw_db_values"],
        normalized_db_values=normalized_evidence[
            "normalized_db_values"
        ],
        matched_value=normalized_evidence["matched_value"],
        match_type=normalized_evidence["match_type"],
        search_layer=normalized_evidence["search_layer"],
        search_depth=normalized_evidence["search_depth"],
        score_components=normalized_evidence["score_components"],
        supporting_match_reasons=normalized_evidence[
            "supporting_match_reasons"
        ],
        conflicts=normalized_evidence["conflicts"],
        match_strength=normalized_evidence["match_strength"],
        query_token_coverage=normalized_evidence[
            "query_token_coverage"
        ],
        retrieved_at=retrieved_at or datetime.now(timezone.utc).isoformat(),
    )
    return candidate


def _normalized_candidate_evidence(
    row: dict[str, Any],
    query: DiscoveryQuery,
    *,
    query_method: str,
) -> dict[str, Any]:
    identity_fields = (
        "product_id",
        "product_name",
        "manufacturer",
        "brand",
        "model",
        "mpn",
        "sku",
        "upc",
        "aka",
    )
    comparison_fields = (
        *identity_fields,
        "product_type",
        "series",
        "size",
        "fuel_type",
        "categories",
        "filters",
        "attributes",
        "options",
        "configurations",
        "relationships",
    )
    raw_values = {
        field: cleaned
        for field in comparison_fields
        if (
            cleaned := _clean_text(_row_casefold_value(row, field))
        )
    }
    normalized_values = {
        field: normalize_identifier(value)
        for field, value in raw_values.items()
        if normalize_identifier(value)
    }
    aliases = _authoritative_aliases(_row_casefold_value(row, "aka"))
    for index, value in enumerate(aliases, 1):
        raw_values[f"alias_{index}"] = value
        normalized_values[f"alias_{index}"] = normalize_identifier(value)

    exact_query_values = tuple(
        _dedupe(
            [
                *query.retrieval_query.exact_identifier_queries,
                *(
                    identifier.normalized
                    for identifier in query.identifiers
                ),
            ]
        )
    )
    exact_matches: list[tuple[str, str, str]] = []
    partial_matches: list[tuple[str, str, str]] = []
    trusted_identifier_fields = (
        "product_id",
        "model",
        "mpn",
        "sku",
        "upc",
        *tuple(
            key for key in normalized_values if key.startswith("alias_")
        ),
    )
    for query_value in exact_query_values:
        normalized_query = normalize_identifier(query_value)
        if not normalized_query:
            continue
        for field in trusted_identifier_fields:
            db_value = normalized_values.get(field)
            if not db_value:
                continue
            if normalized_query == db_value:
                exact_matches.append(
                    (normalized_query, field, raw_values[field])
                )
            elif (
                len(normalized_query) >= 4
                and (
                    db_value.endswith(normalized_query)
                    or normalized_query.endswith(db_value)
                )
            ):
                partial_matches.append(
                    (normalized_query, field, raw_values[field])
                )

    query_tokens = _meaningful_comparison_tokens(query.original_query)
    candidate_text = " ".join(
        raw_values.get(field, "")
        for field in comparison_fields
        if field != "product_id"
    )
    candidate_tokens = set(_comparison_tokens(candidate_text))
    matched_tokens = tuple(
        token for token in query_tokens if token in candidate_tokens
    )
    token_coverage = (
        len(matched_tokens) / len(query_tokens)
        if query_tokens
        else 0.0
    )
    ordered_term_match = _tokens_appear_in_order(
        query_tokens,
        _comparison_tokens(candidate_text),
    )
    product_name_prefix_terms = _matching_prefix_length(
        query_tokens,
        _comparison_tokens(raw_values.get("product_name", "")),
    )
    row_score = _float_or_none(
        row.get("discovery_score")
        if row.get("discovery_score") is not None
        else row.get("score")
        if row.get("score") is not None
        else row.get("relevance")
    )
    components = {
        "exact_identifier": 1000.0 if exact_matches else 0.0,
        "partial_identifier": 180.0 if partial_matches else 0.0,
        "query_token_coverage": round(token_coverage * 100.0, 6),
        "matched_query_terms": float(len(matched_tokens) * 12),
        "ordered_query_terms": 80.0 if ordered_term_match else 0.0,
        "product_name_prefix_terms": float(
            product_name_prefix_terms * 25
        ),
        "database_score_signal": round(
            min(max(row_score or 0.0, 0.0), 1000.0) / 20.0,
            6,
        ),
    }
    match_strength = round(sum(components.values()), 6)
    supplied_field = _clean_text(row.get("matched_field"))
    supplied_value = _clean_text(
        row.get("matched_value") or row.get("matched_identifier")
    )
    supplied_lane = _clean_text(row.get("match_lane"))
    primary = (
        exact_matches[0]
        if exact_matches
        else partial_matches[0]
        if partial_matches
        else None
    )
    matched_field = supplied_field or (primary[1] if primary else None)
    matched_value = supplied_value or (primary[2] if primary else None)
    normalized_identifier = _clean_text(
        row.get("normalized_identifier")
    ) or (primary[0] if primary else None)
    reasons = []
    if exact_matches:
        reasons.append("normalized_trusted_identifier_equality")
    if partial_matches:
        reasons.append("partial_identifier_supported_by_database_value")
    if matched_tokens:
        reasons.append(
            "query_terms_matched:" + ",".join(matched_tokens)
        )
    if row_score is not None:
        reasons.append("database_score_retained")
    supplied_reason = _clean_text(row.get("match_reason"))
    if supplied_reason:
        reasons.append(supplied_reason)
    match_type = (
        "EXACT_NORMALIZED_IDENTIFIER"
        if exact_matches
        else "PARTIAL_IDENTIFIER"
        if partial_matches
        else "DESCRIPTIVE_EVIDENCE"
        if matched_tokens
        else "UNQUALIFIED_ROW"
    )
    match_lane = supplied_lane
    if match_lane is None and exact_matches:
        match_lane = f"EXACT_{exact_matches[0][1].upper()}"
    search_layer = _clean_text(row.get("search_layer")) or (
        "exact_lookup"
        if query_method == "exact_identifier_lookup"
        else f"stored_procedure:{query_method}"
    )
    search_depth = _int_or_none(row.get("search_depth"))
    matched_identifiers = tuple(
        _dedupe(
            [
                item[0]
                for item in exact_matches
            ]
        )
    )
    return {
        "match_lane": match_lane,
        "matched_field": matched_field,
        "matched_value": matched_value,
        "normalized_identifier": normalized_identifier,
        "match_reason": supplied_reason
        or (reasons[0] if reasons else None),
        "matched_identifiers": matched_identifiers,
        "raw_db_values": tuple(raw_values.items()),
        "normalized_db_values": tuple(normalized_values.items()),
        "match_type": match_type,
        "search_layer": search_layer,
        "search_depth": search_depth,
        "score_components": tuple(components.items()),
        "supporting_match_reasons": tuple(dict.fromkeys(reasons)),
        "conflicts": (),
        "match_strength": match_strength,
        "query_token_coverage": round(token_coverage, 6),
    }


def resolve_candidates(
    candidates: tuple[ProductCandidate, ...],
    query: DiscoveryQuery,
) -> CandidateResolution:
    if not candidates:
        return _resolution(
            NO_DB_MATCH,
            None,
            (),
            "NO_DATABASE_CANDIDATES",
            missing=("product_identity",),
        )
    ranked_candidates = tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                candidate.match_strength,
                candidate.query_token_coverage,
                candidate.score or 0.0,
            ),
            reverse=True,
        )
    )
    multi_identifier = _resolved_multi_identifier_candidates(
        ranked_candidates,
        query,
    )
    if multi_identifier:
        return _resolution(
            EXACT_PRODUCT,
            multi_identifier[0],
            ranked_candidates,
            "MULTIPLE_EXACT_IDENTIFIERS_RESOLVED",
            basis=(
                "exact_identifier_match",
                "multiple_exact_subjects_retained",
            ),
            selected_candidates=multi_identifier,
        )
    if _conflicting_identifiers(
        ranked_candidates,
        query.detected_identifiers,
    ):
        return _resolution(
            CANDIDATE_SET,
            None,
            ranked_candidates,
            "IDENTIFIERS_MATCH_DIFFERENT_ROWS",
            ambiguity="conflicting identifiers",
        )
    family_candidates = _family_resolution_candidates(
        ranked_candidates,
        query,
    )
    if family_candidates:
        return _resolution(
            PRODUCT_FAMILY,
            None,
            family_candidates[:5],
            "SHARED_FAMILY_IDENTITY_WITH_UNRESOLVED_VARIANTS",
            ambiguity="product family",
            missing=_family_missing_discriminators(family_candidates),
            selected_candidates=family_candidates[:5],
        )
    if _family_like_query_without_exact_match(
        ranked_candidates,
        query,
    ):
        return _resolution(
            PRODUCT_FAMILY,
            None,
            ranked_candidates[:5],
            "FAMILY_IDENTIFIER_REQUIRES_DISAMBIGUATION",
            ambiguity="product family",
            missing=("exact_model", "configuration"),
        )
    exact = tuple(
        candidate
        for candidate in ranked_candidates
        if candidate.matched_identifiers
    )
    if len(exact) == 1:
        return _exact_resolution(
            exact[0],
            ranked_candidates,
            "ONE_EXACT_IDENTIFIER_MATCH",
        )
    if len(exact) > 1:
        strongest_priority = max(_exact_match_priority(candidate) for candidate in exact)
        strongest = tuple(
            candidate
            for candidate in exact
            if _exact_match_priority(candidate) == strongest_priority
        )
        if len(strongest) == 1:
            return _exact_resolution(
                strongest[0],
                ranked_candidates,
                "STRONGEST_EXACT_IDENTIFIER_LANE",
            )
        materially_same = _same_candidate_identity(strongest)
        if materially_same:
            return _exact_resolution(
                strongest[0],
                ranked_candidates,
                "DUPLICATE_READ_MODEL_ROWS_SAME_IDENTITY",
            )
        return _resolution(
            CANDIDATE_SET,
            None,
            strongest,
            "MULTIPLE_EXACT_IDENTIFIER_MATCHES",
            ambiguity="multiple exact identifier matches",
            missing=("exact_model", "configuration"),
        )
    if len(ranked_candidates) == 1:
        candidate = ranked_candidates[0]
        if _eligible_for_elevation(candidate):
            return _resolution(
                ELEVATED_PRODUCT,
                candidate,
                ranked_candidates,
                "ONE_DOMINANT_DATABASE_CANDIDATE",
                basis=_elevation_basis(candidate),
            )
        return _resolution(
            CANDIDATE_SET,
            None,
            ranked_candidates,
            "ONE_DATABASE_CANDIDATE_WITHOUT_SUFFICIENT_MATCH_EVIDENCE",
            ambiguity="insufficient observable match evidence",
            missing=("product_identity",),
        )
    top, second = ranked_candidates[0], ranked_candidates[1]
    if _materially_dominant(top, second):
        return _resolution(
            ELEVATED_PRODUCT,
            top,
            ranked_candidates,
            "MATERIALLY_DOMINANT_CANDIDATE_EVIDENCE",
            basis=_elevation_basis(top),
        )
    return _resolution(
        CANDIDATE_SET,
        None,
        ranked_candidates[:5],
        "NO_MATERIAL_EVIDENCE_SEPARATION",
        ambiguity="multiple materially plausible products",
        missing=("exact_model", "configuration"),
    )


def is_technical_question(question: str) -> bool:
    lower = question.casefold()
    return any(re.search(rf"\b{re.escape(term)}\b", lower) for term in TECHNICAL_TERMS)


def is_unsupported_question(question: str) -> bool:
    lower = question.casefold()
    return any(re.search(rf"\b{re.escape(term)}\b", lower) for term in UNSUPPORTED_TERMS)


def is_identification_question(question: str) -> bool:
    lower = question.casefold()
    return any(re.search(rf"\b{re.escape(term)}\b", lower) for term in IDENTIFICATION_TERMS)


def enrich_retrieval_query(
    query: RetrievalQuery,
    candidates: tuple[ProductCandidate, ...],
) -> RetrievalQuery:
    authoritative = tuple(
        candidate
        for candidate in candidates
        if _manufacturer_standard_identifier(candidate)
    )
    if not authoritative:
        return query
    identity = parse_query_identity(query.semantic_query_text)
    candidate_by_identifier: dict[str, ProductCandidate] = {}
    for identifier in identity.identifiers:
        matching = tuple(
            candidate
            for candidate in authoritative
            if identifier.normalized in candidate.matched_identifiers
            or identifier.normalized in _candidate_identifier_keys(candidate)
        )
        if len({candidate.product_id for candidate in matching}) == 1:
            candidate_by_identifier[identifier.normalized] = matching[0]
        elif len(authoritative) == 1:
            candidate_by_identifier[identifier.normalized] = authoritative[0]

    replacements: list[tuple[int, int, str]] = []
    standards: list[str] = []
    aid_variants: list[str] = []
    for identifier in identity.identifiers:
        candidate = candidate_by_identifier.get(identifier.normalized)
        standard = (
            _manufacturer_standard_identifier(candidate)
            if candidate is not None
            else None
        )
        if standard:
            standards.append(standard)
            replacements.append(
                (identifier.span_start, identifier.span_end, standard)
            )
        values = [
            identifier.raw,
            identifier.normalized,
            *(
                _candidate_retrieval_aliases(candidate)
                if candidate
                else ()
            ),
        ]
        aid_variants.extend(
            _bounded_identifier_variants(
                *values,
                limit=(
                    MAX_IDENTIFIER_VARIANTS_PER_IDENTIFIER
                    - (1 if standard else 0)
                ),
            )
        )

    if not identity.identifiers:
        for candidate in authoritative:
            standard = _manufacturer_standard_identifier(candidate)
            if not standard:
                continue
            standards.append(standard)
            aid_variants.extend(
                _bounded_identifier_variants(
                    normalize_identifier(standard),
                    *_candidate_retrieval_aliases(candidate),
                    limit=MAX_IDENTIFIER_VARIANTS_PER_IDENTIFIER - 1,
                )
            )

    semantic_text = query.semantic_query_text
    for start, end, replacement in sorted(replacements, reverse=True):
        semantic_text = (
            semantic_text[:start] + replacement + semantic_text[end:]
        )
    semantic_text = re.sub(
        r"\bmanual\s+for\b",
        "manual documentation for",
        semantic_text,
        count=1,
        flags=re.I,
    )
    standards = _dedupe_casefold(standards)
    if not replacements and standards:
        missing = [
            standard
            for standard in standards
            if normalize_identifier(standard)
            not in normalize_identifier(semantic_text)
        ]
        if missing:
            semantic_text = (
                f"{semantic_text} "
                + " ".join(missing)
            )
    exact_queries = _dedupe(
        [
            *query.exact_identifier_queries,
            *(normalize_identifier(value) for value in standards),
        ]
    )
    return RetrievalQuery(
        semantic_query_text=semantic_text,
        exact_identifier_queries=tuple(exact_queries),
        identifier_variants=tuple(
            _dedupe_casefold(
                [
                    *standards,
                    *aid_variants,
                    *query.identifier_variants,
                ]
            )
        ),
        product_facets=tuple(
            _dedupe_facets(
                [
                    *query.product_facets,
                    *(
                        facet
                        for candidate in candidates
                        for facet in _candidate_pdf_facets(candidate)
                    ),
                ]
            )
        ),
    )


def enriched_pdf_query(
    question: str,
    candidate: ProductCandidate | None,
) -> str:
    query = build_retrieval_query(question)
    return enrich_retrieval_query(
        query,
        (candidate,) if candidate else (),
    ).semantic_query_text


def _exact_resolution(candidate: ProductCandidate, candidates: tuple[ProductCandidate, ...], reason: str) -> CandidateResolution:
    return _resolution(
        EXACT_IDENTIFIER_MATCH,
        candidate,
        candidates,
        reason,
        basis=("exact_identifier_match", "unique_exact_subject_retained"),
        selected_candidates=(candidate,),
    )


def _resolution(
    state: str,
    selected: ProductCandidate | None,
    candidates: tuple[ProductCandidate, ...],
    reason: str,
    *,
    basis: tuple[str, ...] = (),
    ambiguity: str | None = None,
    missing: tuple[str, ...] = (),
    selected_candidates: tuple[ProductCandidate, ...] = (),
) -> CandidateResolution:
    return CandidateResolution(
        state=state,
        selected=selected,
        candidates=candidates,
        reason=reason,
        canonical_model=selected.model if selected else None,
        canonical_mpn=selected.mpn if selected else None,
        resolution_basis=basis,
        ambiguity_reason=ambiguity,
        missing_disambiguators=missing,
        selected_candidates=(
            selected_candidates
            or ((selected,) if selected is not None else ())
        ),
    )


def _family_like_query_without_exact_match(
    candidates: tuple[ProductCandidate, ...],
    query: DiscoveryQuery,
) -> bool:
    identity = query.identity
    if identity is None or not any(item.family_like for item in identity.identifiers):
        return False
    return not any(candidate.matched_identifiers for candidate in candidates)


def _family_resolution_candidates(
    candidates: tuple[ProductCandidate, ...],
    query: DiscoveryQuery,
) -> tuple[ProductCandidate, ...]:
    query_key = normalize_identifier(query.original_query)
    if not query_key:
        return ()
    grouped: dict[tuple[str, str], list[ProductCandidate]] = {}
    for candidate in candidates:
        normalized_values = dict(candidate.normalized_db_values)
        for field in ("model", "mpn", "sku", "upc"):
            value = normalized_values.get(field)
            if value == query_key:
                grouped.setdefault((field, value), []).append(candidate)
    family = max(grouped.values(), key=len, default=[])
    if len({candidate.product_id for candidate in family}) < 2:
        return ()
    differing_identifiers = {
        (
            normalize_identifier(candidate.mpn or ""),
            normalize_identifier(candidate.sku or ""),
            normalize_identifier(candidate.upc or ""),
        )
        for candidate in family
    }
    return tuple(family) if len(differing_identifiers) > 1 else ()


def _family_missing_discriminators(
    candidates: tuple[ProductCandidate, ...],
) -> tuple[str, ...]:
    fields = []
    for field, label in (
        ("mpn", "mpn"),
        ("sku", "sku"),
        ("upc", "upc"),
    ):
        values = {
            normalize_identifier(str(getattr(candidate, field) or ""))
            for candidate in candidates
            if getattr(candidate, field)
        }
        if len(values) > 1:
            fields.append(label)
    return tuple(fields or ("configuration",))


def _eligible_for_elevation(candidate: ProductCandidate) -> bool:
    components = dict(candidate.score_components)
    return (
        not candidate.conflicts
        and candidate.query_token_coverage >= 0.6
        and (
            components.get("partial_identifier", 0.0) > 0
            or components.get("ordered_query_terms", 0.0) > 0
            or components.get("matched_query_terms", 0.0) >= 24.0
        )
    )


def _materially_dominant(
    top: ProductCandidate,
    second: ProductCandidate,
) -> bool:
    if not _eligible_for_elevation(top):
        return False
    top_components = dict(top.score_components)
    second_components = dict(second.score_components)
    evidence_margin = top.match_strength - second.match_strength
    coverage_margin = (
        top.query_token_coverage - second.query_token_coverage
    )
    ordered_advantage = (
        top_components.get("ordered_query_terms", 0.0) > 0
        and second_components.get("ordered_query_terms", 0.0) == 0
    )
    identifier_advantage = (
        top_components.get("partial_identifier", 0.0)
        > second_components.get("partial_identifier", 0.0)
    )
    return (
        evidence_margin >= 20.0
        or coverage_margin >= 0.25
        or ordered_advantage
        or identifier_advantage
    )


def _elevation_basis(candidate: ProductCandidate) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                "observable_candidate_evidence",
                *candidate.supporting_match_reasons,
                "no_material_identity_conflict",
            )
        )
    )


def _identifier_terms(text: str) -> list[str]:
    hyphenated = re.findall(r"\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+\b", text)
    compact_hyphenated = {_identifier_key(value) for value in hyphenated}
    tokens = [
        token for token in extract_query_tokens(text)
        if _identifier_key(token) not in compact_hyphenated
        and not re.match(r"^(?:THE|A|AN)\d", token, re.I)
    ]
    found = list(hyphenated)
    found.extend(tokens)
    found.extend(re.findall(r"\b\d{8,14}\b", text))
    return found


def _without_identifier_spans(
    text: str,
    identifiers: tuple[QueryIdentifier, ...],
) -> str:
    if not identifiers:
        return text
    characters = list(text)
    for identifier in identifiers:
        for index in range(identifier.span_start, identifier.span_end):
            if 0 <= index < len(characters):
                characters[index] = " "
    return re.sub(r"\s+", " ", "".join(characters)).strip()


def _entity_terms(text: str, *, excluded_phrases: tuple[str, ...] = ()) -> list[str]:
    excluded_tokens = {
        token.casefold()
        for phrase in excluded_phrases
        for token in extract_query_terms(phrase)
    }
    terms = []
    for term in extract_query_terms(text):
        lowered = term.casefold()
        if lowered in STOP_TERMS or lowered in excluded_tokens:
            continue
        if len(term) < 3:
            continue
        terms.append(term)
    return terms[:8]


def _detected_product_type(text: str) -> str | None:
    lower = text.casefold()
    for term in PRODUCT_TYPE_TERMS:
        if re.search(rf"\b{re.escape(term)}s?\b", lower):
            return term
    return None


def _boolean_terms(
    terms: list[str] | tuple[str, ...],
    *,
    require_product_types: bool = True,
    required_terms: set[str] | None = None,
) -> list[str]:
    required_terms = required_terms or set()
    rendered: list[str] = []
    for term in terms:
        cleaned = str(term).strip()
        if not cleaned:
            continue
        required_term = _boolean_term_key(cleaned) in required_terms
        multiword = bool(re.search(r"\s", cleaned))
        if re.search(r"[^A-Za-z0-9]", cleaned):
            pieces = [piece for piece in re.split(r"[^A-Za-z0-9]+", cleaned) if len(piece) >= 2]
            required = next((piece for piece in pieces if len(piece) >= 3), "")
            if required and not multiword and (
                required_term
                or _requires_boolean_term(cleaned, require_product_types=require_product_types)
            ):
                rendered.append(f"+{required}*")
            phrase_prefix = "+" if required_term and multiword else ""
            rendered.append(f'{phrase_prefix}"{cleaned}"')
            compact = re.sub(r"[^A-Za-z0-9]", "", cleaned)
            if compact and compact.casefold() != cleaned.casefold():
                rendered.append(f"{compact}*")
            for piece in pieces:
                if piece != required:
                    rendered.append(f"{piece}*")
        else:
            prefix = "+" if (
                required_term
                or _requires_boolean_term(cleaned, require_product_types=require_product_types)
            ) else ""
            rendered.append(f"{prefix}{cleaned}*")
    return _dedupe(rendered)


def _legacy_boolean_query(
    raw_identifiers: tuple[str, ...],
    descriptive_terms: list[str],
    *,
    brand: Any,
    series: Any,
    product_type: str | None,
) -> str:
    terms = _dedupe([*raw_identifiers, *descriptive_terms])
    brand_term_keys = {
        _boolean_term_key(term)
        for term in (brand.search_terms if brand else ())
    }
    required_terms = {
        _boolean_term_key(term)
        for term in (
            *raw_identifiers,
            *((series.canonical_name,) if series else ()),
            *((product_type,) if product_type and not raw_identifiers else ()),
        )
        if term
    }
    rendered = _boolean_terms(
        [
            term
            for term in terms
            if _boolean_term_key(term) not in brand_term_keys
        ],
        require_product_types=not raw_identifiers,
        required_terms=required_terms,
    )
    if brand:
        rendered.insert(0, _boolean_brand_group(brand))
    return " ".join(rendered)


def _boolean_brand_group(brand: Any) -> str:
    forms: list[str] = []
    for term in brand.search_terms:
        cleaned = str(term).strip()
        if not cleaned:
            continue
        if re.search(r"\s", cleaned):
            forms.append(f'"{cleaned}"')
            compact = re.sub(r"[^A-Za-z0-9]", "", cleaned)
            if compact:
                forms.append(f"{compact}*")
        else:
            forms.append(f"{cleaned}*")
    return f"+({' '.join(_dedupe(forms))})"


def _matched_identifiers(row: dict[str, Any], query: DiscoveryQuery) -> tuple[str, ...]:
    match_lane = str(row.get("match_lane") or "").upper()
    returned_normalized = normalize_identifier(
        str(row.get("normalized_identifier") or "")
    )
    if match_lane.startswith("EXACT_") and returned_normalized:
        matches = [
            identifier
            for identifier in query.detected_identifiers
            if normalize_identifier(identifier) == returned_normalized
        ]
        if matches:
            return tuple(_dedupe(matches))
    values = {
        _identifier_key(row.get("model")),
        _identifier_key(row.get("mpn")),
        _identifier_key(row.get("sku")),
        _identifier_key(row.get("upc")),
        _identifier_key(row.get("product_id")),
    }
    matches = []
    for identifier in query.detected_identifiers:
        key = _identifier_key(identifier)
        if key and key in values:
            matches.append(identifier)
    return tuple(_dedupe(matches))


def _conflicting_identifiers(
    candidates: tuple[ProductCandidate, ...],
    identifiers: tuple[str, ...],
) -> bool:
    if len(identifiers) < 2:
        return False
    matched_rows = {
        candidate.product_id
        for candidate in candidates
        if candidate.matched_identifiers
    }
    return len(matched_rows) > 1 and all(
        any(identifier in candidate.matched_identifiers for candidate in candidates)
        for identifier in identifiers
    )


def _resolved_multi_identifier_candidates(
    candidates: tuple[ProductCandidate, ...],
    query: DiscoveryQuery,
) -> tuple[ProductCandidate, ...]:
    identifiers = query.retrieval_query.exact_identifier_queries
    if len(identifiers) < 2:
        return ()
    identifier_types = {
        identifier.identifier_type
        for identifier in query.identifiers
        if identifier.normalized in identifiers
    }
    if len(identifier_types) > 1:
        return ()
    selected: list[ProductCandidate] = []
    for identifier in identifiers:
        matches = tuple(
            candidate
            for candidate in candidates
            if identifier in candidate.matched_identifiers
        )
        unique = {
            candidate.product_id: candidate for candidate in matches
        }
        if len(unique) != 1:
            return ()
        candidate = next(iter(unique.values()))
        if all(
            existing.product_id != candidate.product_id
            for existing in selected
        ):
            selected.append(candidate)
    return tuple(selected)


def _same_candidate_identity(candidates: tuple[ProductCandidate, ...]) -> bool:
    keys = {
        (
            candidate.product_id,
            _identifier_key(candidate.model),
            _identifier_key(candidate.mpn),
            _identifier_key(candidate.sku),
            _identifier_key(candidate.upc),
        )
        for candidate in candidates
    }
    return len(keys) == 1


def _candidate_identifier_keys(
    candidate: ProductCandidate,
) -> set[str]:
    return {
        normalized
        for value in (
            candidate.model,
            candidate.mpn,
            candidate.sku,
            candidate.upc,
            *candidate.authoritative_aliases,
        )
        if (normalized := normalize_identifier(str(value or "")))
    }


def _manufacturer_standard_identifier(
    candidate: ProductCandidate | None,
) -> str | None:
    if candidate is None:
        return None
    for value in (
        candidate.model,
        candidate.mpn,
        candidate.upc,
        *candidate.authoritative_aliases,
    ):
        cleaned = str(value or "").strip()
        if cleaned:
            return cleaned
    return None


def _candidate_retrieval_aliases(
    candidate: ProductCandidate,
) -> tuple[str, ...]:
    standard = _manufacturer_standard_identifier(candidate)
    return tuple(
        _dedupe_casefold(
            [
                str(value or "").strip()
                for value in (
                    candidate.model,
                    candidate.mpn,
                    candidate.sku,
                    candidate.upc,
                    *candidate.authoritative_aliases,
                )
                if str(value or "").strip()
                and str(value or "").strip().casefold()
                != str(standard or "").casefold()
            ]
        )
    )


def _candidate_pdf_facets(
    candidate: ProductCandidate,
) -> tuple[tuple[str, str], ...]:
    facts = dict(candidate.approved_general_facts)
    facets = []
    for field, value in (
        ("manufacturer", facts.get("manufacturer")),
        ("brand", candidate.brand),
        ("model", candidate.model),
        ("mpn", candidate.mpn),
        ("sku", candidate.sku),
        ("upc", candidate.upc),
        ("product_name", candidate.product_name),
        ("series", facts.get("series")),
        ("product_type", facts.get("product_type")),
        ("size", facts.get("size")),
        ("fuel_type", facts.get("fuel_type")),
        ("categories", facts.get("categories")),
        ("filters", facts.get("filters")),
        ("attributes", facts.get("attributes")),
        ("options", facts.get("options")),
        ("configurations", facts.get("configurations")),
        ("relationships", facts.get("relationships")),
    ):
        cleaned = _clean_text(value)
        if cleaned:
            facets.append((field, cleaned))
    return tuple(_dedupe_facets(facets))


def _dedupe_facets(
    values: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    result = []
    seen = set()
    for field, value in values:
        key = (field.casefold(), value.casefold())
        if key not in seen:
            result.append((field, value))
            seen.add(key)
    return result


def _authoritative_aliases(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    parsed: Any = value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("[", "{")):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = text
        else:
            parsed = text
    if isinstance(parsed, dict):
        values = list(parsed.values())
    elif isinstance(parsed, (list, tuple, set, frozenset)):
        values = list(parsed)
    else:
        values = re.split(r"[,;|\n]", str(parsed))
    return tuple(
        _dedupe_casefold(
            [
                str(item).strip().strip("[]\"'")
                for item in values
                if str(item).strip().strip("[]\"'")
            ]
        )
    )


def _bounded_identifier_variants(
    *values: str,
    limit: int = MAX_IDENTIFIER_VARIANTS_PER_IDENTIFIER,
) -> list[str]:
    return _dedupe_casefold(
        [str(value or "").strip() for value in values if str(value or "").strip()]
    )[: max(0, limit)]


def _dedupe_casefold(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value or "").strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            result.append(cleaned)
            seen.add(key)
    return result


def _exact_match_priority(candidate: ProductCandidate) -> int:
    lane = (candidate.match_lane or "").upper()
    if lane in {"EXACT_MODEL", "EXACT_MPN", "EXACT_SKU", "EXACT_UPC"}:
        return 1000
    if lane in {"EXACT_ALIAS", "EXACT_AKA"}:
        return 950
    if candidate.matched_identifiers:
        return 900
    return 0


def _identifier_key(value: Any) -> str:
    return normalize_identifier(str(value or "")).casefold()


def _requires_boolean_term(value: str, *, require_product_types: bool = True) -> bool:
    lowered = value.casefold()
    if re.fullmatch(r"\d{2,4}", value.strip()):
        return False
    if require_product_types and lowered in PRODUCT_TYPE_TERMS:
        return True
    return False


def _boolean_term_key(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").casefold()).strip()


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def _row_casefold_value(row: dict[str, Any], field: str) -> Any:
    if field in row:
        return row[field]
    lowered = field.casefold()
    for key, value in row.items():
        if str(key).casefold() == lowered:
            return value
    return None


def _comparison_tokens(value: str) -> list[str]:
    return [
        token.casefold()
        for token in re.findall(r"[A-Za-z0-9]+", value or "")
        if token
    ]


def _meaningful_comparison_tokens(value: str) -> tuple[str, ...]:
    return tuple(
        _dedupe(
            [
                token
                for token in _comparison_tokens(value)
                if token not in STOP_TERMS
            ]
        )
    )


def _tokens_appear_in_order(
    expected: tuple[str, ...],
    actual: list[str],
) -> bool:
    if len(expected) < 2:
        return False
    position = 0
    for token in actual:
        if token == expected[position]:
            position += 1
            if position == len(expected):
                return True
    return False


def _matching_prefix_length(
    expected: tuple[str, ...],
    actual: list[str],
) -> int:
    matched = 0
    for expected_token, actual_token in zip(expected, actual):
        if expected_token != actual_token:
            break
        matched += 1
    return matched


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _dedupe(values: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result
