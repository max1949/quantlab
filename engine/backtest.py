"""回测 (Sprint 4 实现)。

纯函数: 输入因子信号 + 行情 OHLCV + 成本配置, 输出指标 + 净值曲线。
不读数据库, 不发网络。单标的择时口径:
  - 仓位 position = sign(signal) ∈ {-1, 0, +1} (多/空/空仓)
  - 当期收益 = 上期仓位 × 当期标的收益 − 当期交易成本 (上期仓位避免前视偏差)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.cost_model import CostConfig, apply_costs, turnover

TRADING_DAYS = 252


def _f(x) -> float | None:
    """转 JSON 友好的 float (NaN/inf/complex -> None)。"""
    if x is None:
        return None
    if isinstance(x, complex):
        return None
    try:
        xf = float(x)
    except (TypeError, ValueError):
        return None
    return None if (np.isnan(xf) or np.isinf(xf)) else xf


def _annual_return(final_equity: float, n: int, mean: float) -> float | None:
    if n <= 0:
        return 0.0
    if final_equity > 0:
        return final_equity ** (TRADING_DAYS / n) - 1.0
    return (1.0 + mean) ** TRADING_DAYS - 1.0


def signal_to_positions(signal: pd.Series) -> pd.Series:
    """因子信号 -> 仓位 (符号)。NaN 视为空仓。"""
    return np.sign(signal.fillna(0.0)).astype(float)


def run_backtest(
    signal: pd.Series,
    ohlcv: pd.DataFrame,
    cost_config: CostConfig | None = None,
) -> dict:
    """运行回测, 返回 {metrics, equity_curve} (JSON 友好)。"""
    if "close" not in ohlcv.columns:
        raise ValueError("行情缺少 close 列")
    cfg = cost_config or CostConfig()

    close = ohlcv["close"].astype(float)
    asset_ret = close.pct_change().fillna(0.0)

    positions = signal_to_positions(signal).reindex(close.index).fillna(0.0)
    lagged = positions.shift(1).fillna(0.0)  # 避免前视

    costs = apply_costs(positions, cfg)
    net_ret = lagged * asset_ret - costs
    equity = (1.0 + net_ret).cumprod()

    n = int(net_ret.shape[0])
    std = float(net_ret.std())
    mean = float(net_ret.mean())
    final_equity = float(equity.iloc[-1]) if n else 1.0

    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    max_dd = float(drawdown.min()) if n else 0.0

    nonzero = net_ret[lagged != 0.0]
    win_rate = float((nonzero > 0).mean()) if not nonzero.empty else None
    trade_count = int((turnover(positions) > 0).sum())
    total_turnover = float(turnover(positions).sum())

    annual_return = _annual_return(final_equity, n, mean)
    annual_vol = std * np.sqrt(TRADING_DAYS)
    sharpe = (mean / std * np.sqrt(TRADING_DAYS)) if std > 0 else None

    metrics = {
        "total_return": _f(final_equity - 1.0),
        "annual_return": _f(annual_return),
        "annual_volatility": _f(annual_vol),
        "sharpe": _f(sharpe),
        "max_drawdown": _f(max_dd),
        "win_rate": _f(win_rate),
        "trade_count": trade_count,
        "turnover": _f(total_turnover),
        "periods": n,
    }

    equity_curve = [
        {"date": idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx),
         "equity": _f(val)}
        for idx, val in equity.items()
    ]

    return {"metrics": metrics, "equity_curve": equity_curve}
