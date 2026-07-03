"""研究机构 / 团队因子库路由。"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.schemas.organization import (
    OrgCreate,
    OrgFactorShareIn,
    OrgFactorShareOut,
    OrgMemberAdd,
    OrgMemberOut,
    OrgOut,
)
from backend.app.services import audit_service, org_service

router = APIRouter()


@router.post("", response_model=OrgOut, status_code=status.HTTP_201_CREATED, summary="创建研究机构")
def create_org(
    payload: OrgCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgOut:
    out = org_service.create_org(db, current_user, payload.name)
    audit_service.log(
        db,
        actor_id=current_user.id,
        action="org.create",
        resource_type="org",
        resource_id=out["id"],
        detail={"name": payload.name, "slug": out["slug"]},
    )
    return OrgOut(**out)


@router.get("", response_model=list[OrgOut], summary="我的研究机构")
def list_my_orgs(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[OrgOut]:
    return [OrgOut(**o) for o in org_service.list_orgs_for_user(db, current_user.id)]


@router.get("/{org_id}", response_model=OrgOut, summary="机构详情")
def get_org(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgOut:
    try:
        out = org_service.get_org(db, uuid.UUID(org_id), current_user.id)
    except org_service.OrgNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="机构不存在")
    except org_service.OrgAccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该机构")
    return OrgOut(**out)


@router.get("/{org_id}/members", response_model=list[OrgMemberOut], summary="机构成员")
def list_members(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[OrgMemberOut]:
    try:
        rows = org_service.list_members(db, uuid.UUID(org_id), current_user.id)
    except org_service.OrgAccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该机构")
    return [OrgMemberOut(**r) for r in rows]


@router.post("/{org_id}/members", response_model=OrgMemberOut, summary="添加成员 (管理员)")
def add_member(
    org_id: str,
    payload: OrgMemberAdd,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgMemberOut:
    try:
        row = org_service.add_member(
            db, uuid.UUID(org_id), current_user.id, payload.username, payload.role
        )
        user_row = org_service.list_members(db, uuid.UUID(org_id), current_user.id)
        match = next((m for m in user_row if m["user_id"] == row.user_id), None)
        audit_service.log(
            db,
            actor_id=current_user.id,
            action="org.member.add",
            resource_type="org",
            resource_id=org_id,
            detail={"username": payload.username, "role": payload.role},
        )
        return OrgMemberOut(**match) if match else OrgMemberOut(
            user_id=row.user_id, username=payload.username, role=row.role, joined_at=row.created_at
        )
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except org_service.OrgMemberNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")


@router.get("/{org_id}/factors", response_model=list[OrgFactorShareOut], summary="已共享因子")
def list_shared_factors(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[OrgFactorShareOut]:
    try:
        rows = org_service.list_shared_factors(db, uuid.UUID(org_id), current_user.id)
    except org_service.OrgAccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该机构")
    return [OrgFactorShareOut(**r) for r in rows]


@router.post(
    "/{org_id}/factors/{factor_id}/share",
    response_model=OrgFactorShareOut,
    summary="共享因子到机构库",
)
def share_factor(
    org_id: str,
    factor_id: str,
    payload: OrgFactorShareIn,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgFactorShareOut:
    try:
        org_service.share_factor(
            db, uuid.UUID(org_id), current_user.id, uuid.UUID(factor_id), note=payload.note
        )
        rows = org_service.list_shared_factors(db, uuid.UUID(org_id), current_user.id)
        match = next((r for r in rows if str(r["factor_id"]) == factor_id), None)
        audit_service.log(
            db,
            actor_id=current_user.id,
            action="org.factor.share",
            resource_type="factor",
            resource_id=factor_id,
            detail={"org_id": org_id, "note": payload.note},
        )
        if match:
            return OrgFactorShareOut(**match)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="共享失败")
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.delete("/{org_id}/factors/{factor_id}/share", status_code=status.HTTP_204_NO_CONTENT, summary="取消共享")
def unshare_factor(
    org_id: str,
    factor_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        org_service.unshare_factor(db, uuid.UUID(org_id), current_user.id, uuid.UUID(factor_id))
        audit_service.log(
            db,
            actor_id=current_user.id,
            action="org.factor.unshare",
            resource_type="factor",
            resource_id=factor_id,
            detail={"org_id": org_id},
        )
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{org_id}/catalog", summary="机构因子资产库 (冗余扫描)")
def org_catalog(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    symbol: str | None = None,
    timeframe: str = "1d",
) -> dict:
    try:
        return org_service.org_catalog(
            db, uuid.UUID(org_id), current_user.id, symbol=symbol, timeframe=timeframe
        )
    except org_service.OrgAccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该机构")
