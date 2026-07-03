"""admin ops routes — PMF metrics, audit tail, readiness detail."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.v1.routes.admin_billing import require_admin
from backend.app.core.database import get_db
from backend.app.services import audit_service, health_service, ops_metrics_service

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
) -> list[dict]:
    rows = audit_service.list_recent(db, limit=limit)
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
