from __future__ import annotations

"""Generic, observational TABLE answerability detector.

The component consumes already-authorized, source-local TABLE evidence.  It
does not retrieve, rank, select, or generate an answer, and it has no write
path into the frozen TABLE runtime.
"""

from collections import Counter
import hashlib
import json
import re
from time import perf_counter
from typing import Any, Mapping, Sequence


DETECTOR_VERSION = "V1.9.20"
RESULT_SCHEMA = "docling_structural.table_answerability_result.v1"

UNIQUE = "UNIQUE"
DUPLICATE_EQUIVALENT = "DUPLICATE_EQUIVALENT"
MULTIPLE_DISTINCT = "MULTIPLE_DISTINCT"
INSUFFICIENT = "INSUFFICIENT"
RUNTIME_STATES = (UNIQUE, DUPLICATE_EQUIVALENT, MULTIPLE_DISTINCT, INSUFFICIENT)

SUPPORTED_ALTERNATIVE = "SUPPORTED_ALTERNATIVE"
POSSIBLE_ALTERNATIVE = "POSSIBLE_ALTERNATIVE"
REJECTED_STRUCTURAL_ARTIFACT = "REJECTED_STRUCTURAL_ARTIFACT"

CANONICAL_ONLY = "CANONICAL_ONLY"
SAME_TABLE_RAW = "SAME_TABLE_RAW"
SIBLING_TABLE = "SIBLING_TABLE"
SECTION_CONTEXT = "SECTION_CONTEXT"

UNKNOWN = "UNKNOWN"
UNKNOWN_CONTEXT = "UNKNOWN_CONTEXT"


def normalize_semantic_text(value: Any) -> str:
    """Lossless-enough lexical normalization; never repairs source literals."""

    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").casefold()))


def _stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _known(value: Any) -> bool:
    return value not in (None, "", UNKNOWN, UNKNOWN_CONTEXT, [], ())


def _normalized_constraints(query: str, supplied: Mapping[str, Any] | None) -> dict[str, Any]:
    supplied = dict(supplied or {})
    normalized: dict[str, Any] = {"query": query}
    for field in (
        "subject", "attribute", "configuration", "function", "fuel",
        "measurement_purpose", "installation_context", "construction_context",
        "semantic_context", "unit",
    ):
        raw = supplied.get(field)
        state = str(supplied.get(f"{field}_state") or ("EXPLICIT" if _known(raw) else "UNKNOWN"))
        normalized[field] = {
            "raw": raw if _known(raw) else None,
            "normalized": normalize_semantic_text(raw),
            "state": state,
            "provenance": supplied.get(f"{field}_provenance") or ("EXISTING_QUERY_PARSER" if _known(raw) else "UNKNOWN"),
        }
    return normalized


def _row_number(row: Mapping[str, Any]) -> int:
    value = row.get("row_number", row.get("row_index", row.get("row_id")))
    if isinstance(value, int):
        return value
    match = re.search(r"(\d+)$", str(value or ""))
    return int(match.group(1)) if match else 10**9


def _cells(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        (dict(value) for value in row.get("cells") or ()),
        key=lambda value: int(value.get("column_index", 0)),
    )


def _repeated_label(row: Sequence[Any]) -> str | None:
    values = [normalize_semantic_text(value) for value in row if normalize_semantic_text(value)]
    if len(values) < 2 or len(set(values)) != 1:
        return None
    return values[0] if not re.fullmatch(r"[\d\W]+", values[0]) else None


def _group_labels(table: Mapping[str, Any]) -> list[tuple[int, str]]:
    repeated = [
        (index, label)
        for index, raw_row in enumerate(table.get("raw_matrix") or ())
        for label in [_repeated_label(raw_row)]
        if label
    ]
    return repeated if len({label for _, label in repeated}) >= 2 else []


def _row_group(table: Mapping[str, Any], row_number: int) -> tuple[str | None, list[str]]:
    labels = [label for index, label in _group_labels(table) if index < row_number - 1]
    return (labels[-1] if labels else None), labels


def explicitly_related_sibling_table(seed: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Return a source-explicit sibling relationship; UNKNOWN is preserved."""

    if seed.get("document_id") != candidate.get("document_id"):
        return {"state": "NOT_RELATED", "basis": "DIFFERENT_AUTHORITY_DOCUMENT"}
    if seed.get("table_id") == candidate.get("table_id"):
        return {"state": "SAME_TABLE", "basis": "IDENTICAL_TABLE_OCCURRENCE"}
    seed_links = set(seed.get("related_table_ids") or ())
    candidate_links = set(candidate.get("related_table_ids") or ())
    if candidate.get("table_id") in seed_links or seed.get("table_id") in candidate_links:
        return {"state": "RELATED", "basis": "EXPLICIT_RELATED_TABLE_EDGE"}
    seed_group = normalize_semantic_text(seed.get("table_group"))
    candidate_group = normalize_semantic_text(candidate.get("table_group"))
    if seed_group and seed_group == candidate_group:
        return {"state": "RELATED", "basis": "EXPLICIT_COMMON_TABLE_GROUP"}
    seed_parent = str(seed.get("structural_parent_id") or "")
    candidate_parent = str(candidate.get("structural_parent_id") or "")
    if seed_parent and seed_parent == candidate_parent:
        return {"state": "RELATED", "basis": "EXPLICIT_COMMON_STRUCTURAL_PARENT"}
    seed_section = tuple(normalize_semantic_text(value) for value in seed.get("section_ancestry") or ())
    candidate_section = tuple(normalize_semantic_text(value) for value in candidate.get("section_ancestry") or ())
    if seed_section and seed_section == candidate_section:
        return {"state": "RELATED", "basis": "EXPLICIT_COMMON_SECTION_ANCESTRY"}
    return {"state": "UNKNOWN", "basis": "NO_EXPLICIT_SIBLING_RELATION"}


def _scope_tables(
    selected_or_retrieved_table: Sequence[str] | str | None,
    raw_table_structure: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected = (
        {str(selected_or_retrieved_table)} if isinstance(selected_or_retrieved_table, str)
        else {str(value) for value in selected_or_retrieved_table or ()}
    )
    tables = [dict(value) for value in raw_table_structure]
    seeds = [value for value in tables if str(value.get("table_id")) in selected]
    relationships: list[dict[str, Any]] = []
    included = {str(value.get("table_id")) for value in seeds}
    for candidate in tables:
        candidate_id = str(candidate.get("table_id"))
        if candidate_id in included:
            continue
        proofs = [explicitly_related_sibling_table(seed, candidate) for seed in seeds]
        accepted = next((proof for proof in proofs if proof["state"] == "RELATED"), None)
        relationships.append({"table_id": candidate_id, "proofs": proofs, "included": accepted is not None})
        if accepted is not None:
            included.add(candidate_id)
    return [value for value in tables if str(value.get("table_id")) in included], relationships


def _explicit_alternative_marker(value: Any) -> bool:
    normalized = normalize_semantic_text(value)
    return normalized in {"or", "and or", "alternative", "alternate", "alternatively"}


def _header_signature(cells: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(normalize_semantic_text(value.get("header_path")) for value in cells)


def _table_purpose(table: Mapping[str, Any]) -> str | None:
    for field in ("caption", "explicit_table_purpose", "adjacent_table_label"):
        if _known(table.get(field)):
            return str(table[field])
    return None


def _raw_occurrences(
    constraints: Mapping[str, Any], tables: Sequence[Mapping[str, Any]], counters: dict[str, int],
) -> list[dict[str, Any]]:
    subject = constraints["subject"]["normalized"]
    attribute = constraints["attribute"]["normalized"]
    output: list[dict[str, Any]] = []
    for table in tables:
        rows = sorted((dict(value) for value in table.get("rows") or ()), key=_row_number)
        inherited_subject: str | None = None
        previous_cells: list[dict[str, Any]] = []
        previous_row_ref: str | None = None
        for row in rows:
            counters["raw_rows_inspected"] += 1
            cells = _cells(row)
            counters["cells_inspected"] += len(cells)
            if not cells:
                continue
            first = str(cells[0].get("value") or "").strip()
            alternative = _explicit_alternative_marker(first) or not normalize_semantic_text(first)
            signature_preserved = bool(previous_cells) and _header_signature(previous_cells) == _header_signature(cells)
            inheritance_defensible = bool(alternative and inherited_subject and signature_preserved)
            if not alternative:
                inherited_subject = first
            row_subject = inherited_subject if inheritance_defensible else (None if alternative else first)
            inheritance = {
                "state": "DEFENSIBLE" if inheritance_defensible else ("UNKNOWN" if alternative else "NOT_REQUIRED"),
                "marker": first if alternative else None,
                "source_row_reference": row.get("row_id"),
                "parent_row_reference": previous_row_ref if inheritance_defensible else None,
                "basis": "EXPLICIT_ALTERNATIVE_MARKER_AND_PRESERVED_HEADER_BINDING" if inheritance_defensible else None,
                "confidence": "HIGH" if inheritance_defensible else ("NONE" if alternative else "HIGH"),
            }
            if row_subject and normalize_semantic_text(row_subject) == subject:
                group, trace = _row_group(table, _row_number(row))
                descriptive = next(
                    (str(value.get("value")) for value in cells[1:] if "description" in normalize_semantic_text(value.get("header_path"))),
                    None,
                )
                for cell in cells[1:]:
                    if normalize_semantic_text(cell.get("header_path")) != attribute:
                        continue
                    if normalize_semantic_text(cell.get("value")) == subject:
                        continue
                    context_label = group
                    if descriptive and (
                        inheritance_defensible or attribute == "description" or re.search(r"\([^)]{2,}\)", descriptive)
                    ):
                        context_label = descriptive
                    output.append({
                        "origin": "RAW_TABLE_STRUCTURE",
                        "candidate_id": row.get("candidate_id"),
                        "row_id": row.get("row_id"),
                        "cell_id": cell.get("cell_id", cell.get("cell_node_id")),
                        "table_id": table.get("table_id"),
                        "document_id": table.get("document_id"),
                        "source_refs": list(row.get("source_refs") or table.get("source_refs") or ()),
                        "page": row.get("page", table.get("page")),
                        "row_number": _row_number(row),
                        "column_index": cell.get("column_index"),
                        "subject": row_subject,
                        "attribute": cell.get("header_path"),
                        "configuration": None,
                        "raw_value": cell.get("value"),
                        "unit": None,
                        "header_path": [part.strip() for part in str(cell.get("header_path") or "").split(">")],
                        "row_path": [row_subject],
                        "group_context": group,
                        "group_trace": trace,
                        "table_purpose": _table_purpose(table),
                        "context_label": context_label,
                        "semantic_orientation": row.get("semantic_orientation") or "ROW_SUBJECT",
                        "inheritance": inheritance,
                        "section_ancestry": list(table.get("section_ancestry") or ()),
                        "source_scope": SAME_TABLE_RAW,
                    })
            previous_cells = cells
            previous_row_ref = str(row.get("row_id") or "")
    return output


def _canonical_occurrences(
    constraints: Mapping[str, Any], canonical_facts: Sequence[Mapping[str, Any]], scoped_ids: set[str],
) -> list[dict[str, Any]]:
    subject = constraints["subject"]["normalized"]
    attribute = constraints["attribute"]["normalized"]
    output = []
    for source in canonical_facts:
        if str(source.get("table_id")) not in scoped_ids:
            continue
        if normalize_semantic_text(source.get("subject")) != subject:
            continue
        if normalize_semantic_text(source.get("attribute")) != attribute:
            continue
        item = dict(source)
        item.setdefault("origin", "CANONICAL_FACT")
        item.setdefault("raw_value", item.get("value"))
        item.setdefault("inheritance", {"state": "NOT_REQUIRED"})
        item.setdefault("source_scope", CANONICAL_ONLY)
        output.append(item)
    return output


def _merge_occurrences(canonical: Sequence[Mapping[str, Any]], raw: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    raw_by_cell = {str(value.get("cell_id")): value for value in raw if value.get("cell_id")}
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in list(canonical) + list(raw):
        item = dict(source)
        cell_id = str(item.get("cell_id") or "")
        matching = raw_by_cell.get(cell_id)
        if matching:
            for field in (
                "row_id", "row_number", "column_index", "group_context", "group_trace",
                "table_purpose", "context_label", "semantic_orientation", "inheritance",
                "section_ancestry", "source_refs", "page",
            ):
                if _known(matching.get(field)) or field == "inheritance":
                    item[field] = matching.get(field)
        identity = cell_id or _stable_hash({
            "table": item.get("table_id"), "row": item.get("row_id"),
            "subject": item.get("subject"), "attribute": item.get("attribute"),
            "value": item.get("raw_value", item.get("value")),
        })
        if identity in seen:
            continue
        seen.add(identity)
        item["occurrence_identity"] = identity
        output.append(item)
    return output


def _group_vocabulary(tables: Sequence[Mapping[str, Any]]) -> dict[str, set[str]]:
    return {
        str(table.get("table_id")): {label for _, label in _group_labels(table)}
        for table in tables
    }


def _cell_index(tables: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    output = {}
    for table in tables:
        for row in table.get("rows") or ():
            for cell in _cells(row):
                cell_id = cell.get("cell_id", cell.get("cell_node_id"))
                if cell_id:
                    output[str(cell_id)] = {"table": table, "row": row, "cell": cell}
    return output


def _query_compatible(occurrence: Mapping[str, Any], constraints: Mapping[str, Any]) -> tuple[bool, str]:
    requested_configuration = constraints["configuration"]["normalized"]
    occurrence_configuration = normalize_semantic_text(occurrence.get("configuration"))
    if requested_configuration and occurrence_configuration and requested_configuration != occurrence_configuration:
        return False, "EXPLICIT_CONFIGURATION_CONFLICT"
    requested_context = constraints["semantic_context"]["normalized"]
    if requested_context:
        labels = {
            normalize_semantic_text(occurrence.get(field))
            for field in ("group_context", "table_purpose", "context_label")
            if _known(occurrence.get(field))
        }
        if labels and not any(requested_context == label or requested_context in label or label in requested_context for label in labels):
            return False, "EXPLICIT_SEMANTIC_CONTEXT_CONFLICT"
    return True, "QUERY_COMPATIBLE"


def _structural_validity(
    occurrence: Mapping[str, Any], constraints: Mapping[str, Any], scoped_ids: set[str],
    groups: Mapping[str, set[str]], cells: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    cell_id = str(occurrence.get("cell_id") or "")
    binding = cells.get(cell_id)
    raw_value = occurrence.get("raw_value", occurrence.get("value"))
    value_belongs = bool(binding and str(binding["cell"].get("value")) == str(raw_value))
    header_coherent = normalize_semantic_text(occurrence.get("attribute")) == constraints["attribute"]["normalized"]
    row_column_coherent = bool(binding and binding["cell"].get("column_index") is not None)
    orientation_coherent = bool(occurrence.get("subject") and occurrence.get("attribute"))
    table_scope_coherent = str(occurrence.get("table_id")) in scoped_ids
    inheritance = dict(occurrence.get("inheritance") or {"state": "NOT_REQUIRED"})
    inherited_context_defensible = inheritance.get("state") in {"NOT_REQUIRED", "DEFENSIBLE"}

    table_id = str(occurrence.get("table_id") or "")
    vocabulary = set(groups.get(table_id) or ())
    requested = constraints["configuration"]["normalized"]
    group = normalize_semantic_text(occurrence.get("group_context"))
    matching = {value for value in vocabulary if requested and (value == requested or value in requested or requested in value)}
    row_group_coherent: bool | None = True
    reason = "ALL_SOURCE_BINDINGS_COHERENT"
    state = SUPPORTED_ALTERNATIVE
    if matching and group and group not in matching:
        row_group_coherent = False
        state = REJECTED_STRUCTURAL_ARTIFACT
        reason = "EXPLICIT_ROW_GROUP_CONFLICT"
    elif matching and not group:
        row_group_coherent = None
        state = POSSIBLE_ALTERNATIVE
        reason = "ROW_GROUP_BINDING_UNKNOWN"
    elif not all((value_belongs, header_coherent, row_column_coherent, orientation_coherent, table_scope_coherent)):
        state = POSSIBLE_ALTERNATIVE
        reason = "SOURCE_BINDING_INCOMPLETE"
    elif not inherited_context_defensible:
        state = POSSIBLE_ALTERNATIVE
        reason = "INHERITED_CONTEXT_NOT_DEFENSIBLE"
    return {
        "support_state": state,
        "reason": reason,
        "checks": {
            "value_belongs_to_cited_cell": value_belongs,
            "row_column_intersection_coherent": row_column_coherent,
            "header_ancestry_coherent": header_coherent,
            "row_group_ancestry_coherent": row_group_coherent,
            "semantic_orientation_coherent": orientation_coherent,
            "table_section_scope_coherent": table_scope_coherent,
            "inherited_context_defensible": inherited_context_defensible,
        },
    }


def _discriminators(occurrence: Mapping[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    if _known(occurrence.get("group_context")):
        output.append({"dimension": "SOURCE_EXPLICIT_ROW_GROUP", "value": occurrence["group_context"], "state": "KNOWN", "provenance": "EXPLICIT_ROW_HEADER"})
    elif _known(occurrence.get("table_purpose")):
        output.append({"dimension": "SOURCE_EXPLICIT_TABLE_PURPOSE", "value": occurrence["table_purpose"], "state": "KNOWN", "provenance": "EXPLICIT_CAPTION"})
    if _known(occurrence.get("context_label")) and normalize_semantic_text(occurrence.get("context_label")) != normalize_semantic_text(occurrence.get("group_context")):
        output.append({"dimension": "SOURCE_EXPLICIT_ALTERNATIVE_CONTEXT", "value": occurrence["context_label"], "state": "KNOWN", "provenance": "EXPLICIT_ADJACENT_TEXT"})
    return output


def _semantic_answer(authority: Mapping[str, Any], occurrence: Mapping[str, Any], constraints: Mapping[str, Any]) -> dict[str, Any]:
    discriminators = _discriminators(occurrence)
    raw_value = occurrence.get("raw_value", occurrence.get("value"))
    configuration = normalize_semantic_text(occurrence.get("configuration")) or constraints["configuration"]["normalized"]
    unit = normalize_semantic_text(occurrence.get("unit")) or constraints["unit"]["normalized"]
    identity = {
        "document_authority_scope": authority.get("source_document") or authority.get("document_id") or authority.get("authority_scope") or UNKNOWN,
        "subject": normalize_semantic_text(occurrence.get("subject")),
        "attribute": normalize_semantic_text(occurrence.get("attribute")),
        "configuration": configuration or "UNKNOWN_CONFIGURATION",
        "normalized_value": normalize_semantic_text(raw_value),
        "unit": unit or "UNKNOWN_UNIT",
        "semantic_discriminators": tuple((value["dimension"], normalize_semantic_text(value["value"])) for value in discriminators),
    }
    return {
        "semantic_answer_key_id": f"stak2_{_stable_hash(identity)}",
        **identity,
        "semantic_discriminators": discriminators,
        "raw_value": raw_value,
        "normalized_value": normalize_semantic_text(raw_value),
        "normalization_provenance": {
            "method": "LOSSLESS_LEXICAL_CASEFOLD_PUNCTUATION_TOKENIZATION",
            "source_literal_preserved": True,
            "correction_map_used": False,
        },
    }


def semantic_equivalent(a: Mapping[str, Any], b: Mapping[str, Any], query_constraints: Mapping[str, Any] | None = None) -> bool:
    """Semantic equivalence independent of opaque occurrence provenance."""

    fields = ("document_authority_scope", "subject", "attribute", "configuration", "normalized_value", "unit")
    if not all(a.get(field) == b.get(field) for field in fields):
        return False
    left = tuple((value["dimension"], normalize_semantic_text(value["value"])) for value in a.get("semantic_discriminators") or ())
    right = tuple((value["dimension"], normalize_semantic_text(value["value"])) for value in b.get("semantic_discriminators") or ())
    return left == right


def semantically_distinct(a: Mapping[str, Any], b: Mapping[str, Any], query_constraints: Mapping[str, Any] | None = None) -> bool:
    return not semantic_equivalent(a, b, query_constraints)


def _public_occurrence(occurrence: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": occurrence.get("candidate_id"),
        "table_id": occurrence.get("table_id"),
        "row_id": occurrence.get("row_id"),
        "cell_id": occurrence.get("cell_id"),
        "source_refs": list(occurrence.get("source_refs") or ()),
        "page": occurrence.get("page"),
        "raw_value": occurrence.get("raw_value", occurrence.get("value")),
        "origin": occurrence.get("origin"),
        "inheritance": dict(occurrence.get("inheritance") or {}),
        "structural_validity": dict(occurrence.get("structural_validity") or {}),
    }


def detect_table_answerability(
    query: str,
    authority: Mapping[str, Any],
    selected_or_retrieved_table: Sequence[str] | str | None,
    canonical_facts: Sequence[Mapping[str, Any]],
    raw_table_structure: Sequence[Mapping[str, Any]],
    section_context: Mapping[str, Any] | None = None,
    source_refs: Sequence[str] | None = None,
    *,
    query_constraints: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct an observational, source-supported semantic answer set."""

    started = perf_counter()
    constraints = _normalized_constraints(query, query_constraints)
    counters = {"raw_rows_inspected": 0, "cells_inspected": 0}
    scoped_tables, sibling_audit = _scope_tables(selected_or_retrieved_table, raw_table_structure)
    scoped_ids = {str(value.get("table_id")) for value in scoped_tables}
    seed_ids = (
        {str(selected_or_retrieved_table)} if isinstance(selected_or_retrieved_table, str)
        else {str(value) for value in selected_or_retrieved_table or ()}
    )
    counters["sibling_tables_inspected"] = len(sibling_audit)

    canonical = _canonical_occurrences(constraints, canonical_facts, scoped_ids)
    raw = _raw_occurrences(constraints, scoped_tables, counters)
    occurrences = _merge_occurrences(canonical, raw)
    groups = _group_vocabulary(scoped_tables)
    cell_index = _cell_index(scoped_tables)

    supported: list[dict[str, Any]] = []
    possible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    incompatible: list[dict[str, Any]] = []
    for source in occurrences:
        occurrence = dict(source)
        compatible, compatibility_reason = _query_compatible(occurrence, constraints)
        occurrence["query_compatibility"] = compatibility_reason
        if not compatible:
            incompatible.append(occurrence)
            continue
        validity = _structural_validity(occurrence, constraints, scoped_ids, groups, cell_index)
        occurrence["structural_validity"] = validity
        if validity["support_state"] == SUPPORTED_ALTERNATIVE:
            supported.append(occurrence)
        elif validity["support_state"] == POSSIBLE_ALTERNATIVE:
            possible.append(occurrence)
        else:
            rejected.append(occurrence)

    semantic_groups: list[dict[str, Any]] = []
    for occurrence in supported:
        answer = _semantic_answer(authority, occurrence, constraints)
        target = next((value for value in semantic_groups if semantic_equivalent(value["semantic_answer"], answer, constraints)), None)
        if target is None:
            target = {"semantic_answer": answer, "evidence_occurrences": []}
            semantic_groups.append(target)
        target["evidence_occurrences"].append(_public_occurrence(occurrence))

    if not semantic_groups:
        answerability = INSUFFICIENT
        decision_reason = "NO_SOURCE_SUPPORTED_QUERY_COMPATIBLE_ANSWER"
    elif len(semantic_groups) > 1:
        answerability = MULTIPLE_DISTINCT
        decision_reason = "MULTIPLE_SOURCE_SUPPORTED_QUERY_COMPATIBLE_SEMANTIC_ANSWERS"
    elif len(semantic_groups[0]["evidence_occurrences"]) > 1:
        answerability = DUPLICATE_EQUIVALENT
        decision_reason = "MULTIPLE_EVIDENCE_OCCURRENCES_ONE_SEMANTIC_ANSWER"
    else:
        answerability = UNIQUE
        decision_reason = "ONE_SOURCE_SUPPORTED_QUERY_COMPATIBLE_SEMANTIC_ANSWER"

    raw_answer_keys = {
        _semantic_answer(authority, value, constraints)["semantic_answer_key_id"]
        for value in supported if value.get("origin") == "RAW_TABLE_STRUCTURE"
    }
    canonical_answer_keys = {
        _semantic_answer(authority, value, constraints)["semantic_answer_key_id"]
        for value in supported if value.get("origin") == "CANONICAL_FACT"
    }
    raw_only = raw_answer_keys - canonical_answer_keys
    sibling_answer = any(str(value.get("table_id")) not in seed_ids for value in supported)
    if sibling_answer:
        source_scope_used = SIBLING_TABLE
    elif raw_only:
        source_scope_used = SAME_TABLE_RAW
    elif any(value.get("table_purpose") or value.get("section_ancestry") for value in supported) and raw_only:
        source_scope_used = SECTION_CONTEXT
    else:
        source_scope_used = CANONICAL_ONLY

    discriminator_dimensions = sorted({
        value["dimension"]
        for group in semantic_groups
        for value in group["semantic_answer"].get("semantic_discriminators") or ()
    })
    missing_discriminators = discriminator_dimensions if answerability == MULTIPLE_DISTINCT else []
    if answerability == MULTIPLE_DISTINCT and not missing_discriminators:
        missing_discriminators = [UNKNOWN_CONTEXT]
    context_complete = answerability == MULTIPLE_DISTINCT and all(
        group["semantic_answer"].get("semantic_discriminators") for group in semantic_groups
    )
    response_strategy = (
        "MULTI_EVIDENCE" if answerability == MULTIPLE_DISTINCT and context_complete
        else "CLARIFICATION" if answerability == MULTIPLE_DISTINCT
        else None
    )
    elapsed_ms = (perf_counter() - started) * 1000.0
    return {
        "schema": RESULT_SCHEMA,
        "detector_version": DETECTOR_VERSION,
        "answerability": answerability,
        "semantic_answers": semantic_groups,
        "evidence_occurrences": [value for group in semantic_groups for value in group["evidence_occurrences"]],
        "missing_discriminators": missing_discriminators,
        "source_scope_used": source_scope_used,
        "structural_validity_audit": {
            "supported_alternatives": [_public_occurrence(value) for value in supported],
            "possible_alternatives": [_public_occurrence(value) for value in possible],
            "rejected_structural_artifacts": [_public_occurrence(value) for value in rejected],
            "query_incompatible_occurrences": [_public_occurrence(value) for value in incompatible],
            "sibling_relation_audit": sibling_audit,
            "only_supported_contributes_to_cardinality": True,
        },
        "query_constraints": constraints,
        "decision_reason": decision_reason,
        "response_strategy_candidate": response_strategy,
        "source_refs": list(source_refs or ()),
        "section_context": dict(section_context or {}),
        "observational_only": True,
        "document_wide_access": False,
        "detector_metrics": {
            "latency_ms": elapsed_ms,
            **counters,
            "scoped_tables_inspected": len(scoped_tables),
            "semantic_alternatives_constructed": len(semantic_groups),
            "canonical_occurrences_considered": len(canonical),
            "raw_occurrences_discovered": len(raw),
        },
    }
