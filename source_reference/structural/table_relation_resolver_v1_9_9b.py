from __future__ import annotations

"""Frozen V1.9.9 S2 table-relation resolver for canonical runtime use.

This module is deliberately table-only.  Retrieval, authority, candidate
collapse, and non-table selection remain outside its boundary.
"""

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence

from .canonical_ir_v1_9_6 import CanonicalTableFact, CanonicalTechnicalDocumentIR
from .model import DocumentGraph
from .scoped_evidence_v1_5 import EvidenceType


RESOLVER_VERSION = "V1.9.9b"
POLICY_VERSION = "V1.9.9-S2"
QUERY_RELATION_SCHEMA = "docling_structural_v1_9_9.TableQueryRelation.v1"
CANDIDATE_RELATION_SCHEMA = "docling_structural_v1_9_9.TableCandidateRelation.v1"
PROOF_SCHEMA = "docling_structural_v1_9_9b.TableRelationResolverProof.v1"
R2_REPRESENTATION_VERSION = "V1.9.8-R2"
MODEL_IDENTITY = "cross-encoder/ms-marco-MiniLM-L6-v2"
MODEL_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
MATCH = "MATCH"
CONFLICT = "CONFLICT"
UNKNOWN = "UNKNOWN"
QUERY_FIELDS = (
    "requested_subject",
    "requested_attribute",
    "requested_configuration",
    "requested_unit",
    "table_target",
    "manufacturer",
    "year",
    "document_type",
)


def _space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _plain(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _space(value).casefold()).strip()


def _query_field(value: Any, *, status: str, provenance: str, confidence: str) -> dict[str, Any]:
    text = _space(value)
    if not text or text == UNKNOWN:
        return {"value": UNKNOWN, "status": "UNKNOWN", "provenance": provenance, "confidence_class": "NONE"}
    return {"value": text, "status": status, "provenance": provenance, "confidence_class": confidence}


def _candidate_field(
    value: Any,
    *,
    provenance: Any,
    confidence: str,
    alternatives: Sequence[str] = (),
) -> dict[str, Any]:
    text = _space(value)
    clean = list(dict.fromkeys(_space(item) for item in alternatives if _space(item)))
    if not text:
        return {
            "value": UNKNOWN,
            "status": "UNKNOWN",
            "provenance": provenance,
            "confidence_class": "NONE",
            "alternatives": clean,
        }
    return {
        "value": text,
        "status": "EXPLICIT" if confidence == "HIGH" else "DERIVED",
        "provenance": provenance,
        "confidence_class": confidence,
        "alternatives": clean,
    }


def _unit_value(value: Any) -> str:
    text = _space(value).casefold()
    if not text or text == "unknown":
        return UNKNOWN
    if text in {'"', "inch", "inches", "in", "in."}:
        return "INCH"
    if text in {"'", "foot", "feet", "ft", "ft."}:
        return "FOOT"
    if re.fullmatch(r"sq\.?\s*in\.?,?", text):
        return "SQUARE_INCH"
    aliases = {
        "btu": "BTU",
        "cfm": "CFM",
        "psi": "PSI",
        "w.c.": "WATER_COLUMN",
        "wc": "WATER_COLUMN",
        "amp": "AMP",
        "amps": "AMP",
        "hz": "HZ",
        "watt": "WATT",
        "watts": "WATT",
        "volt": "VOLT",
        "volts": "VOLT",
        "lb": "POUND",
        "lbs": "POUND",
        "kg": "KILOGRAM",
        "cm": "CENTIMETER",
        "mm": "MILLIMETER",
    }
    return aliases.get(text, re.sub(r"[^a-z0-9]+", "_", text).strip("_").upper() or UNKNOWN)


def _attribute_unit(value: Any) -> str:
    pattern = r"(?:\bsq\.?\s*in\.?\b|\bbtu\b|\bcfm\b|\bpsi\b|\bw\.?c\.?\b|\b(?:amps?|hz|watts?|volts?|lbs?|kg|cm|mm)\b)"
    values = list(dict.fromkeys(_unit_value(match.group(0)) for match in re.finditer(pattern, _space(value), re.I)))
    return values[0] if len(values) == 1 else UNKNOWN


def normalize_subject(value: Any) -> str:
    text = (
        _space(value)
        .casefold()
        .replace("â€œ", '"')
        .replace("â€", '"')
        .replace("â€²", "'")
        .replace("â€³", '"')
    )
    text = re.sub(r'(?<=\d)\s*"', " inch ", text)
    text = re.sub(r"(?<=\d)\s*'", " foot ", text)
    return " ".join(token for token in re.findall(r"[a-z0-9]+", text) if token != "series")


def normalize_attribute(value: Any) -> str:
    tokens = re.findall(r"[a-z0-9]+", _space(value).casefold())
    collapsed: list[str] = []
    for token in tokens:
        if not collapsed or token != collapsed[-1]:
            collapsed.append(token)
    return " ".join(collapsed)


def normalize_configuration(value: Any) -> str:
    text = _plain(value)
    aliases = {
        "natural": "natural gas",
        "nat gas": "natural gas",
        "natural gas": "natural gas",
        "l p gas": "propane",
        "lp gas": "propane",
        "propane": "propane",
        "masonry built": "masonry built",
        "for masonry built fireplaces": "masonry built",
        "factory built": "factory built",
        "for factory built fireplaces": "factory built",
    }
    return aliases.get(text, text)


def _normalize(field: str, value: Any) -> str:
    if not value or str(value) == UNKNOWN:
        return ""
    if field in {"requested_subject", "subject", "row_identity", "table_target"}:
        return normalize_subject(value)
    if field in {"requested_attribute", "attribute", "column_identity", "header_path"}:
        return normalize_attribute(value)
    if field in {"requested_configuration", "configuration"}:
        return normalize_configuration(value)
    if field in {"requested_unit", "unit"}:
        return _unit_value(value)
    return _plain(value)


def _field_values(field: str, candidate: Mapping[str, Any]) -> list[str]:
    if candidate["value"] == UNKNOWN:
        return []
    values = [candidate["value"], *(candidate.get("alternatives") or ())]
    return list(dict.fromkeys(value for value in (_normalize(field, item) for item in values) if value))


def compare_relation(
    query_field: Mapping[str, Any],
    candidate_field: Mapping[str, Any],
    *,
    query_name: str,
    candidate_name: str,
) -> dict[str, Any]:
    query_value = _normalize(query_name, query_field["value"])
    candidate_values = _field_values(candidate_name, candidate_field)
    if query_field["status"] == "UNKNOWN" or not query_value or not candidate_values:
        state = UNKNOWN
    elif query_value in candidate_values:
        state = MATCH
    else:
        state = CONFLICT
    return {
        "state": state,
        "query_value": query_field["value"],
        "candidate_value": candidate_field["value"],
        "query_normalized": query_value or None,
        "candidate_normalized": candidate_values,
        "query_provenance": query_field["provenance"],
        "candidate_provenance": candidate_field["provenance"],
    }


def parse_table_query_relation(query: str, manufacturers: Sequence[str]) -> dict[str, Any]:
    """Parse only literal, unambiguous query slots; UNKNOWN is conservative."""

    pattern = re.compile(
        r"^\s*In\s+the\s+(?P<prefix>.+?)\s+table\s+for\s+(?P<table_target>.+?),\s*"
        r"what\s+value\s+is\s+listed\s+for\s+(?P<request>.+?)\?\s*$",
        re.I,
    )
    match = pattern.match(query)
    unknown = lambda field: _query_field(
        UNKNOWN,
        status="UNKNOWN",
        provenance=f"NO_EXPLICIT_{field.upper()}_SYNTAX",
        confidence="NONE",
    )
    if not match:
        return {
            "schema": QUERY_RELATION_SCHEMA,
            **{field: unknown(field) for field in QUERY_FIELDS},
            "parser_provenance": {
                "parser": "CONSERVATIVE_TABLE_QUERY_RELATION_V1",
                "gold_fields_used": False,
                "case_mapping_used": False,
                "unknown_preferred": True,
            },
        }
    prefix = match.group("prefix").strip()
    year_match = re.search(r"\b(?:19|20)\d{2}\s*$", prefix)
    year = year_match.group(0).strip() if year_match else UNKNOWN
    manufacturer_text = prefix[: year_match.start()].strip() if year_match else prefix
    manufacturer_matches = [value for value in manufacturers if _plain(value) == _plain(manufacturer_text)]
    manufacturer = manufacturer_matches[0] if len(manufacturer_matches) == 1 else UNKNOWN
    request = match.group("request").strip()
    config_match = re.search(r"\s+with\s+configuration\s+(.+?)\s*$", request, re.I)
    configuration = config_match.group(1).strip() if config_match else UNKNOWN
    if config_match:
        request = request[: config_match.start()].strip()
    splits = list(re.finditer(r"\s+for\s+", request, re.I))
    if splits:
        split = splits[-1]
        attribute = request[: split.start()].strip() or UNKNOWN
        subject = request[split.end() :].strip() or UNKNOWN
    else:
        attribute, subject = request or UNKNOWN, UNKNOWN
    unit = _attribute_unit(attribute)
    document_types = {
        "owner manual": "OM",
        "owners manual": "OM",
        "installation manual": "INSTALL",
        "service manual": "SERVICE",
        "specification": "SPEC",
        "parts manual": "PARTS",
        "warranty": "WARRANTY",
        "quick start guide": "QSG",
    }
    query_plain = _plain(query)
    document_type_matches = [value for phrase, value in document_types.items() if phrase in query_plain]
    document_type = document_type_matches[0] if len(set(document_type_matches)) == 1 else UNKNOWN
    return {
        "schema": QUERY_RELATION_SCHEMA,
        "requested_subject": _query_field(subject, status="EXPLICIT", provenance="QUERY_LAST_FOR_CLAUSE", confidence="HIGH"),
        "requested_attribute": _query_field(attribute, status="EXPLICIT", provenance="QUERY_LISTED_FOR_ATTRIBUTE_CLAUSE", confidence="HIGH"),
        "requested_configuration": _query_field(
            configuration,
            status="EXPLICIT",
            provenance="QUERY_WITH_CONFIGURATION_CLAUSE" if configuration != UNKNOWN else "NO_EXPLICIT_CONFIGURATION_CLAUSE",
            confidence="HIGH",
        ),
        "requested_unit": _query_field(
            unit,
            status="EXPLICIT",
            provenance="QUERY_ATTRIBUTE_UNIT_LITERAL" if unit != UNKNOWN else "NO_UNAMBIGUOUS_ATTRIBUTE_UNIT_LITERAL",
            confidence="HIGH",
        ),
        "table_target": _query_field(match.group("table_target"), status="EXPLICIT", provenance="QUERY_TABLE_FOR_CLAUSE", confidence="HIGH"),
        "manufacturer": _query_field(
            manufacturer,
            status="EXPLICIT",
            provenance="UNIQUE_CANONICAL_MANUFACTURER_EXACT_QUERY_PREFIX" if manufacturer != UNKNOWN else "NO_UNIQUE_MANUFACTURER_EXACT_PREFIX",
            confidence="HIGH",
        ),
        "year": _query_field(year, status="EXPLICIT", provenance="QUERY_FOUR_DIGIT_YEAR_PREFIX" if year != UNKNOWN else "NO_EXPLICIT_YEAR", confidence="HIGH"),
        "document_type": _query_field(
            document_type,
            status="EXPLICIT",
            provenance="QUERY_DOCUMENT_TYPE_LITERAL" if document_type != UNKNOWN else "NO_EXPLICIT_DOCUMENT_TYPE_LITERAL",
            confidence="HIGH",
        ),
        "parser_provenance": {
            "parser": "CONSERVATIVE_TABLE_QUERY_RELATION_V1",
            "literal_query_syntax_only": True,
            "canonical_vocabulary_use": "EXACT_UNAMBIGUOUS_MANUFACTURER_ONLY",
            "generic_ir_substring_promotion": False,
            "gold_fields_used": False,
            "case_mapping_used": False,
            "unknown_preferred": True,
        },
    }


@dataclass(frozen=True)
class _RuntimeIndexes:
    facts_by_row: Mapping[str, tuple[CanonicalTableFact, ...]]
    table_by_row: Mapping[str, Any]
    document_by_id: Mapping[str, Any]


class CanonicalTableRelationResolver:
    """Apply the frozen S2 selector after canonical candidate collapse."""

    def __init__(self, *, graph: DocumentGraph, ir: CanonicalTechnicalDocumentIR) -> None:
        self.graph = graph
        self.ir = ir
        facts_by_row: dict[str, list[CanonicalTableFact]] = {}
        table_by_row: dict[str, Any] = {}
        for table in ir.structure.tables:
            for row in table.rows:
                table_by_row[row.source_node_id] = table
            for fact in table.facts:
                facts_by_row.setdefault(fact.source_row_id, []).append(fact)
                table_by_row[fact.source_row_id] = table
        self.indexes = _RuntimeIndexes(
            facts_by_row={key: tuple(value) for key, value in facts_by_row.items()},
            table_by_row=table_by_row,
            document_by_id={row.document_id: row for row in ir.documents},
        )
        self.manufacturers = sorted(
            {str(row.manufacturer.value) for row in ir.documents if row.manufacturer},
            key=lambda value: (-len(value), value),
        )

    @staticmethod
    def supports(evidence_type: EvidenceType | str) -> bool:
        value = evidence_type.value if isinstance(evidence_type, EvidenceType) else str(evidence_type)
        return value == EvidenceType.TABLE_SPEC.value

    def parse(self, query: str) -> dict[str, Any]:
        return parse_table_query_relation(query, self.manufacturers)

    def _fact_signature(self, fact: CanonicalTableFact, query: Mapping[str, Any]) -> tuple[int, int, int, int, int]:
        fact_attribute = _candidate_field(
            fact.attribute,
            provenance=fact.provenance,
            confidence="HIGH",
            alternatives=(" > ".join(fact.header_path),),
        )
        fact_subject = _candidate_field(
            fact.subject,
            provenance=fact.provenance,
            confidence="HIGH",
            alternatives=fact.row_path,
        )
        fact_configuration = _candidate_field(fact.configuration, provenance=fact.provenance, confidence="HIGH")
        attribute_state = compare_relation(
            query["requested_attribute"], fact_attribute, query_name="requested_attribute", candidate_name="attribute"
        )["state"]
        subject_state = compare_relation(
            query["requested_subject"], fact_subject, query_name="requested_subject", candidate_name="subject"
        )["state"]
        configuration_state = compare_relation(
            query["requested_configuration"], fact_configuration, query_name="requested_configuration", candidate_name="configuration"
        )["state"]
        attribute_tokens = set(normalize_attribute(query["requested_attribute"]["value"]).split())
        fact_tokens = set(normalize_attribute(f"{fact.attribute} {' '.join(fact.header_path)}").split())
        return (
            int(attribute_state == MATCH),
            int(configuration_state == MATCH),
            int(subject_state == MATCH),
            len(attribute_tokens.intersection(fact_tokens)),
            -len(fact_tokens),
        )

    def _select_fact(self, node_id: str, query: Mapping[str, Any]) -> tuple[CanonicalTableFact | None, dict[str, Any]]:
        facts = self.indexes.facts_by_row.get(node_id, ())
        if not facts:
            return None, {"status": "NO_CANONICAL_FACT", "top_signature": None, "tied_fact_ids": []}
        scored = [(fact, self._fact_signature(fact, query)) for fact in facts]
        best_signature = max(signature for _, signature in scored)
        best = [fact for fact, signature in scored if signature == best_signature]
        semantic = {
            (
                normalize_subject(fact.subject),
                normalize_attribute(fact.attribute),
                normalize_configuration(fact.configuration),
                _unit_value(fact.unit),
                _space(fact.value),
                tuple(normalize_attribute(value) for value in fact.header_path),
            )
            for fact in best
        }
        if len(semantic) > 1:
            return None, {
                "status": "AMBIGUOUS_CANONICAL_FACT",
                "top_signature": best_signature,
                "tied_fact_ids": sorted(fact.fact_id for fact in best),
            }
        selected = sorted(best, key=lambda fact: fact.fact_id)[0]
        return selected, {
            "status": "UNIQUE_QUERY_ALIGNED_FACT" if len(best) == 1 else "SEMANTICALLY_EQUIVALENT_FACTS",
            "top_signature": best_signature,
            "tied_fact_ids": sorted(fact.fact_id for fact in best),
        }

    def candidate_relation(self, node_id: str, query: Mapping[str, Any]) -> dict[str, Any]:
        node = self.graph.nodes[node_id]
        fact, selection = self._select_fact(node_id, query)
        table = self.indexes.table_by_row.get(node_id)
        row_values = tuple(_space(value) for value in node.attributes.get("row_headers") or () if _space(value))
        fact_provenance = fact.provenance if fact else {"reason": selection["status"]}
        header = tuple(fact.header_path) if fact else ()
        product = node.product_identity
        table_targets: list[str] = []
        for key in ("model", "product", "series"):
            value = product.get(key)
            for item in value if isinstance(value, list) else [value]:
                if _space(item):
                    table_targets.append(_space(item))
        document_identity: list[str] = []
        for key in ("manufacturer", "model", "series", "product", "year"):
            value = product.get(key)
            for item in value if isinstance(value, list) else [value]:
                if _space(item):
                    document_identity.append(f"{key}={_space(item)}")
        derived_unit = _attribute_unit(f"{fact.attribute} {' '.join(fact.header_path)}") if fact else UNKNOWN
        return {
            "schema": CANDIDATE_RELATION_SCHEMA,
            "candidate_id": node_id,
            "subject": _candidate_field(
                fact.subject if fact else None,
                provenance=fact_provenance,
                confidence="HIGH" if fact else "NONE",
                alternatives=fact.row_path if fact else (),
            ),
            "row_identity": _candidate_field(
                " > ".join(row_values),
                provenance={"source_node_id": node_id, "field": "row_headers"},
                confidence="HIGH",
                alternatives=row_values,
            ),
            "attribute": _candidate_field(fact.attribute if fact else None, provenance=fact_provenance, confidence="HIGH" if fact else "NONE"),
            "column_identity": _candidate_field(header[-1] if header else None, provenance=fact_provenance, confidence="HIGH" if header else "NONE"),
            "header_path": _candidate_field(
                " > ".join(header),
                provenance=fact_provenance,
                confidence="HIGH" if header else "NONE",
                alternatives=header,
            ),
            "configuration": _candidate_field(
                fact.configuration if fact else None,
                provenance=fact_provenance,
                confidence="HIGH" if fact and fact.configuration else "NONE",
            ),
            "unit": _candidate_field(
                fact.unit if fact and fact.unit else (derived_unit if derived_unit != UNKNOWN else None),
                provenance=fact_provenance if fact and fact.unit else {"source": fact_provenance, "derivation": "CANONICAL_ATTRIBUTE_UNIT_LITERAL"},
                confidence="HIGH" if fact and fact.unit else ("MEDIUM" if derived_unit != UNKNOWN else "NONE"),
            ),
            "table_id": _candidate_field(
                table.table_id if table else None,
                provenance={"source_node_id": table.source_node_id if table else None},
                confidence="HIGH" if table else "NONE",
            ),
            "table_target": _candidate_field(
                table_targets[0] if table_targets else None,
                provenance={"source_node_id": node_id, "field": "product_identity"},
                confidence="MEDIUM",
                alternatives=table_targets,
            ),
            "document_identity": _candidate_field(
                " | ".join(document_identity),
                provenance={"source_node_id": node.document_id, "field": "product_identity"},
                confidence="MEDIUM",
                alternatives=document_identity,
            ),
            "fact_selection": selection,
            "selected_fact_id": fact.fact_id if fact else None,
        }

    @staticmethod
    def relation_signature(query: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
        subject_parts = [
            compare_relation(query["requested_subject"], candidate[name], query_name="requested_subject", candidate_name=name)
            for name in ("subject", "row_identity")
        ]
        subject_states = [value["state"] for value in subject_parts]
        subject = MATCH if MATCH in subject_states else CONFLICT if subject_states and all(value == CONFLICT for value in subject_states) else UNKNOWN
        attribute_parts = [
            compare_relation(query["requested_attribute"], candidate[name], query_name="requested_attribute", candidate_name=name)
            for name in ("attribute", "header_path")
        ]
        attribute_states = [value["state"] for value in attribute_parts]
        attribute = MATCH if MATCH in attribute_states else CONFLICT if attribute_states and all(value == CONFLICT for value in attribute_states) else UNKNOWN
        fields = {
            "subject": subject,
            "attribute": attribute,
            "configuration": compare_relation(
                query["requested_configuration"], candidate["configuration"], query_name="requested_configuration", candidate_name="configuration"
            )["state"],
            "unit": compare_relation(query["requested_unit"], candidate["unit"], query_name="requested_unit", candidate_name="unit")["state"],
            "table_target": compare_relation(query["table_target"], candidate["table_target"], query_name="table_target", candidate_name="table_target")["state"],
        }
        return {"fields": fields, "detail": {"subject": subject_parts, "attribute": attribute_parts}}

    @staticmethod
    def _rejections(
        query: Mapping[str, Any], candidate: Mapping[str, Any], signature: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        field_map = {
            "subject": ("requested_subject", "subject"),
            "attribute": ("requested_attribute", "attribute"),
            "configuration": ("requested_configuration", "configuration"),
            "unit": ("requested_unit", "unit"),
        }
        rejected: list[dict[str, Any]] = []
        for relation_name, (query_name, candidate_name) in field_map.items():
            query_field = query[query_name]
            candidate_field = candidate[candidate_name]
            if (
                query_field["status"] == "EXPLICIT"
                and query_field["confidence_class"] == "HIGH"
                and candidate_field["confidence_class"] == "HIGH"
                and signature["fields"][relation_name] == CONFLICT
            ):
                rejected.append(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "field": relation_name,
                        "query_value": query_field["value"],
                        "candidate_value": candidate_field["value"],
                        "query_provenance": query_field["provenance"],
                        "candidate_provenance": candidate_field["provenance"],
                        "relation": CONFLICT,
                        "rejection_reason": "EXPLICIT_HIGH_CONFIDENCE_RELATION_CONFLICT",
                        "resolver_version": RESOLVER_VERSION,
                    }
                )
        return rejected

    def _selected_fact(self, relation: Mapping[str, Any]) -> CanonicalTableFact | None:
        selected = relation.get("selected_fact_id")
        return next(
            (fact for fact in self.indexes.facts_by_row.get(str(relation["candidate_id"]), ()) if fact.fact_id == selected),
            None,
        )

    def r2_representation(self, relation: Mapping[str, Any]) -> str:
        """Pack the accepted V1.9.8 R2 field sequence without R3/R4 additions."""

        node = self.graph.nodes[str(relation["candidate_id"])]
        document = self.indexes.document_by_id[node.document_id]
        table = self.indexes.table_by_row.get(node.node_id)
        fact = self._selected_fact(relation)
        row_path = tuple(fact.row_path) if fact else tuple(str(value) for value in node.attributes.get("row_headers") or ())
        header_path = tuple(fact.header_path) if fact else ()
        document_value = " | ".join(
            value
            for value in (
                _space(document.manufacturer.value if document.manufacturer else None),
                _space(document.document_type.value),
                _space(document.year.value if document.year else None),
                _space(document.title.value if document.title else None),
            )
            if value
        ) or UNKNOWN
        fields = (
            ("DOCUMENT", document_value),
            ("SECTION", " > ".join(node.section_ancestry) or UNKNOWN),
            ("TABLE", _space(table.caption if table else None) or UNKNOWN),
            ("MODEL / SUBJECT", relation["subject"]["value"]),
            ("ATTRIBUTE", relation["attribute"]["value"]),
            ("CONFIGURATION", relation["configuration"]["value"]),
            ("VALUE", _space(fact.value if fact else None) or UNKNOWN),
            ("UNIT", relation["unit"]["value"]),
            ("ROW LABEL", relation["row_identity"]["value"]),
            ("COLUMN LABEL", relation["column_identity"]["value"]),
            ("HEADER PATH", " > ".join(header_path) or UNKNOWN),
            ("ROW PATH", " > ".join(row_path) or UNKNOWN),
            ("CAPTION", _space(table.caption if table else None) or UNKNOWN),
        )
        return "\n\n".join(f"{name}:\n{value}" for name, value in fields)

    def select(
        self,
        *,
        query: str,
        evidence_type: EvidenceType | str,
        candidate_ids: Sequence[str],
        neural_scores: Mapping[str, float] | None = None,
        reranker: Any | None = None,
    ) -> dict[str, Any]:
        if not self.supports(evidence_type):
            raise ValueError("TABLE_RELATION_RESOLVER_REQUIRES_TABLE_SPEC_LANE")
        ordered_ids = list(dict.fromkeys(str(value) for value in candidate_ids))
        parsed = self.parse(query)
        relations = {node_id: self.candidate_relation(node_id, parsed) for node_id in ordered_ids}
        signatures = {node_id: self.relation_signature(parsed, relation) for node_id, relation in relations.items()}
        rejections = {
            node_id: self._rejections(parsed, relations[node_id], signatures[node_id]) for node_id in ordered_ids
        }
        compatible = [node_id for node_id in ordered_ids if not rejections[node_id]]
        survivors = compatible or ordered_ids
        proofs = [item for node_id in ordered_ids if node_id not in survivors for item in rejections[node_id]]
        representations: dict[str, str] = {}
        scores: dict[str, float] = {}
        if not survivors:
            selected = None
            selection_path = "NEURAL_FALLBACK"
        elif len(survivors) == 1:
            selected = survivors[0]
            selection_path = "DETERMINISTIC_FILTER_ONLY"
        else:
            selection_path = "NEURAL_FALLBACK"
            if neural_scores is not None:
                missing = [node_id for node_id in survivors if node_id not in neural_scores]
                if missing:
                    raise ValueError(f"TABLE_RELATION_RESOLVER_MISSING_NEURAL_SCORES:{','.join(missing)}")
                scores = {node_id: float(neural_scores[node_id]) for node_id in survivors}
            elif reranker is not None:
                representations = {node_id: self.r2_representation(relations[node_id]) for node_id in survivors}
                values, _ = reranker.score(query, [representations[node_id] for node_id in survivors])
                scores = {node_id: float(value) for node_id, value in zip(survivors, values)}
            else:
                raise ValueError("TABLE_RELATION_RESOLVER_NEURAL_FALLBACK_REQUIRES_SCORES_OR_RERANKER")
            selected = min(survivors, key=lambda node_id: (-scores[node_id], node_id)) if survivors else None
        return {
            "schema": PROOF_SCHEMA,
            "resolver_version": RESOLVER_VERSION,
            "policy_version": POLICY_VERSION,
            "query_relation_schema": QUERY_RELATION_SCHEMA,
            "candidate_relation_schema": CANDIDATE_RELATION_SCHEMA,
            "r2_representation_version": R2_REPRESENTATION_VERSION,
            "model": {"identity": MODEL_IDENTITY, "revision": MODEL_REVISION, "max_length": 512},
            "parsed_query_relation": parsed,
            "input_candidate_ids": ordered_ids,
            "candidate_relations": relations,
            "candidate_relation_signatures": signatures,
            "rejection_proofs": proofs,
            "rejected_candidate_ids": [node_id for node_id in ordered_ids if node_id not in survivors],
            "surviving_candidate_ids": survivors,
            "selection_path": selection_path,
            "final_selected_candidate": selected,
            "neural_scores": scores if selection_path == "NEURAL_FALLBACK" else {},
            "neural_representations": representations if selection_path == "NEURAL_FALLBACK" else {},
            "resolver_proof": {
                "unknown_survives": True,
                "hard_rejection_policy": "EXPLICIT_HIGH_CONFIDENCE_CONFLICT_ONLY",
                "zero_compatible_policy": "PRESERVE_ORIGINAL_CANDIDATES",
                "fallback_policy": "FROZEN_R2_OVER_SURVIVORS",
                "specificity_selection": False,
                "gold_or_evaluation_data_used": False,
            },
        }


def select_canonical_candidate(
    *,
    evidence_type: EvidenceType | str,
    query: str,
    candidate_ids: Sequence[str],
    existing_selected_candidate: str | None,
    table_resolver: CanonicalTableRelationResolver | None = None,
    neural_scores: Mapping[str, float] | None = None,
    reranker: Any | None = None,
) -> dict[str, Any]:
    """Canonical selection dispatcher with exact non-table bypass semantics."""

    if not CanonicalTableRelationResolver.supports(evidence_type):
        return {
            "resolver_executed": False,
            "selection_path": "NON_TABLE_UNCHANGED",
            "final_selected_candidate": existing_selected_candidate,
            "input_candidate_ids": list(candidate_ids),
        }
    if table_resolver is None:
        raise ValueError("CANONICAL_TABLE_SELECTION_REQUIRES_RELATION_RESOLVER")
    result = table_resolver.select(
        query=query,
        evidence_type=evidence_type,
        candidate_ids=candidate_ids,
        neural_scores=neural_scores,
        reranker=reranker,
    )
    return {"resolver_executed": True, **result}
