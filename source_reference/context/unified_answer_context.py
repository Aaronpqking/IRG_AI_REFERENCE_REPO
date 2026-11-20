from __future__ import annotations

from dataclasses import dataclass, replace
import json
from typing import Any, Mapping

from src.context_serialization import (
    context_serialization_identity,
    serialize_context_v1,
)
from src.conversation_history import BoundedConversation
from src.corpus_neighbors import CorpusExpansionResult
from src.evidence_reconciliation import build_context_reconciliation
from src.models import Chunk, structured_table_to_record
from src.table_evidence import render_structured_tables
from src.product_applicability import ProductApplicabilityContext, product_context_text
from src.retrieval import RankedChunk
from src.runtime_contracts import (
    CONTEXT_PACKET_VERSION,
    CanonicalRequest,
    ModelContextPacket,
)
from src.response_modes import ResponseDecision


@dataclass(frozen=True)
class AssembledAnswerContext:
    question: str
    chunks: tuple[Chunk, ...]
    diagnostics: dict[str, Any]
    packet: ModelContextPacket | None = None


@dataclass(frozen=True)
class ProductOwnedAnswerContext:
    request_index: int
    product_ref_id: str | None
    literal_reference: str
    normalized_identifiers: tuple[str, ...]
    resolution_status: str
    assembled: AssembledAnswerContext
    requested_topics: tuple[str, ...] = ()


def assemble_product_owned_contexts(
    question: str,
    groups: tuple[ProductOwnedAnswerContext, ...],
    *,
    conversation: BoundedConversation | None = None,
    max_total_chars: int = 18000,
    deduplicate_shared_pdf: bool = True,
) -> AssembledAnswerContext:
    """Combine independently evaluated product contexts under one global cap."""

    owned_chunks: list[tuple[Chunk, tuple[ProductOwnedAnswerContext, ...]]] = []
    shared_pdf: dict[tuple[str, int, int], int] = {}
    for group in groups:
        for chunk in group.assembled.chunks:
            if deduplicate_shared_pdf and chunk.content_type == "technical_evidence":
                key = (
                    str(
                        chunk.document_id
                        or chunk.relative_path
                        or chunk.filename
                        or "unknown"
                    ),
                    chunk.page_start,
                    chunk.page_end,
                )
                existing = shared_pdf.get(key)
                if existing is not None:
                    base, owners = owned_chunks[existing]
                    owned_chunks[existing] = (base, (*owners, group))
                    continue
                shared_pdf[key] = len(owned_chunks)
            owned_chunks.append((chunk, (group,)))

    requested_topics = tuple(
        topic
        for group in groups
        for topic in group.requested_topics
        if topic
    )
    scope_chunk = _request_scope_chunk(requested_topics)
    bounded: list[Chunk] = [scope_chunk] if scope_chunk is not None else []
    total = len(scope_chunk.text) if scope_chunk is not None else 0
    omitted: list[str] = []
    for chunk, owners in owned_chunks:
        prefix = _product_owner_heading(owners)
        owned = replace(
            chunk,
            chunk_id=(
                f"requested-product-{owners[0].request_index + 1}:"
                f"{chunk.chunk_id}"
            ),
            text=f"{prefix}\n\n{chunk.text}",
        )
        next_total = total + len(owned.text)
        if max_total_chars > 0 and next_total > max_total_chars:
            omitted.append(owned.chunk_id)
            continue
        bounded.append(owned)
        total = next_total

    serialized = serialize_model_context(
        question,
        tuple(bounded),
        conversation=conversation,
    )
    source_index: list[Mapping[str, Any]] = []
    seen_sources: set[str] = set()
    for group in groups:
        packet = group.assembled.packet
        for source in packet.source_index if packet is not None else ():
            key = json.dumps(source, sort_keys=True, default=str)
            if key not in seen_sources:
                source_index.append(source)
                seen_sources.add(key)
    response_class = _combined_response_class(groups)
    diagnostics = {
        "context_packet_version": CONTEXT_PACKET_VERSION,
        "question": question,
        "requested_product_groups": [
            {
                "request_index": group.request_index,
                "product_ref_id": group.product_ref_id,
                "literal_reference": group.literal_reference,
                "normalized_identifiers": list(
                    group.normalized_identifiers
                ),
                "resolution_status": group.resolution_status,
                "requested_topics": list(group.requested_topics),
                "ordered_chunk_ids": [
                    chunk.chunk_id for chunk in group.assembled.chunks
                ],
            }
            for group in groups
        ],
        "context_capacity_omitted_chunk_ids": omitted,
        "context_status": {
            "product_resolved": any(
                group.resolution_status not in {"NO_DB_MATCH", "NO_CANDIDATE"}
                for group in groups
            ),
            "context_truncated": bool(omitted),
            "total_characters": total,
            "estimated_tokens": estimate_tokens(serialized),
        },
        "context_notes": (
            [
                "The existing global context ceiling omitted later product-owned "
                "sections; no per-product balancing policy was applied."
            ]
            if omitted
            else []
        ),
        "model_payload": {
            "system_prompt_source": "chat_adapter_selected_artifact",
            "context_serialization": context_serialization_identity(),
            "serialized_context": serialized,
            "ordered_chunk_ids": [chunk.chunk_id for chunk in bounded],
        },
    }
    decision = ResponseDecision(
        response_class=response_class,
        response_origin="MODEL",
        diagnostic_status="PRODUCT_OWNED_EVIDENCE_GROUPS",
    )
    return AssembledAnswerContext(
        question=question,
        chunks=tuple(bounded),
        diagnostics=diagnostics,
        packet=ModelContextPacket(
            request=CanonicalRequest.from_question(question),
            chunks=tuple(bounded),
            response_decision=decision,
            source_index=tuple(source_index),
        ),
    )


def _request_scope_chunk(requested_topics: tuple[str, ...]) -> Chunk | None:
    unique: list[str] = []
    seen: set[str] = set()
    for topic in requested_topics:
        normalized = " ".join(str(topic).split())
        key = normalized.casefold()
        if normalized and key not in seen:
            unique.append(normalized)
            seen.add(key)
    if not unique:
        return None
    return Chunk(
        chunk_id="requested-topics-response-scope",
        document_id="runtime.requested_topics",
        filename="Requested Topics",
        relative_path="runtime/requested_topics",
        page_start=1,
        page_end=1,
        text=(
            "[REQUESTED TOPICS - RESPONSE SCOPE, NOT EVIDENCE]\n"
            + "\n".join(f"- {topic}" for topic in unique)
            + "\nTreat CURRENT USER QUESTION and REQUESTED TOPICS as the "
            "authoritative response scope. Evidence outside that scope remains "
            "available for necessary qualification but should not be volunteered "
            "merely because it was retrieved."
        ),
        content_type="product_context",
        chunk_kind="request_scope",
    )


def _product_owner_heading(
    owners: tuple[ProductOwnedAnswerContext, ...],
) -> str:
    if len(owners) == 1:
        owner = owners[0]
        identifiers = ", ".join(owner.normalized_identifiers) or "none"
        return (
            f"[PRODUCT {owner.product_ref_id or owner.request_index + 1}]\n"
            f"[REQUESTED PRODUCT {owner.request_index + 1}]\n"
            f"Literal reference: {owner.literal_reference}\n"
            f"Normalized identifiers: {identifiers}\n"
            f"Resolution status: {owner.resolution_status}"
        )
    return "\n".join(
        (
            "[SHARED EVIDENCE FOR REQUESTED PRODUCTS]",
            *(
                f"- PRODUCT {owner.product_ref_id or owner.request_index + 1}; "
                f"REQUESTED PRODUCT {owner.request_index + 1}: "
                f"{owner.literal_reference} ({owner.resolution_status})"
                for owner in owners
            ),
        )
    )


def _combined_response_class(
    groups: tuple[ProductOwnedAnswerContext, ...],
) -> str:
    classes = {
        group.assembled.packet.response_decision.response_class
        for group in groups
        if group.assembled.packet is not None
    }
    for value in ("CLARIFICATION_REQUIRED", "ANSWER_QUALIFIED"):
        if value in classes:
            return value
    return "ANSWER_SUPPORTED"


def product_context_chunk(context: ProductApplicabilityContext) -> Chunk | None:
    text = product_context_text(context)
    if not text:
        return None
    return Chunk(
        chunk_id=f"product-context-{context.read_model_product_id}",
        document_id="flamy_ai_db.product_details",
        filename="Flamy Product Read Model",
        relative_path=f"database/product_details/{context.read_model_product_id}",
        page_start=1,
        page_end=1,
        text=(
            "[DATABASE EVIDENCE]\n"
            "Source class: product-database approved catalog context\n"
            f"{text}"
        ),
        content_type="product_context",
        chunk_kind="database_context",
    )


def assemble_answer_context(
    question: str,
    *,
    conversation: BoundedConversation | None = None,
    product_context: ProductApplicabilityContext | None,
    selected_pdf: tuple[RankedChunk, ...],
    expanded_pdf: CorpusExpansionResult | None = None,
    relationship_context: Mapping[str, Any] | None = None,
    response_packet: Mapping[str, Any] | None = None,
    max_total_chars: int = 18000,
) -> AssembledAnswerContext:
    chunks: list[Chunk] = []
    reconciliation = build_context_reconciliation(
        question,
        product_context=product_context,
        selected_pdf=selected_pdf,
        response_packet=response_packet,
    )
    packet_payload = dict(response_packet or {})
    packet_payload["evidence_reconciliation"] = reconciliation
    diagnostics: dict[str, Any] = {
        "context_packet_version": CONTEXT_PACKET_VERSION,
        "question": question,
        "product_context": _product_context_schema(product_context),
        "relationship_applicability": dict(relationship_context or {}),
        "technical_evidence": [],
        "context_notes": [],
        "context_capacity_omitted_chunk_ids": [],
        "context_status": {
            "product_resolved": product_context is not None,
            "context_truncated": False,
            "total_characters": 0,
            "estimated_tokens": 0,
        },
        "response_packet": packet_payload,
        "evidence_reconciliation": reconciliation,
    }
    packet_chunk = _response_packet_chunk(packet_payload)
    if packet_chunk is not None:
        chunks.append(packet_chunk)
    product_chunk = product_context_chunk(product_context) if product_context else None
    if product_chunk is not None:
        chunks.append(product_chunk)
    relationship_chunk = _relationship_context_chunk(relationship_context)
    if relationship_chunk is not None:
        chunks.append(relationship_chunk)
    evidence_chunks = _technical_evidence_chunks(selected_pdf, expanded_pdf)
    chunks.extend(evidence_chunks)

    # Preserve direct answer evidence before relationship context. Oversized
    # sections are skipped without rewriting source text.
    high_priority = [chunk for chunk in (packet_chunk, product_chunk) if chunk]
    lower_priority = [
        chunk for chunk in (relationship_chunk,) if chunk
    ]
    bounded: list[Chunk] = []
    total = 0
    reserve = len(evidence_chunks[0].text or "") if evidence_chunks else 0
    for chunk in high_priority:
        remaining_after = max_total_chars - total - reserve
        if max_total_chars > 0 and len(chunk.text or "") > max(0, remaining_after):
            diagnostics["context_status"]["context_truncated"] = True
            diagnostics["context_notes"].append(
                f"Skipped {chunk.chunk_id} to preserve direct answer evidence."
            )
            continue
        bounded.append(chunk)
        total += len(chunk.text or "")
    for chunk in evidence_chunks:
        next_total = total + len(chunk.text or "")
        if max_total_chars > 0 and next_total > max_total_chars:
            diagnostics["context_status"]["context_truncated"] = True
            diagnostics["context_notes"].append(
                f"Omitted {chunk.chunk_id}; its original evidence text exceeded "
                "the remaining context budget."
            )
            diagnostics["context_capacity_omitted_chunk_ids"].append(
                chunk.chunk_id
            )
            continue
        bounded.append(chunk)
        total = next_total
        reserve = 0
    for chunk in lower_priority:
        next_total = total + len(chunk.text or "")
        if max_total_chars > 0 and next_total > max_total_chars:
            diagnostics["context_status"]["context_truncated"] = True
            diagnostics["context_notes"].append(
                f"Skipped lower-priority context section {chunk.chunk_id}."
            )
            continue
        bounded.append(chunk)
        total = next_total
    diagnostics["technical_evidence"] = [_technical_block_schema(chunk) for chunk in bounded if chunk.content_type == "technical_evidence"]
    diagnostics["claim_source_provenance"] = _claim_source_provenance(
        product_context,
        tuple(chunk for chunk in bounded if chunk.content_type == "technical_evidence"),
    )
    diagnostics["context_status"]["total_characters"] = total
    serialized_model_context = serialize_model_context(
        question,
        tuple(bounded),
        conversation=conversation,
    )
    diagnostics["context_status"]["estimated_tokens"] = estimate_tokens(
        serialized_model_context
    )
    diagnostics["model_payload"] = {
        "system_prompt_source": "chat_adapter_selected_artifact",
        "context_serialization": context_serialization_identity(),
        "serialized_context": serialized_model_context,
        "ordered_chunk_ids": [chunk.chunk_id for chunk in bounded],
    }
    decision = ResponseDecision(
        response_class=str(
            (response_packet or {}).get("response_class") or "ANSWER_SUPPORTED"
        ),
        response_origin=str(
            (response_packet or {}).get("response_origin") or "MODEL"
        ),
        diagnostic_status=str(
            (response_packet or {}).get("evidence_status") or "UNKNOWN"
        ),
    )
    packet = ModelContextPacket(
        request=CanonicalRequest.from_question(question),
        chunks=tuple(bounded),
        response_decision=decision,
        source_index=tuple(diagnostics["claim_source_provenance"]),
    )
    return AssembledAnswerContext(
        question=question,
        chunks=tuple(bounded),
        diagnostics=diagnostics,
        packet=packet,
    )


def _response_packet_chunk(packet: Mapping[str, Any] | None) -> Chunk | None:
    if not packet:
        return None
    database = {
        "resolved_product": packet.get("resolved_product"),
        "candidate_products": packet.get("candidate_products") or [],
        "candidate_resolution": packet.get("candidate_resolution"),
        "detected_identifiers": packet.get("detected_identifiers") or [],
    }
    pdf = {
        "evidence_status": packet.get("evidence_status"),
        "sources": packet.get("pdf_sources") or [],
        "missing_evidence": packet.get("missing_evidence") or [],
        "known_conflicts": packet.get("known_conflicts") or [],
    }
    policy = {
        "product_role_or_applicability": packet.get(
            "product_role_or_applicability"
        ),
        "constraints": packet.get("policy_constraints") or [],
        "evidence_reconciliation": packet.get("evidence_reconciliation") or {},
    }
    text = "\n\n".join(
        (
            "[DATABASE EVIDENCE]\n"
            + json.dumps(database, indent=2, sort_keys=True, default=str),
            "[PDF TECHNICAL EVIDENCE]\n"
            + json.dumps(pdf, indent=2, sort_keys=True, default=str),
            "[APPLICABILITY AND RECONCILIATION NOTES]\n"
            + json.dumps(policy, indent=2, sort_keys=True, default=str),
        )
    )
    return Chunk(
        chunk_id="runtime-response-packet",
        document_id="runtime.response_packet",
        filename="Response Packet",
        relative_path="runtime/response_packet",
        page_start=1,
        page_end=1,
        text=text,
        content_type="product_context",
        chunk_kind="evidence_packet",
    )


def _relationship_context_chunk(
    relationship: Mapping[str, Any] | None,
) -> Chunk | None:
    if not relationship:
        return None
    expected = str(relationship.get("expected_behavior") or "")
    subject = str(relationship.get("active_subject") or "")
    subject_type = str(relationship.get("subject_type") or "")
    topic = str(relationship.get("requested_topic") or "")
    owner = str(relationship.get("topic_owner_type") or "")
    missing = [
        str(item) for item in relationship.get("missing_discriminators") or []
    ]
    guidance = []
    if expected == "EXPLAIN_RELATIONSHIP":
        guidance.append(
            "State explicitly that the resolved subject is the mounting/base "
            "product and is not the grill itself."
        )
    if expected == "CLARIFY_CONFIGURATION":
        guidance.append(
            "Explain why the requested topic does not apply directly to the "
            "base, then ask for every listed missing discriminator."
        )
    lines = [
        "[APPLICABILITY AND RECONCILIATION NOTES]",
        f"Resolved subject: {subject}",
        f"Subject type: {subject_type}",
        f"Requested topic: {topic}",
        f"Topic owner type: {owner}",
        f"Topic directly applies: {relationship.get('topic_directly_applies')}",
        f"Related product required: {relationship.get('related_product_required')}",
        f"Missing discriminators: {', '.join(missing) if missing else 'none'}",
        f"Expected behavior: {expected}",
    ]
    if guidance:
        lines.append("Answer guidance: " + " ".join(guidance))
    return Chunk(
        chunk_id="relationship-applicability-guidance",
        document_id="runtime.relationship_applicability",
        filename="Relationship Applicability",
        relative_path="runtime/relationship_applicability",
        page_start=1,
        page_end=1,
        text="\n".join(lines),
        content_type="product_context",
        chunk_kind="relationship_context",
    )


def serialize_model_context(
    question: str,
    context: tuple[Chunk, ...],
    *,
    conversation: BoundedConversation | None = None,
) -> str:
    return serialize_context_v1(
        question,
        context,
        conversation=conversation,
    )


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4) if text else 0


def _technical_evidence_chunks(
    selected_pdf: tuple[RankedChunk, ...],
    expanded_pdf: CorpusExpansionResult | None,
) -> tuple[Chunk, ...]:
    if not selected_pdf:
        return ()
    selected_by_doc: dict[str, list[RankedChunk]] = {}
    for ranked in selected_pdf:
        selected_by_doc.setdefault(_document_key(ranked.chunk), []).append(ranked)
    expanded_chunks = expanded_pdf.chunks if expanded_pdf else tuple(item.chunk for item in selected_pdf)
    expanded_by_doc: dict[str, list[Chunk]] = {}
    for chunk in expanded_chunks:
        expanded_by_doc.setdefault(_document_key(chunk), []).append(chunk)
    blocks = []
    for doc_key, anchors in selected_by_doc.items():
        source_chunks = sorted(expanded_by_doc.get(doc_key, [item.chunk for item in anchors]), key=_chunk_order)
        if not source_chunks:
            continue
        selected_ids = [item.chunk.chunk_id for item in anchors]
        expanded_ids = [chunk.chunk_id for chunk in source_chunks]
        page_start = min(chunk.page_start for chunk in source_chunks)
        page_end = max(chunk.page_end for chunk in source_chunks)
        first = source_chunks[0]
        reasons = (expanded_pdf.diagnostics.get("expansion_reasons") if expanded_pdf else {}) or {}
        text_blocks = []
        for chunk in source_chunks:
            block = f"[chunk {chunk.chunk_id}, page {_page_range(chunk)}]\n{chunk.text}"
            rendered_tables = render_structured_tables(chunk.structured_tables)
            if rendered_tables:
                block += f"\n\n{rendered_tables}"
            text_blocks.append(block)
        notes = _context_notes(source_chunks)
        reason_text = "; ".join(
            sorted({reason for values in reasons.values() for reason in values})
        ) or "selected evidence chunk"
        body = (
            "[TECHNICAL EVIDENCE]\n"
            "Authority type: MANUFACTURER_TECHNICAL\n"
            f"Document: {first.filename or first.document_id or 'unknown'}\n"
            f"Document ID: {first.document_id or 'unknown'}\n"
            f"Source identity: {first.relative_path or first.filename or 'unknown'}\n"
            f"Pages: {page_start}" + (f"-{page_end}" if page_end != page_start else "") + "\n"
            f"Section: {_section_label(source_chunks)}\n"
            f"Selected evidence IDs: {', '.join(selected_ids)}\n"
            f"Included context IDs: {', '.join(expanded_ids)}\n"
            f"Context scope: {reason_text}\n"
            f"Warning/caution status: {_flag_status(source_chunks, 'has_warning', 'has_caution')}\n"
            f"Table status: {_yes_no(any(chunk.has_table or chunk.structured_tables for chunk in source_chunks))}\n"
            f"Figure/diagram-reference status: {_yes_no(any(chunk.has_figure_reference or chunk.has_schematic_reference for chunk in source_chunks))}\n"
            f"Continuation status: {_yes_no(any('continued' in (chunk.text or '').casefold() for chunk in source_chunks))}\n\n"
            "Text:\n"
            + "\n\n".join(text_blocks)
        )
        if notes:
            body += "\n\nContext notes:\n" + "\n".join(f"- {note}" for note in notes)
        blocks.append(
            Chunk(
                chunk_id=selected_ids[0] if len(selected_ids) == 1 else f"technical-evidence:{doc_key}:{page_start}:{'-'.join(selected_ids)}",
                document_id=first.document_id,
                filename=first.filename,
                relative_path=first.relative_path,
                page_start=page_start,
                page_end=page_end,
                text=body,
                content_type="technical_evidence",
                chunk_kind="evidence_block",
                has_warning=any(chunk.has_warning for chunk in source_chunks),
                has_caution=any(chunk.has_caution for chunk in source_chunks),
                has_table=any(chunk.has_table or chunk.structured_tables for chunk in source_chunks),
                has_figure_reference=any(chunk.has_figure_reference for chunk in source_chunks),
                has_schematic_reference=any(chunk.has_schematic_reference for chunk in source_chunks),
                structured_tables=tuple(
                    table
                    for chunk in source_chunks
                    for table in chunk.structured_tables
                ),
            )
        )
    return tuple(blocks)


def _product_context_schema(context: ProductApplicabilityContext | None) -> dict[str, Any] | None:
    if context is None:
        return None
    approved_facts = dict(context.approved_general_facts)
    return {
        "identity": {
            "product_id": context.read_model_product_id,
            "product_name": context.product_name,
            "brand": context.brand,
            "manufacturer": context.manufacturer,
            "model": context.model,
            "mpn": context.mpn,
            "sku": context.sku,
            "upc": context.upc,
            "product_type": context.product_type,
            "series": context.series,
            "size": context.size,
            "fuel_type": context.fuel_type,
            "status": approved_facts.get("product_status"),
            "generation": context.product_generation,
            "revision": context.model_revision,
            "variant_scope": context.variant_scope,
        },
        "description": context.description,
        "category_context": list(context.categories),
        "ordered_category_paths": [
            {
                "category_ids": list(path.category_ids),
                "path": list(path.path),
                "leaf_category_id": path.leaf_category_id,
                "parent_category_id": path.parent_category_id,
                "canonical": path.canonical,
                "source_type": path.source_type,
                "store_scope": path.store_scope,
                "status": path.status,
            }
            for path in context.business_category_paths
        ],
        "category_metrics": {
            "category_context_present": bool(context.categories),
            "ordered_multi_node_path_present": any(len(path.path) > 1 for path in context.business_category_paths),
            "parent_category_ids_present": any(path.parent_category_id is not None for path in context.business_category_paths),
            "full_root_to_leaf_hierarchy_present": any(len(path.path) > 1 and path.category_ids for path in context.business_category_paths),
        },
        "filters": list(context.filters),
        "catalog_attributes": [{"name": name, "value": value} for name, value in context.attributes],
        "database_fields": [
            {"column": column, "value": value}
            for column, value in context.database_fields
        ],
        "derived_relationship_context": [
            {
                "evidence_type": item.evidence_type,
                "name": item.name,
                "value": item.value,
                "source_type": item.source_type,
                "source_reference": item.source_reference,
                "qualification": item.qualification,
            }
            for item in context.derived_relationship_context
        ],
        "explicit_product_relationships": [
            {
                "relationship_type": relationship.relationship_type,
                "subject_product_id": relationship.subject_product_id,
                "related_product_id": relationship.related_product_id,
                "related_identifier": relationship.related_identifier,
                "related_description": relationship.related_description,
                "source_type": relationship.source_type,
                "source_reference": relationship.source_reference,
                "qualification": relationship.qualification,
            }
            for relationship in context.explicit_product_relationships
        ],
        "approved_facts": [{"column": column, "value": value} for column, value in context.approved_general_facts],
        "source_references": list(
            dict.fromkeys((*context.source_paths, *context.source_filenames, *context.source_urls))
        ),
        "enrichment_omissions": [
            {"field": field, "reason": reason}
            for field, reason in context.enrichment_omissions
        ],
    }


def _technical_block_schema(chunk: Chunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "filename": chunk.filename,
        "relative_path": chunk.relative_path,
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "text": chunk.text,
        "source_class": "approved technical manual text",
        "section": _header_value(chunk.text, "Section"),
        "selected_anchor_chunk_ids": _header_list(
            chunk.text, "Selected anchor chunk IDs"
        ),
        "expanded_chunk_ids": _header_list(chunk.text, "Expanded chunk IDs"),
        "selected_because": _header_value(chunk.text, "Selected because"),
        "expanded_because": _header_value(chunk.text, "Expanded because"),
        "warning": chunk.has_warning,
        "caution": chunk.has_caution,
        "table": chunk.has_table,
        "figure_or_diagram_reference": chunk.has_figure_reference or chunk.has_schematic_reference,
        "continuation": "continued" in (chunk.text or "").casefold(),
        "limitations": _context_notes([chunk]),
        "structured_tables": [
            structured_table_to_record(table)
            for table in chunk.structured_tables
        ],
    }


def _claim_source_provenance(
    context: ProductApplicabilityContext | None,
    technical_blocks: tuple[Chunk, ...],
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    if context is not None:
        database_evidence_id = (
            f"db:product:{context.read_model_product_id}"
        )
        database_source = {
            "evidence_id": database_evidence_id,
            "source_type": "database_candidate",
            "authority_channel": "operational_product_database",
            "source_system": "Flamy Product Read Model",
            "object": "product_details",
            "product_id": context.read_model_product_id,
        }
        for column, value in context.approved_general_facts:
            claims.append(
                {
                    "claim": {"field": column, "value": value},
                    "provenance": database_source,
                }
            )
        for name, value in context.attributes:
            claims.append(
                {
                    "claim": {"field": name, "value": value},
                    "provenance": {
                        **database_source,
                        "source_class": "catalog_attribute",
                    },
                }
            )
    for chunk in technical_blocks:
        pdf_evidence_id = (
            f"pdf:{chunk.document_id or chunk.relative_path or chunk.filename}:"
            f"pages:{chunk.page_start}-{chunk.page_end}"
        )
        claims.append(
            {
                "claim": {
                    "field": "technical_manual_evidence",
                    "chunk_id": chunk.chunk_id,
                },
                "provenance": {
                    "evidence_id": pdf_evidence_id,
                    "source_type": "pdf",
                    "authority_channel": "approved_technical_document",
                    "document_id": chunk.document_id,
                    "filename": chunk.filename,
                    "relative_path": chunk.relative_path,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                },
            }
        )
    return claims


def _header_value(text: str, label: str) -> str | None:
    prefix = f"{label}:"
    for line in (text or "").splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip() or None
    return None


def _header_list(text: str, label: str) -> list[str]:
    value = _header_value(text, label)
    return [item.strip() for item in value.split(",") if item.strip()] if value else []


def _context_notes(chunks: list[Chunk]) -> list[str]:
    notes = []
    if any(chunk.has_warning for chunk in chunks):
        notes.append("Warning included.")
    if any(chunk.has_caution for chunk in chunks):
        notes.append("Caution included.")
    if any(chunk.has_figure_reference or chunk.has_schematic_reference for chunk in chunks):
        notes.append("Figure or diagram is referenced but unavailable in extracted text.")
    tables = [table for chunk in chunks for table in chunk.structured_tables]
    if any(table.structure_status == "structured" for table in tables):
        notes.append("Structured table header and cell ownership is included.")
    if any(table.structure_status == "ambiguous" for table in tables):
        notes.append("Ambiguous table cells are source-preserved without inferred ownership.")
    if any(chunk.has_table for chunk in chunks) and not tables:
        notes.append("Table text is included as extracted; table structure may be incomplete.")
    return notes


def _section_label(chunks: list[Chunk]) -> str:
    values = [chunk.section_path or chunk.section_title for chunk in chunks if chunk.section_path or chunk.section_title]
    return values[0] if values else "unknown"


def _flag_status(chunks: list[Chunk], *fields: str) -> str:
    return _yes_no(any(bool(getattr(chunk, field)) for chunk in chunks for field in fields))


def _yes_no(value: bool) -> str:
    return "present" if value else "not present"


def _page_range(chunk: Chunk) -> str:
    return str(chunk.page_start) if chunk.page_end == chunk.page_start else f"{chunk.page_start}-{chunk.page_end}"


def _document_key(chunk: Chunk) -> str:
    return chunk.document_id or chunk.relative_path or chunk.filename or "unknown"


def _chunk_order(chunk: Chunk) -> tuple[str, int, int, str]:
    return (_document_key(chunk), chunk.page_start, chunk.chunk_index, chunk.chunk_id)
