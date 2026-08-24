"""Backtest vs Paper comparison report (Phase 6)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ParityStatus = Literal[
    "CONSISTENT",
    "EXPECTED_EXECUTION_DRIFT",
    "MATERIAL_DRIFT",
    "INVALID_COMPARISON",
]


@dataclass
class BacktestPaperCompareReport:
    strategy_spec_id: str
    strategy_spec_version: str
    parity_status: ParityStatus = "INVALID_COMPARISON"
    signal_frequency_backtest: float = 0.0
    signal_frequency_paper: float = 0.0
    entry_distribution_delta: dict[str, float] = field(default_factory=dict)
    avg_holding_period_backtest: float = 0.0
    avg_holding_period_paper: float = 0.0
    slippage_paper: float = 0.0
    fill_delay_paper_ms: float = 0.0
    pnl_backtest: float = 0.0
    pnl_paper: float = 0.0
    win_rate_backtest: float = 0.0
    win_rate_paper: float = 0.0
    exposure_backtest: float = 0.0
    exposure_paper: float = 0.0
    orders_backtest: int = 0
    orders_paper: int = 0
    fills_paper: int = 0
    summary_zh: list[str] = field(default_factory=list)
    backtest_return: float = 0.0
    paper_return: float = 0.0
    backtest_max_dd: float = 0.0
    paper_max_dd: float = 0.0
    signal_count_delta: float = 0.0
    pnl_delta: float = 0.0
    slippage_delta: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parity_status(
    *,
    bt_signals: float,
    pp_signals: float,
    bt_pnl: float,
    pp_pnl: float,
    has_backtest: bool,
) -> ParityStatus:
    if not has_backtest:
        return "INVALID_COMPARISON"
    if bt_signals <= 0 and pp_signals <= 0:
        return "CONSISTENT"
    signal_ratio = (pp_signals / bt_signals) if bt_signals > 0 else 0.0
    pnl_drift = abs(pp_pnl - bt_pnl)
    if signal_ratio > 2.0 or signal_ratio < 0.4:
        return "MATERIAL_DRIFT"
    if pnl_drift > max(50.0, abs(bt_pnl) * 0.35):
        return "MATERIAL_DRIFT"
    if pnl_drift > max(5.0, abs(bt_pnl) * 0.15):
        return "EXPECTED_EXECUTION_DRIFT"
    return "CONSISTENT"


def build_backtest_paper_report(
    *,
    strategy_spec_id: str,
    strategy_spec_version: str,
    backtest_metrics: dict[str, Any],
    paper_metrics: dict[str, Any],
) -> BacktestPaperCompareReport:
    bt_signals = float(backtest_metrics.get("signals_total", backtest_metrics.get("fill_count", 0)))
    pp_signals = float(paper_metrics.get("signals_total", paper_metrics.get("orders_total", 0)))
    bt_pnl = float(backtest_metrics.get("pnl", backtest_metrics.get("total_pnl", 0) or 0))
    pp_pnl = float(paper_metrics.get("realized_pnl", 0) or 0)
    bt_wr = float(backtest_metrics.get("win_rate", 0) or 0)
    pp_wr = float(paper_metrics.get("win_rate", 0) or 0)
    bt_hold = float(backtest_metrics.get("avg_holding_period", 0) or 0)
    pp_hold = float(paper_metrics.get("avg_holding_period", 0) or 0)
    slip = float(paper_metrics.get("slippage", 0) or 0)
    delay = float(paper_metrics.get("fill_delay_ms", 0) or 0)
    bt_exp = float(backtest_metrics.get("exposure", 0) or 0)
    pp_exp = float(paper_metrics.get("exposure", paper_metrics.get("position_qty", 0)) or 0)
    bt_ret = float(backtest_metrics.get("return_pct", 0) or 0)
    pp_ret = float(paper_metrics.get("return_pct", 0) or 0)
    bt_dd = float(backtest_metrics.get("max_drawdown", 0) or 0)
    pp_dd = float(paper_metrics.get("max_drawdown", 0) or 0)
    has_bt = bool(backtest_metrics.get("from_spec_backtest"))

    parity = _parity_status(
        bt_signals=bt_signals,
        pp_signals=pp_signals,
        bt_pnl=bt_pnl,
        pp_pnl=pp_pnl,
        has_backtest=has_bt,
    )

    summary: list[str] = []
    if pp_signals > bt_signals * 1.5 and bt_signals > 0:
        summary.append("实时信号频率明显高于回测，可能存在过拟合或数据频率差异。")
    elif bt_signals > 0 and pp_signals < bt_signals * 0.5:
        summary.append("实时信号偏少，可能受 DATA_STALE、风控暂停或预热不足影响。")
    else:
        summary.append("信号频率与回测大致一致（或样本尚短）。")

    if abs(pp_pnl - bt_pnl) > max(1.0, abs(bt_pnl) * 0.2):
        summary.append(f"盈亏出现漂移：回测 {bt_pnl:+.2f} vs 模拟 {pp_pnl:+.2f}。")
    else:
        summary.append("盈亏差异在当前样本内可接受。")

    if slip > 0:
        summary.append(f"模拟滑点约 {slip:.4f}。")
    if delay > 0:
        summary.append(f"成交延迟约 {delay:.0f} ms。")
    summary.append(f"一致性判定：{parity}。")

    return BacktestPaperCompareReport(
        strategy_spec_id=strategy_spec_id,
        strategy_spec_version=strategy_spec_version,
        parity_status=parity,
        signal_frequency_backtest=bt_signals,
        signal_frequency_paper=pp_signals,
        entry_distribution_delta={
            "signal_delta": pp_signals - bt_signals,
            "pnl_delta": pp_pnl - bt_pnl,
        },
        avg_holding_period_backtest=bt_hold,
        avg_holding_period_paper=pp_hold,
        slippage_paper=slip,
        fill_delay_paper_ms=delay,
        pnl_backtest=bt_pnl,
        pnl_paper=pp_pnl,
        win_rate_backtest=bt_wr,
        win_rate_paper=pp_wr,
        exposure_backtest=bt_exp,
        exposure_paper=pp_exp,
        orders_backtest=int(backtest_metrics.get("orders_total", backtest_metrics.get("fill_count", 0)) or 0),
        orders_paper=int(paper_metrics.get("orders_total", 0) or 0),
        fills_paper=int(paper_metrics.get("fills_total", 0) or 0),
        summary_zh=summary,
        backtest_return=bt_ret,
        paper_return=pp_ret,
        backtest_max_dd=bt_dd,
        paper_max_dd=pp_dd,
        signal_count_delta=pp_signals - bt_signals,
        pnl_delta=pp_pnl - bt_pnl,
        slippage_delta=slip,
    )
