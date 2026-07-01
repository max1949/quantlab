"""公开研究广场 (免登录): 仅展示 is_public 的报告。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.research import ReportSummary
from backend.app.services import research_service

router = APIRouter()


@router.get("/feed", response_model=list[ReportSummary], summary="研究广场 (免登录)")
def public_research_feed(
    db: Annotated[Session, Depends(get_db)],
    sort: str = "latest",
    limit: int = 30,
) -> list[ReportSummary]:
    return [ReportSummary.model_validate(r) for r in research_service.feed(db, sort, limit)]
