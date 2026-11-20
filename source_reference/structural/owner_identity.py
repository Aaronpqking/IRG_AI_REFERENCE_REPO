from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import re
from typing import Any, Iterable

from src.technical_tokens import extract_technical_tokens

from .model import DocumentGraph, Node, NodeType
from .retrieval_text import normalize


_YEAR = re.compile(r"^(?:19|20)\d{2}$")
_MODEL_DECLARATION = re.compile(r"(?im)\bmodels?(?:\s+(?:number|no\.?|#))?\s*[:#]?\s*([^\n]{1,160})")
_CONFIGURATIONS = {
    "natural gas": ("natural gas", "nat. gas", "ng"),
    "propane": ("propane", "l.p.", "lp", "lpg"),
    "analog": ("analog",),
    "digital": ("digital",),
    "built-in": ("built-in", "builtin"),
    "portable": ("portable",),
    "patio post": ("patio post", "patio_post"),
    "in-ground post": ("in-ground post", "in_ground_post"),
    "cart": ("cart", "cart mount", "cart_mount"),
    "see-through glass": ("see-through glass", "see thru glass", "see_thru_glass"),
    "see-through": ("see-through", "see thru", "see_thru"),
    "glass": ("glass",),
    "standard": ("standard",),
    "multi-user": ("multi-user", "multi user", "multi_user"),
    "t-series": ("t-series", "t series", "t_series"),
    "l-series": ("l-series", "l series", "l_series"),
    "ansi": ("ansi",),
}
_CONFIGURATION_DIMENSIONS = {
    "natural gas": "fuel",
    "propane": "fuel",
    "analog": "interaction_interface",
    "digital": "interaction_interface",
    "built-in": "installation",
    "portable": "installation",
    "patio post": "installation",
    "in-ground post": "installation",
    "cart": "installation",
    "see-through glass": "variant",
    "see-through": "variant",
    "glass": "variant",
    "standard": "variant",
    "multi-user": "variant",
    "t-series": "variant",
    "l-series": "variant",
    "ansi": "certification",
}
_PATH_EXCLUSIONS = {
    "om", "qsg", "cad", "ss", "spec", "catalog", "standard", "listed", "ansi",
    "builtin", "portable", "patio_post", "in_ground_post", "countertop", "analog",
    "digital", "multi_user", "gourmet", "classic", "magnum", "lpg", "ng", "lp",
}


class OwnerMatchState(StrEnum):
    EXACT = "EXACT"
    COMPATIBLE = "COMPATIBLE"
    FAMILY_ONLY = "FAMILY_ONLY"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"


def normalize_model(value: str) -> str:
    """Conservative punctuation normalization; no semantic alias expansion."""
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _contains_normalized_phrase(text: str, phrase: str) -> bool:
    """Match configuration phrases on normalized token boundaries."""
    boundary_text = re.sub(r"[^a-z0-9]+", " ", normalize(text)).strip()
    boundary_phrase = re.sub(r"[^a-z0-9]+", " ", normalize(phrase)).strip()
    return bool(boundary_phrase) and f" {boundary_phrase} " in f" {boundary_text} "


def _looks_like_model(value: str, *, allow_numeric_hyphen: bool = False) -> bool:
    cleaned = value.strip(" .,:;()[]{}")
    compact = normalize_model(cleaned)
    return (
        3 <= len(compact) <= 32
        and (
            any(character.isalpha() for character in compact)
            or (allow_numeric_hyphen and ("-" in cleaned or re.fullmatch(r"\d{4,6}", compact)))
        )
        and any(character.isdigit() for character in compact)
        and not _YEAR.fullmatch(compact)
        and not compact.startswith("column")
        and not re.fullmatch(r"\d+(?:hour|hours)", compact)
        and not re.fullmatch(r"(?:page|fig|figure|table)\d+", compact)
    )


def _model_literals(text: str) -> list[str]:
    values: list[str] = []
    for token in extract_technical_tokens(text):
        token = str(token).strip()
        if _looks_like_model(token):
            values.append(token)
    for value in re.findall(r"\b[A-Za-z]{1,8}[A-Za-z0-9]*(?:[-_/][A-Za-z0-9*()]+)+\b|\b[A-Za-z]{1,8}\d[A-Za-z0-9-]*\b|\b\d{2,}(?:-[A-Za-z0-9]+)+\b|\b\d{4,6}[A-Za-z]?\b", text):
        if _looks_like_model(value, allow_numeric_hyphen=True):
            values.append(value)
    return list(dict.fromkeys(values))


@dataclass(frozen=True)
class IdentityLiteral:
    canonical: str
    normalized: str
    source_literal: str
    source: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ConfigurationIdentityLiteral:
    dimension: str
    canonical: str
    normalized: str
    source_literal: str
    source: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class DocumentOwnerIdentity:
    document_id: str
    relative_path: str
    manufacturer: str | None
    product_family: str | None
    series: str | None
    canonical_models: list[str]
    model_aliases: list[IdentityLiteral]
    part_numbers: list[str]
    year: str | None
    configurations: list[str]
    configuration_aliases: list[ConfigurationIdentityLiteral]
    identity_sources: list[str]

    @property
    def normalized_models(self) -> set[str]:
        return {value.normalized for value in self.model_aliases}

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["model_aliases"] = [row.to_dict() for row in self.model_aliases]
        value["configuration_aliases"] = [row.to_dict() for row in self.configuration_aliases]
        return value


@dataclass(frozen=True)
class OwnerResolution:
    state: str
    document_ids: list[str]
    query_models: list[str]
    matched_models: list[str]
    query_manufacturer: str | None
    query_series: str | None
    query_year: str | None
    query_configurations: list[str]
    basis: str
    candidate_states: dict[str, str]
    alias_match: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_owner_identities(graph: DocumentGraph) -> list[DocumentOwnerIdentity]:
    output: list[DocumentOwnerIdentity] = []
    for document_id in graph.document_ids:
        document = graph.nodes[document_id]
        path = document.relative_path.replace("\\", "/")
        parts = path.split("/")
        literals: list[IdentityLiteral] = []
        configuration_literals: list[ConfigurationIdentityLiteral] = []
        seen: set[tuple[str, str]] = set()
        seen_configurations: set[tuple[str, str, str]] = set()

        def add(source: str, values: Iterable[str], *, allow_numeric_hyphen: bool = False) -> None:
            for raw in values:
                literal = str(raw).strip(" .,:;")
                normalized = normalize_model(literal)
                key = (normalized, source)
                if not _looks_like_model(literal, allow_numeric_hyphen=allow_numeric_hyphen) or key in seen:
                    continue
                seen.add(key)
                literals.append(IdentityLiteral(literal, normalized, literal, source))

        def add_configurations(source: str, text: str) -> None:
            matched: list[tuple[str, str]] = []
            for canonical, forms in _CONFIGURATIONS.items():
                for form in forms:
                    if not _contains_normalized_phrase(text, form):
                        continue
                    matched.append((canonical, form))
                    break
            selected: list[tuple[str, str]] = []
            for dimension in sorted({_CONFIGURATION_DIMENSIONS[canonical] for canonical, _ in matched}):
                rows = [(canonical, form) for canonical, form in matched if _CONFIGURATION_DIMENSIONS[canonical] == dimension]
                if dimension in {"interaction_interface", "installation", "variant"}:
                    rows = [max(rows, key=lambda row: len(normalize_model(row[1])))]
                selected.extend(rows)
            for canonical, form in selected:
                key = (_CONFIGURATION_DIMENSIONS[canonical], canonical, source)
                if key in seen_configurations:
                    continue
                seen_configurations.add(key)
                configuration_literals.append(ConfigurationIdentityLiteral(
                    dimension=_CONFIGURATION_DIMENSIONS[canonical],
                    canonical=canonical,
                    normalized=normalize_model(canonical),
                    source_literal=form,
                    source=source,
                ))

        for part in parts[:-1]:
            if part.casefold() not in _PATH_EXCLUSIONS and not _YEAR.fullmatch(part):
                add("PATH", re.split(r"__|_", part), allow_numeric_hyphen=True)
        add("FILENAME", re.split(r"__|_", parts[-1].rsplit(".", 1)[0]), allow_numeric_hyphen=True)
        add_configurations("PATH", path)
        add_configurations("FILENAME", parts[-1].rsplit(".", 1)[0])
        metadata_models = document.product_identity.get("model") or []
        add("EXISTING_METADATA", metadata_models if isinstance(metadata_models, list) else [str(metadata_models)])

        nodes = sorted((node for node in graph.nodes.values() if node.document_id == document_id), key=lambda node: (node.page_number or 0, node.reading_order, node.node_id))
        cover_nodes = [node for node in nodes if node.page_number == 1 and node.node_type not in {NodeType.PAGE, NodeType.TABLE_CELL, NodeType.PROCEDURE_STEP}]
        for node in cover_nodes:
            add_configurations("COVER_MODEL_DECLARATION", node.source_text)
            for match in _MODEL_DECLARATION.findall(node.source_text):
                add("COVER_MODEL_DECLARATION", _model_literals(match))
        for node in nodes:
            if node.node_type == NodeType.TABLE_ROW and re.match(r"(?is)^\s*model\s*[:#|]", node.source_text):
                add("MODEL_TABLE", _model_literals(node.source_text))
                add_configurations("MODEL_TABLE", node.source_text)
            elif node.node_type == NodeType.TABLE_ROW and re.search(r"(?i)\b(?:natural gas|propane gas|nat\.|l\.p\.)\b", node.source_text) and _model_literals(node.source_text):
                add_configurations("MODEL_TABLE", node.source_text)
            if node.node_type == NodeType.SECTION and node.page_number and node.page_number <= 2:
                add("TITLE", _model_literals(node.source_text))
                add_configurations("TITLE", node.source_text)

        # One normalized identity can have multiple source literals; retain all provenance.
        canonical_by_normalized: dict[str, str] = {}
        for row in literals:
            canonical_by_normalized.setdefault(row.normalized, row.canonical)
        configurations = [name for name, forms in _CONFIGURATIONS.items() if any(_contains_normalized_phrase(path, form) for form in forms)]
        year = str(document.product_identity.get("year") or next((part for part in parts if _YEAR.fullmatch(part)), "")) or None
        output.append(DocumentOwnerIdentity(
            document_id=document_id,
            relative_path=path,
            manufacturer=str(document.product_identity.get("manufacturer") or parts[0] or "") or None,
            product_family=str(document.product_identity.get("product") or (parts[2] if len(parts) > 2 else "") or "") or None,
            series=str(document.product_identity.get("series") or (parts[3] if len(parts) > 3 else "") or "") or None,
            canonical_models=sorted(canonical_by_normalized.values(), key=lambda value: (normalize_model(value), value)),
            model_aliases=sorted(literals, key=lambda value: (value.normalized, value.source, value.source_literal)),
            part_numbers=[],
            year=year,
            configurations=configurations,
            configuration_aliases=sorted(configuration_literals, key=lambda value: (value.dimension, value.normalized, value.source, value.source_literal)),
            identity_sources=sorted({value.source for value in literals}),
        ))
    return sorted(output, key=lambda value: value.relative_path)


class DocumentOwnerAuthority:
    def __init__(self, identities: list[DocumentOwnerIdentity]) -> None:
        self.identities = identities
        self.by_id = {value.document_id: value for value in identities}
        self.by_path = {value.relative_path: value for value in identities}
        self.alias_index: dict[str, set[str]] = {}
        for identity in identities:
            for alias in identity.normalized_models:
                self.alias_index.setdefault(alias, set()).add(identity.document_id)
        self.manufacturers = sorted({normalize(value.manufacturer or "") for value in identities if value.manufacturer}, key=len, reverse=True)
        self.series = sorted({normalize(value.series or "") for value in identities if value.series}, key=len, reverse=True)

    def resolve(self, query: str, runtime_context: dict[str, Any] | None = None) -> OwnerResolution:
        context = runtime_context or {}
        active_document = str(context.get("active_document") or "").replace("\\", "/")
        if active_document in self.by_path:
            identity = self.by_path[active_document]
            states = {value.document_id: (OwnerMatchState.EXACT.value if value.document_id == identity.document_id else OwnerMatchState.CONFLICT.value) for value in self.identities}
            return OwnerResolution(OwnerMatchState.EXACT.value, [identity.document_id], [], [], identity.manufacturer, identity.series, identity.year, identity.configurations, "ACTIVE_DOCUMENT", states, False)

        query_normalized = normalize(query)
        query_tokens = _model_literals(query)
        query_aliases = {normalize_model(value) for value in query_tokens}
        recognized = sorted(query_aliases.intersection(self.alias_index))
        model_documents = set().union(*(self.alias_index[value] for value in recognized)) if recognized else set()
        years = re.findall(r"\b(?:19|20)\d{2}\b", query)
        query_year = years[0] if len(set(years)) == 1 else None
        query_configs = [name for name, forms in _CONFIGURATIONS.items() if any(_contains_normalized_phrase(query, form) for form in forms)]
        query_manufacturer = next((value for value in self.manufacturers if value and _contains_normalized_phrase(query, value)), None)
        query_series = next((value for value in self.series if value and _contains_normalized_phrase(query, value)), None)
        states: dict[str, str] = {}
        selected: list[str] = []
        compatible: list[str] = []
        for identity in self.identities:
            if recognized:
                if identity.document_id not in model_documents:
                    state = OwnerMatchState.CONFLICT
                elif query_year and identity.year and identity.year != query_year:
                    state = OwnerMatchState.CONFLICT
                elif query_configs and identity.configurations and not set(query_configs).intersection(identity.configurations):
                    state = OwnerMatchState.CONFLICT
                else:
                    state = OwnerMatchState.EXACT
                    selected.append(identity.document_id)
            else:
                manufacturer_match = bool(query_manufacturer and query_manufacturer == normalize(identity.manufacturer or ""))
                series_match = bool(query_series and query_series == normalize(identity.series or ""))
                if query_year and identity.year and query_year != identity.year and (manufacturer_match or series_match):
                    state = OwnerMatchState.CONFLICT
                elif query_configs and identity.configurations and not set(query_configs).intersection(identity.configurations) and (manufacturer_match or series_match):
                    state = OwnerMatchState.CONFLICT
                elif (manufacturer_match or series_match) and (
                    (query_year and identity.year == query_year)
                    or (query_configs and bool(set(query_configs).intersection(identity.configurations)))
                ):
                    state = OwnerMatchState.COMPATIBLE
                    compatible.append(identity.document_id)
                elif series_match or manufacturer_match:
                    state = OwnerMatchState.FAMILY_ONLY
                else:
                    state = OwnerMatchState.UNKNOWN
            states[identity.document_id] = state.value
        if selected:
            state = OwnerMatchState.EXACT.value
            basis = "EXACT_OR_NORMALIZED_SOURCE_MODEL"
        elif recognized:
            if compatible:
                state = OwnerMatchState.COMPATIBLE.value
                selected = compatible
                basis = "EXACT_MODEL_WITH_INCOMPLETE_QUALIFIER_METADATA"
            else:
                state = OwnerMatchState.CONFLICT.value
                basis = "MODEL_MATCH_REJECTED_BY_YEAR_OR_CONFIGURATION"
        elif compatible:
            state = OwnerMatchState.COMPATIBLE.value
            selected = compatible
            basis = "EXPLICIT_CONFIGURATION_OR_YEAR_COMPATIBLE"
        elif any(value == OwnerMatchState.FAMILY_ONLY.value for value in states.values()):
            state = OwnerMatchState.FAMILY_ONLY.value
            basis = "FAMILY_OR_MANUFACTURER_ONLY"
        else:
            state = OwnerMatchState.UNKNOWN.value
            basis = "NO_SOURCE_DERIVED_OWNER_SIGNAL"
        alias_match = any(normalize_model(value) in recognized and value.casefold() not in {row.source_literal.casefold() for identity in self.identities if identity.document_id in selected for row in identity.model_aliases} for value in query_tokens)
        return OwnerResolution(state, sorted(selected), query_tokens, recognized, query_manufacturer, query_series, query_year, query_configs, basis, states, alias_match)
