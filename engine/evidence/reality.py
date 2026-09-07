"""Reality Score — discounts pretty backtests that fail stress / regime / extreme checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from engine.evidence.thresholds import EVIDENCE_THRESHOLD_VERSION


@dataclass
class RealityScore:
    score: float
    components: dict[str, float]
    version: str = EVIDENCE_THRESHOLD_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _flag_score(flag: str) -> float:
    if flag == "PASS":
        return 1.0
    if flag == "INSUFFICIENT":
        return 0.4
    return 0.0


def compute_reality_score(
    *,
    oos_flag: str,
    wf_flag: str,
    fee_flag: str,
    slip_flag: str,
    sens_flag: str,
    regime_flag: str,
    extreme_flag: str,
    oos_sharpe: float | None,
    wf_positive_ratio: float | None,
) -> RealityScore:
    comps = {
        "oos": _flag_score(oos_flag) * 0.20,
        "walk_forward": _flag_score(wf_flag) * 0.15,
        "fee_stress": _flag_score(fee_flag) * 0.15,
        "slippage_stress": _flag_score(slip_flag) * 0.15,
        "sensitivity": _flag_score(sens_flag) * 0.10,
        "regime": _flag_score(regime_flag) * 0.10,
        "extreme": _flag_score(extreme_flag) * 0.10,
        "oos_sharpe_quality": min(1.0, max(0.0, (oos_sharpe or 0.0) / 1.5)) * 0.025,
        "wf_consistency": min(1.0, max(0.0, (wf_positive_ratio or 0.0))) * 0.025,
    }
    return RealityScore(score=round(100.0 * sum(comps.values()), 4), components=comps)
