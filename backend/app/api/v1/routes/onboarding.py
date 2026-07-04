"""分流 + onboarding 路由 (Sprint 9A)。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.core.locale import RequestLocale
from backend.app.schemas.growth import (
    ChooseTypeRequest,
    DismissAttentionAlertOut,
    DismissAttentionAlertRequest,
    NextStepOut,
    ResearchJourneyOut,
)
from backend.app.schemas.user import UserOut
from backend.app.services import growth_service, onboarding_service, regime_alert_service

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


@router.get("/journey", response_model=ResearchJourneyOut, summary="七步研究闭环进度")
def research_journey(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    locale: RequestLocale,
) -> ResearchJourneyOut:
    return ResearchJourneyOut(**onboarding_service.research_journey(db, current_user, locale))


@router.post(
    "/attention-alerts/dismiss",
    response_model=DismissAttentionAlertOut,
    status_code=status.HTTP_200_OK,
    summary="忽略工作台主动提醒 (冷却期内不再展示)",
)
def dismiss_attention_alert(
    payload: DismissAttentionAlertRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> DismissAttentionAlertOut:
    try:
        out = regime_alert_service.dismiss_attention_alert(
            db, current_user.id, payload.alert_key
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    growth_service.log_event(
        db, "dismiss_attention_alert", current_user.id, {"alert_key": payload.alert_key}
    )
    return DismissAttentionAlertOut(**out)
