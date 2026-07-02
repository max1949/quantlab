"""公式因子快速评估 — 在真实行情上跑回测 + OOS + IC (无需先创建因子)。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from engine import formula as ff
from engine.backtest import run_backtest
from engine.cost_model import CostConfig
from engine.factor_metrics import IC_HORIZON_BY_TF, composite_factor_score, factor_ic
from engine.research_quality import assess_scan_preview
from engine.walk_forward import evaluate_oos


def evaluate_formula(
    ohlcv: pd.DataFrame,
    expr: str,
    *,
    cost_config: CostConfig | None = None,
    oos_ratio: float = 0.3,
    ic_horizon: int | None = None,
    timeframe: str = "1d",
) -> dict[str, Any]:
    """对公式表达式做快速因子评估, 返回可展示指标与发布预览提示。"""
    if "close" not in ohlcv.columns:
        raise ValueError("行情缺少 close")
    ff.validate(expr)
    horizon = ic_horizon if ic_horizon is not None else IC_HORIZON_BY_TF.get(timeframe, 1)
    cfg = cost_config or CostConfig()
    clean = expr.strip()

    def signal_fn(df: pd.DataFrame) -> pd.Series:
        return ff.compute(df, clean)

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
    coach = _coach_summary(clean, score, oos_sharpe, ic.get("ic_mean"), metrics.get("turnover"))
    return {
        "expr": clean,
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
    expr: str,
    score: float | None,
    oos_sharpe: float | None,
    ic_mean: float | None,
    turnover: float | None,
) -> str:
    label = expr if len(expr) <= 48 else f"{expr[:45]}…"
    lines = [f"公式「{label}」快评综合分 {score}。"]
    if oos_sharpe is not None and oos_sharpe < 0.3:
        lines.append("样本外偏弱，可简化表达式或调整窗口后再试。")
    elif oos_sharpe is not None and oos_sharpe >= 0.5:
        lines.append("表现尚可，确认后可创建因子并跑完整科学验证。")
    if ic_mean is not None and abs(ic_mean) < 0.02:
        lines.append("IC 偏低，预测力有限。")
    if turnover is not None and turnover > 40:
        lines.append("换手率偏高，注意实盘成本。")
    return " ".join(lines)
