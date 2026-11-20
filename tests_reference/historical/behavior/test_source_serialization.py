import json

from src import api_server
from src.source_serialization import serialize_source, serialize_sources


def database_source() -> dict[str, object]:
    payload = {
        "source_type": "database_candidate",
        "source_system": "Flamy Product Read Model",
        "object": "product_details",
        "product_id": 123,
        "identity_scope": "flamy_read_model_only",
        "fields": ["product_name", "brand", "model"],
        "approved_general_fields": ["product_name", "brand"],
        "source_metadata_fields": ["source_document"],
        "authority": "discovery_only",
        "freshness": "unknown",
        "store_scope": "unknown",
        "language_scope": "unknown",
        "variant_scope": "unknown",
    }
    return {
        "chunk_id": "product_details:123",
        "document_id": "flamy_ai_db.product_details",
        "filename": "Flamy Product Read Model",
        "relative_path": "database/product_details/123",
        "score": 91.5,
        "rank": 1,
        "text_preview": json.dumps(payload),
    }


def test_api_and_shared_serializer_return_identical_database_shape() -> None:
    source = database_source()

    assert api_server._source_for_http(source) == serialize_source(source)


def test_database_candidate_serialization_is_stable_without_http() -> None:
    mapped = serialize_source(database_source())

    assert mapped == {
        "type": "database_candidate",
        "source_type": "database",
        "evidence_id": "db:product:123",
        "authority_channel": "operational_product_database",
        "source_id": "Flamy Product Read Model:product_details:123",
        "display_label": "Flamy Product Read Model product 123",
        "source_system": "Flamy Product Read Model",
        "object": "product_details",
        "product_id": 123,
        "record_type": "product_details",
        "text_preview": database_source()["text_preview"],
        "identity_scope": "flamy_read_model_only",
        "fields": ["product_name", "brand", "model"],
        "approved_general_fields": ["product_name", "brand"],
        "source_metadata_fields": ["source_document"],
        "authority": "discovery_only",
        "freshness": "unknown",
        "store_scope": "unknown",
        "language_scope": "unknown",
        "variant_scope": "unknown",
        "score": 91.5,
        "rank": 1,
    }


def test_discriminated_database_source_does_not_require_legacy_type() -> None:
    mapped = serialize_source(
        {
            "source_type": "database",
            "source_system": "Catalog",
            "object": "product",
            "product_id": 42,
        }
    )

    assert mapped["source_type"] == "database"
    assert mapped["source_id"] == "Catalog:product:42"
    assert mapped["display_label"] == "Catalog product 42"
    assert "filename" not in mapped
    assert "relative_path" not in mapped


def test_pdf_source_shape_keeps_existing_external_fields() -> None:
    mapped = serialize_source(
        {
            "chunk_id": "chunk-1",
            "document_id": "doc-1",
            "filename": "manual.pdf",
            "relative_path": "manuals/manual.pdf",
            "page_start": 4,
            "page_end": 5,
            "score": 0.89,
            "rank": 2,
            "text_preview": "internal chunk text",
        }
    )

    assert mapped == {
        "type": "pdf",
        "source_type": "pdf",
        "evidence_id": "pdf:doc-1:pages:4-5",
        "authority_channel": "approved_technical_document",
        "source_id": "doc-1",
        "display_label": "manual.pdf",
        "filename": "manual.pdf",
        "relative_path": "manuals/manual.pdf",
        "page_start": 4,
        "page_end": 5,
        "page": 4,
        "chunk_id": "chunk-1",
        "document_id": "doc-1",
        "score": 0.89,
        "rank": 2,
    }


def test_internal_diagnostics_credentials_and_raw_sql_are_not_serialized() -> None:
    mapped = serialize_source(
        {
            "chunk_id": "chunk-1",
            "filename": "manual.pdf",
            "page_start": 1,
            "raw_sql": "SELECT secret FROM users",
            "password": "secret",
            "api_token": "token",
            "text_preview": "internal chunk text",
        }
    )

    assert "raw_sql" not in mapped
    assert "password" not in mapped
    assert "api_token" not in mapped
    assert "text_preview" not in mapped


def test_serialize_sources_maps_all_entries() -> None:
    mapped = serialize_sources([database_source(), {"chunk_id": "chunk-1", "filename": "manual.pdf"}])

    assert [source["type"] for source in mapped] == ["database_candidate", "pdf"]


def test_same_document_and_page_sources_are_deduplicated_for_users() -> None:
    mapped = serialize_sources(
        [
            {
                "chunk_id": "doc-60",
                "filename": "3282l.pdf",
                "relative_path": "side_cookers/3282l/3282l.pdf",
                "page_start": 15,
                "page_end": 15,
                "rank": 8,
            },
            {
                "chunk_id": "doc-61",
                "filename": "3282l.pdf",
                "relative_path": "side_cookers/3282l/3282l.pdf",
                "page_start": 15,
                "page_end": 15,
                "rank": 2,
            },
        ]
    )

    assert mapped == [
        {
                "type": "pdf",
                "source_type": "pdf",
                "evidence_id": (
                    "pdf:side_cookers/3282l/3282l.pdf:"
                    "pages:15-15"
                ),
                "authority_channel": (
                    "approved_technical_document"
                ),
            "source_id": "side_cookers/3282l/3282l.pdf",
            "display_label": "3282l.pdf",
            "filename": "3282l.pdf",
            "relative_path": "side_cookers/3282l/3282l.pdf",
            "page_start": 15,
            "page_end": 15,
            "page": 15,
        }
    ]
