"""PaperRun portfolio accounting — equity curve + run summary (Phase 6)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class EquityPoint:
    timestamp: str
    equity: float
    cash: float
    unrealized_pnl: float
    realized_pnl: float
    drawdown: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunPerformanceSummary:
    start_time: str | None = None
    end_time: str | None = None
    duration_seconds: float = 0.0
    initial_equity: float = 0.0
    final_equity: float = 0.0
    initial_cash: float = 0.0
    cash: float = 0.0
    balance: float = 0.0
    net_pnl: float = 0.0
    gross_pnl: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    return_pct: float = 0.0
    max_drawdown: float = 0.0
    peak_equity: float = 0.0
    trade_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    win_rate: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    fees: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    position_value: float = 0.0
    exposure: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def compute_unrealized_pnl(
    *,
    position_side: str | None,
    position_qty: float,
    avg_price: float,
    last_price: float | None,
) -> float:
    if not position_side or position_qty <= 0 or last_price is None or avg_price <= 0:
        return 0.0
    sign = 1.0 if position_side == "long" else -1.0
    return sign * float(position_qty) * (float(last_price) - float(avg_price))


def append_equity_point(
    curve: list[dict[str, Any]],
    *,
    equity: float,
    cash: float,
    realized_pnl: float,
    unrealized_pnl: float,
    peak_equity: float | None = None,
    ts: datetime | None = None,
) -> tuple[list[dict[str, Any]], float]:
    ts = ts or datetime.now(timezone.utc)
    peak = peak_equity if peak_equity is not None else equity
    if curve:
        peak = max(peak, max(p.get("equity", 0) for p in curve))
    peak = max(peak, equity)
    dd = (peak - equity) / peak if peak > 0 else 0.0
    point = EquityPoint(
        timestamp=ts.isoformat(),
        equity=round(equity, 4),
        cash=round(cash, 4),
        unrealized_pnl=round(unrealized_pnl, 4),
        realized_pnl=round(realized_pnl, 4),
        drawdown=round(dd, 6),
    )
    curve = list(curve)
    curve.append(point.to_dict())
    return curve, peak


def build_run_summary(
    *,
    starting_balance: float,
    current_balance: float,
    realized_pnl: float,
    unrealized_pnl: float,
    fees: float,
    fills: list[dict[str, Any]],
    equity_curve: list[dict[str, Any]],
    started_at: datetime | None,
    ended_at: datetime | None,
    position_qty: float = 0.0,
    last_price: float | None = None,
) -> RunPerformanceSummary:
    initial = float(starting_balance)
    cash = float(current_balance)
    unreal = float(unrealized_pnl)
    real = float(realized_pnl)
    equity = cash + unreal
    net = real + unreal - float(fees)
    gross = real + unreal
    peak = initial
    max_dd = 0.0
    for pt in equity_curve:
        peak = max(peak, float(pt.get("equity", initial)))
        max_dd = max(max_dd, float(pt.get("drawdown", 0)))

    trade_pnls: list[float] = []
    for f in fills:
        px = float(f.get("price") or f.get("last_px") or 0)
        qty = float(f.get("quantity") or f.get("last_qty") or 0)
        if px and qty:
            side = str(f.get("side", "")).lower()
            sign = 1.0 if side == "sell" else -1.0 if side == "buy" else 0.0
            trade_pnls.append(sign * px * qty)

    wins = [p for p in trade_pnls if p > 0]
    losses = [p for p in trade_pnls if p < 0]
    duration = 0.0
    if started_at and ended_at:
        duration = max(0.0, (ended_at - started_at).total_seconds())

    return RunPerformanceSummary(
        start_time=_iso(started_at),
        end_time=_iso(ended_at),
        duration_seconds=duration,
        initial_equity=initial,
        final_equity=equity,
        initial_cash=initial,
        cash=cash,
        balance=cash,
        net_pnl=net,
        gross_pnl=gross,
        realized_pnl=real,
        unrealized_pnl=unreal,
        return_pct=(net / initial * 100.0) if initial else 0.0,
        max_drawdown=max_dd,
        peak_equity=peak,
        trade_count=len(fills),
        win_count=len(wins),
        loss_count=len(losses),
        win_rate=(len(wins) / len(trade_pnls)) if trade_pnls else 0.0,
        gross_profit=sum(wins),
        gross_loss=sum(losses),
        fees=float(fees),
        largest_win=max(wins) if wins else 0.0,
        largest_loss=min(losses) if losses else 0.0,
        position_value=float(position_qty) * float(last_price or 0),
        exposure=float(position_qty) * float(last_price or 0),
    )


def portfolio_from_snapshot(
    *,
    starting_balance: float,
    snap: dict[str, Any],
    existing_metrics: dict[str, Any] | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
) -> dict[str, Any]:
    """Merge Nautilus snapshot into portfolio metrics + equity curve."""
    metrics = dict(existing_metrics or {})
    balance = float(snap.get("balance") or starting_balance)
    realized = float(snap.get("realized_pnl") or metrics.get("realized_pnl") or 0)
    last_price = snap.get("last_price")
    if last_price is not None:
        last_price = float(last_price)
    pos_side = snap.get("position_side")
    pos_qty = float(snap.get("position_qty") or 0)
    avg_px = 0.0
    if snap.get("positions"):
        avg_px = float(snap["positions"][0].get("avg_px_open") or snap["positions"][0].get("avg_price") or 0)
    unreal = compute_unrealized_pnl(
        position_side=pos_side,
        position_qty=pos_qty,
        avg_price=avg_px,
        last_price=last_price,
    )
    equity = balance + unreal
    curve, peak = append_equity_point(
        metrics.get("equity_curve") or [],
        equity=equity,
        cash=balance,
        realized_pnl=realized,
        unrealized_pnl=unreal,
        peak_equity=float(metrics.get("peak_equity") or starting_balance),
    )
    fills = snap.get("fills") or []
    fees = sum(float(f.get("commission") or f.get("fee") or 0) for f in fills)
    summary = build_run_summary(
        starting_balance=starting_balance,
        current_balance=balance,
        realized_pnl=realized,
        unrealized_pnl=unreal,
        fees=fees,
        fills=fills,
        equity_curve=curve,
        started_at=started_at,
        ended_at=ended_at,
        position_qty=pos_qty,
        last_price=last_price,
    )
    metrics.update(
        {
            "equity_curve": curve,
            "peak_equity": peak,
            "performance_summary": summary.to_dict(),
            "cash": balance,
            "equity": equity,
            "unrealized_pnl": unreal,
            "realized_pnl": realized,
            "fees": fees,
            "last_price": last_price,
        }
    )
    return metrics
