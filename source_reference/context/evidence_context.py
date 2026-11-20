import re
from collections import defaultdict
from fractions import Fraction
from typing import Any

from src.evidence_models import (
    EvidenceDecision,
    EvidenceGroup,
    EvidenceItem,
    EvidencePackage,
)
from src.models import Chunk
from src.product_applicability import ProductApplicabilityContext
from src.query_intent import QueryIntent, classify_query_intent
from src.retrieval import RankedChunk, RankedRetrieval
from src.retrieval_policy import chunk_year
from src.technical_tokens import normalize_technical_token


EXPANDABLE_INTENTS = {
    "dimensions_specification",
    "exact_part_lookup",
    "parts_lookup",
    "installation_warning",
    "compatibility_fitment",
    "troubleshooting",
}


def build_evidence_package(
    question: str,
    retrieval: RankedRetrieval,
    *,
    product_context: ProductApplicabilityContext | None = None,
) -> EvidencePackage:
    intent = classify_query_intent(question)
    candidates = retrieval.candidates or retrieval.chunks
    if not candidates:
        decision = EvidenceDecision(
            mode="insufficient_evidence",
            sufficient=False,
            confidence="none",
            reason="NO_SELECTED_EVIDENCE",
        )
        return EvidencePackage(
            question=question,
            intent=intent,
            selected=(),
            groups=(),
            decision=decision,
            diagnostics=_diagnostics(
                intent,
                (),
                (),
                retrieval,
                decision,
                {},
                product_context,
            ),
        )

    groups = _build_groups(candidates, intent)
    best_group = groups[0]
    selected_items = _select_items(best_group, candidates, intent)
    selected = tuple(item.ranked for item in selected_items)
    decision = decide_evidence(
        intent,
        retrieval,
        selected,
        product_context=product_context,
    )
    reasons = {item.ranked.chunk.chunk_id: item.inclusion_reason for item in selected_items}
    diagnostics = _diagnostics(
        intent,
        selected,
        groups,
        retrieval,
        decision,
        reasons,
        product_context,
    )
    return EvidencePackage(
        question=question,
        intent=intent,
        selected=selected,
        groups=groups,
        decision=decision,
        diagnostics=diagnostics,
    )


def decide_evidence(
    intent: QueryIntent,
    retrieval: RankedRetrieval,
    selected: tuple[RankedChunk, ...],
    *,
    product_context: ProductApplicabilityContext | None = None,
) -> EvidenceDecision:
    if not selected:
        return EvidenceDecision(
            mode="insufficient_evidence",
            sufficient=False,
            confidence="none",
            reason="NO_SELECTED_EVIDENCE",
        )
    if retrieval.low_confidence and not _has_strong_match(selected):
        mode = "clarification" if intent.safety_sensitive else "insufficient_evidence"
        return EvidenceDecision(
            mode=mode,
            sufficient=False,
            confidence="low",
            reason=retrieval.low_confidence_reason or "LOW_CONFIDENCE",
        )
    if intent.requires_exact_identifier and not _selected_contains_identifier(
        selected,
        intent.identifiers,
        product_context=product_context,
    ):
        return EvidenceDecision(
            mode="clarification",
            sufficient=False,
            confidence="low",
            reason="QUERY_IDENTIFIER_NOT_IN_SELECTED_EVIDENCE",
            missing_fields=("identifier",),
        )
    if intent.intent_type == "compatibility_fitment" and not _has_fitment_support(
        selected, intent
    ):
        return EvidenceDecision(
            mode="clarification",
            sufficient=False,
            confidence="low",
            reason="FITMENT_SUPPORT_NOT_FOUND",
            missing_fields=("compatibility",),
        )
    conflicts = _dimension_conflicts(selected, intent)
    if conflicts:
        return EvidenceDecision(
            mode="conflicting_evidence",
            sufficient=False,
            confidence="low",
            reason="CONFLICTING_DIMENSIONS",
            conflicting_fields=conflicts,
        )
    confidence = (
        "high"
        if _has_strong_match(selected)
        or (
            intent.requires_exact_identifier
            and _selected_contains_identifier(
                selected,
                intent.identifiers,
                product_context=product_context,
            )
        )
        else "medium"
    )
    if intent.safety_sensitive and confidence != "high":
        return EvidenceDecision(
            mode="qualified_answer",
            sufficient=True,
            confidence=confidence,
            reason="SAFETY_SENSITIVE_QUALIFIED",
        )
    return EvidenceDecision(
        mode="direct_answer",
        sufficient=True,
        confidence=confidence,
    )


def _build_groups(
    candidates: tuple[RankedChunk, ...],
    intent: QueryIntent,
) -> tuple[EvidenceGroup, ...]:
    buckets: dict[tuple[str, str, str], list[RankedChunk]] = defaultdict(list)
    for ranked in candidates:
        chunk = ranked.chunk
        source = _source(ranked)
        section = chunk.section_path or chunk.section_title or ""
        identifier_key = ",".join(_matched_identifiers(ranked, intent))
        buckets[(source, section, identifier_key)].append(ranked)

    groups = []
    for (source, section, identifier_key), ranked_items in buckets.items():
        items = tuple(
            EvidenceItem(
                chunk=item.chunk,
                ranked=item,
                source=source,
                page_start=item.chunk.page_start,
                page_end=item.chunk.page_end,
                inclusion_reason="candidate_group",
            )
            for item in sorted(ranked_items, key=_document_order)
        )
        identifiers = tuple(
            sorted(
                {
                    identifier
                    for item in ranked_items
                    for identifier in _matched_identifiers(item, intent)
                }
            )
        )
        score = _group_score(ranked_items, intent)
        reason = "identifier_group" if identifier_key else "source_section_group"
        if section:
            reason = f"{reason}:section"
        groups.append(
            EvidenceGroup(
                source=source,
                pages=tuple(sorted({item.chunk.page_start for item in ranked_items})),
                items=items,
                matched_identifiers=identifiers,
                score=score,
                group_reason=reason,
            )
        )
    return tuple(sorted(groups, key=lambda group: group.score, reverse=True))


def _select_items(
    group: EvidenceGroup,
    candidates: tuple[RankedChunk, ...],
    intent: QueryIntent,
) -> tuple[EvidenceItem, ...]:
    anchor = max((item.ranked for item in group.items), key=lambda item: item.final_score)
    selected: dict[str, EvidenceItem] = {}

    def add(ranked: RankedChunk, reason: str) -> None:
        chunk_id = ranked.chunk.chunk_id
        if chunk_id not in selected:
            selected[chunk_id] = EvidenceItem(
                chunk=ranked.chunk,
                ranked=ranked,
                source=_source(ranked),
                page_start=ranked.chunk.page_start,
                page_end=ranked.chunk.page_end,
                inclusion_reason=reason,
            )

    for item in group.items:
        if item.ranked.chunk.page_start == anchor.chunk.page_start:
            add(item.ranked, "coherent_group")

    for ranked in candidates:
        if _source(ranked) != _source(anchor):
            continue
        if ranked.chunk.page_start == anchor.chunk.page_start and abs(
            ranked.chunk.chunk_index - anchor.chunk.chunk_index
        ) <= 1:
            add(ranked, "same_page_adjacent")
        elif intent.intent_type in EXPANDABLE_INTENTS and _close_to_anchor(ranked, anchor):
            add(ranked, "controlled_expansion")

    return tuple(sorted(selected.values(), key=lambda item: _document_order(item.ranked)))


def _close_to_anchor(candidate: RankedChunk, anchor: RankedChunk) -> bool:
    same_or_next_page = abs(candidate.chunk.page_start - anchor.chunk.page_start) <= 2
    close_index = abs(candidate.chunk.chunk_index - anchor.chunk.chunk_index) <= 3
    return same_or_next_page and close_index


def _group_score(ranked_items: list[RankedChunk], intent: QueryIntent) -> float:
    best = max(item.final_score for item in ranked_items)
    best_rank = min(item.rank for item in ranked_items if item.rank > 0)
    identifier_bonus = sum(item.identifier_score for item in ranked_items) * 0.5
    keyword_bonus = (
        max(item.keyword_score for item in ranked_items) * 0.1
        + sum(item.keyword_score for item in ranked_items) * 0.02
    )
    size_bonus = min(len(ranked_items), 3) * 0.25
    exact_bonus = 10.0 if any(_matched_identifiers(item, intent) for item in ranked_items) else 0.0
    rank_bonus = max(0.0, 0.5 - ((best_rank - 1) * 0.05))
    return (
        best
        + identifier_bonus
        + keyword_bonus
        + size_bonus
        + exact_bonus
        + rank_bonus
        + _group_year_bonus(ranked_items, intent)
    )


def _group_year_bonus(
    ranked_items: list[RankedChunk],
    intent: QueryIntent,
) -> float:
    years = [year for item in ranked_items if (year := chunk_year(item.chunk)) is not None]
    if not years:
        return 0.0
    if intent.query_year is not None:
        return 4.0 if intent.query_year in years else -4.0
    if not _has_group_scope_match(ranked_items, intent):
        return 0.0
    latest = max(years)
    return min(4.0, max(0.0, (latest - 2000) * 0.16))


def _has_group_scope_match(
    ranked_items: list[RankedChunk],
    intent: QueryIntent,
) -> bool:
    if any(_matched_identifiers(item, intent) for item in ranked_items):
        return True
    if not intent.query_terms:
        return False
    return any(_source_scope_overlap(item, intent.query_terms) > 0 for item in ranked_items)


def _source_scope_overlap(
    ranked: RankedChunk,
    query_terms: tuple[str, ...],
) -> int:
    chunk = ranked.chunk
    source_text = " ".join(
        value
        for value in (
            chunk.filename or "",
            chunk.relative_path or "",
            chunk.manufacturer or "",
            chunk.brand or "",
            chunk.series or "",
            chunk.product or "",
            chunk.section_title or "",
            chunk.section_path or "",
            " ".join(chunk.technical_tokens_normalized or ()),
            " ".join(chunk.model_numbers or ()),
            " ".join(chunk.part_numbers or ()),
        )
        if value
    )
    normalized_source = normalize_technical_token(source_text)
    return sum(
        1
        for term in query_terms
        if len(normalize_technical_token(term)) >= 3
        and normalize_technical_token(term) in normalized_source
    )


def _matched_identifiers(
    ranked: RankedChunk,
    intent: QueryIntent,
) -> tuple[str, ...]:
    matches = set(ranked.matched_identifiers)
    if intent.identifiers:
        values = _normalized_evidence_values(ranked)
        matches.update(
            identifier for identifier in intent.identifiers
            if _identifier_in_values(identifier, values)
        )
    return tuple(sorted(matches))


def _normalized_evidence_values(ranked: RankedChunk) -> set[str]:
    chunk = ranked.chunk
    values = {
        *(chunk.technical_tokens_normalized or ()),
        *(normalize_technical_token(item) for item in chunk.model_numbers),
        *(normalize_technical_token(item) for item in chunk.part_numbers),
        normalize_technical_token(chunk.text),
        normalize_technical_token(chunk.filename or ""),
        normalize_technical_token(chunk.relative_path or ""),
        normalize_technical_token(chunk.product or ""),
        normalize_technical_token(chunk.series or ""),
        normalize_technical_token(chunk.brand or ""),
    }
    return {value for value in values if value}


def _selected_contains_identifier(
    selected: tuple[RankedChunk, ...],
    identifiers: tuple[str, ...],
    *,
    product_context: ProductApplicabilityContext | None = None,
) -> bool:
    if not identifiers:
        return True
    if any(
        any(
            _identifier_in_values(identifier, _normalized_evidence_values(item))
            for identifier in identifiers
        )
        for item in selected
    ):
        return True
    aliases = _product_identifier_aliases(product_context)
    normalized_identifiers = {
        normalize_technical_token(identifier) for identifier in identifiers
    }
    if not aliases or not normalized_identifiers.issubset(aliases):
        return False
    return any(
        any(_identifier_in_values(alias, _normalized_evidence_values(item)) for alias in aliases)
        for item in selected
    )


def _identifier_in_values(identifier: str, values: set[str]) -> bool:
    return any(identifier == value or identifier in value for value in values)


def _has_strong_match(selected: tuple[RankedChunk, ...]) -> bool:
    return any(item.identifier_score > 0 or item.keyword_score >= 2 for item in selected)


def _has_fitment_support(
    selected: tuple[RankedChunk, ...],
    intent: QueryIntent,
) -> bool:
    terms = ("compatible", "compatibility", "fits", "fit", "works with", "use with")
    return any(
        item.chunk.has_compatibility
        or any(term in item.chunk.text.casefold() for term in terms)
        for item in selected
    )


def _dimension_conflicts(
    selected: tuple[RankedChunk, ...],
    intent: QueryIntent,
) -> tuple[str, ...]:
    if "dimensions" not in intent.requested_fields:
        return ()
    requested_labels = _requested_dimension_labels(intent)
    values: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    for ranked in selected:
        for label, found in _dimension_fields(ranked.chunk.text).items():
            if label not in requested_labels:
                continue
            for value in found:
                values[label][value].add(ranked.chunk.chunk_id)
    return tuple(
        sorted(
            label
            for label, found in values.items()
            if len(found) > 1
            and len({chunk_id for ids in found.values() for chunk_id in ids}) > 1
        )
    )


def _diagnostics(
    intent: QueryIntent,
    selected: tuple[RankedChunk, ...],
    groups: tuple[EvidenceGroup, ...],
    retrieval: RankedRetrieval,
    decision: EvidenceDecision,
    inclusion_reasons: dict[str, str],
    product_context: ProductApplicabilityContext | None,
) -> dict[str, Any]:
    selected_ids = [item.chunk.chunk_id for item in selected]
    top_ids = [item.chunk.chunk_id for item in retrieval.chunks]
    return {
        "query_intent": {
            "intent_type": intent.intent_type,
            "identifiers": list(intent.identifiers),
            "query_terms": list(intent.query_terms),
            "query_year": intent.query_year,
            "prefer_latest": intent.prefer_latest,
            "requires_exact_identifier": intent.requires_exact_identifier,
            "safety_sensitive": intent.safety_sensitive,
            "requested_fields": list(intent.requested_fields),
        },
        "selected_chunk_ids": selected_ids,
        "selected_sources": [
            {
                "chunk_id": item.chunk.chunk_id,
                "source": _source(item),
                "page": item.chunk.page_start,
                "rank": item.rank,
                "inclusion_reason": inclusion_reasons.get(item.chunk.chunk_id),
            }
            for item in selected
        ],
        "discarded_top_k_chunk_ids": [
            chunk_id for chunk_id in top_ids if chunk_id not in selected_ids
        ],
        "group_count": len(groups),
        "groups": [
            {
                "source": group.source,
                "pages": list(group.pages),
                "chunk_ids": [item.chunk.chunk_id for item in group.items],
                "matched_identifiers": list(group.matched_identifiers),
                "score": group.score,
                "group_reason": group.group_reason,
            }
            for group in groups[:5]
        ],
        "evidence_decision": {
            "mode": decision.mode,
            "sufficient": decision.sufficient,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "missing_fields": list(decision.missing_fields),
            "conflicting_fields": list(decision.conflicting_fields),
        },
        "field_diagnostic": _field_diagnostic(
            intent,
            selected,
            product_context,
            decision,
        ),
        "low_confidence": retrieval.low_confidence,
        "low_confidence_reason": retrieval.low_confidence_reason,
    }


def _product_identifier_aliases(
    context: ProductApplicabilityContext | None,
) -> set[str]:
    if context is None:
        return set()
    values = (
        context.model,
        context.mpn,
        context.sku,
        context.upc,
        *context.manual_identifiers,
    )
    return {
        normalized
        for value in values
        if value and (normalized := normalize_technical_token(str(value)))
    }


def _requested_dimension_labels(intent: QueryIntent) -> set[str]:
    question_terms = {term.casefold() for term in intent.query_terms}
    explicit = {
        label
        for label in ("width", "height", "depth", "clearance")
        if label in question_terms
    }
    return explicit or {"width", "height", "depth", "clearance"}


_DIMENSION_PATTERN = re.compile(
    r"\b(width|height|depth|clearance)\b[^0-9]{0,24}"
    r"(\d+(?:\.\d+)?(?:\s+\d+/\d+)?|\d+\s+\d+/\d+|\d+/\d+)"
    r"\s*(?:\"|inches|inch|in\.|in)?",
    re.I,
)
_COMPACT_DIMENSION_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?(?:\s+\d+/\d+)?|\d+/\d+)\s*(?:\"|inches|inch|in\.)?"
    r"\s*([WDH])\b",
    re.I,
)


def _dimension_fields(text: str) -> dict[str, set[str]]:
    fields: dict[str, set[str]] = defaultdict(set)
    for label, value in _DIMENSION_PATTERN.findall(text or ""):
        normalized = _normalize_dimension_value(value)
        if normalized is not None:
            fields[label.casefold()].add(normalized)
    compact_labels = {"w": "width", "d": "depth", "h": "height"}
    for value, label in _COMPACT_DIMENSION_PATTERN.findall(text or ""):
        normalized = _normalize_dimension_value(value)
        if normalized is not None:
            fields[compact_labels[label.casefold()]].add(normalized)
    return dict(fields)


def _normalize_dimension_value(value: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", value.strip())
    try:
        if " " in cleaned and "/" in cleaned:
            whole, fraction = cleaned.split(" ", 1)
            number = Fraction(int(whole), 1) + Fraction(fraction)
        else:
            number = Fraction(cleaned)
    except (ValueError, ZeroDivisionError):
        return None
    rendered = f"{float(number):.6f}".rstrip("0").rstrip(".")
    return f"{rendered} in"


def _database_fields(
    context: ProductApplicabilityContext | None,
) -> dict[str, list[str]]:
    if context is None:
        return {}
    fields: dict[str, set[str]] = defaultdict(set)
    for name, value in (*context.approved_general_facts, *context.attributes):
        for label, found in _dimension_fields(str(value)).items():
            fields[label].update(found)
        normalized_name = str(name).strip().casefold().replace(" ", "_")
        if value and normalized_name in {
            "model",
            "mpn",
            "sku",
            "upc",
            "product_type",
        }:
            fields[normalized_name].add(str(value))
    return {key: sorted(values) for key, values in fields.items()}


def _pdf_fields(selected: tuple[RankedChunk, ...]) -> dict[str, list[str]]:
    fields: dict[str, set[str]] = defaultdict(set)
    for ranked in selected:
        for label, values in _dimension_fields(ranked.chunk.text).items():
            fields[label].update(values)
    return {key: sorted(values) for key, values in fields.items()}


def _field_diagnostic(
    intent: QueryIntent,
    selected: tuple[RankedChunk, ...],
    product_context: ProductApplicabilityContext | None,
    decision: EvidenceDecision,
) -> dict[str, Any]:
    database = _database_fields(product_context)
    pdf = _pdf_fields(selected)
    aliases = sorted(_product_identifier_aliases(product_context))
    normalized = {
        "database_fields": database,
        "pdf_fields": pdf,
        "product_identifier_aliases": aliases,
    }
    corroborated = sorted(
        field
        for field in set(database).intersection(pdf)
        if set(database[field]).intersection(pdf[field])
    )
    provenance = {}
    for field in sorted(set(database).union(pdf)):
        in_database = bool(database.get(field))
        in_pdf = bool(pdf.get(field))
        provenance[field] = (
            "approved product database and technical manual"
            if in_database and in_pdf
            else "approved product database"
            if in_database
            else "technical manual"
        )
    return {
        "requested_fields": list(intent.requested_fields),
        "found_database_fields": database,
        "found_pdf_fields": pdf,
        "normalized_values": normalized,
        "missing_fields": list(decision.missing_fields),
        "conflicting_fields": list(decision.conflicting_fields),
        "corroborated_fields": corroborated,
        "value_provenance": provenance,
        "applicability": {
            "query_identifiers": list(intent.identifiers),
            "product_identifier_aliases": aliases,
            "selected_evidence_matches_product_alias": (
                _selected_contains_identifier(
                    selected,
                    intent.identifiers,
                    product_context=product_context,
                )
                if intent.identifiers
                else None
            ),
        },
        "final_decision": {
            "mode": decision.mode,
            "sufficient": decision.sufficient,
            "confidence": decision.confidence,
            "reason": decision.reason,
        },
    }


def _source(ranked: RankedChunk) -> str:
    return ranked.chunk.relative_path or ranked.chunk.filename or ""


def _document_order(ranked: RankedChunk) -> tuple[str, int, int, int]:
    return (
        _source(ranked),
        ranked.chunk.page_start,
        ranked.chunk.chunk_index,
        ranked.rank,
    )
