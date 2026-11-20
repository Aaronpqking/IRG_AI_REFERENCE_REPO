from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from src.configuration_applicability import (
    DEFAULT_PDF_CONFIGURATION_APPLICABILITY_MODE,
    PdfConfigurationApplicabilityMode,
    assess_configuration_applicability,
)
from src.information_needs import InformationNeeds
from src.models import Chunk
from src.product_applicability import ProductApplicabilityContext
from src.product_taxonomy import DEFAULT_PRODUCT_TAXONOMY
from src.query_identity import parse_query_identity
from src.retrieval_policy import chunk_year, infer_document_type
from src.technical_tokens import (
    extract_query_terms,
    normalize_technical_token,
)


@dataclass(frozen=True)
class DocumentApplicability:
    document_id: str | None
    eligibility: str
    classification: str
    applicability_score: float
    exact_source_reference_match: bool
    exact_model_match: bool
    brand_match: bool
    manufacturer_match: bool
    series_match: bool
    product_type_match: bool
    fuel_match: bool
    year_overlap: bool | None
    generation_match: bool
    document_type_match: bool
    conflicting_signals: tuple[str, ...]
    exclusion_reasons: tuple[str, ...]
    applicable: bool
    diagnostic_reason_codes: tuple[str, ...]
    matched_fields: tuple[str, ...] = ()
    conflicting_fields: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()
    variant_match: bool = False
    conflict_class: str = "MATCH"
    raw_values: dict[str, dict[str, str | None]] | None = None
    normalized_values: dict[str, dict[str, str | None]] | None = None
    configuration_applicability: dict[str, Any] | None = None
    candidate_consensus: dict[str, Any] | None = None


def assess_document_applicability(
    chunk: Chunk,
    context: ProductApplicabilityContext | None,
    needs: InformationNeeds,
    *,
    query_text: str | None = None,
    configuration_mode: (
        str | PdfConfigurationApplicabilityMode
    ) = DEFAULT_PDF_CONFIGURATION_APPLICABILITY_MODE,
) -> DocumentApplicability:
    if context is None:
        query_scoped = _query_scoped_document_applicability(
            chunk,
            query_text,
        )
        if query_scoped is not None:
            return query_scoped
        return DocumentApplicability(
            document_id=chunk.document_id,
            eligibility="UNKNOWN",
            classification="UNPROVEN",
            applicability_score=0.0,
            exact_source_reference_match=False,
            exact_model_match=False,
            brand_match=False,
            manufacturer_match=False,
            series_match=False,
            product_type_match=False,
            fuel_match=False,
            year_overlap=None,
            generation_match=False,
            document_type_match=_document_type_matches(chunk, needs),
            conflicting_signals=(),
            exclusion_reasons=(),
            applicable=False,
            diagnostic_reason_codes=("NO_PRODUCT_CONTEXT",),
        )
    source_match = _source_match(chunk, context)
    model_match = _value_match(context.model, chunk)
    mpn_match = _value_match(context.mpn, chunk)
    brand_match = _structured_identity_match(context.brand, chunk.brand, brand=True)
    manufacturer_match = _structured_identity_match(
        context.manufacturer,
        chunk.manufacturer,
        brand=True,
    )
    series_match = _structured_identity_match(context.series, chunk.series)
    product_type_match = _structured_identity_match(
        context.product_type,
        chunk.product,
    )
    fuel_match = _fuel_match(chunk, context)
    year = chunk_year(chunk)
    year_overlap = _year_overlap(year, context)
    generation_match = _value_match(context.product_generation, chunk)
    variant_match = _value_match(context.variant, chunk)
    document_type_match = _document_type_matches(chunk, needs)
    technical_topic_matches = _technical_topic_matches(
        chunk,
        needs,
        query_text,
    )
    raw_values = _raw_identity_values(context, chunk)
    normalized_values = _normalized_identity_values(raw_values)
    conflicts = []
    exclusions = []
    unknown_reasons = []
    conflicting_fields = []
    missing_fields = []
    conflict_classes = []
    inferred_metadata = _inferred_metadata(chunk)

    if context.brand:
        if not chunk.brand:
            conflicts.append("BRAND_METADATA_MISSING")
            missing_fields.append("brand")
            conflict_classes.append("MISSING_METADATA")
        elif brand_match:
            if _raw_values_differ(context.brand, chunk.brand):
                conflicts.append("BRAND_ALIAS_NORMALIZED")
                conflict_classes.append("ALIAS_NORMALIZATION_WARNING")
        else:
            conflicts.append(
                "INFERRED_PATH_BRAND_MISMATCH"
                if inferred_metadata
                else "BRAND_METADATA_MISMATCH"
            )
            conflicting_fields.append("brand")
            if inferred_metadata:
                conflict_classes.append("SOFT_METADATA_CONFLICT")
            else:
                conflict_classes.append("HARD_CONFLICT")
                exclusions.append("WRONG_BRAND")
    if context.manufacturer:
        if not chunk.manufacturer:
            conflicts.append("MANUFACTURER_METADATA_MISSING")
            missing_fields.append("manufacturer")
            conflict_classes.append("MISSING_METADATA")
        elif manufacturer_match:
            if _raw_values_differ(context.manufacturer, chunk.manufacturer):
                conflicts.append("MANUFACTURER_ALIAS_NORMALIZED")
                conflict_classes.append("ALIAS_NORMALIZATION_WARNING")
        else:
            conflicts.append(
                "INFERRED_PATH_MANUFACTURER_MISMATCH"
                if inferred_metadata
                else "MANUFACTURER_METADATA_MISMATCH"
            )
            conflicting_fields.append("manufacturer")
            conflict_classes.append("SOFT_METADATA_CONFLICT")
    if context.series:
        if not chunk.series:
            conflicts.append("SERIES_METADATA_MISSING")
            missing_fields.append("series")
            conflict_classes.append("MISSING_METADATA")
        elif not series_match:
            conflicts.append(
                "INFERRED_PATH_SERIES_MISMATCH"
                if inferred_metadata
                else "SERIES_METADATA_MISMATCH"
            )
            conflicting_fields.append("series")
            conflict_classes.append("SOFT_METADATA_CONFLICT")
    if context.product_type and chunk.product and not product_type_match:
        conflicts.append(
            "INFERRED_PATH_PRODUCT_TYPE_MISMATCH"
            if inferred_metadata
            else "PRODUCT_TYPE_METADATA_MISMATCH"
        )
        conflicting_fields.append("product_type")
        if inferred_metadata:
            conflict_classes.append("SOFT_METADATA_CONFLICT")
        else:
            conflict_classes.append("SOFT_METADATA_CONFLICT")
    if context.fuel_type and _fuel_conflict(chunk, context.fuel_type):
        conflicts.append("CONFLICTING_FUEL_TYPE")
        conflicting_fields.append("fuel_type")
        conflict_classes.append("SOFT_METADATA_CONFLICT")
    year_reason_codes = _year_diagnostic_reason_codes(chunk, context)
    year_mismatch_codes = tuple(
        code for code in year_reason_codes if "MISMATCH" in code
    )
    if year_overlap is False and not year_mismatch_codes:
        year_mismatch_codes = ("YEAR_METADATA_MISMATCH_OBSERVED",)
    if year_mismatch_codes:
        conflicts.extend(year_mismatch_codes)
        conflicting_fields.append("year")
        conflict_classes.append("SOFT_METADATA_CONFLICT")
    if context.product_generation and not generation_match and _contains_generation_signal(chunk):
        conflicts.append("CONFLICTING_PRODUCT_GENERATION")
        conflicting_fields.append("generation")
        conflict_classes.append("HARD_CONFLICT")
        exclusions.append("WRONG_PRODUCT_GENERATION")
    revision_match = _revision_matches(chunk, context.model_revision)
    if (
        context.model_revision
        and revision_match is False
        and _contains_revision_signal(chunk)
        and not _revision_signal_is_year(chunk)
    ):
        conflicts.append("CONFLICTING_PRODUCT_REVISION")
        conflicting_fields.append("revision")
        conflict_classes.append("HARD_CONFLICT")
        exclusions.append("WRONG_PRODUCT_REVISION")
    if context.variant:
        if variant_match:
            pass
        elif _contains_variant_signal(chunk):
            conflicts.append("CONFLICTING_PRODUCT_VARIANT")
            conflicting_fields.append("variant")
            conflict_classes.append("SOFT_METADATA_CONFLICT")
        else:
            conflicts.append("VARIANT_METADATA_MISSING")
            missing_fields.append("variant")
            conflict_classes.append("MISSING_METADATA")
    explicit_exclusion = _explicit_product_exclusion_reason(chunk, context)
    if explicit_exclusion:
        conflicts.append("DOCUMENT_EXPLICITLY_EXCLUDES_PRODUCT")
        conflicting_fields.append(
            "serial_number"
            if explicit_exclusion == "EXPLICIT_SERIAL_NUMBER_EXCLUSION"
            else "manufacture_date"
            if explicit_exclusion == "EXPLICIT_MANUFACTURE_DATE_EXCLUSION"
            else "model"
        )
        conflict_classes.append("HARD_CONFLICT")
        exclusions.append(explicit_exclusion)
    authoritative_models = _authoritative_model_numbers(chunk)
    document_models = {
        normalize_technical_token(value)
        for value in authoritative_models
        if value
    }
    expected_models = {
        normalize_technical_token(value)
        for value in (context.model, context.mpn)
        if value
    }
    if (
        document_models
        and expected_models
        and not model_match
        and not mpn_match
    ):
        conflicts.append("EXACT_PRODUCT_IDENTIFIER_CONFLICT")
        conflicting_fields.append("model")
        conflict_classes.append("HARD_CONFLICT")
        exclusions.append("WRONG_EXACT_PRODUCT")
    score = 0.0
    reasons = []
    if source_match:
        score += 35.0
        reasons.append("EXACT_SOURCE_REFERENCE_MATCH")
    if model_match:
        score += 25.0
        reasons.append("EXACT_MODEL_MATCH")
    if mpn_match:
        score += 20.0
        reasons.append("EXACT_MPN_MATCH")
    if brand_match:
        score += 6.0
        reasons.append("BRAND_MATCH")
    if manufacturer_match:
        score += 4.0
        reasons.append("MANUFACTURER_MATCH")
    if series_match:
        score += 10.0
        reasons.append("SERIES_MATCH")
    if product_type_match:
        score += 4.0
        reasons.append("PRODUCT_TYPE_MATCH")
    if fuel_match:
        score += 12.0
        reasons.append("FUEL_MATCH")
    if year_overlap:
        score += 8.0
        reasons.extend(("YEAR_OVERLAP", "YEAR_AGREEMENT_OBSERVED"))
    if generation_match:
        score += 10.0
        reasons.append("GENERATION_MATCH")
    if variant_match:
        score += 10.0
        reasons.append("VARIANT_MATCH")
    if document_type_match:
        score += 7.0
        reasons.append("DOCUMENT_TYPE_MATCH")
    if technical_topic_matches:
        score += min(
            24.0,
            float(
                max(
                    len(normalize_technical_token(term))
                    for term in technical_topic_matches
                )
            ),
        )
        reasons.append("TECHNICAL_TOPIC_MATCH")
    if exclusions:
        classification = "CONFLICTING"
    elif source_match or model_match or mpn_match:
        classification = "DIRECT"
    elif series_match and (brand_match or manufacturer_match):
        classification = "FAMILY_APPLICABLE"
    elif product_type_match and (brand_match or manufacturer_match):
        classification = "CATEGORY_APPLICABLE"
    elif brand_match or manufacturer_match:
        classification = "RELATED_ONLY"
    elif any(
        (
            context.brand,
            context.manufacturer,
            context.series,
            context.product_type,
            context.model,
            context.mpn,
        )
    ):
        classification = "UNPROVEN"
    else:
        classification = "UNRELATED"
    if needs.technical and classification not in {
        "DIRECT",
        "FAMILY_APPLICABLE",
        "CATEGORY_APPLICABLE",
    }:
        unknown_reasons.append("NO_APPLICABLE_PRODUCT_DOCUMENT_SIGNAL")
    score -= 50.0 * len(exclusions)
    if exclusions:
        eligibility = "CONFLICTING" if conflicts else "INAPPLICABLE"
    elif classification in {
        "DIRECT",
        "FAMILY_APPLICABLE",
        "CATEGORY_APPLICABLE",
    } and document_type_match:
        eligibility = "APPLICABLE"
    elif unknown_reasons:
        eligibility = "UNKNOWN"
    else:
        eligibility = "UNKNOWN"
    applicable = eligibility == "APPLICABLE"
    configuration = assess_configuration_applicability(
        chunk,
        context,
        mode=configuration_mode,
        base_admitted=applicable,
    )
    if configuration.actual_admission_changed:
        conflicts.append(
            "AUTHORITATIVE_CONFIGURATION_CONFLICT_ENFORCED"
        )
        conflicting_fields.append("configuration")
        exclusions.append("EXPLICIT_CONFIGURATION_CONFLICT")
        conflict_classes.append("HARD_CONFLICT")
        classification = "CONFLICTING"
        eligibility = "CONFLICTING"
        applicable = False
        score -= 50.0
    conflict_class = _highest_conflict_class(conflict_classes)
    reason_codes = tuple(
        dict.fromkeys(
            [
                *reasons,
                *conflicts,
                *(
                    code
                    for code in year_reason_codes
                    if code not in year_mismatch_codes
                ),
                *configuration.reason_codes,
                *unknown_reasons,
                *(("WEAK_APPLICABILITY_SIGNAL",) if not reasons and not conflicts and not unknown_reasons else ()),
            ]
        )
    )
    return DocumentApplicability(
        document_id=chunk.document_id,
        eligibility=eligibility,
        classification=classification,
        applicability_score=score,
        exact_source_reference_match=source_match,
        exact_model_match=model_match,
        brand_match=brand_match,
        manufacturer_match=manufacturer_match,
        series_match=series_match,
        product_type_match=product_type_match,
        fuel_match=fuel_match,
        year_overlap=year_overlap,
        generation_match=generation_match,
        document_type_match=document_type_match,
        conflicting_signals=tuple(conflicts),
        exclusion_reasons=tuple(exclusions),
        applicable=applicable,
        diagnostic_reason_codes=reason_codes,
        matched_fields=tuple(
            field
            for field, matched in (
                ("source_reference", source_match),
                ("model", model_match),
                ("mpn", mpn_match),
                ("brand", brand_match),
                ("manufacturer", manufacturer_match),
                ("series", series_match),
                ("product_type", product_type_match),
                ("fuel_type", fuel_match),
                ("year", bool(year_overlap)),
                ("generation", generation_match),
                ("document_type", document_type_match),
            )
            if matched
        ),
        conflicting_fields=tuple(dict.fromkeys(conflicting_fields)),
        missing_fields=tuple(dict.fromkeys(missing_fields)),
        variant_match=variant_match,
        conflict_class=conflict_class,
        raw_values=raw_values,
        normalized_values=normalized_values,
        configuration_applicability=configuration.as_dict(),
    )


def _query_scoped_document_applicability(
    chunk: Chunk,
    query_text: str | None,
) -> DocumentApplicability | None:
    query = re.sub(r"\s+", " ", query_text or "").strip()
    if not query:
        return None
    query_identity = parse_query_identity(query)
    query_identifiers = {
        item.normalized
        for item in query_identity.identifiers
        if item.confidence == "high"
    }
    authoritative_identifiers = _authoritative_document_identifiers(chunk)
    identity_matches = tuple(
        sorted(query_identifiers & authoritative_identifiers)
    )
    document_type = infer_document_type(chunk)
    requested_document_types = _requested_document_types(query)
    if requested_document_types and not _compatible_requested_document_type(
        document_type,
        requested_document_types,
    ):
        return None
    if identity_matches:
        excluded_identifiers = tuple(
            item.raw
            for item in query_identity.identifiers
            if (
                item.normalized in identity_matches
                and _chunk_text_explicitly_excludes_identifier(
                    chunk,
                    item.raw,
                )
            )
        )
        if excluded_identifiers:
            return DocumentApplicability(
                document_id=chunk.document_id,
                eligibility="CONFLICTING",
                classification="CONFLICTING",
                applicability_score=-18.0,
                exact_source_reference_match=False,
                exact_model_match=True,
                brand_match=False,
                manufacturer_match=False,
                series_match=False,
                product_type_match=False,
                fuel_match=False,
                year_overlap=None,
                generation_match=False,
                document_type_match=True,
                conflicting_signals=(
                    "DOCUMENT_EXPLICITLY_EXCLUDES_PRODUCT",
                ),
                exclusion_reasons=("EXPLICIT_PRODUCT_EXCLUSION",),
                applicable=False,
                diagnostic_reason_codes=(
                    "QUERY_AUTHORITATIVE_IDENTIFIER_MATCH",
                    "DOCUMENT_EXPLICITLY_EXCLUDES_PRODUCT",
                ),
                matched_fields=("query_scope", "document_identity"),
                conflicting_fields=("model",),
                conflict_class="HARD_CONFLICT",
            )
        reason_codes = ["QUERY_AUTHORITATIVE_IDENTIFIER_MATCH"]
        matched_fields = ["query_scope", "document_identity"]
        if requested_document_types:
            reason_codes.append("QUERY_DOCUMENT_TYPE_MATCH")
            matched_fields.append("document_type")
        return DocumentApplicability(
            document_id=chunk.document_id,
            eligibility="APPLICABLE",
            classification="QUERY_SCOPED",
            applicability_score=32.0,
            exact_source_reference_match=False,
            exact_model_match=True,
            brand_match=False,
            manufacturer_match=False,
            series_match=False,
            product_type_match=False,
            fuel_match=False,
            year_overlap=None,
            generation_match=False,
            document_type_match=True,
            conflicting_signals=(),
            exclusion_reasons=(),
            applicable=True,
            diagnostic_reason_codes=tuple(reason_codes),
            matched_fields=tuple(matched_fields),
            raw_values={
                "query_scope": {
                    "expected": query,
                    "actual": ", ".join(identity_matches),
                }
            },
            normalized_values={
                "query_scope": {
                    "expected": ", ".join(sorted(query_identifiers)),
                    "actual": ", ".join(identity_matches),
                }
            },
        )

    # Preserve the existing narrow catalog-style query scope. A query year is
    # a scope signal here, not an admission or rejection condition.
    year_match = re.search(r"\b((?:19|20)\d{2})\b", query)
    document_year = chunk_year(chunk)
    if (
        year_match is None
        or not document_type
        or not _query_mentions_document_type(query, document_type)
    ):
        return None

    query_terms = {
        normalize_technical_token(term)
        for term in extract_query_terms(query)
        if term
    }
    excluded = {
        normalize_technical_token(year_match.group(1)),
        *(
            normalize_technical_token(part)
            for part in re.split(r"[^a-z0-9]+", document_type.casefold())
            if part
        ),
    }
    scoped_terms = {
        term
        for term in query_terms
        if len(term) >= 3 and term not in excluded
    }
    document_values = normalize_technical_token(
        " ".join(
            str(value)
            for value in (
                chunk.document_id,
                chunk.filename,
                chunk.relative_path,
                chunk.manufacturer,
                chunk.brand,
                chunk.series,
                chunk.product,
                chunk.section_title,
                chunk.section_path,
                chunk.text[:4000],
            )
            if value
        )
    )
    matched_scope = tuple(
        sorted(
            term for term in scoped_terms
            if term in document_values
        )
    )
    if not matched_scope:
        return None

    query_year = int(year_match.group(1))
    query_year_agrees = (
        document_year is not None and query_year == document_year
    )
    reason_codes = (
        (
            "QUERY_YEAR_MATCH"
            if query_year_agrees
            else "YEAR_SCOPE_UNPROVEN"
            if document_year is None
            else "YEAR_PATH_MISMATCH_OBSERVED"
        ),
        "QUERY_DOCUMENT_TYPE_MATCH",
        "QUERY_LEXICAL_SCOPE_MATCH",
    )
    return DocumentApplicability(
        document_id=chunk.document_id,
        eligibility="APPLICABLE",
        classification="QUERY_SCOPED",
        applicability_score=22.0 + min(8.0, 2.0 * len(matched_scope)),
        exact_source_reference_match=False,
        exact_model_match=False,
        brand_match=False,
        manufacturer_match=False,
        series_match=False,
        product_type_match=False,
        fuel_match=False,
        year_overlap=query_year_agrees if document_year is not None else None,
        generation_match=False,
        document_type_match=True,
        conflicting_signals=(),
        exclusion_reasons=(),
        applicable=True,
        diagnostic_reason_codes=reason_codes,
        matched_fields=(
            "query_scope",
            "document_type",
            *(("year",) if query_year_agrees else ()),
        ),
        raw_values={
            "query_scope": {
                "expected": query,
                "actual": " ".join(matched_scope),
            }
        },
        normalized_values={
            "query_scope": {
                "expected": normalize_technical_token(query),
                "actual": " ".join(matched_scope),
            }
        },
    )


def _authoritative_document_identifiers(chunk: Chunk) -> set[str]:
    values = set(
        normalize_technical_token(value)
        for value in _authoritative_model_numbers(chunk)
        if value
    )
    # Identifiers printed in the governed document body are direct document
    # evidence even when surrounding taxonomy fields were inferred from a
    # path. Paths remain excluded from identity authority in that case.
    values.update(_labeled_document_body_identifiers(chunk.text or ""))
    if _inferred_metadata(chunk):
        return {value for value in values if value}
    for field in (
        chunk.document_id,
        chunk.filename,
        chunk.relative_path,
        *chunk.catalog_path_aliases,
    ):
        if not field:
            continue
        parsed = parse_query_identity(str(field))
        values.update(
            item.normalized
            for item in parsed.identifiers
            if item.confidence == "high"
        )
    return {value for value in values if value}


def _labeled_document_body_identifiers(text: str) -> set[str]:
    return {
        item.normalized
        for line in text.splitlines()
        if re.search(
            r"\b(?:model|models|mpn|sku|part(?:\s+number)?|p/n)\b",
            line,
            re.I,
        )
        for item in parse_query_identity(line).identifiers
        if item.confidence == "high"
    }


def _requested_document_types(query: str) -> set[str]:
    return {
        document_type
        for document_type in (
            "catalog",
            "parts",
            "specification",
            "quick_start",
            "owner_manual",
        )
        if _query_mentions_document_type(query, document_type)
    }


def _compatible_requested_document_type(
    document_type: str,
    requested: set[str],
) -> bool:
    if document_type in requested:
        return True
    return document_type == "quick_start" and "owner_manual" in requested


def _query_mentions_document_type(
    query: str,
    document_type: str,
) -> bool:
    query_tokens = {
        normalize_technical_token(term)
        for term in re.findall(r"[a-z0-9]+", query.casefold())
        if term
    }
    type_tokens = {
        normalize_technical_token(part)
        for part in re.split(
            r"[^a-z0-9]+",
            document_type.casefold(),
        )
        if part
    }
    return bool(query_tokens & type_tokens)


def chunk_applicability_diagnostics(
    chunk: Chunk,
    context: ProductApplicabilityContext | None,
    document: DocumentApplicability,
) -> dict[str, Any]:
    return {
        "document_id": chunk.document_id,
        "chunk_id": chunk.chunk_id,
        "document_applicability": document.applicable,
        "document_eligibility": document.eligibility,
        "applicability_classification": document.classification,
        "model_applicability": document.exact_model_match,
        "brand_applicability": document.brand_match,
        "manufacturer_applicability": document.manufacturer_match,
        "series_applicability": document.series_match,
        "product_type_applicability": document.product_type_match,
        "fuel_applicability": document.fuel_match,
        "variant_applicability": document.variant_match,
        "year_applicability": document.year_overlap,
        "section_applicability": bool(chunk.section_title or chunk.section_path),
        "table_context_completeness": bool(not chunk.has_table or (chunk.section_title or chunk.text.count("\n") >= 2)),
        "warning_context_completeness": bool(not (chunk.has_warning or chunk.has_caution) or len(chunk.text) >= 80),
        "matched_identifiers": [
            value for value in (getattr(context, "model", None), getattr(context, "mpn", None))
            if value and _value_match(value, chunk)
        ],
        "mismatch_reasons": list(document.exclusion_reasons),
        "matched_fields": list(document.matched_fields),
        "conflicting_fields": list(document.conflicting_fields),
        "missing_fields": list(document.missing_fields),
        "raw_values": document.raw_values or {},
        "normalized_values": document.normalized_values or {},
        "conflict_class": document.conflict_class,
        "reason_codes": list(document.diagnostic_reason_codes),
        "configuration_applicability": (
            document.configuration_applicability or {}
        ),
        "candidate_consensus": document.candidate_consensus or {},
    }


def _source_match(chunk: Chunk, context: ProductApplicabilityContext) -> bool:
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
    reference_values = {
        normalize_technical_token(value)
        for value in (
            *context.source_document_ids,
            *context.source_filenames,
            *context.source_paths,
            *context.source_urls,
        )
        if value
    }
    return bool(source_values & reference_values)


def _value_match(value: str | None, chunk: Chunk) -> bool:
    if not value:
        return False
    token = normalize_technical_token(value)
    if not token:
        return False
    values = " ".join(
        str(item)
        for item in (
            chunk.document_id,
            chunk.filename,
            chunk.relative_path,
            chunk.manufacturer,
            chunk.brand,
            chunk.series,
            chunk.product,
            chunk.section_title,
            chunk.section_path,
            chunk.text[:2000],
            " ".join(chunk.model_numbers or ()),
            " ".join(chunk.document_model_numbers or ()),
            " ".join(chunk.part_numbers or ()),
            " ".join(chunk.technical_tokens_normalized or ()),
        )
        if item
    )
    normalized = normalize_technical_token(values)
    return token in normalized


def _structured_identity_match(
    expected: str | None,
    actual: str | None,
    *,
    brand: bool = False,
) -> bool:
    if not expected or not actual:
        return False
    if brand:
        expected_match = DEFAULT_PRODUCT_TAXONOMY.resolve_brand(expected, exact=True)
        actual_match = DEFAULT_PRODUCT_TAXONOMY.resolve_brand(actual, exact=True)
        if expected_match and actual_match:
            return expected_match.canonical_name == actual_match.canonical_name
    return normalize_technical_token(expected) == normalize_technical_token(actual)


def _raw_values_differ(expected: str, actual: str) -> bool:
    normalized_expected = re.sub(r"\s+", " ", expected).strip().casefold()
    normalized_actual = re.sub(r"\s+", " ", actual).strip().casefold()
    return normalized_expected != normalized_actual


def _raw_identity_values(
    context: ProductApplicabilityContext,
    chunk: Chunk,
) -> dict[str, dict[str, str | None]]:
    return {
        "brand": {"expected": context.brand, "actual": chunk.brand},
        "manufacturer": {
            "expected": context.manufacturer,
            "actual": chunk.manufacturer,
        },
        "series": {"expected": context.series, "actual": chunk.series},
        "model": {
            "expected": context.model,
            "actual": ", ".join(
                _authoritative_model_numbers(chunk)
            )
            or None,
        },
        "mpn": {
            "expected": context.mpn,
            "actual": ", ".join(
                dict.fromkeys(
                    (
                        *_authoritative_model_numbers(chunk),
                        *chunk.part_numbers,
                    )
                )
            )
            or None,
        },
        "product_type": {
            "expected": context.product_type,
            "actual": chunk.product,
        },
        "variant": {"expected": context.variant, "actual": _variant_signal(chunk)},
        "year": {
            "expected": _context_year_range(context),
            "actual": ", ".join(
                str(value)
                for value in (
                    chunk.year,
                    chunk.document_publication_year,
                    chunk.document_revision_year,
                    chunk.document_catalog_year,
                    (
                        f"{chunk.document_year_coverage_start or ''}-"
                        f"{chunk.document_year_coverage_end or ''}"
                        if (
                            chunk.document_year_coverage_start is not None
                            or chunk.document_year_coverage_end is not None
                        )
                        else None
                    ),
                )
                if value not in (None, "")
            )
            or None,
        },
        "generation": {
            "expected": context.product_generation,
            "actual": _generation_signal(chunk),
        },
        "revision": {
            "expected": context.model_revision,
            "actual": _revision_signal(chunk),
        },
        "source_namespace": {
            "expected": ", ".join(context.source_paths) or None,
            "actual": chunk.relative_path,
        },
    }


def _normalized_identity_values(
    raw_values: dict[str, dict[str, str | None]],
) -> dict[str, dict[str, str | None]]:
    normalized: dict[str, dict[str, str | None]] = {}
    for field, values in raw_values.items():
        expected = values.get("expected")
        actual = values.get("actual")
        if field in {"brand", "manufacturer"}:
            expected = _canonical_brand_value(expected)
            actual = _canonical_brand_value(actual)
        normalized[field] = {
            "expected": _normalized_token_or_none(expected),
            "actual": _normalized_token_or_none(actual),
        }
    return normalized


def _canonical_brand_value(value: str | None) -> str | None:
    match = DEFAULT_PRODUCT_TAXONOMY.resolve_brand(value, exact=True)
    return match.canonical_name if match else value


def _normalized_token_or_none(value: str | None) -> str | None:
    return normalize_technical_token(value) or None if value else None


def _inferred_metadata(chunk: Chunk) -> bool:
    return (
        str(chunk.metadata_source or "").casefold() == "path"
        or str(chunk.metadata_confidence or "").casefold() == "inferred"
    )


def _authoritative_model_numbers(chunk: Chunk) -> tuple[str, ...]:
    if chunk.document_model_numbers:
        return chunk.document_model_numbers
    if _inferred_metadata(chunk):
        return ()
    return chunk.model_numbers


def _highest_conflict_class(classes: list[str]) -> str:
    priorities = (
        "HARD_CONFLICT",
        "SOFT_METADATA_CONFLICT",
        "ALIAS_NORMALIZATION_WARNING",
        "MISSING_METADATA",
    )
    return next((name for name in priorities if name in classes), "MATCH")


def _context_year_range(context: ProductApplicabilityContext) -> str | None:
    if context.model_year is not None:
        return str(context.model_year)
    if context.production_start_year is None and context.production_end_year is None:
        return None
    return (
        f"{context.production_start_year or ''}-"
        f"{context.production_end_year or ''}"
    )


def _variant_signal(chunk: Chunk) -> str | None:
    text = " ".join(
        value
        for value in (
            chunk.section_title,
            chunk.section_path,
            chunk.text[:1200],
        )
        if value
    )
    match = re.search(
        r"\b(?:variant|configuration)\s*[:=-]\s*([A-Za-z0-9][A-Za-z0-9 /_-]{0,80})",
        text,
        re.I,
    )
    return match.group(1).strip() if match else None


def _contains_variant_signal(chunk: Chunk) -> bool:
    return _variant_signal(chunk) is not None


def _generation_signal(chunk: Chunk) -> str | None:
    text = " ".join(
        value
        for value in (
            chunk.section_title,
            chunk.section_path,
            chunk.text[:1200],
        )
        if value
    )
    match = re.search(
        r"\bgeneration\s*[:=-]?\s*([A-Za-z0-9][A-Za-z0-9._-]{0,30})",
        text,
        re.I,
    )
    return match.group(1).strip() if match else None


def _revision_signal(chunk: Chunk) -> str | None:
    text = " ".join(
        value
        for value in (
            chunk.section_title,
            chunk.section_path,
            chunk.text[:1200],
        )
        if value
    )
    match = re.search(
        r"\b(?:revision|rev)\s*[:=-]?\s*([A-Za-z0-9][A-Za-z0-9._-]{0,30})",
        text,
        re.I,
    )
    return match.group(1).strip() if match else None


def _contains_revision_signal(chunk: Chunk) -> bool:
    return _revision_signal(chunk) is not None


def _revision_matches(chunk: Chunk, expected: str | None) -> bool | None:
    actual = _revision_signal(chunk)
    if not expected or not actual:
        return None
    return normalize_technical_token(expected) == normalize_technical_token(actual)


def _revision_signal_is_year(chunk: Chunk) -> bool:
    value = _revision_signal(chunk)
    return bool(value and re.fullmatch(r"(?:19|20)\d{2}", value))


def _explicit_product_exclusion_reason(
    chunk: Chunk,
    context: ProductApplicabilityContext,
) -> str | None:
    for identifier in (context.model, context.mpn):
        if not identifier:
            continue
        if _chunk_text_explicitly_excludes_identifier(chunk, identifier):
            return "EXPLICIT_PRODUCT_EXCLUSION"
    text = _chunk_applicability_text(chunk)
    facts = dict(context.approved_general_facts)
    for field, reason in (
        ("serial_number", "EXPLICIT_SERIAL_NUMBER_EXCLUSION"),
        ("manufacture_date", "EXPLICIT_MANUFACTURE_DATE_EXCLUSION"),
    ):
        value = str(facts.get(field) or "").strip()
        if not value:
            continue
        escaped = re.escape(value)
        patterns = (
            rf"\b(?:excludes?|does\s+not\s+cover)\s+{escaped}\b",
            rf"\bnot\s+(?:for|applicable\s+to|compatible\s+with)\s+{escaped}\b",
            rf"\b{escaped}\s+(?:is|are)\s+not\s+(?:covered|supported|compatible)\b",
        )
        if any(re.search(pattern, text, re.I) for pattern in patterns):
            return reason
    return None


def _chunk_text_explicitly_excludes_identifier(
    chunk: Chunk,
    identifier: str,
) -> bool:
    escaped = re.escape(identifier)
    patterns = (
        rf"\bnot\s+(?:for|applicable\s+to|compatible\s+with)\s+{escaped}\b",
        rf"\b(?:excludes?|does\s+not\s+cover)\s+{escaped}\b",
        rf"\b{escaped}\s+(?:is|models?\s+are)\s+not\s+(?:covered|supported|compatible)\b",
    )
    return any(
        re.search(pattern, _chunk_applicability_text(chunk), re.I)
        for pattern in patterns
    )


def _chunk_applicability_text(chunk: Chunk) -> str:
    return " ".join(
        value
        for value in (
            chunk.section_title,
            chunk.section_path,
            chunk.text[:2500],
        )
        if value
    )


def _fuel_match(chunk: Chunk, context: ProductApplicabilityContext) -> bool:
    if not context.fuel_type:
        return False
    return _value_match(context.fuel_type, chunk)


def _fuel_conflict(chunk: Chunk, fuel_type: str) -> bool:
    text = f"{chunk.filename or ''} {chunk.relative_path or ''} {chunk.text[:1500]}".casefold()
    wanted = fuel_type.casefold()
    if "natural gas" in wanted:
        return "propane" in text or " lp " in f" {text} "
    if "propane" in wanted:
        return "natural gas" in text or " ng " in f" {text} "
    return False


def _year_overlap(year: int | None, context: ProductApplicabilityContext) -> bool | None:
    start, end = context.production_start_year, context.production_end_year
    if context.model_year is not None:
        start = end = context.model_year
    if year is None or (start is None and end is None):
        return None
    if start is not None and year < start:
        return False
    if end is not None and year > end:
        return False
    return True


def _year_diagnostic_reason_codes(
    chunk: Chunk,
    context: ProductApplicabilityContext,
) -> tuple[str, ...]:
    observations: list[str] = []

    def observe(value: int | None, mismatch_code: str) -> None:
        overlap = _year_overlap(value, context)
        if overlap is False:
            observations.append(mismatch_code)
        elif overlap is True:
            observations.append("YEAR_AGREEMENT_OBSERVED")

    path_years = _years_in_text(chunk.relative_path or "")
    filename_years = _years_in_text(chunk.filename or "")
    for value in path_years:
        observe(value, "YEAR_PATH_MISMATCH_OBSERVED")
    for value in filename_years:
        observe(value, "YEAR_FILENAME_MISMATCH_OBSERVED")
    metadata_year = chunk_year(chunk)
    if metadata_year is not None and metadata_year not in path_years:
        observe(metadata_year, "YEAR_METADATA_MISMATCH_OBSERVED")
    observe(
        chunk.document_publication_year,
        "YEAR_PUBLICATION_MISMATCH_OBSERVED",
    )
    observe(
        chunk.document_revision_year,
        "YEAR_REVISION_MISMATCH_OBSERVED",
    )
    observe(
        chunk.document_catalog_year,
        "YEAR_CATALOG_MISMATCH_OBSERVED",
    )
    coverage_start = chunk.document_year_coverage_start
    coverage_end = chunk.document_year_coverage_end
    product_start = context.model_year or context.production_start_year
    product_end = context.model_year or context.production_end_year
    if (
        (coverage_start is not None or coverage_end is not None)
        and (product_start is not None or product_end is not None)
    ):
        coverage_low = coverage_start if coverage_start is not None else coverage_end
        coverage_high = coverage_end if coverage_end is not None else coverage_start
        product_low = product_start if product_start is not None else product_end
        product_high = product_end if product_end is not None else product_start
        if (
            coverage_low is not None
            and coverage_high is not None
            and product_low is not None
            and product_high is not None
            and (product_high < coverage_low or product_low > coverage_high)
        ):
            observations.append(
                "YEAR_DECLARED_COVERAGE_MISMATCH_OBSERVED"
            )
        else:
            observations.append("YEAR_AGREEMENT_OBSERVED")
    return tuple(dict.fromkeys(observations))


def _years_in_text(value: str) -> tuple[int, ...]:
    return tuple(
        dict.fromkeys(
            int(match)
            for match in re.findall(r"\b(?:19|20)\d{2}\b", value)
        )
    )


def _document_type_matches(chunk: Chunk, needs: InformationNeeds) -> bool:
    document_type = infer_document_type(chunk)
    technical = set(needs.technical)
    if not technical:
        return True
    if technical & {"installation", "clearances", "cutout", "wiring", "warnings", "cautions"}:
        return document_type in {"owner_manual", "quick_start", "specification", "unknown"}
    if technical & {"parts"}:
        return document_type in {"owner_manual", "parts", "unknown"}
    if technical & {"dimensions", "technical_specification"}:
        return document_type in {"owner_manual", "specification", "unknown"}
    return document_type != "catalog"


def _technical_topic_matches(
    chunk: Chunk,
    needs: InformationNeeds,
    query_text: str | None,
) -> tuple[str, ...]:
    primary_metadata = normalize_technical_token(
        " ".join(
            value
            for value in (
                chunk.content_type,
                chunk.chunk_kind,
            )
            if value
        )
    )
    section_metadata = normalize_technical_token(
        " ".join(
            value
            for value in (
                chunk.section_title,
                chunk.section_path,
            )
            if value
        )
    )
    terms = tuple(
        dict.fromkeys(
            (
                *needs.technical,
                *extract_query_terms(query_text or ""),
            )
        )
    )
    return tuple(
        term
        for term in terms
        if (
            normalized := normalize_technical_token(term)
        )
        and len(normalized) >= 4
        and (
            normalized in primary_metadata
            or (
                len(normalized) >= 8
                and normalized in section_metadata
            )
        )
    )


def _contains_generation_signal(chunk: Chunk) -> bool:
    text = f"{chunk.filename or ''} {chunk.relative_path or ''} {chunk.text[:1000]}".casefold()
    return any(term in text for term in ("generation", "rev", "revision", "series"))
