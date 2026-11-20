from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.citation_validation import NOT_REQUIRED, validation_supports_factual_answer
from src.response_modes import ANSWER_QUALIFIED, ANSWER_SUPPORTED
from src.grounding_mode import (
    DEFAULT_GROUNDING_VALIDATION_MODE,
    GroundingValidationMode,
    resolve_grounding_validation_mode,
)


GROUNDING_VALIDATION_FAILED = "GROUNDING_VALIDATION_FAILED"
GROUNDING_FAILURE_RESPONSE = (
    "I could not verify the answer against the available product information, "
    "so I am not presenting it as confirmed. Please provide the exact model, "
    "part number, or configuration and the specific detail you need checked."
)


@dataclass(frozen=True)
class FinalResponseDisposition:
    answer: str
    response_class: str
    evidence_status: str | None
    downgraded: bool
    reason_codes: tuple[str, ...]


def apply_final_response_disposition(
    answer: str,
    *,
    response_class: str,
    evidence_status: str | None,
    citation_validation: Mapping[str, Any],
    grounding_validation_mode: (
        str | GroundingValidationMode
    ) = DEFAULT_GROUNDING_VALIDATION_MODE,
) -> FinalResponseDisposition:
    """Apply post-validation replacement only in explicit enforce mode."""

    mode = resolve_grounding_validation_mode(grounding_validation_mode)
    if mode == GroundingValidationMode.OFF:
        return FinalResponseDisposition(
            answer=answer,
            response_class=response_class,
            evidence_status=evidence_status,
            downgraded=False,
            reason_codes=(),
        )
    citation_status = str(citation_validation.get("status") or "")
    if (
        response_class != ANSWER_SUPPORTED
        and citation_status == NOT_REQUIRED
    ):
        return FinalResponseDisposition(
            answer=answer,
            response_class=response_class,
            evidence_status=evidence_status,
            downgraded=False,
            reason_codes=(),
        )

    grounding_status = str(citation_validation.get("grounding_status") or "")
    if validation_supports_factual_answer(citation_validation):
        return FinalResponseDisposition(
            answer=answer,
            response_class=response_class,
            evidence_status=evidence_status,
            downgraded=False,
            reason_codes=(),
        )

    reasons = [
        str(item)
        for item in citation_validation.get("reason_codes", ())
        if item
    ]
    if grounding_status and grounding_status not in reasons:
        reasons.append(grounding_status)
    if mode != GroundingValidationMode.ENFORCE:
        return FinalResponseDisposition(
            answer=answer,
            response_class=ANSWER_QUALIFIED,
            evidence_status=GROUNDING_VALIDATION_FAILED,
            downgraded=False,
            reason_codes=tuple(reasons) or (GROUNDING_VALIDATION_FAILED,),
        )
    return FinalResponseDisposition(
        answer=GROUNDING_FAILURE_RESPONSE,
        response_class=ANSWER_QUALIFIED,
        evidence_status=GROUNDING_VALIDATION_FAILED,
        downgraded=True,
        reason_codes=tuple(reasons) or (GROUNDING_VALIDATION_FAILED,),
    )
