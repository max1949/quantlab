"""模拟执行 / 纸面下单服务。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.execution import OrderSide, OrderStatus, PaperOrder, PaperOrderEvent
from backend.app.models.factor import Factor
from backend.app.models.user import User
from backend.app.services import regime_advisory
from backend.app.services.execution_risk import RiskBlockedError, preflight
from engine.execution_adapter import (
    CHANNEL_PAPER,
    CHANNEL_QMT,
    CHANNEL_VNPY,
    AdapterError,
    fetch_gateway_order_status,
    route_qmt_order,
    route_vnpy_order,
)


class ExecutionError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def log_order_event(
    db: Session,
    order: PaperOrder,
    *,
    event_type: str,
    from_status: str | None = None,
    to_status: str | None = None,
    gateway_status: str | None = None,
    detail: str = "",
) -> PaperOrderEvent:
    ev = PaperOrderEvent(
        order_id=order.id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        gateway_status=gateway_status,
        detail=(detail or "")[:500],
    )
    db.add(ev)
    return ev


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
    if channel not in (CHANNEL_PAPER, CHANNEL_VNPY, CHANNEL_QMT):
        raise ExecutionError("无效的执行通道")
    if channel == CHANNEL_VNPY:
        raise ExecutionError(
            "vn.py 执行通道已停止新增（VNPY_LEGACY）。请使用纸面模拟；历史订单仍可查询。"
        )

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

    gateway_status = None

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
        gateway_status = routed.get("gateway_status")
        routed_at = _now()
    elif channel == CHANNEL_QMT:
        status = OrderStatus.ROUTED.value
        routed = route_qmt_order(
            order_id=order_id,
            symbol=sym,
            side=side,
            notional_cny=notional_cny,
            signal_value=signal_value,
        )
        external_ref = routed["external_ref"]
        gateway_status = routed.get("gateway_status")
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
        gateway_status=gateway_status,
        risk_verdict=risk["verdict"],
        risk_detail=risk.get("detail", ""),
        routed_at=routed_at,
        note=(note or "")[:200],
    )
    db.add(order)
    log_order_event(
        db,
        order,
        event_type="submitted",
        to_status=status,
        gateway_status=gateway_status,
        detail=f"channel={channel}",
    )
    db.commit()
    db.refresh(order)
    from backend.app.services import academy_hooks

    order.academy_rewards = academy_hooks.on_paper_order(db, user)
    return order


def route_existing_to_vnpy(db: Session, user_id: uuid.UUID, order_id: uuid.UUID) -> PaperOrder:
    raise ExecutionError(
        "vn.py 执行通道已停止新增（VNPY_LEGACY）。历史订单仍保留，不可再路由到 vn.py。"
    )


def route_existing_to_qmt(db: Session, user_id: uuid.UUID, order_id: uuid.UUID) -> PaperOrder:
    return _route_existing_to_gateway(db, user_id, order_id, CHANNEL_QMT)


def _route_existing_to_gateway(
    db: Session, user_id: uuid.UUID, order_id: uuid.UUID, channel: str
) -> PaperOrder:
    order = get_paper_order(db, user_id, order_id)
    if order is None:
        raise ExecutionError("订单不存在")
    if order.channel == channel and order.external_ref:
        return order
    if order.status == OrderStatus.CANCELLED.value:
        raise ExecutionError("订单已取消")

    try:
        preflight(
            notional_cny=float(order.notional_cny),
            channel=channel,
            regime_fit_score=order.regime_fit_score,
            acknowledge_risk=True,
        )
    except RiskBlockedError as exc:
        raise ExecutionError(str(exc)) from exc

    route_fn = route_vnpy_order if channel == CHANNEL_VNPY else route_qmt_order
    routed = route_fn(
        order_id=order.id,
        symbol=order.symbol,
        side=order.side,
        notional_cny=float(order.notional_cny),
        signal_value=float(order.signal_value) if order.signal_value is not None else None,
    )
    prev_status = order.status
    order.channel = channel
    order.external_ref = routed["external_ref"]
    order.gateway_status = routed.get("gateway_status")
    order.status = OrderStatus.ROUTED.value
    order.routed_at = _now()
    log_order_event(
        db,
        order,
        event_type="routed",
        from_status=prev_status,
        to_status=order.status,
        gateway_status=order.gateway_status,
        detail=f"channel={channel}; ref={order.external_ref}",
    )
    db.commit()
    db.refresh(order)
    return order


def apply_gateway_status(
    db: Session,
    *,
    external_ref: str,
    gateway_status: str,
    event_type: str = "gateway_update",
) -> PaperOrder | None:
    """网关 Webhook / 轮询 — 按 external_ref 更新订单状态。"""
    ref = (external_ref or "").strip()
    if not ref:
        return None
    order = db.execute(
        select(PaperOrder).where(PaperOrder.external_ref == ref)
    ).scalar_one_or_none()
    if order is None:
        return None
    return _apply_status_to_order(db, order, gateway_status, event_type=event_type, detail=f"external_ref={ref}")


def _apply_status_to_order(
    db: Session,
    order: PaperOrder,
    gateway_status: str,
    *,
    event_type: str = "gateway_update",
    detail: str = "",
) -> PaperOrder:
    gs = (gateway_status or "").lower()
    prev_status = order.status
    prev_gs = (order.gateway_status or "").lower()
    new_status = _status_for_gateway(gs, prev_status)
    if gs == prev_gs and new_status == prev_status:
        return order

    order.gateway_status = gs
    order.status = new_status
    if order.status == OrderStatus.FILLED.value and order.filled_at is None:
        order.filled_at = _now()

    log_order_event(
        db,
        order,
        event_type=event_type,
        from_status=prev_status,
        to_status=order.status,
        gateway_status=gs,
        detail=detail[:500],
    )
    db.commit()
    db.refresh(order)
    return order


def _status_for_gateway(gs: str, prev_status: str) -> str:
    if gs in ("filled", "complete", "completed"):
        return OrderStatus.FILLED.value
    if gs in ("rejected", "failed", "error"):
        return OrderStatus.REJECTED.value
    if gs in ("cancelled", "canceled"):
        return OrderStatus.CANCELLED.value
    if gs in ("routed", "accepted", "pending"):
        return OrderStatus.ROUTED.value
    return prev_status


def refresh_order_from_gateway(
    db: Session, user_id: uuid.UUID, order_id: uuid.UUID
) -> PaperOrder:
    order = get_paper_order(db, user_id, order_id)
    if order is None:
        raise ExecutionError("订单不存在")
    return _refresh_gateway_order(db, order)


def _refresh_gateway_order(db: Session, order: PaperOrder) -> PaperOrder:
    if order.channel not in (CHANNEL_VNPY, CHANNEL_QMT):
        raise ExecutionError("仅网关订单可刷新状态")
    if not order.external_ref:
        raise ExecutionError("订单无外部引用")
    if order.status in (
        OrderStatus.FILLED.value,
        OrderStatus.CANCELLED.value,
        OrderStatus.REJECTED.value,
    ):
        return order

    try:
        gs = fetch_gateway_order_status(channel=order.channel, external_ref=order.external_ref)
    except AdapterError as exc:
        raise ExecutionError(str(exc)) from exc

    return _apply_status_to_order(
        db,
        order,
        gs,
        event_type="gateway_poll",
        detail=f"poll channel={order.channel}; ref={order.external_ref}",
    )


def refresh_org_gateway_orders(
    db: Session, org_id: uuid.UUID, actor_id: uuid.UUID, *, limit: int = 30
) -> dict:
    from backend.app.models.organization import OrgMember
    from backend.app.services.org_service import require_admin

    require_admin(db, org_id, actor_id)
    member_ids = list(
        db.execute(select(OrgMember.user_id).where(OrgMember.org_id == org_id)).scalars().all()
    )
    if not member_ids:
        return {"checked": 0, "updated": 0, "errors": 0}

    pending = _pending_gateway_orders_query(db, user_ids=member_ids, limit=limit)
    return _sync_pending_orders(db, pending, detail_prefix="org_batch")


def _pending_gateway_orders_query(
    db: Session,
    *,
    user_ids: list | None = None,
    limit: int = 50,
):
    stmt = (
        select(PaperOrder)
        .where(
            PaperOrder.channel.in_((CHANNEL_VNPY, CHANNEL_QMT)),
            PaperOrder.status == OrderStatus.ROUTED.value,
            PaperOrder.external_ref.is_not(None),
        )
        .order_by(PaperOrder.created_at.desc())
        .limit(min(limit, 200))
    )
    if user_ids is not None:
        stmt = stmt.where(PaperOrder.user_id.in_(user_ids))
    return list(db.execute(stmt).scalars().all())


def _sync_pending_orders(
    db: Session, orders: list[PaperOrder], *, detail_prefix: str
) -> dict:
    updated = 0
    errors = 0
    for order in orders:
        prev_status = order.status
        prev_gs = (order.gateway_status or "").lower()
        try:
            gs = fetch_gateway_order_status(
                channel=order.channel, external_ref=order.external_ref or ""
            )
        except AdapterError:
            errors += 1
            continue
        refreshed = _apply_status_to_order(
            db,
            order,
            gs,
            event_type="gateway_poll",
            detail=f"{detail_prefix} poll ref={order.external_ref}",
        )
        if refreshed.status != prev_status or (refreshed.gateway_status or "").lower() != prev_gs:
            updated += 1
    return {"checked": len(orders), "updated": updated, "errors": errors}


def sync_all_pending_gateway_orders(db: Session, *, limit: int | None = None) -> dict:
    settings = get_settings()
    if not settings.execution_gateway_sync_enabled:
        return {"checked": 0, "updated": 0, "errors": 0, "skipped": True}
    batch = limit if limit is not None else settings.execution_gateway_sync_batch_size
    pending = _pending_gateway_orders_query(db, limit=batch)
    result = _sync_pending_orders(db, pending, detail_prefix="cron")
    result["skipped"] = False
    return result


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


def list_order_events(
    db: Session, user_id: uuid.UUID, order_id: uuid.UUID
) -> list[PaperOrderEvent]:
    order = get_paper_order(db, user_id, order_id)
    if order is None:
        return []
    return list(
        db.execute(
            select(PaperOrderEvent)
            .where(PaperOrderEvent.order_id == order_id)
            .order_by(PaperOrderEvent.created_at.asc())
        ).scalars().all()
    )


def list_org_execution_orders(
    db: Session, org_id: uuid.UUID, actor_id: uuid.UUID, *, limit: int = 50
) -> list[dict]:
    from backend.app.models.organization import OrgMember
    from backend.app.models.user import User
    from backend.app.services.org_service import require_admin

    require_admin(db, org_id, actor_id)
    member_ids = db.execute(
        select(OrgMember.user_id).where(OrgMember.org_id == org_id)
    ).scalars().all()
    if not member_ids:
        return []

    rows = db.execute(
        select(PaperOrder, User.username)
        .join(User, User.id == PaperOrder.user_id)
        .where(PaperOrder.user_id.in_(member_ids))
        .order_by(PaperOrder.created_at.desc())
        .limit(min(limit, 200))
    ).all()
    out: list[dict] = []
    for order, username in rows:
        d = order_to_dict(order)
        d["username"] = username
        out.append(d)
    return out


def event_to_dict(row: PaperOrderEvent) -> dict:
    return {
        "id": row.id,
        "order_id": row.order_id,
        "event_type": row.event_type,
        "from_status": row.from_status,
        "to_status": row.to_status,
        "gateway_status": row.gateway_status,
        "detail": row.detail,
        "created_at": row.created_at,
    }


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
        "gateway_status": row.gateway_status,
        "filled_at": row.filled_at,
        "routed_at": row.routed_at,
        "note": row.note,
        "created_at": row.created_at,
    }
