"""认证路由: 注册 / 登录。

路由层只做编排: 调 service, 把领域异常翻译成 HTTP 响应。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.security import create_access_token
from backend.app.core.database import get_db
from backend.app.schemas.user import Token, UserCreate, UserLogin, UserOut
from backend.app.services import user_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="注册新用户 (默认等级 L0 观察员)",
)
def register(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserOut:
    try:
        user = user_service.create_user(db, payload)
    except user_service.UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{exc.field} 已被注册",
        )
    return UserOut.model_validate(user)


@router.post("/login", response_model=Token, summary="登录获取 JWT")
def login(
    payload: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    try:
        user = user_service.authenticate(db, payload.identifier, payload.password)
    except user_service.InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/邮箱或密码错误",
        )
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)
