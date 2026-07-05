"""会员 / 权益业务逻辑 (Sprint 10 商业化)。

两条闸门:
  - 等级 min_level: 靠做研究练出来 (能力)。
  - 档位 min_tier: 靠订阅解锁 (付费)。
功能可用 = user.level >= min_level 且 当前档位 >= min_tier。
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.membership import (
    RedeemCode,
    Subscription,
    SubscriptionStatus,
)
from backend.app.models.user import User, UserLevel


def frontend_origin() -> str:
    from backend.app.core.config import get_settings

    settings = get_settings()
    return (
        settings.frontend_base_url or settings.public_base_url or "http://localhost:5173"
    ).rstrip("/")


# --- 档位 ---
TIER_FREE = 0
TIER_PLUS = 1
TIER_PRO = 2

TIER_NAMES = {0: "免费", 1: "研究员", 2: "专业研究员"}

# --- 套餐目录 (展示用; 价格单位: 人民币元/月) ---
PLANS: list[dict] = [
    {
        "code": "free",
        "name": "免费",
        "tier": 0,
        "price_cny": 0,
        "period_days": 0,
        "tagline": "入门研究, 跑通第一次闭环",
        "features": [
            "模板因子 (5 种)",
            "因子参数扫描 (L1+)",
            "因子组合器",
            "历史回测 (日线 · 近1年)",
            "样本外 + Walk-Forward 验证",
            "自动研究报告",
            "研究广场 / 榜单 / 30天挑战",
        ],
    },
    {
        "code": "plus_monthly",
        "name": "研究员月卡",
        "tier": 1,
        "price_cny": 499,
        "period_days": 30,
        "tagline": "解锁自主研究: 公式因子 + 截面 + 进阶分析",
        "features": [
            "免费版全部功能",
            "公式因子 (自己写表达式)",
            "截面多标的回测",
            "分钟线回测 (近1年)",
            "5分钟 / 15分钟中频周期",
            "日线回测 (近2年)",
            "成本敏感性分析",
            "多因子正交化",
            "参数稳健性测试",
            "过拟合检查",
        ],
    },
    {
        "code": "pro_monthly",
        "name": "专业研究员月卡",
        "tier": 2,
        "price_cny": 2999,
        "period_days": 30,
        "tagline": "准职业工作流: 组合优化 + 全历史行情",
        "features": [
            "研究员卡全部功能",
            "全历史分钟线 / 日线 (vn.py 级深度)",
            "组合优化 (均值方差 / 风险平价)",
            "模拟实盘 paper trading",
            "优先支持",
        ],
    },
    {
        "code": "org_plus_monthly",
        "name": "团队研究员",
        "tier": 1,
        "price_cny": 1999,
        "period_days": 30,
        "kind": "org",
        "seats": 5,
        "tagline": "5 席位 · 全员解锁研究员工具档",
        "features": [
            "研究员月卡全部功能 (按席位)",
            "团队因子库与冗余扫描",
            "机构活动审计",
            "邀请链接入组",
        ],
    },
    {
        "code": "org_pro_monthly",
        "name": "团队专业版",
        "tier": 2,
        "price_cny": 9999,
        "period_days": 30,
        "kind": "org",
        "seats": 20,
        "tagline": "20 席位 · 准职业机构工作流",
        "features": [
            "团队研究员全部功能",
            "全历史行情 · 组合优化",
            "模拟实盘 (paper trading)",
            "优先支持",
        ],
    },
]

PLAN_BY_CODE = {p["code"]: p for p in PLANS}

# --- 功能权益注册表: key -> (能力等级, 付费档位) ---
FEATURES: dict[str, dict] = {
    "factor_template": {"label": "模板因子", "min_level": 0, "min_tier": 0},
    "factor_stack": {"label": "因子组合", "min_level": 1, "min_tier": 0},
    "factor_formula": {"label": "公式因子", "min_level": 2, "min_tier": 1},
    "factor_python": {"label": "Python 因子", "min_level": 3, "min_tier": 1},
    "backtest_cross_section": {"label": "截面多标的回测", "min_level": 2, "min_tier": 1},
    "cost_sensitivity": {"label": "成本敏感性分析", "min_level": 2, "min_tier": 1},
    "factor_orthogonalize": {"label": "多因子正交化", "min_level": 3, "min_tier": 1},
    "robustness_test": {"label": "参数稳健性测试", "min_level": 3, "min_tier": 1},
    "overfit_check": {"label": "过拟合检查", "min_level": 3, "min_tier": 1},
    "factor_param_scan": {"label": "因子参数扫描", "min_level": 1, "min_tier": 0},
    "portfolio_optimize": {"label": "组合优化", "min_level": 4, "min_tier": 2},
    "paper_trading": {"label": "模拟实盘", "min_level": 4, "min_tier": 2},
}


class RedeemError(Exception):
    """兑换码无效/已用。"""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _active_subscriptions(db: Session, user_id: uuid.UUID) -> list[Subscription]:
    now = _now()
    stmt = select(Subscription).where(
        Subscription.user_id == user_id,
        Subscription.status == SubscriptionStatus.ACTIVE.value,
    )
    subs = list(db.execute(stmt).scalars().all())
    return [
        s
        for s in subs
        if s.expires_at is None or _normalize_utc(s.expires_at) > now
    ]


def current_tier(db: Session, user: User) -> int:
    """当前付费档位 = max(个人订阅, 所属机构团队订阅)。"""
    from backend.app.services import org_billing_service as obs

    personal = max((s.tier for s in _active_subscriptions(db, user.id)), default=TIER_FREE)
    org = obs.org_tiers_for_user(db, user.id)
    return max(personal, org)


def get_status(db: Session, user: User) -> dict:
    from backend.app.services import org_billing_service as obs

    subs = _active_subscriptions(db, user.id)
    personal_tier = max((s.tier for s in subs), default=TIER_FREE)
    org_tier = obs.org_tiers_for_user(db, user.id)
    tier = max(personal_tier, org_tier)
    primary = None
    if subs:
        primary = sorted(
            subs, key=lambda s: (s.tier, s.expires_at or datetime.max.replace(tzinfo=timezone.utc))
        )[-1]
    return {
        "tier": tier,
        "tier_name": TIER_NAMES.get(tier, "免费"),
        "plan_code": primary.plan_code if primary else "free",
        "expires_at": primary.expires_at if primary else None,
        "is_paid": tier > 0,
        "personal_tier": personal_tier,
        "org_tier": org_tier,
        "org_benefit": org_tier > personal_tier,
    }


def feature_state(user_level: int, tier: int, key: str) -> dict:
    """单个功能对(等级,档位)的可用性判断。"""
    spec = FEATURES[key]
    need_level = spec["min_level"]
    need_tier = spec["min_tier"]
    level_ok = user_level >= need_level
    tier_ok = tier >= need_tier
    return {
        "key": key,
        "label": spec["label"],
        "allowed": level_ok and tier_ok,
        "level_ok": level_ok,
        "tier_ok": tier_ok,
        "min_level": need_level,
        "min_level_name": UserLevel(need_level).label,
        "min_tier": need_tier,
        "min_tier_name": TIER_NAMES.get(need_tier, "免费"),
    }


def entitlements(db: Session, user: User) -> dict:
    from backend.app.services import market_data_policy as mdp

    tier = current_tier(db, user)
    feats = [feature_state(user.level, tier, k) for k in FEATURES]
    return {
        "level": user.level,
        "level_name": UserLevel(user.level).label,
        "tier": tier,
        "tier_name": TIER_NAMES.get(tier, "免费"),
        "features": feats,
        "market_data": mdp.entitlement_payload(db, user),
    }


def can_use(db: Session, user: User, key: str) -> dict:
    return feature_state(user.level, current_tier(db, user), key)


def grant(
    db: Session,
    user: User,
    tier: int,
    period_days: int,
    plan_code: str,
    source: str = "redeem",
    stripe_session_id: str | None = None,
) -> Subscription:
    expires = None if period_days <= 0 else _now() + timedelta(days=period_days)
    sub = Subscription(
        user_id=user.id,
        plan_code=plan_code,
        tier=tier,
        status=SubscriptionStatus.ACTIVE.value,
        source=source,
        expires_at=expires,
        stripe_session_id=stripe_session_id,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    from backend.app.services import billing_ledger_service as bls

    bls.record_personal_subscription(
        db,
        user_id=user.id,
        plan_code=plan_code,
        tier=tier,
        source=source,
        subscription_id=sub.id,
        expires_at=sub.expires_at,
        stripe_session_id=stripe_session_id,
    )
    return sub


def redeem(db: Session, user: User, code: str) -> Subscription:
    code = (code or "").strip()
    if not code:
        raise RedeemError("兑换码不能为空")

    from backend.app.services import card_pool_service

    if card_pool_service.is_bkta_code(code):
        sub = card_pool_service.redeem_bkta_card(db, user, code)
        if sub is not None:
            return sub

    normalized = code.upper()
    rc = db.execute(
        select(RedeemCode).where(RedeemCode.code == normalized)
    ).scalar_one_or_none()
    if rc is None:
        if card_pool_service.is_bkta_code(code):
            raise RedeemError("卡密不存在，请核对后重试")
        raise RedeemError("兑换码无效")
    if rc.used_by is not None:
        raise RedeemError("兑换码已被使用")
    rc.used_by = user.id
    rc.used_at = _now()
    db.add(rc)
    sub = grant(db, user, rc.tier, rc.period_days, rc.plan_code, source="redeem")
    return sub


def create_redeem_code(
    db: Session,
    tier: int = TIER_PLUS,
    period_days: int = 30,
    plan_code: str = "plus_monthly",
    note: str | None = None,
    *,
    kind: str = "personal",
    seats: int | None = None,
) -> RedeemCode:
    prefix = "QLT-" if kind == "org" else "QL-"
    code = prefix + secrets.token_hex(4).upper()
    rc = RedeemCode(
        code=code,
        tier=tier,
        period_days=period_days,
        plan_code=plan_code,
        note=note,
        kind=kind,
        seats=seats,
    )
    db.add(rc)
    db.commit()
    db.refresh(rc)
    return rc


def start_checkout(db: Session, user: User, plan_code: str) -> dict:
    """在线支付下单 — Stripe 已配置则返回 pay_url, 否则引导兑换码。"""
    from backend.app.core.config import get_settings
    from backend.app.services import payment_service

    plan = PLAN_BY_CODE.get(plan_code)
    if plan is None or plan["tier"] == 0:
        raise RedeemError("无效的套餐")
    if plan.get("kind") == "org":
        raise RedeemError("团队套餐请在机构详情页购买")

    base = {
        "plan_code": plan_code,
        "plan_name": plan["name"],
        "price_cny": plan["price_cny"],
        "pay_url": None,
        "org_id": None,
    }

    if not payment_service.stripe_configured():
        return {
            **base,
            "configured": False,
            "message": "请向师父购买卡密，在本页下方输入 BKTA-XXXX-XXXX 兑换开通。",
        }

    settings = get_settings()
    origin = frontend_origin()
    pay_url = payment_service.create_checkout_session(
        plan_name=plan["name"],
        price_cny=plan["price_cny"],
        metadata={
            "kind": "personal",
            "plan_code": plan_code,
            "user_id": str(user.id),
        },
        success_url=f"{origin}/app?checkout=success&plan={plan_code}",
        cancel_url=f"{origin}/pricing?checkout=cancel",
    )
    return {
        **base,
        "configured": True,
        "pay_url": pay_url,
        "message": "正在跳转支付…",
    }


def upgrade_coaching_payload(
    db: Session,
    user: User,
    locale: str,
    *,
    mastery_goal: dict,
    challenge_paper_coaching: dict | None = None,
) -> dict | None:
    """大师路径 Pro 升级教练 — Paper 模拟盘等需专业档时友好指引。"""
    from backend.app.core.locale import Locale
    from backend.app.i18n import content as i18n
    from backend.app.services import payment_service

    loc: Locale = "zh" if locale == "zh" else "en"
    tier = current_tier(db, user)
    if tier >= TIER_PRO:
        return None

    paper = feature_state(user.level, tier, "paper_trading")
    if paper["allowed"]:
        return None

    reason: str | None = None
    if mastery_goal.get("paper_ready"):
        reason = "paper_ready"
    elif mastery_goal.get("mastery_next_action") == "paper":
        reason = "mastery_paper"
    elif challenge_paper_coaching and challenge_paper_coaching.get("next_code") == "first_paper_order":
        reason = "challenge_d22"
    elif mastery_goal.get("mastery_next_action") in ("track", "graduate"):
        reason = "mastery_track"

    if not reason:
        return None

    labels = i18n.UPGRADE_COACH.get(loc) or i18n.UPGRADE_COACH["en"]
    plan = PLAN_BY_CODE["pro_monthly"]
    return {
        "current_tier": tier,
        "current_tier_name": TIER_NAMES.get(tier, "免费"),
        "target_tier": TIER_PRO,
        "target_tier_name": TIER_NAMES[TIER_PRO],
        "plan_code": "pro_monthly",
        "plan_name": plan["name"],
        "price_cny": plan["price_cny"],
        "reason": reason,
        "message": labels[reason],
        "cta_path": "/pricing",
        "stripe_available": payment_service.stripe_configured(),
        "unlock_features": labels["unlock_features"],
    }


def post_checkout_coaching_payload(
    db: Session,
    user: User,
    locale: str,
    plan_code: str | None,
    *,
    mastery_goal: dict,
    active_project_id: uuid.UUID | None,
    done_count: int = 0,
) -> dict | None:
    """支付成功回跳 — 解锁指引与大师路径下一步 (新手友好)。"""
    from backend.app.core.locale import Locale
    from backend.app.i18n import content as i18n
    from backend.app.services import billing_email_service as bes

    if not plan_code:
        return None
    plan = PLAN_BY_CODE.get(plan_code)
    if not plan or plan.get("kind") == "org" or plan["tier"] == 0:
        return None

    tier = current_tier(db, user)
    if plan["tier"] != tier:
        return None

    loc: Locale = "zh" if locale == "zh" else "en"
    labels = i18n.CHECKOUT_COACH.get(loc) or i18n.CHECKOUT_COACH["en"]
    next_act = mastery_goal.get("mastery_next_action")

    if tier == TIER_PRO:
        if mastery_goal.get("paper_ready"):
            reason, cta_action = "pro_paper_ready", "run_paper"
        elif next_act == "paper":
            reason, cta_action = "pro_start_paper", "run_paper"
        else:
            reason = "pro_welcome"
            cta_action = next_act or ("create_project" if done_count < 1 else "run_backtest")
    elif next_act == "validation":
        reason, cta_action = "plus_validate", "run_validation"
    elif next_act in ("factor", "backtest") or done_count < 2:
        reason, cta_action = "plus_formula", "create_factor"
    else:
        reason = "plus_welcome"
        cta_action = next_act or "create_factor"

    skip = ("全部", "all", "研究员卡", "Researcher")
    feats = [f for f in plan["features"] if not any(s in f for s in skip)]
    unlock = labels["unlock_joiner"].join(feats[:3])

    if cta_action == "create_project":
        cta_path = "/templates"
    elif active_project_id:
        cta_path = f"/projects/{active_project_id}"
    else:
        cta_path = "/projects"

    return {
        "plan_code": plan_code,
        "plan_name": plan["name"],
        "tier": tier,
        "tier_name": TIER_NAMES.get(tier, ""),
        "reason": reason,
        "message": labels[reason],
        "unlock_features": unlock,
        "cta_action": cta_action,
        "cta_path": cta_path,
        "active_project_id": active_project_id,
        "receipt_email_hint": bes.receipt_coaching_hint(locale),
    }
