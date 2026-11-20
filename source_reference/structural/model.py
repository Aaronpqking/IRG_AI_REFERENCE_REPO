from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class NodeType(StrEnum):
    DOCUMENT = "DOCUMENT"
    PAGE = "PAGE"
    SECTION = "SECTION"
    PARAGRAPH = "PARAGRAPH"
    TABLE = "TABLE"
    TABLE_ROW = "TABLE_ROW"
    TABLE_CELL = "TABLE_CELL"
    ADMONITION = "ADMONITION"
    PROCEDURE = "PROCEDURE"
    PROCEDURE_STEP = "PROCEDURE_STEP"
    FIGURE = "FIGURE"
    CAPTION = "CAPTION"
    OCR_REGION = "OCR_REGION"


@dataclass
class Node:
    node_id: str
    node_type: NodeType
    document_id: str
    page_id: str | None
    parent_id: str | None
    child_ids: list[str]
    source_text: str
    retrieval_text: str
    relative_path: str
    page_number: int | None
    source_provenance: dict[str, Any]
    bbox: dict[str, Any] | None = None
    section_ancestry: list[str] = field(default_factory=list)
    product_identity: dict[str, Any] = field(default_factory=dict)
    retrieval_eligible: bool = True
    reading_order: int = 0
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["node_type"] = self.node_type.value
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Node":
        row = dict(value)
        row["node_type"] = NodeType(row["node_type"])
        return cls(**row)


@dataclass
class DocumentGraph:
    nodes: dict[str, Node]
    document_ids: list[str]
    page_ids: list[str]
    source_manifest: dict[str, Any] = field(default_factory=dict)

    def children(self, node_id: str) -> list[Node]:
        node = self.nodes[node_id]
        return [self.nodes[value] for value in node.child_ids if value in self.nodes]

    def parent(self, node: Node) -> Node | None:
        return self.nodes.get(node.parent_id or "")

    def page(self, node: Node) -> Node | None:
        return self.nodes.get(node.page_id or "")

    def ordered_document_nodes(self, document_id: str) -> list[Node]:
        return sorted(
            (
                node
                for node in self.nodes.values()
                if node.document_id == document_id
                and node.node_type not in {NodeType.DOCUMENT, NodeType.PAGE}
            ),
            key=lambda node: (node.page_number or 0, node.reading_order, node.node_id),
        )

    def to_records(self) -> list[dict[str, Any]]:
        return [self.nodes[key].to_dict() for key in sorted(self.nodes)]

    @classmethod
    def from_records(
        cls, records: list[dict[str, Any]], source_manifest: dict[str, Any] | None = None
    ) -> "DocumentGraph":
        nodes = {row["node_id"]: Node.from_dict(row) for row in records}
        return cls(
            nodes=nodes,
            document_ids=sorted(
                node.node_id for node in nodes.values() if node.node_type == NodeType.DOCUMENT
            ),
            page_ids=sorted(
                node.node_id for node in nodes.values() if node.node_type == NodeType.PAGE
            ),
            source_manifest=source_manifest or {},
        )
