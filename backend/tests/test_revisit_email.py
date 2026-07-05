"""注册后回流邮件测试。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from sqlalchemy import select

from backend.app.models.user import User
from backend.app.services import revisit_email_service as res


def test_revisit_email_skipped_when_smtp_disabled(db_session):
    user = User(
        email="st@x.com",
        username="stalled",
        hashed_password="x",
        onboarding_done=True,
    )
    db_session.add(user)
    db_session.commit()
    assert res.maybe_send_revisit_email(db_session, user) is False


def test_build_revisit_email_contains_links():
    user = User(email="rv@x.com", username="rvuser", hashed_password="x")
    subject, body = res.build_revisit_email(user, days=5, locale="zh")
    assert "大师" in subject
    assert "rvuser" in body
    assert "5" in body
    assert "/templates" in body
    assert "/app" in body


def test_maybe_send_revisit_when_eligible(db_session, monkeypatch):
    from backend.app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from", "hello@quantlab.ai")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_user", "")
    monkeypatch.setattr(settings, "smtp_password", "")

    user = User(
        email="eligible@x.com",
        username="eligible",
        hashed_password="x",
        onboarding_done=True,
        created_at=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db_session.add(user)
    db_session.commit()

    mock_smtp = MagicMock()
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    with patch("backend.app.services.billing_email_service.smtplib.SMTP", mock_smtp):
        assert res.maybe_send_revisit_email(db_session, user) is True
        assert res.maybe_send_revisit_email(db_session, user) is False

    mock_server.sendmail.assert_called_once()
    from backend.app.models.growth import UserEvent

    ev = db_session.execute(
        select(UserEvent).where(UserEvent.user_id == user.id, UserEvent.event == "revisit_email")
    ).scalar_one()
    assert ev.props.get("days") == 5


def test_run_scheduled_revisit_batch(db_session, monkeypatch):
    from backend.app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from", "hello@quantlab.ai")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_user", "")
    monkeypatch.setattr(settings, "smtp_password", "")

    user = User(
        email="cron@x.com",
        username="cronuser",
        hashed_password="x",
        onboarding_done=True,
        created_at=datetime.now(timezone.utc) - timedelta(days=4),
    )
    db_session.add(user)
    db_session.commit()

    mock_smtp = MagicMock()
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    with patch("backend.app.services.billing_email_service.smtplib.SMTP", mock_smtp):
        result = res.run_scheduled_revisit_batch(db_session, limit=10)
        assert result["sent"] == 1
        assert result["failed"] == 0
        result2 = res.run_scheduled_revisit_batch(db_session, limit=10)
        assert result2["sent"] == 0

    mock_server.sendmail.assert_called_once()
