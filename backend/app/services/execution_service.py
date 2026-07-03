"""模拟执行 / 纸面下单服务。"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.execution import OrderSide, OrderStatus, PaperOrder
from backend.app.models.factor import Factor
from backend.app.models.user import User
from backend.app.services import regime_advisory


class ExecutionError(Exception):
    pass


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
) -> PaperOrder:
    sym = (symbol or "").upper().strip()
    if not sym:
        raise ExecutionError("标的不能为空")
    if side not in (OrderSide.BUY.value, OrderSide.SELL.value):
        raise ExecutionError("方向必须是 buy 或 sell")
    if notional_cny <= 0:
        raise ExecutionError("名义金额必须大于 0")

    factor = db.get(Factor, factor_id) if factor_id else None
    if factor_id and factor is None:
        raise ExecutionError("因子不存在")

    regime = regime_advisory.market_regime_for_symbol(
        db, user, sym, timeframe, factor=factor
    )
    regime_key = regime.get("regime") if regime else None
    fit_score = regime.get("fit_score") if regime else None

    order = PaperOrder(
        user_id=user.id,
        factor_id=factor_id,
        symbol=sym,
        side=side,
        notional_cny=round(notional_cny, 2),
        status=OrderStatus.FILLED.value,
        signal_value=signal_value,
        regime=regime_key,
        regime_fit_score=fit_score,
        note=(note or "")[:200],
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


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
        "note": row.note,
        "created_at": row.created_at,
    }
