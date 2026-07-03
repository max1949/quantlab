"""模拟执行 / 纸面下单路由 (机构级执行适配 v0)。"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import require_feature
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.execution import PaperOrderCreate, PaperOrderOut
from backend.app.services import audit_service, execution_service as exs

router = APIRouter()


@router.post(
    "/paper/orders",
    response_model=PaperOrderOut,
    status_code=status.HTTP_201_CREATED,
    summary="提交模拟订单 (需专业月卡)",
)
def create_paper_order(
    payload: PaperOrderCreate,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperOrderOut:
    try:
        order = exs.submit_paper_order(
            db,
            current_user,
            symbol=payload.symbol,
            side=payload.side,
            notional_cny=payload.notional_cny,
            factor_id=payload.factor_id,
            signal_value=payload.signal_value,
            note=payload.note,
        )
    except exs.ExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    audit_service.log(
        db,
        actor_id=current_user.id,
        action="execution.paper.submit",
        resource_type="paper_order",
        resource_id=str(order.id),
        detail={
            "symbol": order.symbol,
            "side": order.side,
            "notional_cny": float(order.notional_cny),
            "regime": order.regime,
            "regime_fit_score": order.regime_fit_score,
        },
    )
    return PaperOrderOut(**exs.order_to_dict(order))


@router.get("/paper/orders", response_model=list[PaperOrderOut], summary="我的模拟订单")
def list_paper_orders(
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
) -> list[PaperOrderOut]:
    rows = exs.list_paper_orders(db, current_user.id, limit=limit)
    return [PaperOrderOut(**exs.order_to_dict(r)) for r in rows]


@router.get("/paper/orders/{order_id}", response_model=PaperOrderOut, summary="模拟订单详情")
def get_paper_order(
    order_id: str,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperOrderOut:
    row = exs.get_paper_order(db, current_user.id, uuid.UUID(order_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    return PaperOrderOut(**exs.order_to_dict(row))
