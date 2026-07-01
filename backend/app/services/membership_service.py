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
            "因子组合器",
            "历史回测 (真实行情)",
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
        "tagline": "准职业工作流: 组合优化 + 模拟实盘",
        "features": [
            "研究员卡全部功能",
            "组合优化 (均值方差 / 风险平价)",
            "模拟实盘 paper trading",
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
    "backtest_cross_section": {"label": "截面多标的回测", "min_level": 2, "min_tier": 1},
    "cost_sensitivity": {"label": "成本敏感性分析", "min_level": 2, "min_tier": 1},
    "factor_orthogonalize": {"label": "多因子正交化", "min_level": 3, "min_tier": 1},
    "robustness_test": {"label": "参数稳健性测试", "min_level": 3, "min_tier": 1},
    "overfit_check": {"label": "过拟合检查", "min_level": 3, "min_tier": 1},
    "portfolio_optimize": {"label": "组合优化", "min_level": 4, "min_tier": 2},
    "paper_trading": {"label": "模拟实盘", "min_level": 4, "min_tier": 2},
}


class RedeemError(Exception):
    """兑换码无效/已用。"""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _active_subscriptions(db: Session, user_id: uuid.UUID) -> list[Subscription]:
    now = _now()
    stmt = select(Subscription).where(
        Subscription.user_id == user_id,
        Subscription.status == SubscriptionStatus.ACTIVE.value,
    )
    subs = list(db.execute(stmt).scalars().all())
    return [s for s in subs if s.expires_at is None or s.expires_at > now]


def current_tier(db: Session, user: User) -> int:
    """当前付费档位 = 所有未过期订阅里的最大 tier; 无则 0 (免费)。"""
    subs = _active_subscriptions(db, user.id)
    return max((s.tier for s in subs), default=TIER_FREE)


def get_status(db: Session, user: User) -> dict:
    subs = _active_subscriptions(db, user.id)
    tier = max((s.tier for s in subs), default=TIER_FREE)
    # 取档位最高、到期最晚的一条作为"主订阅"展示。
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
    tier = current_tier(db, user)
    feats = [feature_state(user.level, tier, k) for k in FEATURES]
    return {
        "level": user.level,
        "level_name": UserLevel(user.level).label,
        "tier": tier,
        "tier_name": TIER_NAMES.get(tier, "免费"),
        "features": feats,
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
) -> Subscription:
    expires = None if period_days <= 0 else _now() + timedelta(days=period_days)
    sub = Subscription(
        user_id=user.id,
        plan_code=plan_code,
        tier=tier,
        status=SubscriptionStatus.ACTIVE.value,
        source=source,
        expires_at=expires,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
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
    db: Session, tier: int = TIER_PLUS, period_days: int = 30,
    plan_code: str = "plus_monthly", note: str | None = None,
) -> RedeemCode:
    code = "QL-" + secrets.token_hex(4).upper()
    rc = RedeemCode(
        code=code, tier=tier, period_days=period_days, plan_code=plan_code, note=note
    )
    db.add(rc)
    db.commit()
    db.refresh(rc)
    return rc


def start_checkout(db: Session, user: User, plan_code: str) -> dict:
    """支付下单占位。

    真实收款需要商户号 (微信支付/支付宝/Stripe)。商户号到位后, 在此处生成支付
    订单并返回 pay_url; 支付回调里调用 grant() 开通。当前返回未配置提示 +
    兑换码引导, 保证流程闭环。
    """
    plan = PLAN_BY_CODE.get(plan_code)
    if plan is None or plan["tier"] == 0:
        raise RedeemError("无效的套餐")
    return {
        "configured": False,
        "plan_code": plan_code,
        "plan_name": plan["name"],
        "price_cny": plan["price_cny"],
        "message": "请向师父购买卡密，在本页下方输入 BKTA-XXXX-XXXX 兑换开通。",
    }
