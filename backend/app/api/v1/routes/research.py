"""研究项目报告路由 (Sprint 8.1): 生成 / 我的报告 / 详情。

报告把"因子 + 回测 + 验证"聚合成人话叙事, 是研究生态的核心资产。
公开报告 (is_public) 可被他人查看, 为后续研究员主页/社区铺路。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.core.locale import RequestLocale
from backend.app.schemas.growth import (
    ShareOut,
    StartTemplateRequest,
    StartTemplateResult,
    TemplateOut,
)
from backend.app.schemas.research import (
    GenerateReportRequest,
    ReportDetail,
    ReportSummary,
)
from backend.app.services import membership_service as ms, research_service, share_service, template_service
from backend.app.i18n import content as i18n

router = APIRouter()


# --- 研究模板库 (Sprint 9A): 一键开局 ---
@router.get("/templates", response_model=list[TemplateOut], summary="研究模板库")
def list_research_templates(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    locale: RequestLocale,
) -> list[TemplateOut]:
    tier = ms.current_tier(db, current_user)
    items = template_service.list_templates_for_user(db, current_user, tier, locale)
    out = []
    for item in items:
        t = item["template"]
        loc = item["localized"]
        out.append(
            TemplateOut(
                code=t.code,
                title=loc["title"],
                symbol=t.symbol,
                factor_template=t.factor_template,
                default_params=t.default_params or {},
                hypothesis=loc["hypothesis"],
                description=loc["description"],
                tags=list(loc["tags"]),
                min_level=item["min_level"],
                min_tier=item["min_tier"],
                allowed=item["allowed"],
                lock_hint=item["lock_hint"],
            )
        )
    return out


@router.post(
    "/templates/{code}/start",
    response_model=StartTemplateResult,
    status_code=status.HTTP_201_CREATED,
    summary="从模板一键创建研究项目 (+默认因子)",
)
def start_from_template(
    code: str,
    payload: StartTemplateRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    locale: RequestLocale,
) -> StartTemplateResult:
    try:
        tier = ms.current_tier(db, current_user)
        res = template_service.start(
            db, current_user, code, with_factor=payload.with_factor, tier=tier, locale=locale
        )
    except template_service.TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=i18n.t(locale, i18n.TEMPLATE_NOT_FOUND),
        )
    except template_service.TemplateLockedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return StartTemplateResult(
        project_id=res["project"].id, factor_id=res["factor_id"], template_code=res["template_code"]
    )


@router.post(
    "/reports/generate",
    response_model=ReportDetail,
    status_code=status.HTTP_201_CREATED,
    summary="生成研究报告 (传 project_id 生成项目报告, 或 factor_id 生成因子报告)",
)
def generate_report(
    payload: GenerateReportRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ReportDetail:
    try:
        if payload.project_id is not None:
            report = research_service.generate_for_project(db, current_user, payload.project_id)
        elif payload.factor_id is not None:
            report = research_service.generate_for_factor(db, current_user, payload.factor_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="需提供 project_id 或 factor_id",
            )
    except (research_service.FactorNotFoundError, research_service.ProjectNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目/因子不存在")
    except research_service.NoResearchYetError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="还没有成功的回测或验证, 先去回测/验证再生成报告",
        )
    return ReportDetail.model_validate(report)


@router.post(
    "/factors/{factor_id}/report",
    response_model=ReportDetail,
    status_code=status.HTTP_201_CREATED,
    summary="为因子生成研究报告 (聚合最新回测 + 验证)",
)
def generate_report_for_factor(
    factor_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ReportDetail:
    try:
        report = research_service.generate_for_factor(db, current_user, uuid.UUID(factor_id))
    except (research_service.FactorNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在")
    except research_service.NoResearchYetError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="该因子还没有成功的回测或验证, 先去回测/验证再生成报告",
        )
    return ReportDetail.model_validate(report)


@router.get("/feed", response_model=list[ReportSummary], summary="研究 Feed (最新/高分 公开研究)")
def research_feed(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    sort: str = Query(default="latest", pattern="^(latest|top)$"),
    limit: int = Query(default=30, ge=1, le=50),
) -> list[ReportSummary]:
    return [ReportSummary(**r) for r in research_service.feed(db, sort, limit)]


@router.get("/reports", response_model=list[ReportSummary], summary="我的研究报告列表")
def my_reports(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[ReportSummary]:
    return [
        ReportSummary.model_validate(r)
        for r in research_service.list_my_reports(db, current_user.id)
    ]


@router.get("/reports/{report_id}", response_model=ReportDetail, summary="研究报告详情")
def report_detail(
    report_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ReportDetail:
    try:
        report = research_service.get_report(db, uuid.UUID(report_id))
    except ValueError:
        report = None
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告不存在")
    # 非本人只能看公开报告
    if report.owner_id != current_user.id and not report.is_public:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="该报告未公开")
    return ReportDetail.model_validate(report)


@router.post(
    "/reports/{report_id}/share",
    response_model=ShareOut,
    status_code=status.HTTP_201_CREATED,
    summary="生成研究分享卡片 (公开可转发 /share/{token})",
)
def share_report(
    report_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ShareOut:
    try:
        share = share_service.create_share(db, current_user, uuid.UUID(report_id))
    except (share_service.ReportNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告不存在")
    return ShareOut(
        token=share.token, share_path=f"/share/{share.token}", card=share.card, views=share.views
    )
