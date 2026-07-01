"""公开研究广场 (免登录): 仅展示 is_public 的报告。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.research import ReportSummary
from backend.app.services import research_service

router = APIRouter()


@router.get("/feed", response_model=list[ReportSummary], summary="研究广场 (免登录)")
def public_research_feed(
    db: Annotated[Session, Depends(get_db)],
    sort: str = Query(default="latest", pattern="^(latest|top)$"),
    limit: int = Query(default=30, ge=1, le=50),
) -> list[ReportSummary]:
    return [ReportSummary(**r) for r in research_service.feed(db, sort, limit)]
