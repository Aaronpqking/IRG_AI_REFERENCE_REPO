from dataclasses import dataclass, field
from typing import Any

from src.runtime_contracts import (
    CONTEXT_PACKET_VERSION,
    PIPELINE_VERSION,
    SOURCE_SCHEMA_VERSION,
)

ANSWER_CONTRACT_VERSION = "phase0.v1"


@dataclass(frozen=True)
class UpsertEmployeeRequest:
    display_name: str = ""
    email: str | None = None
    zoho_id: str | None = None
    employee_lookup: str | None = None


@dataclass(frozen=True)
class UpsertEmployeeResponse:
    employee_id: str
    display_name: str
    email: str | None = None
    zoho_id: str | None = None


@dataclass(frozen=True)
class StartConversationRequest:
    employee_id: str
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None


@dataclass(frozen=True)
class StartConversationResponse:
    conversation_id: str
    employee_id: str
    status: str


@dataclass(frozen=True)
class SubmitChatTurnRequest:
    employee_id: str
    conversation_id: str
    question: str
    top_k: int = 5
    request_id: str | None = None


@dataclass(frozen=True)
class SubmitChatTurnResponse:
    employee_id: str
    conversation_id: str
    user_turn_id: str
    assistant_turn_id: str
    question: str
    answer: str
    sources: list[dict[str, Any]]
    response_origin: str | None = None
    model_name: str | None = None
    latency_ms: int | None = None
    token_count: int | None = None
    low_confidence: bool | None = None
    low_confidence_reason: str | None = None
    diagnostics: dict[str, Any] | None = None
    execution_trace: dict[str, Any] | None = None
    contract_version: str = ANSWER_CONTRACT_VERSION
    answer_text: str | None = None
    answer_sources: list[dict[str, Any]] = field(default_factory=list)
    candidate_basis: list[dict[str, Any]] = field(default_factory=list)
    citation_validation: dict[str, Any] | None = None
    response_class: str | None = None
    evidence_status: str | None = None
    resolution_state: str | None = None
    canonical_question: str | None = None
    source_schema_version: str = SOURCE_SCHEMA_VERSION
    context_packet_version: str = CONTEXT_PACKET_VERSION
    pipeline_version: str = PIPELINE_VERSION
    request_id: str | None = None
    products: list[dict[str, Any]] = field(default_factory=list)
    active_collection: str | None = None


@dataclass(frozen=True)
class RecentTurnsRequest:
    conversation_id: str
    limit: int = 10


@dataclass(frozen=True)
class RecentTurnsResponse:
    conversation_id: str
    turns: list[dict[str, Any]]


@dataclass(frozen=True)
class FeedbackRequest:
    assistant_turn_id: str
    employee_id: str
    rating: str
    note: str | None = None


@dataclass(frozen=True)
class FeedbackResponse:
    feedback_id: str
    assistant_turn_id: str
    employee_id: str
    rating: str


@dataclass(frozen=True)
class EndConversationRequest:
    conversation_id: str
    status: str = "ended"


@dataclass(frozen=True)
class EndConversationResponse:
    conversation_id: str
    status: str
