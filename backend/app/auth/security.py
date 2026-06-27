"""认证原语: 密码哈希 + JWT 签发/校验。

仅放纯函数 (无 DB / 无请求上下文), 便于单测与复用。
- 密码: bcrypt (passlib CryptContext)
- 令牌: HS256 JWT (pyjwt), 载荷含 sub(用户id) / exp / iat / type
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from backend.app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_TYPE = "access"


def hash_password(plain: str) -> str:
    """对明文密码做 bcrypt 哈希。"""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    return pwd_context.verify(plain, hashed)


def create_access_token(
    subject: str, expires_delta: timedelta | None = None
) -> str:
    """签发访问令牌。``subject`` 通常是用户主键 (str(uuid))。"""
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "type": ACCESS_TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """解码并校验令牌签名/过期。

    校验失败 (签名错误 / 过期 / 格式错误) 抛出 ``jwt.PyJWTError`` 子类,
    由调用方 (依赖) 转换为 401。
    """
    return jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
