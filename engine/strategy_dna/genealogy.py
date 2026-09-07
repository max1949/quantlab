"""Strategy genealogy graph — family / parent / fork links (QLN-6)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from engine.strategy_dna.dna import StrategyDNA


class GenealogyEdge(BaseModel):
    parent_id: str
    child_id: str
    relation: str  # parent | fork | derived_from | parameter_only | logic_changing


class GenealogyGraph(BaseModel):
    nodes: dict[str, StrategyDNA] = Field(default_factory=dict)
    edges: list[GenealogyEdge] = Field(default_factory=list)

    def add_node(self, dna: StrategyDNA) -> None:
        self.nodes[f"{dna.strategy_id}@{dna.version}"] = dna

    def link(self, parent_id: str, child_id: str, relation: str) -> None:
        self.edges.append(
            GenealogyEdge(parent_id=parent_id, child_id=child_id, relation=relation)
        )

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def link_parent_child(
    graph: GenealogyGraph,
    parent: StrategyDNA,
    child: StrategyDNA,
    *,
    relation: str,
) -> GenealogyGraph:
    graph.add_node(parent)
    graph.add_node(child)
    graph.link(
        f"{parent.strategy_id}@{parent.version}",
        f"{child.strategy_id}@{child.version}",
        relation,
    )
    return graph
