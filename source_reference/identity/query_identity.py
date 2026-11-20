from __future__ import annotations

import re
from dataclasses import dataclass


_ALPHANUMERIC_BASE = (
    r"(?=[A-Z0-9]{4,24}(?![A-Z0-9]))"
    r"(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*\d)[A-Z0-9]{4,24}"
)
_SHORT_PREFIX_SEGMENTED_IDENTIFIER = (
    r"(?!(?:FIND|SHOW|MODEL|MPN|SKU|UPC|GTIN|EAN|ALIAS|AKA|"
    r"IS|NO|PART|KIT)\b)"
    r"(?:"
    r"(?-i:[A-Z]{2,12})\s+\d{1,8}(?:\s+(?-i:[A-Z0-9]{1,8})){0,2}"
    r"|(?-i:[A-Z]{2,12})\s*[-/'._]\s*\d{1,8}[A-Z0-9]{0,8}"
    r"(?:\s*[-/'._]\s*[A-Z0-9]{1,8}){0,2}"
    r")"
)
_SPACED_IDENTIFIER = (
    r"(?=[A-Z0-9]{4,18}\s)"
    r"(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*\d)[A-Z0-9]{4,18}"
    r"(?:\s+(?=[A-Z0-9]*\d)[A-Z0-9]{1,8}){1,3}"
)
IDENTIFIER_PATTERN = re.compile(
    r"(?<![A-Z0-9])(?:"
    + _SHORT_PREFIX_SEGMENTED_IDENTIFIER
    + r"|"
    + _SPACED_IDENTIFIER
    + r"|"
    + r"[A-Z]{1,12}[-/]\d{1,8}[A-Z0-9]{0,8}"
    + r"|"
    + r"[A-Z]{1,8}[-/]\d{1,8}(?:[-/][A-Z0-9]{1,8}){0,3}"
    + r"|"
    + _ALPHANUMERIC_BASE
    + r"(?:[-/][A-Z0-9]{1,8}){1,3}"
    + r"|"
    + _ALPHANUMERIC_BASE
    + r"|\d{2,8}[-/][A-Z0-9]{1,8}(?:[-/][A-Z0-9]{1,8}){0,3}"
    + r"|\d{2,8}[A-Z][A-Z0-9]{0,8}"
    + r")(?![A-Z0-9])",
    re.I,
)
LABELED_NUMERIC_IDENTIFIER_PATTERN = re.compile(
    r"\b(?P<label>UPC|GTIN|EAN)\s*"
    r"(?:NUMBER|NO\.?|#)?\s*[:#-]?\s*(?P<value>\d{8,14})\b",
    re.I,
)
IDENTIFIER_LABEL_PATTERN = re.compile(
    r"\b(?P<label>MODEL|MPN|SKU|UPC|GTIN|EAN|ALIAS|AKA)\s*"
    r"(?:NUMBER|NO\.?|#)?\s*[:#-]?\s*$",
    re.I,
)
SHORT_MODEL_IDENTIFIER_PATTERN = re.compile(
    r"(?<![A-Z0-9])(?P<value>[A-Z]{1,2}\d{1,2}[A-Z]?)(?![A-Z0-9])",
    re.I,
)
SHORT_IDENTIFIER_SCHEMA_CONTEXT_PATTERN = re.compile(
    r"\b(?:compatible|compatibility|document|fit|fits|fuel|installation|kit|"
    r"manual|model|mpn|part|product|rating|replacement|series|service|sku|"
    r"specification|support|supported|supports|system|type|types|unit)\b",
    re.I,
)

FALSE_POSITIVE_WORDS = {
    "CALL",
    "FAX",
    "FEET",
    "IN",
    "INCH",
    "INCHES",
    "LIMITED",
    "ONLINE",
    "PRODUCT",
    "WARRANTY",
}


@dataclass(frozen=True)
class QueryIdentifier:
    raw: str
    normalized: str
    span_start: int
    span_end: int
    identifier_type: str
    confidence: str
    basis: str
    family_like: bool = False


@dataclass(frozen=True)
class QueryIdentity:
    raw_question: str
    identifiers: tuple[QueryIdentifier, ...]
    unresolved_or_family_like: bool
    rejected_false_positive_spans: tuple[str, ...] = ()


def normalize_identifier(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def parse_query_identity(question: str) -> QueryIdentity:
    raw_question = question or ""
    identifiers: list[QueryIdentifier] = []
    rejected: list[str] = []
    seen: dict[str, int] = {}
    matches = [
        (match.start(), match.end(), match.group(0), None, "recognized_identifier_grammar")
        for match in IDENTIFIER_PATTERN.finditer(raw_question)
    ]
    matches.extend(
        (
            match.start("value"),
            match.end("value"),
            match.group("value"),
            match.group("label"),
            "labeled_numeric_identifier",
        )
        for match in LABELED_NUMERIC_IDENTIFIER_PATTERN.finditer(raw_question)
    )
    occupied = tuple((start, end) for start, end, *_ in matches)
    matches.extend(
        (
            match.start("value"),
            match.end("value"),
            match.group("value"),
            "MODEL",
            "short_identifier_with_schema_context",
        )
        for match in SHORT_MODEL_IDENTIFIER_PATTERN.finditer(raw_question)
        if not any(
            start <= match.start("value") and match.end("value") <= end
            for start, end in occupied
        )
        and _has_short_identifier_schema_context(
            raw_question,
            match.start("value"),
            match.end("value"),
        )
    )
    for span_start, span_end, raw, explicit_label, basis in sorted(matches):
        normalized = normalize_identifier(raw)
        if _is_false_positive(raw, normalized) or _is_descriptive_measurement(
            raw_question,
            span_end,
        ):
            rejected.append(raw)
            continue
        identifier_type = _identifier_type(
            raw_question,
            span_start,
            raw,
            explicit_label=explicit_label,
        )
        if normalized in seen:
            existing_index = seen[normalized]
            existing = identifiers[existing_index]
            if existing.identifier_type != identifier_type:
                identifiers[existing_index] = QueryIdentifier(
                    raw=existing.raw,
                    normalized=existing.normalized,
                    span_start=existing.span_start,
                    span_end=existing.span_end,
                    identifier_type="UNKNOWN_IDENTIFIER",
                    confidence="medium",
                    basis="conflicting_type_labels",
                    family_like=existing.family_like,
                )
            continue
        identifiers.append(
            QueryIdentifier(
                raw=raw,
                normalized=normalized,
                span_start=span_start,
                span_end=span_end,
                identifier_type=identifier_type,
                confidence="high",
                basis=basis,
                family_like=_is_family_like(raw),
            )
        )
        seen[normalized] = len(identifiers) - 1
    return QueryIdentity(
        raw_question=raw_question,
        identifiers=tuple(identifiers),
        unresolved_or_family_like=not identifiers or any(item.family_like for item in identifiers),
        rejected_false_positive_spans=tuple(rejected),
    )


def _identifier_type(
    question: str,
    span_start: int,
    raw: str,
    *,
    explicit_label: str | None = None,
) -> str:
    label = explicit_label
    if label is None:
        prefix = question[max(0, span_start - 32) : span_start]
        match = IDENTIFIER_LABEL_PATTERN.search(prefix)
        label = match.group("label") if match else None
    normalized_label = (label or "").upper()
    if normalized_label in {"UPC", "GTIN", "EAN"}:
        return "UPC"
    if normalized_label in {"MODEL", "MPN", "SKU", "ALIAS", "AKA"}:
        return "ALIAS" if normalized_label == "AKA" else normalized_label
    if re.match(r"^[A-Z]", raw, re.I):
        return "MODEL"
    return "UNKNOWN_IDENTIFIER"


def _has_short_identifier_schema_context(
    question: str,
    span_start: int,
    span_end: int,
) -> bool:
    context = question[max(0, span_start - 48) : span_end + 48]
    return bool(SHORT_IDENTIFIER_SCHEMA_CONTEXT_PATTERN.search(context))


def _is_family_like(raw: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{1,8}\d{1,8}", raw, re.I))


def _is_false_positive(raw: str, normalized: str) -> bool:
    words = {word.upper() for word in re.findall(r"[A-Z]+", raw, re.I)}
    spaced_segments = re.findall(r"[A-Za-z]+|\d+", raw)
    spaced_descriptive_phrase = (
        bool(re.search(r"\s", raw))
        and not any(
            any(char.isalpha() for char in segment)
            and any(char.isdigit() for char in segment)
            for segment in re.findall(r"[A-Za-z0-9]+", raw)
        )
        and any(
            segment.isalpha() and not segment.isupper()
            for segment in spaced_segments
        )
    )
    return (
        len(normalized) < 2
        or len(normalized) > 32
        or not any(char.isdigit() for char in normalized)
        or bool(words & FALSE_POSITIVE_WORDS)
        or spaced_descriptive_phrase
        or bool(re.fullmatch(r"(?:19|20)\d{2}", raw))
        or bool(re.fullmatch(r"\d{5}(?:-\d{4})?", raw))
    )


def _is_descriptive_measurement(question: str, span_end: int) -> bool:
    suffix = question[span_end : span_end + 16]
    return bool(
        re.match(
            r"\s*[- ]?\s*(?:inch(?:es)?\b|in\.?\b|[\"″])",
            suffix,
            re.I,
        )
    )
