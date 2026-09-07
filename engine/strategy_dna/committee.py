"""AI Committee roles — RESEARCHER / SKEPTIC / FALSIFIER (contract + deterministic stub)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Role = Literal["RESEARCHER", "SKEPTIC", "FALSIFIER"]


class CommitteeOpinion(BaseModel):
    role: Role
    stance: str
    notes: list[str] = Field(default_factory=list)
    allows_no_edge: bool = True


def committee_review(evidence: dict[str, Any]) -> list[CommitteeOpinion]:
    """Deterministic committee opinions — no LLM required for QLN-6 contract tests."""
    decision = str(evidence.get("decision") or "HOLD")
    reasons = list(evidence.get("reasons") or [])
    researcher = CommitteeOpinion(
        role="RESEARCHER",
        stance="document_hypothesis_and_evidence",
        notes=["Record WHAT/WHY/WHEN and evidence gates", f"decision={decision}"],
    )
    skeptic = CommitteeOpinion(
        role="SKEPTIC",
        stance="challenge_pretty_backtests",
        notes=[
            "Demand OOS/WF/stress before trust",
            "Flag always-long RSI sign artifact if present",
            *reasons[:2],
        ],
    )
    falsifier = CommitteeOpinion(
        role="FALSIFIER",
        stance="prefer_kill_when_gates_fail",
        notes=[
            "NO_EDGE_FOUND is a valid outcome",
            "Do not optimize_until_pass",
            f"outcome_hint={'NO_EDGE_FOUND' if decision == 'KILL' else decision}",
        ],
        allows_no_edge=True,
    )
    return [researcher, skeptic, falsifier]
