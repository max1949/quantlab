"""PROMOTE / HOLD / REJECT decision + overfit risk (deterministic gate)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Decision = Literal["PROMOTE", "HOLD", "REJECT"]
OverfitRisk = Literal["LOW", "MEDIUM", "HIGH"]
GateFlag = Literal["PASS", "FAIL", "INSUFFICIENT"]

# Evidence floors reused by paper graduation / leaderboard ranking (not invented ad hoc).
MIN_TRADE_COUNT_FOR_EVIDENCE = 30
MIN_PERIODS_FOR_EVIDENCE = 200


@dataclass
class GateChecklist:
    oos: GateFlag = "INSUFFICIENT"
    walk_forward: GateFlag = "INSUFFICIENT"
    robustness: GateFlag = "INSUFFICIENT"
    cost_stress: GateFlag = "INSUFFICIENT"
    paper: GateFlag = "INSUFFICIENT"
    parity: GateFlag = "INSUFFICIENT"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionResult:
    decision: Decision
    overfit_risk: OverfitRisk
    gates: GateChecklist
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "overfit_risk": self.overfit_risk,
            "gates": self.gates.to_dict(),
            "reasons": self.reasons,
        }


def assess_overfit_risk(
    *,
    param_count: int,
    trade_count: int,
    periods: int,
    sens_positive_ratio: float | None,
    sharpe_degradation: float | None,
    wf_positive_ratio: float | None,
    top_win_concentration: float | None,
) -> OverfitRisk:
    flags = 0
    if param_count >= 4:
        flags += 1
    if trade_count < MIN_TRADE_COUNT_FOR_EVIDENCE:
        flags += 1
    if periods < MIN_PERIODS_FOR_EVIDENCE:
        flags += 1
    if sens_positive_ratio is not None and sens_positive_ratio < 0.5:
        flags += 2
    if sharpe_degradation is not None and sharpe_degradation > 0.5:
        flags += 2
    if wf_positive_ratio is not None and wf_positive_ratio < 0.5:
        flags += 1
    if top_win_concentration is not None and top_win_concentration > 0.6:
        flags += 2
    if flags >= 4:
        return "HIGH"
    if flags >= 2:
        return "MEDIUM"
    return "LOW"


def decide_outcome(
    gates: GateChecklist,
    *,
    overfit_risk: OverfitRisk,
    reject_hard: bool = False,
) -> DecisionResult:
    """Deterministic promotion gate. Profitable IS alone never promotes."""
    reasons: list[str] = []

    hard_fails = [
        name
        for name, val in (
            ("oos", gates.oos),
            ("walk_forward", gates.walk_forward),
            ("robustness", gates.robustness),
            ("cost_stress", gates.cost_stress),
            ("paper", gates.paper),
            ("parity", gates.parity),
        )
        if val == "FAIL"
    ]
    if reject_hard or hard_fails:
        reasons.append(f"hard fail: {', '.join(hard_fails) or 'explicit'}")
        if overfit_risk == "HIGH":
            reasons.append("OVERFIT_RISK=HIGH")
        return DecisionResult("REJECT", overfit_risk, gates, reasons)

    required = (
        gates.oos,
        gates.walk_forward,
        gates.robustness,
        gates.cost_stress,
        gates.paper,
        gates.parity,
    )
    if all(g == "PASS" for g in required) and overfit_risk != "HIGH":
        reasons.append("all validation gates PASS; overfit not HIGH")
        return DecisionResult("PROMOTE", overfit_risk, gates, reasons)

    insuff = [n for n, v in (
        ("oos", gates.oos),
        ("walk_forward", gates.walk_forward),
        ("robustness", gates.robustness),
        ("cost_stress", gates.cost_stress),
        ("paper", gates.paper),
        ("parity", gates.parity),
    ) if v == "INSUFFICIENT"]
    if insuff:
        reasons.append(f"insufficient evidence: {', '.join(insuff)}")
    if overfit_risk == "HIGH":
        reasons.append("OVERFIT_RISK=HIGH → cannot PROMOTE")
        return DecisionResult("REJECT", overfit_risk, gates, reasons)
    reasons.append("HOLD: do not retune to chase a pass")
    return DecisionResult("HOLD", overfit_risk, gates, reasons)
