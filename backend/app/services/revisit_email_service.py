"""注册后长期未开始研究 — 登录时或定时任务一次性回流邮件。"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.locale import Locale
from backend.app.i18n import content as i18n
from backend.app.models.growth import UserEvent
from backend.app.models.user import User
from backend.app.services import billing_email_service as bes
from backend.app.services import growth_service, membership_service as ms

logger = logging.getLogger(__name__)

_EVENT = "revisit_email"


def _templates_link() -> str:
    return f"{ms.frontend_origin()}/templates?focus=vol-regime"


def _dashboard_link() -> str:
    return f"{ms.frontend_origin()}/app"


def _already_sent(db: Session, user_id: uuid.UUID) -> bool:
    row = db.execute(
        select(UserEvent.id)
        .where(UserEvent.user_id == user_id, UserEvent.event == _EVENT)
        .limit(1)
    ).scalar_one_or_none()
    return row is not None


def revisit_idle_days(user: User) -> int | None:
    if not user.onboarding_done:
        return None
    created = user.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - created).days
    if days < 3:
        return None
    return days


def preferred_locale(db: Session, user_id: uuid.UUID) -> Locale:
    """从欢迎邮件等历史事件推断用户语言偏好。"""
    for event in ("welcome_email", "revisit_email", "beginner_handbook_pdf"):
        props = db.execute(
            select(UserEvent.props)
            .where(UserEvent.user_id == user_id, UserEvent.event == event)
            .order_by(UserEvent.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if isinstance(props, dict):
            loc = props.get("locale")
            if loc in ("en", "zh"):
                return loc
    return "zh"


def is_revisit_email_eligible(
    db: Session,
    user: User,
    *,
    flags: dict[str, bool] | None = None,
) -> int | None:
    """Return idle days when user should receive revisit email, else None."""
    days = revisit_idle_days(user)
    if days is None:
        return None
    if _already_sent(db, user.id):
        return None
    to_email = (user.email or "").strip().lower()
    if not to_email:
        return None

    if flags is None:
        from backend.app.services import onboarding_service as obs

        flags = obs._journey_flags(db, user)
    if flags.get("backtest") or flags.get("report"):
        return None

    from backend.app.services import org_service

    if org_service.list_orgs_for_user(db, user.id):
        return None
    return days


def build_revisit_email(user: User, *, days: int, locale: Locale = "zh") -> tuple[str, str]:
    labels = i18n.REVISIT_EMAIL.get(locale) or i18n.REVISIT_EMAIL["en"]
    subject = labels["subject"]
    body = labels["body"].format(
        username=user.username,
        days=days,
        templates_link=_templates_link(),
        dashboard_link=_dashboard_link(),
    )
    return subject, body


def _send_revisit_email(db: Session, user: User, *, days: int, locale: Locale) -> bool:
    to_email = (user.email or "").strip().lower()
    subject, body = build_revisit_email(user, days=days, locale=locale)
    try:
        bes.send_plain_email(to_email, subject, body)
        growth_service.log_event(db, _EVENT, user.id, {"locale": locale, "days": days})
        logger.info("revisit email sent to %s user=%s days=%s", to_email, user.id, days)
        return True
    except Exception as exc:
        logger.warning("revisit email failed user=%s: %s", user.id, exc)
        return False


def maybe_send_revisit_email(
    db: Session,
    user: User,
    *,
    locale: Locale = "zh",
) -> bool:
    """登录时发送一次回流邮件；条件与 research_revisit_coaching 对齐。"""
    if not bes.smtp_configured():
        return False
    days = is_revisit_email_eligible(db, user)
    if days is None:
        return False
    return _send_revisit_email(db, user, days=days, locale=locale)


def run_scheduled_revisit_batch(
    db: Session,
    *,
    limit: int = 100,
) -> dict[str, int | str]:
    """Cron: 给注册 ≥3 天仍未开始研究、且尚未收到回流邮件的用户发信。"""
    if not bes.smtp_configured():
        return {"sent": 0, "failed": 0, "scanned": 0, "reason": "smtp_disabled"}

    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    candidates = db.execute(
        select(User)
        .where(
            User.onboarding_done.is_(True),
            User.created_at <= cutoff,
            User.email.isnot(None),
            User.email != "",
        )
        .order_by(User.created_at.asc())
        .limit(max(limit * 5, limit))
    ).scalars().all()

    sent = failed = 0
    scanned = 0
    for user in candidates:
        if sent >= limit:
            break
        scanned += 1
        days = is_revisit_email_eligible(db, user)
        if days is None:
            continue
        user_locale = preferred_locale(db, user.id)
        if _send_revisit_email(db, user, days=days, locale=user_locale):
            sent += 1
        else:
            failed += 1

    return {"sent": sent, "failed": failed, "scanned": scanned}
