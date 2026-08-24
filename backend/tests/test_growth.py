"""Growth OS 子系统测试 (Sprint 9A): onboarding / 模板 / 分享 / 关注 / 榜单 / 邀请 / 导师 / 埋点。"""

from __future__ import annotations

from backend.app.services import llm_client
from backend.app.services.challenge_service import seed_default_challenge
from backend.app.services.market_data import seed_sample_market_data
from backend.app.services.template_service import seed_default_templates

BASE = "/api/v1"


def _register(client, username, user_type=None, ref=None):
    body = {"email": f"{username}@quantlab.ai", "username": username, "password": "s3cret-pass"}
    if user_type:
        body["user_type"] = user_type
    if ref:
        body["ref"] = ref
    client.post(f"{BASE}/auth/register", json=body)
    tok = client.post(
        f"{BASE}/auth/login", json={"identifier": username, "password": "s3cret-pass"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _full_research(client, h, db_session, symbol="RB"):
    """走到生成报告: 项目->因子->回测->验证->报告, 返回 report_id。"""
    proj = client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": symbol}).json()
    fid = client.post(
        f"{BASE}/factors/template", headers=h,
        json={"name": f"f{symbol}", "template_type": "momentum", "params": {"window": 20}, "project_id": proj["id"]},
    ).json()["id"]
    client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": symbol})
    client.post(f"{BASE}/validations", headers=h, json={"factor_id": fid, "symbol": symbol, "oos_ratio": 0.3, "n_splits": 4})
    rep = client.post(f"{BASE}/research/reports/generate", headers=h, json={"project_id": proj["id"]})
    return proj, rep.json()


# ---------------- onboarding ----------------

def test_register_with_user_type_and_onboarding_next(client, db_session):
    h = _register(client, "norah", user_type="trader")
    me = client.get(f"{BASE}/researchers/me", headers=h).json()
    assert me  # profile ok
    nxt = client.get(f"{BASE}/onboarding/next", headers=h).json()
    assert nxt["user_type"] == "trader"
    assert nxt["stage"] == "create_project"
    assert nxt["recommended_template"] == "vol-regime"


def test_next_step_regime_pick_on_create_project(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data
    from backend.app.services.template_service import seed_default_templates

    seed_sample_market_data(db_session)
    seed_default_templates(db_session)
    h = _register(client, "regnext")
    nxt = client.get(f"{BASE}/onboarding/next", headers=h).json()
    assert nxt["stage"] == "create_project"
    assert nxt.get("regime_pick") is not None
    assert nxt["recommended_template"] == nxt["regime_pick"]["template_code"]
    assert nxt["regime_pick"]["fit_score"] >= 0
    assert nxt["regime_pick"]["coach_hint"]


def test_research_journey_endpoint(client, db_session):
    seed_sample_market_data(db_session)
    seed_default_challenge(db_session)
    h = _register(client, "journey1")
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j["total"] == 7
    assert j["done_count"] == 0
    assert len(j["steps"]) == 7
    assert j["steps"][0]["key"] == "template"
    assert j["challenge_enrolled"] is False
    mg = j["mastery_goal"]
    assert mg["paper_graduated_count"] == 0
    assert mg["on_leaderboard"] is False
    assert mg["hint"]
    proj, _ = _full_research(client, h, db_session)
    client.post(f"{BASE}/challenges/30d-research/enroll", headers=h)
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j2["done_count"] >= 4
    assert j2["active_project_id"] == proj["id"]
    assert j2["challenge_enrolled"] is True
    factor_step = next(s for s in j2["steps"] if s["key"] == "factor")
    assert any(cm["code"] == "first_factor" for cm in factor_step["challenge_milestones"])


def test_journey_mastery_goal_challenge_paper_milestones(client, db_session):
    seed_sample_market_data(db_session)
    seed_default_challenge(db_session)
    h = _register(client, "chpaper")
    client.post(f"{BASE}/challenges/30d-research/enroll", headers=h)
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    mg = j["mastery_goal"]
    assert len(mg["challenge_paper_milestones"]) == 2
    codes = {m["code"] for m in mg["challenge_paper_milestones"]}
    assert codes == {"first_paper_order", "paper_graduated"}
    assert all(not m["completed"] for m in mg["challenge_paper_milestones"])
    assert len(mg["challenge_share_milestones"]) == 2
    share_codes = {m["code"] for m in mg["challenge_share_milestones"]}
    assert share_codes == {"network_radar", "research_share"}
    assert all(not m["completed"] for m in mg["challenge_share_milestones"])
    assert mg["board_limit"] == 50
    assert "graduated_needed" in mg


def test_journey_includes_attention_alerts(client, db_session):
    seed_sample_market_data(db_session)
    seed_default_challenge(db_session)
    h = _register(client, "attn1")
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert "attention_alerts" in j
    assert isinstance(j["attention_alerts"], list)
    assert "challenge_paper_coaching" in j

    proj, _ = _full_research(client, h, db_session)
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert isinstance(j2["attention_alerts"], list)
    for alert in j2["attention_alerts"]:
        assert alert["kind"] in ("regime_shift", "weak_regime_fit", "paper_decay")
        assert alert["alert_key"]
        assert alert["title"]
        assert alert["cta_path"]
        assert alert["severity"] in ("info", "watch", "alert")


def test_challenge_paper_coaching_when_enrolled(client, db_session):
    seed_sample_market_data(db_session)
    seed_default_templates(db_session)
    seed_default_challenge(db_session)
    h = _register(client, "chcoach")
    client.post(f"{BASE}/challenges/30d-research/enroll", headers=h)
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    coach = j.get("challenge_paper_coaching")
    assert coach is None or coach["next_code"] in ("first_paper_order", "paper_graduated")

    proj, _ = _full_research(client, h, db_session)
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    coach2 = j2.get("challenge_paper_coaching")
    if coach2:
        assert coach2["next_day"] in (22, 28)
        assert coach2["message"]
        assert coach2["cta_path"]


def test_dismiss_attention_alert_hides_from_journey(client, db_session):
    from backend.app.services.regime_alert_service import make_alert_key

    seed_sample_market_data(db_session)
    h = _register(client, "dismiss1")
    proj, _ = _full_research(client, h, db_session)
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    alerts = j["attention_alerts"]
    if not alerts:
        key = make_alert_key("weak_regime_fit", project_id=proj["id"])
        client.post(
            f"{BASE}/onboarding/attention-alerts/dismiss",
            headers=h,
            json={"alert_key": key},
        ).json()
        return
    key = alerts[0]["alert_key"]
    before = len(alerts)
    out = client.post(
        f"{BASE}/onboarding/attention-alerts/dismiss",
        headers=h,
        json={"alert_key": key},
    ).json()
    assert out["alert_key"] == key
    assert out["cooldown_days"] == 7
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    keys = {a["alert_key"] for a in j2["attention_alerts"]}
    assert key not in keys
    assert len(j2["attention_alerts"]) <= before - 1


def test_attention_alert_history_and_restore(client, db_session):
    from backend.app.services.regime_alert_service import make_alert_key

    seed_sample_market_data(db_session)
    h = _register(client, "alhist")
    proj, _ = _full_research(client, h, db_session)
    key = make_alert_key("weak_regime_fit", project_id=proj["id"])
    client.post(
        f"{BASE}/onboarding/attention-alerts/dismiss",
        headers=h,
        json={"alert_key": key},
    )
    hist = client.get(f"{BASE}/onboarding/attention-alerts/history", headers=h).json()
    assert hist["cooldown_days"] == 7
    assert any(item["alert_key"] == key for item in hist["items"])
    item = next(i for i in hist["items"] if i["alert_key"] == key)
    assert item["kind"] == "weak_regime_fit"
    assert item["days_remaining"] >= 0

    restore = client.post(
        f"{BASE}/onboarding/attention-alerts/restore",
        headers=h,
        json={"alert_key": key},
    ).json()
    assert restore["restored"] is True
    hist2 = client.get(f"{BASE}/onboarding/attention-alerts/history", headers=h).json()
    assert key not in {i["alert_key"] for i in hist2["items"]}


def test_journey_includes_upgrade_coaching_when_paper_ready(client, db_session):
    from backend.app.core.config import get_settings
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    settings = get_settings()
    settings.research_gate_enabled = True
    try:
        seed_sample_market_data(db_session)
        h = _register(client, "upcoach")
        _full_research(client, h, db_session)
        user = db_session.execute(select(User).where(User.username == "upcoach")).scalar_one()
        user.level = UserLevel.L4
        db_session.add(user)
        db_session.commit()
        j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
        assert "upgrade_coaching" in j
        uc = j["upgrade_coaching"]
        if uc:
            assert uc["plan_code"] == "pro_monthly"
            assert uc["target_tier"] == 2
    finally:
        settings.research_gate_enabled = False


def test_journey_includes_market_data_coaching(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "mdcoach")
    proj = client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": "RB"}).json()
    assert proj["id"]
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert "market_data_coaching" in j
    md = j["market_data_coaching"]
    if md:
        assert md["symbol"] == "RB"
        assert md["plan_code"]
        assert "stripe_available" in md


def test_journey_includes_quickstart_guide(client, db_session):
    seed_sample_market_data(db_session)
    seed_default_templates(db_session)
    h = _register(client, "qsguide")
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    qs = j.get("quickstart_guide")
    assert qs is not None
    assert qs["total"] == 3
    assert qs["progress"] == 0
    assert qs["current_index"] == 0
    assert len(qs["steps"]) == 3
    assert qs["steps"][0]["cta_action"] == "create_project"
    assert qs["steps"][0]["done"] is False
    assert qs.get("recommended_template")
    assert qs.get("recommended_template_title")

    client.post(
        f"{BASE}/research/templates/gold-trend/start",
        headers=h,
        json={"with_factor": True},
    )
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    qs2 = j2["quickstart_guide"]
    assert qs2["progress"] == 1
    assert qs2["steps"][0]["done"] is True
    assert qs2["current_index"] == 1

    _full_research(client, h, db_session)
    j3 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j3.get("quickstart_guide") is None


def test_journey_includes_first_report_coaching(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "firstrep")
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j.get("first_report_coaching") is None

    proj, _ = _full_research(client, h, db_session)
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    coach = j2.get("first_report_coaching")
    assert coach is not None
    assert coach["badge"]
    assert coach["celebrate"]
    assert coach["cta_path"] == f"/projects/{proj['id']}"
    assert coach["cta_action"] in ("run_paper", "publish_share", "run_validation")
    assert coach.get("academy_completed") is True
    assert coach.get("academy_xp") == 125
    assert j2.get("quickstart_guide") is None
    if coach.get("paper_ready"):
        assert coach.get("paper_guide_title")
        assert len(coach.get("guide_steps") or []) == 3
        assert coach["guide_steps"][0]["cta_action"] == "run_paper"
        assert coach["guide_steps"][2]["cta_path"] == "/leaderboards?kind=paper_mastery"
    else:
        assert not coach.get("guide_steps")


def test_first_report_paper_guide_steps(client, db_session):
    from backend.app.models.user import User
    from backend.app.services.onboarding_service import first_report_coaching_payload
    from sqlalchemy import select

    seed_sample_market_data(db_session)
    h = _register(client, "papguide")
    proj, _ = _full_research(client, h, db_session)
    user = db_session.execute(select(User).where(User.username == "papguide")).scalar_one()

    coach = first_report_coaching_payload(
        db_session,
        user,
        "zh",
        flags={"report": True},
        mastery_goal={"paper_ready": True, "publish_ready": False},
        active_project_id=proj["id"],
    )
    assert coach is not None
    assert coach["reason"] == "paper_ready"
    assert coach["paper_guide_title"]
    assert len(coach["guide_steps"]) == 3
    assert coach["guide_steps"][0]["label"]
    assert coach["guide_steps"][1]["cta_path"] == f"/projects/{proj['id']}"


def test_beginner_handbook_pdf(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "handpdf")
    resp = client.get(f"{BASE}/onboarding/beginner-handbook.pdf", headers=h)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"


def test_journey_includes_research_revisit_coaching(client, db_session):
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from backend.app.models.user import User

    seed_sample_market_data(db_session)
    seed_default_templates(db_session)
    h = _register(client, "stalled1")
    client.post(f"{BASE}/onboarding/choose-type", headers=h, json={"user_type": "newbie"})
    user = db_session.execute(select(User).where(User.username == "stalled1")).scalar_one()
    user.created_at = datetime.now(timezone.utc) - timedelta(days=4)
    db_session.add(user)
    db_session.commit()

    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    revisit = j.get("research_revisit_coaching")
    assert revisit is not None
    assert revisit["days_idle"] >= 3
    assert revisit["cta_path"] == "/templates?focus=vol-regime"
    assert len(revisit["guide_steps"]) == 3

    _full_research(client, h, db_session)
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j2.get("research_revisit_coaching") is None


def test_journey_includes_beginner_sprint(client, db_session):
    seed_sample_market_data(db_session)
    seed_default_templates(db_session)
    h = _register(client, "sprint1")
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    sprint = j.get("beginner_sprint")
    assert sprint is not None
    assert sprint["sprint_day"] >= 1
    assert sprint["sprint_total"] == 7
    assert sprint["challenge_code"] == "30d-research"
    assert sprint["cta_path"] == "/challenges"

    _full_research(client, h, db_session)
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j2.get("beginner_sprint") is None


def test_journey_includes_mastery_overview(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "moview")
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    ov = j.get("mastery_overview")
    assert ov is not None
    assert ov["total"] == 5
    assert ov["done_count"] == 0
    assert len(ov["phases"]) == 5
    assert ov["phases"][0]["key"] == "incubate"
    assert ov["phases"][0]["cta_path"] == "/templates"
    assert ov["phases"][0]["cta_action"] == "create_project"

    _full_research(client, h, db_session)
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    ov2 = j2["mastery_overview"]
    assert ov2 is not None
    assert ov2["done_count"] >= 2
    assert ov2["phases"][0]["done"] is True
    assert ov2["phases"][1]["done"] is True
    paper_phase = next(p for p in ov2["phases"] if p["key"] == "paper")
    assert paper_phase["cta_path"] == f"/projects/{j2['active_project_id']}"
    assert paper_phase["cta_action"] == "run_paper"
    assert "share_ready" in ov2
    assert "share_hint" in ov2
    assert ov2.get("share_cta")


def test_mastery_overview_share_ready_after_publishable_report(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "movshare")
    proj, rep = _full_research(client, h, db_session)
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    ov = j.get("mastery_overview")
    assert ov is not None
    mg = j.get("mastery_goal") or {}
    if mg.get("publish_ready"):
        assert ov["share_ready"] is True
        assert ov["share_report_id"] == rep["id"]
    else:
        assert ov["share_ready"] is False


def test_share_card_includes_mastery_path(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "movcard")
    _, rep = _full_research(client, h, db_session)
    out = client.post(f"{BASE}/research/reports/{rep['id']}/share", headers=h).json()
    mp = out["card"].get("mastery_path")
    assert mp is not None
    assert mp["total"] == 5
    assert len(mp["phases"]) == 5
    assert mp["done_count"] >= 2


def test_first_report_coaching_hides_after_paper_order(client, db_session):
    from backend.app.models.user import User, UserLevel
    from backend.app.services import membership_service as ms
    from sqlalchemy import select

    seed_sample_market_data(db_session)
    h = _register(client, "firstrep2")
    proj, _ = _full_research(client, h, db_session)
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j.get("first_report_coaching") is not None

    user = db_session.execute(select(User).where(User.username == "firstrep2")).scalar_one()
    user.level = UserLevel.L4
    db_session.add(user)
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")

    factors = client.get(f"{BASE}/factors", headers=h).json()
    fid = next(f["id"] for f in factors if f.get("project_id") == proj["id"])
    created = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={
            "symbol": "RB",
            "side": "buy",
            "notional_cny": 50000,
            "factor_id": fid,
            "signal_value": 0.82,
        },
    )
    assert created.status_code == 201, created.text

    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j2.get("first_report_coaching") is None
    # 研究质量若已过 Paper 毕业线，会进入声誉教练；否则展示首笔 Paper 教练
    coach = j2.get("first_paper_order_coaching") or j2.get("reputation_coaching")
    assert coach is not None
    if j2.get("first_paper_order_coaching"):
        assert coach["cta_path"] == "/leaderboards?kind=paper_mastery"
        assert coach.get("tracking_path", "").endswith("#paper-tracking")
    else:
        assert coach["cta_action"] == "publish_share"


def test_journey_includes_reputation_coaching_after_paper(client, db_session):
    from backend.app.models.user import User, UserLevel
    from backend.app.services import membership_service as ms
    from sqlalchemy import select

    seed_sample_market_data(db_session)
    h = _register(client, "repcoach")
    proj, report = _full_research(client, h, db_session)
    user = db_session.execute(select(User).where(User.username == "repcoach")).scalar_one()
    user.level = UserLevel.L4
    db_session.add(user)
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")

    factors = client.get(f"{BASE}/factors", headers=h).json()
    fid = next(f["id"] for f in factors if f.get("project_id") == proj["id"])
    created = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={
            "symbol": "RB",
            "side": "buy",
            "notional_cny": 50000,
            "factor_id": fid,
            "signal_value": 0.82,
        },
    )
    assert created.status_code == 201, created.text

    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    coach = j.get("reputation_coaching")
    assert coach is not None
    assert coach["badge"]
    assert coach["guide_title"]
    assert len(coach.get("guide_steps") or []) >= 2
    assert coach["cta_action"] == "publish_share"

    share_resp = client.post(f"{BASE}/research/reports/{report['id']}/share", headers=h)
    assert share_resp.status_code == 201, share_resp.text
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j2.get("reputation_coaching") is None
    # 大师路径全部完成时优先展示毕业教练，并抑制 share_growth
    growth = j2.get("share_growth_coaching")
    graduation = j2.get("mastery_graduation_coaching")
    assert growth is not None or graduation is not None
    if growth is not None:
        assert growth["reason"] in ("first_views", "network_start")
        assert growth["views"] == 0
        assert growth["followers"] == 0
        assert growth["following"] == 0
        assert growth["share_url_path"] == f"/share/{share_resp.json()['token']}"
        assert growth["feed_path"] == f"/feed?highlight={report['id']}"
        assert growth["profile_path"] == "/me"
        assert growth["following_feed_path"] == "/me/following"
        assert len(growth.get("guide_steps") or []) == 3
        assert growth["guide_steps"][2]["cta_path"] == "/feed?focus=follow"
    else:
        assert graduation["share_url_path"] == f"/share/{share_resp.json()['token']}"
        assert graduation["cta_path"] == "/leaderboards?kind=paper_mastery"


def test_journey_includes_mastery_graduation_when_path_complete(client, db_session, monkeypatch):
    from backend.app.services import onboarding_service as obs

    seed_sample_market_data(db_session)
    h = _register(client, "gradcoach")
    proj, report = _full_research(client, h, db_session)

    real_goal = obs._mastery_goal_payload

    def boosted_goal(db, user, locale):
        g = real_goal(db, user, locale)
        g["paper_graduated_count"] = 1
        g["paper_tracking_count"] = 1
        g["on_leaderboard"] = True
        g["leaderboard_rank"] = 3
        return g

    monkeypatch.setattr(obs, "_mastery_goal_payload", boosted_goal)

    client.post(f"{BASE}/projects/{proj['id']}/publish", headers=h)
    share_resp = client.post(f"{BASE}/research/reports/{report['id']}/share", headers=h)
    assert share_resp.status_code == 201, share_resp.text

    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j.get("mastery_overview") is None
    grad = j.get("mastery_graduation_coaching")
    assert grad is not None
    assert grad["done_count"] == 5
    assert grad["total"] == 5
    assert grad["paper_graduated_count"] == 1
    assert grad["on_leaderboard"] is True
    assert grad["leaderboard_rank"] == 3
    assert grad["profile_path"] == "/me"
    assert "following" in grad
    assert grad["following"] == 0
    assert grad["share_url_path"].startswith("/share/")
    assert grad["feed_path"].startswith("/feed")
    assert j.get("share_growth_coaching") is None
    assert len(grad.get("guide_steps") or []) == 3
    assert "social_following_count" in j
    assert j["social_following_count"] == 0


def test_journey_includes_checkout_coaching(client, db_session):
    from backend.app.models.user import User
    from backend.app.services import membership_service as ms
    from sqlalchemy import select

    seed_sample_market_data(db_session)
    h = _register(client, "chkcoach")
    user = db_session.execute(select(User).where(User.username == "chkcoach")).scalar_one()
    ms.grant(db_session, user, ms.TIER_PLUS, 30, "plus_monthly")
    client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": "RB"})
    j = client.get(
        f"{BASE}/onboarding/journey",
        headers=h,
        params={"checkout_plan": "plus_monthly"},
    ).json()
    cc = j.get("checkout_coaching")
    assert cc is not None
    assert cc["plan_code"] == "plus_monthly"
    assert j.get("upgrade_coaching") is None
    assert j.get("market_data_coaching") is None


def test_journey_suppresses_market_data_when_upgrade_coaching_wins(client, db_session):
    from backend.app.core.config import get_settings
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    settings = get_settings()
    settings.research_gate_enabled = True
    try:
        seed_sample_market_data(db_session)
        h = _register(client, "coachdedup")
        _full_research(client, h, db_session)
        user = db_session.execute(select(User).where(User.username == "coachdedup")).scalar_one()
        user.level = UserLevel.L4
        db_session.add(user)
        db_session.commit()
        j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
        assert j.get("upgrade_coaching") is not None
        assert j.get("market_data_coaching") is None
    finally:
        settings.research_gate_enabled = False


def test_paper_mastery_board_context_unit(db_session):
    from backend.app.services.leaderboard_service import paper_mastery_board_context
    from backend.app.models.user import User
    import uuid

    user = User(
        id=uuid.uuid4(),
        email="gap@x.com",
        username="gapuser",
        hashed_password="x",
    )
    db_session.add(user)
    db_session.commit()
    ctx = paper_mastery_board_context(db_session, user.id)
    assert ctx["on_leaderboard"] is False
    assert ctx["graduated_needed"] is None
    assert ctx["board_limit"] == 50


def test_public_report_detail(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "pubrep")
    proj, rep = _full_research(client, h, db_session)
    rid = rep["id"]
    assert client.get(f"{BASE}/public/reports/{rid}").status_code == 404
    client.post(f"{BASE}/projects/{proj['id']}/publish", headers=h)
    client.post(f"{BASE}/research/reports/{rid}/share", headers=h)
    pub = client.get(f"{BASE}/public/reports/{rid}").json()
    assert pub["id"] == rid
    assert pub["title"]
    anon = client.get(f"{BASE}/public/reports/{rid}")
    assert anon.status_code == 200


def test_report_seo_preview_and_sitemap(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "seorep")
    proj, rep = _full_research(client, h, db_session)
    rid = rep["id"]
    # 未公开 -> SEO 预览 404
    assert client.get(f"/reports/{rid}").status_code == 404
    client.post(f"{BASE}/projects/{proj['id']}/publish", headers=h)
    client.post(f"{BASE}/research/reports/{rid}/share", headers=h)
    # 公开后 -> 可索引 HTML, 含 OG 标题与 canonical
    page = client.get(f"/reports/{rid}")
    assert page.status_code == 200
    assert 'property="og:title"' in page.text
    assert f"/app/reports/{rid}" in page.text
    assert 'application/ld+json' in page.text
    # sitemap 含该报告
    sm = client.get("/sitemap.xml")
    assert sm.status_code == 200
    assert f"/reports/{rid}" in sm.text
    # robots 指向 sitemap
    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert "Sitemap:" in robots.text


def test_choose_type_updates_user(client, db_session):
    h = _register(client, "oscar")
    out = client.post(f"{BASE}/onboarding/choose-type", headers=h, json={"user_type": "python"}).json()
    assert out["user_type"] == "python"
    assert out["onboarding_done"] is True


# ---------------- 研究模板 ----------------

def test_template_one_click_start(client, db_session):
    seed_sample_market_data(db_session)
    seed_default_templates(db_session)
    h = _register(client, "paula")
    tpls = client.get(f"{BASE}/research/templates", headers=h).json()
    assert any(t["code"] == "gold-trend" for t in tpls)
    res = client.post(f"{BASE}/research/templates/gold-trend/start", headers=h, json={"with_factor": True})
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["factor_id"] is not None
    nxt = client.get(f"{BASE}/onboarding/next", headers=h).json()
    assert nxt["stage"] == "run_backtest"
    assert nxt["active_project_id"] == str(body["project_id"])
    assert nxt["cta_path"] == f"/projects/{body['project_id']}"
    gold = next(t for t in tpls if t["code"] == "gold-trend")
    assert gold.get("learning_steps")
    assert gold.get("factor_note")
    # 因子确实归属新建项目
    f = client.get(f"{BASE}/factors/{body['factor_id']}", headers=h).json()
    assert f["project_id"] == str(body["project_id"])
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    coach = j.get("first_project_coaching")
    assert coach is not None
    assert coach["cta_action"] == "run_backtest"
    assert coach["cta_path"] == f"/projects/{body['project_id']}"
    assert coach.get("factor_name")


def test_journey_first_project_coaching_hides_after_backtest(client, db_session):
    seed_default_templates(db_session)
    seed_sample_market_data(db_session)
    h = _register(client, "projcoach")
    res = client.post(f"{BASE}/research/templates/gold-trend/start", headers=h, json={"with_factor": True}).json()
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j.get("first_project_coaching") is not None
    fid = res["factor_id"]
    client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "AU"})
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j2.get("first_project_coaching") is None


def test_journey_first_backtest_coaching_after_backtest(client, db_session):
    seed_default_templates(db_session)
    seed_sample_market_data(db_session)
    h = _register(client, "btcoach")
    res = client.post(f"{BASE}/research/templates/gold-trend/start", headers=h, json={"with_factor": True}).json()
    fid = res["factor_id"]
    client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "AU"})
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    coach = j.get("first_backtest_coaching")
    assert coach is not None
    assert coach["cta_action"] == "run_validation"
    assert coach["cta_path"] == f"/projects/{res['project_id']}"
    assert j.get("first_project_coaching") is None
    client.post(
        f"{BASE}/validations",
        headers=h,
        json={"factor_id": fid, "symbol": "AU", "oos_ratio": 0.3, "n_splits": 4},
    )
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j2.get("first_backtest_coaching") is None


def test_journey_first_validation_coaching_after_validation(client, db_session):
    seed_default_templates(db_session)
    seed_sample_market_data(db_session)
    h = _register(client, "valcoach")
    res = client.post(f"{BASE}/research/templates/gold-trend/start", headers=h, json={"with_factor": True}).json()
    fid = res["factor_id"]
    client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "AU"})
    client.post(
        f"{BASE}/validations",
        headers=h,
        json={"factor_id": fid, "symbol": "AU", "oos_ratio": 0.3, "n_splits": 4},
    )
    j = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    coach = j.get("first_validation_coaching")
    assert coach is not None
    assert coach["cta_action"] == "generate_report"
    assert coach["cta_path"] == f"/projects/{res['project_id']}"
    assert j.get("first_backtest_coaching") is None
    client.post(f"{BASE}/research/reports/generate", headers=h, json={"project_id": res["project_id"]})
    j2 = client.get(f"{BASE}/onboarding/journey", headers=h).json()
    assert j2.get("first_validation_coaching") is None
    assert j2.get("first_report_coaching") is not None


def test_template_unknown_404(client, db_session):
    h = _register(client, "quill")
    assert client.post(f"{BASE}/research/templates/nope/start", headers=h, json={}).status_code == 404


def test_template_regime_picks(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data
    from backend.app.services.template_service import seed_default_templates

    seed_sample_market_data(db_session)
    seed_default_templates(db_session)
    h = _register(client, "regpick")
    picks = client.get(f"{BASE}/research/templates/regime-picks", headers=h).json()
    assert picks["symbol"] == "RB"
    assert "coach_hint" in picks
    assert isinstance(picks["picks"], list)
    if picks["regime"]:
        assert picks["regime_label"]
        assert len(picks["picks"]) <= 3
        if picks["picks"]:
            first = picks["picks"][0]
            assert "fit_score" in first
            assert "code" in first


def test_template_regime_picks_multi_symbol(client, db_session):
    from backend.app.services.market_data import seed_sample_market_data
    from backend.app.services.template_service import seed_default_templates

    seed_sample_market_data(db_session)
    seed_default_templates(db_session)
    h = _register(client, "regmulti")
    for sym in ("RB", "AU", "IF"):
        picks = client.get(f"{BASE}/research/templates/regime-picks", headers=h, params={"symbol": sym}).json()
        assert picks["symbol"] == sym
        assert "coach_hint" in picks


# ---------------- 分享卡片 ----------------

def test_share_card_public(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "rhea")
    _, rep = _full_research(client, h, db_session)
    share = client.post(f"{BASE}/research/reports/{rep['id']}/share", headers=h)
    assert share.status_code == 201, share.text
    token = share.json()["token"]
    # 公开页免登录可看
    card = client.get(f"{BASE}/share/{token}").json()
    assert card["card"]["researcher"] == "rhea"
    assert card["views"] >= 1


def test_share_html_preview_has_og(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "iris")
    _, rep = _full_research(client, h, db_session)
    token = client.post(f"{BASE}/research/reports/{rep['id']}/share", headers=h).json()["token"]
    html = client.get(f"/share/{token}").text
    assert 'property="og:title"' in html
    assert "/app/share/" in html


def test_seed_public_example_studies(client, db_session):
    from backend.app.services.example_studies_service import seed_public_example_studies

    seed_sample_market_data(db_session)
    out = seed_public_example_studies(db_session)
    assert out["total_examples"] >= 3
    ok = [c for c in out["created"] if c.get("status") in ("published", "shared")]
    assert len(ok) + len(out["skipped"]) >= 3
    feed = client.get(f"{BASE}/public/feed").json()
    seeded_ids = {c["report_id"] for c in ok if c.get("report_id")}
    assert any(str(r["id"]) in seeded_ids for r in feed)


def test_public_feed_no_auth(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "jade")
    proj, rep = _full_research(client, h, db_session)
    client.post(f"{BASE}/projects/{proj['id']}/publish", headers=h)
    client.post(f"{BASE}/research/reports/{rep['id']}/share", headers=h)
    feed = client.get(f"{BASE}/public/feed").json()
    assert isinstance(feed, list)
    assert any(r["id"] == rep["id"] for r in feed)
    card = next(r for r in feed if r["id"] == rep["id"])
    assert card.get("factor_kind") is not None
    assert card.get("timeframe") is not None
    assert "paper_graduated" in card
    assert isinstance(card["paper_graduated"], bool)
    assert isinstance(card.get("paper_tracking"), bool)
    mp = card.get("mastery_path")
    assert mp is not None
    assert mp["total"] == 5
    assert len(mp["phases"]) == 5


def test_public_feed_includes_follow_state_when_authed(client, db_session):
    seed_sample_market_data(db_session)
    ha = _register(client, "feed_a")
    hb = _register(client, "feed_b")
    proj, rep = _full_research(client, ha, db_session)
    client.post(f"{BASE}/projects/{proj['id']}/publish", headers=ha)
    client.post(f"{BASE}/research/reports/{rep['id']}/share", headers=ha)
    owner_id = client.get(f"{BASE}/researchers/me", headers=ha).json()["user_id"]
    feed_guest = client.get(f"{BASE}/public/feed").json()
    card_guest = next(r for r in feed_guest if r["id"] == rep["id"])
    assert card_guest.get("owner_username") == "feed_a"
    assert card_guest.get("is_following") is None

    feed_viewer = client.get(f"{BASE}/public/feed", headers=hb).json()
    card_viewer = next(r for r in feed_viewer if r["id"] == rep["id"])
    assert card_viewer["owner_username"] == "feed_a"
    assert card_viewer["is_following"] is False
    assert card_viewer["owner_id"] == owner_id

    client.post(f"{BASE}/researchers/{owner_id}/follow", headers=hb)
    feed_following = client.get(f"{BASE}/public/feed", headers=hb).json()
    card_following = next(r for r in feed_following if r["id"] == rep["id"])
    assert card_following["is_following"] is True


def test_share_missing_report_404(client, db_session):
    import uuid
    h = _register(client, "seth")
    assert client.post(f"{BASE}/research/reports/{uuid.uuid4()}/share", headers=h).status_code == 404


# ---------------- 关注 + Feed ----------------

def test_follow_and_feed(client, db_session):
    seed_sample_market_data(db_session)
    ha = _register(client, "tom")
    hb = _register(client, "ulysses")
    uid_b = client.get(f"{BASE}/researchers/me", headers=hb).json()["user_id"]
    # B 产出一份公开研究
    _, rep = _full_research(client, hb, db_session)
    client.post(f"{BASE}/research/reports/{rep['id']}/share", headers=hb)  # 置公开
    # A 关注 B
    assert client.post(f"{BASE}/researchers/{uid_b}/follow", headers=ha).status_code == 200
    prof_b = client.get(f"{BASE}/researchers/{uid_b}", headers=ha).json()
    assert prof_b["followers"] == 1 and prof_b["is_following"] is True
    # A 的 feed 看到 B 的研究
    feed = client.get(f"{BASE}/me/feed", headers=ha).json()
    assert any(r["owner_id"] == uid_b for r in feed)
    # 取关
    assert client.delete(f"{BASE}/researchers/{uid_b}/follow", headers=ha).status_code == 204


def test_network_radar_academy_on_third_follow(client, db_session):
    from backend.app.services.task_service import seed_default_tasks

    seed_default_tasks(db_session)
    ha = _register(client, "net_a")
    targets = []
    for name in ("net_b", "net_c", "net_d"):
        hb = _register(client, name)
        targets.append(client.get(f"{BASE}/researchers/me", headers=hb).json()["user_id"])
    rewards = []
    for uid in targets:
        body = client.post(f"{BASE}/researchers/{uid}/follow", headers=ha).json()
        rewards.extend(body.get("academy_rewards") or [])
    assert any(r.get("code") == "network-radar" for r in rewards)


def test_master_replication_academy_on_replication_share(client, db_session):
    from backend.app.services.task_service import seed_default_tasks

    seed_sample_market_data(db_session)
    seed_default_tasks(db_session)
    h = _register(client, "repl_acad")
    proj, rep = _full_research(client, h, db_session)
    client.post(f"{BASE}/projects/{proj['id']}/publish", headers=h)
    out = client.post(
        f"{BASE}/research/reports/{rep['id']}/share",
        headers=h,
        json={"replication_loop": True},
    ).json()
    assert any(r.get("code") == "master-replication" for r in out.get("academy_rewards") or [])
    again = client.post(
        f"{BASE}/research/reports/{rep['id']}/share",
        headers=h,
        json={"replication_loop": True},
    ).json()
    assert not any(r.get("code") == "master-replication" for r in again.get("academy_rewards") or [])


def test_cannot_follow_self(client, db_session):
    h = _register(client, "vera")
    uid = client.get(f"{BASE}/researchers/me", headers=h).json()["user_id"]
    assert client.post(f"{BASE}/researchers/{uid}/follow", headers=h).status_code == 422


# ---------------- 多维榜单 ----------------

def test_leaderboards_kinds(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "wade")
    _full_research(client, h, db_session)
    for kind in ("researcher", "contributor", "newcomer", "improved", "paper_mastery"):
        rows = client.get(f"{BASE}/leaderboards/{kind}", headers=h)
        assert rows.status_code == 200, kind
        anon = client.get(f"{BASE}/leaderboards/{kind}")
        assert anon.status_code == 200, kind
    assert client.get(f"{BASE}/leaderboards/bogus", headers=h).status_code == 404


def test_paper_mastery_cutoff_meta(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "cutoffmeta")
    meta = client.get(f"{BASE}/leaderboards/meta/paper-mastery").json()
    assert meta["board_limit"] == 50
    assert meta["total_ranked"] == 0
    assert meta["cutoff"] is None
    anon = client.get(f"{BASE}/leaderboards/meta/paper-mastery")
    assert anon.status_code == 200

    proj, _ = _full_research(client, h, db_session)
    meta2 = client.get(f"{BASE}/leaderboards/meta/paper-mastery").json()
    assert meta2["total_ranked"] >= 1
    assert meta2["cutoff"] is not None
    assert meta2["cutoff"]["graduated"] >= 1


# ---------------- 邀请裂变 ----------------

def test_referral_activation_rewards_referrer(client, db_session):
    seed_sample_market_data(db_session)
    ha = _register(client, "xena")
    # 被邀请者带 ref=xena 注册
    hb = _register(client, "yuri", ref="xena")
    my_ref = client.get(f"{BASE}/me/referral", headers=ha).json()
    assert my_ref["code"] == "xena" and my_ref["invited"] == 1 and my_ref["activated"] == 0
    # 被邀请者完成首次研究 -> 邀请人激活发奖
    _full_research(client, hb, db_session)
    my_ref2 = client.get(f"{BASE}/me/referral", headers=ha).json()
    assert my_ref2["activated"] == 1
    assert my_ref2["reward_points_earned"] >= 50
    prof_a = client.get(f"{BASE}/researchers/me", headers=ha).json()
    assert prof_a["reward_points"] >= 50


# ---------------- AI 导师 + 埋点 ----------------

def test_ai_mentor_next(client, db_session, monkeypatch):
    monkeypatch.setattr(llm_client, "is_enabled", lambda: False)
    h = _register(client, "zane")
    m = client.get(f"{BASE}/ai/mentor/next", headers=h).json()
    assert m["stage"] == "create_project"
    assert "trading advice" in m["disclaimer"] or "不构成交易建议" in m["disclaimer"]


def test_ai_mentor_includes_regime_pick(client, db_session, monkeypatch):
    from backend.app.services.market_data import seed_sample_market_data
    from backend.app.services.template_service import seed_default_templates

    monkeypatch.setattr(llm_client, "is_enabled", lambda: False)
    seed_sample_market_data(db_session)
    seed_default_templates(db_session)
    h = _register(client, "mentorreg")
    m = client.get(f"{BASE}/ai/mentor/next", headers=h).json()
    assert m.get("regime_pick") is not None
    assert m["regime_pick"]["template_code"] == m["recommended_template"]
    assert m["regime_pick"]["coach_hint"]
    assert m["regime_pick"]["template_title"] in m["message"]
    assert "attention_alerts" in m
    assert isinstance(m["attention_alerts"], list)


def test_event_tracking_anonymous_allowed(client, db_session):
    # 匿名上报 visit
    assert client.post(f"{BASE}/events", json={"event": "visit", "props": {}}).status_code == 204


def test_growth_requires_auth(client):
    assert client.get(f"{BASE}/onboarding/next").status_code == 403
    assert client.get(f"{BASE}/me/referral").status_code == 403
