"""研究员主页路由 (Sprint 8): GET /researchers/{id} 与 /researchers/me。

研究档案是公开的身份资产 (类似 GitHub Profile), 任何登录用户可查看他人主页。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.schemas.profile import ResearcherProfile
from backend.app.services import profile_service, social_service

router = APIRouter()


@router.get("/me", response_model=ResearcherProfile, summary="我的研究主页")
def my_profile(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ResearcherProfile:
    return ResearcherProfile(**profile_service.build_profile(db, current_user))


@router.get("/{user_id}", response_model=ResearcherProfile, summary="研究员主页 (统计 + 方向标签 + 关注状态)")
def researcher_profile(
    user_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ResearcherProfile:
    try:
        user = profile_service.get_user(db, uuid.UUID(user_id))
    except ValueError:
        user = None
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return ResearcherProfile(**profile_service.build_profile(db, user, viewer=current_user))


@router.post("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT, summary="关注研究员")
def follow(
    user_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        social_service.follow(db, current_user, uuid.UUID(user_id))
    except (social_service.UserNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    except social_service.CannotFollowSelfError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不能关注自己")


@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT, summary="取消关注")
def unfollow(
    user_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        social_service.unfollow(db, current_user, uuid.UUID(user_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
