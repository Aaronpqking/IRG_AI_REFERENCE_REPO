from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any, Mapping, NoReturn

from src.product_runtime_state import ProductTurnResult
from src.runtime_contracts import FailureStage


RUNTIME_METADATA_SCHEMA_VERSION = "turn_runtime_metadata.v1"
V2_RUNTIME_METADATA_SCHEMA_VERSION = "turn_runtime_metadata.v2"
SUPPORTED_RUNTIME_METADATA_SCHEMA_VERSIONS = frozenset(
    {RUNTIME_METADATA_SCHEMA_VERSION, V2_RUNTIME_METADATA_SCHEMA_VERSION}
)

MAX_RUNTIME_METADATA_BYTES = 256 * 1024
MAX_RUNTIME_METADATA_DEPTH = 12
MAX_RUNTIME_METADATA_COLLECTION_ITEMS = 256
MAX_RUNTIME_METADATA_STRING_CHARS = 8_192
MAX_RUNTIME_METADATA_KEY_CHARS = 128

RUNTIME_METADATA_COLLECTION_LIMITS = {
    "diagnostics": 256,
    "products": 16,
    "validator_outcomes": 128,
}
_RESPONSE_CLASSES = frozenset(
    {
        "ANSWER_SUPPORTED",
        "ANSWER_QUALIFIED",
        "CLARIFICATION_REQUIRED",
        "SYSTEM_FAILURE",
    }
)
_FAILURE_STAGES = frozenset(item.value for item in FailureStage)

_TOP_LEVEL_FIELDS = frozenset(
    {
        "metadata_schema_version",
        "literal_question",
        "diagnostics",
    }
)
_V2_TOP_LEVEL_FIELDS = frozenset(
    {
        "metadata_schema_version",
        "literal_question",
        "request_id",
        "conversation_id",
        "user_turn_id",
        "assistant_turn_id",
        "active_collection",
        "literal_question_hash",
        "products",
        "analysis_metadata",
        "retrieval_metadata",
        "validator_outcomes",
        "latency_ms",
        "final_response_class",
        "failure_stage",
        "diagnostics",
    }
)
_V2_REQUIRED_FIELDS = _V2_TOP_LEVEL_FIELDS - {"failure_stage"}
_LITERAL_QUESTION_FIELDS = frozenset({"content_hash", "encoding"})
RUNTIME_RESPONSE_DIAGNOSTIC_CODE = "RUNTIME_RESPONSE_METADATA"
RUNTIME_RESPONSE_TRUNCATION_DIAGNOSTIC_CODE = (
    "RUNTIME_RESPONSE_METADATA_TRUNCATED"
)
_RUNTIME_RESPONSE_FIELDS = frozenset(
    {
        "canonical_question",
        "response_class",
        "evidence_status",
        "resolution_state",
        "source_schema_version",
        "context_packet_version",
        "pipeline_version",
        "request_id",
        "grounding_validation_mode",
        "grounding_diagnostic_status",
        "citation_status",
    }
)


class RuntimeMetadataFailureCode(StrEnum):
    VERSION_MISSING = "RUNTIME_METADATA_VERSION_MISSING"
    VERSION_UNSUPPORTED = "RUNTIME_METADATA_VERSION_UNSUPPORTED"
    INVALID_SHAPE = "RUNTIME_METADATA_INVALID_SHAPE"
    SIZE_EXCEEDED = "RUNTIME_METADATA_SIZE_EXCEEDED"
    COLLECTION_LIMIT_EXCEEDED = (
        "RUNTIME_METADATA_COLLECTION_LIMIT_EXCEEDED"
    )
    SERIALIZATION_FAILED = "RUNTIME_METADATA_SERIALIZATION_FAILED"
    TURN_BINDING_MISMATCH = "RUNTIME_METADATA_TURN_BINDING_MISMATCH"


class RuntimeMetadataLoadState(StrEnum):
    LEGACY_ABSENT = "LEGACY_ABSENT"
    AVAILABLE_VALID = "AVAILABLE_VALID"
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"
    INVALID_SHAPE = "INVALID_SHAPE"
    LOAD_FAILED = "LOAD_FAILED"


class RuntimeMetadataContractError(ValueError):
    def __init__(
        self,
        code: RuntimeMetadataFailureCode,
        message: str,
    ) -> None:
        super().__init__(f"{code.value}: {message}")
        self.code = code
        self.detail = message


class RuntimeMetadataPersistenceError(RuntimeError):
    def __init__(self, code: str, stage: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.stage = stage
        self.detail = detail


@dataclass(frozen=True)
class RuntimeMetadataLoadResult:
    state: RuntimeMetadataLoadState
    document: Mapping[str, Any] | None = None
    diagnostic_code: str | None = None
    diagnostic_detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result = {
            "runtime_metadata_state": self.state.value,
            "runtime_metadata_status": self.state.value,
            "runtime_metadata_diagnostic": (
                {
                    "code": self.diagnostic_code,
                    "detail": self.diagnostic_detail,
                }
                if self.diagnostic_code
                else None
            ),
            "candidate_basis": (
                []
                if self.state == RuntimeMetadataLoadState.LEGACY_ABSENT
                else None
            ),
        }
        if self.document is not None:
            result.update(self.document)
            result.update(_runtime_response_metadata(self.document))
        return result


@dataclass(frozen=True)
class LiteralQuestionIntegrity:
    content_hash: str | None = None
    encoding: str = "utf-8"

    def as_dict(self) -> dict[str, str | None]:
        return {
            "content_hash": self.content_hash,
            "encoding": self.encoding,
        }


@dataclass(frozen=True)
class TurnRuntimeMetadataEnvelope:
    metadata_schema_version: str = RUNTIME_METADATA_SCHEMA_VERSION
    literal_question: LiteralQuestionIntegrity = field(
        default_factory=LiteralQuestionIntegrity
    )
    diagnostics: tuple[Mapping[str, Any], ...] = ()
    request_id: str | None = None
    conversation_id: str | None = None
    user_turn_id: str | None = None
    assistant_turn_id: str | None = None
    active_collection: str | None = None
    literal_question_hash: str | None = None
    products: tuple[ProductTurnResult, ...] | None = None
    analysis_metadata: Mapping[str, Any] | None = None
    retrieval_metadata: Mapping[str, Any] | None = None
    validator_outcomes: tuple[Mapping[str, Any], ...] | None = None
    latency_ms: Mapping[str, int] | None = None
    final_response_class: str | None = None
    failure_stage: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result = {
            "metadata_schema_version": self.metadata_schema_version,
            "literal_question": self.literal_question.as_dict(),
            "diagnostics": list(self.diagnostics),
        }
        if self.metadata_schema_version == V2_RUNTIME_METADATA_SCHEMA_VERSION:
            result.update(
                {
                    "request_id": self.request_id,
                    "conversation_id": self.conversation_id,
                    "user_turn_id": self.user_turn_id,
                    "assistant_turn_id": self.assistant_turn_id,
                    "active_collection": self.active_collection,
                    "literal_question_hash": self.literal_question_hash,
                    "products": [
                        item.as_dict() for item in (self.products or ())
                    ],
                    "analysis_metadata": dict(self.analysis_metadata or {}),
                    "retrieval_metadata": dict(self.retrieval_metadata or {}),
                    "validator_outcomes": [
                        dict(item) for item in (self.validator_outcomes or ())
                    ],
                    "latency_ms": dict(self.latency_ms or {}),
                    "final_response_class": self.final_response_class,
                    "failure_stage": self.failure_stage,
                }
            )
        return result

    def serialize(self) -> str:
        return serialize_runtime_metadata_envelope(self.as_dict())


@dataclass(frozen=True)
class BoundTurnRuntimeMetadata:
    turn_id: str
    envelope: TurnRuntimeMetadataEnvelope | Mapping[str, Any]

    def serialize_for_turn(self, expected_turn_id: str) -> str:
        if self.turn_id != expected_turn_id:
            _raise(
                RuntimeMetadataFailureCode.TURN_BINDING_MISMATCH,
                "metadata turn_id does not match the newly created turn",
            )
        payload = (
            self.envelope.as_dict()
            if isinstance(self.envelope, TurnRuntimeMetadataEnvelope)
            else self.envelope
        )
        return serialize_runtime_metadata_envelope(payload)


def bind_turn_runtime_metadata(
    turn_id: str,
    runtime_metadata: Mapping[str, Any],
) -> BoundTurnRuntimeMetadata:
    raw_question = runtime_metadata.get("raw_question")
    content_hash = (
        sha256(raw_question.encode("utf-8")).hexdigest()
        if isinstance(raw_question, str)
        else None
    )
    compatibility_values, truncation_diagnostic = (
        _bounded_runtime_response_values(runtime_metadata)
    )
    diagnostics = tuple(
        item
        for item in (
            {
                "code": RUNTIME_RESPONSE_DIAGNOSTIC_CODE,
                "values": compatibility_values,
            }
            if compatibility_values
            else None,
            truncation_diagnostic,
        )
        if item is not None
    )
    products = tuple(
        ProductTurnResult.from_dict(item).bind_turn(turn_id)
        for item in runtime_metadata.get("products") or []
    )
    use_v2 = runtime_metadata.get("products") is not None
    literal_hash = content_hash
    return BoundTurnRuntimeMetadata(
        turn_id=turn_id,
        envelope=TurnRuntimeMetadataEnvelope(
            metadata_schema_version=(
                V2_RUNTIME_METADATA_SCHEMA_VERSION
                if use_v2
                else RUNTIME_METADATA_SCHEMA_VERSION
            ),
            literal_question=LiteralQuestionIntegrity(
                content_hash=content_hash,
            ),
            diagnostics=diagnostics,
            request_id=_optional_string(runtime_metadata.get("request_id")),
            conversation_id=_optional_string(
                runtime_metadata.get("conversation_id")
            ),
            user_turn_id=_optional_string(runtime_metadata.get("user_turn_id")),
            assistant_turn_id=turn_id if use_v2 else None,
            active_collection=_optional_string(
                runtime_metadata.get("active_collection")
            ),
            literal_question_hash=literal_hash,
            products=products if use_v2 else None,
            analysis_metadata=(
                dict(runtime_metadata.get("analysis_metadata") or {})
                if use_v2
                else None
            ),
            retrieval_metadata=(
                dict(runtime_metadata.get("retrieval_metadata") or {})
                if use_v2
                else None
            ),
            validator_outcomes=(
                tuple(runtime_metadata.get("validator_outcomes") or ())
                if use_v2
                else None
            ),
            latency_ms=(
                dict(runtime_metadata.get("latency_ms") or {})
                if use_v2
                else None
            ),
            final_response_class=(
                _optional_string(runtime_metadata.get("final_response_class"))
                if use_v2
                else None
            ),
            failure_stage=(
                _optional_string(runtime_metadata.get("failure_stage"))
                if use_v2
                else None
            ),
        ),
    )


def validate_runtime_metadata_envelope(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "top-level payload must be an object",
        )
    if any(not isinstance(key, str) for key in payload):
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "top-level object keys must be strings",
        )
    if "metadata_schema_version" not in payload or not payload.get(
        "metadata_schema_version"
    ):
        _raise(
            RuntimeMetadataFailureCode.VERSION_MISSING,
            "metadata_schema_version is required",
        )
    version = payload["metadata_schema_version"]
    if not isinstance(version, str):
        _raise(
            RuntimeMetadataFailureCode.VERSION_UNSUPPORTED,
            f"unsupported metadata_schema_version: {version!r}",
        )
    if version not in SUPPORTED_RUNTIME_METADATA_SCHEMA_VERSIONS:
        _raise(
            RuntimeMetadataFailureCode.VERSION_UNSUPPORTED,
            f"unsupported metadata_schema_version: {version!r}",
        )
    allowed_fields = (
        _V2_TOP_LEVEL_FIELDS
        if version == V2_RUNTIME_METADATA_SCHEMA_VERSION
        else _TOP_LEVEL_FIELDS
    )
    unknown = set(payload) - allowed_fields
    if unknown:
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            f"unknown top-level fields: {sorted(unknown)!r}",
        )

    if version == V2_RUNTIME_METADATA_SCHEMA_VERSION:
        missing = _V2_REQUIRED_FIELDS - set(payload)
        if missing:
            _raise(
                RuntimeMetadataFailureCode.INVALID_SHAPE,
                f"missing V2 fields: {sorted(missing)!r}",
            )
        _validate_v2_fields(payload)

    literal = payload.get("literal_question")
    if literal is not None:
        _validate_literal_question(literal)
    for name, limit in RUNTIME_METADATA_COLLECTION_LIMITS.items():
        value = payload.get(name)
        if value is None:
            continue
        if not isinstance(value, list):
            _raise(
                RuntimeMetadataFailureCode.INVALID_SHAPE,
                f"{name} must be an array when present",
            )
        if len(value) > limit:
            _raise(
                RuntimeMetadataFailureCode.COLLECTION_LIMIT_EXCEEDED,
                f"{name} contains {len(value)} items; maximum is {limit}",
            )
        if any(not isinstance(item, Mapping) for item in value):
            _raise(
                RuntimeMetadataFailureCode.INVALID_SHAPE,
                f"{name} items must be objects",
            )
    return _validate_json_value(payload, path="$", depth=1)


def serialize_runtime_metadata_envelope(
    payload: Mapping[str, Any],
) -> str:
    validated = validate_runtime_metadata_envelope(payload)
    try:
        serialized = json.dumps(
            validated,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise RuntimeMetadataContractError(
            RuntimeMetadataFailureCode.SERIALIZATION_FAILED,
            str(exc),
        ) from exc
    size = len(serialized.encode("utf-8"))
    if size > MAX_RUNTIME_METADATA_BYTES:
        _raise(
            RuntimeMetadataFailureCode.SIZE_EXCEEDED,
            f"serialized payload is {size} bytes; maximum is "
            f"{MAX_RUNTIME_METADATA_BYTES}",
        )
    return serialized


def classify_runtime_metadata_document(
    payload: Any,
) -> RuntimeMetadataLoadResult:
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError:
            return _invalid_load_result(
                RuntimeMetadataFailureCode.INVALID_SHAPE,
                "stored metadata is not valid UTF-8",
            )
    if isinstance(payload, str):
        raw_size = len(payload.encode("utf-8"))
        if raw_size > MAX_RUNTIME_METADATA_BYTES:
            return _invalid_load_result(
                RuntimeMetadataFailureCode.SIZE_EXCEEDED,
                f"stored payload is {raw_size} bytes; maximum is "
                f"{MAX_RUNTIME_METADATA_BYTES}",
            )
        try:
            payload = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            return _invalid_load_result(
                RuntimeMetadataFailureCode.INVALID_SHAPE,
                "stored metadata is not valid JSON",
            )
    try:
        serialized = serialize_runtime_metadata_envelope(payload)
    except RuntimeMetadataContractError as exc:
        state = (
            RuntimeMetadataLoadState.UNSUPPORTED_VERSION
            if exc.code == RuntimeMetadataFailureCode.VERSION_UNSUPPORTED
            else RuntimeMetadataLoadState.INVALID_SHAPE
        )
        return RuntimeMetadataLoadResult(
            state=state,
            diagnostic_code=exc.code.value,
            diagnostic_detail=exc.detail,
        )
    return RuntimeMetadataLoadResult(
        state=RuntimeMetadataLoadState.AVAILABLE_VALID,
        document=json.loads(serialized),
    )


def legacy_absent_runtime_metadata() -> RuntimeMetadataLoadResult:
    return RuntimeMetadataLoadResult(
        state=RuntimeMetadataLoadState.LEGACY_ABSENT,
    )


def failed_runtime_metadata_load(
    code: str,
    detail: str,
) -> RuntimeMetadataLoadResult:
    return RuntimeMetadataLoadResult(
        state=RuntimeMetadataLoadState.LOAD_FAILED,
        diagnostic_code=code,
        diagnostic_detail=detail,
    )


def _invalid_load_result(
    code: RuntimeMetadataFailureCode,
    detail: str,
) -> RuntimeMetadataLoadResult:
    return RuntimeMetadataLoadResult(
        state=RuntimeMetadataLoadState.INVALID_SHAPE,
        diagnostic_code=code.value,
        diagnostic_detail=detail,
    )


def _runtime_response_metadata(
    document: Mapping[str, Any],
) -> dict[str, Any]:
    for diagnostic in document.get("diagnostics") or []:
        if not isinstance(diagnostic, Mapping):
            continue
        if diagnostic.get("code") != RUNTIME_RESPONSE_DIAGNOSTIC_CODE:
            continue
        values = diagnostic.get("values")
        if not isinstance(values, Mapping):
            continue
        return {
            key: values[key]
            for key in _RUNTIME_RESPONSE_FIELDS
            if key in values
        }
    return {}


def _bounded_runtime_response_values(
    runtime_metadata: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    values = {
        key: runtime_metadata[key]
        for key in sorted(_RUNTIME_RESPONSE_FIELDS)
        if key in runtime_metadata and runtime_metadata[key] is not None
    }
    canonical_question = values.get("canonical_question")
    if not isinstance(canonical_question, str) or len(
        canonical_question
    ) <= MAX_RUNTIME_METADATA_STRING_CHARS:
        return values, None

    values["canonical_question"] = canonical_question[
        :MAX_RUNTIME_METADATA_STRING_CHARS
    ]
    return values, {
        "code": RUNTIME_RESPONSE_TRUNCATION_DIAGNOSTIC_CODE,
        "values": {
            "field": "canonical_question",
            "original_character_count": len(canonical_question),
            "stored_character_count": MAX_RUNTIME_METADATA_STRING_CHARS,
            "original_sha256": sha256(
                canonical_question.encode("utf-8")
            ).hexdigest(),
        },
    }


def _validate_literal_question(value: Any) -> None:
    if not isinstance(value, Mapping):
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "literal_question must be an object or null",
        )
    if any(not isinstance(key, str) for key in value):
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "literal_question object keys must be strings",
        )
    unknown = set(value) - _LITERAL_QUESTION_FIELDS
    if unknown:
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            f"unknown literal_question fields: {sorted(unknown)!r}",
        )
    content_hash = value.get("content_hash")
    if content_hash is not None and not isinstance(content_hash, str):
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "literal_question.content_hash must be a string or null",
        )
    if value.get("encoding", "utf-8") != "utf-8":
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "literal_question.encoding must be utf-8",
        )


def _validate_v2_fields(payload: Mapping[str, Any]) -> None:
    for name in (
        "request_id",
        "conversation_id",
        "user_turn_id",
        "assistant_turn_id",
        "active_collection",
        "literal_question_hash",
        "final_response_class",
    ):
        if not isinstance(payload.get(name), str) or not payload[name].strip():
            _raise(
                RuntimeMetadataFailureCode.INVALID_SHAPE,
                f"{name} must be a non-empty string",
            )
    if payload.get("failure_stage") is not None and not isinstance(
        payload.get("failure_stage"), str
    ):
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "failure_stage must be a string or null",
        )
    if payload["final_response_class"] not in _RESPONSE_CLASSES:
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "final_response_class is not a supported response class",
        )
    if (
        payload.get("failure_stage") is not None
        and payload["failure_stage"] not in _FAILURE_STAGES
    ):
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "failure_stage is not a supported pipeline stage",
        )
    for name in ("analysis_metadata", "retrieval_metadata", "latency_ms"):
        if not isinstance(payload.get(name), Mapping):
            _raise(
                RuntimeMetadataFailureCode.INVALID_SHAPE,
                f"{name} must be an object",
            )
    products = payload.get("products")
    if not isinstance(products, list):
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "products must be an array",
        )
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in payload["latency_ms"].values()
    ):
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "latency_ms values must be non-negative integers",
        )
    try:
        parsed = tuple(ProductTurnResult.from_dict(item) for item in products)
    except (TypeError, ValueError) as exc:
        _raise(RuntimeMetadataFailureCode.INVALID_SHAPE, str(exc))
    refs = [item.product_ref_id for item in parsed]
    if any(not item for item in refs) or len(refs) != len(set(refs)):
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "products must contain unique non-empty product_ref_id values",
        )
    if any(
        item.new_evidence_state is not None
        and item.new_evidence_state.created_turn_id
        != payload.get("assistant_turn_id")
        for item in parsed
    ):
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            "new evidence states must bind to assistant_turn_id",
        )


def _optional_string(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _validate_json_value(value: Any, *, path: str, depth: int) -> Any:
    if depth > MAX_RUNTIME_METADATA_DEPTH:
        _raise(
            RuntimeMetadataFailureCode.INVALID_SHAPE,
            f"{path} exceeds maximum nesting depth "
            f"{MAX_RUNTIME_METADATA_DEPTH}",
        )
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        if len(value) > MAX_RUNTIME_METADATA_STRING_CHARS:
            _raise(
                RuntimeMetadataFailureCode.INVALID_SHAPE,
                f"{path} string length exceeds "
                f"{MAX_RUNTIME_METADATA_STRING_CHARS}",
            )
        return value
    if isinstance(value, Mapping):
        if len(value) > MAX_RUNTIME_METADATA_COLLECTION_ITEMS:
            _raise(
                RuntimeMetadataFailureCode.COLLECTION_LIMIT_EXCEEDED,
                f"{path} object contains {len(value)} entries; maximum is "
                f"{MAX_RUNTIME_METADATA_COLLECTION_ITEMS}",
            )
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                _raise(
                    RuntimeMetadataFailureCode.INVALID_SHAPE,
                    f"{path} object keys must be strings",
                )
            if len(key) > MAX_RUNTIME_METADATA_KEY_CHARS:
                _raise(
                    RuntimeMetadataFailureCode.INVALID_SHAPE,
                    f"{path} key length exceeds {MAX_RUNTIME_METADATA_KEY_CHARS}",
                )
            normalized[key] = _validate_json_value(
                item,
                path=f"{path}.{key}",
                depth=depth + 1,
            )
        return normalized
    if isinstance(value, list):
        if len(value) > MAX_RUNTIME_METADATA_COLLECTION_ITEMS:
            _raise(
                RuntimeMetadataFailureCode.COLLECTION_LIMIT_EXCEEDED,
                f"{path} array contains {len(value)} items; maximum is "
                f"{MAX_RUNTIME_METADATA_COLLECTION_ITEMS}",
            )
        return [
            _validate_json_value(
                item,
                path=f"{path}[{index}]",
                depth=depth + 1,
            )
            for index, item in enumerate(value)
        ]
    _raise(
        RuntimeMetadataFailureCode.INVALID_SHAPE,
        f"{path} contains unsupported value type {type(value).__name__}",
    )


def _raise(code: RuntimeMetadataFailureCode, message: str) -> NoReturn:
    raise RuntimeMetadataContractError(code, message)
