"""Frozen Evidence Validation thresholds (QLN-4).

Do NOT lower these to manufacture PASS. Change only via Owner/governance
amendment with a new threshold version id.
"""

from __future__ import annotations

from typing import Any

EVIDENCE_THRESHOLD_VERSION = "qln4_evidence_thr_v1"

EVIDENCE_THRESHOLDS: dict[str, Any] = {
    "version": EVIDENCE_THRESHOLD_VERSION,
    # OOS
    "oos_min_sharpe": 0.0,  # must be strictly > for PASS (checked as >)
    "oos_max_sharpe_degradation": 1.0,
    # Walk forward
    "wf_min_positive_ratio_pass": 0.5,
    "wf_min_positive_ratio_fail": 0.4,
    # Robustness / sensitivity
    "robustness_min_score_pass": 55.0,
    "robustness_min_score_fail": 40.0,
    "sensitivity_min_positive_ratio_fail": 0.35,
    # Cost stresses (separate fee vs slippage)
    "fee_stress_mult": 2.0,
    "slippage_stress_mult": 2.0,
    "stress_min_sharpe": 0.0,  # stressed sharpe must stay > this for PASS
    # Regime / extreme
    "regime_min_positive_ratio": 0.4,
    "extreme_max_drawdown": 0.5,
    # Reality score floors
    "reality_promote_min": 60.0,
    "reality_kill_below": 25.0,
    # Research debt
    "debt_kill_at_or_above": 80.0,
    # Evidence floors (aligned with validation.decision)
    "min_trade_count": 30,
    "min_periods": 200,
}
