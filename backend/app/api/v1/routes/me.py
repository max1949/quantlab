"""当前用户的增长视图 (Sprint 9A): 邀请战绩 / 关注 Feed。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.schemas.growth import ReferralOut
from backend.app.schemas.research import ReportSummary
from backend.app.services import referral_service, social_service

router = APIRouter()


@router.get("/referral", response_model=ReferralOut, summary="我的邀请码与战绩")
def my_referral(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ReferralOut:
    return ReferralOut(**referral_service.my_referral(db, current_user))


@router.get("/feed", response_model=list[ReportSummary], summary="我关注的研究员的最新研究")
def my_feed(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 30,
) -> list[ReportSummary]:
    return [ReportSummary.model_validate(r) for r in social_service.feed(db, current_user.id, limit)]
