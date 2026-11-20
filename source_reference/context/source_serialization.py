from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping


PDF_SOURCE_KEYS = (
    "evidence_id",
    "type",
    "source_type",
    "authority_channel",
    "authority_scope",
    "source_id",
    "display_label",
    "filename",
    "relative_path",
    "page_start",
    "page_end",
    "page",
    "chunk_id",
    "document_id",
    "score",
    "rank",
    "product_ref_id",
    "product_display_identity",
)

DATABASE_CANDIDATE_KEYS = (
    "evidence_id",
    "type",
    "source_type",
    "authority_channel",
    "authority_scope",
    "source_id",
    "display_label",
    "source_system",
    "object",
    "product_id",
    "record_type",
    "model",
    "identifier",
    "text_preview",
    "identity_scope",
    "fields",
    "approved_general_fields",
    "source_metadata_fields",
    "authority",
    "freshness",
    "store_scope",
    "language_scope",
    "variant_scope",
    "score",
    "rank",
    "product_ref_id",
    "product_display_identity",
)


def serialize_sources(sources: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    serialized = [serialize_source(source) for source in sources]
    result: list[dict[str, Any]] = []
    pdf_by_key: dict[tuple[str, Any, Any, Any], dict[str, Any]] = {}
    database_keys: set[tuple[Any, Any, Any]] = set()
    for source in serialized:
        if source.get("source_type") == "database":
            key = (
                source.get("source_id"),
                source.get("product_ref_id"),
                None,
            )
            if key not in database_keys:
                database_keys.add(key)
                result.append(source)
            continue
        relative_path = str(
            source.get("relative_path") or source.get("filename") or ""
        ).replace("\\", "/")
        key = (
            relative_path.casefold(),
            source.get("page_start"),
            source.get("page_end"),
            source.get("product_ref_id"),
        )
        if key in pdf_by_key:
            continue
        simplified = _drop_empty(
            {
                "type": source.get("type") or "pdf",
                "source_type": "pdf",
                "evidence_id": source.get("evidence_id"),
                "authority_channel": source.get(
                    "authority_channel"
                ),
                "authority_scope": source.get("authority_scope"),
                "source_id": source.get("source_id"),
                "display_label": source.get("display_label"),
                "filename": source.get("filename"),
                "relative_path": source.get("relative_path"),
                "page_start": source.get("page_start"),
                "page_end": source.get("page_end"),
                "page": source.get("page")
                if source.get("page") is not None
                else source.get("page_start"),
                "product_ref_id": source.get("product_ref_id"),
                "product_display_identity": source.get(
                    "product_display_identity"
                ),
            },
            (
                "type",
                "source_type",
                "evidence_id",
                "authority_channel",
                "authority_scope",
                "source_id",
                "display_label",
                "filename",
                "relative_path",
                "page_start",
                "page_end",
                "page",
                "product_ref_id",
                "product_display_identity",
            ),
        )
        pdf_by_key[key] = simplified
        result.append(simplified)
    return result


def authoritative_answer_sources(
    sources: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> list[dict[str, Any]]:
    """Exclude discovery provenance from the answer-evidence channel."""

    result = []
    for source in sources:
        serialized = serialize_source(source)
        if (
            serialized.get("source_type") == "database"
            and serialized.get("authority") != "answer_evidence"
        ):
            continue
        result.append(dict(source))
    return result


def serialize_source(source: Mapping[str, Any] | Any) -> dict[str, Any]:
    raw = _as_mapping(source)
    database = _database_candidate_source(raw)
    if database is not None:
        return database
    return _pdf_source(raw)


def _as_mapping(source: Mapping[str, Any] | Any) -> dict[str, Any]:
    if is_dataclass(source):
        return asdict(source)
    if isinstance(source, Mapping):
        return dict(source)
    raise TypeError("source must be a mapping or dataclass")


def _database_candidate_source(source: dict[str, Any]) -> dict[str, Any] | None:
    payload = _database_payload(source)
    if payload is None:
        return None
    row_key = payload.get("row_key") if isinstance(payload.get("row_key"), dict) else {}
    source_system = payload.get("source_system") or "Flamy Product Read Model"
    object_name = payload.get("object") or "product_details"
    product_id = payload.get("product_id") or row_key.get("product_id")
    mapped = {
        "evidence_id": source.get("evidence_id")
        or payload.get("evidence_id")
        or (
            f"db:product:{product_id}"
            if product_id not in (None, "")
            else None
        ),
        "type": "database_candidate",
        "source_type": "database",
        "authority_channel": source.get("authority_channel")
        or payload.get("authority_channel")
        or "operational_product_database",
        "authority_scope": source.get("authority_scope")
        or payload.get("authority_scope"),
        "source_id": (
            f"{source_system}:{object_name}:{product_id}"
            if product_id not in (None, "")
            else None
        ),
        "display_label": (
            f"{source_system} product {product_id}"
            if product_id not in (None, "")
            else source_system
        ),
        "source_system": source_system,
        "object": object_name,
        "product_id": product_id,
        "record_type": payload.get("record_type") or object_name,
        "model": payload.get("model"),
        "identifier": payload.get("identifier") or payload.get("mpn") or payload.get("sku"),
        "text_preview": source.get("text_preview") or payload.get("text_preview"),
        "identity_scope": payload.get("identity_scope") or "flamy_read_model_only",
        "fields": _field_names(payload.get("fields")),
        "approved_general_fields": _field_names(payload.get("approved_general_fields")),
        "source_metadata_fields": _field_names(payload.get("source_metadata_fields")),
        "authority": payload.get("authority") or "general_product_data_or_discovery",
        "freshness": payload.get("freshness") or "unknown_or_known",
        "store_scope": payload.get("store_scope"),
        "language_scope": payload.get("language_scope"),
        "variant_scope": payload.get("variant_scope"),
        "score": source.get("score"),
        "rank": source.get("rank"),
        "product_ref_id": source.get("product_ref_id"),
        "product_display_identity": source.get("product_display_identity"),
    }
    return _drop_empty(mapped, DATABASE_CANDIDATE_KEYS)


def _database_payload(source: dict[str, Any]) -> dict[str, Any] | None:
    if (
        source.get("type") == "database_candidate"
        or source.get("source_type") in {
            "database",
            "product_db",
        }
    ):
        return source
    preview = source.get("text_preview")
    if not isinstance(preview, str) or "database_candidate" not in preview:
        return None
    try:
        payload = json.loads(preview)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("source_type") != "database_candidate":
        return None
    return payload


def _field_names(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [str(key) for key, item in value.items() if item not in (None, "", [], ())]
    if isinstance(value, list):
        names = []
        for item in value:
            if isinstance(item, dict) and item.get("column"):
                names.append(str(item["column"]))
            elif isinstance(item, str):
                names.append(item)
        return names
    return []


def _pdf_source(source: dict[str, Any]) -> dict[str, Any]:
    relative_path = str(source.get("relative_path") or "").replace("\\", "/")
    filename = source.get("filename")
    document_id = source.get("document_id")
    source_id = document_id or relative_path or filename
    mapped = {
        "evidence_id": source.get("evidence_id")
        or (
            f"pdf:{source_id}:pages:{source.get('page_start')}-{source.get('page_end')}"
            if source_id
            and source.get("page_start") is not None
            else None
        ),
        "type": source.get("type") or "pdf",
        "source_type": "pdf",
        "authority_channel": source.get("authority_channel")
        or "approved_technical_document",
        "authority_scope": source.get("authority_scope"),
        "source_id": source_id,
        "display_label": filename or relative_path or document_id,
        "filename": filename,
        "relative_path": relative_path or None,
        "page_start": source.get("page_start"),
        "page_end": source.get("page_end"),
        "page": source.get("page") if source.get("page") is not None else source.get("page_start"),
        "chunk_id": source.get("chunk_id"),
        "document_id": source.get("document_id"),
        "score": source.get("score"),
        "rank": source.get("rank"),
        "product_ref_id": source.get("product_ref_id"),
        "product_display_identity": source.get("product_display_identity"),
    }
    return _drop_empty(mapped, PDF_SOURCE_KEYS)


def _drop_empty(source: dict[str, Any], allowed_keys: tuple[str, ...]) -> dict[str, Any]:
    result = {}
    for key in allowed_keys:
        value = source.get(key)
        if value in (None, "", [], ()):
            continue
        result[key] = value
    return result
