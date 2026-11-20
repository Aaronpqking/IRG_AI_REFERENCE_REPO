from __future__ import annotations

"""Canonical, provenance-bearing technical-document intermediate representation.

This module is deliberately an ingestion/compiler boundary.  Path and filename
conventions may be interpreted here, but consumers receive only the versioned
IR and never need to know how a manufacturer laid out its source corpus.
"""

from dataclasses import asdict, dataclass, field
from enum import StrEnum
import hashlib
from pathlib import PurePosixPath
import re
from typing import Any, Iterable, Mapping, Sequence

from .model import DocumentGraph, Node, NodeType
from .owner_identity import compile_owner_identities, normalize_model


IR_VERSION = "1.0.0"


class ProvenanceClass(StrEnum):
    SOURCE_BODY_EXPLICIT = "SOURCE_BODY_EXPLICIT"
    SOURCE_TITLE_EXPLICIT = "SOURCE_TITLE_EXPLICIT"
    SOURCE_COVER_EXPLICIT = "SOURCE_COVER_EXPLICIT"
    SOURCE_METADATA_EXPLICIT = "SOURCE_METADATA_EXPLICIT"
    FILENAME_DERIVED = "FILENAME_DERIVED"
    PATH_DERIVED = "PATH_DERIVED"
    STRUCTURAL_DERIVED = "STRUCTURAL_DERIVED"
    CATEGORY_INFERRED = "CATEGORY_INFERRED"
    LEXICAL_INFERRED = "LEXICAL_INFERRED"


PROVENANCE_PRECEDENCE: dict[ProvenanceClass, int] = {
    ProvenanceClass.SOURCE_BODY_EXPLICIT: 0,
    ProvenanceClass.SOURCE_TITLE_EXPLICIT: 0,
    ProvenanceClass.SOURCE_COVER_EXPLICIT: 0,
    ProvenanceClass.SOURCE_METADATA_EXPLICIT: 1,
    ProvenanceClass.FILENAME_DERIVED: 2,
    ProvenanceClass.PATH_DERIVED: 3,
    ProvenanceClass.STRUCTURAL_DERIVED: 4,
    ProvenanceClass.CATEGORY_INFERRED: 5,
    ProvenanceClass.LEXICAL_INFERRED: 6,
}


class ConfidenceClass(StrEnum):
    EXPLICIT = "EXPLICIT"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"


class CanonicalDocumentType(StrEnum):
    OM = "OM"
    QSG = "QSG"
    INSTALL = "INSTALL"
    SERVICE = "SERVICE"
    SPEC = "SPEC"
    PARTS = "PARTS"
    WARRANTY = "WARRANTY"
    OTHER = "OTHER"


class CanonicalIdentityType(StrEnum):
    MODEL = "MODEL"
    BASE_MODEL = "BASE_MODEL"
    SERIES = "SERIES"
    FAMILY = "FAMILY"
    PART_NUMBER = "PART_NUMBER"
    CONFIGURATION = "CONFIGURATION"
    COVERAGE_GROUP = "COVERAGE_GROUP"


class RelationshipType(StrEnum):
    PARENT_OF = "PARENT_OF"
    CHILD_OF = "CHILD_OF"
    REFERENCES = "REFERENCES"
    APPLIES_TO = "APPLIES_TO"
    VARIANT_OF = "VARIANT_OF"
    BASE_MODEL_OF = "BASE_MODEL_OF"
    SIBLING_OF = "SIBLING_OF"
    TABLE_HEADER_OF = "TABLE_HEADER_OF"
    TABLE_VALUE_FOR = "TABLE_VALUE_FOR"
    PROCEDURE_STEP_OF = "PROCEDURE_STEP_OF"
    WARNING_GOVERNS = "WARNING_GOVERNS"
    FIGURE_REFERENCED_BY = "FIGURE_REFERENCED_BY"


@dataclass(frozen=True)
class ProvenancedValue:
    value: Any
    provenance: str
    confidence_class: str
    source_reference: str | None = None

    @property
    def precedence(self) -> int:
        return PROVENANCE_PRECEDENCE[ProvenanceClass(self.provenance)]

    def stronger_than(self, other: "ProvenancedValue") -> bool:
        return self.precedence < other.precedence


@dataclass(frozen=True)
class CanonicalDocument:
    document_id: str
    manufacturer: ProvenancedValue | None
    document_type: ProvenancedValue
    title: ProvenancedValue | None
    revision: ProvenancedValue | None
    year: ProvenancedValue | None
    source_path: ProvenancedValue
    source_hash: ProvenancedValue | None
    source_provenance: Mapping[str, Any]


@dataclass(frozen=True)
class CanonicalIdentity:
    canonical_id: str
    identity_type: str
    manufacturer: ProvenancedValue | None
    series: ProvenancedValue | None = None
    family: ProvenancedValue | None = None
    base_model: ProvenancedValue | None = None
    model: ProvenancedValue | None = None
    variant: ProvenancedValue | None = None
    suffix: ProvenancedValue | None = None
    part_number: ProvenancedValue | None = None
    configuration: ProvenancedValue | None = None
    normalized_forms: tuple[str, ...] = ()
    coverage_members: tuple[str, ...] = ()

    def display_value(self) -> str:
        for value in (self.model, self.part_number, self.configuration, self.series, self.family):
            if value and str(value.value).strip():
                return str(value.value)
        return self.canonical_id


@dataclass(frozen=True)
class CanonicalApplicability:
    document_id: str
    identity_id: str
    relation_type: str
    provenance: str
    confidence_class: str


@dataclass(frozen=True)
class CanonicalRelationship:
    relationship_type: str
    source_id: str
    target_id: str
    provenance: str
    source_reference: str | None = None


@dataclass(frozen=True)
class CanonicalSection:
    section_id: str
    document_id: str
    heading: str
    section_ancestry: tuple[str, ...]
    page: int | None
    source_node_id: str
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class CanonicalParagraph:
    paragraph_id: str
    document_id: str
    section_ancestry: tuple[str, ...]
    heading_ancestry: tuple[str, ...]
    source_text: str
    page: int | None
    source_node_id: str
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class CanonicalProcedureStep:
    step_id: str
    ordinal: int
    action: str
    source_text: str
    parent_procedure: str
    referenced_figure_or_table: tuple[str, ...]
    source_node_id: str
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class CanonicalProcedure:
    procedure_id: str
    document_id: str
    title: str
    section_ancestry: tuple[str, ...]
    ordered_steps: tuple[CanonicalProcedureStep, ...]
    source_text: str
    page: int | None
    source_node_id: str
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class CanonicalWarning:
    warning_id: str
    document_id: str
    warning_type: str
    heading: str
    body: str
    section_ancestry: tuple[str, ...]
    applicability: tuple[str, ...]
    governed_procedure: str | None
    page: int | None
    source_node_id: str
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class CanonicalTableRow:
    row_id: str
    values: tuple[str, ...]
    row_path: tuple[str, ...]
    source_node_id: str
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class CanonicalTableFact:
    fact_id: str
    subject: str | None
    attribute: str
    configuration: str | None
    value: str
    unit: str | None
    header_path: tuple[str, ...]
    row_path: tuple[str, ...]
    source_row_id: str
    source_table_id: str
    source_node_id: str
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class CanonicalTable:
    table_id: str
    document_id: str
    caption: str | None
    section_ancestry: tuple[str, ...]
    headers: tuple[tuple[str, ...], ...]
    rows: tuple[CanonicalTableRow, ...]
    facts: tuple[CanonicalTableFact, ...]
    page: int | None
    source_node_id: str
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class CanonicalFigure:
    figure_id: str
    document_id: str
    page: int | None
    bbox: Mapping[str, Any] | None
    caption: str | None
    ocr: str | None
    section_ancestry: tuple[str, ...]
    explicit_references: tuple[str, ...]
    source_crop_identity: str | None
    source_node_id: str
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class CanonicalStructure:
    sections: tuple[CanonicalSection, ...] = ()
    paragraphs: tuple[CanonicalParagraph, ...] = ()
    procedures: tuple[CanonicalProcedure, ...] = ()
    warnings: tuple[CanonicalWarning, ...] = ()
    tables: tuple[CanonicalTable, ...] = ()
    figures: tuple[CanonicalFigure, ...] = ()
    captions: tuple[CanonicalParagraph, ...] = ()
    ocr_regions: tuple[CanonicalParagraph, ...] = ()


@dataclass(frozen=True)
class CanonicalTechnicalDocumentIR:
    ir_version: str
    documents: tuple[CanonicalDocument, ...]
    identities: tuple[CanonicalIdentity, ...]
    applicability: tuple[CanonicalApplicability, ...]
    structure: CanonicalStructure
    relationships: tuple[CanonicalRelationship, ...]
    compiler_metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ManufacturerProfile:
    """Optional declarative compiler data; never consumed by runtime."""

    manufacturer: str
    document_type_aliases: Mapping[str, str] = field(default_factory=dict)
    series_aliases: Mapping[str, str] = field(default_factory=dict)
    path_fields: tuple[str, ...] = ()
    identifier_separators: tuple[str, ...] = ("_", "/")
    identifier_grammar_hints: tuple[str, ...] = ()


DEFAULT_DOCUMENT_TYPE_ALIASES: dict[str, CanonicalDocumentType] = {
    "om": CanonicalDocumentType.OM,
    "owners_manual": CanonicalDocumentType.OM,
    "qsg": CanonicalDocumentType.QSG,
    "quick_start": CanonicalDocumentType.QSG,
    "quick_start_guide": CanonicalDocumentType.QSG,
    "install": CanonicalDocumentType.INSTALL,
    "installation": CanonicalDocumentType.INSTALL,
    "service": CanonicalDocumentType.SERVICE,
    "spec": CanonicalDocumentType.SPEC,
    "specification": CanonicalDocumentType.SPEC,
    "submittal": CanonicalDocumentType.SPEC,
    "parts": CanonicalDocumentType.PARTS,
    "warranty": CanonicalDocumentType.WARRANTY,
}


def _stable(prefix: str, *values: object) -> str:
    raw = "\x1f".join(str(value) for value in values)
    return f"cir_{prefix}_{hashlib.sha256(raw.encode('utf-8')).hexdigest()}"


def _confidence(provenance: ProvenanceClass) -> ConfidenceClass:
    if provenance.value.startswith("SOURCE_"):
        return ConfidenceClass.EXPLICIT
    if provenance in {
        ProvenanceClass.FILENAME_DERIVED,
        ProvenanceClass.PATH_DERIVED,
        ProvenanceClass.STRUCTURAL_DERIVED,
    }:
        return ConfidenceClass.DERIVED
    return ConfidenceClass.INFERRED


def _pv(value: Any, provenance: ProvenanceClass, reference: str | None = None) -> ProvenancedValue:
    return ProvenancedValue(value, provenance.value, _confidence(provenance).value, reference)


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _forms(value: str) -> tuple[str, ...]:
    display = _clean(value)
    compact = normalize_model(display)
    hyphenated = re.sub(r"[^a-z0-9]+", "-", display.casefold()).strip("-")
    spaced = re.sub(r"[^a-z0-9]+", " ", display.casefold()).strip()
    return tuple(dict.fromkeys(item for item in (display.casefold(), compact, hyphenated, spaced) if item))


def _identity_parts(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in re.split(r"[_/]+", value) if item.strip())


def _technical_identifier(value: str) -> bool:
    compact = normalize_model(value)
    return bool(len(compact) >= 3 and any(c.isdigit() for c in compact) and not re.fullmatch(r"(?:19|20)\d{2}", compact))


def _unit(value: str) -> str | None:
    match = re.search(r"(?:^|\s)(°?[a-zA-Z%]+)\s*$", value)
    return match.group(1) if match else None


def _semantic_table_fact_id(
    document_id: str,
    subject: str | None,
    attribute: str,
    configuration: str | None,
    value: str,
    unit: str | None,
) -> str:
    """Identify a fact by meaning, not by its visual table coordinates."""

    return _stable(
        "table_fact",
        document_id,
        normalize_model(subject or ""),
        normalize_model(attribute),
        normalize_model(configuration or ""),
        _clean(value).casefold(),
        normalize_model(unit or ""),
    )


def _configuration_header_part(parts: Sequence[str]) -> str | None:
    """Return source-explicit configuration ancestry without product knowledge."""

    pattern = re.compile(
        r"\b(?:configuration|natural\s+gas|propane|l\.?p\.?\s*gas|built[ -]?in|portable|factory[ -]?built|masonry[ -]?built)\b",
        re.IGNORECASE,
    )
    return next((part for part in parts if pattern.search(part)), None)


def _unit_from_header(parts: Sequence[str]) -> str | None:
    for part in reversed(parts):
        match = re.search(r"[\[(]\s*([a-zA-Z%]+)\.?\s*[\])]", part)
        if match:
            return match.group(1)
    return None


def _shared_identifier_stem(values: Sequence[str]) -> bool:
    """Recognize a neutral repeated identifier family from sibling headers."""

    if any(not re.search(r"[-_/]", value) for value in values):
        return False
    cleaned = [re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip().split() for value in values]
    if len(cleaned) < 2 or any(len(parts) < 2 for parts in cleaned):
        return False
    stems = {tuple(parts[:-1]) for parts in cleaned}
    suffixes = {parts[-1] for parts in cleaned}
    return len(stems) == 1 and len(suffixes) >= 2 and len("".join(next(iter(stems)))) >= 2


def _column_subject_ancestors(headers: Sequence[Sequence[str]]) -> dict[str, str]:
    """Infer only strongly evidenced hierarchical column-subject ancestors."""

    hierarchical = [tuple(_clean(part) for part in path if _clean(part)) for path in headers if len(path) >= 2]
    by_ancestor: dict[str, list[tuple[str, ...]]] = {}
    display: dict[str, str] = {}
    for path in hierarchical:
        key = normalize_model(path[0])
        if not key:
            continue
        display.setdefault(key, path[0])
        by_ancestor.setdefault(key, []).append(path[1:])
    inferred: dict[str, str] = {}
    for key, value in display.items():
        if re.search(r"\bmodels?\b", value, re.IGNORECASE):
            inferred[key] = "SOURCE_HEADER_EXPLICIT"
    ancestors = list(display.values())
    repeated_leaves = any(
        len({normalize_model(path[0]) for path in hierarchical if tuple(path[1:]) == leaf}) >= 2
        for leaf in {tuple(path[1:]) for path in hierarchical}
    )
    identifier_family = len(ancestors) >= 2 and (
        all(_technical_identifier(value) and any(c.isalpha() for c in value) for value in ancestors)
        or _shared_identifier_stem(ancestors)
    )
    if repeated_leaves and identifier_family:
        for key in by_ancestor:
            inferred.setdefault(key, "STRUCTURAL_DERIVED")
    return inferred


def _table_fact_provenance(
    base: Mapping[str, Any],
    cell: Mapping[str, Any],
    *,
    orientation: str,
    subject_axis: str,
    subject_state: str,
    attribute_axis: str,
    attribute_state: str,
    configuration: str | None = None,
) -> dict[str, Any]:
    provenance = dict(base)
    provenance["source_cells"] = [dict(cell)]
    provenance["semantic_orientation"] = orientation
    provenance["axis_roles"] = {
        "subject": {"axis": subject_axis, "state": subject_state},
        "attribute": {"axis": attribute_axis, "state": attribute_state},
        "configuration": {
            "axis": "COLUMN_HEADER_ANCESTRY" if configuration else "NONE",
            "state": "SOURCE_HEADER_EXPLICIT" if configuration else "UNKNOWN",
        },
    }
    return provenance


def _references(value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(re.findall(r"\b(?:figure|fig\.?|table)\s*[A-Z0-9.-]+", value, re.IGNORECASE)))


class GenericTechnicalDocumentCompiler:
    """Compile a Docling structural graph into manufacturer-neutral IR."""

    def __init__(self, profiles: Mapping[str, ManufacturerProfile] | None = None) -> None:
        self.profiles = {key.casefold(): value for key, value in (profiles or {}).items()}

    def compile(self, graph: DocumentGraph) -> CanonicalTechnicalDocumentIR:
        owner_by_document = {row.document_id: row for row in compile_owner_identities(graph)}
        documents: list[CanonicalDocument] = []
        identities: list[CanonicalIdentity] = []
        applicability: list[CanonicalApplicability] = []
        relationships: list[CanonicalRelationship] = []
        identity_ids_by_document: dict[str, list[str]] = {}
        for document_id in graph.document_ids:
            node = graph.nodes[document_id]
            document = self._document(graph, node)
            documents.append(document)
            compiled = self._identities(node, owner_by_document[document_id])
            identities.extend(compiled)
            identity_ids_by_document[document_id] = [row.canonical_id for row in compiled]
            for identity in compiled:
                strongest = min(
                    (value for value in (identity.model, identity.part_number, identity.configuration, identity.series, identity.family) if value),
                    key=lambda value: value.precedence,
                    default=_pv(identity.display_value(), ProvenanceClass.LEXICAL_INFERRED, node.relative_path),
                )
                applicability.append(CanonicalApplicability(
                    document_id=document_id,
                    identity_id=identity.canonical_id,
                    relation_type=RelationshipType.APPLIES_TO.value,
                    provenance=strongest.provenance,
                    confidence_class=strongest.confidence_class,
                ))
                relationships.append(CanonicalRelationship(
                    RelationshipType.APPLIES_TO.value,
                    document_id,
                    identity.canonical_id,
                    strongest.provenance,
                    strongest.source_reference,
                ))
            member_ids = [row.canonical_id for row in compiled if row.identity_type != CanonicalIdentityType.COVERAGE_GROUP.value]
            for group in (row for row in compiled if row.identity_type == CanonicalIdentityType.COVERAGE_GROUP.value):
                for member in member_ids:
                    relationships.append(CanonicalRelationship(
                        RelationshipType.SIBLING_OF.value,
                        member,
                        group.canonical_id,
                        ProvenanceClass.PATH_DERIVED.value,
                        node.relative_path,
                    ))

        structure, structural_relationships = self._structure(graph)
        relationships.extend(structural_relationships)
        return CanonicalTechnicalDocumentIR(
            ir_version=IR_VERSION,
            documents=tuple(sorted(documents, key=lambda row: row.document_id)),
            identities=tuple(sorted(identities, key=lambda row: (row.canonical_id, row.identity_type))),
            applicability=tuple(sorted(applicability, key=lambda row: (row.document_id, row.identity_id))),
            structure=structure,
            relationships=tuple(sorted(relationships, key=lambda row: (row.relationship_type, row.source_id, row.target_id))),
            compiler_metadata={
                "compiler": type(self).__name__,
                "manufacturer_profiles": sorted(self.profiles),
                "manufacturer_conditionals": 0,
                "source_graph_documents": len(graph.document_ids),
                "source_graph_nodes": len(graph.nodes),
            },
        )

    def _document(self, graph: DocumentGraph, node: Node) -> CanonicalDocument:
        path = PurePosixPath(node.relative_path.replace("\\", "/"))
        identity = node.product_identity
        manufacturer = _clean(identity.get("manufacturer"))
        profile = self.profiles.get(manufacturer.casefold())
        aliases = dict(DEFAULT_DOCUMENT_TYPE_ALIASES)
        if profile:
            aliases.update({key.casefold(): CanonicalDocumentType(value) for key, value in profile.document_type_aliases.items()})
        document_type = next((aliases[part.casefold()] for part in reversed(path.parts[:-1]) if part.casefold() in aliases), CanonicalDocumentType.OTHER)
        headings = [
            item.source_text.strip()
            for item in graph.ordered_document_nodes(node.document_id)
            if item.page_number == 1 and item.node_type == NodeType.SECTION and item.source_text.strip()
        ]
        title = headings[0] if headings else path.stem
        source_hash = node.source_provenance.get("source_sha256")
        return CanonicalDocument(
            document_id=node.document_id,
            manufacturer=_pv(manufacturer, ProvenanceClass.SOURCE_METADATA_EXPLICIT, node.relative_path) if manufacturer else None,
            document_type=_pv(document_type.value, ProvenanceClass.PATH_DERIVED, node.relative_path),
            title=_pv(title, ProvenanceClass.SOURCE_TITLE_EXPLICIT if headings else ProvenanceClass.FILENAME_DERIVED, node.relative_path) if title else None,
            revision=_pv(identity["revision"], ProvenanceClass.SOURCE_METADATA_EXPLICIT, node.relative_path) if identity.get("revision") else None,
            year=_pv(str(identity["year"]), ProvenanceClass.SOURCE_METADATA_EXPLICIT, node.relative_path) if identity.get("year") else None,
            source_path=_pv(node.relative_path, ProvenanceClass.SOURCE_METADATA_EXPLICIT, node.relative_path),
            source_hash=_pv(str(source_hash), ProvenanceClass.SOURCE_METADATA_EXPLICIT, node.relative_path) if source_hash else None,
            source_provenance=dict(node.source_provenance),
        )

    def _identities(self, node: Node, owner: Any) -> list[CanonicalIdentity]:
        manufacturer_text = _clean(owner.manufacturer or node.product_identity.get("manufacturer"))
        manufacturer = _pv(manufacturer_text, ProvenanceClass.SOURCE_METADATA_EXPLICIT, node.relative_path) if manufacturer_text else None
        origin_map = {
            "EXISTING_METADATA": ProvenanceClass.SOURCE_METADATA_EXPLICIT,
            "TITLE": ProvenanceClass.SOURCE_TITLE_EXPLICIT,
            "COVER_MODEL_DECLARATION": ProvenanceClass.SOURCE_COVER_EXPLICIT,
            "MODEL_TABLE": ProvenanceClass.SOURCE_BODY_EXPLICIT,
            "FILENAME": ProvenanceClass.FILENAME_DERIVED,
            "PATH": ProvenanceClass.PATH_DERIVED,
        }
        grouped: dict[str, list[Any]] = {}
        for alias in owner.model_aliases:
            if _technical_identifier(alias.source_literal):
                grouped.setdefault(alias.normalized, []).append(alias)
        output: list[CanonicalIdentity] = []
        for normalized, aliases in sorted(grouped.items()):
            aliases.sort(key=lambda item: PROVENANCE_PRECEDENCE[origin_map.get(item.source, ProvenanceClass.LEXICAL_INFERRED)])
            best = aliases[0]
            provenance = origin_map.get(best.source, ProvenanceClass.LEXICAL_INFERRED)
            value = _pv(best.source_literal, provenance, node.relative_path)
            base = re.sub(r"(?:[-_/]?[a-z])?[-_/]\d+$", "", best.source_literal, flags=re.IGNORECASE)
            suffix_match = re.search(r"[-_/]([a-z0-9]+)$", best.source_literal, re.IGNORECASE)
            output.append(CanonicalIdentity(
                canonical_id=_stable("identity", node.document_id, CanonicalIdentityType.MODEL.value, normalized),
                identity_type=CanonicalIdentityType.MODEL.value,
                manufacturer=manufacturer,
                base_model=_pv(base, ProvenanceClass.STRUCTURAL_DERIVED, node.relative_path) if base and normalize_model(base) != normalized else None,
                model=value,
                suffix=_pv(suffix_match.group(1), ProvenanceClass.STRUCTURAL_DERIVED, node.relative_path) if suffix_match else None,
                normalized_forms=tuple(dict.fromkeys(form for alias in aliases for form in _forms(alias.source_literal))),
            ))

        path = PurePosixPath(node.relative_path.replace("\\", "/"))
        coverage_candidates = [path.stem]
        year_index = next((index for index, part in enumerate(path.parts) if re.fullmatch(r"(?:19|20)\d{2}", part)), None)
        if year_index and year_index > 0:
            coverage_candidates.append(path.parts[year_index - 1])
        for raw in coverage_candidates:
            members = tuple(part for part in _identity_parts(raw) if _technical_identifier(part))
            if len(members) < 2:
                continue
            normalized_group = normalize_model(raw)
            if any(row.identity_type == CanonicalIdentityType.COVERAGE_GROUP.value and normalized_group in row.normalized_forms for row in output):
                continue
            output.append(CanonicalIdentity(
                canonical_id=_stable("identity", node.document_id, CanonicalIdentityType.COVERAGE_GROUP.value, normalized_group),
                identity_type=CanonicalIdentityType.COVERAGE_GROUP.value,
                manufacturer=manufacturer,
                model=_pv(raw, ProvenanceClass.FILENAME_DERIVED if raw == path.stem else ProvenanceClass.PATH_DERIVED, node.relative_path),
                normalized_forms=_forms(raw),
                coverage_members=tuple(normalize_model(value) for value in members),
            ))

        for kind, raw in (
            (CanonicalIdentityType.SERIES, _clean(owner.series)),
            (CanonicalIdentityType.FAMILY, _clean(owner.product_family)),
        ):
            if not raw:
                continue
            output.append(CanonicalIdentity(
                canonical_id=_stable("identity", node.document_id, kind.value, normalize_model(raw)),
                identity_type=kind.value,
                manufacturer=manufacturer,
                series=_pv(raw, ProvenanceClass.PATH_DERIVED, node.relative_path) if kind == CanonicalIdentityType.SERIES else None,
                family=_pv(raw, ProvenanceClass.PATH_DERIVED, node.relative_path) if kind == CanonicalIdentityType.FAMILY else None,
                normalized_forms=_forms(raw),
            ))
        for alias in owner.configuration_aliases:
            raw = _clean(alias.source_literal)
            if not raw:
                continue
            provenance = origin_map.get(alias.source, ProvenanceClass.STRUCTURAL_DERIVED)
            output.append(CanonicalIdentity(
                canonical_id=_stable("identity", node.document_id, CanonicalIdentityType.CONFIGURATION.value, normalize_model(raw)),
                identity_type=CanonicalIdentityType.CONFIGURATION.value,
                manufacturer=manufacturer,
                configuration=_pv(raw, provenance, node.relative_path),
                normalized_forms=_forms(raw),
            ))
        reserved = {
            normalize_model(manufacturer_text),
            normalize_model(_clean(owner.series)),
            normalize_model(_clean(owner.product_family)),
            "om", "qsg", "install", "installation", "service", "spec", "parts", "warranty",
        }
        for part in path.parts[1:-1]:
            raw = _clean(part)
            compact = normalize_model(raw)
            if not raw or compact in reserved or re.fullmatch(r"(?:19|20)\d{2}", compact) or _technical_identifier(raw):
                continue
            output.append(CanonicalIdentity(
                canonical_id=_stable("identity", node.document_id, CanonicalIdentityType.CONFIGURATION.value, compact),
                identity_type=CanonicalIdentityType.CONFIGURATION.value,
                manufacturer=manufacturer,
                configuration=_pv(raw, ProvenanceClass.PATH_DERIVED, node.relative_path),
                normalized_forms=_forms(raw),
            ))
        unique = {(row.canonical_id, row.identity_type): row for row in output}
        return list(unique.values())

    def _structure(self, graph: DocumentGraph) -> tuple[CanonicalStructure, list[CanonicalRelationship]]:
        sections: list[CanonicalSection] = []
        paragraphs: list[CanonicalParagraph] = []
        procedures: list[CanonicalProcedure] = []
        warnings: list[CanonicalWarning] = []
        tables: list[CanonicalTable] = []
        figures: list[CanonicalFigure] = []
        captions: list[CanonicalParagraph] = []
        ocr_regions: list[CanonicalParagraph] = []
        relationships: list[CanonicalRelationship] = []
        for node in sorted(graph.nodes.values(), key=lambda item: item.node_id):
            if node.node_type == NodeType.SECTION:
                sections.append(CanonicalSection(node.node_id, node.document_id, node.source_text, tuple(node.section_ancestry), node.page_number, node.node_id, dict(node.source_provenance)))
            elif node.node_type == NodeType.PARAGRAPH:
                paragraphs.append(self._paragraph(node))
            elif node.node_type == NodeType.CAPTION:
                captions.append(self._paragraph(node))
            elif node.node_type == NodeType.OCR_REGION:
                ocr_regions.append(self._paragraph(node))
            elif node.node_type == NodeType.PROCEDURE:
                steps: list[CanonicalProcedureStep] = []
                children = [child for child in graph.children(node.node_id) if child.node_type == NodeType.PROCEDURE_STEP]
                children.sort(key=lambda child: (child.attributes.get("step_number") if isinstance(child.attributes.get("step_number"), int) else 1_000_000, child.reading_order, child.node_id))
                for position, child in enumerate(children, 1):
                    ordinal = child.attributes.get("step_number") if isinstance(child.attributes.get("step_number"), int) else position
                    refs = _references(child.source_text)
                    steps.append(CanonicalProcedureStep(child.node_id, ordinal, child.source_text, child.source_text, node.node_id, refs, child.node_id, dict(child.source_provenance)))
                    relationships.append(CanonicalRelationship(RelationshipType.PROCEDURE_STEP_OF.value, child.node_id, node.node_id, ProvenanceClass.STRUCTURAL_DERIVED.value, child.node_id))
                procedures.append(CanonicalProcedure(node.node_id, node.document_id, _clean(node.attributes.get("title")), tuple(node.section_ancestry), tuple(steps), node.source_text, node.page_number, node.node_id, dict(node.source_provenance)))
            elif node.node_type == NodeType.ADMONITION:
                governed = next((candidate.node_id for candidate in graph.ordered_document_nodes(node.document_id) if candidate.node_type == NodeType.PROCEDURE and candidate.page_number == node.page_number and candidate.reading_order >= node.reading_order), None)
                warnings.append(CanonicalWarning(node.node_id, node.document_id, _clean(node.attributes.get("admonition_type")) or "NOTE", _clean(node.attributes.get("heading")), node.source_text, tuple(node.section_ancestry), (), governed, node.page_number, node.node_id, dict(node.source_provenance)))
                if governed:
                    relationships.append(CanonicalRelationship(RelationshipType.WARNING_GOVERNS.value, node.node_id, governed, ProvenanceClass.STRUCTURAL_DERIVED.value, node.node_id))
            elif node.node_type == NodeType.TABLE:
                tables.append(self._table(graph, node, relationships))
            elif node.node_type == NodeType.FIGURE:
                figures.append(CanonicalFigure(
                    node.node_id,
                    node.document_id,
                    node.page_number,
                    dict(node.bbox) if node.bbox else None,
                    _clean(node.attributes.get("caption")) or None,
                    _clean(node.attributes.get("ocr_text") or node.source_text) or None,
                    tuple(node.section_ancestry),
                    tuple(node.attributes.get("callouts") or ()),
                    _clean(node.attributes.get("image_region_reference")) or None,
                    node.node_id,
                    dict(node.source_provenance),
                ))
        return CanonicalStructure(tuple(sections), tuple(paragraphs), tuple(procedures), tuple(warnings), tuple(tables), tuple(figures), tuple(captions), tuple(ocr_regions)), relationships

    @staticmethod
    def _paragraph(node: Node) -> CanonicalParagraph:
        return CanonicalParagraph(node.node_id, node.document_id, tuple(node.section_ancestry), tuple(node.section_ancestry), node.source_text, node.page_number, node.node_id, dict(node.source_provenance))

    @staticmethod
    def _table(graph: DocumentGraph, node: Node, relationships: list[CanonicalRelationship]) -> CanonicalTable:
        headers = tuple(tuple(str(part) for part in path) for path in node.attributes.get("column_headers") or ())
        column_subjects = _column_subject_ancestors(headers)
        rows: list[CanonicalTableRow] = []
        facts: list[CanonicalTableFact] = []
        for child in graph.children(node.node_id):
            if child.node_type != NodeType.TABLE_ROW:
                continue
            row_path = tuple(str(value) for value in child.attributes.get("row_headers") or ())
            cells = list(child.attributes.get("cells") or ())
            rows.append(CanonicalTableRow(child.node_id, tuple(str(cell.get("value") or "") for cell in cells), row_path, child.node_id, dict(child.source_provenance)))
            row_subject = " > ".join(row_path).strip() or None
            for cell in cells:
                value = _clean(cell.get("value"))
                header = tuple(part.strip() for part in str(cell.get("header_path") or "").split(">") if part.strip())
                if not value:
                    continue
                header_subject = " > ".join(header).strip() or None
                if value and (
                    (row_subject and normalize_model(value) == normalize_model(row_subject))
                    or (header_subject and normalize_model(value) == normalize_model(header_subject))
                ):
                    continue
                # Preserve both semantic axes.  A row-major and a column-major
                # rendering therefore compile to the same pair of facts; runtime
                # retrieval no longer has to guess the source's visual orientation.
                orientations = [(
                    row_subject or header_subject,
                    header_subject or "value",
                    "ROW_SUBJECT",
                    "ROW",
                    "SOURCE_CELL_EXPLICIT" if row_subject else "UNKNOWN",
                    "COLUMN_HEADER",
                    "SOURCE_HEADER_EXPLICIT" if header_subject else "UNKNOWN",
                )]
                if row_subject and header_subject and normalize_model(row_subject) != normalize_model(header_subject):
                    orientations.append((
                        header_subject,
                        row_subject,
                        "COLUMN_SUBJECT",
                        "COLUMN_HEADER",
                        "UNKNOWN",
                        "ROW",
                        "SOURCE_CELL_EXPLICIT",
                    ))
                for subject, attribute, orientation, subject_axis, subject_state, attribute_axis, attribute_state in orientations:
                    if subject and normalize_model(value) == normalize_model(subject):
                        continue
                    unit = _unit(value)
                    fact_id = _semantic_table_fact_id(node.document_id, subject, attribute, None, value, unit)
                    provenance = _table_fact_provenance(
                        child.source_provenance,
                        cell,
                        orientation=orientation,
                        subject_axis=subject_axis,
                        subject_state=subject_state,
                        attribute_axis=attribute_axis,
                        attribute_state=attribute_state,
                    )
                    facts.append(CanonicalTableFact(fact_id, subject, attribute, None, value, unit, header, row_path, child.node_id, node.node_id, child.node_id, provenance))
                    relationships.append(CanonicalRelationship(RelationshipType.TABLE_VALUE_FOR.value, fact_id, child.node_id, ProvenanceClass.STRUCTURAL_DERIVED.value, child.node_id))
                # A strong hierarchical column-subject ancestor carries the
                # entity identity; row ancestry and non-configuration leaves
                # together carry the attribute. Existing facts above remain
                # available, making this a conservative additive repair.
                ancestor_state = column_subjects.get(normalize_model(header[0])) if len(header) >= 2 else None
                if ancestor_state and row_path:
                    configuration = _configuration_header_part(header[1:])
                    leaves = [part for part in header[1:] if part != configuration]
                    attribute = " > ".join([*row_path, *leaves]).strip()
                    subject = header[0]
                    unit = _unit(value) or _unit_from_header(leaves)
                    if attribute and normalize_model(value) != normalize_model(subject):
                        fact_id = _semantic_table_fact_id(node.document_id, subject, attribute, configuration, value, unit)
                        provenance = _table_fact_provenance(
                            child.source_provenance,
                            cell,
                            orientation="COLUMN_SUBJECT",
                            subject_axis="COLUMN_HEADER_ANCESTRY",
                            subject_state=ancestor_state,
                            attribute_axis="ROW_AND_COLUMN_LEAF",
                            attribute_state="STRUCTURAL_DERIVED",
                            configuration=configuration,
                        )
                        facts.append(CanonicalTableFact(fact_id, subject, attribute, configuration, value, unit, header, row_path, child.node_id, node.node_id, child.node_id, provenance))
                        relationships.append(CanonicalRelationship(RelationshipType.TABLE_VALUE_FOR.value, fact_id, child.node_id, ProvenanceClass.STRUCTURAL_DERIVED.value, child.node_id))
            relationships.append(CanonicalRelationship(RelationshipType.CHILD_OF.value, child.node_id, node.node_id, ProvenanceClass.STRUCTURAL_DERIVED.value, child.node_id))
        return CanonicalTable(node.node_id, node.document_id, _clean(node.attributes.get("caption")) or None, tuple(node.section_ancestry), headers, tuple(rows), tuple(facts), node.page_number, node.node_id, dict(node.source_provenance))


def select_strongest(values: Iterable[ProvenancedValue]) -> ProvenancedValue | None:
    """Select deterministically; weaker inferred values can never veto explicit ones."""

    candidates = list(values)
    if not candidates:
        return None
    return min(candidates, key=lambda value: (value.precedence, str(value.value).casefold(), value.source_reference or ""))
