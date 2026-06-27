"""认证相关的 FastAPI 依赖。

- ``get_current_user``: 从 Bearer 令牌解析出当前用户。
- ``require_level``: 等级权限闸门工厂 (L0<L1<L2<L3)。Sprint 2 起各受限路由
  以 ``Depends(require_level(UserLevel.Lx))`` 声明所需最低等级。
"""

from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.auth.security import ACCESS_TOKEN_TYPE, decode_token
from backend.app.core.database import get_db
from backend.app.models.user import User, UserLevel
from backend.app.services import user_service

bearer_scheme = HTTPBearer(auto_error=True)

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="无效或过期的凭证",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise _CREDENTIALS_EXC

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise _CREDENTIALS_EXC
    subject = payload.get("sub")
    if not subject:
        raise _CREDENTIALS_EXC
    try:
        user_id = uuid.UUID(str(subject))
    except ValueError:
        raise _CREDENTIALS_EXC

    user = user_service.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_level(min_level: UserLevel):
    """生成一个校验"当前用户等级 >= min_level"的依赖。"""

    def _checker(current_user: CurrentUser) -> User:
        if current_user.user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要等级 {min_level.name} ({min_level.label}) 或以上",
            )
        return current_user

    return _checker
