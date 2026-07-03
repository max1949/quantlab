"""模拟执行 / 纸面下单路由 (机构级执行适配)。"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import require_feature
from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.execution import (
    ExecutionConfigOut,
    GatewayHealthOut,
    GatewayRefreshOut,
    GatewayWebhookIn,
    OrgPaperOrderOut,
    PaperOrderCreate,
    PaperOrderEventOut,
    PaperOrderOut,
    RiskCheckIn,
    RiskCheckOut,
)
from backend.app.services import audit_service, execution_service as exs
from engine.execution_adapter import execution_config_payload, gateway_health_summary, verify_gateway_webhook

router = APIRouter()


@router.get("/config", response_model=ExecutionConfigOut, summary="执行通道与风控配置")
def execution_config(
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
) -> ExecutionConfigOut:
    return ExecutionConfigOut(**execution_config_payload())


@router.get("/gateway-health", response_model=GatewayHealthOut, summary="执行网关健康探针")
def execution_gateway_health(
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
) -> GatewayHealthOut:
    return GatewayHealthOut(gateways=gateway_health_summary())


@router.post("/risk-check", response_model=RiskCheckOut, summary="下单前风控预检")
def risk_check(
    payload: RiskCheckIn,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> RiskCheckOut:
    return RiskCheckOut(
        **exs.risk_check_preview(
            db,
            current_user,
            symbol=payload.symbol,
            notional_cny=payload.notional_cny,
            channel=payload.channel,
            factor_id=payload.factor_id,
            acknowledge_risk=payload.acknowledge_risk,
        )
    )


@router.post(
    "/paper/orders",
    response_model=PaperOrderOut,
    status_code=status.HTTP_201_CREATED,
    summary="提交模拟/网关订单 (需专业月卡)",
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
            channel=payload.channel,
            acknowledge_risk=payload.acknowledge_risk,
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
            "channel": order.channel,
            "external_ref": order.external_ref,
            "regime": order.regime,
            "regime_fit_score": order.regime_fit_score,
        },
    )
    return PaperOrderOut(**exs.order_to_dict(order))


@router.post(
    "/paper/orders/{order_id}/route-vnpy",
    response_model=PaperOrderOut,
    summary="将纸面订单路由到 vn.py 网关",
)
def route_order_vnpy(
    order_id: str,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperOrderOut:
    try:
        order = exs.route_existing_to_vnpy(db, current_user.id, uuid.UUID(order_id))
    except exs.ExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    audit_service.log(
        db,
        actor_id=current_user.id,
        action="execution.vnpy.route",
        resource_type="paper_order",
        resource_id=str(order.id),
        detail={"external_ref": order.external_ref},
    )
    return PaperOrderOut(**exs.order_to_dict(order))


@router.post(
    "/paper/orders/{order_id}/route-qmt",
    response_model=PaperOrderOut,
    summary="将纸面订单路由到 QMT 网关",
)
def route_order_qmt(
    order_id: str,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperOrderOut:
    try:
        order = exs.route_existing_to_qmt(db, current_user.id, uuid.UUID(order_id))
    except exs.ExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    audit_service.log(
        db,
        actor_id=current_user.id,
        action="execution.qmt.route",
        resource_type="paper_order",
        resource_id=str(order.id),
        detail={"external_ref": order.external_ref},
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


@router.get(
    "/paper/orders/{order_id}/events",
    response_model=list[PaperOrderEventOut],
    summary="订单状态事件时间线",
)
def list_order_events(
    order_id: str,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> list[PaperOrderEventOut]:
    rows = exs.list_order_events(db, current_user.id, uuid.UUID(order_id))
    if not rows and exs.get_paper_order(db, current_user.id, uuid.UUID(order_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    return [PaperOrderEventOut(**exs.event_to_dict(r)) for r in rows]


@router.post(
    "/paper/orders/{order_id}/refresh",
    response_model=PaperOrderOut,
    summary="从网关轮询并刷新订单状态",
)
def refresh_paper_order(
    order_id: str,
    current_user: Annotated[User, Depends(require_feature("paper_trading"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaperOrderOut:
    try:
        order = exs.refresh_order_from_gateway(db, current_user.id, uuid.UUID(order_id))
    except exs.ExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    audit_service.log(
        db,
        actor_id=current_user.id,
        action="execution.gateway.poll",
        resource_type="paper_order",
        resource_id=str(order.id),
        detail={"status": order.status, "gateway_status": order.gateway_status},
    )
    return PaperOrderOut(**exs.order_to_dict(order))


@router.post("/webhook/gateway", summary="执行网关状态回调", include_in_schema=False)
async def gateway_webhook(
    payload: GatewayWebhookIn,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    x_gateway_signature: Annotated[str | None, Header(alias="X-Gateway-Signature")] = None,
) -> dict:
    settings = get_settings()
    secret = settings.execution_webhook_secret.strip()
    body = await request.body()
    if not secret or not verify_gateway_webhook(body, x_gateway_signature or "", secret):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid signature")

    order = exs.apply_gateway_status(
        db, external_ref=payload.external_ref, gateway_status=payload.status
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    audit_service.log(
        db,
        actor_id=None,
        action="execution.gateway.status",
        resource_type="paper_order",
        resource_id=str(order.id),
        detail={
            "external_ref": payload.external_ref,
            "status": payload.status,
            "channel": order.channel,
        },
    )
    return {"ok": True, "order_id": str(order.id), "status": order.status}
