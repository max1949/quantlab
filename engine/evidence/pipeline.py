"""Canonical Evidence Validation Pipeline (QLN-4)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

import pandas as pd

from engine.backtest import run_backtest
from engine.cost_model import CostConfig
from engine.evidence.debt import ResearchDebt, compute_research_debt
from engine.evidence.reality import RealityScore, compute_reality_score
from engine.evidence.rules import EvidenceGates, RuleOutcome, apply_promotion_kill_rules
from engine.evidence.stresses import (
    extreme_period_test,
    fee_stress,
    regime_split_test,
    slippage_stress,
)
from engine.evidence.thresholds import EVIDENCE_THRESHOLD_VERSION, EVIDENCE_THRESHOLDS
from engine.validation.decision import assess_overfit_risk
from engine.validation.metrics_ext import compute_extended_metrics
from engine.walk_forward import evaluate_oos, robustness_score, sensitivity, walk_forward

SignalFn = Callable[[pd.DataFrame], pd.Series]


@dataclass
class EvidenceReport:
    strategy_id: str
    strategy_version: str
    decision: str
    reasons: list[str]
    gates: dict[str, Any]
    reality_score: dict[str, Any]
    research_debt: dict[str, Any]
    overfit_risk: str
    backtest: dict[str, Any] = field(default_factory=dict)
    oos: dict[str, Any] = field(default_factory=dict)
    walk_forward: dict[str, Any] = field(default_factory=dict)
    fee_stress: dict[str, Any] = field(default_factory=dict)
    slippage_stress: dict[str, Any] = field(default_factory=dict)
    parameter_sensitivity: dict[str, Any] = field(default_factory=dict)
    regime_split: dict[str, Any] = field(default_factory=dict)
    extreme_period: dict[str, Any] = field(default_factory=dict)
    robustness: dict[str, Any] = field(default_factory=dict)
    threshold_version: str = EVIDENCE_THRESHOLD_VERSION
    live_execution: str = "DENY"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _oos_flag(oos: dict) -> str:
    thr = EVIDENCE_THRESHOLDS
    oos_m = oos.get("out_of_sample") or {}
    is_m = oos.get("in_sample") or {}
    oos_s = oos_m.get("sharpe")
    is_s = is_m.get("sharpe")
    deg = oos.get("sharpe_degradation")
    if oos_s is None:
        return "INSUFFICIENT"
    if float(oos_s) <= float(thr["oos_min_sharpe"]):
        return "FAIL"
    if (
        deg is not None
        and float(deg) > float(thr["oos_max_sharpe_degradation"])
        and is_s is not None
        and float(is_s) > 0.5
    ):
        return "FAIL"
    return "PASS"


def _wf_flag(wf: dict) -> str:
    thr = EVIDENCE_THRESHOLDS
    summary = wf.get("summary") or {}
    pr = summary.get("positive_ratio")
    if pr is None or not wf.get("folds"):
        return "INSUFFICIENT"
    if float(pr) < float(thr["wf_min_positive_ratio_fail"]):
        return "FAIL"
    if float(pr) < float(thr["wf_min_positive_ratio_pass"]):
        return "INSUFFICIENT"
    return "PASS"


def _sens_flag(sens: dict, rob: dict) -> str:
    thr = EVIDENCE_THRESHOLDS
    score = rob.get("score")
    sens_pr = (sens.get("summary") or {}).get("positive_ratio")
    if score is None:
        return "INSUFFICIENT"
    if float(score) < float(thr["robustness_min_score_fail"]):
        return "FAIL"
    if sens_pr is not None and float(sens_pr) < float(thr["sensitivity_min_positive_ratio_fail"]):
        return "FAIL"
    if float(score) < float(thr["robustness_min_score_pass"]):
        return "INSUFFICIENT"
    return "PASS"


def run_evidence_pipeline(
    *,
    strategy_id: str,
    strategy_version: str,
    ohlcv: pd.DataFrame,
    compute_signal: SignalFn,
    neighborhood: list[tuple[str, SignalFn]] | None = None,
    param_count: int = 2,
) -> EvidenceReport:
    """Canonical Backtest + OOS + WF + stresses + Reality/Debt → PROMOTE/HOLD/KILL."""
    thr = EVIDENCE_THRESHOLDS
    cost = CostConfig()
    bt = run_backtest(compute_signal(ohlcv), ohlcv, cost)
    metrics_full = compute_extended_metrics(compute_signal(ohlcv), ohlcv, cost)
    oos = evaluate_oos(compute_signal, ohlcv, cost_config=cost)
    wf = walk_forward(compute_signal, ohlcv, cost_config=cost, n_splits=3)

    if neighborhood is None or len(neighborhood) == 0:
        # Empty neighborhood → sensitivity INSUFFICIENT (fail closed for promote).
        sens: dict[str, Any] = {"summary": {}, "variants": [], "status": "INSUFFICIENT"}
        rob = robustness_score(oos, wf, sens)
        sens_forced_insufficient = True
    else:
        sens = sensitivity(neighborhood, ohlcv, cost_config=cost)
        rob = robustness_score(oos, wf, sens)
        sens_forced_insufficient = False

    fee = fee_stress(compute_signal, ohlcv)
    slip = slippage_stress(compute_signal, ohlcv)
    regime = regime_split_test(compute_signal, ohlcv)
    extreme = extreme_period_test(compute_signal, ohlcv)

    backtest_flag = "PASS" if bt.get("metrics") else "FAIL"
    oos_f = _oos_flag(oos)
    wf_f = _wf_flag(wf)
    sens_f = "INSUFFICIENT" if sens_forced_insufficient else _sens_flag(sens, rob)
    fee_f = str(fee["status"])
    slip_f = str(slip["status"])
    regime_f = str(regime["status"])
    extreme_f = str(extreme["status"])

    gates = EvidenceGates(
        backtest=backtest_flag,  # type: ignore[arg-type]
        oos=oos_f,  # type: ignore[arg-type]
        walk_forward=wf_f,  # type: ignore[arg-type]
        fee_stress=fee_f,  # type: ignore[arg-type]
        slippage_stress=slip_f,  # type: ignore[arg-type]
        parameter_sensitivity=sens_f,  # type: ignore[arg-type]
        regime_split=regime_f,  # type: ignore[arg-type]
        extreme_period=extreme_f,  # type: ignore[arg-type]
    )

    overfit = assess_overfit_risk(
        param_count=param_count,
        trade_count=int(metrics_full.get("trade_count") or 0),
        periods=int(metrics_full.get("periods") or len(ohlcv)),
        sens_positive_ratio=(sens.get("summary") or {}).get("positive_ratio"),
        sharpe_degradation=oos.get("sharpe_degradation"),
        wf_positive_ratio=(wf.get("summary") or {}).get("positive_ratio"),
        top_win_concentration=metrics_full.get("top_win_concentration"),
    )

    oos_sharpe = (oos.get("out_of_sample") or {}).get("sharpe")
    wf_pr = (wf.get("summary") or {}).get("positive_ratio")
    reality = compute_reality_score(
        oos_flag=oos_f,
        wf_flag=wf_f,
        fee_flag=fee_f,
        slip_flag=slip_f,
        sens_flag=sens_f,
        regime_flag=regime_f,
        extreme_flag=extreme_f,
        oos_sharpe=float(oos_sharpe) if oos_sharpe is not None else None,
        wf_positive_ratio=float(wf_pr) if wf_pr is not None else None,
    )
    debt = compute_research_debt(
        gates=gates.to_dict(),
        overfit_risk=overfit,
        trade_count=int(metrics_full.get("trade_count") or 0),
        periods=int(metrics_full.get("periods") or len(ohlcv)),
        min_trades=int(thr["min_trade_count"]),
        min_periods=int(thr["min_periods"]),
    )
    outcome: RuleOutcome = apply_promotion_kill_rules(
        gates,
        reality_score=reality.score,
        research_debt=debt.score,
        overfit_risk=overfit,
    )

    return EvidenceReport(
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        decision=outcome.decision,
        reasons=outcome.reasons,
        gates=gates.to_dict(),
        reality_score=reality.to_dict(),
        research_debt=debt.to_dict(),
        overfit_risk=overfit,
        backtest=bt.get("metrics") or {},
        oos=oos,
        walk_forward=wf if isinstance(wf, dict) else {},
        fee_stress=fee,
        slippage_stress=slip,
        parameter_sensitivity=sens,
        regime_split=regime,
        extreme_period=extreme,
        robustness={**rob, "full_sample_extended": metrics_full},
        threshold_version=str(thr["version"]),
        live_execution="DENY",
    )
