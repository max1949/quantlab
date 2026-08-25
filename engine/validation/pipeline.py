"""Full Strategy Validation pipeline (no skip levels; Paper may be INSUFFICIENT)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd

from engine.backtest import run_backtest
from engine.cost_model import CostConfig
from engine.data.dataset_resolver import resolve_dataset
from engine.validation.baselines import BaselineCandidate
from engine.validation.decision import (
    DecisionResult,
    GateChecklist,
    assess_overfit_risk,
    decide_outcome,
)
from engine.validation.graveyard import GraveyardEntry, append_reject
from engine.validation.metrics_ext import compute_extended_metrics
from engine.walk_forward import evaluate_oos, robustness_score, sensitivity, walk_forward


@dataclass
class StrategyValidationReport:
    strategy_id: str
    strategy_version: str
    family: str
    hypothesis: str
    market: str
    timeframe: str
    decision: str
    overfit_risk: str
    gates: dict[str, Any]
    reasons: list[str]
    metrics_is: dict[str, Any] = field(default_factory=dict)
    metrics_oos: dict[str, Any] = field(default_factory=dict)
    walk_forward: dict[str, Any] = field(default_factory=dict)
    robustness: dict[str, Any] = field(default_factory=dict)
    cost_stress: dict[str, Any] = field(default_factory=dict)
    paper: dict[str, Any] = field(default_factory=dict)
    parity: dict[str, Any] = field(default_factory=dict)
    neighborhood: dict[str, Any] = field(default_factory=dict)
    live_execution: str = "DENY"
    phase_7: str = "DENY"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _cost_stress(compute, ohlcv: pd.DataFrame) -> tuple[dict[str, Any], str]:
    base = CostConfig()
    multipliers = (("BASE_COST", 1.0), ("1.5X_COST", 1.5), ("2X_COST", 2.0))
    rows: dict[str, Any] = {}
    sharpes: list[float] = []
    for label, m in multipliers:
        cfg = CostConfig(fee_rate=base.fee_rate * m, slippage_bps=base.slippage_bps * m)
        met = run_backtest(compute(ohlcv), ohlcv, cfg)["metrics"]
        rows[label] = met
        if met.get("sharpe") is not None:
            sharpes.append(float(met["sharpe"]))
    base_s = rows["BASE_COST"].get("sharpe")
    x15 = rows["1.5X_COST"].get("sharpe")
    x2 = rows["2X_COST"].get("sharpe")
    status = "PASS"
    if base_s is None or float(base_s) <= 0:
        status = "FAIL"
    elif x15 is not None and float(x15) <= 0 and float(base_s) > 0:
        status = "FAIL"  # dies under mild cost increase
    elif x2 is not None and float(x2) < -0.5:
        status = "FAIL"
    return {"multipliers": rows, "status": status}, status


def _oos_flag(oos: dict) -> str:
    oos_m = oos.get("out_of_sample") or {}
    is_m = oos.get("in_sample") or {}
    oos_s = oos_m.get("sharpe")
    is_s = is_m.get("sharpe")
    deg = oos.get("sharpe_degradation")
    if oos_s is None:
        return "INSUFFICIENT"
    if float(oos_s) <= 0:
        return "FAIL"
    if deg is not None and float(deg) > 1.0 and is_s is not None and float(is_s) > 0.5:
        return "FAIL"
    return "PASS"


def _wf_flag(wf: dict) -> str:
    summary = wf.get("summary") or {}
    pr = summary.get("positive_ratio")
    if pr is None or not wf.get("folds"):
        return "INSUFFICIENT"
    if float(pr) < 0.4:
        return "FAIL"
    if float(pr) < 0.5:
        return "INSUFFICIENT"
    return "PASS"


def _rob_flag(rob: dict, sens: dict) -> str:
    score = rob.get("score")
    sens_pr = (sens.get("summary") or {}).get("positive_ratio")
    if score is None:
        return "INSUFFICIENT"
    if float(score) < 40:
        return "FAIL"
    if sens_pr is not None and float(sens_pr) < 0.35:
        return "FAIL"  # only a knife-edge param works
    if float(score) < 55:
        return "INSUFFICIENT"
    return "PASS"


def validate_candidate(
    candidate: BaselineCandidate,
    *,
    ohlcv: pd.DataFrame | None = None,
    write_graveyard: bool = True,
    paper_status: str = "INSUFFICIENT",
    parity_status: str = "INSUFFICIENT",
) -> StrategyValidationReport:
    if ohlcv is None:
        _ref, ohlcv = resolve_dataset(candidate.market)
        if ohlcv is None:
            gates = GateChecklist(notes=["dataset missing"])
            dec = decide_outcome(gates, overfit_risk="HIGH", reject_hard=True)
            return StrategyValidationReport(
                strategy_id=candidate.strategy_id,
                strategy_version=candidate.strategy_version,
                family=candidate.family,
                hypothesis=candidate.hypothesis,
                market=candidate.market,
                timeframe=candidate.timeframe,
                decision=dec.decision,
                overfit_risk=dec.overfit_risk,
                gates=dec.gates.to_dict(),
                reasons=dec.reasons + ["no dataset"],
            )

    compute = candidate.signal_factory(candidate.base_params)
    cost = CostConfig()

    metrics_full = compute_extended_metrics(compute(ohlcv), ohlcv, cost)
    oos = evaluate_oos(compute, ohlcv, cost_config=cost)
    wf = walk_forward(compute, ohlcv, cost_config=cost, n_splits=3)
    variants = [
        (
            "_".join(f"{k}{v}" for k, v in sorted(p.items())),
            candidate.signal_factory(p),
        )
        for p in candidate.neighborhood
    ]
    sens = sensitivity(variants, ohlcv, cost_config=cost)
    rob = robustness_score(oos, wf, sens)
    cost_payload, cost_flag = _cost_stress(compute, ohlcv)

    gates = GateChecklist(
        oos=_oos_flag(oos),  # type: ignore[arg-type]
        walk_forward=_wf_flag(wf),  # type: ignore[arg-type]
        robustness=_rob_flag(rob, sens),  # type: ignore[arg-type]
        cost_stress=cost_flag,  # type: ignore[arg-type]
        paper=paper_status,  # type: ignore[arg-type]
        parity=parity_status,  # type: ignore[arg-type]
    )

    overfit = assess_overfit_risk(
        param_count=candidate.param_count,
        trade_count=int(metrics_full.get("trade_count") or 0),
        periods=int(metrics_full.get("periods") or 0),
        sens_positive_ratio=(sens.get("summary") or {}).get("positive_ratio"),
        sharpe_degradation=oos.get("sharpe_degradation"),
        wf_positive_ratio=(wf.get("summary") or {}).get("positive_ratio"),
        top_win_concentration=metrics_full.get("top_win_concentration"),
    )
    decision: DecisionResult = decide_outcome(gates, overfit_risk=overfit)

    report = StrategyValidationReport(
        strategy_id=candidate.strategy_id,
        strategy_version=candidate.strategy_version,
        family=candidate.family,
        hypothesis=candidate.hypothesis,
        market=candidate.market,
        timeframe=candidate.timeframe,
        decision=decision.decision,
        overfit_risk=decision.overfit_risk,
        gates=decision.gates.to_dict(),
        reasons=decision.reasons,
        metrics_is=oos.get("in_sample") or {},
        metrics_oos=oos.get("out_of_sample") or {},
        walk_forward=wf if isinstance(wf, dict) else {},
        robustness=rob,
        cost_stress=cost_payload,
        paper={"status": paper_status, "note": "Batch-001: long Paper window not yet run"},
        parity={"status": parity_status, "note": "Requires Paper evidence; not skipped as PASS"},
        neighborhood=sens,
    )
    # Attach full-sample extended metrics under robustness evidence
    report.robustness = {**rob, "full_sample_extended": metrics_full}

    if decision.decision == "REJECT" and write_graveyard:
        append_reject(
            GraveyardEntry(
                strategy_id=candidate.strategy_id,
                strategy_version=candidate.strategy_version,
                hypothesis=candidate.hypothesis,
                market=candidate.market,
                timeframe=candidate.timeframe,
                validation_results={
                    "gates": gates.to_dict(),
                    "overfit_risk": overfit,
                    "robustness_score": rob.get("score"),
                    "metrics_oos": oos.get("out_of_sample"),
                },
                failure_reason="; ".join(decision.reasons) or "REJECT",
                rejected_at="",
            )
        )
    return report
