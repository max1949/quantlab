"""样本外 / Walk-Forward / 稳健性验证 (Sprint 5 实现)。

把"一次回测"升级为"可信验证": 一个因子在历史上整体跑得好不算数,
要看它在**样本外**、**不同时间段**、**参数扰动**下是否稳定 —— 这是平台"过程 > 结果"
理念的技术抓手, 用于抑制过拟合。

纯函数: 输入 `compute_signal(df)->Series` 闭包 + 行情, 在各数据切片上独立计算信号
(避免前视/泄漏), 复用 engine.backtest.run_backtest 评估。
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from engine.backtest import run_backtest
from engine.cost_model import CostConfig

SignalFn = Callable[[pd.DataFrame], pd.Series]


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _sharpe(metrics: dict) -> float | None:
    return metrics.get("sharpe")


def holdout_split(
    ohlcv: pd.DataFrame, oos_ratio: float = 0.3
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """按时间顺序切分样本内 (前) / 样本外 (后)。"""
    if not (0.0 < oos_ratio < 1.0):
        raise ValueError("oos_ratio 需在 (0,1) 之间")
    n = ohlcv.shape[0]
    cut = int(n * (1.0 - oos_ratio))
    return ohlcv.iloc[:cut], ohlcv.iloc[cut:]


def evaluate_oos(
    compute_signal: SignalFn,
    ohlcv: pd.DataFrame,
    cost_config: CostConfig | None = None,
    oos_ratio: float = 0.3,
) -> dict:
    """样本外检验: 分别在 IS / OOS 上回测, 给出夏普衰减。"""
    cfg = cost_config or CostConfig()
    is_df, oos_df = holdout_split(ohlcv, oos_ratio)
    is_m = run_backtest(compute_signal(is_df), is_df, cfg)["metrics"]
    oos_m = run_backtest(compute_signal(oos_df), oos_df, cfg)["metrics"]
    is_s, oos_s = _sharpe(is_m), _sharpe(oos_m)
    degradation = (
        None if (is_s is None or oos_s is None) else float(is_s - oos_s)
    )
    return {
        "oos_ratio": oos_ratio,
        "in_sample": is_m,
        "out_of_sample": oos_m,
        "sharpe_degradation": degradation,
    }


def walk_forward(
    compute_signal: SignalFn,
    ohlcv: pd.DataFrame,
    cost_config: CostConfig | None = None,
    n_splits: int = 4,
) -> dict:
    """Walk-Forward: 将时间线切成 n 段, 逐段独立回测, 评估跨期一致性。"""
    if n_splits < 2:
        raise ValueError("n_splits 至少为 2")
    cfg = cost_config or CostConfig()
    n = ohlcv.shape[0]
    bounds = np.linspace(0, n, n_splits + 1, dtype=int)

    folds = []
    sharpes: list[float] = []
    for i in range(n_splits):
        seg = ohlcv.iloc[bounds[i]: bounds[i + 1]]
        if seg.shape[0] < 3:
            continue
        m = run_backtest(compute_signal(seg), seg, cfg)["metrics"]
        folds.append(
            {
                "fold": i + 1,
                "start": str(seg.index.min().date())
                if hasattr(seg.index.min(), "date")
                else str(seg.index.min()),
                "end": str(seg.index.max().date())
                if hasattr(seg.index.max(), "date")
                else str(seg.index.max()),
                "sharpe": m.get("sharpe"),
                "total_return": m.get("total_return"),
            }
        )
        if m.get("sharpe") is not None:
            sharpes.append(float(m["sharpe"]))

    positive_ratio = (
        float(np.mean([s > 0 for s in sharpes])) if sharpes else 0.0
    )
    summary = {
        "n_splits": n_splits,
        "mean_sharpe": float(np.mean(sharpes)) if sharpes else None,
        "std_sharpe": float(np.std(sharpes)) if sharpes else None,
        "positive_ratio": positive_ratio,
    }
    return {"folds": folds, "summary": summary}


def sensitivity(
    variants: list[tuple[str, SignalFn]],
    ohlcv: pd.DataFrame,
    cost_config: CostConfig | None = None,
) -> dict:
    """参数敏感性: 对一组参数变体分别回测, 看表现是否稳定 (而非单点尖峰)。"""
    cfg = cost_config or CostConfig()
    points = []
    sharpes: list[float] = []
    for label, fn in variants:
        m = run_backtest(fn(ohlcv), ohlcv, cfg)["metrics"]
        points.append(
            {"label": label, "sharpe": m.get("sharpe"), "total_return": m.get("total_return")}
        )
        if m.get("sharpe") is not None:
            sharpes.append(float(m["sharpe"]))

    positive_ratio = (
        float(np.mean([s > 0 for s in sharpes])) if sharpes else 0.0
    )
    summary = {
        "n_variants": len(variants),
        "mean_sharpe": float(np.mean(sharpes)) if sharpes else None,
        "std_sharpe": float(np.std(sharpes)) if sharpes else None,
        "min_sharpe": float(np.min(sharpes)) if sharpes else None,
        "positive_ratio": positive_ratio,
    }
    return {"points": points, "summary": summary}


def robustness_score(oos: dict, wf: dict, sens: dict | None) -> dict:
    """综合稳健性评分 (0-100) 与评级。看的是稳定性, 不是单段高收益。"""
    oos_sharpe = oos.get("out_of_sample", {}).get("sharpe")
    oos_comp = _clamp((oos_sharpe or 0.0) / 1.5)
    wf_comp = _clamp(wf.get("summary", {}).get("positive_ratio", 0.0))
    sens_comp = (
        _clamp(sens.get("summary", {}).get("positive_ratio", 0.0))
        if sens and sens.get("summary", {}).get("n_variants", 0) > 1
        else wf_comp  # 无敏感性 (如组合器) 时退化为 WF 一致性
    )

    score = round(100.0 * (0.40 * oos_comp + 0.35 * wf_comp + 0.25 * sens_comp), 1)
    if score >= 70:
        grade = "稳健"
    elif score >= 50:
        grade = "中等"
    elif score >= 30:
        grade = "偏弱"
    else:
        grade = "脆弱"

    notes = []
    if oos_sharpe is not None and oos_sharpe <= 0:
        notes.append("样本外夏普非正, 警惕过拟合。")
    if (oos.get("sharpe_degradation") or 0) > 0.5:
        notes.append("样本外相对样本内明显衰减。")
    if wf.get("summary", {}).get("positive_ratio", 0) < 0.5:
        notes.append("跨期一致性不足 (多数分段未盈利)。")

    return {
        "score": score,
        "grade": grade,
        "components": {"oos": oos_comp, "walk_forward": wf_comp, "sensitivity": sens_comp},
        "notes": notes or ["各维度表现尚可, 可进入下一步竞争性评估。"],
    }
