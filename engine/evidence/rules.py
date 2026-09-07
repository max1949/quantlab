"""Promotion / Kill rules — map gates + scores → PROMOTE | HOLD | KILL."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from engine.evidence.thresholds import EVIDENCE_THRESHOLDS

EvidenceDecision = Literal["PROMOTE", "HOLD", "KILL"]
GateFlag = Literal["PASS", "FAIL", "INSUFFICIENT"]


@dataclass
class EvidenceGates:
    backtest: GateFlag = "INSUFFICIENT"
    oos: GateFlag = "INSUFFICIENT"
    walk_forward: GateFlag = "INSUFFICIENT"
    fee_stress: GateFlag = "INSUFFICIENT"
    slippage_stress: GateFlag = "INSUFFICIENT"
    parameter_sensitivity: GateFlag = "INSUFFICIENT"
    regime_split: GateFlag = "INSUFFICIENT"
    extreme_period: GateFlag = "INSUFFICIENT"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuleOutcome:
    decision: EvidenceDecision
    reasons: list[str] = field(default_factory=list)
    threshold_version: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def apply_promotion_kill_rules(
    gates: EvidenceGates,
    *,
    reality_score: float,
    research_debt: float,
    overfit_risk: str,
) -> RuleOutcome:
    """Deterministic rules. Profitable IS alone never promotes. Thresholds frozen."""
    thr = EVIDENCE_THRESHOLDS
    reasons: list[str] = []
    hard = [
        name
        for name, val in gates.to_dict().items()
        if val == "FAIL"
    ]
    if hard:
        reasons.append(f"KILL: hard gate fail: {', '.join(hard)}")
        return RuleOutcome("KILL", reasons, str(thr["version"]))

    if research_debt >= float(thr["debt_kill_at_or_above"]):
        reasons.append(
            f"KILL: research_debt={research_debt} >= {thr['debt_kill_at_or_above']}"
        )
        return RuleOutcome("KILL", reasons, str(thr["version"]))

    if reality_score < float(thr["reality_kill_below"]):
        reasons.append(
            f"KILL: reality_score={reality_score} < {thr['reality_kill_below']}"
        )
        return RuleOutcome("KILL", reasons, str(thr["version"]))

    if overfit_risk == "HIGH":
        reasons.append("KILL: OVERFIT_RISK=HIGH")
        return RuleOutcome("KILL", reasons, str(thr["version"]))

    core = (
        gates.backtest,
        gates.oos,
        gates.walk_forward,
        gates.fee_stress,
        gates.slippage_stress,
        gates.parameter_sensitivity,
    )
    insuff = [n for n, v in gates.to_dict().items() if v == "INSUFFICIENT"]

    if (
        all(g == "PASS" for g in core)
        and gates.regime_split != "FAIL"
        and gates.extreme_period != "FAIL"
        and reality_score >= float(thr["reality_promote_min"])
        and overfit_risk != "HIGH"
    ):
        reasons.append(
            f"PROMOTE: core gates PASS; reality_score>={thr['reality_promote_min']}; "
            f"debt={research_debt}"
        )
        return RuleOutcome("PROMOTE", reasons, str(thr["version"]))

    if insuff:
        reasons.append(f"HOLD: insufficient evidence: {', '.join(insuff)}")
    else:
        reasons.append("HOLD: gates incomplete or reality below promote floor")
    if reality_score < float(thr["reality_promote_min"]):
        reasons.append(
            f"HOLD: reality_score={reality_score} < promote_min={thr['reality_promote_min']}"
        )
    reasons.append("do not retune thresholds to chase PASS")
    return RuleOutcome("HOLD", reasons, str(thr["version"]))
