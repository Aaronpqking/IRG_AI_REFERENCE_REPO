from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import re
from time import perf_counter
from typing import Any, Mapping
from uuid import uuid4

from src.configuration_applicability import (
    DEFAULT_PDF_CONFIGURATION_APPLICABILITY_MODE,
    PdfConfigurationApplicabilityMode,
    resolve_pdf_configuration_applicability_mode,
)
from src.conversation_history import BoundedConversation
from src.document_applicability import (
    DocumentApplicability,
    assess_document_applicability,
    chunk_applicability_diagnostics,
)
from src.corpus_neighbors import CorpusExpansionConfig, CorpusNeighborIndex
from src.evidence_context import build_evidence_package
from src.evidence_models import (
    database_evidence_identity,
    pdf_evidence_identity,
)
from src.information_needs import InformationNeeds, classify_information_needs
from src.models import Chunk
from src.ports import (
    PdfEvidencePort,
    ProductConfigurationPort,
    ProductDiscoveryPort,
)
from src.product_configuration_matching import observe_with_source
from src.product_applicability import ProductApplicabilityContext, build_product_applicability_context
from src.product_discovery import (
    CandidateResolution,
    CANDIDATE_SET,
    ELEVATED_PRODUCT,
    EXACT_IDENTIFIER_MATCH,
    IDENTITY_UNRESOLVED,
    NO_CANDIDATE,
    PRODUCT_FAMILY,
    ProductCandidate,
    build_retrieval_query,
    enrich_retrieval_query,
    is_identification_question,
    is_technical_question,
    resolve_candidates,
)
from src.product_roles import contextual_product_role
from src.prompt_loader import (
    RESPONSE_PACKET_PROMPT_FAMILY,
    LoadedPrompt,
    load_configured_prompt,
)
from src.requested_products import (
    ProductRequest,
    RequestedProductReference,
    TurnAnalysis,
    analyze_requested_products,
)
from src.product_runtime_state import (
    EvidenceState,
    PersistedEvidenceHandle,
    ProductTurnResult,
    active_evidence_hash,
)
from src.query_identity import normalize_identifier, parse_query_identity
from src.retrieval import RankedChunk, RankedRetrieval
from src.response_modes import (
    ANSWER_QUALIFIED,
    ANSWER_SUPPORTED,
    CLARIFICATION_REQUIRED,
    ResponseDecision,
    candidate_packet,
    classify_successful_response,
)
from src.source_selection import select_sources
from src.unified_answer_context import (
    AssembledAnswerContext,
    ProductOwnedAnswerContext,
    assemble_answer_context,
    assemble_product_owned_contexts,
    serialize_model_context,
)
from src.runtime_contracts import (
    ControlledRetrievalResult,
    ProductDiscoveryResult,
    RetrievalQuery,
    UserQuestion,
)
from src.structured_logging import current_request_id
from src.grounding_mode import (
    DEFAULT_GROUNDING_VALIDATION_MODE,
    GroundingValidationMode,
    resolve_grounding_validation_mode,
)


@dataclass(frozen=True)
class _RetrievedProductGroup:
    reference: RequestedProductReference
    discovery: ProductDiscoveryResult
    resolution: CandidateResolution
    selected_candidate: ProductCandidate | None
    product_context: ProductApplicabilityContext | None
    needs: InformationNeeds
    initial_retrieval_query: RetrievalQuery
    retrieval_query: RetrievalQuery
    pdf: Any
    ranked_pdf: RankedRetrieval
    evidence: Any
    expanded_pdf: Any
    applicability: tuple[dict[str, Any], ...]
    relationship: dict[str, Any]
    response_decision: ResponseDecision
    response_packet: dict[str, Any]
    assembled: AssembledAnswerContext
    canonical_evidence: tuple[Any, ...]
    configuration_observation: Mapping[str, Any]


@dataclass(frozen=True)
class _ProductExecution:
    request: ProductRequest
    assembled: AssembledAnswerContext
    answer_sources: tuple[dict[str, Any], ...]
    handles: tuple[PersistedEvidenceHandle, ...]
    retrieved_handles: tuple[PersistedEvidenceHandle, ...]
    product_id: str | None
    display_identity: str
    normalized_identifiers: tuple[str, ...]
    response_class: str
    evidence_status: str
    resolution_state: str
    candidate_basis: tuple[dict[str, Any], ...]
    applicability: tuple[dict[str, Any], ...]
    retrieval_performed: bool
    prior_context_reused: bool
    prior_lineage_reused: bool
    configuration_observation: Mapping[str, Any]
    answer_context_semantics: Mapping[str, Any] | None


class ControlledDiscoveryRetrievalService:
    def __init__(
        self,
        product_discovery: ProductDiscoveryPort,
        pdf_evidence: PdfEvidencePort,
        corpus_neighbors: CorpusNeighborIndex | None = None,
        expansion_config: CorpusExpansionConfig | None = None,
        product_context_max_chars: int = 6000,
        grounding_validation_mode: (
            str | GroundingValidationMode
        ) = DEFAULT_GROUNDING_VALIDATION_MODE,
        pdf_configuration_applicability_mode: (
            str | PdfConfigurationApplicabilityMode
        ) = DEFAULT_PDF_CONFIGURATION_APPLICABILITY_MODE,
        collection_identity: str = "unconfigured",
        response_packet_prompt: LoadedPrompt | None = None,
        product_configuration: ProductConfigurationPort | None = None,
    ) -> None:
        self.product_discovery = product_discovery
        self.pdf_evidence = pdf_evidence
        self.corpus_neighbors = (
            corpus_neighbors
            if corpus_neighbors is not None
            else CorpusNeighborIndex.empty()
        )
        self.expansion_config = expansion_config or CorpusExpansionConfig()
        self.product_context_max_chars = product_context_max_chars
        self.grounding_validation_mode = resolve_grounding_validation_mode(
            grounding_validation_mode
        )
        self.pdf_configuration_applicability_mode = (
            resolve_pdf_configuration_applicability_mode(
                pdf_configuration_applicability_mode
            )
        )
        self.collection_identity = str(collection_identity or "unconfigured")
        self.product_configuration = product_configuration
        self.response_packet_prompt = (
            response_packet_prompt
            or load_configured_prompt(RESPONSE_PACKET_PROMPT_FAMILY)
        )

    def _response_packet_analysis_metadata(
        self,
        metadata: Mapping[str, Any] | None = None,
        *,
        context_chunks: tuple[Chunk, ...] = (),
    ) -> dict[str, Any]:
        result = dict(metadata or {})
        identity = self.response_packet_prompt.identity()
        for key in ("configured_prompt_artifacts", "loaded_prompt_artifacts"):
            artifacts = dict(result.get(key) or {})
            artifacts[RESPONSE_PACKET_PROMPT_FAMILY] = identity
            result[key] = artifacts
        packet_applied = (
            self.grounding_validation_mode != GroundingValidationMode.ENFORCE
            and any(chunk.chunk_kind == "response_packet" for chunk in context_chunks)
        )
        if packet_applied:
            for key in ("applied_prompt_artifacts", "prompt_artifacts"):
                artifacts = dict(result.get(key) or {})
                artifacts[RESPONSE_PACKET_PROMPT_FAMILY] = identity
                result[key] = artifacts
        return result

    def _resolve_product_context(
        self,
        retrieval_text: str,
        *,
        route_hint: str,
        needs: InformationNeeds,
        preserve_query_ownership: bool = False,
    ) -> tuple[
        ProductDiscoveryResult | None,
        CandidateResolution,
        ProductCandidate | None,
        ProductApplicabilityContext | None,
        InformationNeeds,
    ]:
        discovery = None
        resolution = CandidateResolution(NO_CANDIDATE, None, (), "DISCOVERY_NOT_RUN")
        selected_candidate: ProductCandidate | None = None
        product_context: ProductApplicabilityContext | None = None
        discovery = self.product_discovery.discover(retrieval_text)
        owned_candidates = (
            _discovery_candidates_for_query(discovery)
            if preserve_query_ownership
            else tuple(discovery.candidates)
        )
        resolution = resolve_candidates(
            owned_candidates,
            discovery.query,
        )
        selected_candidate = resolution.selected
        if selected_candidate is not None:
            product_context = build_product_applicability_context(
                selected_candidate
            )
            if needs.technical and not needs.general:
                needs = InformationNeeds(
                    general=("product_identity",),
                    technical=needs.technical,
                    unsupported=needs.unsupported,
                )
        return (
            discovery,
            resolution,
            selected_candidate,
            product_context,
            needs,
        )

    def _observe_product_configuration(
        self,
        product_id: int | None,
        question: str,
    ) -> dict[str, Any]:
        return observe_with_source(
            self.product_configuration,
            product_id=product_id,
            question=question,
        )

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
        started = perf_counter()
        correlation_id = f"cdr_{uuid4().hex}"
        request_id = current_request_id()
        user_question = (
            question
            if isinstance(question, UserQuestion)
            else UserQuestion(question)
        )
        original_question = user_question.content
        question = user_question.canonical_content
        if not question:
            raise ValueError("question is required")
        if turn_analysis is not None:
            if turn_analysis.literal_question != original_question:
                raise ValueError("turn analysis literal question mismatch")
            # V1.9.38 canonical direct-RAG: a turn-analysis clarification is
            # diagnostic only. It cannot short-circuit retrieval or become a
            # model-facing response plan. The historical result builder is
            # retained below for research/replay compatibility.
            if turn_analysis.product_requests:
                return self._retrieve_analyzed_products(
                    user_question=user_question,
                    canonical_question=question,
                    analysis=turn_analysis,
                    prior_products=prior_products,
                    top_k=top_k,
                    conversation=conversation,
                    started=started,
                    correlation_id=correlation_id,
                    request_id=request_id,
                )
        conversation_retrieval_text = (
            conversation.retrieval_text()
            if conversation is not None
            else original_question
        )
        requested_products = analyze_requested_products(original_question)
        if len(requested_products) > 1:
            return self._retrieve_multiple_products(
                user_question=user_question,
                canonical_question=question,
                references=requested_products,
                top_k=top_k,
                conversation=conversation,
                started=started,
                correlation_id=correlation_id,
                request_id=request_id,
            )
        requested_product = None
        if requested_products:
            (requested_product,) = requested_products
        semantic_query_text = (
            original_question
            if requested_products
            else conversation_retrieval_text
        )
        discovery_question = semantic_query_text
        initial_retrieval_query = build_retrieval_query(semantic_query_text)
        needs = classify_information_needs(semantic_query_text)
        route_hint = _initial_route(semantic_query_text)
        (
            discovery,
            resolution,
            selected_candidate,
            product_context,
            needs,
        ) = self._resolve_product_context(
            discovery_question,
            route_hint=route_hint,
            needs=needs,
        )
        configuration_observation = self._observe_product_configuration(
            selected_candidate.product_id if selected_candidate else None,
            original_question,
        )
        retrieval_query = _merge_discovery_retrieval_query(
            initial_retrieval_query,
            discovery,
        )
        enrichment_candidates = resolution.selected_candidates
        if not enrichment_candidates and selected_candidate is not None:
            enrichment_candidates = (selected_candidate,)
        if not enrichment_candidates and resolution.candidates:
            enrichment_candidates = resolution.candidates[:5]
        retrieval_query = enrich_retrieval_query(
            retrieval_query,
            enrichment_candidates,
        )

        unsupported_only = route_hint == "UNSUPPORTED"
        pdf = _retrieve_pdf(
            self.pdf_evidence,
            retrieval_query,
            top_k,
            product_context,
        )
        pdf_duration_ms = pdf.duration_ms
        ranked_pdf = _rerank_by_applicability(
            pdf.retrieval,
            product_context,
            needs,
            top_k,
            corpus_neighbors=self.corpus_neighbors,
            candidate_contexts=_candidate_consensus_contexts(
                resolution,
                product_context,
            ),
            configuration_mode=(
                self.pdf_configuration_applicability_mode
            ),
        )
        evidence = build_evidence_package(
            semantic_query_text,
            ranked_pdf,
            product_context=product_context,
        )
        relationship = _relationship_applicability(
            semantic_query_text,
            needs,
            product_context,
        )
        expanded_pdf = self.corpus_neighbors.expand(
            tuple(item.chunk for item in evidence.selected),
            self.expansion_config,
        )
        response_decision = classify_successful_response(
            needs=needs,
            resolution=resolution,
            product_context=product_context,
            evidence=evidence,
            ranked_pdf=ranked_pdf,
            relationship=relationship,
            grounding_validation_mode=self.grounding_validation_mode,
        )
        response_packet = _response_packet(
            original_question=original_question,
            canonical_question=question,
            response_decision=response_decision,
            resolution=resolution,
            discovery=discovery,
            product_context=product_context,
            evidence=evidence,
            relationship=relationship,
            retrieval_query=retrieval_query,
            grounding_validation_mode=self.grounding_validation_mode,
            response_packet_prompt=self.response_packet_prompt,
        )
        assembled = assemble_answer_context(
            user_question.content,
            conversation=conversation,
            product_context=product_context,
            selected_pdf=evidence.selected,
            expanded_pdf=expanded_pdf,
            relationship_context=relationship,
            response_packet=response_packet,
            max_total_chars=self.expansion_config.max_pdf_context_chars
            + self.product_context_max_chars,
        )
        context = assembled.chunks
        candidate_basis = tuple(
            {
                **candidate_packet(candidate),
                "context_role": contextual_product_role(
                    candidate, semantic_query_text
                ),
                "rank": index + 1,
                "selected": (
                    selected_candidate is not None
                    and candidate.product_id == selected_candidate.product_id
                ),
                "resolution_state": resolution.state,
            }
            for index, candidate in enumerate(resolution.candidates[:10])
        )
        database_model_evidence = _admitted_database_evidence(
            resolution=resolution,
            selected_candidate=selected_candidate,
            product_context=product_context,
            assembled_chunks=assembled.chunks,
        )
        pdf_model_evidence = [
            pdf_evidence_identity(
                chunk,
                rank=len(database_model_evidence) + index,
            )
            for index, chunk in enumerate(
                item
                for item in assembled.chunks
                if item.content_type == "technical_evidence"
            )
        ]
        canonical_evidence = [
            *database_model_evidence,
            *pdf_model_evidence,
        ]
        answer_evidence = list(canonical_evidence)
        answer_sources = [
            dict(item.persistence_source)
            for item in answer_evidence
        ]
        selection = select_sources(needs, product_resolved=product_context is not None)
        route = "POLICY_RESTRICTED" if unsupported_only else selection.route
        low_confidence = (
            response_decision.response_class != ANSWER_SUPPORTED
            or not evidence.decision.sufficient
            or ranked_pdf.low_confidence
        )
        return ControlledRetrievalResult(
            route=route,
            context_chunks=context,
            answer_sources=tuple(answer_sources),
            diagnostics=_diagnostics(
                route,
                correlation_id,
                started,
                discovery,
                resolution,
                initial_retrieval_query,
                retrieval_query,
                pdf_duration_ms,
                evidence.diagnostics,
                needs=needs,
                product_context=product_context,
                applicability=_applicability_diagnostics(ranked_pdf, product_context, needs),
                internal_states=selection.internal_states,
                pdf_retrieval_diagnostics=getattr(ranked_pdf, "diagnostics", {}),
                context_assembly=assembled.diagnostics,
                pdf_expansion=expanded_pdf.diagnostics,
                relationship_applicability=relationship,
                conversation_history=(
                    conversation.diagnostics()
                    if conversation is not None
                    else None
                ),
                response_decision=response_decision,
                website_configuration_observation=(
                    configuration_observation
                ),
                canonical_evidence=tuple(
                    {
                        **_canonical_evidence_diagnostics(item),
                        **(
                            {"requested_product_owners": [0]}
                            if requested_products
                            else {}
                        ),
                    }
                    for item in canonical_evidence
                ),
                requested_products=(
                    _requested_product_diagnostics(
                        requested_product,
                        discovery,
                        resolution,
                        retrieval_query,
                        applicability=_applicability_diagnostics(
                            ranked_pdf,
                            product_context,
                            needs,
                        ),
                        canonical_evidence=tuple(
                            _canonical_evidence_diagnostics(item)
                            for item in canonical_evidence
                        ),
                        product_context=product_context,
                        response_decision=response_decision,
                        context_assembly=assembled.diagnostics,
                    ),
                )
                if requested_product is not None
                else (),
                request_id=request_id,
                grounding_validation_mode=self.grounding_validation_mode,
                pdf_configuration_applicability_mode=(
                    self.pdf_configuration_applicability_mode
                ),
            ),
            low_confidence=low_confidence,
            low_confidence_reason=(
                None
                if not low_confidence
                else response_decision.diagnostic_status
            ),
            retrieval_query=retrieval_query,
            response_class=response_decision.response_class,
            evidence_status=response_decision.diagnostic_status,
            resolution_state=resolution.state,
            candidate_basis=candidate_basis,
            analysis_metadata=self._response_packet_analysis_metadata(
                context_chunks=context,
            ),
            active_collection=self.collection_identity,
        )

    def _clarification_result(
        self,
        user_question: UserQuestion,
        analysis: TurnAnalysis,
        *,
        conversation: BoundedConversation | None,
        started: float,
        correlation_id: str,
        request_id: str | None,
    ) -> ControlledRetrievalResult:
        clarification = str(analysis.clarification_question or "").strip()
        chunk = Chunk(
            chunk_id="turn-analysis-clarification",
            document_id="runtime.turn_analysis",
            filename="Turn Analysis",
            relative_path="runtime/turn_analysis",
            page_start=1,
            page_end=1,
            text=(
                "[RESPONSE MODE]\n"
                "Mode: CLARIFICATION_REQUIRED\n"
                f"Clarification question: {clarification}"
            ),
            content_type="product_context",
            chunk_kind="response_packet",
        )
        diagnostics = {
            "request_id": request_id,
            "controlled_discovery": {
                "route": "TURN_ANALYSIS_CLARIFICATION",
                "requested_products": [],
                "requested_product_count": 0,
                "canonical_evidence": [],
                "coverage": {"requested_products": []},
                "evidence_status": "MATERIAL_PRODUCT_AMBIGUITY",
                "database_candidate_state": "NO_DB_MATCH",
                "context_assembly": {
                    "model_payload": {
                        "serialized_context": serialize_model_context(
                            user_question.content,
                            (chunk,),
                            conversation=conversation,
                        ),
                        "ordered_chunk_ids": [chunk.chunk_id],
                    }
                },
                "correlation_id": correlation_id,
                "total_retrieval_duration_ms": int(
                    (perf_counter() - started) * 1000
                ),
            },
        }
        return ControlledRetrievalResult(
            route="TURN_ANALYSIS_CLARIFICATION",
            context_chunks=(chunk,),
            answer_sources=(),
            diagnostics=diagnostics,
            low_confidence=True,
            low_confidence_reason="MATERIAL_PRODUCT_AMBIGUITY",
            response_class=CLARIFICATION_REQUIRED,
            evidence_status="MATERIAL_PRODUCT_AMBIGUITY",
            resolution_state="TURN_ANALYSIS_CLARIFICATION",
            products=(),
            analysis_metadata=analysis.persistence_metadata(),
            active_collection=self.collection_identity,
        )

    def _retrieve_analyzed_products(
        self,
        *,
        user_question: UserQuestion,
        canonical_question: str,
        analysis: TurnAnalysis,
        prior_products: tuple[Mapping[str, Any], ...],
        top_k: int,
        conversation: BoundedConversation | None,
        started: float,
        correlation_id: str,
        request_id: str | None,
    ) -> ControlledRetrievalResult:
        prior_by_ref = {
            str(item.get("product_ref_id")): item
            for item in prior_products
            if item.get("product_ref_id")
        }
        executions = tuple(
            self._execute_product_request(
                request,
                request_index=index,
                user_question=user_question,
                canonical_question=canonical_question,
                prior=prior_by_ref.get(request.prior_product_ref_id or ""),
                top_k=top_k,
            )
            for index, request in enumerate(analysis.product_requests)
        )
        assembled = assemble_product_owned_contexts(
            user_question.content,
            tuple(
                ProductOwnedAnswerContext(
                    request_index=index,
                    product_ref_id=item.request.product_ref_id,
                    literal_reference=(
                        item.request.current_mentions[0]
                        if item.request.current_mentions
                        else item.display_identity
                    ),
                    normalized_identifiers=item.normalized_identifiers,
                    resolution_status=item.resolution_state,
                    assembled=item.assembled,
                    requested_topics=item.request.requested_topics,
                )
                for index, item in enumerate(executions)
            ),
            conversation=conversation,
            max_total_chars=(
                self.expansion_config.max_pdf_context_chars
                + self.product_context_max_chars
            ),
            deduplicate_shared_pdf=False,
        )
        product_results: list[ProductTurnResult] = []
        answer_sources: list[dict[str, Any]] = []
        requested_diagnostics: list[dict[str, Any]] = []
        candidate_basis: list[dict[str, Any]] = []
        for index, execution in enumerate(executions):
            prior = prior_by_ref.get(execution.request.prior_product_ref_id or "")
            prior_handles = tuple(
                PersistedEvidenceHandle.from_dict(item)
                for item in (prior or {}).get("active_evidence") or []
            )
            result = _build_product_turn_result(
                execution,
                prior=prior,
                prior_handles=prior_handles,
                collection_identity=self.collection_identity,
                ordinal=index + 1,
            )
            product_results.append(result)
            answer_sources.extend(execution.answer_sources)
            candidate_basis.extend(execution.candidate_basis)
            requested_diagnostics.append(
                {
                    "request_index": index,
                    "product_ref_id": execution.request.product_ref_id,
                    "prior_product_ref_id": execution.request.prior_product_ref_id,
                    "current_mentions": list(execution.request.current_mentions),
                    "normalized_identifiers": list(
                        execution.normalized_identifiers
                    ),
                    "product_id": execution.product_id,
                    "display_identity": execution.display_identity,
                    "resolution_status": execution.resolution_state,
                    "response_class": execution.response_class,
                    "evidence_status": execution.evidence_status,
                    "retrieval_performed": execution.retrieval_performed,
                    "prior_evidence_reused": bool(prior_handles),
                    "prior_evidence_used_for_answer_context": (
                        execution.prior_context_reused
                    ),
                    "prior_evidence_used_for_lineage": (
                        execution.prior_lineage_reused
                    ),
                    "prior_active_evidence_ids": [
                        handle.evidence_id for handle in prior_handles
                    ],
                    "retrieved_evidence_ids": [
                        handle.evidence_id
                        for handle in execution.retrieved_handles
                    ],
                    "newly_retrieved_evidence_ids": [
                        handle.evidence_id
                        for handle in execution.retrieved_handles
                        if handle.evidence_id
                        not in {prior.evidence_id for prior in prior_handles}
                    ],
                    "retrieval_classification": _retrieval_classification(
                        execution.retrieval_performed,
                        prior_handles,
                        execution.retrieved_handles,
                    ),
                    "retrieval_observations": (
                        ["REDUNDANT_RETRIEVAL_OBSERVED"]
                        if _retrieval_classification(
                            execution.retrieval_performed,
                            prior_handles,
                            execution.retrieved_handles,
                        )
                        == "REDUNDANT"
                        else []
                    ),
                    "canonical_evidence": [
                        handle.as_dict() for handle in execution.handles
                    ],
                    "pdf_applicability": list(execution.applicability),
                    "website_configuration_observation": dict(
                        execution.configuration_observation
                    ),
                }
            )
        response_class = _combined_execution_response_class(executions)
        evidence_status = (
            executions[0].evidence_status
            if len({item.evidence_status for item in executions}) == 1
            else "PRODUCT_OWNED_EVIDENCE_GROUPS"
        )
        diagnostics = {
            "request_id": request_id,
            "controlled_discovery": {
                "route": "PRODUCT_COLLECTION_RETRIEVAL",
                "requested_products": requested_diagnostics,
                "requested_product_count": len(executions),
                "canonical_evidence": [
                    {
                        **handle.as_dict(),
                        "requested_product_owners": [
                            execution.request.product_ref_id
                        ],
                    }
                    for execution in executions
                    for handle in execution.handles
                ],
                "candidate_basis": candidate_basis,
                "database_candidate_state": "PRODUCT_COLLECTION",
                "resolution_basis": ["model_turn_analysis_then_database"],
                "evidence_status": evidence_status,
                "response_class": response_class,
                "coverage": {
                    "requested_products": [
                        {
                            "product_ref_id": execution.request.product_ref_id,
                            "evidence_ids": [
                                item.evidence_id for item in execution.handles
                            ],
                        }
                        for execution in executions
                    ]
                },
                "context_assembly": assembled.diagnostics,
                "relationship_applicability": {"requested_products": []},
                "website_configuration_observation": {
                    "schema_version": (
                        "product_configuration_observation.v1"
                    ),
                    "mode": "observe_only",
                    "answer_effect": "none",
                    "requested_products": [
                        {
                            "product_ref_id": execution.request.product_ref_id,
                            "observation": dict(
                                execution.configuration_observation
                            ),
                        }
                        for execution in executions
                    ],
                },
                "conversation_history": (
                    conversation.diagnostics() if conversation else {}
                ),
                "correlation_id": correlation_id,
                "total_retrieval_duration_ms": int(
                    (perf_counter() - started) * 1000
                ),
                "active_collection": self.collection_identity,
            },
        }
        low_confidence = any(
            item.response_class != ANSWER_SUPPORTED for item in executions
        )
        return ControlledRetrievalResult(
            route="PRODUCT_COLLECTION_RETRIEVAL",
            context_chunks=assembled.chunks,
            answer_sources=tuple(answer_sources),
            diagnostics=diagnostics,
            low_confidence=low_confidence,
            low_confidence_reason=evidence_status if low_confidence else None,
            retrieval_query=build_retrieval_query(user_question.content),
            response_class=response_class,
            evidence_status=evidence_status,
            resolution_state="PRODUCT_COLLECTION",
            candidate_basis=tuple(candidate_basis),
            products=tuple(item.as_dict() for item in product_results),
            analysis_metadata=self._response_packet_analysis_metadata(
                analysis.persistence_metadata(),
                context_chunks=assembled.chunks,
            ),
            active_collection=self.collection_identity,
        )

    def _execute_product_request(
        self,
        request: ProductRequest,
        *,
        request_index: int,
        user_question: UserQuestion,
        canonical_question: str,
        prior: Mapping[str, Any] | None,
        top_k: int,
    ) -> _ProductExecution:
        prior_handles = tuple(
            PersistedEvidenceHandle.from_dict(item)
            for item in (prior or {}).get("active_evidence") or []
        )
        compatible_prior_lineage = bool(
            prior
            and prior_handles
            and prior.get("active_evidence_state_id")
            and prior.get("evidence_state_turn_id")
            and all(
                item.product_ref_id == request.product_ref_id
                and (
                    not item.bounded_payload
                    or item.bounded_payload.get("collection_identity")
                    in (None, self.collection_identity)
                )
                for item in prior_handles
            )
        )
        compatible_prior_context = bool(
            request.use_prior_evidence and compatible_prior_lineage
        )
        prior_assembled: AssembledAnswerContext | None = None
        prior_sources: tuple[dict[str, Any], ...] = ()
        if compatible_prior_context:
            self._confirm_prior_product_identity(request, prior)
            prior_assembled, prior_sources = self._context_from_handles(
                user_question.content,
                prior_handles,
                answer_context_semantics=(
                    dict(prior.get("answer_context_semantics") or {})
                    if prior
                    else None
                ),
            )
        retrieval_required = (
            not compatible_prior_context
            or request.additional_retrieval_requested
        )
        fresh_group: _RetrievedProductGroup | None = None
        fresh_handles: tuple[PersistedEvidenceHandle, ...] = ()
        fresh_sources: tuple[dict[str, Any], ...] = ()
        if retrieval_required:
            reference = RequestedProductReference(
                request_index=request_index,
                literal_reference=request.product_query,
                normalized_identifiers=request.candidate_identifiers,
                analysis_basis="model_turn_analysis",
            )
            fresh_group = self._retrieve_product_group(
                user_question=user_question,
                canonical_question=canonical_question,
                reference=reference,
                top_k=top_k,
            )
            fresh_handles = _handles_from_group(
                fresh_group,
                product_ref_id=request.product_ref_id,
                collection_identity=self.collection_identity,
            )
            fresh_sources = tuple(
                {
                    **dict(item.persistence_source),
                    "product_ref_id": request.product_ref_id,
                }
                for item in fresh_group.canonical_evidence
            )
        assembled_parts = tuple(
            item
            for item in (
                prior_assembled,
                fresh_group.assembled if fresh_group else None,
            )
            if item is not None
        )
        if not assembled_parts:
            raise RuntimeError("EVIDENCE_HANDLE_CANNOT_BE_LOADED")
        chunks_by_id: dict[str, Chunk] = {}
        for part in assembled_parts:
            for chunk in part.chunks:
                chunks_by_id.setdefault(chunk.chunk_id, chunk)
        assembled = AssembledAnswerContext(
            question=user_question.content,
            chunks=tuple(chunks_by_id.values()),
            diagnostics={
                "prior_evidence_reused": compatible_prior_context,
                "prior_evidence_used_for_answer_context": (
                    compatible_prior_context
                ),
                "retrieval_performed": retrieval_required,
            },
            packet=(fresh_group.assembled.packet if fresh_group else None),
        )
        source_by_owner_identity: dict[tuple[str, str], dict[str, Any]] = {}
        for source in (*prior_sources, *fresh_sources):
            key = (
                request.product_ref_id,
                str(source.get("evidence_id") or source.get("chunk_id") or ""),
            )
            source_by_owner_identity.setdefault(key, source)
        product_id = (
            str(fresh_group.product_context.read_model_product_id)
            if fresh_group and fresh_group.product_context is not None
            else str(prior.get("product_id"))
            if prior and prior.get("product_id") is not None
            else None
        )
        prior_product_id = (
            str(prior.get("product_id"))
            if prior and prior.get("product_id") is not None
            else None
        )
        compatible_prior_lineage = bool(
            compatible_prior_lineage
            and product_id is not None
            and product_id == prior_product_id
        )
        handles = _deduplicate_handles(
            (
                *((prior_handles) if compatible_prior_lineage else ()),
                *fresh_handles,
            )
        )
        display_identity = (
            _display_identity(fresh_group.product_context)
            if fresh_group and fresh_group.product_context is not None
            else str((prior or {}).get("display_identity") or request.product_query)
        )
        normalized = tuple(
            dict.fromkeys(
                (
                    *request.candidate_identifiers,
                    *tuple((prior or {}).get("normalized_identifiers") or ()),
                )
            )
        )
        owned_sources = tuple(
            {
                **source,
                "product_ref_id": request.product_ref_id,
                "product_display_identity": display_identity,
            }
            for source in source_by_owner_identity.values()
        )
        configuration_observation = (
            dict(fresh_group.configuration_observation)
            if fresh_group is not None
            else self._observe_product_configuration(
                int(product_id)
                if product_id is not None and str(product_id).isdigit()
                else None,
                user_question.content,
            )
        )
        return _ProductExecution(
            request=request,
            assembled=assembled,
            answer_sources=owned_sources,
            handles=handles,
            retrieved_handles=fresh_handles,
            product_id=product_id,
            display_identity=display_identity,
            normalized_identifiers=normalized,
            response_class=(
                fresh_group.response_decision.response_class
                if fresh_group
                else ANSWER_SUPPORTED
            ),
            evidence_status=(
                fresh_group.response_decision.diagnostic_status
                if fresh_group
                else "PERSISTED_EVIDENCE_REUSED"
            ),
            resolution_state=(
                fresh_group.resolution.state
                if fresh_group
                else "PRIOR_PRODUCT_REUSED"
            ),
            candidate_basis=(
                tuple(
                    {
                        **candidate_packet(candidate),
                        "request_index": request_index,
                        "product_ref_id": request.product_ref_id,
                    }
                    for candidate in fresh_group.resolution.candidates[:10]
                )
                if fresh_group
                else ()
            ),
            applicability=(fresh_group.applicability if fresh_group else ()),
            retrieval_performed=retrieval_required,
            prior_context_reused=compatible_prior_context,
            prior_lineage_reused=compatible_prior_lineage,
            configuration_observation=configuration_observation,
            answer_context_semantics=(
                _answer_context_semantics(fresh_group)
                if fresh_group is not None
                else dict((prior or {}).get("answer_context_semantics") or {})
                or None
            ),
        )

    def _confirm_prior_product_identity(
        self,
        request: ProductRequest,
        prior: Mapping[str, Any],
    ) -> None:
        product_id = prior.get("product_id")
        if product_id is None:
            return
        discovery = self.product_discovery.discover(request.product_query)
        resolution = resolve_candidates(
            _discovery_candidates_for_query(discovery),
            discovery.query,
        )
        candidate_ids = {str(item.product_id) for item in resolution.candidates}
        if str(product_id) not in candidate_ids:
            raise RuntimeError("PRIOR_PRODUCT_IDENTITY_UNCONFIRMED")

    def _context_from_handles(
        self,
        question: str,
        handles: tuple[PersistedEvidenceHandle, ...],
        *,
        answer_context_semantics: Mapping[str, Any] | None = None,
    ) -> tuple[AssembledAnswerContext, tuple[dict[str, Any], ...]]:
        chunks: list[Chunk] = []
        sources: list[dict[str, Any]] = []
        for handle in handles:
            payload = dict(handle.bounded_payload or {})
            source = dict(payload.get("source") or {})
            source["product_ref_id"] = handle.product_ref_id
            if handle.evidence_type == "product_db":
                content = str(payload.get("model_visible_content") or "").strip()
                if not content:
                    raise RuntimeError("EVIDENCE_HANDLE_CANNOT_BE_LOADED")
                chunks.append(
                    Chunk(
                        chunk_id=f"persisted:{handle.evidence_id}",
                        document_id="flamy_ai_db.product_details",
                        filename="Flamy Product Read Model",
                        relative_path=f"database/product_details/{handle.product_id}",
                        page_start=1,
                        page_end=1,
                        text=content,
                        content_type="product_context",
                        chunk_kind="database_context",
                    )
                )
                source["evidence_text"] = content
            elif handle.evidence_type == "technical_pdf":
                source_ids = tuple(payload.get("source_chunk_ids") or ())
                if not source_ids and handle.chunk_id:
                    source_ids = (handle.chunk_id,)
                loaded = [
                    self.corpus_neighbors.by_chunk_id.get(str(chunk_id))
                    for chunk_id in source_ids
                ]
                loaded = [item for item in loaded if item is not None]
                if not loaded:
                    raise RuntimeError("EVIDENCE_HANDLE_CANNOT_BE_LOADED")
                for chunk in loaded:
                    chunks.append(
                        replace(chunk, content_type="technical_evidence")
                    )
                source["evidence_text"] = "\n\n".join(
                    chunk.text for chunk in loaded
                )
            else:
                raise RuntimeError("EVIDENCE_HANDLE_TYPE_UNSUPPORTED")
            sources.append(source)
        if answer_context_semantics:
            chunks.insert(
                0,
                _answer_context_semantics_chunk(answer_context_semantics),
            )
        return (
            AssembledAnswerContext(
                question=question,
                chunks=tuple(chunks),
                diagnostics={"persisted_evidence_rehydrated": True},
            ),
            tuple(sources),
        )

    def _retrieve_multiple_products(
        self,
        *,
        user_question: UserQuestion,
        canonical_question: str,
        references: tuple[RequestedProductReference, ...],
        top_k: int,
        conversation: BoundedConversation | None,
        started: float,
        correlation_id: str,
        request_id: str | None,
    ) -> ControlledRetrievalResult:
        groups = tuple(
            self._retrieve_product_group(
                user_question=user_question,
                canonical_question=canonical_question,
                reference=reference,
                top_k=top_k,
            )
            for reference in references
        )
        assembled = assemble_product_owned_contexts(
            user_question.content,
            tuple(
                ProductOwnedAnswerContext(
                    request_index=group.reference.request_index,
                    product_ref_id=(
                        f"current_product_{group.reference.request_index + 1}"
                    ),
                    literal_reference=group.reference.literal_reference,
                    normalized_identifiers=(
                        group.reference.normalized_identifiers
                    ),
                    resolution_status=group.resolution.state,
                    assembled=group.assembled,
                )
                for group in groups
            ),
            conversation=conversation,
            max_total_chars=(
                self.expansion_config.max_pdf_context_chars
                + self.product_context_max_chars
            ),
        )

        canonical_by_id: dict[str, Any] = {}
        evidence_owners: dict[str, list[int]] = {}
        for group in groups:
            for item in group.canonical_evidence:
                if not _evidence_visible_in_product_owned_context(
                    item,
                    group.reference.request_index,
                    assembled,
                ):
                    continue
                canonical_by_id.setdefault(item.evidence_id, item)
                evidence_owners.setdefault(item.evidence_id, []).append(
                    group.reference.request_index
                )
        canonical_evidence = tuple(canonical_by_id.values())
        canonical_diagnostics = tuple(
            {
                **_canonical_evidence_diagnostics(item),
                "requested_product_owners": evidence_owners[item.evidence_id],
            }
            for item in canonical_evidence
        )
        answer_sources = tuple(
            dict(item.persistence_source) for item in canonical_evidence
        )
        candidate_basis = tuple(
            {
                **candidate_packet(candidate),
                "context_role": contextual_product_role(
                    candidate, user_question.content
                ),
                "rank": rank,
                "selected": (
                    group.selected_candidate is not None
                    and candidate.product_id
                    == group.selected_candidate.product_id
                ),
                "resolution_state": group.resolution.state,
                "request_index": group.reference.request_index,
                "literal_reference": group.reference.literal_reference,
            }
            for group in groups
            for rank, candidate in enumerate(
                group.resolution.candidates[:10], 1
            )
        )
        requested_product_diagnostics = tuple(
            _requested_product_diagnostics(
                group.reference,
                group.discovery,
                group.resolution,
                group.retrieval_query,
                applicability=group.applicability,
                canonical_evidence=tuple(
                    {
                        **_canonical_evidence_diagnostics(item),
                        "requested_product_owners": evidence_owners[
                            item.evidence_id
                        ],
                    }
                    for item in group.canonical_evidence
                    if item.evidence_id in evidence_owners
                ),
                product_context=group.product_context,
                response_decision=group.response_decision,
                context_assembly=group.assembled.diagnostics,
            )
            for group in groups
        )
        response_class = _combined_group_response_class(groups)
        evidence_status = (
            groups[0].response_decision.diagnostic_status
            if len(
                {
                    group.response_decision.diagnostic_status
                    for group in groups
                }
            )
            == 1
            else "PRODUCT_OWNED_EVIDENCE_GROUPS"
        )
        needs = classify_information_needs(user_question.content)
        selection = select_sources(
            needs,
            product_resolved=any(
                group.product_context is not None for group in groups
            ),
        )
        unsupported_only = _initial_route(user_question.content) == "UNSUPPORTED"
        route = "POLICY_RESTRICTED" if unsupported_only else selection.route
        low_confidence = any(
            group.response_decision.response_class != ANSWER_SUPPORTED
            or not group.evidence.decision.sufficient
            or group.ranked_pdf.low_confidence
            for group in groups
        )
        diagnostics = _multi_product_diagnostics(
            route=route,
            correlation_id=correlation_id,
            started=started,
            groups=groups,
            requested_products=requested_product_diagnostics,
            canonical_evidence=canonical_diagnostics,
            candidate_basis=candidate_basis,
            context_assembly=assembled.diagnostics,
            conversation_history=(
                conversation.diagnostics()
                if conversation is not None
                else None
            ),
            response_class=response_class,
            evidence_status=evidence_status,
            internal_states=selection.internal_states,
            request_id=request_id,
            grounding_validation_mode=self.grounding_validation_mode,
            pdf_configuration_applicability_mode=(
                self.pdf_configuration_applicability_mode
            ),
        )
        return ControlledRetrievalResult(
            route=route,
            context_chunks=assembled.chunks,
            answer_sources=answer_sources,
            diagnostics=diagnostics,
            low_confidence=low_confidence,
            low_confidence_reason=(
                evidence_status if low_confidence else None
            ),
            retrieval_query=build_retrieval_query(user_question.content),
            response_class=response_class,
            evidence_status=evidence_status,
            resolution_state="REQUESTED_PRODUCT_GROUPS",
            candidate_basis=candidate_basis,
            analysis_metadata=self._response_packet_analysis_metadata(
                context_chunks=assembled.chunks,
            ),
        )

    def _retrieve_product_group(
        self,
        *,
        user_question: UserQuestion,
        canonical_question: str,
        reference: RequestedProductReference,
        top_k: int,
    ) -> _RetrievedProductGroup:
        needs = classify_information_needs(user_question.content)
        route_hint = _initial_route(user_question.content)
        (
            discovery,
            resolution,
            selected_candidate,
            product_context,
            needs,
        ) = self._resolve_product_context(
            reference.literal_reference,
            route_hint=route_hint,
            needs=needs,
            preserve_query_ownership=True,
        )
        assert discovery is not None
        configuration_observation = self._observe_product_configuration(
            selected_candidate.product_id if selected_candidate else None,
            user_question.content,
        )
        reference_query = build_retrieval_query(
            reference.literal_reference
        )
        initial_retrieval_query = replace(
            reference_query,
            semantic_query_text=user_question.content,
        )
        retrieval_query = _merge_discovery_retrieval_query(
            initial_retrieval_query,
            discovery,
        )
        enrichment_candidates = resolution.selected_candidates
        if not enrichment_candidates and selected_candidate is not None:
            enrichment_candidates = (selected_candidate,)
        if not enrichment_candidates and resolution.candidates:
            enrichment_candidates = resolution.candidates[:5]
        retrieval_query = enrich_retrieval_query(
            retrieval_query,
            enrichment_candidates,
        )
        pdf = _retrieve_pdf(
            self.pdf_evidence,
            retrieval_query,
            top_k,
            product_context,
        )
        ranked_pdf = _rerank_by_applicability(
            pdf.retrieval,
            product_context,
            needs,
            top_k,
            corpus_neighbors=self.corpus_neighbors,
            candidate_contexts=_candidate_consensus_contexts(
                resolution,
                product_context,
            ),
            configuration_mode=(
                self.pdf_configuration_applicability_mode
            ),
        )
        evidence = build_evidence_package(
            user_question.content,
            ranked_pdf,
            product_context=product_context,
        )
        relationship = _relationship_applicability(
            user_question.content,
            needs,
            product_context,
        )
        expanded_pdf = self.corpus_neighbors.expand(
            tuple(item.chunk for item in evidence.selected),
            self.expansion_config,
        )
        response_decision = classify_successful_response(
            needs=needs,
            resolution=resolution,
            product_context=product_context,
            evidence=evidence,
            ranked_pdf=ranked_pdf,
            relationship=relationship,
            grounding_validation_mode=self.grounding_validation_mode,
        )
        response_packet = _response_packet(
            original_question=user_question.content,
            canonical_question=canonical_question,
            response_decision=response_decision,
            resolution=resolution,
            discovery=discovery,
            product_context=product_context,
            evidence=evidence,
            relationship=relationship,
            retrieval_query=retrieval_query,
            grounding_validation_mode=self.grounding_validation_mode,
            response_packet_prompt=self.response_packet_prompt,
        )
        assembled = assemble_answer_context(
            user_question.content,
            product_context=product_context,
            selected_pdf=evidence.selected,
            expanded_pdf=expanded_pdf,
            relationship_context=relationship,
            response_packet=response_packet,
            max_total_chars=0,
        )
        database_evidence = _admitted_database_evidence(
            resolution=resolution,
            selected_candidate=selected_candidate,
            product_context=product_context,
            assembled_chunks=assembled.chunks,
        )
        pdf_evidence = [
            pdf_evidence_identity(
                chunk,
                rank=len(database_evidence) + index,
            )
            for index, chunk in enumerate(
                item
                for item in assembled.chunks
                if item.content_type == "technical_evidence"
            )
        ]
        applicability = tuple(
            _applicability_diagnostics(
                ranked_pdf,
                product_context,
                needs,
            )
        )
        return _RetrievedProductGroup(
            reference=reference,
            discovery=discovery,
            resolution=resolution,
            selected_candidate=selected_candidate,
            product_context=product_context,
            needs=needs,
            initial_retrieval_query=initial_retrieval_query,
            retrieval_query=retrieval_query,
            pdf=pdf,
            ranked_pdf=ranked_pdf,
            evidence=evidence,
            expanded_pdf=expanded_pdf,
            applicability=applicability,
            relationship=relationship,
            response_decision=response_decision,
            response_packet=response_packet,
            assembled=assembled,
            canonical_evidence=tuple(
                [*database_evidence, *pdf_evidence]
            ),
            configuration_observation=configuration_observation,
        )


def _handles_from_group(
    group: _RetrievedProductGroup,
    *,
    product_ref_id: str,
    collection_identity: str,
) -> tuple[PersistedEvidenceHandle, ...]:
    product_id = (
        str(group.product_context.read_model_product_id)
        if group.product_context is not None
        else None
    )
    handles: list[PersistedEvidenceHandle] = []
    for item in group.canonical_evidence:
        source = _json_safe({
            key: value
            for key, value in dict(item.persistence_source).items()
            if key not in {"evidence_text", "score"}
        })
        if isinstance(source.get("text_preview"), str):
            source["text_preview"] = source["text_preview"][:240]
        source_identity = str(item.evidence_id)
        model_content = str(item.model_visible_content or "")
        source_chunk_ids = _source_chunk_ids(model_content, source.get("chunk_id"))
        bounded_payload: dict[str, Any] = {
            "collection_identity": collection_identity,
            "source": source,
        }
        if item.source_type == "product_db":
            bounded_payload["model_visible_content"] = model_content[:8000]
        elif source_chunk_ids:
            bounded_payload["source_chunk_ids"] = list(source_chunk_ids)
        handles.append(
            PersistedEvidenceHandle(
                evidence_id=f"{source_identity}|owner:{product_ref_id}",
                evidence_type=str(item.source_type),
                product_ref_id=product_ref_id,
                product_id=product_id,
                source_identity=source_identity,
                document_id=(
                    str(source.get("document_id"))
                    if source.get("document_id") is not None
                    else None
                ),
                chunk_id=(
                    str(source.get("chunk_id"))
                    if source.get("chunk_id") is not None
                    else None
                ),
                page_start=(
                    int(source["page_start"])
                    if source.get("page_start") is not None
                    else None
                ),
                page_end=(
                    int(source["page_end"])
                    if source.get("page_end") is not None
                    else None
                ),
                content_hash=(
                    sha256(model_content.encode("utf-8")).hexdigest()
                    if model_content
                    else None
                ),
                bounded_payload=bounded_payload,
            )
        )
    return _deduplicate_handles(tuple(handles))


def _source_chunk_ids(
    model_content: str,
    fallback: Any,
) -> tuple[str, ...]:
    values: list[str] = []
    for label in ("Selected anchor chunk IDs", "Expanded chunk IDs"):
        match = re.search(
            rf"^{re.escape(label)}:\s*(.+)$",
            model_content,
            re.MULTILINE,
        )
        if match:
            values.extend(
                item.strip()
                for item in match.group(1).split(",")
                if item.strip()
            )
    if not values and fallback:
        values.append(str(fallback))
    return tuple(dict.fromkeys(values))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    return value


def _deduplicate_handles(
    handles: tuple[PersistedEvidenceHandle, ...],
) -> tuple[PersistedEvidenceHandle, ...]:
    by_id: dict[str, PersistedEvidenceHandle] = {}
    for handle in handles:
        by_id.setdefault(handle.evidence_id, handle)
    return tuple(by_id.values())


def _retrieval_classification(
    retrieval_performed: bool,
    prior_handles: tuple[PersistedEvidenceHandle, ...],
    retrieved_handles: tuple[PersistedEvidenceHandle, ...],
) -> str:
    if not retrieval_performed:
        return "NOT_PERFORMED"
    prior_ids = {item.evidence_id for item in prior_handles}
    new_ids = {
        item.evidence_id
        for item in retrieved_handles
        if item.evidence_id not in prior_ids
    }
    if prior_ids and not new_ids:
        return "REDUNDANT"
    if new_ids and len(new_ids) < len(retrieved_handles):
        return "PARTIALLY_ADDITIVE"
    return "FULLY_ADDITIVE"


def _build_product_turn_result(
    execution: _ProductExecution,
    *,
    prior: Mapping[str, Any] | None,
    prior_handles: tuple[PersistedEvidenceHandle, ...],
    collection_identity: str,
    ordinal: int,
) -> ProductTurnResult:
    active = execution.handles
    new_state: EvidenceState | None = None
    added: tuple[PersistedEvidenceHandle, ...] = ()
    active_state_id: str | None = None
    state_turn_id: str | None = None
    if active:
        if execution.prior_lineage_reused and prior:
            prior_ids = {item.evidence_id for item in prior_handles}
            added = tuple(
                item for item in active if item.evidence_id not in prior_ids
            )
            if not added:
                active_state_id = str(
                    prior.get("active_evidence_state_id") or ""
                ) or None
                state_turn_id = str(
                    prior.get("evidence_state_turn_id") or ""
                ) or None
            else:
                active_state_id = f"evidence_state_{uuid4().hex}"
                new_state = EvidenceState(
                    evidence_state_id=active_state_id,
                    product_ref_id=execution.request.product_ref_id,
                    product_id=execution.product_id,
                    parent_state_id=str(
                        prior.get("active_evidence_state_id") or ""
                    )
                    or None,
                    parent_state_turn_id=str(
                        prior.get("evidence_state_turn_id") or ""
                    )
                    or None,
                    added_evidence=added,
                    collection_identity=collection_identity,
                    created_turn_id=None,
                    active_evidence_count=len(active),
                    active_evidence_hash=active_evidence_hash(active),
                )
        else:
            added = active
            active_state_id = f"evidence_state_{uuid4().hex}"
            new_state = EvidenceState(
                evidence_state_id=active_state_id,
                product_ref_id=execution.request.product_ref_id,
                product_id=execution.product_id,
                parent_state_id=None,
                parent_state_turn_id=None,
                added_evidence=active,
                collection_identity=collection_identity,
                created_turn_id=None,
                active_evidence_count=len(active),
                active_evidence_hash=active_evidence_hash(active),
            )
    return ProductTurnResult(
        product_ref_id=execution.request.product_ref_id,
        product_id=execution.product_id,
        display_identity=execution.display_identity,
        normalized_identifiers=execution.normalized_identifiers,
        current_mentions=execution.request.current_mentions,
        ordinal=ordinal,
        active_evidence_state_id=active_state_id,
        evidence_state_turn_id=state_turn_id,
        new_evidence_state=new_state,
        prior_product_reused=execution.prior_lineage_reused,
        retrieval_performed=execution.retrieval_performed,
        added_evidence_ids=tuple(item.evidence_id for item in added),
        applicability_state=execution.evidence_status,
        answer_context_semantics=(
            dict(execution.answer_context_semantics)
            if execution.answer_context_semantics is not None
            else None
        ),
        validator_outcomes=(
            {
                "validator": "product_evidence_owner",
                "status": "PASS",
            },
        ),
    )


def _answer_context_semantics(
    group: _RetrievedProductGroup,
) -> dict[str, Any]:
    packet = group.response_packet
    return {
        "schema_version": "product_answer_context_semantics.v1",
        "applicability_state": group.response_decision.diagnostic_status,
        "product_role_or_applicability": _json_safe(
            packet.get("product_role_or_applicability")
        ),
        "policy_constraints": _json_safe(
            packet.get("policy_constraints") or []
        ),
        "recommended_clarification_target": packet.get(
            "recommended_clarification_target"
        ),
        "evidence_reconciliation": _json_safe(
            group.assembled.diagnostics.get("evidence_reconciliation") or {}
        ),
        "relationship_applicability": _json_safe(group.relationship),
    }


def _answer_context_semantics_chunk(
    semantics: Mapping[str, Any],
) -> Chunk:
    return Chunk(
        chunk_id="persisted-product-applicability-reconciliation",
        document_id="runtime.persisted_product_semantics",
        filename="Persisted Product Semantics",
        relative_path="runtime/persisted_product_semantics",
        page_start=1,
        page_end=1,
        text=(
            "[PERSISTED PRODUCT APPLICABILITY AND RECONCILIATION - "
            "CONTEXT ONLY, NOT EVIDENCE]\n"
            + json.dumps(
                dict(semantics),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                default=str,
            )
        ),
        content_type="product_context",
        chunk_kind="reconciliation_context",
    )


def _display_identity(context: ProductApplicabilityContext | None) -> str:
    if context is None:
        return "unresolved product"
    return str(
        context.model
        or context.mpn
        or context.sku
        or context.product_name
        or context.read_model_product_id
    )


def _combined_execution_response_class(
    executions: tuple[_ProductExecution, ...],
) -> str:
    classes = {item.response_class for item in executions}
    for value in (CLARIFICATION_REQUIRED, ANSWER_QUALIFIED):
        if value in classes:
            return value
    return ANSWER_SUPPORTED


def _requested_product_diagnostics(
    reference: RequestedProductReference,
    discovery: ProductDiscoveryResult,
    resolution: CandidateResolution,
    retrieval_query: RetrievalQuery,
    *,
    applicability: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    canonical_evidence: tuple[dict[str, Any], ...],
    product_context: ProductApplicabilityContext | None = None,
    response_decision: ResponseDecision | None = None,
    context_assembly: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "request_index": reference.request_index,
        "literal_reference": reference.literal_reference,
        "normalized_identifiers": list(reference.normalized_identifiers),
        "analysis_basis": reference.analysis_basis,
        "resolution_status": resolution.state,
        "resolution_reason": resolution.reason,
        "resolution_basis": list(resolution.resolution_basis),
        "missing_disambiguators": list(resolution.missing_disambiguators),
        "candidate_product_ids": [
            candidate.product_id for candidate in resolution.candidates
        ],
        "candidates": [
            {
                **candidate_packet(candidate),
                "requested_product_owner": reference.request_index,
            }
            for candidate in resolution.candidates[:10]
        ],
        "selected_product_context": _product_context_diagnostics(product_context),
        "database_query": {
            "original_query": discovery.query.original_query,
            "trace_id": discovery.trace_id,
            "rows_returned": discovery.rows_returned,
            "rows_retained": discovery.rows_retained,
            "duration_ms": discovery.duration_ms,
        },
        "pdf_query": _retrieval_query_packet(retrieval_query),
        "pdf_applicability": [
            {
                **dict(item),
                "requested_product_owner": reference.request_index,
            }
            for item in applicability
        ],
        "canonical_evidence": [
            {
                **dict(item),
                "requested_product_owners": item.get(
                    "requested_product_owners",
                    [reference.request_index],
                ),
            }
            for item in canonical_evidence
        ],
        "response_class": (
            response_decision.response_class
            if response_decision is not None
            else None
        ),
        "evidence_status": (
            response_decision.diagnostic_status
            if response_decision is not None
            else None
        ),
        "context_assembly": context_assembly or {},
    }


def _discovery_candidates_for_query(
    discovery: ProductDiscoveryResult,
) -> tuple[ProductCandidate, ...]:
    requested = set(discovery.query.detected_identifiers)
    candidates = tuple(discovery.candidates)
    if not requested:
        return candidates
    owned = []
    for candidate in candidates:
        candidate_identifiers = {
            normalize_identifier(str(value))
            for value in (
                *candidate.matched_identifiers,
                candidate.matched_identifier,
                candidate.normalized_identifier,
                candidate.model,
                candidate.mpn,
                candidate.sku,
                candidate.upc,
            )
            if value not in (None, "")
        }
        if requested & candidate_identifiers:
            owned.append(candidate)
    return tuple(owned)


def _evidence_visible_in_product_owned_context(
    evidence: Any,
    request_index: int,
    assembled: AssembledAnswerContext,
) -> bool:
    owner_label = f"REQUESTED PRODUCT {request_index + 1}"
    owned_chunks = tuple(
        chunk for chunk in assembled.chunks if owner_label in chunk.text
    )
    if evidence.source_type == "product_db":
        return any(
            chunk.chunk_kind in {
                "evidence_packet",
                "response_packet",
                "database_context",
            }
            for chunk in owned_chunks
        )
    if evidence.source_type != "technical_pdf":
        return False
    document_id = str(evidence.subject_identity.get("document_id") or "")
    page_start = evidence.persistence_source.get("page_start")
    page_end = evidence.persistence_source.get("page_end")
    return any(
        chunk.content_type == "technical_evidence"
        and str(
            chunk.document_id
            or chunk.relative_path
            or chunk.filename
            or ""
        )
        == document_id
        and chunk.page_start == page_start
        and chunk.page_end == page_end
        for chunk in owned_chunks
    )


def _combined_group_response_class(
    groups: tuple[_RetrievedProductGroup, ...],
) -> str:
    classes = {group.response_decision.response_class for group in groups}
    for value in (CLARIFICATION_REQUIRED, ANSWER_QUALIFIED):
        if value in classes:
            return value
    return ANSWER_SUPPORTED


def _multi_product_diagnostics(
    *,
    route: str,
    correlation_id: str,
    started: float,
    groups: tuple[_RetrievedProductGroup, ...],
    requested_products: tuple[dict[str, Any], ...],
    canonical_evidence: tuple[dict[str, Any], ...],
    candidate_basis: tuple[dict[str, Any], ...],
    context_assembly: dict[str, Any],
    conversation_history: dict[str, Any] | None,
    response_class: str,
    evidence_status: str,
    internal_states: tuple[str, ...],
    request_id: str | None,
    grounding_validation_mode: GroundingValidationMode,
    pdf_configuration_applicability_mode: PdfConfigurationApplicabilityMode,
) -> dict[str, Any]:
    applicability = [
        {
            **dict(item),
            "requested_product_owner": group.reference.request_index,
        }
        for group in groups
        for item in group.applicability
    ]
    database_ids = [
        item["evidence_id"]
        for item in canonical_evidence
        if item.get("source_type") == "product_db"
    ]
    pdf_ids = [
        item["evidence_id"]
        for item in canonical_evidence
        if item.get("source_type") == "technical_pdf"
    ]
    needs = classify_information_needs(groups[0].evidence.question)
    controlled = {
        "route": route,
        "reason_codes": [group.resolution.reason for group in groups],
        "requested_products": list(requested_products),
        "requested_product_count": len(groups),
        "detected_identifiers": [
            identifier
            for group in groups
            for identifier in group.reference.normalized_identifiers
        ],
        "identifier_intents": [
            {
                "type": identifier.identifier_type,
                "raw": identifier.raw,
                "normalized": identifier.normalized,
                "requested_product_owner": group.reference.request_index,
            }
            for group in groups
            for identifier in group.discovery.query.identifiers
        ],
        "detected_brand": None,
        "detected_product_type": None,
        "database_candidate_state": "REQUESTED_PRODUCT_GROUPS",
        "resolution_basis": ["requested_product_ownership"],
        "ambiguity_reason": None,
        "missing_disambiguators": list(
            dict.fromkeys(
                item
                for group in groups
                for item in group.resolution.missing_disambiguators
            )
        ),
        "selected_candidate_identity": None,
        "selected_product_context": None,
        "candidate_products": [
            candidate
            for group in requested_products
            for candidate in group["candidates"]
        ],
        "candidate_basis": list(candidate_basis),
        "database_query_terms": [],
        "database_descriptive_terms": [],
        "database_boolean_query": None,
        "exact_identifier_queries": [
            identifier
            for group in groups
            for identifier in group.retrieval_query.exact_identifier_queries
        ],
        "identifier_variants": [
            variant
            for group in groups
            for variant in group.retrieval_query.identifier_variants
        ],
        "semantic_query_text": groups[0].retrieval_query.semantic_query_text,
        "retrieval_query_before_resolution": None,
        "retrieval_query_after_resolution": None,
        "database_retrieval_query": None,
        "database_discovery_diagnostics": {
            "requested_products": [
                dict(getattr(group.discovery, "diagnostics", {}) or {})
                for group in groups
            ]
        },
        "database_rows_returned": sum(
            group.discovery.rows_returned for group in groups
        ),
        "database_rows_retained": sum(
            group.discovery.rows_retained for group in groups
        ),
        "database_duration_ms": sum(
            group.discovery.duration_ms for group in groups
        ),
        "database_trace_id": None,
        "database_connection_id": None,
        "database_trace_path": None,
        "database_server_observation": None,
        "pdf_query": groups[0].retrieval_query.semantic_query_text,
        "pdf_duration_ms": sum(group.pdf.duration_ms for group in groups),
        "pdf_candidate_retrieval": {
            "requested_products": [
                dict(getattr(group.ranked_pdf, "diagnostics", {}) or {})
                for group in groups
            ]
        },
        "information_needs": {
            "general": list(needs.general),
            "technical": list(needs.technical),
            "unsupported": list(needs.unsupported),
            "source_types": list(needs.source_types),
        },
        "document_applicability": applicability,
        "canonical_evidence": list(canonical_evidence),
        "coverage": {
            "requested_products": [
                {
                    "request_index": group["request_index"],
                    "resolution_status": group["resolution_status"],
                    "evidence_ids": [
                        item["evidence_id"]
                        for item in group["canonical_evidence"]
                    ],
                }
                for group in requested_products
            ],
            "database": {"model_evidence_ids": database_ids},
            "pdf": {"model_evidence_ids": pdf_ids},
        },
        "response_class": response_class,
        "evidence_status": evidence_status,
        "grounding_validation_mode": grounding_validation_mode.value,
        "pdf_configuration_applicability_mode": (
            pdf_configuration_applicability_mode.value
        ),
        "configuration_applicability": {
            "requested_products": [
                dict(
                    (getattr(group.ranked_pdf, "diagnostics", {}) or {}).get(
                        "configuration_applicability"
                    )
                    or {}
                )
                for group in groups
            ]
        },
        "website_configuration_observation": {
            "schema_version": "product_configuration_observation.v1",
            "mode": "observe_only",
            "answer_effect": "none",
            "requested_products": [
                {
                    "request_index": group.reference.request_index,
                    "observation": dict(
                        group.configuration_observation
                    ),
                }
                for group in groups
            ],
        },
        "context_assembly": context_assembly,
        "pdf_neighbor_expansion": {
            "requested_products": [
                dict(getattr(group.expanded_pdf, "diagnostics", {}) or {})
                for group in groups
            ]
        },
        "relationship_applicability": {
            "requested_products": [
                {
                    "request_index": group.reference.request_index,
                    **group.relationship,
                }
                for group in groups
            ]
        },
        "conversation_history": conversation_history or {},
        "internal_states": list(internal_states),
        "correlation_id": correlation_id,
        "total_retrieval_duration_ms": int((perf_counter() - started) * 1000),
    }
    return {
        "request_id": request_id,
        "controlled_discovery": controlled,
        "pdf_evidence": {
            "requested_products": [
                dict(group.evidence.diagnostics or {}) for group in groups
            ]
        },
    }


def _initial_route(question: str) -> str:
    needs = classify_information_needs(question)
    if (
        needs.unsupported
        and not needs.technical
        and not parse_query_identity(question).identifiers
    ):
        return "UNSUPPORTED"
    if needs.technical or is_technical_question(question):
        return "DATABASE_DISCOVERY_THEN_PDF"
    if needs.general or is_identification_question(question):
        return "DATABASE_IDENTIFICATION_ONLY"
    return "PDF_ONLY"


def _pdf_source_refs(selected: tuple[Any, ...]) -> tuple[dict[str, Any], ...]:
    refs = []
    for item in selected:
        chunk = item.chunk
        refs.append(
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "relative_path": chunk.relative_path,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "score": item.final_score,
                "rank": item.rank,
                "text_preview": chunk.text[:240],
                "evidence_text": chunk.text,
            }
        )
    return tuple(refs)


def _diagnostics(
    route: str,
    correlation_id: str,
    started: float,
    discovery: ProductDiscoveryResult | None,
    resolution: CandidateResolution,
    initial_retrieval_query: RetrievalQuery,
    retrieval_query: RetrievalQuery,
    pdf_duration_ms: int | None,
    pdf_diagnostics: dict[str, Any] | None,
    *,
    needs: InformationNeeds | None = None,
    product_context: ProductApplicabilityContext | None = None,
    applicability: list[dict[str, Any]] | None = None,
    internal_states: tuple[str, ...] = (),
    pdf_retrieval_diagnostics: dict[str, Any] | None = None,
    context_assembly: dict[str, Any] | None = None,
    pdf_expansion: dict[str, Any] | None = None,
    relationship_applicability: dict[str, Any] | None = None,
    conversation_history: dict[str, Any] | None = None,
    response_decision: ResponseDecision | None = None,
    website_configuration_observation: Mapping[str, Any] | None = None,
    canonical_evidence: tuple[dict[str, Any], ...] = (),
    requested_products: tuple[dict[str, Any], ...] = (),
    request_id: str | None = None,
    grounding_validation_mode: GroundingValidationMode = (
        DEFAULT_GROUNDING_VALIDATION_MODE
    ),
    pdf_configuration_applicability_mode: (
        PdfConfigurationApplicabilityMode
    ) = DEFAULT_PDF_CONFIGURATION_APPLICABILITY_MODE,
) -> dict[str, Any]:
    query = getattr(discovery, "query", None)
    discovery_retrieval_query = getattr(query, "retrieval_query", None)
    return {
        "request_id": request_id,
        "controlled_discovery": {
            "route": route,
            "reason_codes": [resolution.reason],
            "detected_identifiers": list(getattr(query, "detected_identifiers", ()) or ()),
            "identifier_intents": [
                {
                    "type": identifier.identifier_type,
                    "raw": identifier.raw,
                    "normalized": identifier.normalized,
                }
                for identifier in (getattr(query, "identifiers", ()) or ())
            ],
            "detected_brand": getattr(query, "detected_brand", None),
            "detected_product_type": getattr(query, "detected_product_type", None),
            "database_candidate_state": resolution.state,
            "resolution_basis": list(resolution.resolution_basis),
            "ambiguity_reason": resolution.ambiguity_reason,
            "missing_disambiguators": list(resolution.missing_disambiguators),
            "selected_candidate_identity": (
                {
                    "product_id": resolution.selected.product_id,
                    "identity_scope": resolution.selected.identity_scope,
                }
                if resolution.selected
                else None
            ),
            "candidate_products": [
                {
                    "product_id": candidate.product_id,
                    "product_name": candidate.product_name,
                    "brand": candidate.brand,
                    "model": candidate.model,
                    "mpn": candidate.mpn,
                    "sku": candidate.sku,
                    "upc": candidate.upc,
                    "product_status": candidate.product_status,
                    "score": candidate.score,
                    "match_lane": candidate.match_lane,
                    "matched_field": candidate.matched_field,
                    "matched_identifier": candidate.matched_identifier,
                    "normalized_identifier": candidate.normalized_identifier,
                    "match_reason": candidate.match_reason,
                    "match_type": candidate.match_type,
                    "search_layer": candidate.search_layer,
                    "search_depth": candidate.search_depth,
                    "score_components": dict(
                        candidate.score_components
                    ),
                    "supporting_match_reasons": list(
                        candidate.supporting_match_reasons
                    ),
                    "conflicts": list(candidate.conflicts),
                    "match_strength": candidate.match_strength,
                    "query_token_coverage": (
                        candidate.query_token_coverage
                    ),
                    "matched_identifiers": list(candidate.matched_identifiers),
                }
                for candidate in resolution.candidates[:10]
            ],
            "candidate_basis": [
                {
                    **candidate_packet(candidate),
                    "context_role": contextual_product_role(
                        candidate,
                        str(getattr(query, "original_query", "") or ""),
                    ),
                    "rank": index + 1,
                    "selected": (
                        resolution.selected is not None
                        and candidate.product_id == resolution.selected.product_id
                    ),
                    "resolution_state": resolution.state,
                }
                for index, candidate in enumerate(resolution.candidates[:10])
            ],
            "database_query_terms": list(getattr(query, "original_terms", ()) or ()),
            "database_descriptive_terms": list(
                getattr(query, "descriptive_terms", ()) or ()
            ),
            "database_boolean_query": getattr(query, "boolean_query", None),
            "exact_identifier_queries": list(
                retrieval_query.exact_identifier_queries
            ),
            "identifier_variants": list(
                retrieval_query.identifier_variants
            ),
            "semantic_query_text": retrieval_query.semantic_query_text,
            "retrieval_query_before_resolution": _retrieval_query_packet(
                initial_retrieval_query
            ),
            "retrieval_query_after_resolution": _retrieval_query_packet(
                retrieval_query
            ),
            "database_retrieval_query": (
                _retrieval_query_packet(discovery_retrieval_query)
                if discovery_retrieval_query is not None
                else None
            ),
            "database_discovery_diagnostics": dict(
                getattr(discovery, "diagnostics", {}) or {}
            ),
            "database_rows_returned": getattr(discovery, "rows_returned", None),
            "database_rows_retained": getattr(discovery, "rows_retained", None),
            "database_duration_ms": getattr(discovery, "duration_ms", None),
            "database_trace_id": getattr(discovery, "trace_id", None),
            "database_connection_id": getattr(discovery, "connection_id", None),
            "database_trace_path": getattr(discovery, "trace_path", None),
            "database_server_observation": getattr(discovery, "server_observation", None),
            "pdf_query": retrieval_query.semantic_query_text,
            "pdf_duration_ms": pdf_duration_ms,
            "pdf_candidate_retrieval": pdf_retrieval_diagnostics or {},
            "information_needs": {
                "general": list(needs.general) if needs else [],
                "technical": list(needs.technical) if needs else [],
                "unsupported": list(needs.unsupported) if needs else [],
                "source_types": list(needs.source_types) if needs else [],
            },
            "selected_product_context": _product_context_diagnostics(product_context),
            "requested_products": list(requested_products),
            "document_applicability": applicability or [],
            "canonical_evidence": list(canonical_evidence),
            "coverage": _coverage_diagnostics(
                discovery=discovery,
                resolution=resolution,
                applicability=applicability or [],
                canonical_evidence=canonical_evidence,
                needs=needs,
                product_context=product_context,
                context_assembly=context_assembly,
            ),
            "response_class": (
                response_decision.response_class if response_decision else None
            ),
            "evidence_status": (
                response_decision.diagnostic_status
                if response_decision
                else None
            ),
            "grounding_validation_mode": grounding_validation_mode.value,
            "pdf_configuration_applicability_mode": (
                pdf_configuration_applicability_mode.value
            ),
            "configuration_applicability": dict(
                (pdf_retrieval_diagnostics or {}).get(
                    "configuration_applicability"
                )
                or {}
            ),
            "website_configuration_observation": dict(
                website_configuration_observation or {}
            ),
            "context_assembly": context_assembly or {},
            "pdf_neighbor_expansion": pdf_expansion or {},
            "relationship_applicability": relationship_applicability or {},
            "conversation_history": conversation_history or {},
            "internal_states": list(internal_states),
            "correlation_id": correlation_id,
            "total_retrieval_duration_ms": int((perf_counter() - started) * 1000),
        },
        "pdf_evidence": pdf_diagnostics,
    }


def _canonical_evidence_diagnostics(item: Any) -> dict[str, Any]:
    return {
        "evidence_id": item.evidence_id,
        "source_type": item.source_type,
        "authority_channel": item.authority_channel,
        "authority_scope": list(item.authority_scope),
        "subject_identity": dict(item.subject_identity),
        "model_visible_reference": {
            key: item.persistence_source.get(key)
            for key in (
                "chunk_id",
                "document_id",
                "page_start",
                "page_end",
                "product_id",
            )
            if item.persistence_source.get(key)
            not in (None, "")
        },
        "admitted_fact_ids": list(item.admitted_fact_ids),
        "public_source": dict(item.public_source),
        "persistence_projection": {
            "evidence_id": item.persistence_source.get(
                "evidence_id"
            ),
            "source_type": item.persistence_source.get(
                "source_type"
            ),
            "text_preview_present": bool(
                item.persistence_source.get("text_preview")
            ),
        },
    }


def _coverage_diagnostics(
    *,
    discovery: ProductDiscoveryResult | None,
    resolution: CandidateResolution,
    applicability: list[dict[str, Any]],
    canonical_evidence: tuple[dict[str, Any], ...],
    needs: InformationNeeds | None,
    product_context: ProductApplicabilityContext | None,
    context_assembly: dict[str, Any] | None = None,
) -> dict[str, Any]:
    database_ids = [
        item["evidence_id"]
        for item in canonical_evidence
        if item.get("source_type") == "product_db"
    ]
    pdf_ids = [
        item["evidence_id"]
        for item in canonical_evidence
        if item.get("source_type") == "technical_pdf"
    ]
    applicable_count = sum(
        bool(item.get("document_applicability"))
        for item in applicability
    )
    consensus_exclusions = [
        {
            "document_id": item.get("document_id"),
            "chunk_id": item.get("chunk_id"),
            **dict(item.get("candidate_consensus") or {}),
        }
        for item in applicability
        if dict(item.get("candidate_consensus") or {}).get(
            "excluded_by_consensus_only"
        )
    ]
    capacity_omissions = list(
        (context_assembly or {}).get(
            "context_capacity_omitted_chunk_ids"
        )
        or ()
    )
    requested = {
        *tuple(needs.general if needs else ()),
        *tuple(needs.technical if needs else ()),
    }
    facets: dict[str, str] = {}
    db_fields = set(
        dict(product_context.approved_general_facts)
        if product_context is not None
        else {}
    )
    for facet in sorted(requested):
        db_supported = facet in db_fields or (
            facet == "product_identity"
            and bool(resolution.candidates)
        )
        pdf_supported = bool(pdf_ids)
        facets[facet] = (
            "BOTH"
            if db_supported and pdf_supported
            else "DB_SUPPORTED"
            if db_supported
            else "PDF_SUPPORTED"
            if pdf_supported
            else "MISSING"
        )
    return {
        "database": {
            "attempted": discovery is not None,
            "candidate_count": len(resolution.candidates),
            "resolution_state": resolution.state,
            "model_evidence_ids": database_ids,
            "omission_reason": (
                None
                if discovery is not None
                else "database_adapter_unavailable"
            ),
        },
        "pdf": {
            "attempted": True,
            "retrieval_status": (
                "CANDIDATES_RETRIEVED"
                if applicability
                else "NO_CANDIDATES"
            ),
            "candidate_count": len(applicability),
            "applicable_count": applicable_count,
            "rejected_count": max(
                0,
                len(applicability) - applicable_count,
            ),
            "applicability_status": (
                "NOT_EVALUATED_NO_CANDIDATES"
                if not applicability
                else "CANDIDATES_APPLICABLE"
                if applicable_count
                else "ALL_CANDIDATES_REJECTED"
            ),
            "context_capacity_omitted_chunk_ids": capacity_omissions,
            "consensus_only_exclusion_count": len(
                consensus_exclusions
            ),
            "consensus_only_exclusions": consensus_exclusions,
            "model_evidence_ids": pdf_ids,
            "omission_reason": None,
        },
        "facets": facets,
    }


def _response_packet(
    *,
    original_question: str,
    canonical_question: str,
    response_decision: ResponseDecision,
    resolution: CandidateResolution,
    discovery: ProductDiscoveryResult | None,
    product_context: ProductApplicabilityContext | None,
    evidence: Any,
    relationship: dict[str, Any],
    retrieval_query: RetrievalQuery,
    grounding_validation_mode: GroundingValidationMode,
    response_packet_prompt: LoadedPrompt,
) -> dict[str, Any]:
    query = getattr(discovery, "query", None)
    selected_pdf = tuple(getattr(evidence, "selected", ()) or ())
    evidence_decision = getattr(evidence, "decision", None)
    conflicts = tuple(
        getattr(evidence_decision, "conflicting_fields", ()) or ()
    )
    missing = [
        *tuple(getattr(evidence_decision, "missing_fields", ()) or ()),
        *tuple(resolution.missing_disambiguators or ()),
    ]
    missing = list(dict.fromkeys(str(item) for item in missing if item))
    target_parts = [
        *resolution.missing_disambiguators,
        *relationship.get("missing_discriminators", ()),
    ]
    clarification_target = ", ".join(
        dict.fromkeys(
            str(item).replace("_", " ") for item in target_parts if item
        )
    )
    if grounding_validation_mode == GroundingValidationMode.ENFORCE:
        instructions = {
            ANSWER_SUPPORTED: (
                "Give the direct supported answer and cite each supplied source."
            ),
            ANSWER_QUALIFIED: (
                "State what was found, what is not confirmed, and the safest "
                "useful next step. Do not use a generic refusal."
            ),
            CLARIFICATION_REQUIRED: (
                "Explain the candidate-specific ambiguity and ask one targeted "
                "question based on an actual candidate distinction."
            ),
        }[response_decision.response_class]
    else:
        instructions = response_packet_prompt.text
    return {
        "original_question": original_question,
        "canonical_question": canonical_question,
        "response_class": response_decision.response_class,
        "response_origin": response_decision.response_origin,
        "grounding_validation_mode": grounding_validation_mode.value,
        "response_instructions": instructions,
        "resolved_product": _product_context_packet(product_context),
        "candidate_products": [
            {
                **candidate_packet(candidate),
                "context_role": contextual_product_role(
                    candidate, canonical_question
                ),
            }
            for candidate in _response_packet_answer_candidates(
                resolution
            )
        ],
        "candidate_resolution": {
            "state": resolution.state,
            "reason": resolution.reason,
            "resolution_basis": list(resolution.resolution_basis),
            "ambiguity_reason": resolution.ambiguity_reason,
            "missing_disambiguators": list(
                resolution.missing_disambiguators
            ),
        },
        "detected_identifiers": list(
            getattr(query, "detected_identifiers", ()) or ()
        ),
        "retrieval_query": _retrieval_query_packet(retrieval_query),
        "evidence_status": response_decision.diagnostic_status,
        "pdf_sources": [
            {
                "filename": item.chunk.filename,
                "relative_path": item.chunk.relative_path,
                "page_start": item.chunk.page_start,
                "page_end": item.chunk.page_end,
                "selected_chunk_id": item.chunk.chunk_id,
            }
            for item in selected_pdf
        ],
        "known_conflicts": list(conflicts),
        "missing_evidence": missing,
        "product_role_or_applicability": relationship,
        "policy_constraints": [
            "Use supplied product and approved-document context.",
            "Treat product roles as contextual metadata, not answer authority.",
            "Distinguish confirmed facts from inference in the answer.",
        ],
        "recommended_clarification_target": (
            clarification_target or None
            if grounding_validation_mode == GroundingValidationMode.ENFORCE
            else None
        ),
    }


def _retrieve_pdf(
    pdf_evidence: PdfEvidencePort,
    query: RetrievalQuery,
    top_k: int,
    product_context: ProductApplicabilityContext | None,
) -> Any:
    return pdf_evidence.retrieve(
        query,
        top_k=top_k,
        product_context=product_context,
    )


def _merge_discovery_retrieval_query(
    initial: RetrievalQuery,
    discovery: ProductDiscoveryResult | None,
) -> RetrievalQuery:
    discovery_query = (
        discovery.query.retrieval_query
        if discovery is not None
        else None
    )
    if discovery_query is None:
        return initial
    return RetrievalQuery(
        semantic_query_text=initial.semantic_query_text,
        exact_identifier_queries=(
            *initial.exact_identifier_queries,
            *discovery_query.exact_identifier_queries,
        ),
        identifier_variants=(
            *initial.identifier_variants,
            *discovery_query.identifier_variants,
        ),
        product_facets=(
            *initial.product_facets,
            *discovery_query.product_facets,
        ),
    )


def _response_packet_answer_candidates(
    resolution: CandidateResolution,
) -> tuple[ProductCandidate, ...]:
    if resolution.state in {
        EXACT_IDENTIFIER_MATCH,
        ELEVATED_PRODUCT,
    }:
        return tuple(resolution.selected_candidates[:10])
    if resolution.state == PRODUCT_FAMILY:
        return tuple(
            (
                resolution.selected_candidates
                or resolution.candidates
            )[:10]
        )
    if resolution.state == CANDIDATE_SET:
        return tuple(resolution.candidates[:10])
    return ()


def _admitted_database_evidence(
    *,
    resolution: CandidateResolution,
    selected_candidate: ProductCandidate | None,
    product_context: ProductApplicabilityContext | None,
    assembled_chunks: tuple[Any, ...],
) -> list[Any]:
    chunks_by_id = {
        str(chunk.chunk_id): chunk for chunk in assembled_chunks
    }
    packet_visible = "runtime-response-packet" in chunks_by_id
    admitted: dict[int, dict[str, Any]] = {}

    def add(
        candidate: ProductCandidate,
        *,
        content: str,
        fact_ids: tuple[str, ...],
    ) -> None:
        product_id = int(candidate.product_id)
        current = admitted.get(product_id)
        if current is None:
            admitted[product_id] = {
                "candidate": candidate,
                "contents": [content],
                "fact_ids": list(fact_ids),
            }
            return
        if content not in current["contents"]:
            current["contents"].append(content)
        current["fact_ids"] = list(
            dict.fromkeys([*current["fact_ids"], *fact_ids])
        )

    if product_context is not None:
        product_id = int(product_context.read_model_product_id or 0)
        product_chunk = chunks_by_id.get(
            f"product-context-{product_id}"
        )
        if product_chunk is not None:
            context_candidate = (
                selected_candidate
                if selected_candidate is not None
                and int(selected_candidate.product_id) == product_id
                else _candidate_from_cached_context(product_context)
            )
            add(
                context_candidate,
                content=str(product_chunk.text),
                fact_ids=_product_context_fact_ids(product_context),
            )
        elif packet_visible:
            context_candidate = (
                selected_candidate
                if selected_candidate is not None
                and int(selected_candidate.product_id) == product_id
                else _candidate_from_cached_context(product_context)
            )
            packet = _product_context_packet(product_context)
            add(
                context_candidate,
                content=json.dumps(
                    packet,
                    indent=2,
                    sort_keys=True,
                    default=str,
                ),
                fact_ids=_product_context_fact_ids(product_context),
            )

    if packet_visible:
        for candidate in _response_packet_answer_candidates(
            resolution
        ):
            packet = candidate_packet(candidate)
            add(
                candidate,
                content=json.dumps(
                    packet,
                    indent=2,
                    sort_keys=True,
                    default=str,
                ),
                fact_ids=_candidate_packet_fact_ids(
                    candidate,
                    packet,
                ),
            )

    return [
        database_evidence_identity(
            item["candidate"],
            rank=index,
            admitted_fact_ids=tuple(item["fact_ids"]),
            model_visible_content="\n\n".join(item["contents"]),
        )
        for index, item in enumerate(admitted.values())
    ]


def _product_context_fact_ids(
    context: ProductApplicabilityContext,
) -> tuple[str, ...]:
    product_id = int(context.read_model_product_id or 0)
    fields = {
        column
        for column, value in context.database_fields
        if value not in (None, "")
    }
    fields.update(
        field
        for field in (
            "product_id",
            "product_name",
            "brand",
            "manufacturer",
            "model",
            "mpn",
            "sku",
            "upc",
            "product_type",
            "series",
            "fuel_type",
            "variant",
            "model_year",
            "product_generation",
            "description",
        )
        if getattr(context, field, None) not in (None, "")
    )
    return tuple(
        _database_fact_id(product_id, field)
        for field in sorted(fields)
    )


def _candidate_packet_fact_ids(
    candidate: ProductCandidate,
    packet: dict[str, Any],
) -> tuple[str, ...]:
    excluded = {
        "candidate_score",
        "conflicts",
        "identity_status",
        "match_type",
        "matched_field",
        "matched_identifiers",
        "matched_value",
        "score_components",
        "search_depth",
        "search_layer",
        "supporting_match_reasons",
    }
    fields: set[str] = set()
    for field, value in packet.items():
        if field in excluded or value in (None, "", [], {}, ()):
            continue
        if field == "structured_product_context":
            fields.update(str(name) for name in value)
        else:
            fields.add(field)
    return tuple(
        _database_fact_id(candidate.product_id, field)
        for field in sorted(fields)
    )


def _database_fact_id(product_id: int, field: str) -> str:
    normalized = re.sub(
        r"[^a-z0-9]+",
        "_",
        str(field).casefold(),
    ).strip("_")
    return f"db:product:{int(product_id)}/fact/{normalized}"


def _retrieval_query_packet(query: RetrievalQuery) -> dict[str, Any]:
    return {
        "semantic_query_text": query.semantic_query_text,
        "exact_identifier_queries": list(query.exact_identifier_queries),
        "identifier_variants": list(query.identifier_variants),
        "product_facets": [
            {"field": field, "value": value}
            for field, value in query.product_facets
        ],
    }


def _product_context_packet(
    context: ProductApplicabilityContext | None,
) -> dict[str, Any] | None:
    if context is None:
        return None
    return {
        "read_model_product_id": context.read_model_product_id,
        "product_name": context.product_name,
        "brand": context.brand,
        "manufacturer": context.manufacturer,
        "model": context.model,
        "mpn": context.mpn,
        "sku": context.sku,
        "upc": context.upc,
        "product_type": context.product_type,
        "series": context.series,
        "fuel_type": context.fuel_type,
        "variant": context.variant,
        "model_year": context.model_year,
        "product_generation": context.product_generation,
        "description": context.description,
        "database_fields": [
            {"column": column, "value": value}
            for column, value in context.database_fields
        ],
    }


def _rerank_by_applicability(
    retrieval: RankedRetrieval,
    product_context: ProductApplicabilityContext | None,
    needs: InformationNeeds,
    top_k: int,
    *,
    corpus_neighbors: CorpusNeighborIndex | None = None,
    candidate_contexts: tuple[ProductApplicabilityContext, ...] = (),
    configuration_mode: (
        str | PdfConfigurationApplicabilityMode
    ) = DEFAULT_PDF_CONFIGURATION_APPLICABILITY_MODE,
) -> RankedRetrieval:
    candidates = retrieval.candidates or retrieval.chunks
    adjusted: list[RankedChunk] = []
    applicability_rows: list[dict[str, Any]] = []
    for item in candidates:
        chunk = (
            corpus_neighbors.with_document_identity(item.chunk)
            if corpus_neighbors is not None
            else item.chunk
        )
        applicability = _assess_with_candidate_consensus(
            chunk,
            product_context,
            needs,
            query_text=retrieval.query,
            candidate_contexts=candidate_contexts,
            configuration_mode=configuration_mode,
        )
        diagnostic_context = (
            candidate_contexts[0]
            if applicability.applicable
            and product_context is None
            and candidate_contexts
            else product_context
        )
        applicability_rows.append(
            {
                **chunk_applicability_diagnostics(
                    chunk,
                    diagnostic_context,
                    applicability,
                ),
                "rank": item.rank,
                "document": chunk.filename
                or chunk.document_id,
                "relative_path": chunk.relative_path,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "section": chunk.section_path
                or chunk.section_title,
                "vector_score": item.vector_score,
                "identifier_score": item.identifier_score,
                "keyword_score": item.keyword_score,
                "year_score": item.year_score,
                "path_quality_score": item.path_quality_score,
                "applicability_score": (
                    applicability.applicability_score
                ),
                "final_score": item.final_score,
                "matched_identifiers": list(
                    item.matched_identifiers
                ),
                "matched_lexical_terms": list(
                    item.matched_lexical_terms
                ),
                "diagnostic_reason_codes": list(
                    applicability.diagnostic_reason_codes
                ),
                "conflicting_signals": list(
                    applicability.conflicting_signals
                ),
            }
        )
        if not applicability.applicable:
            continue
        adjusted.append(
            RankedChunk(
                chunk=chunk,
                rank=0,
                vector_score=item.vector_score,
                identifier_score=item.identifier_score,
                keyword_score=item.keyword_score,
                year_score=item.year_score,
                path_quality_score=item.path_quality_score,
                final_score=item.final_score + applicability.applicability_score,
                matched_identifiers=item.matched_identifiers,
                matched_lexical_terms=item.matched_lexical_terms,
                channel_provenance=item.channel_provenance,
                fusion_score=item.fusion_score,
            )
        )
    adjusted.sort(key=lambda item: (item.final_score, item.vector_score), reverse=True)
    ranked = tuple(
        RankedChunk(**{**item.__dict__, "rank": index})
        for index, item in enumerate(adjusted, 1)
    )
    selected = ranked[:top_k]
    selected_chunk_ids = {
        item.chunk.chunk_id for item in selected
    }
    for row in applicability_rows:
        row["selected"] = (
            row.get("chunk_id") in selected_chunk_ids
        )
        row["selection_reason"] = (
            "selected after document-applicability reranking"
            if row["selected"]
            else "rejected by document applicability"
            if not row.get("document_applicability")
            else "not selected within the final evidence limit"
        )
    low_confidence = retrieval.low_confidence or not selected
    diagnostics = dict(getattr(retrieval, "diagnostics", {}) or {})
    diagnostics["document_applicability_candidates"] = (
        applicability_rows
    )
    diagnostics["configuration_applicability"] = (
        _configuration_applicability_summary(
            applicability_rows
        )
    )
    return RankedRetrieval(
        query=retrieval.query,
        chunks=selected,
        low_confidence=low_confidence,
        low_confidence_reason="NO_APPLICABLE_DOCUMENT" if not selected else retrieval.low_confidence_reason,
        candidates=ranked,
        diagnostics=diagnostics,
    )


def _candidate_consensus_contexts(
    resolution: CandidateResolution,
    product_context: ProductApplicabilityContext | None,
) -> tuple[ProductApplicabilityContext, ...]:
    if product_context is not None:
        return ()
    candidates = (
        resolution.selected_candidates
        or resolution.candidates
    )
    if len(candidates) < 2:
        return ()
    identifier_sets = [
        set(candidate.matched_identifiers)
        for candidate in candidates
    ]
    if (
        not identifier_sets
        or any(not values for values in identifier_sets)
        or not set.intersection(*identifier_sets)
    ):
        return ()
    return tuple(
        build_product_applicability_context(candidate)
        for candidate in candidates
    )


def _configuration_applicability_summary(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    assessments = [
        (
            row,
            dict(row.get("configuration_applicability") or {}),
        )
        for row in rows
        if row.get("configuration_applicability")
    ]

    def document_record(
        row: dict[str, Any],
        assessment: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "document_id": row.get("document_id"),
            "chunk_id": row.get("chunk_id"),
            "relative_path": row.get("relative_path"),
            "page_start": row.get("page_start"),
            "page_end": row.get("page_end"),
            "assessment": assessment.get("assessment"),
            "reason_codes": assessment.get("reason_codes") or [],
            "evidence_authority": (
                assessment.get("evidence_authority") or []
            ),
            "selected": bool(row.get("selected")),
        }

    mismatches = [
        {
            **document_record(row, assessment),
            "configuration_mismatches": (
                assessment.get("configuration_mismatches") or []
            ),
        }
        for row, assessment in assessments
        if assessment.get("configuration_mismatches")
    ]
    shared = [
        document_record(row, assessment)
        for row, assessment in assessments
        if assessment.get("assessment") == "SHARED_MANUAL_POSSIBLE"
    ]
    explicit = [
        document_record(row, assessment)
        for row, assessment in assessments
        if assessment.get("authoritative_conflict") is True
    ]
    enforce_changes = [
        document_record(row, assessment)
        for row, assessment in assessments
        if assessment.get("enforcement_would_alter_admission") is True
    ]
    actual_changes = [
        document_record(row, assessment)
        for row, assessment in assessments
        if assessment.get("actual_admission_changed") is True
    ]
    useful_rejected = [
        document_record(row, assessment)
        for row, assessment in assessments
        if row.get("selected")
        and assessment.get("enforcement_would_alter_admission") is True
    ]
    multi_alias_documents: dict[str, dict[str, Any]] = {}
    for row, assessment in assessments:
        aliases = tuple(
            assessment.get("canonical_catalog_aliases") or ()
        )
        if len(aliases) < 2:
            continue
        key = str(
            row.get("document_id")
            or row.get("relative_path")
            or row.get("chunk_id")
        )
        multi_alias_documents[key] = {
            "document_id": row.get("document_id"),
            "relative_path": row.get("relative_path"),
            "canonical_catalog_aliases": list(aliases),
        }
    return {
        "mode": next(
            (
                assessment.get("mode")
                for _, assessment in assessments
                if assessment.get("mode")
            ),
            None,
        ),
        "configuration_mismatches_observed": mismatches,
        "shared_manual_possibilities": shared,
        "explicit_configuration_conflicts": explicit,
        "documents_whose_admission_would_change_under_enforce": (
            enforce_changes
        ),
        "documents_whose_admission_actually_changed": actual_changes,
        "useful_evidence_enforcement_would_reject": useful_rejected,
        "canonical_documents_with_multiple_catalog_aliases": list(
            multi_alias_documents.values()
        ),
    }


def _assess_with_candidate_consensus(
    chunk: Chunk,
    product_context: ProductApplicabilityContext | None,
    needs: InformationNeeds,
    *,
    query_text: str,
    candidate_contexts: tuple[ProductApplicabilityContext, ...],
    configuration_mode: (
        str | PdfConfigurationApplicabilityMode
    ),
) -> DocumentApplicability:
    if product_context is not None or not candidate_contexts:
        return assess_document_applicability(
            chunk,
            product_context,
            needs,
            query_text=query_text,
            configuration_mode=configuration_mode,
        )
    assessments = tuple(
        assess_document_applicability(
            chunk,
            context,
            needs,
            query_text=query_text,
            configuration_mode=configuration_mode,
        )
        for context in candidate_contexts
    )
    candidate_outcomes = [
        {
            "product_id": context.read_model_product_id,
            "status": assessment.classification,
            "eligibility": assessment.eligibility,
            "applicable": assessment.applicable,
            "positive_evidence": list(assessment.matched_fields),
            "conflict_evidence": list(
                dict.fromkeys(
                    (
                        *assessment.conflicting_fields,
                        *assessment.exclusion_reasons,
                    )
                )
            ),
            "reason_codes": list(
                assessment.diagnostic_reason_codes
            ),
        }
        for context, assessment in zip(candidate_contexts, assessments)
    ]
    subset_applicable = [
        context.read_model_product_id
        for context, assessment in zip(candidate_contexts, assessments)
        if assessment.applicable
    ]
    consensus = bool(
        assessments and all(item.applicable for item in assessments)
    )
    consensus_diagnostics = {
        "document_id": chunk.document_id,
        "candidate_applicability": candidate_outcomes,
        "applied_to_all_candidates": consensus,
        "applied_to_subset": bool(subset_applicable) and not consensus,
        "applied_to_none": not subset_applicable,
        "consensus": consensus,
        "subset_applicable_product_ids": subset_applicable,
        "excluded_by_consensus_only": False,
    }
    if consensus:
        weakest = min(
            assessments,
            key=lambda item: item.applicability_score,
        )
        return replace(
            weakest,
            classification="CANDIDATE_SET_CONSENSUS",
            diagnostic_reason_codes=tuple(
                dict.fromkeys(
                    (
                        *weakest.diagnostic_reason_codes,
                        "CANDIDATE_SET_APPLICABILITY_CONSENSUS",
                    )
                )
            ),
            candidate_consensus=consensus_diagnostics,
        )
    aggregate = assess_document_applicability(
        chunk,
        None,
        needs,
        query_text=query_text,
        configuration_mode=configuration_mode,
    )
    consensus_diagnostics["excluded_by_consensus_only"] = bool(
        subset_applicable and not aggregate.applicable
    )
    return replace(
        aggregate,
        candidate_consensus=consensus_diagnostics,
    )


def _applicability_diagnostics(
    retrieval: RankedRetrieval,
    product_context: ProductApplicabilityContext | None,
    needs: InformationNeeds,
) -> list[dict[str, Any]]:
    preserved = dict(
        getattr(retrieval, "diagnostics", {}) or {}
    ).get("document_applicability_candidates")
    if isinstance(preserved, list):
        return [dict(item) for item in preserved]
    rows = []
    for item in (retrieval.candidates or retrieval.chunks)[:10]:
        document = assess_document_applicability(item.chunk, product_context, needs)
        rows.append(
            {
                **chunk_applicability_diagnostics(item.chunk, product_context, document),
                "rank": item.rank,
                "document": item.chunk.filename or item.chunk.document_id,
                "relative_path": item.chunk.relative_path,
                "page_start": item.chunk.page_start,
                "page_end": item.chunk.page_end,
                "section": item.chunk.section_path or item.chunk.section_title,
                "vector_score": item.vector_score,
                "identifier_score": item.identifier_score,
                "keyword_score": item.keyword_score,
                "year_score": item.year_score,
                "path_quality_score": item.path_quality_score,
                "applicability_score": document.applicability_score,
                "final_score": item.final_score,
                "matched_identifiers": list(item.matched_identifiers),
                "matched_lexical_terms": list(item.matched_lexical_terms),
                "selected": item in retrieval.chunks,
                "selection_reason": (
                    "selected after document-applicability reranking"
                    if item in retrieval.chunks
                    else "not selected within the final evidence limit"
                ),
                "diagnostic_reason_codes": list(document.diagnostic_reason_codes),
                "conflicting_signals": list(document.conflicting_signals),
            }
        )
    return rows


def _product_context_diagnostics(context: ProductApplicabilityContext | None) -> dict[str, Any] | None:
    if context is None:
        return None
    return {
        "read_model_product_id": context.read_model_product_id,
        "product_name": context.product_name,
        "model": context.model,
        "mpn": context.mpn,
        "sku": context.sku,
        "upc": context.upc,
        "brand": context.brand,
        "manufacturer": context.manufacturer,
        "product_type": context.product_type,
        "series": context.series,
        "fuel_type": context.fuel_type,
        "status": dict(context.approved_general_facts).get("product_status"),
        "production_start_year": context.production_start_year,
        "production_end_year": context.production_end_year,
        "product_generation": context.product_generation,
        "description": context.description,
        "categories": list(context.categories),
        "ordered_category_paths": [
            {
                "category_ids": list(path.category_ids),
                "path": list(path.path),
                "leaf_category_id": path.leaf_category_id,
                "parent_category_id": path.parent_category_id,
                "canonical": path.canonical,
                "source_type": path.source_type,
                "store_scope": path.store_scope,
                "status": path.status,
            }
            for path in context.business_category_paths
        ],
        "category_metrics": {
            "category_context_present": bool(context.categories),
            "ordered_multi_node_path_present": any(len(path.path) > 1 for path in context.business_category_paths),
            "parent_category_ids_present": any(path.parent_category_id is not None for path in context.business_category_paths),
            "full_root_to_leaf_hierarchy_present": any(len(path.path) > 1 and path.category_ids for path in context.business_category_paths),
        },
        "filters": list(context.filters),
        "catalog_attributes": [{"name": name, "value": value} for name, value in context.attributes],
        "database_fields": [
            {"column": column, "value": value}
            for column, value in context.database_fields
        ],
        "derived_relationship_context": [
            {
                "evidence_type": item.evidence_type,
                "name": item.name,
                "value": item.value,
                "source_type": item.source_type,
                "source_reference": item.source_reference,
                "qualification": item.qualification,
            }
            for item in context.derived_relationship_context
        ],
        "explicit_product_relationships": [
            {
                "relationship_type": relationship.relationship_type,
                "subject_product_id": relationship.subject_product_id,
                "related_product_id": relationship.related_product_id,
                "related_identifier": relationship.related_identifier,
                "related_description": relationship.related_description,
                "source_type": relationship.source_type,
                "source_reference": relationship.source_reference,
                "qualification": relationship.qualification,
            }
            for relationship in context.explicit_product_relationships
        ],
        "approved_general_fields": [column for column, _ in context.approved_general_facts],
        "source_filenames": list(context.source_filenames),
        "source_paths": list(context.source_paths),
        "unresolved_applicability_fields": list(context.unresolved_applicability_fields),
        "enrichment_omissions": [
            {"field": field, "reason": reason}
            for field, reason in context.enrichment_omissions
        ],
    }


_MOUNT_OR_BASE = re.compile(r"\b(?:mount|mounting|base|post)\b", re.I)
_TOPIC_LABELS = {
    "gas_pressure": "burner pressure",
    "clearances": "clearance",
    "cutout": "cutout dimensions",
    "dimensions": "dimensions",
    "fuel_conversion": "fuel conversion",
    "installation": "installation",
    "maintenance": "maintenance",
    "startup": "ignition or startup",
    "troubleshooting": "troubleshooting",
    "wiring": "wiring",
    "electrical": "electrical requirements",
    "ventilation": "ventilation",
}
_RELATED_APPLIANCE_TOPICS = {
    "gas_pressure",
    "fuel_conversion",
    "startup",
    "shutdown",
    "troubleshooting",
    "maintenance",
    "service",
    "wiring",
    "electrical",
    "ventilation",
    "clearances",
    "cutout",
    "dimensions",
    "model_specific_procedure",
    "technical_specification",
}


def _relationship_applicability(
    question: str,
    needs: InformationNeeds,
    context: ProductApplicabilityContext | None,
) -> dict[str, Any]:
    if context is None:
        return {
            "resolved_subject": {},
            "subject_type": "",
            "requested_topic": _requested_topic(needs),
            "topic_owner_type": "",
            "topic_directly_applies": False,
            "related_product_required": False,
            "related_product_scope": [],
            "missing_discriminators": [],
            "expected_behavior": "CLARIFY_PRODUCT",
        }
    subject = {
        "product_id": context.read_model_product_id,
        "product_name": context.product_name,
        "model": context.model,
        "mpn": context.mpn,
    }
    subject_type = context.product_type or ""
    is_supporting_product = bool(_MOUNT_OR_BASE.search(subject_type))
    technical_topics = tuple(needs.technical)
    requested_topic = _requested_topic(needs)
    active_subject = context.model or context.mpn or context.product_name or ""
    if not technical_topics:
        return {
            "resolved_subject": subject,
            "active_subject": active_subject,
            "subject_type": subject_type,
            "requested_topic": "identity",
            "topic_owner_type": subject_type,
            "topic_directly_applies": True,
            "related_product_required": False,
            "related_product_scope": _related_product_scope(context),
            "missing_discriminators": [],
            "expected_behavior": (
                "EXPLAIN_RELATIONSHIP"
                if is_supporting_product
                else "DIRECT_ANSWER"
            ),
        }
    mismatch = is_supporting_product and any(
        topic in _RELATED_APPLIANCE_TOPICS for topic in technical_topics
    )
    if mismatch:
        gas_configuration = "gas_pressure" in technical_topics or bool(
            re.search(r"\b(?:burner|gas pressure|manifold pressure)\b", question, re.I)
        )
        missing = ["installed grill model or series"]
        if gas_configuration:
            missing.append("fuel type")
        return {
            "resolved_subject": subject,
            "active_subject": active_subject,
            "subject_type": subject_type,
            "requested_topic": requested_topic,
            "topic_owner_type": "grill appliance",
            "topic_directly_applies": False,
            "related_product_required": True,
            "related_product_scope": _related_product_scope(context),
            "missing_discriminators": missing,
            "expected_behavior": (
                "CLARIFY_CONFIGURATION"
                if gas_configuration
                else "CLARIFY_PRODUCT"
            ),
        }
    return {
        "resolved_subject": subject,
        "active_subject": active_subject,
        "subject_type": subject_type,
        "requested_topic": requested_topic,
        "topic_owner_type": subject_type,
        "topic_directly_applies": True,
        "related_product_required": False,
        "related_product_scope": [],
        "missing_discriminators": [],
        "expected_behavior": "DIRECT_ANSWER",
    }


def _requested_topic(needs: InformationNeeds) -> str:
    if not needs.technical:
        return "identity"
    for need in needs.technical:
        if need in _TOPIC_LABELS:
            return _TOPIC_LABELS[need]
    return str(needs.technical[0]).replace("_", " ")


def _related_product_scope(context: ProductApplicabilityContext) -> list[str]:
    values: list[str] = []
    for name, value in context.attributes:
        if re.search(r"\bgrill models?\b", name, re.I) and value:
            values.append(value)
    for relationship in context.explicit_product_relationships:
        value = relationship.related_identifier or relationship.related_description
        if value:
            values.append(value)
    return list(dict.fromkeys(values))
