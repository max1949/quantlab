"""执行合规报表与 SLA 告警 (机构级运维)。"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.execution import OrderStatus, PaperOrder
from backend.app.models.organization import OrgMember
from backend.app.models.user import User
from backend.app.services import execution_service as exs
from backend.app.services.org_service import require_admin
from engine.execution_adapter import CHANNEL_QMT, CHANNEL_VNPY, gateway_health_summary


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _order_brief(row: PaperOrder, *, username: str | None = None) -> dict:
    routed = _normalize_utc(row.routed_at) or _normalize_utc(row.created_at)
    age_min = int((_now() - routed).total_seconds() // 60) if routed else 0
    d = exs.order_to_dict(row)
    d["age_minutes"] = age_min
    if username:
        d["username"] = username
    return d


def _stale_routed_orders(
    db: Session,
    *,
    user_ids: list | None = None,
    limit: int = 50,
) -> list[PaperOrder]:
    settings = get_settings()
    threshold = _now() - timedelta(minutes=settings.execution_sla_stale_minutes)
    stmt = (
        select(PaperOrder)
        .where(
            PaperOrder.channel.in_((CHANNEL_VNPY, CHANNEL_QMT)),
            PaperOrder.status == OrderStatus.ROUTED.value,
            PaperOrder.external_ref.is_not(None),
        )
        .order_by(PaperOrder.created_at.asc())
        .limit(min(limit, 200))
    )
    if user_ids is not None:
        stmt = stmt.where(PaperOrder.user_id.in_(user_ids))
    rows = list(db.execute(stmt).scalars().all())
    stale: list[PaperOrder] = []
    for row in rows:
        anchor = _normalize_utc(row.routed_at) or _normalize_utc(row.created_at)
        if anchor and anchor < threshold:
            stale.append(row)
    return stale


def _order_status_counts(db: Session, *, user_ids: list | None = None) -> dict[str, int]:
    stmt = select(PaperOrder.status, func.count()).group_by(PaperOrder.status)
    if user_ids is not None:
        stmt = stmt.where(PaperOrder.user_id.in_(user_ids))
    rows = db.execute(stmt).all()
    out = {status: int(count) for status, count in rows}
    out["total"] = sum(out.values())
    return out


def _gateway_alerts(gateways: list[dict]) -> list[dict]:
    alerts: list[dict] = []
    for g in gateways:
        if not g.get("configured"):
            continue
        if g.get("ok") is False:
            alerts.append(
                {
                    "code": "gateway_down",
                    "severity": "critical",
                    "channel": g.get("channel"),
                    "message": f"{g.get('channel')} 网关不可达: {g.get('error', 'unknown')}",
                }
            )
    return alerts


def _stale_order_alerts(orders: list[dict], *, scope: str) -> list[dict]:
    settings = get_settings()
    alerts: list[dict] = []
    for o in orders:
        alerts.append(
            {
                "code": "stale_routed_order",
                "severity": "warning",
                "scope": scope,
                "order_id": str(o["id"]),
                "channel": o.get("channel"),
                "external_ref": o.get("external_ref"),
                "age_minutes": o.get("age_minutes"),
                "message": (
                    f"订单 {o.get('symbol')} {o.get('side')} 在 {o.get('channel')} "
                    f"滞留 {o.get('age_minutes')} 分钟 (阈值 {settings.execution_sla_stale_minutes})"
                ),
            }
        )
    return alerts


def build_global_compliance_report(db: Session, *, stale_limit: int = 50) -> dict:
    settings = get_settings()
    gateways = gateway_health_summary()
    stale_rows = _stale_routed_orders(db, limit=stale_limit)
    stale_brief = [_order_brief(r) for r in stale_rows]
    alerts = _gateway_alerts(gateways)
    if settings.execution_kill_switch:
        alerts.append(
            {
                "code": "kill_switch_on",
                "severity": "critical",
                "message": "执行总闸已关闭 — 所有下单被拦截",
            }
        )
    alerts.extend(_stale_order_alerts(stale_brief, scope="global"))
    return {
        "generated_at": _now(),
        "scope": "global",
        "kill_switch": settings.execution_kill_switch,
        "sla_stale_minutes": settings.execution_sla_stale_minutes,
        "gateways": gateways,
        "order_summary": _order_status_counts(db),
        "stale_orders": stale_brief,
        "sla_alerts": alerts,
        "alert_count": len(alerts),
    }


def build_org_compliance_report(
    db: Session, org_id: uuid.UUID, actor_id: uuid.UUID, *, stale_limit: int = 30
) -> dict:
    require_admin(db, org_id, actor_id)
    settings = get_settings()
    member_ids = list(
        db.execute(select(OrgMember.user_id).where(OrgMember.org_id == org_id)).scalars().all()
    )
    gateways = gateway_health_summary()
    stale_rows = _stale_routed_orders(db, user_ids=member_ids, limit=stale_limit)
    if stale_rows:
        users = {
            u.id: u.username
            for u in db.execute(select(User).where(User.id.in_([r.user_id for r in stale_rows]))).scalars().all()
        }
        stale_brief = [_order_brief(r, username=users.get(r.user_id)) for r in stale_rows]
    else:
        stale_brief = []

    alerts = _gateway_alerts(gateways)
    if settings.execution_kill_switch:
        alerts.append(
            {
                "code": "kill_switch_on",
                "severity": "critical",
                "message": "执行总闸已关闭 — 所有下单被拦截",
            }
        )
    alerts.extend(_stale_order_alerts(stale_brief, scope="org"))

    return {
        "generated_at": _now(),
        "scope": "org",
        "org_id": org_id,
        "kill_switch": settings.execution_kill_switch,
        "sla_stale_minutes": settings.execution_sla_stale_minutes,
        "gateways": gateways,
        "order_summary": _order_status_counts(db, user_ids=member_ids) if member_ids else {"total": 0},
        "stale_orders": stale_brief,
        "sla_alerts": alerts,
        "alert_count": len(alerts),
    }
