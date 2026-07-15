"""运营 / PMF 指标聚合 (机构后台只读)。"""

from __future__ import annotations

import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.factor import Factor
from backend.app.models.growth import ResearchShare, UserEvent
from backend.app.models.membership import Subscription, SubscriptionStatus
from backend.app.models.project import ProjectStatus, ResearchProject
from backend.app.models.research import ResearchReport
from backend.app.models.organization import OrgFactorShare, OrgMember, ResearchOrg
from backend.app.models.execution import PaperOrder
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus

TEST_PATTERN = re.compile(
    r"^(s9btester|uitester|smoke|test|demo|quantlab_examples|ql_seed)",
    re.IGNORECASE,
)


def _pct(n: int, d: int) -> float:
    return round(n / d, 4) if d else 0.0


def _owner_ids(db: Session, model, where=None) -> set:
    stmt = select(model.owner_id).distinct()
    if where is not None:
        stmt = stmt.where(where)
    return {row[0] for row in db.execute(stmt).all()}


def compute_pmf_metrics(db: Session, *, exclude_test: bool = True) -> dict:
    users = db.execute(select(User.id, User.username)).all()
    all_ids = {u.id for u in users}
    test_ids = {u.id for u in users if TEST_PATTERN.match(u.username or "")}
    universe = (all_ids - test_ids) if exclude_test else all_ids

    s_project = _owner_ids(db, ResearchProject) & universe
    s_factor = _owner_ids(db, Factor) & universe
    s_bt = _owner_ids(db, Backtest, Backtest.status == BacktestStatus.SUCCESS.value) & universe
    s_val = _owner_ids(db, Validation, Validation.status == ValidationStatus.SUCCESS.value) & universe
    s_report = _owner_ids(db, ResearchReport) & universe
    s_share = _owner_ids(db, ResearchShare) & universe

    registered = len(universe)
    rcr_users = s_project & s_factor & s_bt & s_val & s_report & s_share

    f_project = s_project
    f_bt = f_project & s_bt
    f_report = f_bt & s_report
    f_share = f_report & s_share

    events = db.execute(select(UserEvent.event, func.count()).group_by(UserEvent.event)).all()
    event_counts = {e: int(c) for e, c in events}

    active_subs = db.execute(
        select(func.count()).select_from(Subscription).where(
            Subscription.status == SubscriptionStatus.ACTIVE.value
        )
    ).scalar_one()

    published_projects = db.execute(
        select(func.count()).select_from(ResearchProject).where(
            ResearchProject.status == ProjectStatus.PUBLISHED.value
        )
    ).scalar_one()

    public_reports = db.execute(
        select(func.count()).select_from(ResearchReport).where(ResearchReport.is_public.is_(True))
    ).scalar_one()

    total_orgs = db.execute(select(func.count()).select_from(ResearchOrg)).scalar_one()
    total_org_members = db.execute(select(func.count()).select_from(OrgMember)).scalar_one()
    shared_org_factors = db.execute(select(func.count()).select_from(OrgFactorShare)).scalar_one()
    paper_orders = db.execute(select(func.count()).select_from(PaperOrder)).scalar_one()
    vnpy_orders = db.execute(
        select(func.count()).select_from(PaperOrder).where(PaperOrder.channel == "vnpy")
    ).scalar_one()
    qmt_orders = db.execute(
        select(func.count()).select_from(PaperOrder).where(PaperOrder.channel == "qmt")
    ).scalar_one()
    routed_gateway_orders = db.execute(
        select(func.count()).select_from(PaperOrder).where(
            PaperOrder.channel.in_(("vnpy", "qmt")),
            PaperOrder.status == "routed",
        )
    ).scalar_one()

    from engine.execution_adapter import gateway_health_summary
    from backend.app.services import execution_compliance_service as ecs

    compliance = ecs.build_global_compliance_report(db, stale_limit=20)

    return {
        "registered_users": registered,
        "test_accounts_excluded": len(test_ids) if exclude_test else 0,
        "rcr": _pct(len(rcr_users), registered),
        "rcr_users": len(rcr_users),
        "activation": _pct(len(s_report), registered),
        "share_rate": _pct(len(s_share), len(s_report)),
        "funnel": {
            "registered": registered,
            "project": len(f_project),
            "backtest_success": len(f_bt),
            "report": len(f_report),
            "share": len(f_share),
        },
        "event_counts": event_counts,
        "active_subscriptions": int(active_subs or 0),
        "published_projects": int(published_projects or 0),
        "public_reports": int(public_reports or 0),
        "retention_day7": None,
        "retention_note": "需要 login/session 埋点",
        "institutional": {
            "total_orgs": int(total_orgs or 0),
            "total_org_members": int(total_org_members or 0),
            "shared_org_factors": int(shared_org_factors or 0),
            "paper_orders": int(paper_orders or 0),
            "vnpy_orders": int(vnpy_orders or 0),
            "qmt_orders": int(qmt_orders or 0),
            "routed_gateway_orders": int(routed_gateway_orders or 0),
            "gateway_health": gateway_health_summary(),
            "execution_sla_alerts": compliance["alert_count"],
            "execution_stale_orders": len(compliance["stale_orders"]),
        },
    }
