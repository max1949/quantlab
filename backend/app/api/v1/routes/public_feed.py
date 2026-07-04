"""公开研究广场 (免登录): 仅展示 is_public 的报告。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.research import ReportDetail, ReportSummary
from backend.app.services import research_service

router = APIRouter()


@router.get("/feed", response_model=list[ReportSummary], summary="研究广场 (免登录)")
def public_research_feed(
    db: Annotated[Session, Depends(get_db)],
    sort: str = Query(default="latest", pattern="^(latest|top)$"),
    limit: int = Query(default=30, ge=1, le=50),
    graduated_only: bool = Query(default=False, description="仅展示 Paper 毕业研究"),
) -> list[ReportSummary]:
    return [
        ReportSummary(**r)
        for r in research_service.feed(db, sort, limit, graduated_only=graduated_only)
    ]


@router.get(
    "/reports/{report_id}",
    response_model=ReportDetail,
    summary="公开研究报告详情 (仅 is_public)",
)
def public_report_detail(
    report_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> ReportDetail:
    from fastapi import HTTPException, status
    import uuid

    try:
        report = research_service.get_report(db, uuid.UUID(report_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告不存在")
    if report is None or not report.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报告不存在或未公开")
    return ReportDetail.model_validate(report)
