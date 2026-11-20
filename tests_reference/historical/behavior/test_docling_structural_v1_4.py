from __future__ import annotations

from src.docling_structural.configuration_authority_v1_3 import ConfigurationOwnerAuthority
from src.docling_structural.model import DocumentGraph, Node, NodeType
from src.docling_structural.owner_identity import compile_owner_identities
from src.docling_structural.procedure_retriever_v1_4 import (
    ScopedProcedureRetriever,
    build_procedure_inventory,
    build_procedure_views,
    rank_scoped_procedures,
    scoped_procedure_intent,
    strict_procedure_answer,
)


def _node(node_id: str, kind: NodeType, document_id: str, path: str, *, parent: str | None, children: list[str], text: str, title: str | None = None, page: int | None = 1, step: int | None = None) -> Node:
    attributes = {}
    if title:
        attributes["title"] = title
    if step is not None:
        attributes["step_number"] = step
    return Node(
        node_id=node_id,
        node_type=kind,
        document_id=document_id,
        page_id=f"{document_id}-page" if page else None,
        parent_id=parent,
        child_ids=children,
        source_text=text,
        retrieval_text=text,
        relative_path=path,
        page_number=page,
        source_provenance={"source_refs": [f"#/{node_id}"]},
        section_ancestry=[title] if title else [],
        product_identity={"manufacturer": "maker", "product": "griddle", "model": ["m100"], "year": "2024"},
        retrieval_eligible=kind not in {NodeType.PAGE, NodeType.PROCEDURE_STEP},
        attributes=attributes,
    )


def _graph() -> DocumentGraph:
    path = "maker/griddles/series/m100/builtin/2024/om/manual.pdf"
    nodes = {
        "doc": _node("doc", NodeType.DOCUMENT, "doc", path, parent=None, children=["doc-page"], text=path, page=None),
        "doc-page": _node("doc-page", NodeType.PAGE, "doc", path, parent="doc", children=["remove", "clean", "paragraph"], text="M100", page=2),
        "remove": _node("remove", NodeType.PROCEDURE, "doc", path, parent="doc-page", children=["r2", "r1"], text="source container", title="BURNER REMOVAL", page=2),
        "r1": _node("r1", NodeType.PROCEDURE_STEP, "doc", path, parent="remove", children=[], text="1. Lift the burner cover.", page=2, step=1),
        "r2": _node("r2", NodeType.PROCEDURE_STEP, "doc", path, parent="remove", children=[], text="2. Pull the burner from its support.", page=2, step=2),
        "clean": _node("clean", NodeType.PROCEDURE, "doc", path, parent="doc-page", children=["c1"], text="source container", title="BURNER CLEANING", page=2),
        "c1": _node("c1", NodeType.PROCEDURE_STEP, "doc", path, parent="clean", children=[], text="1. Brush debris from burner ports.", page=2, step=1),
        "paragraph": _node("paragraph", NodeType.PARAGRAPH, "doc", path, parent="doc-page", children=[], text="Appliance rating is 12 VDC.", page=2),
    }
    return DocumentGraph(nodes, ["doc"], ["doc-page"])


def test_views_preserve_graph_and_include_all_exact_children() -> None:
    graph = _graph()
    before = graph.nodes["remove"].retrieval_text
    view = next(row for row in build_procedure_views(graph) if row.procedure_id == "remove")
    assert view.step_ids == ("r1", "r2")
    assert view.step_numbers == (1, 2)
    assert "Pull the burner" in view.derived_retrieval_text
    assert graph.nodes["remove"].retrieval_text == before


def test_inventory_verifies_exact_parent_links() -> None:
    inventory = build_procedure_inventory(_graph())
    assert inventory["procedure_count"] == 2
    assert inventory["procedure_step_count"] == 3
    assert inventory["exact_parent_validation"] == "PASS"


def test_parent_child_ranking_discovers_step_specific_parent() -> None:
    graph = _graph()
    views = build_procedure_views(graph)
    owner = ConfigurationOwnerAuthority(compile_owner_identities(graph)).resolve("2024 M100").to_dict()
    intent = scoped_procedure_intent("What is the second burner-removal step for the 2024 M100?")
    ranked = rank_scoped_procedures("What is the second burner-removal step for the 2024 M100?", views, owner, intent, "P2")
    assert ranked[0]["procedure_id"] == "remove"
    assert ranked[0]["score_components"]["best_child"] > 0


def test_strict_expansion_returns_only_winning_parent_children() -> None:
    graph = _graph()
    intent = scoped_procedure_intent("What are the ordered burner-removal steps?")
    primary, expanded = strict_procedure_answer(graph, graph.nodes["remove"], intent)
    assert [node.node_id for node in primary] == ["remove"]
    assert [node.node_id for node in expanded if node.node_type == NodeType.PROCEDURE_STEP] == ["r1", "r2"]
    assert "c1" not in {node.node_id for node in expanded}


def test_ordinal_is_resolved_inside_winning_procedure() -> None:
    graph = _graph()
    intent = scoped_procedure_intent("What is the second burner-removal step?")
    primary, expanded = strict_procedure_answer(graph, graph.nodes["remove"], intent)
    assert [node.node_id for node in primary] == ["r2"]
    assert [node.node_id for node in expanded] == ["remove", "doc-page"]


def test_nonprocedure_query_preserves_configuration_baseline_packet() -> None:
    graph = _graph()
    authority = ConfigurationOwnerAuthority(compile_owner_identities(graph))
    retriever = ScopedProcedureRetriever(graph, authority, ablation="P3", strict_expansion=True)
    packet = retriever.retrieve("What appliance rating is listed for the 2024 M100?")
    assert packet["procedure_scope"]["lane_included"] is False
    assert packet["procedure_scope"]["v1_3_parent_promotion_used"] is False
    assert packet["primary_evidence"][0]["node_id"] == "paragraph"
