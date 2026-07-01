"""全站多维榜单路由 (Sprint 9A): researcher / contributor / newcomer / improved。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.growth import LeaderRow
from backend.app.services import leaderboard_service

router = APIRouter()


@router.get("/{kind}", response_model=list[LeaderRow], summary="多维榜单 (公开可读)")
def leaderboard(
    kind: str,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
) -> list[LeaderRow]:
    try:
        rows = leaderboard_service.leaderboard(db, kind, limit)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未知榜单, 可选: researcher / contributor / newcomer / improved",
        )
    return [LeaderRow(**r) for r in rows]
