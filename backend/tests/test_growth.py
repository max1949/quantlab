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


def test_choose_type_updates_user(client, db_session):
    h = _register(client, "oscar")
    out = client.post(f"{BASE}/onboarding/choose-type", headers=h, json={"user_type": "python"}).json()
    assert out["user_type"] == "python"
    assert out["onboarding_done"] is True


# ---------------- 研究模板 ----------------

def test_template_one_click_start(client, db_session):
    seed_default_templates(db_session)
    h = _register(client, "paula")
    tpls = client.get(f"{BASE}/research/templates", headers=h).json()
    assert any(t["code"] == "gold-trend" for t in tpls)
    res = client.post(f"{BASE}/research/templates/gold-trend/start", headers=h, json={"with_factor": True})
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["factor_id"] is not None
    # 因子确实归属新建项目
    f = client.get(f"{BASE}/factors/{body['factor_id']}", headers=h).json()
    assert f["project_id"] == str(body["project_id"])


def test_template_unknown_404(client, db_session):
    h = _register(client, "quill")
    assert client.post(f"{BASE}/research/templates/nope/start", headers=h, json={}).status_code == 404


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
    assert client.post(f"{BASE}/researchers/{uid_b}/follow", headers=ha).status_code == 204
    prof_b = client.get(f"{BASE}/researchers/{uid_b}", headers=ha).json()
    assert prof_b["followers"] == 1 and prof_b["is_following"] is True
    # A 的 feed 看到 B 的研究
    feed = client.get(f"{BASE}/me/feed", headers=ha).json()
    assert any(r["owner_id"] == uid_b for r in feed)
    # 取关
    assert client.delete(f"{BASE}/researchers/{uid_b}/follow", headers=ha).status_code == 204


def test_cannot_follow_self(client, db_session):
    h = _register(client, "vera")
    uid = client.get(f"{BASE}/researchers/me", headers=h).json()["user_id"]
    assert client.post(f"{BASE}/researchers/{uid}/follow", headers=h).status_code == 422


# ---------------- 多维榜单 ----------------

def test_leaderboards_kinds(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "wade")
    _full_research(client, h, db_session)
    for kind in ("researcher", "contributor", "newcomer", "improved"):
        rows = client.get(f"{BASE}/leaderboards/{kind}", headers=h)
        assert rows.status_code == 200, kind
    assert client.get(f"{BASE}/leaderboards/bogus", headers=h).status_code == 404


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
    assert "不构成交易建议" in m["disclaimer"]


def test_event_tracking_anonymous_allowed(client, db_session):
    # 匿名上报 visit
    assert client.post(f"{BASE}/events", json={"event": "visit", "props": {}}).status_code == 204


def test_growth_requires_auth(client):
    assert client.get(f"{BASE}/onboarding/next").status_code == 403
    assert client.get(f"{BASE}/me/referral").status_code == 403
    assert client.get(f"{BASE}/leaderboards/researcher").status_code == 403
