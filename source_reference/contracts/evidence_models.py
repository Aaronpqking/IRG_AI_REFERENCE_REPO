from dataclasses import dataclass
import hashlib
from typing import Any

from src.models import Chunk
from src.query_intent import QueryIntent
from src.retrieval import RankedChunk


@dataclass(frozen=True)
class EvidenceItem:
    chunk: Chunk
    ranked: RankedChunk
    source: str
    page_start: int
    page_end: int
    inclusion_reason: str


@dataclass(frozen=True)
class EvidenceGroup:
    source: str
    pages: tuple[int, ...]
    items: tuple[EvidenceItem, ...]
    matched_identifiers: tuple[str, ...]
    score: float
    group_reason: str


@dataclass(frozen=True)
class EvidenceDecision:
    mode: str
    sufficient: bool
    confidence: str
    reason: str | None = None
    missing_fields: tuple[str, ...] = ()
    conflicting_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidencePackage:
    question: str
    intent: QueryIntent
    selected: tuple[RankedChunk, ...]
    groups: tuple[EvidenceGroup, ...]
    decision: EvidenceDecision
    diagnostics: dict[str, Any]


@dataclass(frozen=True)
class NormalizedFact:
    attribute_name: str
    attribute_key: str
    raw_value: str
    value_type: str
    unit: str | None
    minimum: float | None
    maximum: float | None
    list_values: tuple[str, ...]
    source_type: str
    source_identity: str
    product_model: str | None = None
    manufacturer: str | None = None
    configuration: str | None = None
    fuel: str | None = None
    year_version: str | None = None
    applicability: str = "unproven"
    document_type: str | None = None
    specificity: str = "summary"
    citation: str | None = None
    limitations: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "attribute_name": self.attribute_name,
            "attribute_key": self.attribute_key,
            "raw_value": self.raw_value,
            "value_type": self.value_type,
            "unit": self.unit,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "list_values": list(self.list_values),
            "source_type": self.source_type,
            "source_identity": self.source_identity,
            "product_model": self.product_model,
            "manufacturer": self.manufacturer,
            "configuration": self.configuration,
            "fuel": self.fuel,
            "year_version": self.year_version,
            "applicability": self.applicability,
            "document_type": self.document_type,
            "specificity": self.specificity,
            "citation": self.citation,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class ReconciledFact:
    attribute_key: str
    outcome: str
    preferred_value: str | None
    facts: tuple[NormalizedFact, ...]
    notes: tuple[str, ...]
    requires_qualification: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "attribute_key": self.attribute_key,
            "outcome": self.outcome,
            "preferred_value": self.preferred_value,
            "facts": [fact.as_dict() for fact in self.facts],
            "notes": list(self.notes),
            "requires_qualification": self.requires_qualification,
        }


@dataclass(frozen=True)
class CanonicalEvidenceIdentity:
    evidence_id: str
    source_type: str
    authority_channel: str
    authority_scope: tuple[str, ...]
    subject_identity: dict[str, Any]
    model_visible_content: str | None
    public_source: dict[str, Any]
    persistence_source: dict[str, Any]
    admitted_fact_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_type": self.source_type,
            "authority_channel": self.authority_channel,
            "authority_scope": list(self.authority_scope),
            "subject_identity": dict(self.subject_identity),
            "model_visible_content": self.model_visible_content,
            "public_source": dict(self.public_source),
            "persistence_source": dict(self.persistence_source),
            "admitted_fact_ids": list(self.admitted_fact_ids),
        }


def database_evidence_identity(
    candidate: Any,
    *,
    rank: int,
    admitted_fact_ids: tuple[str, ...] = (),
    model_visible_content: str | None = None,
) -> CanonicalEvidenceIdentity:
    product_id = int(candidate.product_id)
    evidence_id = f"db:product:{product_id}"
    authority_scope = tuple(
        dict.fromkeys(
            (
                "identity",
                *(
                    column
                    for column, value in (
                        getattr(candidate, "approved_general_facts", ())
                        or ()
                    )
                    if value not in (None, "")
                ),
            )
        )
    )
    persistence = dict(candidate.answer_source_ref(rank))
    persistence.update(
        {
            "evidence_id": evidence_id,
            "source_type": "product_db",
            "authority_channel": "operational_product_database",
            "authority_scope": authority_scope,
            "subject_product_id": product_id,
            "product_id": product_id,
            "source_system": "Flamy Product Read Model",
            "object": "product_details",
            "authority": "answer_evidence",
        }
    )
    if model_visible_content:
        persistence["text_preview"] = model_visible_content
    public = {
        "evidence_id": evidence_id,
        "source_type": "product_db",
        "authority_channel": "operational_product_database",
        "authority_scope": list(authority_scope),
        "label": "Flamy Product Read Model",
        "product_id": product_id,
    }
    return CanonicalEvidenceIdentity(
        evidence_id=evidence_id,
        source_type="product_db",
        authority_channel="operational_product_database",
        authority_scope=authority_scope,
        subject_identity={"product_id": product_id},
        model_visible_content=model_visible_content,
        public_source=public,
        persistence_source=persistence,
        admitted_fact_ids=tuple(dict.fromkeys(admitted_fact_ids)),
    )


def pdf_evidence_identity(
    chunk: Chunk,
    *,
    rank: int,
    score: float | None = None,
) -> CanonicalEvidenceIdentity:
    document_id = (
        chunk.document_id
        or chunk.relative_path
        or chunk.filename
        or "unknown"
    )
    evidence_id = (
        f"pdf:{document_id}:pages:{chunk.page_start}-{chunk.page_end}"
    )
    authority_scope = ("technical_documentation",)
    common = {
        "evidence_id": evidence_id,
        "source_type": "technical_pdf",
        "authority_channel": "approved_technical_document",
        "authority_scope": authority_scope,
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "filename": chunk.filename,
        "relative_path": chunk.relative_path,
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "score": score,
        "rank": rank,
    }
    persistence = {
        **common,
        "text_preview": chunk.text[:240],
        "evidence_text": chunk.text,
        "structural_evidence": _structural_evidence(chunk),
    }
    public = {
        key: value
        for key, value in common.items()
        if key
        not in {
            "chunk_id",
            "score",
            "rank",
        }
        and value not in (None, "")
    }
    return CanonicalEvidenceIdentity(
        evidence_id=evidence_id,
        source_type="technical_pdf",
        authority_channel="approved_technical_document",
        authority_scope=authority_scope,
        subject_identity={"document_id": document_id},
        model_visible_content=chunk.text,
        public_source=public,
        persistence_source=persistence,
        admitted_fact_ids=(),
    )


def _structural_evidence(chunk: Chunk) -> list[dict[str, Any]]:
    """Return stable row/cell identities for later citation verification."""

    records: list[dict[str, Any]] = []
    for table in chunk.structured_tables:
        cells_by_row: dict[int, list[Any]] = {}
        for cell in table.cells:
            cells_by_row.setdefault(cell.row_index, []).append(cell)
        for row_index, cells in sorted(cells_by_row.items()):
            if row_index < table.header_row_count:
                continue
            ordered = sorted(cells, key=lambda item: item.column_index)
            rendered_cells = []
            row_parts = []
            for cell in ordered:
                cell_id = (
                    f"{table.table_id}:cell:{cell.row_index}:"
                    f"{cell.column_index}"
                )
                header = " > ".join(cell.column_header_path)
                rendered_cells.append(
                    {
                        "cell_id": cell_id,
                        "row_index": cell.row_index,
                        "column_index": cell.column_index,
                        "role": cell.role,
                        "row_header": cell.row_header,
                        "column_header_path": list(
                            cell.column_header_path
                        ),
                        "unit": cell.unit,
                        "text": cell.text,
                    }
                )
                row_parts.append(
                    " | ".join(
                        value
                        for value in (
                            cell.row_header,
                            header,
                            cell.text,
                            cell.unit,
                        )
                        if value
                    )
                )
            evidence_text = " | ".join(
                value
                for value in (table.title, *row_parts)
                if value
            )
            records.append(
                {
                    "table_id": table.table_id,
                    "row_id": f"{table.table_id}:row:{row_index}",
                    "row_index": row_index,
                    "cell_ids": [
                        item["cell_id"] for item in rendered_cells
                    ],
                    "cells": rendered_cells,
                    "document_id": table.document_id or chunk.document_id,
                    "relative_path": (
                        table.relative_path or chunk.relative_path
                    ),
                    "page": table.page_number,
                    "structure_status": table.structure_status,
                    "evidence_text": evidence_text,
                    "evidence_text_sha256": hashlib.sha256(
                        evidence_text.encode("utf-8")
                    ).hexdigest(),
                }
            )
    return records
