"""计费凭证邮件 — 支付/兑换后自动发送 PDF 下载指引。"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.locale import Locale
from backend.app.i18n import content as i18n
from backend.app.models.billing_ledger import BillingLedger
from backend.app.models.organization import ResearchOrg
from backend.app.models.user import User
from backend.app.services import billing_ledger_service as bls
from backend.app.services import membership_service as ms

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    settings = get_settings()
    return bool(settings.smtp_host.strip() and settings.smtp_from.strip())


def _recipient_email(db: Session, ledger: BillingLedger) -> str | None:
    if ledger.scope == "personal" and ledger.user_id:
        user = db.get(User, ledger.user_id)
        return (user.email or "").strip().lower() if user else None
    if ledger.scope == "org":
        uid = ledger.actor_id or ledger.user_id
        if uid:
            user = db.get(User, uid)
            if user and user.email:
                return user.email.strip().lower()
        if ledger.org_id:
            org = db.get(ResearchOrg, ledger.org_id)
            if org:
                owner = db.get(User, org.owner_id)
                if owner and owner.email:
                    return owner.email.strip().lower()
    return None


def _receipt_link(ledger: BillingLedger) -> str:
    origin = ms.frontend_origin()
    if ledger.scope == "org" and ledger.org_id:
        return f"{origin}/orgs/{ledger.org_id}?receipt={ledger.id}"
    return f"{origin}/pricing?receipt={ledger.id}"


def _dashboard_link() -> str:
    return f"{ms.frontend_origin()}/app"


def _format_expires(expires) -> str:
    if expires is None:
        return "-"
    if hasattr(expires, "strftime"):
        return expires.strftime("%Y-%m-%d")
    return str(expires)


def build_receipt_email(
    ledger: BillingLedger,
    *,
    locale: Locale = "zh",
) -> tuple[str, str]:
    labels = i18n.BILLING_RECEIPT_EMAIL.get(locale) or i18n.BILLING_RECEIPT_EMAIL["en"]
    row = bls.ledger_to_dict(ledger)
    link = _receipt_link(ledger)
    dash = _dashboard_link()
    subject = labels["subject"].format(plan_name=row["plan_name"])
    body = labels["body"].format(
        plan_name=row["plan_name"],
        amount=row["amount_cny"],
        currency=row.get("currency", "CNY"),
        receipt_id=row["id"],
        expires=_format_expires(row.get("expires_at")),
        receipt_link=link,
        dashboard_link=dash,
    )
    return subject, body


def send_receipt_email(to_email: str, subject: str, body: str) -> None:
    settings = get_settings()
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from.strip()
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(settings.smtp_host.strip(), settings.smtp_port, timeout=20) as server:
        if settings.smtp_use_tls:
            server.starttls()
        user = settings.smtp_user.strip()
        if user:
            server.login(user, settings.smtp_password)
        server.sendmail(msg["From"], [to_email], msg.as_string())


def notify_receipt_for_ledger(
    db: Session,
    ledger: BillingLedger,
    *,
    locale: Locale = "zh",
) -> bool:
    """支付/兑换成功后发送凭证邮件；未配置 SMTP 时静默跳过。"""
    if not smtp_configured():
        return False
    if ledger.event not in ("redeem", "checkout"):
        return False

    to_email = _recipient_email(db, ledger)
    if not to_email:
        return False

    subject, body = build_receipt_email(ledger, locale=locale)
    try:
        send_receipt_email(to_email, subject, body)
        logger.info("billing receipt email sent to %s ledger=%s", to_email, ledger.id)
        return True
    except Exception as exc:
        logger.warning("billing receipt email failed ledger=%s: %s", ledger.id, exc)
        return False


def receipt_coaching_hint(locale: str = "zh") -> str | None:
    if not smtp_configured():
        return None
    loc: Locale = "zh" if locale == "zh" else "en"
    labels = i18n.BILLING_RECEIPT_EMAIL.get(loc) or i18n.BILLING_RECEIPT_EMAIL["en"]
    return labels.get("checkout_hint")
