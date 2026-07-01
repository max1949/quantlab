"""分流 + onboarding 路由 (Sprint 9A)。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.core.locale import RequestLocale
from backend.app.schemas.growth import ChooseTypeRequest, NextStepOut
from backend.app.schemas.user import UserOut
from backend.app.services import growth_service, onboarding_service

router = APIRouter()


@router.post("/choose-type", response_model=UserOut, summary="选择分流身份 (新手/Python/交易经验)")
def choose_type(
    payload: ChooseTypeRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> UserOut:
    try:
        user = onboarding_service.choose_type(db, current_user, payload.user_type.value)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="未知用户类型")
    growth_service.log_event(db, "choose_type", user.id, {"user_type": user.user_type})
    return UserOut.model_validate(user)


@router.get("/next", response_model=NextStepOut, summary="个性化下一步 (身份 + 进度)")
def next_step(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    locale: RequestLocale,
) -> NextStepOut:
    return NextStepOut(**onboarding_service.next_step(db, current_user, locale))
