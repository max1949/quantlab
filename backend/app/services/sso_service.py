"""企业 SSO (OIDC Authorization Code Flow) 适配层。

留空配置则视为未启用。仅依赖 httpx, 不引入额外 OIDC SDK。
state 使用短时 HMAC 签名令牌 (无需服务端存储), 防 CSRF。
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import urllib.parse
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.auth.security import hash_password
from backend.app.core.config import get_settings
from backend.app.models.user import User

_STATE_TTL = 600


class SsoNotConfiguredError(Exception):
    pass


class SsoError(Exception):
    pass


def sso_configured() -> bool:
    s = get_settings()
    return bool(s.oidc_client_id and s.oidc_client_secret and s.oidc_issuer)


def _endpoints() -> dict[str, str]:
    s = get_settings()
    issuer = s.oidc_issuer.rstrip("/")
    return {
        "authorization": s.oidc_authorization_endpoint or f"{issuer}/authorize",
        "token": s.oidc_token_endpoint or f"{issuer}/oauth/token",
        "userinfo": s.oidc_userinfo_endpoint or f"{issuer}/userinfo",
    }


def _sign_state(nonce: str, ts: int) -> str:
    s = get_settings()
    msg = f"{nonce}.{ts}"
    sig = hmac.new(s.secret_key.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return f"{msg}.{sig}"


def issue_state() -> str:
    return _sign_state(secrets.token_urlsafe(16), int(time.time()))


def verify_state(state: str) -> bool:
    parts = (state or "").split(".")
    if len(parts) != 3:
        return False
    nonce, ts_raw, sig = parts
    try:
        ts = int(ts_raw)
    except ValueError:
        return False
    if abs(time.time() - ts) > _STATE_TTL:
        return False
    expected = _sign_state(nonce, ts)
    return hmac.compare_digest(expected, state)


def build_authorize_url(redirect_uri: str) -> str:
    if not sso_configured():
        raise SsoNotConfiguredError("SSO 未配置")
    s = get_settings()
    params = {
        "response_type": "code",
        "client_id": s.oidc_client_id,
        "redirect_uri": redirect_uri,
        "scope": s.oidc_scopes,
        "state": issue_state(),
    }
    return f"{_endpoints()['authorization']}?{urllib.parse.urlencode(params)}"


def exchange_code(code: str, redirect_uri: str) -> dict:
    s = get_settings()
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            _endpoints()["token"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": s.oidc_client_id,
                "client_secret": s.oidc_client_secret,
            },
            headers={"Accept": "application/json"},
        )
    if resp.status_code != 200:
        raise SsoError("令牌交换失败")
    return resp.json()


def fetch_userinfo(access_token: str) -> dict:
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(
            _endpoints()["userinfo"],
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise SsoError("获取用户信息失败")
    return resp.json()


def _unique_username(db: Session, base: str) -> str:
    base = "".join(ch for ch in base if ch.isalnum() or ch in "-_") or "user"
    base = base[:40]
    candidate = base
    n = 1
    while db.execute(select(User.id).where(User.username == candidate)).first():
        n += 1
        candidate = f"{base}-{n}"[:48]
    return candidate


def get_or_create_user(db: Session, userinfo: dict) -> tuple[User, bool]:
    email = (userinfo.get("email") or "").strip().lower()
    if not email:
        raise SsoError("身份提供商未返回邮箱")

    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is not None:
        return user, False

    base = userinfo.get("preferred_username") or email.split("@")[0]
    username = _unique_username(db, str(base))
    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(uuid.uuid4().hex),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True
