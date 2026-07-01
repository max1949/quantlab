"""运营: 批量生成月卡兑换码 (需 ADMIN_API_KEY)。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.services import membership_service as ms

router = APIRouter()


class BatchCodesIn(BaseModel):
    count: int = Field(ge=1, le=200, default=10)
    tier: int = Field(ge=1, le=2, default=1)
    period_days: int = Field(ge=1, le=365, default=30)
    plan_code: str = "plus_monthly"
    note: str | None = None


class BatchCodesOut(BaseModel):
    created: int
    codes: list[str]


def require_admin(x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None) -> None:
    settings = get_settings()
    expected = getattr(settings, "admin_api_key", "") or ""
    if not expected or x_admin_key != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无效的管理密钥")


@router.post(
    "/codes/batch",
    response_model=BatchCodesOut,
    summary="批量生成兑换码 (Header: X-Admin-Key)",
)
def batch_create_codes(
    payload: BatchCodesIn,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin)],
) -> BatchCodesOut:
    codes: list[str] = []
    for _ in range(payload.count):
        rc = ms.create_redeem_code(
            db,
            tier=payload.tier,
            period_days=payload.period_days,
            plan_code=payload.plan_code,
            note=payload.note,
        )
        codes.append(rc.code)
    return BatchCodesOut(created=len(codes), codes=codes)
