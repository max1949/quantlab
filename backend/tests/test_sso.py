"""企业 SSO (OIDC) 状态与 state 签名测试。"""

from __future__ import annotations

from backend.app.services import sso_service

BASE = "/api/v1"


def test_sso_disabled_by_default(client):
    resp = client.get(f"{BASE}/auth/sso/config")
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


def test_sso_login_404_when_disabled(client):
    resp = client.get(f"{BASE}/auth/sso/login", follow_redirects=False)
    assert resp.status_code == 404


def test_state_sign_and_verify():
    state = sso_service.issue_state()
    assert sso_service.verify_state(state) is True
    assert sso_service.verify_state("tampered.123.abc") is False
    assert sso_service.verify_state("") is False


def test_get_or_create_user_by_email(db_session):
    from sqlalchemy import select

    from backend.app.models.user import User

    info = {"email": "SSO.User@Corp.com", "preferred_username": "ssouser"}
    user = sso_service.get_or_create_user(db_session, info)
    assert user.email == "sso.user@corp.com"
    assert user.username == "ssouser"

    # 再次调用同邮箱应复用同一账号。
    again = sso_service.get_or_create_user(db_session, info)
    assert again.id == user.id

    count = db_session.execute(
        select(User).where(User.email == "sso.user@corp.com")
    ).scalars().all()
    assert len(count) == 1
