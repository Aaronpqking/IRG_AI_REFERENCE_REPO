from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any, Mapping
import unicodedata

from src.source_serialization import serialize_sources


PASS = "PASS"
MISSING_CITATION = "MISSING_CITATION"
MALFORMED_CITATION = "MALFORMED_CITATION"
UNKNOWN_SOURCE = "UNKNOWN_SOURCE"
PAGE_MISMATCH = "PAGE_MISMATCH"
SOURCE_TYPE_MISMATCH = "SOURCE_TYPE_MISMATCH"
CROSS_PRODUCT_CITATION = "CROSS_PRODUCT_CITATION"
NOT_REQUIRED = "NOT_REQUIRED"
SUPPORTED = "SUPPORTED"
PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
UNSUPPORTED = "UNSUPPORTED"
VALIDATOR_UNCERTAIN = "VALIDATOR_UNCERTAIN"
BINDING_MISSING = "BINDING_MISSING"
BINDING_INVALID = "BINDING_INVALID"
UNVERIFIABLE = VALIDATOR_UNCERTAIN
CITATION_BINDING_SCHEMA_VERSION = "citation_binding.v1.9.38"

_CITATION_START = re.compile(r"\[\s*source\s*:", re.IGNORECASE)
_CITATION = re.compile(
    r"\[\s*source\s*:\s*(?P<body>[^\[\]]+?)\s*\]",
    re.IGNORECASE,
)
_DATABASE_BODY = re.compile(
    r"^(?P<label>.+?),\s*product(?:_|\s+)id\s*(?:[:=#]?\s*)"
    r"(?P<product_id>[0-9]+)\s*$",
    re.IGNORECASE,
)
_PDF_BODY = re.compile(
    r"^(?P<label>.+?),\s*page\s+(?P<page>[0-9]+)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedCitation:
    raw: str
    source_type: str
    source_label: str
    page: int | None = None
    product_id: str | None = None
    citation_id: str | None = None
    start: int | None = None
    end: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CitationValidationResult:
    status: str
    citations: tuple[ParsedCitation, ...]
    matched_source_ids: tuple[str, ...]
    unmatched_citations: tuple[str, ...]
    missing_required_citations: bool
    reason_codes: tuple[str, ...]
    grounding_status: str = UNVERIFIABLE
    support_results: tuple[dict[str, Any], ...] = ()
    binding_status: str = VALIDATOR_UNCERTAIN
    bindings: tuple[dict[str, Any], ...] = ()
    binding_schema_version: str = CITATION_BINDING_SCHEMA_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "citations": [citation.as_dict() for citation in self.citations],
            "matched_source_ids": list(self.matched_source_ids),
            "unmatched_citations": list(self.unmatched_citations),
            "missing_required_citations": self.missing_required_citations,
            "reason_codes": list(self.reason_codes),
            "grounding_status": self.grounding_status,
            "support_results": list(self.support_results),
            "binding_status": self.binding_status,
            "bindings": list(self.bindings),
            "binding_schema_version": self.binding_schema_version,
        }


def validation_supports_factual_answer(
    validation: Mapping[str, Any] | CitationValidationResult,
) -> bool:
    payload = (
        validation.as_dict()
        if isinstance(validation, CitationValidationResult)
        else validation
    )
    return (
        payload.get("status") == PASS
        and payload.get("grounding_status") == SUPPORTED
    )


def parse_citations(answer: str) -> tuple[tuple[ParsedCitation, ...], tuple[str, ...]]:
    text = answer or ""
    matches = tuple(_CITATION.finditer(text))
    malformed: list[str] = []
    if len(tuple(_CITATION_START.finditer(text))) != len(matches):
        malformed.append("UNCLOSED_OR_NESTED_CITATION")
    parsed: list[ParsedCitation] = []
    for index, match in enumerate(matches, 1):
        raw = match.group(0)
        body = match.group("body").strip()
        database = _DATABASE_BODY.fullmatch(body)
        if database:
            parsed.append(
                ParsedCitation(
                    raw=raw,
                    source_type="database",
                    source_label=database.group("label").strip(),
                    product_id=database.group("product_id"),
                    citation_id=f"citation:{index}",
                    start=match.start(),
                    end=match.end(),
                )
            )
            continue
        pdf = _PDF_BODY.fullmatch(body)
        if pdf:
            parsed.append(
                ParsedCitation(
                    raw=raw,
                    source_type="pdf",
                    source_label=pdf.group("label").strip(),
                    page=int(pdf.group("page")),
                    citation_id=f"citation:{index}",
                    start=match.start(),
                    end=match.end(),
                )
            )
            continue
        malformed.append(raw)
    return tuple(parsed), tuple(malformed)


def validate_answer_citations(
    answer: str,
    answer_sources: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    citations_required: bool | None = None,
) -> CitationValidationResult:
    sources = serialize_sources(answer_sources)
    for raw_source in answer_sources:
        raw = asdict(raw_source) if hasattr(raw_source, "__dataclass_fields__") else dict(raw_source)
        preview = raw.get("evidence_text") or raw.get("text_preview") or raw.get("text")
        serialized = serialize_sources([raw])
        source_id = serialized[0].get("source_id") if serialized else None
        for source in sources:
            if source.get("source_id") == source_id:
                if preview:
                    prior = str(source.get("evidence_text") or "")
                    value = str(preview)
                    source["evidence_text"] = (
                        prior
                        if value in prior
                        else "\n\n".join(
                            item for item in (prior, value) if item
                        )
                    )
                for field in (
                    "chunk_id",
                    "document_id",
                    "applicable_product_ref_ids",
                    "applicable_product_display_identities",
                ):
                    if raw.get(field):
                        source[field] = raw[field]
                structural = raw.get("structural_evidence") or []
                if structural:
                    existing = list(source.get("structural_evidence") or [])
                    known = {
                        _structural_record_key(item) for item in existing
                    }
                    for item in structural:
                        record = dict(item)
                        key = _structural_record_key(record)
                        if key not in known:
                            existing.append(record)
                            known.add(key)
                    source["structural_evidence"] = existing
    required = bool(sources) if citations_required is None else citations_required
    citations, malformed = parse_citations(answer)
    if malformed:
        return CitationValidationResult(
            status=MALFORMED_CITATION,
            citations=citations,
            matched_source_ids=(),
            unmatched_citations=malformed,
            missing_required_citations=False,
            reason_codes=(MALFORMED_CITATION,),
            grounding_status=UNSUPPORTED,
            binding_status=BINDING_INVALID,
        )
    if not citations:
        status = MISSING_CITATION if required else NOT_REQUIRED
        return CitationValidationResult(
            status=status,
            citations=(),
            matched_source_ids=(),
            unmatched_citations=(),
            missing_required_citations=required,
            reason_codes=(status,),
            grounding_status=UNSUPPORTED if required else NOT_REQUIRED,
            binding_status=BINDING_MISSING if required else NOT_REQUIRED,
        )

    matched: list[str] = []
    matched_pairs: list[tuple[ParsedCitation, Mapping[str, Any]]] = []
    unmatched: list[str] = []
    page_mismatches: list[str] = []
    type_mismatches: list[str] = []
    for citation in citations:
        same_type = [
            source
            for source in sources
            if source.get("source_type") == citation.source_type
        ]
        if citation.source_type == "database":
            matches = [
                source
                for source in same_type
                if str(source.get("product_id")) == citation.product_id
            ]
        else:
            identity_matches = [
                source
                for source in same_type
                if _pdf_identity_matches(citation.source_label, source)
            ]
            matches = [
                source
                for source in identity_matches
                if _page_matches(citation.page, source)
            ]
            if identity_matches and not matches:
                page_mismatches.append(citation.raw)
                continue
        if matches:
            matched_pairs.extend((citation, source) for source in matches)
            matched.extend(
                str(
                    source.get("evidence_id")
                    or source.get("source_id")
                )
                for source in matches
                if source.get("evidence_id")
                or source.get("source_id")
            )
            continue
        if _matches_other_source_type(citation, sources):
            type_mismatches.append(citation.raw)
        else:
            unmatched.append(citation.raw)

    reason_codes: list[str] = []
    if page_mismatches:
        reason_codes.append(PAGE_MISMATCH)
    if type_mismatches:
        reason_codes.append(SOURCE_TYPE_MISMATCH)
    if unmatched:
        reason_codes.append(UNKNOWN_SOURCE)
    if len(citations) != len({citation.raw.casefold() for citation in citations}):
        reason_codes.append("DUPLICATE_CITATION_IGNORED")
    status = (
        PAGE_MISMATCH
        if page_mismatches
        else SOURCE_TYPE_MISMATCH
        if type_mismatches
        else UNKNOWN_SOURCE
        if unmatched
        else PASS
    )
    if status == PASS:
        reason_codes.insert(0, PASS)
    support_results, grounding_status = _validate_claim_support(
        answer, matched_pairs, status, sources
    )
    if any(
        item.get("product_owner_status") == "MISMATCH"
        for item in support_results
    ):
        reason_codes.append(CROSS_PRODUCT_CITATION)
    binding_status = _binding_status(
        status=status,
        grounding_status=grounding_status,
        unmatched=unmatched,
    )
    bindings = _build_claim_source_bindings(
        answer,
        citations,
        matched_pairs,
        support_results,
        unresolved_status=(
            binding_status if status != PASS else BINDING_MISSING
        ),
    )
    if binding_status not in {SUPPORTED, NOT_REQUIRED}:
        reason_codes.append(binding_status)
    return CitationValidationResult(
        status=status,
        citations=citations,
        matched_source_ids=tuple(dict.fromkeys(matched)),
        unmatched_citations=tuple(
            dict.fromkeys([*page_mismatches, *type_mismatches, *unmatched])
        ),
        missing_required_citations=False,
        reason_codes=tuple(reason_codes),
        grounding_status=grounding_status,
        support_results=support_results,
        binding_status=binding_status,
        bindings=bindings,
    )


_SUPPORT_TOKEN = re.compile(r"[a-z0-9][a-z0-9._/-]*", re.IGNORECASE)
_STOPWORDS = {
    "about", "after", "also", "answer", "before", "from", "have", "into",
    "page", "source", "that", "the", "their", "this", "with", "your",
}
_CLAIM_SENTENCE_BOUNDARY = re.compile(r"(?:[!?]\s+|\.\s+(?=[A-Z0-9]))")
_CLAIM_CLAUSE_BOUNDARY = re.compile(
    r"(?:\r?\n|;|,\s*(?:and|but|while|whereas|so)\s+|\s+(?:and|but|while|whereas)\s+)",
    re.IGNORECASE,
)
_COORDINATED_SCOPE_BOUNDARY = re.compile(r"[;\r\n]")
_COORDINATION_REJECT = re.compile(
    r"\b(?:or|respectively|unlike)\b|\bcompared\s+with\b",
    re.IGNORECASE,
)
_LEADING_CLAIM_CONNECTOR = re.compile(
    r"^[\s,;:.]*(?:(?:and|but|while|whereas)\b[\s,;:.]*)?",
    re.IGNORECASE,
)
_GROUNDING_UNIT_PATTERNS = (
    (
        re.compile(
            r"\b(?:square[\s-]*inch(?:es)?|sq\.?\s*(?:inch(?:es)?|in\.?))\b",
            re.IGNORECASE,
        ),
        "squareinch",
    ),
    (re.compile(r"\b(?:inch(?:es)?|in)\b\.?", re.IGNORECASE), "inch"),
    (re.compile(r"\b(?:feet|foot|ft\.?)\b", re.IGNORECASE), "foot"),
    (re.compile(r"\b(?:watts?|w)\b", re.IGNORECASE), "watt"),
    (re.compile(r"\b(?:volts?|v)\b", re.IGNORECASE), "volt"),
    (re.compile(r"\b(?:btus?|btu/hr)\b", re.IGNORECASE), "btu"),
)
_GROUNDING_UNITS = frozenset(
    replacement for _, replacement in _GROUNDING_UNIT_PATTERNS
)
_RELATION_TERMS = frozenset(
    {
        "difference",
        "equal",
        "equals",
        "fewer",
        "greater",
        "higher",
        "larger",
        "less",
        "longer",
        "lower",
        "more",
        "same",
        "shorter",
        "smaller",
        "than",
    }
)
_DIFFERENCE_TERMS = frozenset(
    {
        "difference",
        "fewer",
        "greater",
        "higher",
        "larger",
        "less",
        "longer",
        "lower",
        "more",
        "shorter",
        "smaller",
    }
)
_COMPARISON_FUNCTION_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "at",
        "both",
        "each",
        "for",
        "has",
        "have",
        "is",
        "listed",
        "model",
        "models",
        "neither",
        "nor",
        "of",
        "one",
        "than",
        "the",
        "they",
        "which",
        "with",
    }
)


@dataclass(frozen=True)
class _ClaimBinding:
    text: str
    group_id: int


def _validate_claim_support(
    answer: str,
    pairs: list[tuple[ParsedCitation, Mapping[str, Any]]],
    resolution_status: str,
    all_sources: list[Mapping[str, Any]],
) -> tuple[tuple[dict[str, Any], ...], str]:
    if resolution_status != PASS:
        return (), UNSUPPORTED
    results: list[dict[str, Any]] = []
    identity_by_ref = _product_identity_by_ref(all_sources)
    product_identities = _all_product_identities(all_sources, identity_by_ref)
    claim_bindings = _claim_bindings_by_citation(answer, pairs)
    citation_ids: dict[int, str] = {}
    for citation, _ in pairs:
        citation_ids.setdefault(
            id(citation),
            citation.citation_id or f"citation:{len(citation_ids) + 1}",
        )
    for citation, source in pairs:
        binding = claim_bindings.get(id(citation), _ClaimBinding("", 0))
        claim = binding.text
        evidence_text = str(
            source.get("evidence_text")
            or source.get("text")
            or source.get("text_preview")
            or ""
        )
        structural_match = _supporting_structural_evidence(claim, source)
        if structural_match is not None:
            evidence_text = str(structural_match["evidence_text"])
        source_metadata = " ".join(
            str(source.get(field) or "")
            for field in ("relative_path", "filename", "document_id")
        )
        grounding_text = " ".join(
            value for value in (evidence_text, source_metadata) if value
        )
        owner_identities = _source_owner_identities(source, identity_by_ref)
        normalized_claim = _normalize_grounding_text(claim)
        claim_identities = {
            identity
            for identity in product_identities
            if identity in normalized_claim
        }
        implicit_two_owner_comparison = bool(
            len(product_identities) == 2
            and len(claim_identities) == 1
            and _implicit_comparison_set_claim(normalized_claim)
        )
        owner_mismatch = bool(
            owner_identities
            and claim_identities
            and owner_identities.isdisjoint(claim_identities)
            and not implicit_two_owner_comparison
        )
        if not evidence_text:
            support = UNVERIFIABLE
            overlap: list[str] = []
            claim_tokens: set[str] = set()
            evidence_tokens: set[str] = set()
            claim_numbers: set[str] = set()
            evidence_numbers: set[str] = set()
            claim_units: set[str] = set()
            evidence_units: set[str] = set()
            decision_rule = "EVIDENCE_TEXT_ABSENT"
        else:
            claim_tokens = _support_tokens(claim)
            evidence_tokens = _support_tokens(grounding_text) | _support_tokens(
                re.sub(r"[\\/_.-]+", " ", source_metadata)
            )
            overlap = sorted(claim_tokens & evidence_tokens)
            claim_numbers = _grounding_numbers(claim)
            evidence_numbers = _grounding_numbers(grounding_text)
            claim_units = _grounding_units(claim)
            evidence_units = _grounding_units(grounding_text)
            numbers_supported = (
                not claim_numbers or claim_numbers <= evidence_numbers
            )
            units_supported = not claim_units or claim_units <= evidence_units
            contextual_overlap = bool(
                set(overlap) - claim_numbers - claim_units
            ) or bool(claim_units & evidence_units)
            support = (
                SUPPORTED
                if numbers_supported and units_supported and contextual_overlap
                else UNSUPPORTED
            )
            decision_rule = (
                "NUMBERS_UNSUPPORTED"
                if not numbers_supported
                else "UNITS_UNSUPPORTED"
                if not units_supported
                else "NO_CONTEXTUAL_OVERLAP"
                if not contextual_overlap
                else "CANONICAL_VALUE_AND_CONTEXT_MATCH"
            )
            if support == SUPPORTED and structural_match is not None:
                decision_rule = "STRUCTURAL_ROW_CELL_MATCH"
        if owner_mismatch:
            support = UNSUPPORTED
            decision_rule = "PRODUCT_OWNER_MISMATCH"
        results.append(
            {
                "citation": citation.raw,
                "citation_id": citation_ids[id(citation)],
                "source_id": source.get("source_id"),
                "evidence_id": source.get("evidence_id"),
                "status": support,
                "claim_text": claim,
                "normalized_claim_text": normalized_claim,
                "claim_tokens": sorted(claim_tokens),
                "claim_numbers": sorted(claim_numbers),
                "evidence_numbers": sorted(evidence_numbers),
                "claim_units": sorted(claim_units),
                "evidence_units": sorted(evidence_units),
                "overlap_tokens": overlap[:12],
                "decision_rule": decision_rule,
                "structural_identity": (
                    _public_structural_identity(structural_match)
                    if structural_match is not None
                    else None
                ),
                "product_owner_status": (
                    "MISMATCH" if owner_mismatch else "PASS"
                ),
                "_claim_group_id": binding.group_id,
                "_claim_identities": sorted(claim_identities),
                "_source_owner_identities": sorted(owner_identities),
                "_evidence_tokens": sorted(evidence_tokens),
                "_evidence_text": evidence_text,
                "_has_evidence_text": bool(evidence_text),
            }
        )
    group_statuses: list[str] = []
    grouped_results: dict[int, list[dict[str, Any]]] = {}
    for result in results:
        grouped_results.setdefault(result["_claim_group_id"], []).append(result)
    for group in grouped_results.values():
        if _requires_collective_support(group):
            group_statuses.append(
                _apply_collective_support(group, product_identities)
            )
        else:
            group_statuses.append(_aggregate_support_statuses(group))
    statuses = set(group_statuses)
    if statuses == {SUPPORTED}:
        overall = SUPPORTED
    elif SUPPORTED in statuses or PARTIALLY_SUPPORTED in statuses:
        overall = PARTIALLY_SUPPORTED
    elif statuses == {UNVERIFIABLE}:
        overall = UNVERIFIABLE
    else:
        overall = UNSUPPORTED
    for result in results:
        for field in tuple(result):
            if field.startswith("_"):
                result.pop(field)
    return tuple(results), overall


def _aggregate_support_statuses(results: list[dict[str, Any]]) -> str:
    statuses = {str(result["status"]) for result in results}
    if statuses == {SUPPORTED}:
        return SUPPORTED
    if SUPPORTED in statuses:
        return PARTIALLY_SUPPORTED
    if statuses == {UNVERIFIABLE}:
        return UNVERIFIABLE
    return UNSUPPORTED


def _requires_collective_support(results: list[dict[str, Any]]) -> bool:
    citations = {str(result["citation_id"]) for result in results}
    identities = {
        identity
        for result in results
        for identity in result["_claim_identities"]
    }
    return len(citations) > 1 or len(identities) > 1


def _apply_collective_support(
    results: list[dict[str, Any]],
    product_identities: set[str],
) -> str:
    claim = str(results[0].get("claim_text") or "")
    elements = _atomic_claim_elements(claim, product_identities)
    if not elements:
        return _aggregate_support_statuses(results)

    direct_elements = [
        element
        for element in elements
        if element["element_type"] in {"factual_value", "factual_context"}
    ]
    for element in direct_elements:
        _evaluate_direct_element(element, results)
    for element in elements:
        if element["element_type"] == "owner_group_fact":
            _evaluate_owner_group_element(element, results)

    by_id = {str(element["element_id"]): element for element in elements}
    for element in elements:
        if element["element_type"] == "derived_comparison":
            dependencies = [
                by_id[dependency]
                for dependency in element["derived_from_element_ids"]
            ]
            if dependencies and all(
                dependency["status"] == SUPPORTED
                for dependency in dependencies
            ):
                _inherit_element_support(element, dependencies)

    for element in elements:
        if element["element_type"] == "comparative_relation":
            _evaluate_relation_element(element, elements, claim, results)
    for element in elements:
        if (
            element["element_type"] == "comparative_relation"
            and element["status"] == SUPPORTED
        ):
            _support_relation_context_elements(element, elements, claim)

    citation_ids = {str(result["citation_id"]) for result in results}
    contributing_citations = {
        citation_id
        for element in elements
        for citation_id in element["supporting_citation_ids"]
    }
    supported_elements = [
        element for element in elements if element["status"] == SUPPORTED
    ]
    partially_supported_elements = [
        element
        for element in elements
        if element["status"] == PARTIALLY_SUPPORTED
    ]
    all_elements_supported = len(supported_elements) == len(elements)
    all_citations_contribute = citation_ids <= contributing_citations
    if all_elements_supported and all_citations_contribute:
        group_status = SUPPORTED
    elif supported_elements or partially_supported_elements:
        group_status = PARTIALLY_SUPPORTED
    elif all(not result["_has_evidence_text"] for result in results):
        group_status = UNVERIFIABLE
    else:
        group_status = UNSUPPORTED

    public_elements = [_public_claim_element(element) for element in elements]
    for result in results:
        supported_ids = [
            str(element["element_id"])
            for element in elements
            if id(result) in element["_supporting_result_ids"]
        ]
        result["supported_element_ids"] = supported_ids
        result["claim_elements"] = public_elements
        result["collective_claim_status"] = group_status
        if supported_ids:
            result["status"] = SUPPORTED
            result["decision_rule"] = "COLLECTIVE_ELEMENT_CONTRIBUTION"
        elif result["_has_evidence_text"]:
            result["status"] = UNSUPPORTED
            result["decision_rule"] = "IRRELEVANT_CITATION"
        else:
            result["status"] = UNVERIFIABLE
            result["decision_rule"] = "EVIDENCE_TEXT_ABSENT"
    return group_status


def _evaluate_direct_element(
    element: dict[str, Any],
    results: list[dict[str, Any]],
) -> None:
    required_numbers = set(element["required_numbers"])
    required_units = set(element["required_units"])
    contextual_terms = set(element["contextual_terms"])
    owner = element.get("product_owner")
    for result in results:
        if result["product_owner_status"] == "MISMATCH":
            continue
        source_owners = set(result["_source_owner_identities"])
        if owner and owner not in source_owners:
            continue
        evidence_numbers = set(result["evidence_numbers"])
        evidence_units = set(result["evidence_units"])
        evidence_tokens = set(result["_evidence_tokens"])
        numbers_supported = required_numbers <= evidence_numbers
        units_supported = required_units <= evidence_units
        context_overlap = contextual_terms & evidence_tokens
        context_supported = bool(context_overlap) or bool(
            required_units & evidence_units
        )
        if not contextual_terms and owner and owner in source_owners:
            context_supported = True
        if numbers_supported and units_supported and context_supported:
            element["supporting_citation_ids"].append(result["citation_id"])
            element["supporting_source_ids"].append(
                result.get("evidence_id") or result.get("source_id")
            )
            element["_supporting_result_ids"].add(id(result))
    element["supporting_citation_ids"] = sorted(
        set(element["supporting_citation_ids"])
    )
    element["supporting_source_ids"] = sorted(
        str(source_id)
        for source_id in set(element["supporting_source_ids"])
        if source_id
    )
    if element["supporting_citation_ids"]:
        element["status"] = SUPPORTED


def _evaluate_owner_group_element(
    element: dict[str, Any],
    results: list[dict[str, Any]],
) -> None:
    premises = element["owner_premises"]
    for premise in premises:
        _evaluate_direct_element(premise, results)
    supported = [
        premise for premise in premises if premise["status"] == SUPPORTED
    ]
    if supported:
        element["supporting_citation_ids"] = sorted(
            {
                citation_id
                for premise in supported
                for citation_id in premise["supporting_citation_ids"]
            }
        )
        element["supporting_source_ids"] = sorted(
            {
                source_id
                for premise in supported
                for source_id in premise["supporting_source_ids"]
            }
        )
        element["_supporting_result_ids"] = {
            result_id
            for premise in supported
            for result_id in premise["_supporting_result_ids"]
        }
    if len(supported) == len(premises):
        element["status"] = SUPPORTED
    elif supported:
        element["status"] = PARTIALLY_SUPPORTED


def _public_claim_element(element: dict[str, Any]) -> dict[str, Any]:
    public = {
        key: value
        for key, value in element.items()
        if not key.startswith("_") and key != "owner_premises"
    }
    if "owner_premises" in element:
        public["owner_premises"] = [
            _public_claim_element(premise)
            for premise in element["owner_premises"]
        ]
    return public


def _inherit_element_support(
    element: dict[str, Any],
    dependencies: list[dict[str, Any]],
) -> None:
    element["supporting_citation_ids"] = sorted(
        {
            citation_id
            for dependency in dependencies
            for citation_id in dependency["supporting_citation_ids"]
        }
    )
    element["supporting_source_ids"] = sorted(
        {
            source_id
            for dependency in dependencies
            for source_id in dependency["supporting_source_ids"]
        }
    )
    element["_supporting_result_ids"] = {
        result_id
        for dependency in dependencies
        for result_id in dependency["_supporting_result_ids"]
    }
    element["status"] = SUPPORTED


def _evaluate_relation_element(
    relation: dict[str, Any],
    elements: list[dict[str, Any]],
    claim: str,
    results: list[dict[str, Any]],
) -> None:
    owners = list(relation["product_owners"])
    terms = set(relation["relation_terms"])
    relation_kind = _relation_kind(claim, terms)
    owner_groups = [
        element
        for element in elements
        if element["element_type"] == "owner_group_fact"
        and element["status"] == SUPPORTED
        and set(owners) <= set(element["product_owners"])
    ]
    if owner_groups and relation_kind == "equal":
        _inherit_element_support(relation, [owner_groups[0]])
        return
    factual = [
        element
        for element in elements
        if element["element_type"] == "factual_value"
        and not element.get("derived_from_element_ids")
        and element["status"] == SUPPORTED
        and element.get("product_owner")
    ]
    primary_by_owner: dict[str, dict[str, Any]] = {}
    for element in factual:
        primary_by_owner.setdefault(str(element["product_owner"]), element)
    canonical_premises: list[dict[str, Any]] = []
    if len(primary_by_owner) < len(owners):
        canonical_premises = _canonical_relation_premises(
            claim,
            owners,
            results,
        )
        primary_by_owner = {
            str(premise["product_owner"]): premise
            for premise in canonical_premises
        }
        if len(primary_by_owner) < len(owners):
            return
        relation["canonical_premises"] = [
            _public_claim_element(premise)
            for premise in canonical_premises
        ]
    dependencies: list[dict[str, Any]] = []
    if relation_kind == "equal":
        dependencies = [primary_by_owner[owner] for owner in owners]
        values = {
            dependency["required_numbers"][0]
            for dependency in dependencies
        }
        if len(values) != 1:
            return
    else:
        derived = [
            element
            for element in elements
            if element["element_type"] == "derived_comparison"
            and element["status"] == SUPPORTED
        ]
        if derived:
            dependencies = derived
        else:
            direction = relation_kind
            subject = _comparison_subject(claim, owners, terms)
            if not direction or not subject:
                return
            other_owners = [owner for owner in owners if owner != subject]
            if not other_owners:
                return
            subject_value = _decimal_value(
                primary_by_owner[subject]["required_numbers"][0]
            )
            other_value = _decimal_value(
                primary_by_owner[other_owners[0]]["required_numbers"][0]
            )
            if subject_value is None or other_value is None:
                return
            if direction == "greater" and subject_value <= other_value:
                return
            if direction == "less" and subject_value >= other_value:
                return
            dependencies = [
                primary_by_owner[subject],
                primary_by_owner[other_owners[0]],
            ]
            _support_matching_difference_element(
                elements,
                dependencies,
            )
    if dependencies:
        _inherit_element_support(relation, dependencies)


def _relation_kind(claim: str, terms: set[str]) -> str | None:
    if terms & {"same", "equal", "equals"}:
        return "equal"
    direction = _comparison_direction(terms)
    if direction and re.search(r"\bneither\b", claim, re.IGNORECASE):
        return "equal"
    return direction


def _implicit_comparison_set_claim(claim: str) -> bool:
    return bool(
        re.search(
            r"\bthe\s+(?:fewer|greater|higher|larger|less|longer|lower|"
            r"more|shorter|smaller)\b",
            claim,
            re.IGNORECASE,
        )
    )


def _support_relation_context_elements(
    relation: dict[str, Any],
    elements: list[dict[str, Any]],
    claim: str,
) -> None:
    attribute_terms, _ = _comparison_attribute_scope(
        claim,
        set(relation["product_owners"]),
    )
    if not attribute_terms:
        return
    for element in elements:
        if (
            element["element_type"] != "factual_context"
            or element["status"] == SUPPORTED
        ):
            continue
        element_terms = {
            word
            for term in element["contextual_terms"]
            for word in re.findall(r"[a-z]+", str(term).casefold())
            if word not in _COMPARISON_FUNCTION_WORDS
            and word not in _RELATION_TERMS
        }
        if element_terms and element_terms <= attribute_terms:
            _inherit_element_support(element, [relation])


def _canonical_relation_premises(
    claim: str,
    owners: list[str],
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    attribute_terms, attribute_phrases = _comparison_attribute_scope(
        claim,
        set(owners),
    )
    if not attribute_terms:
        return []
    premises: list[dict[str, Any]] = []
    for owner_index, owner in enumerate(owners):
        owner_results = [
            result
            for result in results
            if result["product_owner_status"] != "MISMATCH"
            and owner in set(result["_source_owner_identities"])
            and result["_has_evidence_text"]
        ]
        candidates: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for result in owner_results:
            for value, unit in _scoped_scalar_candidates(
                str(result["_evidence_text"]),
                attribute_terms,
                attribute_phrases,
            ):
                candidates.setdefault((value, unit), []).append(result)
        if len(candidates) != 1:
            return []
        (value, unit), supporting_results = next(iter(candidates.items()))
        premise = _new_claim_element(
            element_id=f"canonical-premise:{owner_index + 1}",
            element_type="canonical_scalar_premise",
            text=claim,
            span=(0, len(claim)),
            product_owner=owner,
            required_numbers=(value,),
            required_units=(unit,),
            contextual_terms=attribute_terms,
        )
        premise["supporting_citation_ids"] = sorted(
            {str(result["citation_id"]) for result in supporting_results}
        )
        premise["supporting_source_ids"] = sorted(
            {
                str(result.get("evidence_id") or result.get("source_id"))
                for result in supporting_results
                if result.get("evidence_id") or result.get("source_id")
            }
        )
        premise["_supporting_result_ids"] = {
            id(result) for result in supporting_results
        }
        premise["status"] = SUPPORTED
        premises.append(premise)
    units = {
        premise["required_units"][0]
        for premise in premises
    }
    if len(units) != 1:
        return []
    return premises


def _comparison_attribute_scope(
    claim: str,
    owners: set[str],
) -> tuple[set[str], set[str]]:
    normalized = _normalize_grounding_text(claim)
    for owner in sorted(owners, key=len, reverse=True):
        normalized = normalized.replace(owner, " ")
    words = re.findall(r"[a-z]+", normalized)
    excluded = _COMPARISON_FUNCTION_WORDS | _RELATION_TERMS | _GROUNDING_UNITS
    scoped = [word for word in words if word not in excluded]
    terms = set(scoped)
    phrases = {
        f"{left} {right}"
        for left, right in zip(scoped, scoped[1:])
    }
    return terms, phrases


def _scoped_scalar_candidates(
    evidence_text: str,
    attribute_terms: set[str],
    attribute_phrases: set[str],
) -> set[tuple[str, str]]:
    normalized = _normalize_grounding_text(evidence_text)
    scopes = re.split(
        r"(?:\r?\n|;|\]\s*,?\s*\[|(?<=[!?])\s+)",
        normalized,
    )
    candidates: set[tuple[str, str]] = set()
    for scope in scopes:
        lexical_scope = " ".join(re.findall(r"[a-z]+", scope))
        scope_terms = set(lexical_scope.split())
        attribute_matches = (
            any(phrase in lexical_scope for phrase in attribute_phrases)
            if attribute_phrases
            else bool(attribute_terms & scope_terms)
        )
        if not attribute_matches:
            continue
        for number in re.finditer(
            r"(?<![a-z0-9])\d+(?:\.\d+)?(?![a-z0-9])",
            scope,
        ):
            units = _immediate_units(scope, number.end())
            for unit in units:
                candidates.add((number.group(0), unit))
    return candidates


def _support_matching_difference_element(
    elements: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
) -> None:
    if len(dependencies) != 2:
        return
    left = _decimal_value(dependencies[0]["required_numbers"][0])
    right = _decimal_value(dependencies[1]["required_numbers"][0])
    if left is None or right is None:
        return
    difference = abs(left - right)
    for element in elements:
        if element["element_type"] != "factual_value":
            continue
        numbers = element.get("required_numbers") or []
        if len(numbers) != 1 or _decimal_value(numbers[0]) != difference:
            continue
        units = {
            unit
            for dependency in dependencies
            for unit in dependency.get("required_units") or []
        }
        if element.get("required_units") and not (
            set(element["required_units"]) <= units
        ):
            continue
        element["element_type"] = "derived_comparison"
        element["derivation"] = "ABSOLUTE_DIFFERENCE"
        _inherit_element_support(element, dependencies)


def _atomic_claim_elements(
    claim: str,
    product_identities: set[str],
) -> list[dict[str, Any]]:
    normalized = _normalize_grounding_text(claim)
    identities = {
        identity for identity in product_identities if identity in normalized
    }
    identity_occurrences = [
        (identity, match.start(), match.end())
        for identity in identities
        for match in re.finditer(re.escape(identity), normalized)
    ]
    number_matches = list(
        re.finditer(
            r"(?<![a-z0-9])\d+(?:\.\d+)?(?![a-z0-9])",
            normalized,
        )
    )
    relation_terms = sorted(_support_tokens(normalized) & _RELATION_TERMS)
    derived = _derived_number_dependencies(number_matches, relation_terms)
    respectively = _respectively_owner_assignments(
        normalized,
        identity_occurrences,
        number_matches,
    )
    elements: list[dict[str, Any]] = []
    for index, match in enumerate(number_matches):
        owner_group = _coordinated_owner_group(
            normalized,
            match,
            identity_occurrences,
            number_matches,
        )
        if owner_group:
            required_units = _immediate_units(normalized, match.end())
            contextual_terms = _element_context_terms(
                normalized,
                owner_group["span"][0],
                owner_group["span"][1],
                set(owner_group["owners"]),
            )
            element = _new_claim_element(
                element_id=f"element:{index + 1}",
                element_type="owner_group_fact",
                text=normalized[
                    owner_group["span"][0] : owner_group["span"][1]
                ].strip(),
                span=tuple(owner_group["span"]),
                product_owner=None,
                required_numbers=(match.group(0),),
                required_units=required_units,
                contextual_terms=contextual_terms,
            )
            element["product_owners"] = list(owner_group["owners"])
            element["owner_mentions"] = owner_group["owner_mentions"]
            element["coordination_tokens"] = owner_group[
                "coordination_tokens"
            ]
            element["shared_predicate_terms"] = owner_group[
                "predicate_terms"
            ]
            element["shared_attribute_terms"] = sorted(contextual_terms)
            element["owner_premises"] = [
                _new_claim_element(
                    element_id=f"element:{index + 1}:owner:{owner_index + 1}",
                    element_type="owner_premise",
                    text=element["text"],
                    span=tuple(owner_group["span"]),
                    product_owner=owner,
                    required_numbers=(match.group(0),),
                    required_units=required_units,
                    contextual_terms=contextual_terms,
                )
                for owner_index, owner in enumerate(owner_group["owners"])
            ]
            elements.append(element)
            continue
        span_start, span_end = _claim_element_span(normalized, match.start())
        if index in respectively:
            span_start, span_end = 0, len(normalized)
        clause_owners = [
            occurrence
            for occurrence in identity_occurrences
            if span_start <= occurrence[1] and occurrence[2] <= span_end
        ]
        owner = respectively.get(index) or _nearest_owner(
            match.start(),
            match.end(),
            clause_owners or identity_occurrences,
        )
        required_units = _immediate_units(normalized, match.end())
        contextual_terms = _element_context_terms(
            normalized,
            span_start,
            span_end,
            identities,
        )
        element = _new_claim_element(
            element_id=f"element:{index + 1}",
            element_type=(
                "derived_comparison" if index in derived else "factual_value"
            ),
            text=normalized[span_start:span_end].strip(),
            span=(span_start, span_end),
            product_owner=owner,
            required_numbers=(match.group(0),),
            required_units=required_units,
            contextual_terms=contextual_terms,
        )
        if index in derived:
            element["derived_from_element_ids"] = [
                f"element:{dependency + 1}" for dependency in derived[index]
            ]
        elements.append(element)

    if not number_matches:
        elements.extend(
            _context_only_elements(normalized, identities, identity_occurrences)
        )

    relation_identities = set(identities)
    if (
        len(product_identities) == 2
        and len(identities) == 1
        and _implicit_comparison_set_claim(normalized)
    ):
        relation_identities = set(product_identities)
    if relation_terms and (len(relation_identities) > 1 or derived):
        relation = _new_claim_element(
            element_id=f"element:{len(elements) + 1}",
            element_type="comparative_relation",
            text=normalized,
            span=(0, len(normalized)),
            product_owner=None,
            required_numbers=(),
            required_units=(),
            contextual_terms=relation_terms,
        )
        relation["product_owners"] = sorted(relation_identities)
        relation["relation_terms"] = relation_terms
        elements.append(relation)
    return elements


def _coordinated_owner_group(
    claim: str,
    number_match: re.Match[str],
    identity_occurrences: list[tuple[str, int, int]],
    number_matches: list[re.Match[str]],
) -> dict[str, Any] | None:
    scope_start, scope_end = _coordination_scope(claim, number_match.start())
    scope = claim[scope_start:scope_end]
    if _COORDINATION_REJECT.search(scope):
        return None
    scoped_numbers = [
        match
        for match in number_matches
        if scope_start <= match.start() and match.end() <= scope_end
    ]
    if len(scoped_numbers) != 1:
        return None
    occurrences = sorted(
        (
            (identity, start, end)
            for identity, start, end in identity_occurrences
            if scope_start <= start and end <= scope_end
        ),
        key=lambda item: item[1],
    )
    unique_occurrences = []
    seen_owners = set()
    for occurrence in occurrences:
        if occurrence[0] not in seen_owners:
            unique_occurrences.append(occurrence)
            seen_owners.add(occurrence[0])
    if len(unique_occurrences) < 2:
        return None
    owner_phrase = claim[
        unique_occurrences[0][1] : unique_occurrences[-1][2]
    ]
    if not re.search(r"\band\b", owner_phrase, re.IGNORECASE):
        return None
    scope_tokens = _support_tokens(scope)
    clear_cue = bool(
        scope_tokens & {"both", "each", "equal", "equals", "same"}
    )
    prefix = claim[scope_start : unique_occurrences[0][1]]
    bridge = claim[unique_occurrences[-1][2] : number_match.start()]
    attribute_for_group = bool(
        re.search(r"\bfor\b", prefix, re.IGNORECASE)
        and re.search(r"\b(?:are|is|lists?)\b", bridge, re.IGNORECASE)
    )
    if not clear_cue and not attribute_for_group:
        return None
    coordination_tokens = [
        {
            "text": match.group(0).casefold(),
            "span": [scope_start + match.start(), scope_start + match.end()],
        }
        for match in re.finditer(r"\b(?:and|both|each)\b", scope, re.IGNORECASE)
    ]
    predicate_terms = sorted(
        scope_tokens
        & {
            "are",
            "both",
            "each",
            "equal",
            "equals",
            "has",
            "have",
            "is",
            "lists",
            "same",
        }
    )
    return {
        "owners": [occurrence[0] for occurrence in unique_occurrences],
        "owner_mentions": [
            {
                "owner": identity,
                "span": [start, end],
            }
            for identity, start, end in unique_occurrences
        ],
        "coordination_tokens": coordination_tokens,
        "predicate_terms": predicate_terms,
        "span": [scope_start, scope_end],
    }


def _coordination_scope(claim: str, position: int) -> tuple[int, int]:
    start = 0
    end = len(claim)
    for boundary in _COORDINATED_SCOPE_BOUNDARY.finditer(claim):
        if boundary.end() <= position:
            start = boundary.end()
        elif boundary.start() >= position:
            end = boundary.start()
            break
    return start, end


def _respectively_owner_assignments(
    claim: str,
    identity_occurrences: list[tuple[str, int, int]],
    number_matches: list[re.Match[str]],
) -> dict[int, str]:
    if not re.search(r"\brespectively\b", claim, re.IGNORECASE):
        return {}
    owners = []
    for identity, _, _ in sorted(identity_occurrences, key=lambda item: item[1]):
        if identity not in owners:
            owners.append(identity)
    if len(owners) != len(number_matches):
        return {}
    return {index: owner for index, owner in enumerate(owners)}


def _new_claim_element(
    *,
    element_id: str,
    element_type: str,
    text: str,
    span: tuple[int, int],
    product_owner: str | None,
    required_numbers: tuple[str, ...] | list[str],
    required_units: set[str] | tuple[str, ...] | list[str],
    contextual_terms: set[str] | tuple[str, ...] | list[str],
) -> dict[str, Any]:
    return {
        "element_id": element_id,
        "element_type": element_type,
        "text": text,
        "span": list(span),
        "product_owner": product_owner,
        "required_numbers": list(required_numbers),
        "required_units": sorted(required_units),
        "contextual_terms": sorted(contextual_terms),
        "supporting_citation_ids": [],
        "supporting_source_ids": [],
        "status": UNSUPPORTED,
        "_supporting_result_ids": set(),
    }


def _context_only_elements(
    claim: str,
    identities: set[str],
    identity_occurrences: list[tuple[str, int, int]],
) -> list[dict[str, Any]]:
    clauses = []
    start = 0
    for boundary in _CLAIM_CLAUSE_BOUNDARY.finditer(claim):
        clauses.append((start, boundary.start()))
        start = boundary.end()
    clauses.append((start, len(claim)))
    elements = []
    for index, (span_start, span_end) in enumerate(clauses):
        text = claim[span_start:span_end].strip()
        if not text:
            continue
        owner = _nearest_owner(span_start, span_end, identity_occurrences)
        context = _element_context_terms(
            claim,
            span_start,
            span_end,
            identities,
        )
        if not context:
            continue
        elements.append(
            _new_claim_element(
                element_id=f"element:{index + 1}",
                element_type="factual_context",
                text=text,
                span=(span_start, span_end),
                product_owner=owner,
                required_numbers=(),
                required_units=(),
                contextual_terms=context,
            )
        )
    return elements


def _derived_number_dependencies(
    matches: list[re.Match[str]],
    relation_terms: list[str],
) -> dict[int, tuple[int, int]]:
    if not set(relation_terms) & _DIFFERENCE_TERMS:
        return {}
    values = [_decimal_value(match.group(0)) for match in matches]
    derived: dict[int, tuple[int, int]] = {}
    for index in range(2, len(values)):
        candidate = values[index]
        if candidate is None:
            continue
        for left in range(index - 1):
            for right in range(left + 1, index):
                if values[left] is None or values[right] is None:
                    continue
                if candidate == abs(values[left] - values[right]):
                    derived[index] = (left, right)
                    break
            if index in derived:
                break
    return derived


def _claim_element_span(claim: str, position: int) -> tuple[int, int]:
    start = 0
    end = len(claim)
    for boundary in _CLAIM_CLAUSE_BOUNDARY.finditer(claim):
        if boundary.end() <= position:
            start = boundary.end()
        elif boundary.start() >= position:
            end = boundary.start()
            break
    return start, end


def _element_context_terms(
    claim: str,
    span_start: int,
    span_end: int,
    identities: set[str],
) -> set[str]:
    local = claim[span_start:span_end]
    colon = claim.find(":")
    anchor = claim[:colon] if 0 <= colon < span_start else ""
    tokens = _support_tokens(f"{anchor} {local}")
    tokens -= _grounding_numbers(f"{anchor} {local}")
    tokens -= _grounding_units(f"{anchor} {local}")
    tokens -= _RELATION_TERMS
    for identity in identities:
        tokens -= _support_tokens(identity)
    return tokens


def _immediate_units(claim: str, number_end: int) -> set[str]:
    tail = claim[number_end : number_end + 24]
    match = re.match(
        r"[\s.-]*(squareinch|inch|foot|watt|volt|btu)\b",
        tail,
    )
    return {match.group(1)} if match else set()


def _nearest_owner(
    span_start: int,
    span_end: int,
    occurrences: list[tuple[str, int, int]],
) -> str | None:
    if not occurrences:
        return None
    center = (span_start + span_end) / 2
    owner, _, _ = min(
        occurrences,
        key=lambda item: abs(center - ((item[1] + item[2]) / 2)),
    )
    return owner


def _comparison_direction(terms: set[str]) -> str | None:
    if terms & {"fewer", "less", "lower", "shorter", "smaller"}:
        return "less"
    if terms & {"greater", "higher", "larger", "longer", "more"}:
        return "greater"
    return None


def _comparison_subject(
    claim: str,
    owners: list[str],
    terms: set[str],
) -> str | None:
    normalized = _normalize_grounding_text(claim)
    positions = [
        match.start()
        for term in terms
        for match in re.finditer(rf"\b{re.escape(term)}\b", normalized)
    ]
    if not positions:
        return None
    relation_position = min(positions)
    preceding = [
        (owner, normalized.rfind(owner, 0, relation_position))
        for owner in owners
    ]
    preceding = [(owner, position) for owner, position in preceding if position >= 0]
    if not preceding:
        return None
    return max(preceding, key=lambda item: item[1])[0]


def _decimal_value(value: str) -> Decimal | None:
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def _all_product_identities(
    sources: list[Mapping[str, Any]],
    identity_by_ref: Mapping[str, str],
) -> set[str]:
    return {
        identity
        for source in sources
        for identity in _source_owner_identities(source, identity_by_ref)
    }


def _product_identity_by_ref(
    sources: list[Mapping[str, Any]],
) -> dict[str, str]:
    return {
        str(source["product_ref_id"]): _normalize_grounding_text(
            str(source["product_display_identity"])
        )
        for source in sources
        if source.get("product_ref_id")
        and source.get("product_display_identity")
    }


def _source_owner_identities(
    source: Mapping[str, Any],
    identity_by_ref: Mapping[str, str],
) -> set[str]:
    values: list[Any] = [source.get("product_display_identity")]
    applicable = source.get("applicable_product_display_identities")
    if isinstance(applicable, (list, tuple, set)):
        values.extend(applicable)
    identities = {
        _normalize_grounding_text(str(value))
        for value in values
        if value
    }
    applicable_refs = source.get("applicable_product_ref_ids")
    if isinstance(applicable_refs, (list, tuple, set)):
        identities.update(
            identity_by_ref[str(product_ref)]
            for product_ref in applicable_refs
            if str(product_ref) in identity_by_ref
        )
    return identities


def _support_tokens(text: str) -> set[str]:
    tokens = {
        token.casefold().rstrip(".,;:")
        for token in _SUPPORT_TOKEN.findall(_normalize_grounding_text(text))
    }
    return {
        token
        for token in tokens
        if token
        and (len(token) > 2 or token.isdigit())
        and token not in _STOPWORDS
    }


def _claims_by_citation(
    answer: str,
    pairs: list[tuple[ParsedCitation, Mapping[str, Any]]],
) -> dict[int, str]:
    return {
        citation_id: binding.text
        for citation_id, binding in _claim_bindings_by_citation(
            answer,
            pairs,
        ).items()
    }


def _claim_bindings_by_citation(
    answer: str,
    pairs: list[tuple[ParsedCitation, Mapping[str, Any]]],
) -> dict[int, _ClaimBinding]:
    citations: list[ParsedCitation] = []
    seen: set[int] = set()
    for citation, _ in pairs:
        identity = id(citation)
        if identity not in seen:
            citations.append(citation)
            seen.add(identity)
    matches = list(_CITATION.finditer(answer or ""))
    claims: dict[int, _ClaimBinding] = {}
    previous_end = 0
    previous_claim = ""
    group_id = 0
    for citation, match in zip(citations, matches):
        segment = (answer or "")[previous_end : match.start()]
        cleaned = _LEADING_CLAIM_CONNECTOR.sub("", segment).strip()
        if cleaned:
            parts = _CLAIM_SENTENCE_BOUNDARY.split(cleaned)
            claim = parts[-1].strip()[-400:]
            if claim:
                previous_claim = claim
                group_id += 1
        claims[id(citation)] = _ClaimBinding(previous_claim, group_id)
        previous_end = match.end()
    return claims


def _binding_status(
    *,
    status: str,
    grounding_status: str,
    unmatched: list[str],
) -> str:
    if status in {PAGE_MISMATCH, SOURCE_TYPE_MISMATCH, MALFORMED_CITATION}:
        return BINDING_INVALID
    if unmatched or status == UNKNOWN_SOURCE:
        return BINDING_MISSING
    if grounding_status == SUPPORTED:
        return SUPPORTED
    if grounding_status == VALIDATOR_UNCERTAIN:
        return VALIDATOR_UNCERTAIN
    return UNSUPPORTED


def _build_claim_source_bindings(
    answer: str,
    citations: tuple[ParsedCitation, ...],
    pairs: list[tuple[ParsedCitation, Mapping[str, Any]]],
    support_results: tuple[dict[str, Any], ...],
    *,
    unresolved_status: str,
) -> tuple[dict[str, Any], ...]:
    claim_bindings = _claim_bindings_by_citation(answer, pairs)
    results: list[dict[str, Any]] = []
    matched_citations: set[int] = set()
    for (citation, source), support in zip(pairs, support_results):
        matched_citations.add(id(citation))
        claim = claim_bindings.get(
            id(citation), _ClaimBinding("", 0)
        ).text
        evidence_text = str(
            source.get("evidence_text")
            or source.get("text")
            or source.get("text_preview")
            or ""
        )
        structural = support.get("structural_identity")
        structural_match = _supporting_structural_evidence(claim, source)
        if structural_match is not None:
            evidence_text = str(structural_match.get("evidence_text") or "")
        claim_sha = hashlib.sha256(claim.encode("utf-8")).hexdigest()
        evidence_sha = hashlib.sha256(
            evidence_text.encode("utf-8")
        ).hexdigest()
        citation_id = citation.citation_id or "citation:unknown"
        identity = {
            "citation_id": citation_id,
            "claim_sha256": claim_sha,
            "source_id": source.get("source_id"),
            "evidence_id": source.get("evidence_id"),
            "document_id": source.get("document_id"),
            "page": citation.page,
            "table_id": (
                structural.get("table_id")
                if isinstance(structural, Mapping)
                else None
            ),
            "row_id": (
                structural.get("row_id")
                if isinstance(structural, Mapping)
                else None
            ),
        }
        binding_id = "binding:" + hashlib.sha256(
            json.dumps(
                identity,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        ).hexdigest()
        support_status = str(
            support.get("status") or VALIDATOR_UNCERTAIN
        )
        if support_status == UNVERIFIABLE:
            support_status = VALIDATOR_UNCERTAIN
        results.append(
            {
                "schema_version": CITATION_BINDING_SCHEMA_VERSION,
                "binding_id": binding_id,
                "status": support_status,
                "citation_identity": {
                    "citation_id": citation_id,
                    "raw": citation.raw,
                    "source_type": citation.source_type,
                    "source_label": citation.source_label,
                    "page": citation.page,
                    "product_id": citation.product_id,
                    "start": citation.start,
                    "end": citation.end,
                },
                "claim_identity": {
                    "claim_id": f"claim:{claim_sha}",
                    "text": claim,
                    "text_sha256": claim_sha,
                },
                "source_identity": {
                    "source_id": source.get("source_id"),
                    "evidence_id": source.get("evidence_id"),
                    "document_id": source.get("document_id"),
                    "chunk_id": source.get("chunk_id"),
                    "filename": source.get("filename"),
                    "relative_path": source.get("relative_path"),
                    "page": citation.page,
                    "product_id": source.get("product_id"),
                    "structural_identity": structural,
                },
                "evidence_identity": {
                    "text_sha256": evidence_sha,
                    "text_excerpt": evidence_text[:1000],
                },
                "decision_rule": support.get("decision_rule"),
            }
        )
    for citation in citations:
        if id(citation) in matched_citations:
            continue
        results.append(
            {
                "schema_version": CITATION_BINDING_SCHEMA_VERSION,
                "binding_id": None,
                "status": unresolved_status,
                "citation_identity": citation.as_dict(),
                "claim_identity": None,
                "source_identity": None,
                "evidence_identity": None,
                "decision_rule": (
                    "RENDERED_CITATION_HAS_NO_SOURCE_BINDING"
                ),
            }
        )
    return tuple(results)


def _structural_record_key(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("document_id"),
        record.get("page"),
        record.get("table_id"),
        record.get("row_id"),
    )


def _supporting_structural_evidence(
    claim: str,
    source: Mapping[str, Any],
) -> dict[str, Any] | None:
    claim_numbers = _grounding_numbers(claim)
    claim_units = _grounding_units(claim)
    claim_tokens = _support_tokens(claim) - claim_numbers - claim_units
    candidates: list[tuple[int, dict[str, Any]]] = []
    for raw in source.get("structural_evidence") or []:
        record = dict(raw)
        if str(
            record.get("structure_status") or "structured"
        ) != "structured":
            continue
        evidence_text = str(
            record.get("evidence_text")
            or record.get("row_text")
            or record.get("text")
            or ""
        )
        if not evidence_text:
            cells = record.get("cells") or []
            evidence_text = " | ".join(
                str(cell.get("text") or "")
                for cell in cells
                if isinstance(cell, Mapping)
            )
        evidence_numbers = _grounding_numbers(evidence_text)
        evidence_units = _grounding_units(evidence_text)
        evidence_tokens = _support_tokens(evidence_text)
        overlap = claim_tokens & evidence_tokens
        if (
            claim_numbers <= evidence_numbers
            and claim_units <= evidence_units
            and (overlap or bool(claim_units & evidence_units))
        ):
            record["evidence_text"] = evidence_text
            candidates.append((len(overlap), record))
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            -item[0],
            str(item[1].get("table_id") or ""),
            str(item[1].get("row_id") or ""),
        )
    )
    return candidates[0][1]


def _public_structural_identity(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        key: record.get(key)
        for key in (
            "document_id",
            "relative_path",
            "page",
            "table_id",
            "row_id",
            "row_index",
            "cell_ids",
            "evidence_text_sha256",
        )
        if record.get(key) not in (None, "", [], ())
    }


def _normalize_grounding_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(text or "")).casefold()
    normalized = re.sub(r"(?<=\d),(?=\d)", "", normalized)
    for pattern, replacement in _GROUNDING_UNIT_PATTERNS:
        normalized = pattern.sub(replacement, normalized)
    normalized = re.sub(r"(?<=\d)-(?=(?:squareinch|inch|foot|watt|volt|btu)\b)", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _grounding_numbers(text: str) -> set[str]:
    return set(re.findall(r"(?<![a-z0-9])\d+(?:\.\d+)?(?![a-z0-9])", _normalize_grounding_text(text)))


def _grounding_units(text: str) -> set[str]:
    return _support_tokens(text) & _GROUNDING_UNITS


def _pdf_identity_matches(label: str, source: Mapping[str, Any]) -> bool:
    expected = _normalized_path(label)
    expected_name = PurePosixPath(expected).name
    actual_values = {
        _normalized_path(str(value))
        for value in (
            source.get("relative_path"),
            source.get("filename"),
            source.get("document_id"),
            source.get("source_id"),
        )
        if value
    }
    return expected in actual_values or any(
        PurePosixPath(value).name == expected_name for value in actual_values
    )


def _page_matches(page: int | None, source: Mapping[str, Any]) -> bool:
    if page is None:
        return False
    start = source.get("page_start")
    end = source.get("page_end")
    if start is None and source.get("page") is not None:
        start = end = source.get("page")
    if start is None:
        return False
    if end is None:
        end = start
    return int(start) <= page <= int(end)


def _matches_other_source_type(
    citation: ParsedCitation,
    sources: list[dict[str, Any]],
) -> bool:
    if citation.source_type == "database":
        return any(
            str(source.get("product_id")) == citation.product_id
            for source in sources
            if source.get("source_type") != "database"
        )
    return any(
        _pdf_identity_matches(citation.source_label, source)
        for source in sources
        if source.get("source_type") != "pdf"
    )


def _normalized_path(value: str) -> str:
    return value.strip().strip("\"'").replace("\\", "/").casefold()
