"""图形验证码 (HMAC 签名 token, 5 分钟有效)。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time

from backend.app.core.config import get_settings

_CHARS = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
_TTL_SEC = 300


def _secret() -> str | None:
    s = get_settings().captcha_secret or get_settings().secret_key
    return s if s and s != "change-me-in-production" else get_settings().secret_key


def issue_captcha() -> dict[str, str] | None:
    secret = _secret()
    if not secret:
        return None
    code = "".join(secrets.choice(_CHARS) for _ in range(4))
    exp = int(time.time()) + _TTL_SEC
    payload = f"{code}:{exp}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    token = (
        base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
        + "."
        + base64.urlsafe_b64encode(sig).decode().rstrip("=")
    )
    return {"code": code, "token": token, "svg": _render_svg(code)}


def verify_captcha(answer: str, token: str) -> bool:
    secret = _secret()
    if not secret or not answer or not token:
        return False
    parts = token.split(".", 1)
    if len(parts) != 2:
        return False
    enc, sig_b64 = parts
    pad = "=" * (-len(enc) % 4)
    try:
        payload = base64.urlsafe_b64decode(enc + pad).decode()
        sig = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))
    except (ValueError, UnicodeDecodeError):
        return False
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return False
    code, exp_s = payload.split(":", 1)
    if int(exp_s) < int(time.time()):
        return False
    return answer.strip().upper() == code.upper()


def _render_svg(code: str) -> str:
    rects = []
    for i, ch in enumerate(code):
        x = 18 + i * 28
        y = 30
        rects.append(
            f'<text x="{x}" y="{y}" fill="#3478f6" font-size="24" '
            f'font-family="monospace" font-weight="700">{ch}</text>'
        )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="140" height="48" '
        'viewBox="0 0 140 48"><rect width="140" height="48" rx="8" '
        f'fill="#1e293b"/>{"".join(rects)}</svg>'
    )
