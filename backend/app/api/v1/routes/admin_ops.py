"""admin ops routes — PMF metrics, audit tail, readiness detail."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.v1.routes.admin_billing import require_admin
from backend.app.core.database import get_db
from backend.app.schemas.execution import ExecutionComplianceOut, GatewayRefreshOut
from backend.app.services import audit_service, execution_compliance_service as ecs, execution_alert_service as eas, health_service, ops_metrics_service, execution_service as exs

router = APIRouter()


@router.get("/metrics", summary="PMF / 运营指标 (X-Admin-Key)")
def ops_metrics(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin)],
    exclude_test: bool = True,
) -> dict:
    return ops_metrics_service.compute_pmf_metrics(db, exclude_test=exclude_test)


@router.get("/health", summary="就绪探针详情 (X-Admin-Key)")
def ops_health(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin)],
) -> dict:
    return health_service.readiness(db)


@router.get("/audit", summary="最近审计事件 (X-Admin-Key)")
def ops_audit(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin)],
    limit: int = 50,
    action_prefix: str | None = None,
) -> list[dict]:
    rows = audit_service.list_recent(db, limit=limit, action_prefix=action_prefix)
    return [
        {
            "id": str(r.id),
            "actor_id": str(r.actor_id) if r.actor_id else None,
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "detail": r.detail,
            "ip": r.ip,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/execution/health", summary="执行网关健康 (X-Admin-Key)")
def ops_execution_health(
    _: Annotated[None, Depends(require_admin)],
) -> dict:
    from engine.execution_adapter import gateway_health_summary

    return {"gateways": gateway_health_summary()}


@router.post("/execution/sync", response_model=GatewayRefreshOut, summary="全站网关订单同步 (X-Admin-Key)")
def ops_execution_sync(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin)],
    limit: int = 50,
) -> GatewayRefreshOut:
    result = exs.sync_all_pending_gateway_orders(db, limit=limit)
    audit_service.log(
        db,
        actor_id=None,
        action="admin.execution.sync",
        resource_type="execution",
        resource_id="global",
        detail=result,
    )
    return GatewayRefreshOut(**result)


@router.get("/execution/compliance", response_model=ExecutionComplianceOut, summary="执行合规与 SLA 报表 (X-Admin-Key)")
def ops_execution_compliance(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin)],
    stale_limit: int = 50,
) -> ExecutionComplianceOut:
    return ExecutionComplianceOut(**ecs.build_global_compliance_report(db, stale_limit=stale_limit))


@router.post("/execution/alerts/dispatch", summary="推送 SLA 告警 Webhook (X-Admin-Key)")
def ops_execution_alerts_dispatch(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(require_admin)],
    force: bool = False,
) -> dict:
    result = eas.dispatch_sla_webhook(db, force=force)
    if result.get("sent", 0) > 0:
        audit_service.log(
            db,
            actor_id=None,
            action="admin.execution.alerts.dispatch",
            resource_type="execution",
            resource_id="global",
            detail=result,
        )
    return result
