"""用户业务逻辑。

路由层保持"薄"(只编排), 注册/登录的实际规则集中在这里:
唯一性校验、密码哈希、凭证验证。抛出领域异常, 由路由翻译为 HTTP 响应。
"""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.auth.security import hash_password, verify_password
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate


class UserAlreadyExistsError(Exception):
    """邮箱或用户名已被占用。"""

    def __init__(self, field: str) -> None:
        self.field = field
        super().__init__(f"{field} already registered")


class InvalidCredentialsError(Exception):
    """登录凭证无效。"""


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_by_identifier(db: Session, identifier: str) -> User | None:
    """按邮箱或用户名查找 (登录用)。"""
    stmt = select(User).where(
        or_(User.email == identifier, User.username == identifier)
    )
    return db.execute(stmt).scalar_one_or_none()


def create_user(db: Session, payload: UserCreate) -> User:
    """创建用户。邮箱/用户名重复时抛 ``UserAlreadyExistsError``。"""
    if db.execute(
        select(User.id).where(User.email == payload.email)
    ).first():
        raise UserAlreadyExistsError("email")
    if db.execute(
        select(User.id).where(User.username == payload.username)
    ).first():
        raise UserAlreadyExistsError("username")

    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
    )
    if payload.user_type is not None:
        user.user_type = payload.user_type.value
        user.onboarding_done = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, identifier: str, password: str) -> User:
    """校验凭证, 成功返回 User, 失败抛 ``InvalidCredentialsError``。

    注意: 用户不存在与密码错误返回同一异常, 避免账号枚举。
    """
    user = get_by_identifier(db, identifier)
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError
    if not user.is_active:
        raise InvalidCredentialsError
    return user
