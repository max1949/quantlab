"""AI 研究助手路由 (Sprint 7): 验证复盘 / 回测总结 / 状态 / 我的洞察。

对所有登录用户开放。是否接入外部 LLM 由服务端配置决定; 未接入时自动降级为本地规则分析,
接口形状不变 (响应里的 `source` 标注 llm 还是 local)。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.schemas.ai import AiStatusOut, InsightOut
from backend.app.services import ai_service

router = APIRouter()


@router.get("/status", response_model=AiStatusOut, summary="AI 助手状态 (是否接入 LLM)")
def ai_status(current_user: CurrentUser) -> AiStatusOut:
    return AiStatusOut(**ai_service.ai_status())


@router.get("/insights", response_model=list[InsightOut], summary="我的 AI 洞察列表")
def my_insights(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[InsightOut]:
    return [
        InsightOut.model_validate(i)
        for i in ai_service.list_insights(db, current_user.id)
    ]


@router.post(
    "/validations/{validation_id}/review",
    response_model=InsightOut,
    status_code=status.HTTP_201_CREATED,
    summary="AI 复盘科学验证结果 (优点/风险/改进建议)",
)
def review_validation(
    validation_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InsightOut:
    try:
        insight = ai_service.review_validation(db, current_user, uuid.UUID(validation_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="验证不存在")
    except ai_service.TargetNotReadyError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="验证不存在 / 非本人 / 未成功, 无法复盘",
        )
    return InsightOut.model_validate(insight)


@router.post(
    "/backtests/{backtest_id}/summary",
    response_model=InsightOut,
    status_code=status.HTTP_201_CREATED,
    summary="AI 总结回测研究报告 (通俗版)",
)
def summarize_backtest(
    backtest_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InsightOut:
    try:
        insight = ai_service.summarize_backtest(db, current_user, uuid.UUID(backtest_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="回测不存在")
    except ai_service.TargetNotReadyError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="回测不存在 / 非本人 / 未成功, 无法总结",
        )
    return InsightOut.model_validate(insight)
