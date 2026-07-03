"""研究机构 / 团队因子库路由。"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.schemas.membership import CheckoutIn, CheckoutOut
from backend.app.schemas.organization import (
    OrgActivityOut,
    OrgBillingOut,
    OrgBillingRedeemIn,
    OrgBillingRedeemOut,
    OrgBillingLedgerOut,
    OrgCreate,
    OrgFactorShareIn,
    OrgFactorShareOut,
    OrgInviteCreate,
    OrgInviteListOut,
    OrgInviteOut,
    OrgInvitePreviewOut,
    OrgMemberAdd,
    OrgMemberOut,
    OrgMemberUpdate,
    OrgOut,
    OrgAlertWebhookIn,
    OrgAlertWebhookOut,
    OrgSsoDomainsIn,
    OrgSsoDomainsOut,
)
from backend.app.schemas.execution import ExecutionComplianceOut, GatewayRefreshOut, OrgPaperOrderOut, SlaAlertDeliveryOut
from backend.app.services import audit_service, execution_compliance_service as ecs, execution_alert_service as eas, execution_service as exs, org_billing_service, org_service
from backend.app.services import billing_ledger_service as bls

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


@router.get(
    "/invites/{token}",
    response_model=OrgInvitePreviewOut,
    summary="预览机构邀请",
)
def preview_invite(
    token: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgInvitePreviewOut:
    try:
        return OrgInvitePreviewOut(
            **org_service.preview_invite(db, token, current_user.id)
        )
    except org_service.OrgInviteInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/invites/{token}/accept",
    response_model=OrgOut,
    summary="接受机构邀请",
)
def accept_invite(
    token: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgOut:
    try:
        out = org_service.accept_invite(db, token, current_user.id)
        audit_service.log(
            db,
            actor_id=current_user.id,
            action="org.invite.accept",
            resource_type="org",
            resource_id=out["id"],
            detail={"role": out["my_role"]},
        )
        return OrgOut(**out)
    except org_service.OrgInviteInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except org_billing_service.OrgSeatLimitError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except org_service.OrgEmailDomainError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


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


@router.post(
    "/{org_id}/invites",
    response_model=OrgInviteOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建机构邀请链接 (管理员)",
)
def create_invite(
    org_id: str,
    payload: OrgInviteCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgInviteOut:
    try:
        out = org_service.create_invite(
            db,
            uuid.UUID(org_id),
            current_user.id,
            role=payload.role,
            expires_in_days=payload.expires_in_days,
            max_uses=payload.max_uses,
        )
        audit_service.log(
            db,
            actor_id=current_user.id,
            action="org.invite.create",
            resource_type="org",
            resource_id=org_id,
            detail={
                "role": payload.role,
                "expires_in_days": payload.expires_in_days,
                "max_uses": payload.max_uses,
            },
        )
        return OrgInviteOut(**out)
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


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


@router.patch(
    "/{org_id}/members/{user_id}",
    response_model=OrgMemberOut,
    summary="更新成员角色 (管理员)",
)
def update_member_role(
    org_id: str,
    user_id: str,
    payload: OrgMemberUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgMemberOut:
    try:
        org_service.update_member_role(
            db,
            uuid.UUID(org_id),
            current_user.id,
            uuid.UUID(user_id),
            payload.role,
        )
        rows = org_service.list_members(db, uuid.UUID(org_id), current_user.id)
        match = next((m for m in rows if str(m["user_id"]) == user_id), None)
        audit_service.log(
            db,
            actor_id=current_user.id,
            action="org.member.role",
            resource_type="org",
            resource_id=org_id,
            detail={"user_id": user_id, "role": payload.role},
        )
        if match:
            return OrgMemberOut(**match)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except org_service.OrgMemberNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")


@router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="移除成员或自行退出",
)
def remove_member(
    org_id: str,
    user_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        org_service.remove_member(
            db, uuid.UUID(org_id), current_user.id, uuid.UUID(user_id)
        )
        audit_service.log(
            db,
            actor_id=current_user.id,
            action="org.member.remove",
            resource_type="org",
            resource_id=org_id,
            detail={"user_id": user_id},
        )
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{org_id}/invites",
    response_model=list[OrgInviteListOut],
    summary="机构邀请列表 (管理员)",
)
def list_invites(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[OrgInviteListOut]:
    try:
        return [OrgInviteListOut(**row) for row in org_service.list_invites(db, uuid.UUID(org_id), current_user.id)]
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.delete(
    "/{org_id}/invites/{invite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="撤销邀请 (管理员)",
)
def revoke_invite(
    org_id: str,
    invite_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        org_service.revoke_invite(
            db, uuid.UUID(org_id), current_user.id, uuid.UUID(invite_id)
        )
        audit_service.log(
            db,
            actor_id=current_user.id,
            action="org.invite.revoke",
            resource_type="org",
            resource_id=org_id,
            detail={"invite_id": invite_id},
        )
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{org_id}/activity",
    response_model=list[OrgActivityOut],
    summary="机构活动审计",
)
def org_activity(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
) -> list[OrgActivityOut]:
    try:
        rows = org_service.org_activity(db, uuid.UUID(org_id), current_user.id, limit=limit)
    except org_service.OrgAccessDeniedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该机构")
    return [OrgActivityOut(**r) for r in rows]


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
    except org_billing_service.OrgSeatLimitError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except org_service.OrgEmailDomainError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


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


@router.get("/{org_id}/billing", response_model=OrgBillingOut, summary="机构团队订阅状态")
def org_billing_status(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgBillingOut:
    try:
        return OrgBillingOut(**org_billing_service.get_org_billing(db, uuid.UUID(org_id), current_user.id))
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get(
    "/{org_id}/billing/history",
    response_model=list[OrgBillingLedgerOut],
    summary="机构计费流水 (管理员)",
)
def org_billing_history(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
) -> list[OrgBillingLedgerOut]:
    try:
        rows = bls.list_org_billing_history(db, uuid.UUID(org_id), current_user.id, limit=limit)
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return [OrgBillingLedgerOut(**r) for r in rows]


@router.get(
    "/{org_id}/billing/history/export",
    summary="导出机构计费流水 CSV (管理员)",
)
def org_billing_history_export(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 500,
) -> Response:
    try:
        csv_text = bls.export_org_billing_csv(
            db, uuid.UUID(org_id), current_user.id, limit=limit
        )
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return Response(
        content="\ufeff" + csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="org-{org_id}-billing.csv"'},
    )


@router.get(
    "/{org_id}/billing/history/{ledger_id}/invoice.pdf",
    summary="下载机构计费凭证 PDF (管理员)",
)
def org_billing_invoice_pdf(
    org_id: str,
    ledger_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        row = bls.get_org_ledger_entry(
            db, uuid.UUID(org_id), current_user.id, uuid.UUID(ledger_id)
        )
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="计费流水不存在")
    return Response(
        content=bls.render_invoice_pdf(row),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="org-{org_id}-billing-{ledger_id}.pdf"'},
    )


@router.post("/{org_id}/billing/checkout", response_model=CheckoutOut, summary="机构团队套餐下单")
def org_billing_checkout(
    org_id: str,
    payload: CheckoutIn,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CheckoutOut:
    try:
        result = org_billing_service.start_org_checkout(
            db, uuid.UUID(org_id), current_user.id, payload.plan_code
        )
    except org_billing_service.OrgBillingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return CheckoutOut(**result)


@router.post("/{org_id}/billing/redeem", response_model=OrgBillingRedeemOut, summary="机构团队兑换码")
def org_billing_redeem(
    org_id: str,
    payload: OrgBillingRedeemIn,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgBillingRedeemOut:
    from backend.app.services import membership_service as ms

    try:
        sub = org_billing_service.redeem_org_code(
            db, uuid.UUID(org_id), current_user.id, payload.code
        )
    except org_billing_service.OrgBillingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    audit_service.log(
        db,
        actor_id=current_user.id,
        action="org.billing.redeem",
        resource_type="org",
        resource_id=org_id,
        detail={"plan_code": sub.plan_code, "tier": sub.tier, "seats": sub.seats},
    )
    return OrgBillingRedeemOut(
        ok=True,
        tier=sub.tier,
        tier_name=ms.TIER_NAMES.get(sub.tier, "免费"),
        expires_at=sub.expires_at,
        seats=sub.seats,
        message=f"机构已开通「{ms.TIER_NAMES.get(sub.tier, '免费')}」团队套餐",
    )


@router.get(
    "/{org_id}/sso-domains",
    response_model=OrgSsoDomainsOut,
    summary="机构 SSO 邮箱域 (管理员可读)",
)
def get_org_sso_domains(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgSsoDomainsOut:
    try:
        domains = org_service.get_sso_domains(db, uuid.UUID(org_id), current_user.id)
    except org_service.OrgNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="机构不存在")
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return OrgSsoDomainsOut(domains=domains)


@router.put(
    "/{org_id}/sso-domains",
    response_model=OrgSsoDomainsOut,
    summary="配置机构 SSO 邮箱域 (仅所有者)",
)
def set_org_sso_domains(
    org_id: str,
    payload: OrgSsoDomainsIn,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgSsoDomainsOut:
    try:
        domains = org_service.set_sso_domains(
            db, uuid.UUID(org_id), current_user.id, payload.domains
        )
        audit_service.log(
            db,
            actor_id=current_user.id,
            action="org.sso.domains",
            resource_type="org",
            resource_id=org_id,
            detail={"domains": domains},
        )
    except org_service.OrgNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="机构不存在")
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return OrgSsoDomainsOut(domains=domains)


@router.get(
    "/{org_id}/execution/orders",
    response_model=list[OrgPaperOrderOut],
    summary="机构团队执行订单 (管理员)",
)
def list_org_execution_orders(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
) -> list[OrgPaperOrderOut]:
    try:
        rows = exs.list_org_execution_orders(db, uuid.UUID(org_id), current_user.id, limit=limit)
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return [OrgPaperOrderOut(**r) for r in rows]


@router.post(
    "/{org_id}/execution/refresh",
    response_model=GatewayRefreshOut,
    summary="批量轮询机构待成交网关订单",
)
def refresh_org_execution_orders(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = 30,
) -> GatewayRefreshOut:
    try:
        result = exs.refresh_org_gateway_orders(
            db, uuid.UUID(org_id), current_user.id, limit=limit
        )
        audit_service.log(
            db,
            actor_id=current_user.id,
            action="org.execution.refresh",
            resource_type="org",
            resource_id=org_id,
            detail=result,
        )
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return GatewayRefreshOut(**result)


@router.get(
    "/{org_id}/execution/compliance",
    response_model=ExecutionComplianceOut,
    summary="机构执行合规与 SLA 报表 (管理员)",
)
def org_execution_compliance(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    stale_limit: int = 30,
) -> ExecutionComplianceOut:
    try:
        report = ecs.build_org_compliance_report(
            db, uuid.UUID(org_id), current_user.id, stale_limit=stale_limit
        )
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return ExecutionComplianceOut(**report)


@router.get(
    "/{org_id}/execution/alert-webhook",
    response_model=OrgAlertWebhookOut,
    summary="机构 SLA 告警 Webhook (管理员)",
)
def get_org_alert_webhook(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgAlertWebhookOut:
    try:
        data = org_service.get_alert_webhook(db, uuid.UUID(org_id), current_user.id)
    except org_service.OrgNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="机构不存在")
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return OrgAlertWebhookOut(**data)


@router.put(
    "/{org_id}/execution/alert-webhook",
    response_model=OrgAlertWebhookOut,
    summary="配置机构 SLA 告警 Webhook (管理员)",
)
def set_org_alert_webhook(
    org_id: str,
    payload: OrgAlertWebhookIn,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OrgAlertWebhookOut:
    try:
        data = org_service.set_alert_webhook(
            db,
            uuid.UUID(org_id),
            current_user.id,
            payload.webhook_url,
            payload.webhook_secret,
        )
        audit_service.log(
            db,
            actor_id=current_user.id,
            action="org.execution.alert_webhook",
            resource_type="org",
            resource_id=org_id,
            detail={
                "configured": bool(data["webhook_url"]),
                "secret_configured": bool(data["secret_configured"]),
            },
        )
    except org_service.OrgNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="机构不存在")
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return OrgAlertWebhookOut(**data)


@router.post(
    "/{org_id}/execution/alerts/dispatch",
    summary="推送机构 SLA 告警 Webhook (管理员)",
)
def org_execution_alerts_dispatch(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    force: bool = False,
) -> dict:
    try:
        result = eas.dispatch_org_sla_webhook(
            db, uuid.UUID(org_id), actor_id=current_user.id, force=force
        )
        if result.get("sent", 0) > 0 or result.get("failed"):
            audit_service.log(
                db,
                actor_id=current_user.id,
                action="org.execution.alerts.dispatch",
                resource_type="org",
                resource_id=org_id,
                detail=result,
            )
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return result


@router.get(
    "/{org_id}/execution/alert-deliveries",
    response_model=list[SlaAlertDeliveryOut],
    summary="机构 SLA 告警投递审计 (管理员)",
)
def org_execution_alert_deliveries(
    org_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    status: str | None = None,
    limit: int = 30,
) -> list[SlaAlertDeliveryOut]:
    try:
        org_service.require_admin(db, uuid.UUID(org_id), current_user.id)
        rows = eas.list_deliveries(
            db, scope="org", org_id=uuid.UUID(org_id), status=status, limit=limit
        )
    except org_service.OrgAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return [SlaAlertDeliveryOut(**r) for r in rows]
