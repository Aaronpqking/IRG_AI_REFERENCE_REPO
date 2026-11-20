from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from src.conversation_history import BoundedConversation
from src.models import Chunk
from src.table_evidence import render_structured_tables


CONTEXT_SERIALIZATION_VERSION = "IRG_CONTEXT_SERIALIZATION_V1"
CONTEXT_SERIALIZATION_SCHEMA: dict[str, Any] = {
    "schema_version": "irg.model_visible_context.v1",
    "contract_version": CONTEXT_SERIALIZATION_VERSION,
    "block_order": [
        "CONVERSATION_CONTINUITY",
        "QUESTION",
        "CONTROL",
        "AUTHORITY_RESULTS",
        "TECHNICAL_EVIDENCE",
        "DYNAMIC_STATE",
        "SOURCE_IDENTITIES",
    ],
    "required_blocks": ["QUESTION"],
    "omission_rule": "omit_blocks_without_current_runtime_data",
    "conversation_authority": "NONE_CONTINUITY_ONLY",
    "control_authority": "NONE_INSTRUCTION_ONLY",
    "source_mechanics_narration": "PROHIBITED",
}
CONTEXT_SERIALIZATION_SCHEMA_SHA256 = sha256(
    json.dumps(
        CONTEXT_SERIALIZATION_SCHEMA,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()


def context_serialization_identity() -> dict[str, str]:
    return {
        "version": CONTEXT_SERIALIZATION_VERSION,
        "schema_sha256": CONTEXT_SERIALIZATION_SCHEMA_SHA256,
    }


def serialize_context_v1(
    question: str,
    context: tuple[Chunk, ...],
    *,
    conversation: BoundedConversation | None = None,
) -> str:
    """Serialize the exact model-visible V1 context without retrieval narration."""

    if not question.strip():
        raise ValueError("question is required")
    blocks: list[str] = []
    if conversation is not None and conversation.prior_turns:
        messages = [
            "[CONVERSATION CONTINUITY]",
            "Authority: NONE - continuity only",
        ]
        for turn in conversation.prior_turns:
            messages.append(f"[{turn.role.upper()}]\n{turn.content}")
        blocks.append("\n\n".join(messages))
    blocks.append(f"[QUESTION]\n{question}")
    for index, chunk in enumerate(context, 1):
        blocks.append(_serialize_chunk(chunk, index))
    return "\n\n".join(blocks)


def _serialize_chunk(chunk: Chunk, index: int) -> str:
    if chunk.chunk_kind == "canonical_authority_absence" or chunk.content_type in {
        "control",
        "evidence_absence_control",
    }:
        return (
            "[CONTROL]\n"
            "Authority: NONE - instruction only\n"
            f"Control ID: {chunk.chunk_id}\n\n"
            f"{chunk.text}"
        )
    if chunk.content_type in {"product_context", "technical_evidence"}:
        return chunk.text
    if chunk.content_type == "dynamic_state":
        source = chunk.relative_path or chunk.filename or chunk.document_id or "unknown"
        return (
            f"[DYNAMIC STATE {index}]\n"
            f"Authority type: {_authority_type(chunk)}\n"
            f"Source identity: {source}\n"
            f"Record ID: {chunk.chunk_id}\n\n"
            f"{chunk.text}"
        )
    source = chunk.relative_path or chunk.filename or chunk.document_id or "unknown"
    rendered_tables = render_structured_tables(chunk.structured_tables)
    evidence_text = chunk.text
    if rendered_tables:
        evidence_text += f"\n\n{rendered_tables}"
    return (
        f"[TECHNICAL EVIDENCE {index}]\n"
        f"Authority type: {_authority_type(chunk)}\n"
        f"Source identity: {source}\n"
        f"Document: {chunk.filename or chunk.document_id or 'unknown'}\n"
        f"Document ID: {chunk.document_id or 'unknown'}\n"
        f"Pages: {_page_range(chunk)}\n"
        f"Section: {chunk.section_path or chunk.section_title or 'unknown'}\n"
        f"Evidence ID: {chunk.chunk_id}\n"
        f"Revision year: {chunk.document_revision_year or 'unknown'}\n\n"
        f"Text:\n{evidence_text}"
    )


def _authority_type(chunk: Chunk) -> str:
    if chunk.content_type == "dynamic_state":
        return str(chunk.metadata_source or "DYNAMIC_AUTHORITY_UNSPECIFIED")
    return "MANUFACTURER_TECHNICAL"


def _page_range(chunk: Chunk) -> str:
    return (
        str(chunk.page_start)
        if chunk.page_start == chunk.page_end
        else f"{chunk.page_start}-{chunk.page_end}"
    )
