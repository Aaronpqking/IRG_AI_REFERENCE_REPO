from __future__ import annotations

from .model import DocumentGraph, Node, NodeType
from .retrieval_text import tokens


def _append(output: list[Node], seen: set[str], node: Node | None) -> None:
    if node is not None and node.node_id not in seen:
        seen.add(node.node_id)
        output.append(node)


def expand_structurally(graph: DocumentGraph, anchors: list[Node], *, query: str) -> list[Node]:
    output: list[Node] = []
    seen = {node.node_id for node in anchors}
    query_terms = set(tokens(query))
    for anchor in anchors:
        parent = graph.parent(anchor)
        page = graph.page(anchor)
        if anchor.node_type == NodeType.TABLE_ROW:
            for child in graph.children(anchor.node_id):
                _append(output, seen, child)
            _append(output, seen, parent)
        elif anchor.node_type == NodeType.TABLE:
            children = graph.children(anchor.node_id)
            children.sort(key=lambda node: (-len(query_terms.intersection(tokens(node.retrieval_text))), node.node_id))
            for child in children[:3]:
                _append(output, seen, child)
                for cell in graph.children(child.node_id):
                    _append(output, seen, cell)
        elif anchor.node_type == NodeType.PROCEDURE_STEP:
            _append(output, seen, parent)
            if parent:
                for child in graph.children(parent.node_id):
                    if child.node_type == NodeType.PROCEDURE_STEP:
                        _append(output, seen, child)
        elif anchor.node_type == NodeType.PROCEDURE:
            for child in graph.children(anchor.node_id):
                if child.node_type == NodeType.PROCEDURE_STEP:
                    _append(output, seen, child)
        elif anchor.node_type == NodeType.ADMONITION:
            for associated in anchor.attributes.get("associated_node_ids") or []:
                _append(output, seen, graph.nodes.get(str(associated)))
        elif anchor.node_type in {NodeType.FIGURE, NodeType.CAPTION, NodeType.OCR_REGION}:
            figure = anchor if anchor.node_type == NodeType.FIGURE else parent
            _append(output, seen, figure)
            if figure:
                for child in graph.children(figure.node_id):
                    _append(output, seen, child)
        elif anchor.node_type == NodeType.DOCUMENT:
            pages = [child for child in graph.children(anchor.node_id) if child.node_type == NodeType.PAGE]
            if pages:
                first_page = sorted(pages, key=lambda node: (node.page_number or 0, node.node_id))[0]
                _append(output, seen, first_page)
                for child in graph.children(first_page.node_id)[:8]:
                    _append(output, seen, child)
        else:
            _append(output, seen, parent)
        _append(output, seen, page)
    return output


def expand_generic_neighbors(graph: DocumentGraph, anchors: list[Node]) -> list[Node]:
    output: list[Node] = []
    seen = {node.node_id for node in anchors}
    by_document: dict[str, list[Node]] = {}
    for anchor in anchors:
        ordered = by_document.setdefault(anchor.document_id, graph.ordered_document_nodes(anchor.document_id))
        positions = {node.node_id: index for index, node in enumerate(ordered)}
        position = positions.get(anchor.node_id)
        if position is None:
            continue
        for index in (position - 1, position + 1):
            if 0 <= index < len(ordered):
                _append(output, seen, ordered[index])
    return output
