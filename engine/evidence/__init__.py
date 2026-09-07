"""QLN-4 Evidence Validation Pipeline — PROMOTE / HOLD / KILL with explainable reasons."""

from __future__ import annotations

from engine.evidence.debt import ResearchDebt, compute_research_debt
from engine.evidence.pipeline import EvidenceReport, run_evidence_pipeline
from engine.evidence.reality import RealityScore, compute_reality_score
from engine.evidence.rules import EvidenceDecision, apply_promotion_kill_rules
from engine.evidence.thresholds import EVIDENCE_THRESHOLD_VERSION

__all__ = [
    "EVIDENCE_THRESHOLD_VERSION",
    "EvidenceDecision",
    "EvidenceReport",
    "RealityScore",
    "ResearchDebt",
    "apply_promotion_kill_rules",
    "compute_reality_score",
    "compute_research_debt",
    "run_evidence_pipeline",
]
