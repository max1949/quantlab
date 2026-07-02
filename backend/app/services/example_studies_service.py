"""公开示例研究种子 — 为首页 Feed / SEO 提供 3–5 份可浏览的完整研究案例。"""

from __future__ import annotations

import os
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.factor import Factor
from backend.app.models.project import ProjectStatus, ResearchProject
from backend.app.models.user import User, UserLevel
from backend.app.schemas.user import UserCreate
from backend.app.services import (
    backtest_service,
    factor_service,
    project_service,
    research_service,
    share_service,
    user_service,
    validation_service,
)
from backend.app.services.project_service import ProjectQualityRejectedError

DEMO_USERNAME = "quantlab_examples"

EXAMPLE_SPECS: list[dict] = [
    {
        "title": "螺纹钢动量因子示例",
        "symbol": "RB",
        "template_type": "momentum",
        "params": {"window": 20},
        "question": "动量效应在黑色系期货上是否具备样本外稳健性？",
        "tags": ["示例", "动量", "螺纹钢"],
    },
    {
        "title": "黄金均值回归示例",
        "symbol": "AU",
        "template_type": "mean_reversion",
        "params": {"window": 15},
        "question": "贵金属短期偏离后是否存在可交易的回归机会？",
        "tags": ["示例", "均值回归", "黄金"],
    },
    {
        "title": "股指期货波动率示例",
        "symbol": "IF",
        "template_type": "volatility",
        "params": {"window": 20},
        "question": "波动率因子在股指日线上的风险溢价特征如何？",
        "tags": ["示例", "波动率", "股指"],
    },
    {
        "title": "螺纹钢均线偏离示例",
        "symbol": "RB",
        "template_type": "sma_ratio",
        "params": {"window": 30},
        "question": "价格相对均线的偏离能否作为短期反转信号？",
        "tags": ["示例", "均线", "螺纹钢"],
    },
]


def _get_or_create_demo_user(db: Session) -> User:
    user = user_service.get_by_identifier(db, DEMO_USERNAME)
    if user is not None:
        return user
    pwd = os.environ.get("EXAMPLES_USER_PASSWORD", "Examples-Demo-2026!")
    user = user_service.create_user(
        db,
        UserCreate(
            email="examples@quantlab.ai",
            username=DEMO_USERNAME,
            password=pwd,
        ),
    )
    user.level = UserLevel.L2
    user.onboarding_done = True
    db.commit()
    db.refresh(user)
    return user


def _existing_project(db: Session, owner_id: uuid.UUID, title: str) -> ResearchProject | None:
    return db.execute(
        select(ResearchProject).where(
            ResearchProject.owner_id == owner_id,
            ResearchProject.title == title,
        )
    ).scalar_one_or_none()


def _build_one_example(db: Session, user: User, spec: dict) -> dict:
    title = spec["title"]
    existing = _existing_project(db, user.id, title)
    if existing is not None and existing.status == ProjectStatus.PUBLISHED.value:
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

    factor_name = f"{spec['template_type']}-{symbol}-demo"
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
        factors = list(
            db.execute(select(Factor).where(Factor.project_id == project.id)).scalars().all()
        )
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
    published = False
    try:
        project_service.publish_project(db, user.id, project.id)
        published = True
    except ProjectQualityRejectedError:
        project.status = ProjectStatus.PUBLISHED.value
        report.is_public = True
        db.commit()
        published = True

    try:
        share_service.create_share(db, user, report.id)
    except Exception:
        pass  # 示例种子：质量未达标时仍保留公开报告
    return {
        "title": title,
        "status": "published" if published else "shared",
        "project_id": str(project.id),
        "report_id": str(report.id),
    }


def seed_public_example_studies(db: Session) -> dict:
    """幂等播种公开示例研究。返回 created / skipped 统计。"""
    user = _get_or_create_demo_user(db)
    created: list[dict] = []
    skipped: list[str] = []
    for spec in EXAMPLE_SPECS:
        existing = _existing_project(db, user.id, spec["title"])
        if existing is not None and existing.status == ProjectStatus.PUBLISHED.value:
            skipped.append(spec["title"])
            continue
        try:
            created.append(_build_one_example(db, user, spec))
        except Exception as exc:  # noqa: BLE001 — 单个示例失败不阻断其余
            created.append({"title": spec["title"], "status": "error", "error": str(exc)})
    return {
        "username": DEMO_USERNAME,
        "created": created,
        "skipped": skipped,
        "total_examples": len(EXAMPLE_SPECS),
    }
