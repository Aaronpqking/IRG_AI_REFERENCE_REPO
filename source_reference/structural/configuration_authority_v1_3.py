from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from .owner_identity import (
    DocumentOwnerAuthority,
    DocumentOwnerIdentity,
    OwnerMatchState,
    OwnerResolution,
    _CONFIGURATIONS,
    _CONFIGURATION_DIMENSIONS,
    _contains_normalized_phrase,
)


class ConfigurationMatchState(StrEnum):
    EXACT = "CONFIG_EXACT"
    COMPATIBLE = "CONFIG_COMPATIBLE"
    UNKNOWN = "CONFIG_UNKNOWN"
    CONFLICT = "CONFIG_CONFLICT"


@dataclass(frozen=True)
class ConfigurationResolution:
    state: str
    query_values: dict[str, list[str]]
    candidate_states: dict[str, str]
    candidate_dimensions: dict[str, dict[str, list[str]]]
    basis: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CombinedOwnerResolution:
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
    model_resolution: dict[str, Any]
    configuration_resolution: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def query_configuration_values(query: str) -> dict[str, list[str]]:
    matched: dict[str, list[tuple[str, str]]] = {}
    for canonical, forms in _CONFIGURATIONS.items():
        form = next((value for value in forms if _contains_normalized_phrase(query, value)), None)
        if canonical == "glass" and _contains_normalized_phrase(query, "glass doors"):
            form = None
        if form:
            matched.setdefault(_CONFIGURATION_DIMENSIONS[canonical], []).append((canonical, form))
    values: dict[str, list[str]] = {}
    for dimension, rows in matched.items():
        if dimension in {"interaction_interface", "installation", "variant"}:
            rows = [max(rows, key=lambda row: len(row[1]))]
        values[dimension] = [canonical for canonical, _ in rows]
    return {key: sorted(set(rows)) for key, rows in sorted(values.items())}


def identity_configuration_values(identity: DocumentOwnerIdentity) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for literal in identity.configuration_aliases:
        values.setdefault(literal.dimension, []).append(literal.canonical)
    return {key: sorted(set(rows)) for key, rows in sorted(values.items())}


class ConfigurationOwnerAuthority:
    """Keep model and configuration authority separate, then apply precedence."""

    def __init__(self, identities: list[DocumentOwnerIdentity]) -> None:
        self.model_authority = DocumentOwnerAuthority(identities)
        self.identities = identities
        self.by_id = self.model_authority.by_id
        self.by_path = self.model_authority.by_path

    def resolve_configuration(self, query: str) -> ConfigurationResolution:
        query_values = query_configuration_values(query)
        candidate_states: dict[str, str] = {}
        candidate_dimensions: dict[str, dict[str, list[str]]] = {}
        for identity in self.identities:
            document_values = identity_configuration_values(identity)
            candidate_dimensions[identity.document_id] = document_values
            if not query_values:
                state = ConfigurationMatchState.UNKNOWN
            else:
                matched = 0
                missing = 0
                conflict = False
                for dimension, wanted in query_values.items():
                    available = document_values.get(dimension, [])
                    if not available:
                        missing += 1
                    elif set(wanted).intersection(available):
                        matched += 1
                    else:
                        conflict = True
                        break
                if conflict:
                    state = ConfigurationMatchState.CONFLICT
                elif matched and not missing:
                    state = ConfigurationMatchState.EXACT
                elif matched:
                    state = ConfigurationMatchState.COMPATIBLE
                else:
                    state = ConfigurationMatchState.UNKNOWN
            candidate_states[identity.document_id] = state.value
        states = set(candidate_states.values())
        overall = (
            ConfigurationMatchState.EXACT.value if ConfigurationMatchState.EXACT.value in states
            else ConfigurationMatchState.COMPATIBLE.value if ConfigurationMatchState.COMPATIBLE.value in states
            else ConfigurationMatchState.UNKNOWN.value
        )
        return ConfigurationResolution(overall, query_values, candidate_states, candidate_dimensions, "SOURCE_DERIVED_CONFIGURATION_DIMENSIONS")

    def resolve(self, query: str, runtime_context: dict[str, Any] | None = None) -> CombinedOwnerResolution:
        model = self.model_authority.resolve(query, runtime_context)
        configuration = self.resolve_configuration(query)
        active = model.basis == "ACTIVE_DOCUMENT"
        exact_model_documents: set[str] = set()
        if model.matched_models:
            exact_model_documents = set().union(*(self.model_authority.alias_index[value] for value in model.matched_models))
            exact_model_documents = {
                document_id for document_id in exact_model_documents
                if not model.query_year or not self.by_id[document_id].year or self.by_id[document_id].year == model.query_year
            }
        selected: list[str] = []
        combined_states: dict[str, str] = {}
        for document_id, model_state in model.candidate_states.items():
            effective_model_state = OwnerMatchState.EXACT.value if document_id in exact_model_documents else model_state
            config_state = configuration.candidate_states.get(document_id, ConfigurationMatchState.UNKNOWN.value)
            if active:
                combined = effective_model_state
            elif effective_model_state == OwnerMatchState.CONFLICT.value or config_state == ConfigurationMatchState.CONFLICT.value:
                combined = OwnerMatchState.CONFLICT.value
            else:
                combined = effective_model_state
            combined_states[document_id] = combined
        hypotheses = model.document_ids
        if not active and exact_model_documents:
            hypotheses = sorted(exact_model_documents)
        if not hypotheses and model.state in {OwnerMatchState.COMPATIBLE.value, OwnerMatchState.FAMILY_ONLY.value}:
            hypotheses = [
                document_id for document_id, state in model.candidate_states.items()
                if state in {OwnerMatchState.COMPATIBLE.value, OwnerMatchState.FAMILY_ONLY.value}
            ]
        non_conflicting = [document_id for document_id in hypotheses if configuration.candidate_states.get(document_id) != ConfigurationMatchState.CONFLICT.value]
        if active:
            selected = hypotheses
        elif non_conflicting:
            exact_config = [document_id for document_id in non_conflicting if configuration.candidate_states.get(document_id) == ConfigurationMatchState.EXACT.value]
            compatible_config = [document_id for document_id in non_conflicting if configuration.candidate_states.get(document_id) == ConfigurationMatchState.COMPATIBLE.value]
            selected = exact_config or compatible_config or non_conflicting
        if selected and exact_model_documents:
            state = OwnerMatchState.EXACT.value
        elif selected and model.state == OwnerMatchState.FAMILY_ONLY.value:
            state = OwnerMatchState.COMPATIBLE.value
        else:
            state = model.state if selected else OwnerMatchState.CONFLICT.value if hypotheses else model.state
        basis = f"{model.basis}+CONFIGURATION_PRECEDENCE"
        return CombinedOwnerResolution(
            state=state,
            document_ids=sorted(selected),
            query_models=model.query_models,
            matched_models=model.matched_models,
            query_manufacturer=model.query_manufacturer,
            query_series=model.query_series,
            query_year=model.query_year,
            query_configurations=model.query_configurations,
            basis=basis,
            candidate_states=combined_states,
            alias_match=model.alias_match,
            model_resolution=model.to_dict(),
            configuration_resolution=configuration.to_dict(),
        )
