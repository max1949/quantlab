"""30 天研究挑战路由 (Sprint 8): 列表 / 报名 / 进度 (自动判定)。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.core.locale import RequestLocale
from backend.app.i18n.content import localize_challenge, localize_progress
from backend.app.schemas.challenge import CertificateOut, ChallengeOut, ProgressOut
from backend.app.services import challenge_service

router = APIRouter()


@router.get("", response_model=list[ChallengeOut], summary="挑战列表")
def list_challenges(
    current_user: CurrentUser,
    locale: RequestLocale,
    db: Annotated[Session, Depends(get_db)],
) -> list[ChallengeOut]:
    return [
        ChallengeOut(**localize_challenge(c, locale))
        for c in challenge_service.list_challenges(db)
    ]


@router.post("/{code}/enroll", response_model=ProgressOut, summary="报名挑战")
def enroll(
    code: str,
    current_user: CurrentUser,
    locale: RequestLocale,
    db: Annotated[Session, Depends(get_db)],
) -> ProgressOut:
    try:
        was_enrolled = challenge_service.is_enrolled(db, current_user, code)
        challenge_service.enroll(db, current_user, code)
        result = challenge_service.evaluate(db, current_user, code)
        if not was_enrolled:
            from backend.app.services import academy_hooks

            result["academy_rewards"] = academy_hooks.on_challenge_enrolled(db, current_user)
        else:
            result["academy_rewards"] = []
        return ProgressOut(**localize_progress(result, locale))
    except challenge_service.ChallengeNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="挑战不存在")


@router.get("/{code}/progress", response_model=ProgressOut, summary="我的挑战进度 (实时按产物判定, 自动发奖)")
def progress(
    code: str,
    current_user: CurrentUser,
    locale: RequestLocale,
    db: Annotated[Session, Depends(get_db)],
) -> ProgressOut:
    try:
        return ProgressOut(**localize_progress(challenge_service.evaluate(db, current_user, code), locale))
    except challenge_service.ChallengeNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="挑战不存在")


@router.get("/{code}/certificate", response_model=CertificateOut, summary="领取完成证书 (需全部里程碑完成)")
def certificate(
    code: str,
    current_user: CurrentUser,
    locale: RequestLocale,
    db: Annotated[Session, Depends(get_db)],
) -> CertificateOut:
    try:
        cert = challenge_service.get_certificate(db, current_user, code)
        prog = localize_progress(challenge_service.evaluate(db, current_user, code), locale)
        cert["challenge_title"] = prog["title"]
        return CertificateOut(**cert)
    except challenge_service.ChallengeNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="挑战不存在")
    except challenge_service.ChallengeNotCompletedError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="挑战尚未全部完成, 暂不能领证书"
        )
