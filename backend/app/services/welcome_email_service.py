"""注册欢迎邮件 — 附带新手手册与工作台链接。"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.app.core.locale import Locale
from backend.app.i18n import content as i18n
from backend.app.models.user import User
from backend.app.services import billing_email_service as bes
from backend.app.services import growth_service, membership_service as ms

logger = logging.getLogger(__name__)


def _handbook_link() -> str:
    return f"{ms.frontend_origin()}/handbook"


def _dashboard_link() -> str:
    return f"{ms.frontend_origin()}/app"


def build_welcome_email(user: User, *, locale: Locale = "zh") -> tuple[str, str]:
    labels = i18n.WELCOME_EMAIL.get(locale) or i18n.WELCOME_EMAIL["en"]
    subject = labels["subject"]
    body = labels["body"].format(
        username=user.username,
        handbook_link=_handbook_link(),
        dashboard_link=_dashboard_link(),
    )
    return subject, body


def register_hint(locale: Locale = "zh") -> str | None:
    if not bes.smtp_configured():
        return None
    labels = i18n.WELCOME_EMAIL.get(locale) or i18n.WELCOME_EMAIL["en"]
    return labels.get("register_hint")


def notify_welcome_email(
    db: Session,
    user: User,
    *,
    locale: Locale = "zh",
) -> bool:
    """注册成功后发送欢迎邮件；未配置 SMTP 时静默跳过。"""
    if not bes.smtp_configured():
        return False

    to_email = (user.email or "").strip().lower()
    if not to_email:
        return False

    subject, body = build_welcome_email(user, locale=locale)
    try:
        bes.send_plain_email(to_email, subject, body)
        growth_service.log_event(db, "welcome_email", user.id, {"locale": locale})
        logger.info("welcome email sent to %s user=%s", to_email, user.id)
        return True
    except Exception as exc:
        logger.warning("welcome email failed user=%s: %s", user.id, exc)
        return False
