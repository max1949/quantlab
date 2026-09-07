"""Version / lineage aligned with QLN-1 version semantics."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from engine.domain.versioning import next_strategy_version, VersionBump
from engine.strategies.v2.errors import SpecV2Error
from engine.strategies.v2.semantic_diff import SemanticDiffResult, semantic_diff
from engine.strategies.v2.spec_v2 import StrategySpecV2


ChildKind = Literal[
    "parameter_only_child",
    "logic_changing_child",
    "fork",
    "derived_from",
]


class LineageRecord(BaseModel):
    family_id: str
    strategy_id: str
    version: str
    parent_version: str | None = None
    derived_from: str | None = None
    fork_of: str | None = None
    child_kind: ChildKind | None = None
    content_hash: str | None = None
    notes: str = ""

    def canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def lineage_from_spec(spec: StrategySpecV2) -> LineageRecord:
    return LineageRecord(
        family_id=spec.identity.family_id or spec.identity.strategy_id,
        strategy_id=spec.identity.strategy_id,
        version=spec.identity.version,
        parent_version=spec.identity.parent_version,
        derived_from=spec.identity.derived_from,
        fork_of=spec.identity.fork_of,
        content_hash=spec.content_hash(),
    )


def classify_child(diff: SemanticDiffResult) -> ChildKind:
    if diff.is_breaking or any(
        c.change_class in ("logic", "risk", "breaking_semantic", "data_requirement", "execution_assumption")
        for c in diff.changes
    ):
        return "logic_changing_child"
    if any(c.change_class == "parameter" for c in diff.changes):
        return "parameter_only_child"
    return "parameter_only_child"


def derive_child_lineage(
    parent: StrategySpecV2,
    child: StrategySpecV2,
    *,
    kind: ChildKind | None = None,
) -> LineageRecord:
    if parent.identity.strategy_id != child.identity.strategy_id and kind != "fork":
        # Different ids without fork declaration → treat as fork
        kind = "fork"
    diff = semantic_diff(parent, child)
    resolved = kind or classify_child(diff)
    if not child.identity.version.strip():
        raise SpecV2Error("child version required")
    # Align with QLN-1 version bump helpers (legacy tags like "v1" remain valid)
    _ = next_strategy_version(child.identity.version, VersionBump.NONE)

    return LineageRecord(
        family_id=child.identity.family_id or parent.identity.family_id or parent.identity.strategy_id,
        strategy_id=child.identity.strategy_id,
        version=child.identity.version,
        parent_version=parent.identity.version,
        derived_from=f"{parent.identity.strategy_id}@{parent.identity.version}",
        fork_of=f"{parent.identity.strategy_id}@{parent.identity.version}" if resolved == "fork" else None,
        child_kind=resolved,
        content_hash=child.content_hash(),
        notes=f"classes={diff.summary_classes}",
    )
