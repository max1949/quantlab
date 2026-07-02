"""因子信号快速评估 — 回测 + OOS + IC (模板/公式/Python 共用)。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd

from engine.backtest import run_backtest
from engine.cost_model import CostConfig
from engine.factor_metrics import IC_HORIZON_BY_TF, composite_factor_score, factor_ic
from engine.research_quality import assess_scan_preview
from engine.walk_forward import evaluate_oos

SignalFn = Callable[[pd.DataFrame], pd.Series]


def evaluate_signal(
    ohlcv: pd.DataFrame,
    signal_fn: SignalFn,
    *,
    label: str,
    kind: str = "formula",
    cost_config: CostConfig | None = None,
    oos_ratio: float = 0.3,
    ic_horizon: int | None = None,
    timeframe: str = "1d",
) -> dict[str, Any]:
    if "close" not in ohlcv.columns:
        raise ValueError("行情缺少 close")
    horizon = ic_horizon if ic_horizon is not None else IC_HORIZON_BY_TF.get(timeframe, 1)
    cfg = cost_config or CostConfig()

    full_signal = signal_fn(ohlcv)
    bt = run_backtest(full_signal, ohlcv, cfg)
    metrics = bt["metrics"]
    oos = evaluate_oos(signal_fn, ohlcv, cfg, oos_ratio=oos_ratio)
    ic = factor_ic(full_signal, ohlcv["close"], horizon=horizon)
    oos_sharpe = (oos.get("out_of_sample") or {}).get("sharpe")
    score = composite_factor_score(
        sharpe=metrics.get("sharpe"),
        oos_sharpe=oos_sharpe,
        ic_mean=ic.get("ic_mean"),
        turnover=metrics.get("turnover"),
    )
    preview = assess_scan_preview(
        sharpe=metrics.get("sharpe"),
        oos_sharpe=oos_sharpe,
        ic_mean=ic.get("ic_mean"),
        turnover=metrics.get("turnover"),
    )
    coach = _coach_summary(
        kind, label, score, oos_sharpe, ic.get("ic_mean"), metrics.get("turnover")
    )
    return {
        "score": score,
        "sharpe": metrics.get("sharpe"),
        "oos_sharpe": oos_sharpe,
        "ic_mean": ic.get("ic_mean"),
        "turnover": metrics.get("turnover"),
        "max_drawdown": metrics.get("max_drawdown"),
        "publish_promising": preview.promising,
        "publish_hints": preview.hints,
        "coach_summary": coach,
    }


def _coach_summary(
    kind: str,
    label: str,
    score: float | None,
    oos_sharpe: float | None,
    ic_mean: float | None,
    turnover: float | None,
) -> str:
    short = label if len(label) <= 48 else f"{label[:45]}…"
    if kind == "python":
        lines = [f"Python 因子快评综合分 {score}。"]
    elif kind == "template":
        lines = [f"模板参数 {short} 快评综合分 {score}。"]
    else:
        lines = [f"公式「{short}」快评综合分 {score}。"]
    if oos_sharpe is not None and oos_sharpe < 0.3:
        if kind == "python":
            hint = "样本外偏弱，可简化代码或调整窗口后再试。"
        elif kind == "template":
            hint = "样本外偏弱，可调整参数或换模板后再试。"
        else:
            hint = "样本外偏弱，可简化表达式或调整窗口后再试。"
        lines.append(hint)
    elif oos_sharpe is not None and oos_sharpe >= 0.5:
        lines.append("表现尚可，确认后可创建因子并跑完整科学验证。")
    if ic_mean is not None and abs(ic_mean) < 0.02:
        lines.append("IC 偏低，预测力有限。")
    if turnover is not None and turnover > 40:
        lines.append("换手率偏高，注意实盘成本。")
    return " ".join(lines)
