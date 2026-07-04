"""Feed 大师化徽章测试。"""

from __future__ import annotations

import uuid

from backend.app.services.research_service import _feed_mastery_badges
from backend.tests.test_growth import BASE, _register


def test_feed_mastery_badges_defaults_without_validation(client, db_session):
    from backend.app.models.research import ResearchReport
    from backend.app.services.market_data import seed_sample_market_data

    seed_sample_market_data(db_session)
    h = _register(client, "fbadge1")
    proj = client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": "RB"}).json()
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "f", "template_type": "momentum", "params": {"window": 20}, "project_id": proj["id"]},
    ).json()["id"]
    owner_id = uuid.UUID(client.get(f"{BASE}/researchers/me", headers=h).json()["user_id"])
    report = ResearchReport(
        owner_id=owner_id,
        project_id=uuid.UUID(proj["id"]),
        factor_id=uuid.UUID(fid),
        symbol="RB",
        title="t",
        summary="s",
        hypothesis="h",
        methodology="m",
        result="r",
        risk_analysis="ra",
        improvement_suggestion="i",
        is_public=True,
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    badges = _feed_mastery_badges(db_session, report)
    assert badges["paper_graduated"] is False
    assert badges["paper_tracking"] is False
    assert badges["mastery_badge"] is None
