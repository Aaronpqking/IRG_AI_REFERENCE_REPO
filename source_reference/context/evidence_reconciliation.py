from __future__ import annotations

from collections import defaultdict
import re
from typing import Any, Iterable, Mapping

from src.evidence_models import NormalizedFact, ReconciledFact
from src.product_applicability import ProductApplicabilityContext
from src.query_identity import normalize_identifier, parse_query_identity
from src.retrieval import RankedChunk
from src.retrieval_policy import infer_document_type


_NUMBER = r"\d[\d,]*(?:\.\d+)?"
_RANGE = re.compile(
    rf"(?P<minimum>{_NUMBER})\s*(?:[-\u2013\u2014]|\bto\b)\s*"
    rf"(?P<maximum>{_NUMBER})",
    re.I,
)
_SCALAR = re.compile(_NUMBER)
_ATTRIBUTE_STOPWORDS = {"a", "an", "the", "listed", "range", "value", "values"}
_ATTRIBUTE_QUALIFIERS = {"maximum", "minimum", "nominal", "rated", "total"}


def normalize_evidence_fact(
    attribute_name: str,
    value: Any,
    *,
    source_type: str,
    source_identity: str,
    product_model: str | None = None,
    manufacturer: str | None = None,
    configuration: str | None = None,
    fuel: str | None = None,
    year_version: str | None = None,
    applicability: str = "unproven",
    document_type: str | None = None,
    specificity: str = "summary",
    citation: str | None = None,
    limitations: Iterable[str] = (),
) -> NormalizedFact:
    raw = re.sub(r"\s+", " ", str(value or "")).strip()
    value_type, minimum, maximum, list_values = _value_shape(raw)
    return NormalizedFact(
        attribute_name=re.sub(r"\s+", " ", str(attribute_name or "")).strip(),
        attribute_key=_attribute_key(attribute_name),
        raw_value=raw,
        value_type=value_type,
        unit=_unit(raw, attribute_name),
        minimum=minimum,
        maximum=maximum,
        list_values=list_values,
        source_type=str(source_type),
        source_identity=str(source_identity),
        product_model=_clean(product_model),
        manufacturer=_clean(manufacturer),
        configuration=_clean(configuration),
        fuel=_clean(fuel),
        year_version=_clean(year_version),
        applicability=str(applicability or "unproven"),
        document_type=_clean(document_type),
        specificity=str(specificity or "summary"),
        citation=_clean(citation),
        limitations=tuple(dict.fromkeys(str(item) for item in limitations if item)),
    )


def reconcile_evidence_facts(
    facts: Iterable[NormalizedFact],
) -> tuple[ReconciledFact, ...]:
    grouped: dict[str, list[NormalizedFact]] = defaultdict(list)
    for fact in facts:
        if fact.attribute_key:
            grouped[fact.attribute_key].append(fact)
    return tuple(
        _reconcile_group(key, tuple(grouped[key]))
        for key in sorted(grouped)
        if len({fact.source_type for fact in grouped[key]}) > 1
    )


def build_context_reconciliation(
    question: str,
    *,
    product_context: ProductApplicabilityContext | None,
    selected_pdf: tuple[RankedChunk, ...],
    response_packet: Mapping[str, Any] | None,
) -> dict[str, Any]:
    facts = [
        *_database_facts(question, product_context, response_packet),
        *_pdf_facts(question, selected_pdf),
    ]
    reconciled = reconcile_evidence_facts(facts)
    return {
        "normalized_facts": [fact.as_dict() for fact in facts],
        "reconciled_facts": [item.as_dict() for item in reconciled],
        "model_notes": [
            note
            for item in reconciled
            for note in item.notes
        ],
    }


def _reconcile_group(
    attribute_key: str,
    facts: tuple[NormalizedFact, ...],
) -> ReconciledFact:
    ordered = tuple(sorted(facts, key=_fact_order))
    db = next((fact for fact in ordered if fact.source_type == "database"), None)
    pdf = next((fact for fact in ordered if fact.source_type == "pdf"), None)
    if db is None or pdf is None:
        return ReconciledFact(attribute_key, "SINGLE_SOURCE", None, ordered, ())

    different_scope = _different_scope(db, pdf)
    if different_scope:
        return ReconciledFact(
            attribute_key,
            "DIFFERENT_APPLICABILITY",
            None,
            ordered,
            (
                "Preserve both values and label their differing "
                f"{', '.join(different_scope)} scope; do not present them as a conflict.",
            ),
        )

    if _numeric_compatible(db, pdf):
        if _same_numeric_value(db, pdf):
            return ReconciledFact(
                attribute_key,
                "EXACT_AGREEMENT",
                _more_specific(db, pdf).raw_value,
                ordered,
                ("The database and PDF values agree; retain both provenances.",),
            )
        container, scalar = _containing_range(db, pdf)
        if container is not None and scalar is not None:
            return ReconciledFact(
                attribute_key,
                "RANGE_PRESERVED_SCALAR_CONTAINED",
                container.raw_value,
                ordered,
                (
                    f"Preserve the {container.source_type.upper()} range "
                    f"{container.raw_value}; the {scalar.source_type.upper()} scalar "
                    f"{scalar.raw_value} is contained within it and is incomplete "
                    "summary data unless a separate narrower meaning is established.",
                    "Retain both provenances and do not collapse the range to the scalar.",
                ),
            )

    if _specificity_score(db) != _specificity_score(pdf):
        preferred = _more_specific(db, pdf)
        return ReconciledFact(
            attribute_key,
            "SPECIFIC_EVIDENCE_PREFERRED",
            preferred.raw_value,
            ordered,
            (
                f"Use the more specifically scoped value {preferred.raw_value} from "
                f"{preferred.source_type.upper()} evidence; retain the other value as "
                "separately labeled context and note any missing applicability scope.",
            ),
        )

    if _same_scope(db, pdf) and _materially_different(db, pdf):
        return ReconciledFact(
            attribute_key,
            "MATERIAL_CONFLICT",
            None,
            ordered,
            (
                "The supplied sources materially disagree at the same known scope. "
                "Expose the conflict, cite both sources, and qualify the answer.",
            ),
            requires_qualification=True,
        )

    preferred = _more_specific(db, pdf)
    return ReconciledFact(
        attribute_key,
        "SPECIFIC_EVIDENCE_PREFERRED",
        preferred.raw_value,
        ordered,
        (
            f"Use the more specifically scoped value {preferred.raw_value} from "
            f"{preferred.source_type.upper()} evidence; retain the other value as "
            "separately labeled context.",
        ),
    )


def _database_facts(
    question: str,
    context: ProductApplicabilityContext | None,
    packet: Mapping[str, Any] | None,
) -> list[NormalizedFact]:
    facts: list[NormalizedFact] = []
    if context is not None:
        for name, value in context.attributes:
            if _attribute_relevant(question, name):
                facts.append(
                    normalize_evidence_fact(
                        name,
                        value,
                        source_type="database",
                        source_identity=f"product:{context.read_model_product_id}",
                        product_model=context.mpn or context.model,
                        manufacturer=context.manufacturer or context.brand,
                        configuration=context.variant,
                        fuel=context.fuel_type,
                        year_version=(
                            str(context.model_year) if context.model_year else None
                        ),
                        applicability="resolved_product",
                        specificity="model_specific",
                        citation=(
                            "[source: Flamy Product Read Model, product ID "
                            f"{context.read_model_product_id}]"
                        ),
                    )
                )
        return facts

    for candidate in (packet or {}).get("candidate_products") or ():
        if not isinstance(candidate, Mapping):
            continue
        structured = candidate.get("structured_product_context") or {}
        raw_attributes = (
            structured.get("attributes")
            if isinstance(structured, Mapping)
            else None
        )
        for name, value in _parse_catalog_attributes(raw_attributes):
            if not _attribute_relevant(question, name):
                continue
            product_id = candidate.get("product_id")
            facts.append(
                normalize_evidence_fact(
                    name,
                    value,
                    source_type="database",
                    source_identity=f"product:{product_id}",
                    product_model=str(
                        candidate.get("mpn") or candidate.get("model") or ""
                    ),
                    manufacturer=str(candidate.get("brand") or ""),
                    applicability="candidate_only",
                    specificity="summary",
                    citation=(
                        "[source: Flamy Product Read Model, product ID "
                        f"{product_id}]"
                    ),
                    limitations=("candidate identity is not uniquely resolved",),
                )
            )
    return facts


def _pdf_facts(
    question: str,
    selected_pdf: tuple[RankedChunk, ...],
) -> list[NormalizedFact]:
    facts: list[NormalizedFact] = []
    query_ids = {
        item.normalized
        for item in parse_query_identity(question).identifiers
        if item.confidence == "high"
    }
    for ranked in selected_pdf:
        chunk = ranked.chunk
        body_ids = {
            item.normalized
            for line in (chunk.text or "").splitlines()
            if re.search(
                r"\b(?:model|models|mpn|sku|part(?:\s+number)?|p/n)\b",
                line,
                re.I,
            )
            for item in parse_query_identity(line).identifiers
            if item.confidence == "high"
        }
        exact_identity = sorted(query_ids & body_ids)
        for line in (chunk.text or "").splitlines():
            match = re.match(
                rf"\s*(?P<label>[^0-9]{{2,80}}?)\s+(?P<value>{_NUMBER}(?:\s*(?:[-\u2013\u2014]|\bto\b)\s*{_NUMBER})?[^\n]*)$",
                line,
                re.I,
            )
            if not match:
                continue
            name = match.group("label").strip(" :-")
            value = match.group("value").strip()
            if not _attribute_relevant(question, name):
                continue
            source = chunk.relative_path or chunk.filename or chunk.document_id or "unknown"
            facts.append(
                normalize_evidence_fact(
                    name,
                    value,
                    source_type="pdf",
                    source_identity=f"{source}:pages:{chunk.page_start}-{chunk.page_end}",
                    product_model=(
                        next(
                            (
                                item.raw
                                for item in parse_query_identity(question).identifiers
                                if item.normalized in exact_identity
                            ),
                            None,
                        )
                    ),
                    manufacturer=chunk.manufacturer or chunk.brand,
                    year_version=str(chunk.year or "") or None,
                    applicability=(
                        "exact_document_body_identifier"
                        if exact_identity
                        else "retrieved_document"
                    ),
                    document_type=infer_document_type(chunk),
                    specificity=(
                        "model_specific_technical"
                        if exact_identity
                        else "technical_document"
                    ),
                    citation=f"[source: {source}, page {chunk.page_start}]",
                )
            )
    return facts


def _parse_catalog_attributes(value: Any) -> tuple[tuple[str, str], ...]:
    text = str(value or "")
    return tuple(
        (match.group("name").strip(), match.group("value").strip())
        for match in re.finditer(
            r"\[\s*(?P<name>[^\[\]]+?)\s+-\s+(?P<value>[^\[\]]+?)\s*\]",
            text,
        )
    )


def _attribute_key(value: Any) -> str:
    tokens = []
    for token in re.findall(r"[a-z0-9]+", str(value or "").casefold()):
        if token in _ATTRIBUTE_STOPWORDS or token in _ATTRIBUTE_QUALIFIERS:
            continue
        if len(token) > 3 and token.endswith("s") and token != "series":
            token = token[:-1]
        tokens.append(token)
    return " ".join(tokens)


def _attribute_relevant(question: str, attribute_name: str) -> bool:
    attribute = set(_attribute_key(attribute_name).split())
    query = set(_attribute_key(question).split())
    return bool(attribute and attribute <= query)


def _value_shape(
    raw: str,
) -> tuple[str, float | None, float | None, tuple[str, ...]]:
    match = _RANGE.search(raw)
    if match:
        return (
            "range",
            _number(match.group("minimum")),
            _number(match.group("maximum")),
            (),
        )
    numbers = _SCALAR.findall(raw)
    if len(numbers) == 1:
        value = _number(numbers[0])
        return "scalar", value, value, ()
    if ";" in raw or ("," in raw and not re.fullmatch(r"[\d,\.\s]+", raw)):
        values = tuple(
            item.strip() for item in re.split(r"[;,]", raw) if item.strip()
        )
        return "list", None, None, values
    lowered = raw.casefold()
    if lowered in {"true", "false", "yes", "no"}:
        return "boolean", None, None, ()
    return "text", None, None, ()


def _unit(raw: str, attribute_name: str) -> str | None:
    without_numbers = _RANGE.sub(" ", raw)
    without_numbers = _SCALAR.sub(" ", without_numbers)
    tokens = re.findall(r"[A-Za-z]+", without_numbers)
    if not tokens:
        tokens = re.findall(r"[A-Za-z]+", str(attribute_name or ""))
    if not tokens:
        return None
    unit = tokens[-1].casefold()
    return unit[:-1] if len(unit) > 3 and unit.endswith("s") else unit


def _number(value: str) -> float:
    return float(value.replace(",", ""))


def _clean(value: Any) -> str | None:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or None


def _fact_order(fact: NormalizedFact) -> tuple[str, str, str]:
    return fact.source_type, fact.source_identity, fact.raw_value


def _scope_value(value: str | None) -> str:
    return normalize_identifier(value or "")


def _different_scope(a: NormalizedFact, b: NormalizedFact) -> tuple[str, ...]:
    fields = []
    for field in ("configuration", "fuel", "year_version"):
        left = getattr(a, field)
        right = getattr(b, field)
        if left and right and _scope_value(left) != _scope_value(right):
            fields.append(field)
    return tuple(fields)


def _same_scope(a: NormalizedFact, b: NormalizedFact) -> bool:
    if _different_scope(a, b):
        return False
    comparable = 0
    for field in ("product_model", "configuration", "fuel", "year_version"):
        left = getattr(a, field)
        right = getattr(b, field)
        if left and right:
            comparable += 1
            if _scope_value(left) != _scope_value(right):
                return False
    return comparable > 0


def _numeric_compatible(a: NormalizedFact, b: NormalizedFact) -> bool:
    return (
        a.value_type in {"scalar", "range"}
        and b.value_type in {"scalar", "range"}
        and (not a.unit or not b.unit or a.unit == b.unit)
    )


def _same_numeric_value(a: NormalizedFact, b: NormalizedFact) -> bool:
    return a.minimum == b.minimum and a.maximum == b.maximum


def _containing_range(
    a: NormalizedFact,
    b: NormalizedFact,
) -> tuple[NormalizedFact | None, NormalizedFact | None]:
    for container, scalar in ((a, b), (b, a)):
        if (
            container.value_type == "range"
            and scalar.value_type == "scalar"
            and container.minimum is not None
            and container.maximum is not None
            and scalar.minimum is not None
            and container.minimum <= scalar.minimum <= container.maximum
        ):
            return container, scalar
    return None, None


def _materially_different(a: NormalizedFact, b: NormalizedFact) -> bool:
    if _numeric_compatible(a, b):
        return (a.minimum, a.maximum) != (b.minimum, b.maximum)
    return a.raw_value.casefold() != b.raw_value.casefold()


def _more_specific(a: NormalizedFact, b: NormalizedFact) -> NormalizedFact:
    return max(
        (a, b),
        key=lambda fact: (
            _specificity_score(fact),
            fact.source_identity,
        ),
    )


def _specificity_score(fact: NormalizedFact) -> tuple[int, int]:
    weights = {
        "configuration_specific": 5,
        "model_specific_technical": 4,
        "model_specific": 3,
        "technical_document": 2,
        "summary": 1,
        "generic": 0,
    }
    return (
        weights.get(fact.specificity, 0),
        int(fact.applicability not in {"unproven", "candidate_only"}),
    )
