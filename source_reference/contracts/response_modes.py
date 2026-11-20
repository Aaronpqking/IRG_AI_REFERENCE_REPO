from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.information_needs import InformationNeeds
from src.product_discovery import AMBIGUOUS_RESOLUTION_STATES
from src.grounding_mode import (
    DEFAULT_GROUNDING_VALIDATION_MODE,
    GroundingValidationMode,
    resolve_grounding_validation_mode,
)


ANSWER_SUPPORTED = "ANSWER_SUPPORTED"
ANSWER_QUALIFIED = "ANSWER_QUALIFIED"
CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
SYSTEM_FAILURE = "SYSTEM_FAILURE"

SYSTEM_FAILURE_RESPONSE = (
    "The product-information service is temporarily unavailable. "
    "Please try again shortly."
)

@dataclass(frozen=True)
class ResponseDecision:
    response_class: str
    response_origin: str
    diagnostic_status: str


def classify_successful_response(
    *,
    needs: InformationNeeds,
    resolution: Any,
    product_context: Any,
    evidence: Any,
    ranked_pdf: Any,
    relationship: dict[str, Any],
    grounding_validation_mode: (
        str | GroundingValidationMode
    ) = DEFAULT_GROUNDING_VALIDATION_MODE,
) -> ResponseDecision:
    mode = resolve_grounding_validation_mode(grounding_validation_mode)
    evidence_decision = getattr(evidence, "decision", None)
    conflicts = tuple(getattr(evidence_decision, "conflicting_fields", ()) or ())

    if needs.unsupported and not needs.technical:
        return ResponseDecision(
            (
                ANSWER_QUALIFIED
                if mode == GroundingValidationMode.ENFORCE
                else ANSWER_SUPPORTED
            ),
            "MODEL",
            "POLICY_RESTRICTED",
        )

    resolution_state = str(getattr(resolution, "state", "") or "")
    relationship_behavior = str(relationship.get("expected_behavior") or "")
    if (
        resolution_state in AMBIGUOUS_RESOLUTION_STATES
        or (
            bool(needs.technical)
            and relationship_behavior.startswith("CLARIFY_")
        )
    ):
        return ResponseDecision(
            (
                CLARIFICATION_REQUIRED
                if mode == GroundingValidationMode.ENFORCE
                else ANSWER_SUPPORTED
            ),
            "MODEL",
            "AMBIGUOUS_CANDIDATES",
        )

    selected = tuple(getattr(evidence, "selected", ()) or ())
    sufficient = bool(getattr(evidence_decision, "sufficient", False))
    if not needs.technical:
        if product_context is not None:
            return ResponseDecision(
                ANSWER_SUPPORTED,
                "MODEL",
                "DIRECT_DATABASE_SUPPORT",
            )
        return ResponseDecision(
            (
                ANSWER_QUALIFIED
                if mode == GroundingValidationMode.ENFORCE
                else ANSWER_SUPPORTED
            ),
            "MODEL",
            "NO_DIRECT_PRODUCT_MATCH",
        )

    if sufficient and selected:
        return ResponseDecision(
            ANSWER_SUPPORTED,
            "MODEL",
            "DIRECT_EVIDENCE_SUPPORT",
        )

    status = (
        "CONFLICTING_EVIDENCE"
        if conflicts
        else "WEAK_OR_INDIRECT_EVIDENCE"
        if selected
        else "NO_DIRECT_MATCH"
    )
    if getattr(ranked_pdf, "low_confidence", False) and selected:
        status = "WEAK_OR_INDIRECT_EVIDENCE"
    return ResponseDecision(
        (
            ANSWER_QUALIFIED
            if mode == GroundingValidationMode.ENFORCE
            else ANSWER_SUPPORTED
        ),
        "MODEL",
        status,
    )


def candidate_packet(candidate: Any) -> dict[str, Any]:
    approved_facts = dict(getattr(candidate, "approved_general_facts", ()) or ())
    structured_fields = {
        field: approved_facts.get(field)
        for field in (
            "categories",
            "filters",
            "attributes",
            "options",
            "configurations",
            "relationships",
        )
        if approved_facts.get(field) not in (None, "")
    }
    return {
        "product_id": getattr(candidate, "product_id", None),
        "product_name": getattr(candidate, "product_name", None),
        "brand": getattr(candidate, "brand", None),
        "model": getattr(candidate, "model", None),
        "mpn": getattr(candidate, "mpn", None),
        "upc": getattr(candidate, "upc", None),
        "product_status": getattr(candidate, "product_status", None),
        "description": approved_facts.get("product_description")
        or getattr(candidate, "description_excerpt", None),
        "matched_identifiers": list(
            getattr(candidate, "matched_identifiers", ()) or ()
        ),
        "candidate_score": getattr(candidate, "score", None),
        "match_type": getattr(candidate, "match_type", None),
        "matched_field": getattr(candidate, "matched_field", None),
        "matched_value": getattr(candidate, "matched_value", None),
        "search_layer": getattr(candidate, "search_layer", None),
        "search_depth": getattr(candidate, "search_depth", None),
        "score_components": dict(
            getattr(candidate, "score_components", ()) or ()
        ),
        "supporting_match_reasons": list(
            getattr(candidate, "supporting_match_reasons", ()) or ()
        ),
        "conflicts": list(
            getattr(candidate, "conflicts", ()) or ()
        ),
        "structured_product_context": structured_fields,
        "identity_status": "CANDIDATE_ONLY",
    }
