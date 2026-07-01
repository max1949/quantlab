"""研究模板库 (Sprint 9A): 一键创建研究项目 + 默认因子。

降低小白的"冷启动门槛": 选一个主题模板, 系统自动建好项目并造好第一个因子,
用户直接进入回测/验证, 而不是面对空白页发呆。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.locale import Locale
from backend.app.i18n import content as i18n
from backend.app.models.growth import ResearchTemplate
from backend.app.models.user import User
from backend.app.services import factor_service, project_service

# 平台预置研究模板。factor_template 必须是 engine 合法因子模板 code。
# 模板权限: min_level / min_tier (与 membership_service 一致)
TEMPLATE_GATES: dict[str, dict[str, int]] = {
    "gold-trend": {"min_level": 0, "min_tier": 0},
    "commodity-momentum": {"min_level": 0, "min_tier": 0},
    "vol-regime": {"min_level": 0, "min_tier": 0},
    "mean-reversion": {"min_level": 0, "min_tier": 0},
    "rsi-study": {"min_level": 0, "min_tier": 0},
    "sma-cross": {"min_level": 1, "min_tier": 0},
    "multi-momentum": {"min_level": 2, "min_tier": 1},
}

DEFAULT_TEMPLATES = [
    {
        "code": "gold-trend", "title": "黄金趋势研究", "symbol": "AU",
        "factor_template": "momentum", "default_params": {"window": 20},
        "hypothesis": "黄金价格是否存在趋势延续性?",
        "description": "用动量因子检验黄金 (AU) 的趋势是否可被捕捉。",
        "tags": ["趋势", "贵金属"],
    },
    {
        "code": "commodity-momentum", "title": "商品动量研究", "symbol": "RB",
        "factor_template": "momentum", "default_params": {"window": 20},
        "hypothesis": "螺纹钢 (RB) 的动量效应是否有效?",
        "description": "用动量因子研究商品期货的趋势惯性。",
        "tags": ["动量", "商品"],
    },
    {
        "code": "vol-regime", "title": "波动率研究", "symbol": "IF",
        "factor_template": "volatility", "default_params": {"window": 20},
        "hypothesis": "波动率状态能否预示后续收益分布?",
        "description": "用波动率因子研究股指 (IF) 的风险状态切换。",
        "tags": ["波动率", "股指"],
    },
    {
        "code": "mean-reversion", "title": "均值回归研究", "symbol": "RB",
        "factor_template": "mean_reversion", "default_params": {"window": 20},
        "hypothesis": "价格偏离均值后是否倾向回归?",
        "description": "用均值回归因子检验价格的回归特性。",
        "tags": ["均值回归"],
    },
    {
        "code": "rsi-study", "title": "RSI 强弱研究", "symbol": "RB",
        "factor_template": "rsi", "default_params": {"window": 14},
        "hypothesis": "RSI 超买超卖区域是否蕴含反转信号?",
        "description": "用 RSI 因子研究螺纹钢短期强弱切换。",
        "tags": ["RSI", "商品"],
    },
    {
        "code": "sma-cross", "title": "均线偏离研究", "symbol": "IF",
        "factor_template": "sma_ratio", "default_params": {"window": 20},
        "hypothesis": "价格偏离均线后是否存在可交易信号?",
        "description": "用均线偏离因子研究股指定价偏离。",
        "tags": ["均线", "股指"],
    },
    {
        "code": "multi-momentum", "title": "进阶动量组合", "symbol": "AU",
        "factor_template": "momentum", "default_params": {"window": 60},
        "hypothesis": "长周期动量在黄金上是否更稳健?",
        "description": "研究员会员专属 — 长窗口动量研究模板。",
        "tags": ["动量", "进阶"],
    },
]


class TemplateNotFoundError(Exception):
    pass


class TemplateLockedError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def seed_default_templates(db: Session) -> dict:
    created = 0
    for t in DEFAULT_TEMPLATES:
        exists = db.execute(
            select(ResearchTemplate.id).where(ResearchTemplate.code == t["code"])
        ).first()
        if exists:
            continue
        db.add(ResearchTemplate(**t))
        created += 1
    db.commit()
    return {"created": created, "total": len(DEFAULT_TEMPLATES)}


def list_templates(db: Session) -> list[ResearchTemplate]:
    return list(
        db.execute(select(ResearchTemplate).order_by(ResearchTemplate.created_at.asc())).scalars().all()
    )


def access_for(user: User, code: str, tier: int, locale: Locale = "en") -> dict:
    gate = TEMPLATE_GATES.get(code, {"min_level": 0, "min_tier": 0})
    min_level = gate["min_level"]
    min_tier = gate["min_tier"]
    level_ok = user.level >= min_level
    tier_ok = tier >= min_tier
    allowed = level_ok and tier_ok
    lock_hint = i18n.format_lock_hint(locale, min_level, min_tier, level_ok, tier_ok)
    return {
        "min_level": min_level,
        "min_tier": min_tier,
        "allowed": allowed,
        "lock_hint": lock_hint,
    }


def list_templates_for_user(db: Session, user: User, tier: int, locale: Locale = "en") -> list[dict]:
    rows = list_templates(db)
    out = []
    for t in rows:
        acc = access_for(user, t.code, tier, locale)
        loc = i18n.localize_research_template(
            t.code,
            locale,
            {
                "title": t.title,
                "hypothesis": t.hypothesis,
                "description": t.description,
                "tags": list(t.tags or []),
            },
        )
        out.append({**acc, "template": t, "localized": loc})
    return out


def get_by_code(db: Session, code: str) -> ResearchTemplate:
    t = db.execute(select(ResearchTemplate).where(ResearchTemplate.code == code)).scalar_one_or_none()
    if t is None:
        raise TemplateNotFoundError(code)
    return t


def start(db: Session, user: User, code: str, with_factor: bool = True, tier: int = 0, locale: Locale = "en") -> dict:
    """从模板一键开局: 建项目 (+可选首个因子)。返回 project 与 factor_id。"""
    acc = access_for(user, code, tier, locale)
    if not acc["allowed"]:
        raise TemplateLockedError(i18n.t(locale, i18n.TEMPLATE_LOCKED))
    tpl = get_by_code(db, code)
    loc = i18n.localize_research_template(
        code,
        locale,
        {
            "title": tpl.title,
            "hypothesis": tpl.hypothesis,
            "description": tpl.description,
            "tags": list(tpl.tags or []),
        },
    )
    project = project_service.create_project(
        db, user, title=loc["title"], symbol=tpl.symbol, question=loc["hypothesis"],
        description=loc["description"], tags=list(loc["tags"]),
    )
    factor_id = None
    if with_factor:
        # 因子名带短后缀, 避免同一用户多次开同模板时重名。
        suffix = uuid.uuid4().hex[:6]
        factor = factor_service.create_template_factor(
            db, user, name=f"{tpl.factor_template}-{tpl.symbol}-{suffix}",
            template_type=tpl.factor_template, params=dict(tpl.default_params or {}),
            project_id=project.id,
        )
        factor_id = factor.id
    return {"project": project, "factor_id": factor_id, "template_code": tpl.code}
