import inspect
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from src.adapters.conversation_store_json import JsonConversationStore
from src.adapters.pdf_evidence import PdfEvidenceAdapter
from src.bootstrap import build_chat_service, build_runtime_components
from src.citation_validation import (
    NOT_REQUIRED,
    SUPPORTED,
    UNSUPPORTED,
    validate_answer_citations,
)
from src.conversation_history import BoundedConversation
from src.models import Chunk, ConversationTurn
from src.ports import (
    ControlledRetrievalPort,
    PdfEvidencePort,
    ProductDiscoveryPort,
)
from src.retrieval import RankedChunk
from src.runtime_contracts import (
    CONTEXT_PACKET_VERSION,
    PIPELINE_VERSION,
    SOURCE_SCHEMA_VERSION,
    RetrievalQuery,
)
from src.runtime_metadata_envelope import (
    RuntimeMetadataLoadState,
    TurnRuntimeMetadataEnvelope,
)
from src.structured_logging import (
    StructuredEventFormatter,
    current_request_id,
    log_event,
    request_log_context,
)
from src.unified_answer_context import assemble_answer_context


def _ranked(chunk: Chunk) -> RankedChunk:
    return RankedChunk(chunk, 1, 0.9, 1.0, 1.0, 0.0, 0.0, 1.0)


def test_public_ports_have_explicit_primary_contracts() -> None:
    assert inspect.signature(ProductDiscoveryPort.discover).return_annotation != inspect.Signature.empty
    assert "product_context" in inspect.signature(PdfEvidencePort.retrieve).parameters
    assert "conversation" in inspect.signature(ControlledRetrievalPort.retrieve).parameters


def test_offline_composition_builds_service_and_versioned_manifest(tmp_path) -> None:
    components = build_runtime_components(
        project_root=tmp_path,
        store_name="json",
        local_store="store.json",
        mode="offline_smoke",
        ensure_schema=True,
    )

    assert build_chat_service(components).controlled_retrieval is None
    assert components.manifest["pipeline_version"] == PIPELINE_VERSION
    assert components.manifest["source_schema_version"] == SOURCE_SCHEMA_VERSION
    assert components.manifest["context_packet_version"] == CONTEXT_PACKET_VERSION


def test_standard_pdf_adapter_conforms_to_product_context_signature() -> None:
    class Embedding:
        def embed_query(self, text):
            return [0.1]

    class Vector:
        def search(self, vector, limit):
            from src.models import RetrievalResult

            return RetrievalResult("q", ())

    result = PdfEvidenceAdapter(Embedding(), Vector()).retrieve(
        RetrievalQuery("question"), product_context=None
    )
    assert result.query.semantic_query_text == "question"


def test_context_budget_preserves_direct_evidence_with_separate_conversation_context() -> None:
    evidence = Chunk(
        "evidence",
        "Direct clearance evidence is 12 inches.",
        2,
        2,
        filename="manual.pdf",
        relative_path="manuals/manual.pdf",
    )
    result = assemble_answer_context(
        "What is the clearance?",
        conversation=BoundedConversation(
            turns=(
                ConversationTurn("turn-1", "conv-1", "user", "x" * 1000),
                ConversationTurn("turn-2", "conv-1", "assistant", "y" * 1000),
                ConversationTurn("turn-3", "conv-1", "user", "What is the clearance?"),
            ),
            current_turn_id="turn-3",
            current_turn_was_loaded=True,
        ),
        product_context=None,
        selected_pdf=(_ranked(evidence),),
        max_total_chars=800,
    )

    assert any(chunk.content_type == "technical_evidence" for chunk in result.chunks)
    assert result.packet is not None
    assert result.packet.version == CONTEXT_PACKET_VERSION


def test_citation_resolution_and_claim_support_are_separate() -> None:
    source = {
        "document_id": "doc-1",
        "filename": "manual.pdf",
        "relative_path": "manual.pdf",
        "page_start": 2,
        "page_end": 2,
        "text_preview": "Required clearance is 12 inches.",
    }
    supported = validate_answer_citations(
        "Required clearance is 12 inches. [source: manual.pdf, page 2]",
        [source],
    )
    unsupported = validate_answer_citations(
        "Required clearance is 99 inches. [source: manual.pdf, page 2]",
        [source],
    )

    assert supported.grounding_status == SUPPORTED
    assert unsupported.grounding_status == UNSUPPORTED
    assert validate_answer_citations("Service unavailable.", [], citations_required=False).grounding_status == NOT_REQUIRED


def test_json_store_round_trips_runtime_metadata(tmp_path) -> None:
    store = JsonConversationStore(tmp_path / "store.json")
    employee = store.upsert_employee("Aaron")
    conversation = store.start_conversation(employee)
    turn = store.save_turn(conversation, "assistant", "Answer")
    metadata = TurnRuntimeMetadataEnvelope(
        diagnostics=({"code": "READY"},),
    )

    store.save_turn_metadata(turn, metadata.as_dict())

    loaded = store.get_turn_metadata((turn,))[turn]
    assert loaded["runtime_metadata_state"] == (
        RuntimeMetadataLoadState.AVAILABLE_VALID.value
    )
    assert loaded["diagnostics"] == [{"code": "READY"}]


def test_structured_event_formatter_emits_required_shape() -> None:
    record = logging.LogRecord("test", logging.INFO, "", 0, "", (), None)
    record.structured_event = {
        "event": "pipeline.completed",
        "request_id": "req-1",
        "pipeline_stage": "persistence",
        "password": "do-not-log",
    }
    payload = json.loads(StructuredEventFormatter().format(record))

    assert payload["event"] == "pipeline.completed"
    assert payload["request_id"] == "req-1"
    assert payload["password"] == "[REDACTED]"


def test_request_log_context_is_operation_local(caplog) -> None:
    logger = logging.getLogger("request-context-proof")

    with request_log_context("req-context-proof"):
        assert current_request_id() == "req-context-proof"
        with caplog.at_level(logging.INFO, logger=logger.name):
            log_event(logger, logging.INFO, "external.operation")

    assert current_request_id() is None
    payload = caplog.records[-1].structured_event
    assert payload["request_id"] == "req-context-proof"


def test_parallel_request_log_contexts_do_not_cross_contaminate() -> None:
    request_ids = tuple(f"req-parallel-{index}" for index in range(10))

    def observe(request_id: str) -> str | None:
        with request_log_context(request_id):
            return current_request_id()

    with ThreadPoolExecutor(max_workers=10) as executor:
        observed = tuple(executor.map(observe, request_ids))

    assert observed == request_ids
    assert current_request_id() is None
