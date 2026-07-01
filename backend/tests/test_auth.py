"""用户系统接口测试: 注册 / 登录 / JWT / /users/me / 等级。"""

from __future__ import annotations

BASE = "/api/v1"

VALID_USER = {
    "email": "alice@quantlab.ai",
    "username": "alice",
    "password": "s3cret-pass",
}


def _register(client, **overrides):
    payload = {**VALID_USER, **overrides}
    return client.post(f"{BASE}/auth/register", json=payload)


def _login(client, identifier: str, password: str):
    return client.post(
        f"{BASE}/auth/login",
        json={"identifier": identifier, "password": password},
    )


def test_register_success_defaults_to_l0(client):
    resp = _register(client)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    user = body["user"]
    assert user["email"] == VALID_USER["email"]
    assert user["username"] == VALID_USER["username"]
    assert user["level"] == 0
    assert user["level_label"] == "观察员"
    assert user["research_score"] == 0
    assert user["is_active"] is True
    assert "access_token" in body
    assert "hashed_password" not in user
    assert "password" not in user


def test_register_duplicate_email_conflicts(client):
    assert _register(client).status_code == 201
    resp = _register(client, username="alice2")  # 同邮箱不同用户名
    assert resp.status_code == 409


def test_register_duplicate_username_conflicts(client):
    assert _register(client).status_code == 201
    resp = _register(client, email="other@quantlab.ai")
    assert resp.status_code == 409


def test_register_weak_password_rejected(client):
    resp = _register(client, password="short")
    assert resp.status_code == 422


def test_register_bad_email_rejected(client):
    resp = _register(client, email="not-an-email")
    assert resp.status_code == 422


def test_login_with_email_and_username(client):
    _register(client)
    for identifier in (VALID_USER["email"], VALID_USER["username"]):
        resp = _login(client, identifier, VALID_USER["password"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]


def test_login_wrong_password_unauthorized(client):
    _register(client)
    resp = _login(client, VALID_USER["username"], "wrong-password")
    assert resp.status_code == 401


def test_login_unknown_user_unauthorized(client):
    resp = _login(client, "ghost", "whatever-pass")
    assert resp.status_code == 401


def test_me_with_valid_token(client):
    _register(client)
    token = _login(client, VALID_USER["username"], VALID_USER["password"]).json()[
        "access_token"
    ]
    resp = client.get(
        f"{BASE}/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["username"] == VALID_USER["username"]


def test_me_without_token_forbidden(client):
    # HTTPBearer(auto_error=True): 缺少凭证 -> 403
    resp = client.get(f"{BASE}/users/me")
    assert resp.status_code == 403


def test_me_with_invalid_token_unauthorized(client):
    resp = client.get(
        f"{BASE}/users/me",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert resp.status_code == 401
