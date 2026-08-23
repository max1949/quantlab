"""AI 研究助手路由 (Sprint 7): 验证复盘 / 回测总结 / 状态 / 我的洞察。

对所有登录用户开放。是否接入外部 LLM 由服务端配置决定; 未接入时自动降级为本地规则分析,
接口形状不变 (响应里的 `source` 标注 llm 还是 local)。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from pydantic import BaseModel, Field

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.core.locale import RequestLocale
from backend.app.schemas.ai import AiStatusOut, InsightOut
from backend.app.schemas.growth import MentorOut
from backend.app.services import ai_service, rate_limit

router = APIRouter()


def _check_ai_quota(user_id) -> None:
    try:
        rate_limit.check_ai(str(user_id))
    except rate_limit.RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))


class ResearchPlanRequest(BaseModel):
    theme: str = Field(min_length=1, max_length=120)  # 研究方向, 如"黄金"/"螺纹钢趋势"


@router.get("/mentor/next", response_model=MentorOut, summary="AI 研究导师: 下一步提醒 (基于当前进度)")
def mentor_next(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    locale: RequestLocale,
) -> MentorOut:
    return MentorOut(**ai_service.mentor_next(db, current_user, locale))


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
    "/research-plan",
    response_model=InsightOut,
    status_code=status.HTTP_201_CREATED,
    summary="AI 研究指导: 给方向 → 研究假设 + 推荐因子 + 实验计划 (不给交易建议)",
)
def research_plan(
    payload: ResearchPlanRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InsightOut:
    _check_ai_quota(current_user.id)
    insight = ai_service.research_plan(db, current_user, payload.theme)
    return InsightOut.model_validate(insight)


@router.post(
    "/scans/{scan_id}/review",
    response_model=InsightOut,
    status_code=status.HTTP_201_CREATED,
    summary="AI 解读因子参数扫描结果",
)
def review_factor_scan(
    scan_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InsightOut:
    _check_ai_quota(current_user.id)
    try:
        insight = ai_service.review_scan(db, current_user, uuid.UUID(scan_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="扫描不存在")
    except ai_service.TargetNotReadyError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="扫描不存在 / 非本人, 无法解读",
        )
    return InsightOut.model_validate(insight)


class ScanBatchReviewRequest(BaseModel):
    scan_ids: list[str] = Field(min_length=2, max_length=5)


@router.post(
    "/scans/review-batch",
    response_model=InsightOut,
    status_code=status.HTTP_201_CREATED,
    summary="AI 批量对比解读多条参数扫描",
)
def review_factor_scans_batch(
    payload: ScanBatchReviewRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InsightOut:
    _check_ai_quota(current_user.id)
    try:
        ids = [uuid.UUID(s) for s in payload.scan_ids]
        insight = ai_service.review_scans_batch(db, current_user, ids)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="无效的扫描 ID")
    except ai_service.TargetNotReadyError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="扫描不存在 / 非本人, 无法批量解读",
        )
    return InsightOut.model_validate(insight)


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
    _check_ai_quota(current_user.id)
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


class StrategyBuilderRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    confirm: bool = False
    run_backtest: bool = False


@router.post(
    "/strategy-builder",
    summary="中文交易想法 → Strategy Spec 草稿 (不可实盘)",
)
def strategy_builder(
    body: StrategyBuilderRequest,
    current_user: CurrentUser,
) -> dict:
    """QUANTLAB_AI_STRATEGY_BUILDER feature path. AI cannot approve LIVE."""
    from backend.app.core.config import get_settings
    from engine.ai.mvp_pipeline import run_mvp_chinese_idea
    from engine.ai.strategy_builder import build_strategy_from_chinese

    settings = get_settings()
    if not (
        settings.quantlab_ai_strategy_builder
        or settings.quantlab_nautilus_engine
        or settings.app_env in {"development", "test"}
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI 策略构建器未启用",
        )
    _check_ai_quota(current_user.id)
    if body.run_backtest:
        return run_mvp_chinese_idea(body.text, confirm=body.confirm)
    built = build_strategy_from_chinese(body.text, author=str(current_user.id))
    return {"live_denied": True, "builder": built.to_dict()}


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
    _check_ai_quota(current_user.id)
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
