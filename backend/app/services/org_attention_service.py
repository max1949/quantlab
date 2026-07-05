"""机构团队研究提醒汇总 — Owner/Admin 孵化台 + Webhook 推送。"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.locale import Locale
from backend.app.i18n import content as i18n
from backend.app.models.organization import ResearchOrg
from backend.app.models.user import User
from backend.app.services import org_service, regime_alert_service as ras

logger = logging.getLogger(__name__)

_SEVERITY_ORDER = {"info": 0, "watch": 1, "alert": 2}
_MAX_PER_MEMBER = 2
_MAX_TOTAL = 20


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _redis_client() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


def _research_item_fingerprint(item: dict) -> str:
    return f"{item.get('username', '')}:{item.get('alert_key', '')}"


def filter_new_research_items(
    items: list[dict],
    *,
    dedup_prefix: str,
) -> list[dict]:
    """过滤冷却期内已推送过的研究提醒 (Redis SET NX)。"""
    settings = get_settings()
    if not settings.execution_sla_alert_enabled:
        return []

    cooldown_sec = max(60, settings.execution_sla_alert_cooldown_minutes * 60)
    fresh: list[dict] = []
    try:
        r = _redis_client()
        for item in items:
            key = f"research_alert:{dedup_prefix}:{_research_item_fingerprint(item)}"
            if r.set(key, "1", nx=True, ex=cooldown_sec):
                fresh.append(item)
    except redis.RedisError as exc:
        logger.warning("research alert dedup unavailable, sending all: %s", exc)
        return list(items)
    return fresh


def collect_team_attention(
    db: Session,
    org_id: uuid.UUID,
    locale: Locale = "en",
) -> dict:
    """汇总成员工作台主动提醒 (无权限校验，供内部/Webhook 使用)。"""
    from backend.app.models.organization import OrgMember

    rows = db.execute(
        select(OrgMember, User)
        .join(User, User.id == OrgMember.user_id)
        .where(OrgMember.org_id == org_id)
        .order_by(OrgMember.created_at)
    ).all()
    member_dicts = [
        {"user_id": m.user_id, "username": u.username, "role": m.role, "joined_at": m.created_at}
        for m, u in rows
    ]

    kind_labels = i18n.ATTENTION_HISTORY_KIND.get(locale) or i18n.ATTENTION_HISTORY_KIND["en"]
    coach = i18n.TEAM_ATTENTION_COACH.get(locale) or i18n.TEAM_ATTENTION_COACH["en"]

    items: list[dict] = []
    members_with = 0
    active_members = [m for m in member_dicts if m["role"] != "viewer"]

    for m in active_members:
        user = db.get(User, m["user_id"])
        if user is None:
            continue
        alerts = ras.list_attention_alerts(db, user, locale, max_projects=3)
        if not alerts:
            continue
        members_with += 1
        for alert in alerts[:_MAX_PER_MEMBER]:
            pid = alert.get("project_id")
            items.append(
                {
                    "user_id": m["user_id"],
                    "username": m["username"],
                    "role": m["role"],
                    "alert_key": alert["alert_key"],
                    "kind": alert["kind"],
                    "kind_label": kind_labels.get(alert["kind"], alert["kind"]),
                    "title": alert["title"],
                    "message": alert["message"],
                    "severity": alert.get("severity", "info"),
                    "symbol": alert.get("symbol"),
                    "project_id": pid,
                    "cta_path": alert.get("cta_path", "/app"),
                }
            )

    items.sort(key=lambda x: _SEVERITY_ORDER.get(x["severity"], 0), reverse=True)
    items = items[:_MAX_TOTAL]
    total = len(items)

    if total == 0:
        summary = coach["none"]
    elif members_with == 1:
        summary = coach["one_member"].format(count=total)
    else:
        summary = coach["many_members"].format(members=members_with, count=total)

    return {
        "member_count": len(active_members),
        "members_with_alerts": members_with,
        "total_alerts": total,
        "summary": summary,
        "items": items,
    }


def team_attention_rollup(
    db: Session,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    locale: Locale = "en",
) -> dict:
    """汇总成员工作台主动提醒，供机构负责人跟进研究质量。"""
    org_service.require_admin(db, org_id, actor_id)
    return collect_team_attention(db, org_id, locale)


def dispatch_org_research_attention_webhook(
    db: Session,
    org_id: uuid.UUID,
    *,
    actor_id: uuid.UUID | None = None,
    locale: Locale = "en",
    force: bool = False,
    trigger: str = "manual",
    retry_of_id: uuid.UUID | None = None,
) -> dict:
    """推送团队研究提醒到机构 Webhook (与 SLA 共用 URL/签名密钥)。"""
    from backend.app.services import execution_alert_service as eas

    org = db.get(ResearchOrg, org_id)
    if org is None:
        return {"sent": 0, "skipped": True, "reason": "org_not_found", "org_id": str(org_id)}

    if actor_id is not None:
        org_service.require_admin(db, org_id, actor_id)

    url = (org.alert_webhook_url or "").strip()
    if not url:
        return eas._log_skipped(
            db,
            scope="org_research",
            org_id=org_id,
            trigger=trigger,
            reason="webhook_not_configured",
            total_alerts=0,
            retry_of_id=retry_of_id,
        )

    settings = get_settings()
    if not settings.execution_sla_alert_enabled:
        return eas._log_skipped(
            db,
            scope="org_research",
            org_id=org_id,
            trigger=trigger,
            reason="alerts_disabled",
            total_alerts=0,
            webhook_url=url,
            retry_of_id=retry_of_id,
        )

    rollup = collect_team_attention(db, org_id, locale)
    items: list[dict] = list(rollup.get("items") or [])
    dedup_prefix = f"org:{org_id}"
    to_send = items if force else filter_new_research_items(items, dedup_prefix=dedup_prefix)
    if not to_send:
        return eas._log_skipped(
            db,
            scope="org_research",
            org_id=org_id,
            trigger=trigger,
            reason="no_new_alerts" if items else "no_alerts",
            total_alerts=len(items),
            webhook_url=url,
            retry_of_id=retry_of_id,
        )

    signing_secret = (org.alert_webhook_secret or "").strip() or settings.execution_sla_webhook_secret
    payload = {
        "event": "research_attention_rollup",
        "generated_at": _now().isoformat(),
        "scope": "org",
        "org_id": str(org_id),
        "org_name": org.name,
        "summary": rollup["summary"],
        "members_with_alerts": rollup["members_with_alerts"],
        "member_count": rollup["member_count"],
        "alert_count": len(to_send),
        "items": to_send,
    }
    try:
        status_code = eas._post_webhook(url, payload, secret=signing_secret)
    except Exception as exc:
        delivery = eas.record_delivery(
            db,
            scope="org_research",
            org_id=org_id,
            status="failed",
            trigger=trigger,
            alert_count=len(to_send),
            webhook_url=url,
            signed=bool(signing_secret.strip()),
            error_message=str(exc),
            detail={
                "total_alerts": len(items),
                "kinds": [i.get("kind") for i in to_send],
            },
            retry_of_id=retry_of_id,
        )
        return {
            "sent": 0,
            "skipped": False,
            "failed": True,
            "error": str(exc),
            "total_alerts": len(items),
            "org_id": str(org_id),
            "scope": "org_research",
            "delivery_id": str(delivery["id"]),
        }

    delivery = eas.record_delivery(
        db,
        scope="org_research",
        org_id=org_id,
        status="sent",
        trigger=trigger,
        alert_count=len(to_send),
        webhook_url=url,
        signed=bool(signing_secret.strip()),
        http_status=status_code,
        detail={
            "total_alerts": len(items),
            "kinds": [i.get("kind") for i in to_send],
        },
        retry_of_id=retry_of_id,
    )
    return {
        "sent": len(to_send),
        "skipped": False,
        "status_code": status_code,
        "total_alerts": len(items),
        "org_id": str(org_id),
        "scope": "org_research",
        "signed": bool(signing_secret.strip()),
        "delivery_id": str(delivery["id"]),
    }


def dispatch_all_org_research_attention_webhooks(db: Session) -> list[dict]:
    """定时任务：向已配置 Webhook 的机构推送团队研究提醒。"""
    org_ids = list(
        db.execute(
            select(ResearchOrg.id).where(ResearchOrg.alert_webhook_url != "")
        ).scalars().all()
    )
    results: list[dict] = []
    for org_id in org_ids:
        if org_id:
            results.append(
                dispatch_org_research_attention_webhook(
                    db, org_id, force=False, trigger="scheduled"
                )
            )
    return results
