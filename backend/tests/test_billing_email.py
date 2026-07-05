"""计费凭证邮件测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from backend.app.models.billing_ledger import BillingLedger
from backend.app.models.user import User
from backend.app.services import billing_email_service as bes
from backend.app.services import membership_service as ms


def test_smtp_not_configured_by_default():
    assert bes.smtp_configured() is False


def test_notify_skipped_when_smtp_disabled(db_session):
    user = User(email="mail@x.com", username="mailuser", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    ledger = BillingLedger(
        scope="personal",
        event="redeem",
        user_id=user.id,
        actor_id=user.id,
        plan_code="plus_monthly",
        plan_name="研究员月卡",
        tier=1,
        amount_cny=499,
        source="redeem",
        detail="test",
    )
    db_session.add(ledger)
    db_session.commit()

    assert bes.notify_receipt_for_ledger(db_session, ledger) is False


def test_build_receipt_email_contains_links(db_session):
    user = User(email="rcp@x.com", username="rcpuser", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    ledger = BillingLedger(
        scope="personal",
        event="checkout",
        user_id=user.id,
        actor_id=user.id,
        plan_code="pro_monthly",
        plan_name="专业研究员月卡",
        tier=2,
        amount_cny=2999,
        source="checkout",
        detail="test",
    )
    db_session.add(ledger)
    db_session.commit()
    db_session.refresh(ledger)

    subject, body = bes.build_receipt_email(ledger, locale="zh")
    assert "专业研究员月卡" in subject
    assert str(ledger.id) in body
    assert "/pricing?receipt=" in body
    assert "/app" in body


def test_notify_sends_when_smtp_configured(db_session, monkeypatch):
    from backend.app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from", "billing@quantlab.ai")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_user", "")
    monkeypatch.setattr(settings, "smtp_password", "")

    user = User(email="send@x.com", username="senduser", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    ledger = BillingLedger(
        scope="personal",
        event="redeem",
        user_id=user.id,
        actor_id=user.id,
        plan_code="plus_monthly",
        plan_name=ms.PLAN_BY_CODE["plus_monthly"]["name"],
        tier=1,
        amount_cny=499,
        source="redeem",
        detail="test",
    )
    db_session.add(ledger)
    db_session.commit()
    db_session.refresh(ledger)

    mock_smtp = MagicMock()
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    with patch("backend.app.services.billing_email_service.smtplib.SMTP", mock_smtp):
        assert bes.notify_receipt_for_ledger(db_session, ledger) is True

    mock_smtp.assert_called_once()
    mock_server.sendmail.assert_called_once()
