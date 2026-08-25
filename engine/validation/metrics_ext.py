"""Extended risk/return metrics for Strategy Validation (research-only)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.backtest import TRADING_DAYS, signal_to_positions
from engine.cost_model import CostConfig, apply_costs, turnover


def _f(x) -> float | None:
    if x is None:
        return None
    try:
        xf = float(x)
    except (TypeError, ValueError):
        return None
    return None if (np.isnan(xf) or np.isinf(xf)) else xf


def compute_extended_metrics(
    signal: pd.Series,
    ohlcv: pd.DataFrame,
    cost_config: CostConfig | None = None,
) -> dict:
    """Return/risk/risk-adjusted suite required by the Validation Gate."""
    cfg = cost_config or CostConfig()
    close = ohlcv["close"].astype(float)
    asset_ret = close.pct_change(fill_method=None).fillna(0.0)
    positions = signal_to_positions(signal).reindex(close.index).fillna(0.0)
    lagged = positions.shift(1).fillna(0.0)
    costs = apply_costs(positions, cfg)
    net_ret = lagged * asset_ret - costs
    equity = (1.0 + net_ret).cumprod()
    n = int(net_ret.shape[0])
    if n == 0:
        return {}

    std = float(net_ret.std())
    mean = float(net_ret.mean())
    final_equity = float(equity.iloc[-1])
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    max_dd = float(drawdown.min())

    # Drawdown duration (bars underwater)
    underwater = drawdown < 0
    dd_dur = 0
    cur = 0
    for flag in underwater.tolist():
        cur = cur + 1 if flag else 0
        dd_dur = max(dd_dur, cur)

    downside = net_ret[net_ret < 0]
    downside_std = float(downside.std()) if len(downside) else 0.0
    sortino = (
        (mean / downside_std * np.sqrt(TRADING_DAYS)) if downside_std > 0 else None
    )
    annual_return = (
        final_equity ** (TRADING_DAYS / n) - 1.0 if final_equity > 0 else None
    )
    calmar = (
        (annual_return / abs(max_dd))
        if annual_return is not None and max_dd < 0
        else None
    )
    sharpe = (mean / std * np.sqrt(TRADING_DAYS)) if std > 0 else None

    # Trade-level approx: each non-zero turnover start as a trade PnL chunk
    trade_pnls: list[float] = []
    in_trade = False
    pnl_acc = 0.0
    for i in range(n):
        pos = float(lagged.iloc[i])
        r = float(net_ret.iloc[i])
        if abs(pos) > 0:
            in_trade = True
            pnl_acc += r
        elif in_trade:
            trade_pnls.append(pnl_acc)
            pnl_acc = 0.0
            in_trade = False
    if in_trade:
        trade_pnls.append(pnl_acc)

    wins = [p for p in trade_pnls if p > 0]
    losses = [p for p in trade_pnls if p < 0]
    gross_profit = float(sum(wins)) if wins else 0.0
    gross_loss = float(abs(sum(losses))) if losses else 0.0
    profit_factor = (
        (gross_profit / gross_loss) if gross_loss > 0 else (None if not wins else 99.0)
    )
    expectancy = float(np.mean(trade_pnls)) if trade_pnls else None
    avg_trade = expectancy
    worst_trade = float(min(trade_pnls)) if trade_pnls else None
    worst_day = float(net_ret.min()) if n else None

    consec = 0
    max_consec = 0
    for p in trade_pnls:
        if p < 0:
            consec += 1
            max_consec = max(max_consec, consec)
        else:
            consec = 0

    # Concentration: top trades share of gross profit
    top_share = None
    if wins and gross_profit > 0:
        top_n = sorted(wins, reverse=True)[: max(1, len(wins) // 10 or 1)]
        top_share = float(sum(top_n) / gross_profit)

    return {
        "total_return": _f(final_equity - 1.0),
        "cagr": _f(annual_return),
        "net_pnl": _f(final_equity - 1.0),
        "profit_factor": _f(profit_factor),
        "expectancy": _f(expectancy),
        "average_trade": _f(avg_trade),
        "max_drawdown": _f(max_dd),
        "drawdown_duration_bars": int(dd_dur),
        "volatility": _f(std * np.sqrt(TRADING_DAYS)),
        "worst_day": _f(worst_day),
        "worst_trade": _f(worst_trade),
        "consecutive_losses": int(max_consec),
        "sharpe": _f(sharpe),
        "sortino": _f(sortino),
        "calmar": _f(calmar),
        "trade_count": int((turnover(positions) > 0).sum()),
        "top_win_concentration": _f(top_share),
        "periods": n,
    }
