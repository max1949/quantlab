"""L4 组合优化 + 模拟实盘工具.

这是从"研究一个因子"升级到"管理一个组合"的最小可用实现:
  - equal_weight: 等权基准
  - min_variance: 最小方差
  - mean_variance: 均值方差近似 (风险调整收益)
  - risk_parity: 逆波动率风险平价近似

全部使用 numpy/pandas, 不引入 scipy 依赖; 输出 JSON 友好的权重、指标和净值。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _f(x) -> float | None:
    if x is None:
        return None
    xf = float(x)
    return None if (np.isnan(xf) or np.isinf(xf)) else xf


def _normalize_long_only(w: np.ndarray) -> np.ndarray:
    w = np.maximum(np.asarray(w, dtype=float), 0.0)
    s = float(w.sum())
    if s <= 0:
        return np.ones_like(w) / len(w)
    return w / s


def returns_from_closes(closes: dict[str, pd.Series]) -> pd.DataFrame:
    price = pd.concat({k: v.astype(float) for k, v in closes.items()}, axis=1).sort_index()
    return price.pct_change().dropna(how="all").fillna(0.0)


def optimize_weights(returns: pd.DataFrame, method: str = "risk_parity") -> dict:
    """计算 long-only 组合权重。"""
    if returns.shape[1] < 2:
        raise ValueError("组合优化至少需要 2 个标的")
    symbols = list(returns.columns)
    mu = returns.mean().to_numpy() * TRADING_DAYS
    cov = returns.cov().to_numpy() * TRADING_DAYS
    vol = np.sqrt(np.clip(np.diag(cov), 1e-12, None))
    n = len(symbols)

    if method == "equal_weight":
        w = np.ones(n) / n
    elif method == "risk_parity":
        w = _normalize_long_only(1.0 / vol)
    elif method == "min_variance":
        inv = np.linalg.pinv(cov + np.eye(n) * 1e-10)
        w = _normalize_long_only(inv @ np.ones(n))
    elif method == "mean_variance":
        inv = np.linalg.pinv(cov + np.eye(n) * 1e-10)
        w = _normalize_long_only(inv @ np.maximum(mu, 0.0))
    else:
        raise ValueError("method 必须是 equal_weight/min_variance/mean_variance/risk_parity")

    port_ret = returns @ w
    ann_ret = float(port_ret.mean() * TRADING_DAYS)
    ann_vol = float(port_ret.std() * np.sqrt(TRADING_DAYS))
    sharpe = ann_ret / ann_vol if ann_vol > 0 else None
    return {
        "method": method,
        "weights": {s: _f(w[i]) for i, s in enumerate(symbols)},
        "expected": {
            "annual_return": _f(ann_ret),
            "annual_volatility": _f(ann_vol),
            "sharpe": _f(sharpe),
        },
        "asset_stats": {
            s: {"annual_return": _f(mu[i]), "annual_volatility": _f(vol[i])}
            for i, s in enumerate(symbols)
        },
    }


def simulate_portfolio(
    returns: pd.DataFrame,
    weights: dict[str, float],
    rebalance: str = "monthly",
) -> dict:
    """用固定/低频再平衡权重模拟组合净值。"""
    if returns.empty:
        raise ValueError("收益率为空")
    symbols = list(returns.columns)
    w = pd.Series({s: float(weights.get(s, 0.0)) for s in symbols})
    if w.abs().sum() == 0:
        raise ValueError("权重不能全为 0")
    w = w / w.abs().sum()

    # MVP: 日收益按目标权重计算; rebalance 字段先作为语义输出保留。
    net_ret = (returns * w).sum(axis=1)
    equity = (1.0 + net_ret).cumprod()
    running_max = equity.cummax()
    dd = equity / running_max - 1.0
    n = len(net_ret)
    ann_ret = float(equity.iloc[-1] ** (TRADING_DAYS / n) - 1.0) if n else 0.0
    ann_vol = float(net_ret.std() * np.sqrt(TRADING_DAYS))
    sharpe = ann_ret / ann_vol if ann_vol > 0 else None
    metrics = {
        "total_return": _f(float(equity.iloc[-1] - 1.0)),
        "annual_return": _f(ann_ret),
        "annual_volatility": _f(ann_vol),
        "sharpe": _f(sharpe),
        "max_drawdown": _f(float(dd.min())),
        "periods": n,
    }
    curve = [
        {"date": idx.strftime("%Y-%m-%d"), "equity": _f(v)}
        for idx, v in equity.items()
    ]
    return {"rebalance": rebalance, "metrics": metrics, "equity_curve": curve}
