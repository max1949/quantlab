"""Semantic diff for Strategy Spec v2 — not plain JSON diff."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from engine.strategies.v2.spec_v2 import StrategySpecV2, validate_spec_v2


ChangeClass = Literal[
    "metadata_only",
    "parameter",
    "logic",
    "risk",
    "data_requirement",
    "execution_assumption",
    "breaking_semantic",
    "identity",
    "compatibility",
    "unchanged",
]


@dataclass
class FieldChange:
    path: str
    before: Any
    after: Any
    change_class: ChangeClass


@dataclass
class SemanticDiffResult:
    strategy_a: str
    strategy_b: str
    changes: list[FieldChange] = field(default_factory=list)
    summary_classes: dict[str, int] = field(default_factory=dict)
    is_breaking: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_a": self.strategy_a,
            "strategy_b": self.strategy_b,
            "is_breaking": self.is_breaking,
            "summary_classes": dict(self.summary_classes),
            "changes": [
                {
                    "path": c.path,
                    "before": c.before,
                    "after": c.after,
                    "change_class": c.change_class,
                }
                for c in self.changes
            ],
        }


def _classify(path: str) -> ChangeClass:
    p = path.lower()
    if p.startswith("identity."):
        if any(x in p for x in ("strategy_id", "version", "family", "parent", "fork", "derived")):
            return "identity"
        return "metadata_only"
    if p.startswith("metadata."):
        return "metadata_only"
    if p.startswith("parameters.") or "parameters.values" in p:
        return "parameter"
    if p.startswith("signal_logic.") or "extension_points" in p:
        return "logic"
    if p.startswith("risk.") or p.startswith("stop_loss") or p.startswith("take_profit") or p.startswith(
        "position_sizing"
    ):
        return "risk"
    if p.startswith("data_requirements") or p.startswith("universe.") or p.startswith("timeframe."):
        if "instruments" in p or "timeframe.timeframe" in p:
            return "breaking_semantic"
        return "data_requirement"
    if p.startswith("execution.") or "assumptions" in p:
        return "execution_assumption"
    if p.startswith("compatibility."):
        return "compatibility"
    if p.startswith("regime."):
        return "logic"
    if "invariant" in p or "contract_id" in p:
        return "breaking_semantic"
    return "breaking_semantic"


_BREAKING = {
    "breaking_semantic",
    "logic",
    "risk",
    "identity",
    "data_requirement",
    "execution_assumption",
}


def _flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in sorted(obj.items()):
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(_flatten(v, key))
    elif isinstance(obj, list):
        # Compare lists as canonical JSON-ish tuples via index for structure;
        # also store whole-list when short for readability
        out[prefix] = obj
        for i, v in enumerate(obj):
            out.update(_flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


def semantic_diff(
    a: StrategySpecV2 | dict[str, Any],
    b: StrategySpecV2 | dict[str, Any],
) -> SemanticDiffResult:
    sa = validate_spec_v2(a)
    sb = validate_spec_v2(b)
    fa = _flatten(sa.canonical_dict())
    fb = _flatten(sb.canonical_dict())
    keys = sorted(set(fa) | set(fb))
    changes: list[FieldChange] = []
    for k in keys:
        va = fa.get(k, "__MISSING__")
        vb = fb.get(k, "__MISSING__")
        if va == vb:
            continue
        # Skip duplicate parent list vs indexed children noise: keep leaf + top-level list
        cls = _classify(k)
        changes.append(FieldChange(path=k, before=va, after=vb, change_class=cls))

    summary: dict[str, int] = {}
    for c in changes:
        summary[c.change_class] = summary.get(c.change_class, 0) + 1

    breaking = any(c.change_class in _BREAKING for c in changes)
    # Parameter-only + metadata-only is non-breaking for lineage classification
    only_soft = set(summary) <= {"metadata_only", "parameter"} and "identity" not in summary
    if only_soft:
        breaking = False

    return SemanticDiffResult(
        strategy_a=f"{sa.identity.strategy_id}@{sa.identity.version}",
        strategy_b=f"{sb.identity.strategy_id}@{sb.identity.version}",
        changes=changes,
        summary_classes=summary,
        is_breaking=breaking,
    )
