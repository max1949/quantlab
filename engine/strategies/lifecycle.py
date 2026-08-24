"""Strategy Spec lifecycle + Validation/Robustness gate wiring (reuse existing engines)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

import pandas as pd

from engine.strategies.spec import StrategySpec
from engine.strategies.validate import validate_spec

Lifecycle = Literal[
    "DRAFT",
    "BACKTESTED",
    "VALIDATED",
    "ROBUST",
    "PAPER_READY",
]

GateStatus = Literal["PASS", "WARN", "FAIL"]


@dataclass
class ValidationGateResult:
    status: GateStatus
    lifecycle: Lifecycle
    oos: dict[str, Any] | None = None
    walk_forward: dict[str, Any] | None = None
    sensitivity: dict[str, Any] | None = None
    robustness: dict[str, Any] | None = None
    strategy_spec_id: str = ""
    strategy_spec_version: str = ""
    summary_zh: str = ""
    detail_zh: list[str] = field(default_factory=list)
    paper_ready: bool = False
    paper_runtime: bool = False
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def explain_robustness_zh(status: GateStatus, robustness: dict[str, Any] | None) -> dict[str, str]:
    score = None
    if robustness:
        score = robustness.get("score") or robustness.get("robustness_score")
    if status == "PASS":
        level = "较好"
        advice = "可标记为稳健候选；本阶段仍不自动进入模拟运行。"
    elif status == "WARN":
        level = "中等"
        advice = "继续研究，不建议进入模拟交易。"
    else:
        level = "偏弱"
        advice = "先修复数据或规则，再谈稳健性。"
    body = (
        f"稳健性：{level}"
        + (f"（分数约 {score}）" if score is not None else "")
        + "。这个策略在不同检验下表现"
        + ("相对稳定。" if status == "PASS" else "仍有明显波动或退化。")
    )
    return {"level_zh": level, "summary_zh": body, "advice_zh": advice}


def _ema_signal(ohlcv: pd.DataFrame, fast: int, slow: int) -> pd.Series:
    close = ohlcv["close"].astype(float)
    ema_f = close.ewm(span=fast, adjust=False).mean()
    ema_s = close.ewm(span=slow, adjust=False).mean()
    return (ema_f - ema_s).fillna(0.0)


def run_validation_gate(
    spec: StrategySpec | dict[str, Any],
    ohlcv: pd.DataFrame,
    *,
    signal: pd.Series | None = None,
) -> ValidationGateResult:
    """Wire existing OOS / WF / sensitivity / robustness to a Spec version."""
    if isinstance(spec, dict):
        spec = validate_spec(spec)

    fast, slow = 10, 20
    for side in (spec.entry.long, spec.entry.short):
        for cond in side.conditions:
            if cond.type == "ema_cross":
                fast = int(cond.params.get("fast", 10))
                slow = int(cond.params.get("slow", 20))
    if signal is None:
        signal = _ema_signal(ohlcv, fast, slow)

    from engine.backtest import run_backtest
    from engine.cost_model import CostConfig
    from engine.walk_forward import (
        evaluate_oos,
        robustness_score,
        sensitivity,
        walk_forward,
    )

    cost = CostConfig()
    compute = lambda df: _ema_signal(df, fast, slow)  # noqa: E731
    if signal is not None:
        # Align provided signal path: wrap constant series builder from full frame
        full_signal = signal
        compute = lambda df: full_signal.reindex(df.index).fillna(0.0)  # noqa: E731

    bt = run_backtest(compute(ohlcv), ohlcv, cost)
    oos = evaluate_oos(compute, ohlcv, cost_config=cost)
    wf = walk_forward(compute, ohlcv, cost_config=cost, n_splits=3)
    variants = [
        (f"ema_{f}_{s}", (lambda df, ff=f, ss=s: _ema_signal(df, ff, ss)))
        for f, s in ((max(2, fast - 2), slow), (fast, slow), (fast, slow + 2), (fast + 2, slow + 2))
    ]
    sens = sensitivity(variants, ohlcv, cost_config=cost)
    robustness = robustness_score(oos, wf, sens)

    score = robustness.get("score")
    if score is not None and float(score) >= 70:
        status: GateStatus = "PASS"
        lifecycle: Lifecycle = "ROBUST"
        paper_ready = True
    elif score is not None and float(score) >= 45:
        status = "WARN"
        lifecycle = "VALIDATED"
        paper_ready = False
    else:
        status = "FAIL" if score is not None else "WARN"
        lifecycle = "BACKTESTED"
        paper_ready = False

    if not (bt.get("metrics") or {}):
        status = "FAIL"
        lifecycle = "DRAFT"
        paper_ready = False

    expl = explain_robustness_zh(status, robustness)
    return ValidationGateResult(
        status=status,
        lifecycle=lifecycle,
        oos=oos if isinstance(oos, dict) else {"raw": oos},
        walk_forward=wf if isinstance(wf, dict) else {"raw": wf},
        sensitivity=sens if isinstance(sens, dict) else {"raw": sens},
        robustness=robustness,
        strategy_spec_id=spec.strategy.id,
        strategy_spec_version=spec.strategy.version,
        summary_zh=expl["summary_zh"],
        detail_zh=[expl["advice_zh"], f"生命周期：{lifecycle}", "PAPER_RUNTIME=OFF", "LIVE=HOLD"],
        paper_ready=paper_ready,
        paper_runtime=False,
        evidence={
            "backtest_metrics": bt.get("metrics"),
            "spec_hash": spec.content_hash(),
            "gate": "VALIDATION_GATE",
            "spec_version": spec.strategy.version,
        },
    )


def strategy_status_card(
    *,
    name: str,
    lifecycle: Lifecycle,
    data_gate_status: str,
    validation: ValidationGateResult | None,
    max_drawdown: float | None = None,
    ai_verdict_zh: str = "",
) -> dict[str, Any]:
    enter_sim = "暂不建议"
    if validation and validation.paper_ready:
        enter_sim = "可标记 PAPER_READY（运行仍关闭）"
    return {
        "name": name,
        "lifecycle": lifecycle,
        "research_status_zh": f"研究状态：{lifecycle}",
        "robustness_zh": validation.summary_zh if validation else "稳健性：待评估",
        "data_quality_zh": f"数据质量：{data_gate_status}",
        "max_drawdown_zh": (
            f"最大回撤：{abs(float(max_drawdown)) * 100:.1f}%"
            if max_drawdown is not None
            else "最大回撤：—"
        ),
        "enter_simulation_zh": f"进入模拟：{enter_sim}",
        "ai_conclusion_zh": ai_verdict_zh or "等待 AI 结论",
    }
