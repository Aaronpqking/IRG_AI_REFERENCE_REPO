from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Mapping, Protocol

from src.models import Answer, Chunk, ConversationTurn, DocumentRecord, PageText
from src.models import RetrievalResult

if TYPE_CHECKING:
    from src.conversation_history import BoundedConversation
    from src.product_applicability import ProductApplicabilityContext
    from src.runtime_contracts import (
        ControlledRetrievalResult,
        PdfEvidenceResult,
        ProductDiscoveryResult,
        RetrievalQuery,
        UserQuestion,
    )
    from src.runtime_metadata_envelope import BoundTurnRuntimeMetadata
    from src.requested_products import TurnAnalysis
    from src.product_configurations import ProductConfigurationSourceResult


class CorpusReaderPort(Protocol):
    def read_pages(self, document: DocumentRecord) -> tuple[PageText, ...]:
        ...


class EmbeddingPort(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class VectorStorePort(Protocol):
    def ensure_collection(self, vector_size: int) -> None:
        ...

    def recreate_collection(self, vector_size: int) -> None:
        ...

    def create_payload_indexes(self) -> list[str]:
        ...

    def upsert_chunks(
        self,
        chunks: list[Chunk],
        vectors: list[list[float]],
    ) -> int:
        ...

    def count(self) -> int:
        ...

    def search(self, query_vector: list[float], limit: int) -> RetrievalResult:
        ...


class ChatModelPort(Protocol):
    def analyze_turn(
        self,
        question: str,
        *,
        conversation: BoundedConversation | None = None,
        prior_products: tuple[Mapping[str, Any], ...] = (),
    ) -> TurnAnalysis:
        ...

    def answer(
        self,
        question: str,
        context: tuple[Chunk, ...],
        *,
        conversation: BoundedConversation | None = None,
    ) -> Answer:
        ...


class ProductDiscoveryPort(Protocol):
    def discover(self, question: str) -> ProductDiscoveryResult:
        ...


class ProductConfigurationPort(Protocol):
    def get_configurations(
        self,
        product_id: int,
    ) -> ProductConfigurationSourceResult:
        ...


class PdfEvidencePort(Protocol):
    def retrieve(
        self,
        query: RetrievalQuery,
        *,
        top_k: int = 5,
        product_context: ProductApplicabilityContext | None = None,
    ) -> PdfEvidenceResult:
        ...


class ControlledRetrievalPort(Protocol):
    def retrieve(
        self,
        question: UserQuestion | str,
        *,
        top_k: int = 5,
        conversation_id: str | None = None,
        conversation: BoundedConversation | None = None,
        turn_analysis: TurnAnalysis | None = None,
        prior_products: tuple[Mapping[str, Any], ...] = (),
    ) -> ControlledRetrievalResult:
        ...


class ConversationStorePort(Protocol):
    def ensure_schema(self) -> None:
        ...

    def upsert_employee(
        self,
        display_name: str,
        email: str | None = None,
        zoho_id: str | None = None,
    ) -> str:
        ...

    def start_conversation(
        self,
        employee_id: str,
        customer_name: str | None = None,
        customer_phone: str | None = None,
        customer_email: str | None = None,
    ) -> str:
        ...

    def save_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: list[dict] | None = None,
        model_name: str | None = None,
        latency_ms: int | None = None,
        token_count: int | None = None,
    ) -> str:
        ...

    def save_turn_with_metadata(
        self,
        conversation_id: str,
        role: str,
        content: str,
        *,
        metadata: Mapping[str, Any],
        sources: list[dict] | None = None,
        model_name: str | None = None,
        latency_ms: int | None = None,
        token_count: int | None = None,
    ) -> str:
        ...

    def save_v2_turn_with_metadata(
        self,
        conversation_id: str,
        role: str,
        content: str,
        *,
        metadata_factory: Callable[[str], BoundTurnRuntimeMetadata],
        sources: list[dict] | None = None,
        model_name: str | None = None,
        latency_ms: int | None = None,
        token_count: int | None = None,
    ) -> str:
        ...

    def save_turn_metadata(
        self,
        turn_id: str,
        metadata: Mapping[str, Any],
    ) -> None:
        ...

    def get_turn_metadata(self, turn_ids: tuple[str, ...]) -> Mapping[str, Mapping[str, Any]]:
        ...

    def get_recent_turns(
        self,
        conversation_id: str,
        limit: int = 10,
    ) -> tuple[ConversationTurn, ...]:
        ...

    def get_recent_turns_bulk(
        self,
        conversation_ids: tuple[str, ...],
        limit: int = 10,
    ) -> Mapping[str, tuple[ConversationTurn, ...]]:
        ...

    def save_feedback(
        self,
        assistant_turn_id: str,
        employee_id: str,
        rating: str,
        note: str | None = None,
    ) -> str:
        ...

    def end_conversation(self, conversation_id: str, status: str = "ended") -> None:
        ...


class FileStorePort(Protocol):
    def write_text(self, path: str, content: str) -> None:
        ...

    def read_text(self, path: str) -> str:
        ...

    def read_json(self, path: str) -> Any:
        ...

    def write_json(self, path: str, payload: Any) -> None:
        ...

    def read_jsonl(self, path: str) -> list[Any]:
        ...

    def write_jsonl(self, path: str, rows: list[Any]) -> None:
        ...

    def append_jsonl(self, path: str, row: Any) -> None:
        ...

    def list_pdf_files(self, source_dir: str) -> list[str]:
        ...

    def sha256_file(self, source_dir: str, relative_path: str) -> str:
        ...


class ManifestStorePort(Protocol):
    def load(self, path: str) -> dict[str, Any]:
        ...

    def save(self, path: str, manifest: dict[str, Any]) -> None:
        ...

    def upsert_document(
        self,
        manifest: dict[str, Any],
        document: dict[str, Any],
    ) -> dict[str, Any]:
        ...
