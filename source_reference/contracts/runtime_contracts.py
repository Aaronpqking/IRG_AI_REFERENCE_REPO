from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Mapping

from src.models import Chunk
from src.query_normalization import normalize_question
from src.retrieval import RankedRetrieval

if TYPE_CHECKING:
    from src.product_discovery import DiscoveryQuery, ProductCandidate
    from src.response_modes import ResponseDecision


PIPELINE_VERSION = "hexagonal.v1"
SOURCE_SCHEMA_VERSION = "sources.v2"
CONTEXT_PACKET_VERSION = "context.v1"
CANONICAL_CANDIDATE_ARCHITECTURE = "canonical_direct_rag.v1.9.38"
CANONICAL_CANDIDATE_LIFECYCLE_STATE = "CANONICAL_INTERNAL_PRE_UAT"
AUTHORITATIVE_ANSWER_SOURCE = "direct_generator"
SHADOW_CONTROL_FIELDS_CONSUMED: tuple[str, ...] = ()
MAX_IDENTIFIER_VARIANTS_PER_IDENTIFIER = 4


class FailureStage(StrEnum):
    VALIDATION = "validation"
    CONVERSATION_LOAD = "conversation_load"
    PRODUCT_DISCOVERY = "product_discovery"
    PRODUCT_RESOLUTION = "product_resolution"
    PDF_RETRIEVAL = "pdf_retrieval"
    CONTEXT_ASSEMBLY = "context_assembly"
    MODEL = "model"
    CITATION_VALIDATION = "citation_validation"
    PERSISTENCE = "persistence"
    UNEXPECTED = "unexpected"


@dataclass(frozen=True)
class UserQuestion:
    """The immutable user-authored question at the request boundary."""

    content: str
    encoding: str = "utf-8"

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("user question content must be a string")
        if self.encoding != "utf-8":
            raise ValueError("user question encoding must be utf-8")

    @property
    def canonical_content(self) -> str:
        return normalize_question(self.content).canonical_question


@dataclass(frozen=True)
class CanonicalRequest:
    user_question: UserQuestion
    canonical_question: str
    conversation_id: str | None = None
    employee_id: str | None = None
    request_id: str | None = None
    normalization_changed_input: bool = False

    @property
    def original_question(self) -> str:
        """Compatibility accessor for the immutable literal content."""
        return self.user_question.content

    @classmethod
    def from_question(
        cls,
        question: str,
        *,
        conversation_id: str | None = None,
        employee_id: str | None = None,
        request_id: str | None = None,
    ) -> "CanonicalRequest":
        normalized = normalize_question(question)
        return cls(
            user_question=UserQuestion(normalized.original_question),
            canonical_question=normalized.canonical_question,
            conversation_id=conversation_id,
            employee_id=employee_id,
            request_id=request_id,
            normalization_changed_input=normalized.normalization_changed_input,
        )


@dataclass(frozen=True)
class RetrievalQuery:
    semantic_query_text: str
    exact_identifier_queries: tuple[str, ...] = ()
    identifier_variants: tuple[str, ...] = ()
    product_facets: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        semantic = self.semantic_query_text.strip()
        if not semantic:
            raise ValueError("semantic_query_text is required")
        object.__setattr__(self, "semantic_query_text", semantic)
        object.__setattr__(
            self,
            "exact_identifier_queries",
            _clean_query_values(self.exact_identifier_queries),
        )
        object.__setattr__(
            self,
            "identifier_variants",
            _clean_query_values(self.identifier_variants),
        )
        object.__setattr__(
            self,
            "product_facets",
            _clean_product_facets(self.product_facets),
        )


def _clean_query_values(values: tuple[str, ...]) -> tuple[str, ...]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = str(value or "").strip()
        key = item.casefold()
        if item and key not in seen:
            cleaned.append(item)
            seen.add(key)
    return tuple(cleaned)


def _clean_product_facets(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    cleaned: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for name, value in values:
        field = str(name or "").strip()
        item = str(value or "").strip()
        key = (field.casefold(), item.casefold())
        if field and item and key not in seen:
            cleaned.append((field, item))
            seen.add(key)
    return tuple(cleaned)


@dataclass(frozen=True)
class ProductDiscoveryResult:
    query: DiscoveryQuery
    candidates: tuple[ProductCandidate, ...]
    rows_returned: int
    rows_retained: int
    duration_ms: int
    retrieved_at: str
    trace_id: str
    connection_id: int | None = None
    trace_path: str | None = None
    server_observation: Mapping[str, Any] | None = None
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PdfEvidenceResult:
    query: RetrievalQuery
    retrieval: RankedRetrieval
    duration_ms: int
    diagnostics: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelContextPacket:
    request: CanonicalRequest
    chunks: tuple[Chunk, ...]
    response_decision: ResponseDecision
    source_index: tuple[Mapping[str, Any], ...]
    version: str = CONTEXT_PACKET_VERSION


@dataclass(frozen=True)
class PipelineFailure:
    stage: FailureStage
    category: str
    error_code: str
    cause_type: str
    customer_message: str
    internal_details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeMetadata:
    canonical_question: str
    response_class: str | None
    evidence_status: str | None
    resolution_state: str | None
    source_schema_version: str = SOURCE_SCHEMA_VERSION
    context_packet_version: str = CONTEXT_PACKET_VERSION
    pipeline_version: str = PIPELINE_VERSION
    candidate_basis: tuple[Mapping[str, Any], ...] = ()
    request_id: str | None = None
    grounding_validation_mode: str | None = None
    grounding_diagnostic_status: str | None = None
    citation_status: str | None = None
    raw_question: str | None = None
    retrieval_evidence: Mapping[str, Any] = field(
        default_factory=dict
    )
    conversation_id: str | None = None
    user_turn_id: str | None = None
    active_collection: str | None = None
    products: tuple[Mapping[str, Any], ...] | None = None
    analysis_metadata: Mapping[str, Any] = field(default_factory=dict)
    retrieval_metadata: Mapping[str, Any] = field(default_factory=dict)
    validator_outcomes: tuple[Mapping[str, Any], ...] = ()
    latency_ms: Mapping[str, int] = field(default_factory=dict)
    final_response_class: str | None = None
    failure_stage: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ControlledRetrievalResult:
    route: str
    context_chunks: tuple[Chunk, ...]
    answer_sources: tuple[Mapping[str, Any], ...]
    diagnostics: Mapping[str, Any]
    low_confidence: bool
    low_confidence_reason: str | None
    retrieval_query: RetrievalQuery | None = None
    response_class: str = "ANSWER_SUPPORTED"
    evidence_status: str | None = None
    resolution_state: str | None = None
    candidate_basis: tuple[Mapping[str, Any], ...] = ()
    products: tuple[Mapping[str, Any], ...] = ()
    analysis_metadata: Mapping[str, Any] = field(default_factory=dict)
    active_collection: str | None = None
