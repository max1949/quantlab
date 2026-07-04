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


def test_feed_graduated_only_filter(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data
    from backend.app.services.research_service import feed
    from backend.tests.test_growth import _full_research

    seed_sample_market_data(db_session)
    h = _register(client, "fgrad1")
    proj, rep = _full_research(client, h, db_session)
    client.post(f"{BASE}/projects/{proj['id']}/publish", headers=h)
    client.post(f"{BASE}/research/reports/{rep['id']}/share", headers=h)

    all_rows = feed(db_session, sort="latest", limit=50, graduated_only=False)
    grad_rows = feed(db_session, sort="latest", limit=50, graduated_only=True)
    assert len(grad_rows) <= len(all_rows)
    assert all(r.get("paper_graduated") for r in grad_rows)

    api_all = client.get(f"{BASE}/public/feed").json()
    api_grad = client.get(f"{BASE}/public/feed", params={"graduated_only": True}).json()
    assert isinstance(api_grad, list)
    assert len(api_grad) <= len(api_all)


def test_profile_includes_paper_mastery_counts(client, db_session):
    h = _register(client, "fprof1")
    prof = client.get(f"{BASE}/researchers/me", headers=h).json()
    assert "paper_graduated_count" in prof
    assert "paper_tracking_count" in prof
    assert prof["paper_graduated_count"] >= 0
