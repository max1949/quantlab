"""埋点 + 增长漏斗路由 (Sprint 9A)。

POST /events 允许匿名 (访客 visit 事件); GET /funnel 需 L3 (运营视角)。
"""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import OptionalUser, require_level
from backend.app.core.database import get_db
from backend.app.core.request_ip import get_client_ip
from backend.app.models.user import User, UserLevel
from backend.app.schemas.growth import EventIn
from backend.app.services import growth_service, rate_limit

router = APIRouter()


@router.post("", status_code=204, summary="上报埋点事件 (允许匿名)")
def track(
    payload: EventIn,
    request: Request,
    current_user: OptionalUser,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        rate_limit.check_event(get_client_ip(request))
    except rate_limit.RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    if len(json.dumps(payload.props, ensure_ascii=False, default=str)) > 4096:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="埋点 payload 过大",
        )
    uid = current_user.id if current_user else None
    growth_service.log_event(db, payload.event, uid, payload.props)


@router.get("/funnel", summary="增长漏斗 (需 L3)")
def funnel(
    current_user: Annotated[User, Depends(require_level(UserLevel.L3))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return growth_service.funnel(db)
