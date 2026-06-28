"""分流 + onboarding (Sprint 9A)。

按"分流身份 + 当前研究进度"算出"下一步该做什么", 给小白明确指引。
该 next_step 同时被 onboarding/next 与 AI 研究导师 (/ai/mentor/next) 复用。
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.factor import Factor
from backend.app.models.project import ProjectStatus, ResearchProject
from backend.app.models.research import ResearchReport
from backend.app.models.user import User, UserType
from backend.app.models.validation import Validation, ValidationStatus

# 不同身份推荐的开局研究模板 (code 见 template_service.DEFAULT_TEMPLATES)。
TYPE_DEFAULT_TEMPLATE = {
    UserType.NEWBIE.value: "gold-trend",
    UserType.PYTHON.value: "commodity-momentum",
    UserType.TRADER.value: "vol-regime",
}

TYPE_INTRO = {
    UserType.NEWBIE.value: "完全不用写代码, 我们带你用模板一步步做出第一个研究。",
    UserType.PYTHON.value: "你有 Python 基础, 可以更快上手因子与组合, 我们直接给你硬核路线。",
    UserType.TRADER.value: "你懂交易, 我们帮你把盘感变成可被验证的因子与研究结论。",
}


def choose_type(db: Session, user: User, user_type: str) -> User:
    if user_type not in {t.value for t in UserType}:
        raise ValueError("未知用户类型")
    user.user_type = user_type
    user.onboarding_done = True
    db.commit()
    db.refresh(user)
    return user


def _count(db: Session, stmt) -> int:
    return int(db.execute(stmt).scalar_one() or 0)


def _stage(db: Session, user: User) -> str:
    uid = user.id
    projects = _count(db, select(func.count(ResearchProject.id)).where(ResearchProject.owner_id == uid))
    if projects == 0:
        return "create_project"
    factors = _count(db, select(func.count(Factor.id)).where(Factor.owner_id == uid))
    if factors == 0:
        return "create_factor"
    bt = _count(
        db,
        select(func.count(Backtest.id)).where(
            Backtest.owner_id == uid, Backtest.status == BacktestStatus.SUCCESS.value
        ),
    )
    if bt == 0:
        return "run_backtest"
    val = _count(
        db,
        select(func.count(Validation.id)).where(
            Validation.owner_id == uid, Validation.status == ValidationStatus.SUCCESS.value
        ),
    )
    if val == 0:
        return "run_validation"
    reports = _count(db, select(func.count(ResearchReport.id)).where(ResearchReport.owner_id == uid))
    if reports == 0:
        return "generate_report"
    published = _count(
        db,
        select(func.count(ResearchProject.id)).where(
            ResearchProject.owner_id == uid, ResearchProject.status == ProjectStatus.PUBLISHED.value
        ),
    )
    if published == 0:
        return "publish_share"
    return "keep_going"


_STEP_DETAIL = {
    "create_project": {
        "title": "创建你的第一个研究项目",
        "action": "用研究模板一键开局, 定一个研究主题",
        "cta": "/research/create",
    },
    "create_factor": {
        "title": "造你的第一个因子",
        "action": "在项目下选一个模板因子 (如动量), 填个窗口参数即可",
        "cta": "/factor-lab",
    },
    "run_backtest": {
        "title": "跑第一次回测",
        "action": "看看这个因子在历史行情上的表现",
        "cta": "/factor-lab",
    },
    "run_validation": {
        "title": "做一次科学验证 (OOS)",
        "action": "用样本外 + Walk-Forward 检验因子是不是过拟合",
        "cta": "/factor-lab",
    },
    "generate_report": {
        "title": "生成研究报告",
        "action": "把因子+回测+验证聚合成一篇人话研究报告",
        "cta": "/dashboard",
    },
    "publish_share": {
        "title": "发布并分享你的研究",
        "action": "公开项目、生成分享卡片, 让更多人看到你的研究",
        "cta": "/dashboard",
    },
    "keep_going": {
        "title": "继续深化研究",
        "action": "试试组合因子、跨品种验证, 或开一个新主题冲榜",
        "cta": "/leaderboard",
    },
}


def next_step(db: Session, user: User) -> dict:
    """返回个性化下一步 (身份 + 进度)。"""
    stage = _stage(db, user)
    detail = _STEP_DETAIL[stage]
    out = {
        "user_type": user.user_type,
        "user_type_label": UserType(user.user_type).label,
        "intro": TYPE_INTRO.get(user.user_type, ""),
        "stage": stage,
        "title": detail["title"],
        "action": detail["action"],
        "cta_path": detail["cta"],
    }
    if stage == "create_project":
        out["recommended_template"] = TYPE_DEFAULT_TEMPLATE.get(user.user_type, "momentum")
    return out
