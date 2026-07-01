"""截面多标的回测 (L2).

输入多个标的的因子序列与收盘价, 每天按因子分数排序:
  - 做多分数最高的一组
  - 做空分数最低的一组
  - 等权组合, 仓位滞后一日执行以避免前视

这是研究员从"单标的择时"升级到"多标的横向比较"的第一步。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.cost_model import CostConfig

TRADING_DAYS = 252


def _f(x) -> float | None:
    if x is None:
        return None
    xf = float(x)
    return None if (np.isnan(xf) or np.isinf(xf)) else xf


def _metrics(net_ret: pd.Series, equity: pd.Series, weights: pd.DataFrame) -> dict:
    n = int(net_ret.shape[0])
    std = float(net_ret.std())
    mean = float(net_ret.mean())
    final_equity = float(equity.iloc[-1]) if n else 1.0
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    max_dd = float(drawdown.min()) if n else 0.0
    annual_return = final_equity ** (TRADING_DAYS / n) - 1.0 if n else 0.0
    annual_vol = std * np.sqrt(TRADING_DAYS)
    sharpe = (mean / std * np.sqrt(TRADING_DAYS)) if std > 0 else None
    turnover = weights.diff().abs()
    if not turnover.empty:
        turnover.iloc[0] = weights.iloc[0].abs()
    return {
        "total_return": _f(final_equity - 1.0),
        "annual_return": _f(annual_return),
        "annual_volatility": _f(annual_vol),
        "sharpe": _f(sharpe),
        "max_drawdown": _f(max_dd),
        "win_rate": _f((net_ret[net_ret != 0] > 0).mean()) if (net_ret != 0).any() else None,
        "turnover": _f(turnover.sum(axis=1).sum()),
        "periods": n,
    }


def _rank_weights(scores: pd.DataFrame, top_n: int = 1, long_short: bool = True) -> pd.DataFrame:
    if top_n < 1:
        raise ValueError("top_n 必须 >= 1")
    if scores.shape[1] < 2:
        raise ValueError("截面回测至少需要 2 个标的")
    top_n = min(top_n, scores.shape[1] // (2 if long_short else 1))
    rows = []
    for _, row in scores.iterrows():
        valid = row.dropna()
        w = pd.Series(0.0, index=scores.columns)
        if valid.shape[0] >= (top_n * (2 if long_short else 1)):
            longs = valid.nlargest(top_n).index
            w.loc[longs] = 1.0 / top_n
            if long_short:
                shorts = valid.nsmallest(top_n).index
                w.loc[shorts] = -1.0 / top_n
        rows.append(w)
    return pd.DataFrame(rows, index=scores.index, columns=scores.columns)


def run_cross_section_backtest(
    signals: dict[str, pd.Series],
    closes: dict[str, pd.Series],
    cost_config: CostConfig | None = None,
    top_n: int = 1,
    long_short: bool = True,
) -> dict:
    """运行截面组合回测, 返回指标、净值和最近持仓。"""
    if set(signals) != set(closes):
        raise ValueError("signals 和 closes 的标的集合必须一致")
    if len(signals) < 2:
        raise ValueError("截面回测至少需要 2 个标的")

    cfg = cost_config or CostConfig()
    scores = pd.concat({k: v.astype(float) for k, v in signals.items()}, axis=1).sort_index()
    price = pd.concat({k: v.astype(float) for k, v in closes.items()}, axis=1).sort_index()
    common = scores.index.intersection(price.index)
    scores = scores.loc[common]
    price = price.loc[common]
    asset_ret = price.pct_change().fillna(0.0)

    weights = _rank_weights(scores, top_n=top_n, long_short=long_short)
    lagged = weights.shift(1).fillna(0.0)
    gross_ret = (lagged * asset_ret).sum(axis=1)

    turnover = weights.diff().abs()
    if not turnover.empty:
        turnover.iloc[0] = weights.iloc[0].abs()
    costs = turnover.sum(axis=1) * cfg.per_turnover_cost
    net_ret = gross_ret - costs
    equity = (1.0 + net_ret).cumprod()

    equity_curve = [
        {"date": idx.strftime("%Y-%m-%d"), "equity": _f(val)}
        for idx, val in equity.items()
    ]
    latest_weights = {
        symbol: _f(weight)
        for symbol, weight in weights.iloc[-1].items()
    } if not weights.empty else {}

    return {
        "metrics": _metrics(net_ret, equity, weights),
        "equity_curve": equity_curve,
        "latest_weights": latest_weights,
        "symbols": list(signals.keys()),
        "top_n": top_n,
        "long_short": long_short,
    }
