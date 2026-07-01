"""BK-GTA 统一卡密池 (Supabase, 与 ai.ziyingke.com 共用)。

师父在 ai 后台生成卡密 (BKTA-XXXX-XXXX), 用户可在 QuantLab 核销开通会员。
核销后更新 membership_cards, 写入 membership_redemptions (含师父归因)。
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models.user import User
from backend.app.services.membership_service import (
    RedeemError,
    TIER_PLUS,
    TIER_PRO,
    grant,
)

QUANTLAB_PLAN_MAP: dict[str, tuple[int, str]] = {
    "quantlab_plus_monthly": (TIER_PLUS, "plus_monthly"),
    "quantlab_pro_monthly": (TIER_PRO, "pro_monthly"),
}

AI_PLAN_PREFIXES = ("trainee_", "coach_")


def is_bkta_code(raw: str) -> bool:
    n = re.sub(r"[\s-]+", "", (raw or "").strip().upper())
    return n.startswith("BKTA") and len(n) >= 12


def normalize_card_code(raw: str) -> str:
    n = re.sub(r"[\s-]+", "", (raw or "").strip().upper())
    if not n.startswith("BKTA"):
        return (raw or "").strip().upper()
    body = n[4:]
    if len(body) >= 8:
        return f"BKTA-{body[:4]}-{body[4:8]}"
    return (raw or "").strip().upper()


def _pool_configured() -> bool:
    s = get_settings()
    return bool(s.card_pool_supabase_url and s.card_pool_service_key)


def _headers() -> dict[str, str]:
    key = get_settings().card_pool_service_key
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _base_url() -> str:
    return get_settings().card_pool_supabase_url.rstrip("/")


def redeem_bkta_card(db: Session, user: User, raw_code: str):
    """核销 BKTA 卡密; 成功返回 Subscription, 非 BKTA 格式返回 None。"""
    if not is_bkta_code(raw_code):
        return None
    if not _pool_configured():
        raise RedeemError("卡密服务未配置，请联系管理员")

    code = normalize_card_code(raw_code)
    base = _base_url()
    headers = _headers()

    with httpx.Client(timeout=20.0) as client:
        resp = client.get(
            f"{base}/rest/v1/membership_cards",
            params={"code": f"eq.{code}", "select": "*"},
            headers=headers,
        )
        if resp.status_code >= 400:
            raise RedeemError("卡密服务暂时不可用，请稍后再试")
        rows = resp.json()
        if not rows:
            raise RedeemError("卡密不存在，请核对后重试")
        card = rows[0]

        status = card.get("status")
        if status == "revoked":
            raise RedeemError("该卡密已作废")
        if status == "redeemed":
            raise RedeemError("该卡密已被使用")

        plan = str(card.get("plan") or "")
        if plan.startswith(AI_PLAN_PREFIXES) or plan in {
            "trainee_monthly",
            "coach_monthly",
        }:
            raise RedeemError(
                "此卡密用于决策挑战场，请前往 https://ai.ziyingke.com 兑换"
            )
        mapped = QUANTLAB_PLAN_MAP.get(plan)
        if mapped is None:
            raise RedeemError("卡密产品类型无效，请联系发卡方")

        tier, plan_code = mapped
        months = max(1, int(card.get("months") or 1))
        period_days = months * 30
        now = datetime.now(timezone.utc).isoformat()
        external_ref = f"quantlab:{user.username}"

        patch = client.patch(
            f"{base}/rest/v1/membership_cards",
            params={"code": f"eq.{code}", "status": "eq.unused"},
            headers={**headers, "Prefer": "return=representation"},
            json={
                "status": "redeemed",
                "redeemed_at": now,
                "note": external_ref,
            },
        )
        if patch.status_code >= 400 or not patch.json():
            raise RedeemError("卡密核销失败，可能已被使用，请重试")

        expires_at = (datetime.now(timezone.utc) + timedelta(days=period_days)).isoformat()
        redemption = {
            "card_id": card["id"],
            "plan": plan,
            "months": months,
            "expires_at": expires_at,
            "source_invite_code": card.get("source_invite_code"),
            "external_user_ref": external_ref,
        }
        try:
            client.post(
                f"{base}/rest/v1/membership_redemptions",
                headers=headers,
                json=redemption,
            )
        except httpx.HTTPError:
            pass

    return grant(db, user, tier, period_days, plan_code, source="card")


def pool_status() -> dict:
    configured = _pool_configured()
    return {
        "enabled": configured,
        "code_format": "BKTA-XXXX-XXXX",
        "purchase_hint": "向师父购买卡密兑换会员（与决策挑战场同一发卡体系）",
    }
