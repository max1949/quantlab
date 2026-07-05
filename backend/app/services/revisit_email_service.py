"""注册后长期未开始研究 — 登录时一次性回流邮件。"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

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


def maybe_send_revisit_email(
    db: Session,
    user: User,
    *,
    locale: Locale = "zh",
) -> bool:
    """登录时发送一次回流邮件；条件与 research_revisit_coaching 对齐。"""
    if not bes.smtp_configured():
        return False
    if not user.onboarding_done:
        return False
    if _already_sent(db, user.id):
        return False

    to_email = (user.email or "").strip().lower()
    if not to_email:
        return False

    from backend.app.services import onboarding_service as obs
    from backend.app.services import org_service

    flags = obs._journey_flags(db, user)
    if flags.get("backtest") or flags.get("report"):
        return False
    if org_service.list_orgs_for_user(db, user.id):
        return False

    created = user.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - created).days
    if days < 3:
        return False

    subject, body = build_revisit_email(user, days=days, locale=locale)
    try:
        bes.send_plain_email(to_email, subject, body)
        growth_service.log_event(db, _EVENT, user.id, {"locale": locale, "days": days})
        logger.info("revisit email sent to %s user=%s days=%s", to_email, user.id, days)
        return True
    except Exception as exc:
        logger.warning("revisit email failed user=%s: %s", user.id, exc)
        return False
