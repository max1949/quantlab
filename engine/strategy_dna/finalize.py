"""Finalize a bounded research step — terminal NO_EDGE_FOUND without optimize-until-pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engine.strategy_dna.budget import ResearchBudget, assert_within_budget
from engine.strategy_dna.committee import CommitteeOpinion, committee_review
from engine.strategy_dna.graveyard import GraveyardIndex, index_reject, persist_reject
from engine.strategy_dna.memory import MemoryRecord, ResearchMemory
from engine.strategy_dna.outcomes import (
    evidence_decision_to_memory_outcome,
    forbid_continue_optimize_payload,
    is_negative_outcome,
)


@dataclass
class ResearchFinalizeResult:
    strategy_id: str
    version: str
    evidence_decision: str
    memory_outcome: str
    negative_result: bool
    reasons: list[str] = field(default_factory=list)
    committee: list[CommitteeOpinion] = field(default_factory=list)
    recommendation: dict[str, Any] = field(default_factory=dict)
    graveyard_persisted: bool = False
    memory_persisted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "evidence_decision": self.evidence_decision,
            "memory_outcome": self.memory_outcome,
            "negative_result": self.negative_result,
            "reasons": list(self.reasons),
            "committee": [c.model_dump(mode="json") for c in self.committee],
            "recommendation": dict(self.recommendation),
            "graveyard_persisted": self.graveyard_persisted,
            "memory_persisted": self.memory_persisted,
        }


def finalize_research_outcome(
    *,
    strategy_id: str,
    version: str,
    evidence_decision: str,
    reasons: list[str] | None = None,
    gates: dict[str, Any] | None = None,
    evidence_summary: dict[str, Any] | None = None,
    dataset_id: str = "",
    market: str = "",
    timeframe: str = "1d",
    budget: ResearchBudget | None = None,
    candidates_created: int = 0,
    memory: ResearchMemory | None = None,
    graveyard_index: GraveyardIndex | None = None,
    persist_graveyard_path: Path | str | None = None,
    persist: bool = True,
) -> ResearchFinalizeResult:
    """Seal one research step under QLN-6 contracts.

    - OPTIMIZE_UNTIL_PASS forbidden via budget
    - KILL → memory outcome NO_EDGE_FOUND
    - Negative outcomes never recommend continue-optimize
    - Optional dual-write to legacy validation graveyard JSONL
    """
    budget = budget or ResearchBudget()
    assert_within_budget(budget, created=candidates_created)

    reasons = list(reasons or [])
    gates = dict(gates or {})
    outcome = evidence_decision_to_memory_outcome(evidence_decision)
    if budget.require_negative_result_logging and is_negative_outcome(outcome) and not reasons:
        reasons = [f"evidence_decision={evidence_decision}"]

    committee = committee_review(
        {"decision": evidence_decision, "reasons": reasons, "gates": gates}
    )
    rec = forbid_continue_optimize_payload(outcome)

    result = ResearchFinalizeResult(
        strategy_id=strategy_id,
        version=version,
        evidence_decision=evidence_decision,
        memory_outcome=outcome,
        negative_result=is_negative_outcome(outcome),
        reasons=reasons,
        committee=committee,
        recommendation=rec,
    )

    if not persist:
        return result

    mem = memory or ResearchMemory()
    mem.append(
        MemoryRecord(
            strategy_id=strategy_id,
            version=version,
            outcome=outcome,
            reasons=reasons,
            evidence_summary=evidence_summary or {"gates": gates, "decision": evidence_decision},
            dataset_id=dataset_id,
            negative_result=result.negative_result,
        )
    )
    result.memory_persisted = True

    if result.negative_result:
        entry = index_reject(
            strategy_id=strategy_id,
            version=version,
            reason="; ".join(reasons) or outcome,
            gates=gates,
        )
        if graveyard_index is not None:
            graveyard_index.add(entry)
        persist_reject(
            strategy_id=strategy_id,
            version=version,
            reason=entry["reason"],
            gates=gates,
            market=market,
            timeframe=timeframe,
            path=persist_graveyard_path,
        )
        result.graveyard_persisted = True

    return result
