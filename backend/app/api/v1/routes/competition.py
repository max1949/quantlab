"""竞技系统路由 (Sprint 6): 赛季 / 提交 / 排行榜。

赛季创建用 require_level(L3) 把关 (由高级研究员管理赛季); 提交对所有登录用户开放。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser, require_level
from backend.app.core.database import get_db
from backend.app.models.user import User, UserLevel
from backend.app.schemas.competition import (
    LeaderboardRow,
    SeasonCreate,
    SeasonOut,
    SubmissionCreate,
    SubmissionOut,
)
from backend.app.services import competition_service

router = APIRouter()


@router.get("", response_model=list[SeasonOut], summary="赛季列表")
def list_seasons(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[SeasonOut]:
    return [SeasonOut.model_validate(s) for s in competition_service.list_seasons(db)]


@router.post(
    "",
    response_model=SeasonOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建赛季 (需 L3, 高级研究员管理)",
)
def create_season(
    payload: SeasonCreate,
    current_user: Annotated[User, Depends(require_level(UserLevel.L3))],
    db: Annotated[Session, Depends(get_db)],
) -> SeasonOut:
    try:
        season = competition_service.create_season(db, payload.name, payload.description)
    except competition_service.SeasonNameTakenError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="赛季名已存在")
    return SeasonOut.model_validate(season)


@router.post(
    "/{season_id}/submissions",
    response_model=SubmissionOut,
    status_code=status.HTTP_201_CREATED,
    summary="提交已通过科学验证的因子到赛季 (计算 Research Score)",
)
def submit(
    season_id: str,
    payload: SubmissionCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> SubmissionOut:
    try:
        sub = competition_service.submit(
            db, current_user, uuid.UUID(season_id), payload.validation_id
        )
    except (competition_service.SeasonNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="赛季不存在")
    except competition_service.SeasonClosedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="赛季已结束")
    except competition_service.ValidationNotEligibleError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="验证不存在 / 非本人 / 未成功, 不可提交",
        )
    except competition_service.AlreadySubmittedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该验证已提交过")
    return SubmissionOut.model_validate(sub)


@router.get(
    "/{season_id}/leaderboard",
    response_model=list[LeaderboardRow],
    summary="赛季排行榜 (按最终分降序)",
)
def leaderboard(
    season_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
) -> list[LeaderboardRow]:
    try:
        rows = competition_service.leaderboard(db, uuid.UUID(season_id), limit)
    except (competition_service.SeasonNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="赛季不存在")
    return [LeaderboardRow(**r) for r in rows]


@router.get(
    "/{season_id}/submissions/me",
    response_model=list[SubmissionOut],
    summary="我在该赛季的提交",
)
def my_submissions(
    season_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[SubmissionOut]:
    try:
        sid = uuid.UUID(season_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="赛季不存在")
    return [
        SubmissionOut.model_validate(s)
        for s in competition_service.list_my_submissions(db, current_user.id, sid)
    ]
