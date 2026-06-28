"""公开 (免登录) 路由 (Sprint 9A): 研究分享卡片 /share/{token}。

无需鉴权 -> 分享链接可直接转发到社群/朋友圈, 驱动获取闭环。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.growth import ShareCardOut
from backend.app.services import share_service

router = APIRouter()


@router.get("/{token}", response_model=ShareCardOut, summary="公开研究分享卡片 (免登录)")
def share_card(
    token: str,
    db: Annotated[Session, Depends(get_db)],
) -> ShareCardOut:
    try:
        share = share_service.get_share(db, token)
    except share_service.ShareNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分享不存在或已失效")
    return ShareCardOut(
        token=share.token, card=share.card, views=share.views, created_at=share.created_at
    )
