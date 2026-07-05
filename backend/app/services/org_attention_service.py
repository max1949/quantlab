"""机构团队研究提醒汇总 — Owner/Admin 孵化台。"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from backend.app.core.locale import Locale
from backend.app.i18n import content as i18n
from backend.app.models.user import User
from backend.app.services import org_service, regime_alert_service as ras

_SEVERITY_ORDER = {"info": 0, "watch": 1, "alert": 2}
_MAX_PER_MEMBER = 2
_MAX_TOTAL = 20


def team_attention_rollup(
    db: Session,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    locale: Locale = "en",
) -> dict:
    """汇总成员工作台主动提醒，供机构负责人跟进研究质量。"""
    org_service.require_admin(db, org_id, actor_id)
    members = org_service.list_members(db, org_id, actor_id)
    kind_labels = i18n.ATTENTION_HISTORY_KIND.get(locale) or i18n.ATTENTION_HISTORY_KIND["en"]
    coach = i18n.TEAM_ATTENTION_COACH.get(locale) or i18n.TEAM_ATTENTION_COACH["en"]

    items: list[dict] = []
    members_with = 0
    active_members = [m for m in members if m["role"] != "viewer"]

    for m in active_members:
        user = db.get(User, m["user_id"])
        if user is None:
            continue
        alerts = ras.list_attention_alerts(db, user, locale, max_projects=3)
        if not alerts:
            continue
        members_with += 1
        for alert in alerts[:_MAX_PER_MEMBER]:
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
                    "project_id": alert.get("project_id"),
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
