from __future__ import annotations

"""V1.9.40 additive multi-domain retrieval over frozen V1.9.39 artifacts.

V1.9.39 is intentionally not modified.  This development candidate removes
the table-only runtime projection while preserving the governed canonical IR,
multi-view records, vectors, table context builder, RRF implementation, and
citation pipeline.
"""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence

from src.evidence_models import pdf_evidence_identity
from src.models import Chunk
from src.retrieval import RankedChunk, RankedRetrieval
from src.runtime_contracts import (
    CANONICAL_CANDIDATE_ARCHITECTURE,
    ControlledRetrievalResult,
    PdfEvidenceResult,
    RetrievalQuery,
    UserQuestion,
)

from .adaptive_multisource_v1_7 import (
    SOURCE_DENSE,
    SOURCE_LEXICAL,
    fuse_rankings,
    structural_representation,
)
from .canonical_direct_rag_v1_9_38 import (
    CanonicalDirectRagComposition,
    _context_chunks as _table_context_chunks,
    _json_value,
)
from .canonical_direct_rag_v1_9_39 import (
    INDEX_INTEGRITY_FAILURE,
    StructuralIndexIntegrityError,
    VALID_NO_ELIGIBLE_EVIDENCE,
    CanonicalDirectRagRetrievalService as V1939RetrievalService,
    CanonicalIRAuthorityV1939,
    _stable_hash,
    audit_structural_index,
    build_canonical_direct_rag_composition as build_v1_9_39_composition,
)
from .canonical_ir_v1_9_6 import CanonicalIdentityType
from .local_reranker_v1_8 import evidence_representation
from .model import Node, NodeType
from .multiview_v1_9 import (
    AGGREGATION_MAX_VIEW,
    collapse_view_scores,
    lexical_view_scores,
)
from .scoped_evidence_v1_5 import EvidenceType


RUNTIME_VERSION = "canonical-direct-rag.v1.9.40"
CONTEXT_SCHEMA_VERSION = "canonical-structural-context.v1.9.40"
CONTEXT_K = 3
FUSION_POOL = 100
FUSION_LIMIT = 20
UNEXPECTED_RETRIEVAL_EMPTY = "UNEXPECTED_RETRIEVAL_EMPTY"
MULTI_TARGET_AUTHORITY_CONTRACT = "per-explicit-target-provenance-precedence.v1"

SUPPORTED_DENSE_NODE_TYPES = frozenset(
    {
        NodeType.TABLE_ROW,
        NodeType.PROCEDURE,
        NodeType.ADMONITION,
        NodeType.PARAGRAPH,
        NodeType.SECTION,
    }
)
NODE_EVIDENCE_TYPE = {
    NodeType.TABLE_ROW: EvidenceType.TABLE_SPEC.value,
    NodeType.PROCEDURE: EvidenceType.PROCEDURE.value,
    NodeType.ADMONITION: EvidenceType.WARNING_ADMONITION.value,
    NodeType.PARAGRAPH: EvidenceType.NARRATIVE.value,
    NodeType.SECTION: EvidenceType.NARRATIVE.value,
    NodeType.FIGURE: EvidenceType.FIGURE_OCR.value,
}


class UnexpectedRetrievalEmptyError(RuntimeError):
    """Eligible authority existed but the multi-domain runtime found nothing."""

    def __init__(self, diagnostics: Mapping[str, Any]):
        super().__init__(f"V1_9_40_{UNEXPECTED_RETRIEVAL_EMPTY}")
        self.diagnostics = dict(diagnostics)


def _identifier_diagnostics(resolution_dict: Mapping[str, Any]) -> dict[str, Any]:
    target = dict(resolution_dict.get("query_target_identity") or {})
    return {
        "raw_literals": list(target.get("raw_literals") or ()),
        "canonical_target_forms": list(
            target.get("canonical_target_forms") or ()
        ),
        "document_coverage_forms": list(
            target.get("document_coverage_forms") or ()
        ),
        "configuration_forms": list(target.get("configuration_forms") or ()),
        "multi_target": bool(target.get("multi_target")),
    }


def _valid_empty_pdf(
    query: RetrievalQuery,
    *,
    started: float,
    resolution: Any,
) -> PdfEvidenceResult:
    resolution_dict = _json_value(resolution.to_dict())
    diagnostics = {
        "schema": "canonical-structural-retrieval.v1.9.40",
        "runtime_version": RUNTIME_VERSION,
        "query": query.semantic_query_text,
        "query_normalization": "NFKC_CASEFOLD_ALNUM_TOKENIZATION",
        "identifiers": _identifier_diagnostics(resolution_dict),
        "authority": resolution_dict,
        "empty_retrieval_classification": VALID_NO_ELIGIBLE_EVIDENCE,
        "lexical_views": [],
        "dense_views": [],
        "collapsed_lexical_ids": [],
        "collapsed_dense_ids": [],
        "fused_candidates": [],
        "selected_canonical_evidence_ids": [],
        "selected_chunk_ids": [],
        "selected_table_ids": [],
        "embedding_calls": 0,
        "qdrant_calls": 0,
        "duration_ms": int((perf_counter() - started) * 1000),
    }
    retrieval = RankedRetrieval(
        query=query.semantic_query_text,
        chunks=(),
        low_confidence=True,
        low_confidence_reason=VALID_NO_ELIGIBLE_EVIDENCE,
        candidates=(),
        diagnostics=diagnostics,
    )
    return PdfEvidenceResult(
        query=query,
        retrieval=retrieval,
        duration_ms=diagnostics["duration_ms"],
        diagnostics=diagnostics,
    )


class CanonicalIRAuthorityV1940(CanonicalIRAuthorityV1939):
    """Preserve strongest exact owners independently for every query target."""

    def resolve(
        self,
        query: str,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> Any:
        original = super().resolve(query, runtime_context)
        target = self.parse_query_target(query)
        if not target.multi_target or not target.canonical_target_forms:
            return original

        per_target: dict[str, list[tuple[str, Any, int]]] = {}
        for wanted in target.canonical_target_forms:
            matches: list[tuple[str, Any, int]] = []
            for document_id, identities in self.identities_by_document.items():
                if not self._satisfies_explicit_constraints(document_id, target):
                    continue
                for identity in identities:
                    if identity.identity_type not in {
                        CanonicalIdentityType.MODEL.value,
                        CanonicalIdentityType.PART_NUMBER.value,
                    }:
                        continue
                    forms = {
                        "".join(character for character in value.casefold() if character.isalnum())
                        for value in identity.normalized_forms
                    }
                    if wanted not in forms:
                        continue
                    strength = min(
                        (
                            value.precedence
                            for value in (identity.model, identity.part_number)
                            if value is not None
                        ),
                        default=99,
                    )
                    matches.append((document_id, identity, strength))
            if matches:
                best = min(row[2] for row in matches)
                per_target[wanted] = [row for row in matches if row[2] == best]

        if set(per_target) != set(target.canonical_target_forms):
            return original

        matches_by_document: dict[str, list[Any]] = {}
        for rows in per_target.values():
            for document_id, identity, _ in rows:
                matches_by_document.setdefault(document_id, []).append(identity)
        eligible = tuple(sorted(matches_by_document))
        if not eligible:
            return original
        return self._resolution(
            eligible,
            target,
            2,
            "CANONICAL_QUERY_MULTI_TARGET_EXACT+PER_TARGET_PROVENANCE_PRECEDENCE",
            matches_by_document,
        )


def audit_multidomain_index(
    composition: CanonicalDirectRagComposition,
) -> dict[str, Any]:
    """Close every supported canonical node through view, record, and vector."""

    base = audit_structural_index(composition)
    records = {row.view_id: row for row in composition.dense_index.records}
    vector_count = int(composition.dense_index.vectors.shape[0])
    nodes = {
        node.node_id: node
        for node in composition.graph.nodes.values()
        if node.node_type in SUPPORTED_DENSE_NODE_TYPES and node.retrieval_eligible
    }
    views_by_node: dict[str, list[Any]] = {}
    for view in composition.dense_view_map.values():
        views_by_node.setdefault(view.canonical_node_id, []).append(view)

    missing_views = sorted(set(nodes).difference(views_by_node))
    missing_records: list[str] = []
    invalid_vectors: list[str] = []
    domain_counts: dict[str, dict[str, int]] = {}
    for node_type in sorted(SUPPORTED_DENSE_NODE_TYPES, key=lambda value: value.value):
        typed_nodes = [node for node in nodes.values() if node.node_type == node_type]
        typed_views = [
            view
            for node in typed_nodes
            for view in views_by_node.get(node.node_id, ())
        ]
        typed_records = [records[view.view_id] for view in typed_views if view.view_id in records]
        domain_counts[node_type.value] = {
            "canonical_nodes": len(typed_nodes),
            "retrieval_views": len(typed_views),
            "embedding_records": len(typed_records),
            "vector_records": sum(
                0 <= int(record.vector_index) < vector_count for record in typed_records
            ),
        }
        missing_records.extend(
            view.view_id for view in typed_views if view.view_id not in records
        )
        invalid_vectors.extend(
            record.view_id
            for record in typed_records
            if not 0 <= int(record.vector_index) < vector_count
        )

    mismatches = {
        "canonical_node_without_view": missing_views,
        "view_without_embedding_record": sorted(set(missing_records)),
        "embedding_record_without_vector": sorted(set(invalid_vectors)),
    }
    return {
        "schema": "canonical-multidomain-index-audit.v1.9.40",
        "status": "PASS" if base["status"] == "PASS" and not any(mismatches.values()) else "FAIL",
        "base_v1_9_39_audit": base,
        "domain_counts": domain_counts,
        "mismatches": mismatches,
    }


def build_canonical_direct_rag_composition(
    root: Path,
) -> CanonicalDirectRagComposition:
    base = build_v1_9_39_composition(root)
    audit = audit_multidomain_index(base)
    if audit["status"] != "PASS":
        raise StructuralIndexIntegrityError(
            f"V1_9_40_{INDEX_INTEGRITY_FAILURE}:{_stable_hash(audit['mismatches'])}"
        )
    identity = dict(base.artifact_identity)
    identity.update(
        {
            "schema": "canonical-direct-rag-artifacts.v1.9.40",
            "parent_v1_9_39_fingerprint": base.artifact_identity["fingerprint"],
            "multi_target_authority_contract": MULTI_TARGET_AUTHORITY_CONTRACT,
            "multidomain_index_integrity": audit,
            "retrieval_contract": "additive-canonical-multidomain-rrf.v1",
        }
    )
    identity["fingerprint"] = _stable_hash(identity)
    return replace(
        base,
        authority=CanonicalIRAuthorityV1940(base.ir),
        artifact_identity=identity,
    )


def evidence_domain_metadata(node: Node) -> dict[str, Any]:
    text = " ".join(
        (
            node.source_text,
            node.retrieval_text,
            " ".join(node.section_ancestry),
        )
    ).casefold()
    tags = []
    signals = {
        "specifications": ("specification", "rating", "pressure", "voltage", "btu"),
        "dimensions": ("dimension", "width", "height", "depth", "clearance"),
        "identifiers": ("model", "part number", "serial"),
        "compatibility": ("compatible", "intended for", "fits", "use with"),
        "troubleshooting": ("troubleshooting", "problem", "possible cause", "correction"),
        "enumerations": ("following", "includes", "available", "models"),
    }
    for tag, needles in signals.items():
        if any(needle in text for needle in needles):
            tags.append(tag)
    if node.node_type == NodeType.PROCEDURE:
        tags.append("procedures")
    if node.node_type == NodeType.ADMONITION:
        tags.append("warnings_cautions")
    if node.node_type in {NodeType.PARAGRAPH, NodeType.SECTION}:
        tags.append("section_text")
    if node.node_type == NodeType.TABLE_ROW:
        tags.append("table_rows")
    return {
        "evidence_type": NODE_EVIDENCE_TYPE.get(node.node_type, node.node_type.value),
        "node_type": node.node_type.value,
        "domain_tags": sorted(set(tags)),
    }


def _non_table_chunk(graph: Any, node: Node) -> Chunk:
    domain = evidence_domain_metadata(node)
    page = int(node.page_number or 1)
    filename = Path(node.relative_path).name or node.document_id
    representation = structural_representation(graph, node)
    return Chunk(
        chunk_id=f"canonical-structural-{node.node_type.value.casefold()}:{node.node_id}",
        text=(
            "[PDF TECHNICAL EVIDENCE]\n"
            "Source class: governed canonical structural non-table evidence\n"
            f"Document: {filename}\n"
            f"Document ID: {node.document_id}\n"
            f"Path: {node.relative_path}\n"
            f"Page: {page}\n"
            f"Canonical evidence ID: {node.node_id}\n"
            f"Evidence type: {domain['evidence_type']}\n"
            f"Evidence-domain tags: {', '.join(domain['domain_tags']) or 'none'}\n"
            f"Section: {' > '.join(node.section_ancestry) or 'unknown'}\n\n"
            f"Exact structural evidence:\n{representation}"
        ),
        page_start=page,
        page_end=page,
        filename=filename,
        document_id=node.document_id,
        relative_path=node.relative_path,
        source_path=node.relative_path,
        content_type="technical_evidence",
        section_path=" > ".join(node.section_ancestry),
        chunk_kind=f"canonical_structural_{node.node_type.value.casefold()}",
        has_warning=node.node_type == NodeType.ADMONITION,
        has_caution=node.node_type == NodeType.ADMONITION,
        has_installation_step=node.node_type == NodeType.PROCEDURE,
        has_dimensions="dimensions" in domain["domain_tags"],
        has_compatibility="compatibility" in domain["domain_tags"],
    )


def _round_robin_documents(
    ordered_ids: Sequence[str],
    *,
    composition: CanonicalDirectRagComposition,
    limit: int,
    diversify: bool,
) -> list[str]:
    if not diversify:
        return list(ordered_ids[:limit])
    first: list[str] = []
    later: list[str] = []
    seen_documents: set[str] = set()
    for node_id in ordered_ids:
        document_id = composition.graph.nodes[node_id].document_id
        if document_id not in seen_documents:
            first.append(node_id)
            seen_documents.add(document_id)
        else:
            later.append(node_id)
    return [*first, *later][:limit]


def _context_chunks(
    composition: CanonicalDirectRagComposition,
    *,
    query: str,
    order: Sequence[str],
) -> tuple[Chunk, ...]:
    table_ids = [
        node_id
        for node_id in order
        if composition.graph.nodes[node_id].node_type == NodeType.TABLE_ROW
    ]
    table_chunks = (
        _table_context_chunks(composition, query=query, order=table_ids)
        if table_ids
        else ()
    )
    table_by_id = {
        chunk.structured_tables[0].table_id: chunk
        for chunk in table_chunks
        if chunk.structured_tables
    }
    chunks: list[Chunk] = []
    seen: set[str] = set()
    for node_id in order:
        node = composition.graph.nodes[node_id]
        if node.node_type == NodeType.TABLE_ROW:
            table_id = str(node.attributes.get("table_id") or "")
            chunk = table_by_id.get(table_id)
            if chunk is None:
                continue
        else:
            chunk = _non_table_chunk(composition.graph, node)
        if chunk.chunk_id not in seen:
            chunks.append(chunk)
            seen.add(chunk.chunk_id)
    return tuple(chunks)


class CanonicalStructuralRetrievalAdapter:
    """One-query-embedding additive retrieval over every governed domain."""

    def __init__(self, embedding: Any, composition: CanonicalDirectRagComposition):
        self.embedding = embedding
        self.composition = composition

    def retrieve(
        self,
        query: RetrievalQuery,
        *,
        top_k: int = CONTEXT_K,
        product_context: Any | None = None,
    ) -> PdfEvidenceResult:
        del product_context
        started = perf_counter()
        literal = query.semantic_query_text
        resolution = self.composition.authority.resolve(literal, {})
        resolution_dict = _json_value(resolution.to_dict())
        eligible = set(resolution.eligible_document_ids)
        if not eligible:
            return _valid_empty_pdf(query, started=started, resolution=resolution)

        eligible_views = {
            view_id: view
            for view_id, view in self.composition.dense_view_map.items()
            if view.document_id in eligible
            and NodeType(view.node_type) in SUPPORTED_DENSE_NODE_TYPES
        }
        if not eligible_views:
            diagnostics = {
                "schema": "canonical-structural-retrieval.v1.9.40",
                "runtime_version": RUNTIME_VERSION,
                "query": literal,
                "identifiers": _identifier_diagnostics(resolution_dict),
                "authority": resolution_dict,
                "empty_retrieval_classification": UNEXPECTED_RETRIEVAL_EMPTY,
                "first_empty_stage": "MULTIDOMAIN_ELIGIBLE_VIEW_FILTER",
            }
            raise UnexpectedRetrievalEmptyError(diagnostics)

        lexical_raw = lexical_view_scores(literal, eligible_views.values())
        lexical_ids, lexical_metadata = collapse_view_scores(
            scored_views=lexical_raw,
            view_map=eligible_views,
            aggregation=AGGREGATION_MAX_VIEW,
        )
        vector = self.embedding.embed_query(literal)
        dense_raw = self.composition.dense_index.search(
            vector,
            document_ids=eligible,
            node_types=set(SUPPORTED_DENSE_NODE_TYPES),
        )
        dense_ids, dense_metadata = collapse_view_scores(
            scored_views=dense_raw,
            view_map=eligible_views,
            aggregation=AGGREGATION_MAX_VIEW,
        )
        fused = [
            row.to_dict()
            for row in fuse_rankings(
                graph=self.composition.graph,
                query=literal,
                selected_tier=int(resolution.priority),
                rankings={
                    SOURCE_LEXICAL: lexical_ids[:FUSION_POOL],
                    SOURCE_DENSE: dense_ids[:FUSION_POOL],
                },
                mode="RRF",
                limit=FUSION_LIMIT,
            )
        ]
        post_filter = [
            row
            for row in fused
            if row["document_id"] in eligible
            and self.composition.graph.nodes[row["node_id"]].retrieval_eligible
        ]
        if not post_filter:
            diagnostics = {
                "schema": "canonical-structural-retrieval.v1.9.40",
                "runtime_version": RUNTIME_VERSION,
                "query": literal,
                "identifiers": _identifier_diagnostics(resolution_dict),
                "authority": resolution_dict,
                "empty_retrieval_classification": UNEXPECTED_RETRIEVAL_EMPTY,
                "first_empty_stage": "POST_APPLICABILITY_FILTER",
            }
            raise UnexpectedRetrievalEmptyError(diagnostics)

        nodes = [self.composition.graph.nodes[row["node_id"]] for row in post_filter]
        reranker_scores, reranker_latency = self.composition.reranker.score(
            literal,
            [evidence_representation(self.composition.graph, node) for node in nodes],
        )
        scored = list(zip(post_filter, reranker_scores))
        scored.sort(
            key=lambda value: (
                -int(bool(value[0].get("exact_identifier_match"))),
                -float(value[1]),
                int(value[0].get("fusion_rank") or 1_000_000),
                str(value[0]["node_id"]),
            )
        )
        reranked_ids = [str(row["node_id"]) for row, _ in scored]
        target = resolution_dict.get("query_target_identity") or {}
        selected_ids = _round_robin_documents(
            reranked_ids,
            composition=self.composition,
            limit=max(1, min(int(top_k), CONTEXT_K)),
            diversify=bool(target.get("multi_target")),
        )
        chunks = _context_chunks(
            self.composition,
            query=literal,
            order=selected_ids,
        )
        if not chunks:
            diagnostics = {
                "schema": "canonical-structural-retrieval.v1.9.40",
                "runtime_version": RUNTIME_VERSION,
                "query": literal,
                "identifiers": _identifier_diagnostics(resolution_dict),
                "authority": resolution_dict,
                "empty_retrieval_classification": UNEXPECTED_RETRIEVAL_EMPTY,
                "first_empty_stage": "STRUCTURAL_CONTEXT_ASSEMBLY",
            }
            raise UnexpectedRetrievalEmptyError(diagnostics)

        score_by_id = {str(row["node_id"]): float(score) for row, score in scored}
        fused_by_id = {str(row["node_id"]): row for row in post_filter}
        ranked: list[RankedChunk] = []
        for rank, chunk in enumerate(chunks, 1):
            node_id = chunk.chunk_id.rsplit(":", 1)[-1]
            if chunk.structured_tables:
                table_id = chunk.structured_tables[0].table_id
                table_rows = [
                    value
                    for value in selected_ids
                    if str(self.composition.graph.nodes[value].attributes.get("table_id") or "")
                    == table_id
                ]
                node_id = table_rows[0] if table_rows else node_id
            fused_row = fused_by_id.get(node_id, {})
            lexical_rank = fused_row.get("lexical_rank")
            dense_rank = fused_row.get("dense_rank")
            ranked.append(
                RankedChunk(
                    chunk=chunk,
                    rank=rank,
                    vector_score=float(
                        dense_metadata.get(node_id, {}).get("aggregate_score") or 0.0
                    ),
                    identifier_score=float(bool(fused_row.get("exact_identifier_match"))),
                    keyword_score=(1.0 / float(lexical_rank) if lexical_rank else 0.0),
                    year_score=0.0,
                    path_quality_score=0.0,
                    final_score=score_by_id.get(node_id, 0.0),
                    matched_identifiers=query.exact_identifier_queries,
                    channel_provenance=(
                        {"channel": "canonical_lexical", "rank": lexical_rank},
                        {"channel": "dense_structural_view", "rank": dense_rank},
                    ),
                    fusion_score=float(fused_row.get("fusion_score") or 0.0),
                )
            )

        candidate_rows = []
        for row, reranker_score in scored:
            node_id = str(row["node_id"])
            node = self.composition.graph.nodes[node_id]
            lexical_meta = lexical_metadata.get(node_id, {})
            dense_meta = dense_metadata.get(node_id, {})
            source_node_ids = sorted(
                {
                    source_id
                    for view in eligible_views.values()
                    if view.canonical_node_id == node_id
                    for source_id in view.source_node_ids
                }
            )
            candidate_rows.append(
                {
                    **row,
                    "canonical_evidence_id": node_id,
                    "retrieval_view_ids": {
                        "lexical": lexical_meta.get("best_view_id"),
                        "dense": dense_meta.get("best_view_id"),
                    },
                    "source_node_ids": source_node_ids,
                    "page": node.page_number,
                    "section": list(node.section_ancestry),
                    "owner": node.document_id,
                    "source_provenance": _json_value(node.source_provenance),
                    "evidence_domain": evidence_domain_metadata(node),
                    "reranker_score": float(reranker_score),
                }
            )

        diagnostics = {
            "schema": "canonical-structural-retrieval.v1.9.40",
            "runtime_version": RUNTIME_VERSION,
            "query": literal,
            "query_normalization": "NFKC_CASEFOLD_ALNUM_TOKENIZATION",
            "identifiers": _identifier_diagnostics(resolution_dict),
            "authority": resolution_dict,
            "empty_retrieval_classification": None,
            "lexical_candidate_count": len(lexical_ids),
            "dense_candidate_count": len(dense_ids),
            "table_candidate_count": sum(
                self.composition.graph.nodes[row["node_id"]].node_type
                == NodeType.TABLE_ROW
                for row in post_filter
            ),
            "non_table_candidate_count": sum(
                self.composition.graph.nodes[row["node_id"]].node_type
                != NodeType.TABLE_ROW
                for row in post_filter
            ),
            "fusion_candidate_count": len(fused),
            "post_filter_count": len(post_filter),
            "context_count": len(chunks),
            "lexical_views": [
                {"view_id": view_id, "score": float(score)}
                for view_id, score in lexical_raw[:FUSION_POOL]
            ],
            "dense_views": [
                {"view_id": view_id, "score": float(score)}
                for view_id, score in dense_raw[:FUSION_POOL]
            ],
            "collapsed_lexical_ids": lexical_ids[:FUSION_POOL],
            "collapsed_dense_ids": dense_ids[:FUSION_POOL],
            "fused_candidates": _json_value(candidate_rows),
            "selected_canonical_evidence_ids": selected_ids,
            "selected_chunk_ids": [item.chunk.chunk_id for item in ranked],
            "selected_table_ids": [
                item.chunk.structured_tables[0].table_id
                for item in ranked
                if item.chunk.structured_tables
            ],
            "reranker": {
                "ordered_candidate_ids": reranked_ids,
                "latency_ms": reranker_latency,
                "depth": len(scored),
            },
            "context_k": CONTEXT_K,
            "fusion_limit": FUSION_LIMIT,
            "aggregation": AGGREGATION_MAX_VIEW,
            "embedding_calls": 1,
            "qdrant_calls": 0,
            "duration_ms": int((perf_counter() - started) * 1000),
        }
        retrieval = RankedRetrieval(
            query=literal,
            chunks=tuple(ranked),
            low_confidence=False,
            candidates=tuple(ranked),
            diagnostics=diagnostics,
        )
        return PdfEvidenceResult(
            query=query,
            retrieval=retrieval,
            duration_ms=diagnostics["duration_ms"],
            diagnostics=diagnostics,
        )


class CanonicalDirectRagRetrievalService(V1939RetrievalService):
    """V1.9.40 service wrapper with canonical occurrence source identities."""

    def __init__(
        self,
        *,
        embedding: Any,
        composition: CanonicalDirectRagComposition,
    ) -> None:
        super().__init__(embedding=embedding, composition=composition)
        self.pdf_evidence = CanonicalStructuralRetrievalAdapter(embedding, composition)
        self.readiness = {
            **dict(self.readiness),
            "schema": "canonical-direct-rag-readiness.v1.9.40",
            "architecture": CANONICAL_CANDIDATE_ARCHITECTURE,
            "runtime_version": RUNTIME_VERSION,
            "artifact_fingerprint": composition.artifact_identity["fingerprint"],
            "multidomain_index_integrity": composition.artifact_identity.get(
                "multidomain_index_integrity"
            ),
        }

    def retrieve(self, question: UserQuestion | str, **kwargs: Any) -> ControlledRetrievalResult:
        result = super().retrieve(question, **kwargs)
        diagnostics = _json_value(result.diagnostics)
        canonical = diagnostics["controlled_discovery"]["canonical_candidate"]
        canonical["runtime_version"] = RUNTIME_VERSION
        canonical["evidence_domain_contract"] = "additive-multidomain"
        diagnostics["controlled_discovery"]["context_assembly"]["schema"] = (
            CONTEXT_SCHEMA_VERSION
        )
        sources = []
        candidate_rows = {
            str(row["canonical_evidence_id"]): row
            for row in diagnostics["controlled_discovery"]["pdf_candidate_retrieval"].get(
                "fused_candidates", []
            )
        }
        selected_ids = diagnostics["controlled_discovery"][
            "pdf_candidate_retrieval"
        ].get("selected_canonical_evidence_ids", [])
        for index, source in enumerate(result.answer_sources):
            value = dict(source)
            chunk = result.context_chunks[index] if index < len(result.context_chunks) else None
            canonical_id = ""
            if chunk is not None and not chunk.structured_tables:
                parsed = chunk.chunk_id.rsplit(":", 1)[-1]
                if parsed in candidate_rows:
                    canonical_id = parsed
            elif chunk is not None and chunk.structured_tables:
                table_id = chunk.structured_tables[0].table_id
                canonical_id = next(
                    (
                        str(node_id)
                        for node_id in selected_ids
                        if str(
                            self.composition.graph.nodes[str(node_id)].attributes.get(
                                "table_id"
                            )
                            or ""
                        )
                        == table_id
                    ),
                    "",
                )
            if not canonical_id and index < len(selected_ids):
                canonical_id = str(selected_ids[index])
            candidate = candidate_rows.get(canonical_id, {})
            if canonical_id:
                value["canonical_evidence_id"] = canonical_id
                value["evidence_id"] = (
                    f"pdf:{value.get('document_id')}:canonical:{canonical_id}"
                )
            value["evidence_domain"] = candidate.get("evidence_domain")
            value["source_node_ids"] = candidate.get("source_node_ids", [])
            value["retrieval_view_ids"] = candidate.get("retrieval_view_ids", {})
            sources.append(value)
        return replace(
            result,
            diagnostics=diagnostics,
            answer_sources=tuple(sources),
            active_collection=(
                "local-structural-view-index:"
                + str(self.composition.artifact_identity["fingerprint"])
            ),
        )


def source_artifact_hashes(root: Path) -> dict[str, str]:
    composition = build_canonical_direct_rag_composition(root)
    return {
        "canonical_ir": str(composition.artifact_identity["canonical_ir"]["sha256"]),
        "view_records": str(
            composition.artifact_identity["view_index"]["records_sha256"]
        ),
        "view_vectors": str(
            composition.artifact_identity["view_index"]["vectors_sha256"]
        ),
        "source_module": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "composition_fingerprint": str(composition.artifact_identity["fingerprint"]),
    }
