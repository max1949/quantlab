"""科学验证路由 (Sprint 5): 创建 (异步) / 列表 / 详情。"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.schemas.validation import (
    ValidationCreate,
    ValidationDetail,
    ValidationSummary,
)
from backend.app.services import backtest_service, factor_service, validation_service

router = APIRouter()


@router.post(
    "",
    response_model=ValidationDetail,
    status_code=status.HTTP_201_CREATED,
    summary="创建并运行科学验证 (OOS + Walk-Forward + 敏感性; 异步/Celery)",
)
def create_validation(
    payload: ValidationCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ValidationDetail:
    try:
        v = validation_service.create_and_run(
            db,
            current_user,
            payload.factor_id,
            payload.symbol,
            {"fee_rate": payload.fee_rate, "slippage_bps": payload.slippage_bps},
            payload.oos_ratio,
            payload.n_splits,
        )
    except factor_service.FactorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在")
    except backtest_service.DatasetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行情数据集不存在 (先生成样本数据: scripts/seed-market-data.ps1)",
        )
    return ValidationDetail.model_validate(v)


@router.get("", response_model=list[ValidationSummary], summary="我的验证列表")
def list_validations(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[ValidationSummary]:
    return [
        ValidationSummary.model_validate(v)
        for v in validation_service.list_validations(db, current_user.id)
    ]


@router.get("/{validation_id}", response_model=ValidationDetail, summary="验证详情")
def get_validation(
    validation_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ValidationDetail:
    try:
        v = validation_service.get_validation(
            db, current_user.id, uuid.UUID(validation_id)
        )
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="验证不存在")
    return ValidationDetail.model_validate(v)
