"""模拟执行 / 纸面下单服务。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.execution import OrderSide, OrderStatus, PaperOrder
from backend.app.models.factor import Factor
from backend.app.models.user import User
from backend.app.services import regime_advisory
from backend.app.services.execution_risk import RiskBlockedError, preflight
from engine.execution_adapter import CHANNEL_PAPER, CHANNEL_VNPY, route_vnpy_order


class ExecutionError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def submit_paper_order(
    db: Session,
    user: User,
    *,
    symbol: str,
    side: str,
    notional_cny: float,
    factor_id: uuid.UUID | None = None,
    signal_value: float | None = None,
    note: str = "",
    timeframe: str = "1d",
    channel: str = CHANNEL_PAPER,
    acknowledge_risk: bool = False,
) -> PaperOrder:
    sym = (symbol or "").upper().strip()
    if not sym:
        raise ExecutionError("标的不能为空")
    if side not in (OrderSide.BUY.value, OrderSide.SELL.value):
        raise ExecutionError("方向必须是 buy 或 sell")
    if notional_cny <= 0:
        raise ExecutionError("名义金额必须大于 0")
    if channel not in (CHANNEL_PAPER, CHANNEL_VNPY):
        raise ExecutionError("无效的执行通道")

    factor = db.get(Factor, factor_id) if factor_id else None
    if factor_id and factor is None:
        raise ExecutionError("因子不存在")

    regime = regime_advisory.market_regime_for_symbol(
        db, user, sym, timeframe, factor=factor
    )
    regime_key = regime.get("regime") if regime else None
    fit_score = regime.get("fit_score") if regime else None

    try:
        risk = preflight(
            notional_cny=notional_cny,
            channel=channel,
            regime_fit_score=fit_score,
            acknowledge_risk=acknowledge_risk,
        )
    except RiskBlockedError as exc:
        raise ExecutionError(str(exc)) from exc

    status = OrderStatus.FILLED.value
    external_ref = None
    routed_at = None
    order_id = uuid.uuid4()

    if channel == CHANNEL_VNPY:
        status = OrderStatus.ROUTED.value
        routed = route_vnpy_order(
            order_id=order_id,
            symbol=sym,
            side=side,
            notional_cny=notional_cny,
            signal_value=signal_value,
        )
        external_ref = routed["external_ref"]
        routed_at = _now()

    order = PaperOrder(
        id=order_id,
        user_id=user.id,
        factor_id=factor_id,
        symbol=sym,
        side=side,
        notional_cny=round(notional_cny, 2),
        status=status,
        signal_value=signal_value,
        regime=regime_key,
        regime_fit_score=fit_score,
        channel=channel,
        external_ref=external_ref,
        risk_verdict=risk["verdict"],
        risk_detail=risk.get("detail", ""),
        routed_at=routed_at,
        note=(note or "")[:200],
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def route_existing_to_vnpy(db: Session, user_id: uuid.UUID, order_id: uuid.UUID) -> PaperOrder:
    order = get_paper_order(db, user_id, order_id)
    if order is None:
        raise ExecutionError("订单不存在")
    if order.channel == CHANNEL_VNPY and order.external_ref:
        return order
    if order.status == OrderStatus.CANCELLED.value:
        raise ExecutionError("订单已取消")

    try:
        preflight(
            notional_cny=float(order.notional_cny),
            channel=CHANNEL_PAPER,
            regime_fit_score=order.regime_fit_score,
            acknowledge_risk=True,
        )
    except RiskBlockedError as exc:
        raise ExecutionError(str(exc)) from exc

    routed = route_vnpy_order(
        order_id=order.id,
        symbol=order.symbol,
        side=order.side,
        notional_cny=float(order.notional_cny),
        signal_value=float(order.signal_value) if order.signal_value is not None else None,
    )
    order.channel = CHANNEL_VNPY
    order.external_ref = routed["external_ref"]
    order.status = OrderStatus.ROUTED.value
    order.routed_at = _now()
    db.commit()
    db.refresh(order)
    return order


def risk_check_preview(
    db: Session,
    user: User,
    *,
    symbol: str,
    notional_cny: float,
    channel: str = CHANNEL_PAPER,
    factor_id: uuid.UUID | None = None,
    timeframe: str = "1d",
    acknowledge_risk: bool = False,
) -> dict:
    factor = db.get(Factor, factor_id) if factor_id else None
    regime = regime_advisory.market_regime_for_symbol(
        db, user, symbol.upper(), timeframe, factor=factor
    )
    fit_score = regime.get("fit_score") if regime else None
    try:
        risk = preflight(
            notional_cny=notional_cny,
            channel=channel,
            regime_fit_score=fit_score,
            acknowledge_risk=acknowledge_risk,
        )
        allowed = True
        message = "通过风控预检"
    except RiskBlockedError as exc:
        risk = {"verdict": exc.verdict, "detail": exc.detail}
        allowed = False
        message = str(exc)

    return {
        "allowed": allowed,
        "message": message,
        "channel": channel,
        "regime": regime,
        "risk": risk,
    }


def list_paper_orders(
    db: Session, user_id: uuid.UUID, *, limit: int = 50
) -> list[PaperOrder]:
    return list(
        db.execute(
            select(PaperOrder)
            .where(PaperOrder.user_id == user_id)
            .order_by(PaperOrder.created_at.desc())
            .limit(min(limit, 200))
        ).scalars().all()
    )


def get_paper_order(db: Session, user_id: uuid.UUID, order_id: uuid.UUID) -> PaperOrder | None:
    row = db.get(PaperOrder, order_id)
    if row is None or row.user_id != user_id:
        return None
    return row


def order_to_dict(row: PaperOrder) -> dict:
    return {
        "id": row.id,
        "factor_id": row.factor_id,
        "symbol": row.symbol,
        "side": row.side,
        "notional_cny": float(row.notional_cny),
        "status": row.status,
        "signal_value": float(row.signal_value) if row.signal_value is not None else None,
        "regime": row.regime,
        "regime_fit_score": row.regime_fit_score,
        "channel": row.channel,
        "external_ref": row.external_ref,
        "risk_verdict": row.risk_verdict,
        "risk_detail": row.risk_detail,
        "routed_at": row.routed_at,
        "note": row.note,
        "created_at": row.created_at,
    }
