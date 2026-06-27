"""用户路由: 当前用户信息。"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.auth.deps import CurrentUser
from backend.app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut, summary="获取当前登录用户")
def read_me(current_user: CurrentUser) -> UserOut:
    return UserOut.model_validate(current_user)
