from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import time
from typing import Any, Iterable

from .bundle_ranker import packet_node
from .configuration_authority_v1_3 import ConfigurationMatchState
from .expansion import expand_structurally
from .model import DocumentGraph, Node, NodeType
from .owner_identity import OwnerMatchState
from .owner_retriever import OwnerFirstNodeRetriever
from .retrieval_text import normalize, stable_unique, tokens


STRONG_PROCEDURE_PATTERNS = (
    r"\bprocedure\b",
    r"\bsteps?\b",
    r"\bordered\b",
    r"\bsequence\b",
    r"\bfirst\b",
    r"\bsecond\b",
    r"\bthird\b",
    r"\bnext\b",
    r"\bremaining\b",
    r"\bcontinuation\b",
    r"\bhow do\b",
    r"\bhow is\b.+\b(?:removed|installed|replaced|reset|adjusted|converted|cleaned)\b",
    r"\bwhat should\b",
    r"\binstructions?\b",
)
ACTION_TERMS = {
    "remove", "removal", "install", "installation", "replace", "replacement",
    "light", "lighting", "startup", "shutdown", "setup", "reset", "clean",
    "cleaning", "adjust", "adjustment", "convert", "conversion",
}
AMBIGUOUS_TERMS = ACTION_TERMS | {"before", "after"}
ORDINAL_PATTERNS = {
    1: (r"\bfirst\b", r"\bstep\s*1\b", r"\bstep\s*one\b"),
    2: (r"\bsecond\b", r"\bstep\s*2\b", r"\bstep\s*two\b", r"\bmiddle\b"),
    3: (r"\bthird\b", r"\bstep\s*3\b", r"\bstep\s*three\b"),
}
QUERY_STOPWORDS = {
    "a", "an", "and", "are", "be", "do", "does", "for", "from", "how",
    "i", "in", "is", "it", "of", "on", "or", "the", "to", "what",
    "which", "with", "procedure", "procedures", "step", "steps", "ordered",
    "sequence", "model", "manual",
}


@dataclass(frozen=True)
class ScopedProcedureIntent:
    strong_signals: tuple[str, ...]
    ambiguous_signals: tuple[str, ...]
    requested_ordinal: int | None
    ordered: bool
    continuation: bool
    initial: bool

    @property
    def active(self) -> bool:
        return bool(self.strong_signals or self.ambiguous_signals)

    @property
    def strong(self) -> bool:
        return bool(self.strong_signals)


@dataclass(frozen=True)
class ProcedureRetrievalView:
    procedure_id: str
    document_id: str
    relative_path: str
    page: int | None
    section_ancestry: tuple[str, ...]
    explicit_heading: str | None
    source_parent_text: str
    parent_only_text: str
    step_ids: tuple[str, ...]
    step_numbers: tuple[int | None, ...]
    step_texts: tuple[str, ...]
    source_refs: tuple[str, ...]
    step_source_refs: tuple[tuple[str, ...], ...]
    derived_retrieval_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def scoped_procedure_intent(query: str) -> ScopedProcedureIntent:
    value = normalize(query)
    strong = tuple(pattern for pattern in STRONG_PROCEDURE_PATTERNS if re.search(pattern, value))
    query_tokens = set(tokens(value))
    ambiguous = tuple(sorted(query_tokens.intersection(AMBIGUOUS_TERMS)))
    ordinal = next(
        (number for number, patterns in ORDINAL_PATTERNS.items() if any(re.search(pattern, value) for pattern in patterns)),
        None,
    )
    continuation = bool(re.search(r"\b(?:continuation|remaining|next|after)\b", value))
    initial = bool(re.search(r"\b(?:initial|opening|beginning)\b", value))
    ordered = ordinal is None and bool(re.search(r"\b(?:ordered|sequence|procedure|steps|how do|how is)\b", value))
    return ScopedProcedureIntent(strong, ambiguous, ordinal, ordered, continuation, initial)


def _step_key(node: Node) -> tuple[int, int, str]:
    number = node.attributes.get("step_number")
    return (int(number) if isinstance(number, int) else 1_000_000, node.reading_order, node.node_id)


def _procedure_children(graph: DocumentGraph, parent: Node) -> list[Node]:
    return sorted(
        (node for node in graph.children(parent.node_id) if node.node_type == NodeType.PROCEDURE_STEP),
        key=_step_key,
    )


def build_procedure_views(graph: DocumentGraph) -> list[ProcedureRetrievalView]:
    """Build a source-preserving retrieval view without mutating graph nodes."""
    output: list[ProcedureRetrievalView] = []
    for parent in sorted(
        (node for node in graph.nodes.values() if node.node_type == NodeType.PROCEDURE),
        key=lambda node: (node.relative_path, node.page_number or 0, node.reading_order, node.node_id),
    ):
        children = _procedure_children(graph, parent)
        heading = str(parent.attributes.get("title") or parent.attributes.get("heading") or "").strip() or None
        ancestry = tuple(str(value) for value in parent.section_ancestry if str(value).strip())
        parent_only = "\n".join(stable_unique([*ancestry, *( [heading] if heading else [])]))
        step_texts = tuple(node.source_text for node in children)
        owner_values: list[str] = []
        for key in ("manufacturer", "product", "series", "year"):
            value = parent.product_identity.get(key)
            if value:
                owner_values.append(str(value))
        models = parent.product_identity.get("model") or []
        owner_values.extend(str(value) for value in models if value)
        derived = "\n".join(stable_unique([*owner_values, parent_only, parent.source_text, *step_texts]))
        output.append(
            ProcedureRetrievalView(
                procedure_id=parent.node_id,
                document_id=parent.document_id,
                relative_path=parent.relative_path,
                page=parent.page_number,
                section_ancestry=ancestry,
                explicit_heading=heading,
                source_parent_text=parent.source_text,
                parent_only_text=parent_only,
                step_ids=tuple(node.node_id for node in children),
                step_numbers=tuple(node.attributes.get("step_number") if isinstance(node.attributes.get("step_number"), int) else None for node in children),
                step_texts=step_texts,
                source_refs=tuple(str(value) for value in parent.source_provenance.get("source_refs") or []),
                step_source_refs=tuple(tuple(str(value) for value in node.source_provenance.get("source_refs") or []) for node in children),
                derived_retrieval_text=derived,
            )
        )
    return output


def build_procedure_inventory(graph: DocumentGraph, document_ids: Iterable[str] | None = None) -> dict[str, Any]:
    scope = set(document_ids or graph.document_ids)
    views = [view for view in build_procedure_views(graph) if view.document_id in scope]
    steps = [node for node in graph.nodes.values() if node.document_id in scope and node.node_type == NodeType.PROCEDURE_STEP]
    invalid: list[dict[str, Any]] = []
    for step in steps:
        parent = graph.parent(step)
        if parent is None or parent.node_type != NodeType.PROCEDURE:
            invalid.append({"step_id": step.node_id, "parent_id": step.parent_id, "reason": "NO_EXACT_PROCEDURE_PARENT"})
        elif step.node_id not in parent.child_ids:
            invalid.append({"step_id": step.node_id, "parent_id": parent.node_id, "reason": "PARENT_CHILD_LINK_NOT_BIDIRECTIONAL"})
    counts: dict[str, dict[str, int]] = {}
    for document_id in sorted(scope):
        counts[document_id] = {
            "procedures": sum(view.document_id == document_id for view in views),
            "procedure_steps": sum(node.document_id == document_id for node in steps),
        }
    return {
        "schema": "docling_structural_v1_4.procedure_inventory.v1",
        "document_count": len(scope),
        "procedure_count": len(views),
        "procedure_step_count": len(steps),
        "exact_parent_validation": "PASS" if not invalid else "FAIL",
        "invalid_step_parent_links": invalid,
        "per_document_counts": counts,
        "procedures": [view.to_dict() for view in views],
    }


def _content_terms(value: str) -> set[str]:
    return {
        term for term in re.findall(r"[a-z0-9]+", normalize(value))
        if len(term) > 1 and term not in QUERY_STOPWORDS and not term.isdigit()
    }


def _term_overlap(query: str, text: str) -> float:
    wanted = _content_terms(query)
    if not wanted:
        return 0.0
    return len(wanted.intersection(_content_terms(text))) / len(wanted)


def _owner_component(owner: dict[str, Any], document_id: str) -> tuple[float, str | None, str | None]:
    model_state = (owner.get("model_resolution") or {}).get("candidate_states", {}).get(document_id)
    if model_state is None:
        model_state = owner.get("candidate_states", {}).get(document_id)
    config_state = (owner.get("configuration_resolution") or {}).get("candidate_states", {}).get(document_id)
    model_values = {
        OwnerMatchState.EXACT.value: 1.0,
        OwnerMatchState.COMPATIBLE.value: 0.7,
        OwnerMatchState.FAMILY_ONLY.value: 0.35,
        OwnerMatchState.UNKNOWN.value: 0.1,
        OwnerMatchState.CONFLICT.value: -1.0,
    }
    config_values = {
        ConfigurationMatchState.EXACT.value: 0.5,
        ConfigurationMatchState.COMPATIBLE.value: 0.3,
        ConfigurationMatchState.UNKNOWN.value: 0.1,
        ConfigurationMatchState.CONFLICT.value: -1.0,
        None: 0.0,
    }
    return model_values.get(model_state, 0.0) + config_values.get(config_state, 0.0), model_state, config_state


def procedure_score_components(query: str, view: ProcedureRetrievalView, owner: dict[str, Any], intent: ScopedProcedureIntent) -> dict[str, Any]:
    heading = _term_overlap(query, view.explicit_heading or "")
    ancestry = _term_overlap(query, " ".join(view.section_ancestry[-3:]))
    parent = _term_overlap(query, view.parent_only_text)
    child_scores = sorted((_term_overlap(query, value) for value in view.step_texts), reverse=True)
    best = child_scores[0] if child_scores else 0.0
    second = child_scores[1] if len(child_scores) > 1 else 0.0
    third = child_scores[2] if len(child_scores) > 2 else 0.0
    bounded_child = best + 0.35 * second + 0.15 * third
    child_union = _term_overlap(query, " ".join(view.step_texts))
    query_actions = _content_terms(query).intersection(ACTION_TERMS)
    procedure_actions = _content_terms(" ".join([view.explicit_heading or "", *view.step_texts])).intersection(ACTION_TERMS)
    action_match = len(query_actions.intersection(procedure_actions)) / len(query_actions) if query_actions else 0.0
    numbers = {value for value in view.step_numbers if value is not None}
    ordinal_match = 1.0 if intent.requested_ordinal is not None and intent.requested_ordinal in numbers else 0.0
    first_number = min(numbers) if numbers else None
    continuation_match = 1.0 if intent.continuation and first_number is not None and first_number > 1 else 0.0
    initial_match = 1.0 if intent.initial and first_number == 1 else 0.0
    owner_score, model_state, config_state = _owner_component(owner, view.document_id)
    p0 = owner_score + 2.0 * heading + 0.8 * ancestry + 0.4 * parent
    p1 = p0 + 1.5 * best
    p2 = p0 + 1.5 * bounded_child + 0.5 * child_union + 0.35 * action_match + 0.4 * ordinal_match + 0.4 * continuation_match + 0.2 * initial_match
    return {
        "owner_authority": owner_score,
        "model_state": model_state,
        "configuration_state": config_state,
        "heading_lexical": heading,
        "section_lexical": ancestry,
        "parent_lexical": parent,
        "best_child": best,
        "second_child": second,
        "third_child": third,
        "bounded_child": bounded_child,
        "multi_step_coverage": child_union,
        "action_match": action_match,
        "ordinal_match": ordinal_match,
        "continuation_match": continuation_match,
        "initial_match": initial_match,
        "P0": p0,
        "P1": p1,
        "P2": p2,
        "P3": p2,
    }


def rank_scoped_procedures(query: str, views: list[ProcedureRetrievalView], owner: dict[str, Any], intent: ScopedProcedureIntent, ablation: str) -> list[dict[str, Any]]:
    if ablation not in {"P0", "P1", "P2", "P3"}:
        raise ValueError(f"UNKNOWN_PROCEDURE_ABLATION:{ablation}")
    rows: list[dict[str, Any]] = []
    for view in views:
        components = procedure_score_components(query, view, owner, intent)
        rows.append({"procedure_id": view.procedure_id, "document_id": view.document_id, "relative_path": view.relative_path, "page": view.page, "score": components[ablation], "score_components": components})
    return sorted(rows, key=lambda row: (-float(row["score"]), row["page"] or 0, row["procedure_id"]))


def _unique(nodes: Iterable[Node]) -> list[Node]:
    output: list[Node] = []
    seen: set[str] = set()
    for node in nodes:
        if node.node_id not in seen:
            seen.add(node.node_id)
            output.append(node)
    return output


def strict_procedure_answer(graph: DocumentGraph, parent: Node, intent: ScopedProcedureIntent) -> tuple[list[Node], list[Node]]:
    children = _procedure_children(graph, parent)
    if intent.requested_ordinal is not None:
        step = next((node for node in children if node.attributes.get("step_number") == intent.requested_ordinal), None)
        if step is not None:
            page = graph.page(step)
            return [step], _unique([parent, *( [page] if page else [])])
    pages = [graph.page(node) for node in [parent, *children]]
    return [parent], _unique([*children, *(node for node in pages if node is not None)])


class ScopedProcedureRetriever:
    """Add an all-procedure, owner-scoped lane without V1.3 global promotion."""

    def __init__(self, graph: DocumentGraph, authority: Any, *, ablation: str, strict_expansion: bool) -> None:
        self.graph = graph
        self.authority = authority
        self.ablation = ablation
        self.strict_expansion = strict_expansion
        self.baseline = OwnerFirstNodeRetriever(graph, authority, scope_compatible=True)
        self.views = build_procedure_views(graph)
        self.views_by_document: dict[str, list[ProcedureRetrievalView]] = {}
        for view in self.views:
            self.views_by_document.setdefault(view.document_id, []).append(view)

    def retrieve(self, query: str, *, runtime_context: dict[str, Any] | None = None, clarification_expected: bool = False) -> dict[str, Any]:
        started = time.perf_counter()
        baseline = self.baseline.retrieve(query, runtime_context=runtime_context, clarification_expected=clarification_expected, procedure_relationship_repair=True)
        intent = scoped_procedure_intent(query)
        owner = baseline.get("owner_resolution") or {}
        document_ids = list(owner.get("document_ids") or [])
        scoped_views = [view for document_id in document_ids for view in self.views_by_document.get(document_id, [])]
        ranked = rank_scoped_procedures(query, scoped_views, owner, intent, self.ablation) if intent.active else []
        diagnostics = {
            "lane_included": intent.active,
            "lane_selected": bool(intent.strong and ranked),
            "intent_strength": "STRONG" if intent.strong else "AMBIGUOUS" if intent.active else "NONE",
            "strong_signals": list(intent.strong_signals),
            "ambiguous_signals": list(intent.ambiguous_signals),
            "ordered": intent.ordered,
            "requested_ordinal": intent.requested_ordinal,
            "continuation": intent.continuation,
            "resolved_document_ids": document_ids,
            "procedure_candidate_count": len(scoped_views),
            "global_cutoff_required": False,
            "v1_3_parent_promotion_used": False,
            "ablation": self.ablation,
        }
        baseline["procedure_scope"] = diagnostics
        baseline["ordinary_candidates"] = baseline.get("candidates", [])
        baseline["scoped_procedure_candidates"] = [{**row, "rank": index} for index, row in enumerate(ranked, 1)]
        if not intent.strong or not ranked:
            baseline["latency_ms"] = (time.perf_counter() - started) * 1000.0
            return baseline
        parent = self.graph.nodes[ranked[0]["procedure_id"]]
        if self.strict_expansion:
            primary, expanded = strict_procedure_answer(self.graph, parent, intent)
        else:
            primary = [parent]
            expanded = expand_structurally(self.graph, primary, query=query)
        baseline["documents"] = [parent.relative_path]
        baseline["primary_evidence"] = [packet_node(self.graph, node) for node in primary]
        baseline["expanded_context"] = [packet_node(self.graph, node) for node in expanded]
        baseline["candidates"] = [
            {
                "rank": index,
                "node_id": row["procedure_id"],
                "node_type": NodeType.PROCEDURE.value,
                "document_id": row["document_id"],
                "relative_path": row["relative_path"],
                "page": row["page"],
                "lane": "scoped_procedure",
                "normalized_within_lane_rank": index,
                "v1_4_score": row["score"],
                "score_components": row["score_components"],
            }
            for index, row in enumerate(ranked, 1)
        ]
        baseline["latency_ms"] = (time.perf_counter() - started) * 1000.0
        return baseline
