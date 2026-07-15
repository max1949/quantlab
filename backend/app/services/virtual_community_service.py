"""虚拟社区种子 — 让广场 / 榜单 / 关注流看起来有真实人气。

用户名前缀 ``demo_`` 会被 ops PMF 指标排除, 不影响真实运营漏斗统计。
幂等: 按 username + 项目标题跳过已有产物。
"""

from __future__ import annotations

import os
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.execution import OrderSide, OrderStatus, PaperOrder
from backend.app.models.factor import Factor
from backend.app.models.growth import ResearchShare, UserFollow
from backend.app.models.project import ProjectStatus, ResearchProject
from backend.app.models.research import ResearchReport
from backend.app.models.user import User, UserLevel, UserType
from backend.app.schemas.user import UserCreate
from backend.app.services import (
    backtest_service,
    factor_service,
    growth_service,
    project_service,
    research_service,
    share_service,
    social_service,
    user_service,
    validation_service,
)
from backend.app.services.project_service import ProjectQualityRejectedError
from backend.app.services.research_quality_service import assess_factor_paper

SEED_PASSWORD = os.environ.get("VIRTUAL_COMMUNITY_PASSWORD", "Demo-Camp-2026!")

# 12 位演示研究员 — 看起来像真实用户, 前缀 demo_ 供指标排除
COMMUNITY_PROFILES: list[dict] = [
    {
        "username": "demo_linyi",
        "email": "demo_linyi@demo.quantlab.ai",
        "display_hint": "林屿",
        "level": UserLevel.L3,
        "user_type": UserType.TRADER.value,
        "reward_points": 420,
        "experience": 980,
        "days_ago": 48,
        "studies": [
            {
                "title": "螺纹钢 20 日动量稳健性复盘",
                "symbol": "RB",
                "template_type": "momentum",
                "params": {"window": 20},
                "question": "黑色系日线动量在扣成本后样本外是否仍有效？",
                "tags": ["动量", "螺纹钢", "OOS"],
                "days_ago": 40,
                "share_views": 186,
                "want_paper": True,
            },
            {
                "title": "螺纹钢短窗动量换手压力测试",
                "symbol": "RB",
                "template_type": "momentum",
                "params": {"window": 8},
                "question": "缩短回看窗口后, 换手与成本敏感性如何变化？",
                "tags": ["动量", "成本", "螺纹钢"],
                "days_ago": 22,
                "share_views": 94,
            },
        ],
    },
    {
        "username": "demo_chenhao",
        "email": "demo_chenhao@demo.quantlab.ai",
        "level": UserLevel.L2,
        "user_type": UserType.PYTHON.value,
        "reward_points": 310,
        "experience": 640,
        "days_ago": 36,
        "studies": [
            {
                "title": "黄金趋势延续性初探",
                "symbol": "AU",
                "template_type": "momentum",
                "params": {"window": 25},
                "question": "贵金属中周期动量能否穿越制度切换？",
                "tags": ["黄金", "趋势", "贵金属"],
                "days_ago": 30,
                "share_views": 142,
                "want_paper": True,
            }
        ],
    },
    {
        "username": "demo_zhoumin",
        "email": "demo_zhoumin@demo.quantlab.ai",
        "level": UserLevel.L2,
        "user_type": UserType.NEWBIE.value,
        "reward_points": 255,
        "experience": 510,
        "days_ago": 28,
        "studies": [
            {
                "title": "黄金均值回归短线信号",
                "symbol": "AU",
                "template_type": "mean_reversion",
                "params": {"window": 15},
                "question": "价格偏离均值后, 回归速度与胜率如何？",
                "tags": ["均值回归", "黄金"],
                "days_ago": 18,
                "share_views": 118,
            }
        ],
    },
    {
        "username": "demo_wangqi",
        "email": "demo_wangqi@demo.quantlab.ai",
        "level": UserLevel.L3,
        "user_type": UserType.TRADER.value,
        "reward_points": 505,
        "experience": 1200,
        "days_ago": 55,
        "studies": [
            {
                "title": "股指波动率状态与收益分布",
                "symbol": "IF",
                "template_type": "volatility",
                "params": {"window": 20},
                "question": "高波动制度下 IF 日线因子表现是否系统性变差？",
                "tags": ["波动率", "股指", "regime"],
                "days_ago": 45,
                "share_views": 221,
                "want_paper": True,
            },
            {
                "title": "股指均线偏离反转检验",
                "symbol": "IF",
                "template_type": "sma_ratio",
                "params": {"window": 30},
                "question": "价格相对 30 日均线偏离是否含短期反转信息？",
                "tags": ["均线", "股指"],
                "days_ago": 12,
                "share_views": 67,
            },
        ],
    },
    {
        "username": "demo_suqing",
        "email": "demo_suqing@demo.quantlab.ai",
        "level": UserLevel.L1,
        "user_type": UserType.NEWBIE.value,
        "reward_points": 180,
        "experience": 280,
        "days_ago": 16,
        "studies": [
            {
                "title": "螺纹钢 RSI 超买超卖初验",
                "symbol": "RB",
                "template_type": "mean_reversion",
                "params": {"window": 14},
                "question": "价格偏离均值后, 黑色系短期反转有无统计优势？",
                "tags": ["均值回归", "螺纹钢", "新手"],
                "days_ago": 9,
                "share_views": 73,
            }
        ],
    },
    {
        "username": "demo_hejun",
        "email": "demo_hejun@demo.quantlab.ai",
        "level": UserLevel.L2,
        "user_type": UserType.PYTHON.value,
        "reward_points": 275,
        "experience": 720,
        "days_ago": 33,
        "studies": [
            {
                "title": "螺纹钢放量突破因子笔记",
                "symbol": "RB",
                "template_type": "volume_surge",
                "params": {"window": 20},
                "question": "异常放量配合方向后, 后续 5 日延续概率如何？",
                "tags": ["成交量", "突破", "螺纹钢"],
                "days_ago": 20,
                "share_views": 105,
            }
        ],
    },
    {
        "username": "demo_yanfei",
        "email": "demo_yanfei@demo.quantlab.ai",
        "level": UserLevel.L2,
        "user_type": UserType.TRADER.value,
        "reward_points": 340,
        "experience": 800,
        "days_ago": 41,
        "studies": [
            {
                "title": "黄金长窗动量稳健路径",
                "symbol": "AU",
                "template_type": "momentum",
                "params": {"window": 60},
                "question": "60 日动量相对 20 日是否更稳、更不易过拟合？",
                "tags": ["动量", "黄金", "长周期"],
                "days_ago": 27,
                "share_views": 156,
                "want_paper": True,
            }
        ],
    },
    {
        "username": "demo_luoran",
        "email": "demo_luoran@demo.quantlab.ai",
        "level": UserLevel.L1,
        "user_type": UserType.NEWBIE.value,
        "reward_points": 145,
        "experience": 220,
        "days_ago": 12,
        "studies": [
            {
                "title": "IF 短周期动量入门笔记",
                "symbol": "IF",
                "template_type": "momentum",
                "params": {"window": 12},
                "question": "新手第一份回测: 短窗动量在股指上会过热吗？",
                "tags": ["新手", "股指", "动量"],
                "days_ago": 6,
                "share_views": 41,
            }
        ],
    },
    {
        "username": "demo_xiaoyu",
        "email": "demo_xiaoyu@demo.quantlab.ai",
        "level": UserLevel.L2,
        "user_type": UserType.PYTHON.value,
        "reward_points": 290,
        "experience": 560,
        "days_ago": 24,
        "studies": [
            {
                "title": "螺纹钢均线偏离对照实验",
                "symbol": "RB",
                "template_type": "sma_ratio",
                "params": {"window": 20},
                "question": "均线偏离与纯动量在同样标的上差异有多大？",
                "tags": ["均线", "对照", "螺纹钢"],
                "days_ago": 14,
                "share_views": 88,
            }
        ],
    },
    {
        "username": "demo_gaobo",
        "email": "demo_gaobo@demo.quantlab.ai",
        "level": UserLevel.L3,
        "user_type": UserType.TRADER.value,
        "reward_points": 480,
        "experience": 1100,
        "days_ago": 52,
        "studies": [
            {
                "title": "股指制度适配动量研究",
                "symbol": "IF",
                "template_type": "momentum",
                "params": {"window": 40},
                "question": "中低波动制度下趋势因子是否更稳？",
                "tags": ["regime", "股指", "动量"],
                "days_ago": 35,
                "share_views": 198,
                "want_paper": True,
            }
        ],
    },
    {
        "username": "demo_shuyan",
        "email": "demo_shuyan@demo.quantlab.ai",
        "level": UserLevel.L1,
        "user_type": UserType.NEWBIE.value,
        "reward_points": 160,
        "experience": 260,
        "days_ago": 10,
        "studies": [
            {
                "title": "黄金强弱偏离入门对照",
                "symbol": "AU",
                "template_type": "sma_ratio",
                "params": {"window": 14},
                "question": "同一偏离思路在贵金属与黑色系上结论一样吗？",
                "tags": ["均线", "黄金", "新手"],
                "days_ago": 4,
                "share_views": 52,
            }
        ],
    },
    {
        "username": "demo_fengke",
        "email": "demo_fengke@demo.quantlab.ai",
        "level": UserLevel.L2,
        "user_type": UserType.PYTHON.value,
        "reward_points": 265,
        "experience": 690,
        "days_ago": 20,
        "studies": [
            {
                "title": "IF 波动率因子快速复核",
                "symbol": "IF",
                "template_type": "volatility",
                "params": {"window": 15},
                "question": "缩短波动窗口后信号是否更噪、OOS 更脆？",
                "tags": ["波动率", "股指"],
                "days_ago": 8,
                "share_views": 79,
            }
        ],
    },
]

# 关注关系: follower → followee (username)
FOLLOW_EDGES: list[tuple[str, str]] = [
    ("demo_chenhao", "demo_linyi"),
    ("demo_zhoumin", "demo_linyi"),
    ("demo_suqing", "demo_linyi"),
    ("demo_hejun", "demo_wangqi"),
    ("demo_yanfei", "demo_wangqi"),
    ("demo_luoran", "demo_wangqi"),
    ("demo_xiaoyu", "demo_chenhao"),
    ("demo_shuyan", "demo_chenhao"),
    ("demo_fengke", "demo_yanfei"),
    ("demo_linyi", "demo_wangqi"),
    ("demo_linyi", "demo_gaobo"),
    ("demo_wangqi", "demo_gaobo"),
    ("demo_gaobo", "demo_linyi"),
    ("demo_zhoumin", "demo_yanfei"),
    ("demo_hejun", "demo_linyi"),
    ("demo_suqing", "demo_zhoumin"),
    ("demo_luoran", "demo_suqing"),
    ("demo_shuyan", "demo_zhoumin"),
    ("demo_fengke", "demo_hejun"),
    ("demo_xiaoyu", "demo_gaobo"),
    ("demo_chenhao", "demo_gaobo"),
    ("demo_yanfei", "demo_linyi"),
]


def _utc_days_ago(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days, hours=random.randint(0, 12))


def _get_or_create_user(db: Session, profile: dict) -> User:
    user = user_service.get_by_identifier(db, profile["username"])
    if user is None:
        user = user_service.create_user(
            db,
            UserCreate(
                email=profile["email"],
                username=profile["username"],
                password=SEED_PASSWORD,
            ),
        )
    user.level = int(profile["level"])
    user.user_type = profile.get("user_type", UserType.NEWBIE.value)
    user.onboarding_done = True
    user.is_active = True
    user.experience = max(int(user.experience or 0), int(profile.get("experience", 0)))
    user.reward_points = max(int(user.reward_points or 0), int(profile.get("reward_points", 0)))
    user.created_at = _utc_days_ago(int(profile.get("days_ago", 30)))
    db.commit()
    db.refresh(user)
    return user


def _existing_project(db: Session, owner_id, title: str) -> ResearchProject | None:
    return db.execute(
        select(ResearchProject).where(
            ResearchProject.owner_id == owner_id,
            ResearchProject.title == title,
        )
    ).scalar_one_or_none()


def _ensure_paper_order(db: Session, user: User, factor: Factor, symbol: str) -> None:
    existing = db.execute(
        select(PaperOrder.id).where(
            PaperOrder.user_id == user.id,
            PaperOrder.factor_id == factor.id,
        )
    ).first()
    if existing:
        return
    if not assess_factor_paper(db, factor.id).passed:
        return
    db.add(
        PaperOrder(
            user_id=user.id,
            factor_id=factor.id,
            symbol=symbol,
            side=OrderSide.BUY.value,
            notional_cny=50000,
            status=OrderStatus.FILLED.value,
            channel="paper",
            risk_verdict="passed",
            note="virtual community seed",
            filled_at=datetime.now(timezone.utc),
        )
    )
    db.commit()


def _bump_share_views(db: Session, report_id, views: int) -> None:
    share = db.execute(
        select(ResearchShare).where(ResearchShare.report_id == report_id)
    ).scalar_one_or_none()
    if share is None:
        return
    share.views = max(int(share.views or 0), int(views))
    db.commit()


def _build_study(db: Session, user: User, spec: dict) -> dict:
    title = spec["title"]
    existing = _existing_project(db, user.id, title)
    if existing is not None and existing.status == ProjectStatus.PUBLISHED.value:
        report = db.execute(
            select(ResearchReport)
            .where(ResearchReport.project_id == existing.id)
            .order_by(ResearchReport.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if report is not None:
            report.title = title
            if spec.get("question"):
                report.hypothesis = spec["question"]
            report.created_at = _utc_days_ago(int(spec.get("days_ago", 14)))
            existing.created_at = report.created_at
            db.commit()
            try:
                share_service.create_share(db, user, report.id)
            except Exception:
                pass
            _bump_share_views(db, report.id, int(spec.get("share_views", 50)))
            factors = list(db.execute(select(Factor).where(Factor.project_id == existing.id)).scalars().all())
            if factors and spec.get("want_paper"):
                _ensure_paper_order(db, user, factors[0], spec["symbol"])
        return {"title": title, "status": "skipped", "project_id": str(existing.id)}

    symbol = spec["symbol"]
    if existing is None:
        project = project_service.create_project(
            db,
            user,
            title=title,
            symbol=symbol,
            question=spec.get("question", ""),
            tags=spec.get("tags") or [],
        )
    else:
        project = existing

    stamp = _utc_days_ago(int(spec.get("days_ago", 14)))
    project.created_at = stamp
    db.commit()

    factor_name = f"{spec['template_type']}-{symbol}-w{spec['params'].get('window', 20)}-{user.username[-6:]}"
    try:
        factor = factor_service.create_template_factor(
            db,
            user,
            factor_name,
            spec["template_type"],
            spec["params"],
            project_id=project.id,
        )
    except factor_service.FactorNameTakenError:
        factors = list(db.execute(select(Factor).where(Factor.project_id == project.id)).scalars().all())
        factor = factors[0] if factors else None
        if factor is None:
            raise

    bt = backtest_service.create_backtest(db, user, factor.id, symbol, None, timeframe="1d")
    backtest_service.execute(db, bt.id)

    val = validation_service.create_validation(
        db, user, factor.id, symbol, None, oos_ratio=0.3, n_splits=4, timeframe="1d"
    )
    validation_service.execute(db, val.id)

    report = research_service.generate_for_project(db, user, project.id)
    # 使用有人情味的项目标题, 避免引擎默认「标的·因子名」看起来像机器批量产物
    report.title = title
    if spec.get("question"):
        report.hypothesis = spec["question"]
    db.commit()
    try:
        project_service.publish_project(db, user.id, project.id)
    except ProjectQualityRejectedError:
        project.status = ProjectStatus.PUBLISHED.value
        report.is_public = True
        db.commit()

    report.created_at = stamp
    project.created_at = stamp
    report.title = title
    db.commit()

    try:
        share_service.create_share(db, user, report.id)
    except Exception:
        pass
    _bump_share_views(db, report.id, int(spec.get("share_views", 50)))

    if spec.get("want_paper"):
        _ensure_paper_order(db, user, factor, symbol)

    return {
        "title": title,
        "status": "published",
        "project_id": str(project.id),
        "report_id": str(report.id),
    }


def _seed_follows(db: Session, users_by_name: dict[str, User]) -> int:
    created = 0
    for follower_name, followee_name in FOLLOW_EDGES:
        follower = users_by_name.get(follower_name)
        followee = users_by_name.get(followee_name)
        if follower is None or followee is None:
            continue
        existing = db.execute(
            select(UserFollow.id).where(
                UserFollow.follower_id == follower.id,
                UserFollow.followee_id == followee.id,
            )
        ).first()
        if existing:
            continue
        try:
            social_service.follow(db, follower, followee.id)
            created += 1
        except Exception:
            continue
    return created


def seed_virtual_community(db: Session) -> dict:
    """幂等播种虚拟社区: 用户 + 公开研究 + 关注 + 分享浏览量 + 榜单积分。"""
    users_by_name: dict[str, User] = {}
    studies: list[dict] = []
    errors: list[dict] = []

    for profile in COMMUNITY_PROFILES:
        try:
            user = _get_or_create_user(db, profile)
            users_by_name[user.username] = user
            for spec in profile.get("studies") or []:
                try:
                    studies.append(_build_study(db, user, spec))
                except Exception as exc:  # noqa: BLE001
                    errors.append({"title": spec.get("title"), "error": str(exc)})
            growth_service.recompute_contribution_score(db, user)
        except Exception as exc:  # noqa: BLE001
            errors.append({"username": profile["username"], "error": str(exc)})

    follows = _seed_follows(db, users_by_name)

    # 再次沉淀信用分 (关注数会影响分数)
    for user in users_by_name.values():
        growth_service.recompute_contribution_score(db, user)

    published = sum(1 for s in studies if s.get("status") == "published")
    skipped = sum(1 for s in studies if s.get("status") == "skipped")
    return {
        "users": len(users_by_name),
        "studies_published": published,
        "studies_skipped": skipped,
        "follows_created": follows,
        "errors": errors[:8],
        "total_profiles": len(COMMUNITY_PROFILES),
    }
