"""注册欢迎邮件测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from backend.app.models.user import User
from backend.app.services import welcome_email_service as wes


def test_welcome_email_skipped_when_smtp_disabled(db_session):
    user = User(email="new@x.com", username="newbie1", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    assert wes.notify_welcome_email(db_session, user) is False


def test_build_welcome_email_contains_handbook_and_dashboard():
    user = User(email="wb@x.com", username="wbuser", hashed_password="x")
    subject, body = wes.build_welcome_email(user, locale="zh")
    assert "欢迎" in subject
    assert "wbuser" in body
    assert "/handbook" in body
    assert "/app" in body


def test_notify_welcome_sends_when_smtp_configured(db_session, monkeypatch):
    from backend.app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from", "hello@quantlab.ai")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_user", "")
    monkeypatch.setattr(settings, "smtp_password", "")

    user = User(email="send@x.com", username="sendwel", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    mock_smtp = MagicMock()
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    with patch("backend.app.services.billing_email_service.smtplib.SMTP", mock_smtp):
        assert wes.notify_welcome_email(db_session, user) is True

    mock_server.sendmail.assert_called_once()
