"""研究生态测试: 研究员主页 / AI 研究指导 / 30 天挑战。"""

from __future__ import annotations

from backend.app.services import llm_client
from backend.app.services.challenge_service import seed_default_challenge
from backend.app.services.market_data import seed_sample_market_data

BASE = "/api/v1"


def _register(client, username):
    client.post(
        f"{BASE}/auth/register",
        json={"email": f"{username}@quantlab.ai", "username": username, "password": "s3cret-pass"},
    )
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": username, "password": "s3cret-pass"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


# ---------------- 研究员主页 ----------------

def test_profile_counts(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "wendy")
    proj = client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": "RB"}).json()
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "mom", "template_type": "momentum", "params": {"window": 20}, "project_id": proj["id"]},
    ).json()["id"]
    client.post(f"{BASE}/validations", headers=h, json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4})

    prof = client.get(f"{BASE}/researchers/me", headers=h).json()
    assert prof["username"] == "wendy"
    assert prof["project_count"] == 1
    assert prof["factor_count"] == 1
    assert prof["validation_count"] == 1
    assert any(t in prof["tags"] for t in ("动量因子", "Momentum"))


def test_profile_other_user_visible(client, db_session):
    h1 = _register(client, "xander")
    uid = client.get(f"{BASE}/researchers/me", headers=h1).json()["user_id"]
    h2 = _register(client, "yuki")
    resp = client.get(f"{BASE}/researchers/{uid}", headers=h2)
    assert resp.status_code == 200
    assert resp.json()["username"] == "xander"


# ---------------- AI 研究指导 ----------------

def test_ai_research_plan_local(client, db_session, monkeypatch):
    monkeypatch.setattr(llm_client, "is_enabled", lambda: False)
    h = _register(client, "zoe")
    body = client.post(f"{BASE}/ai/research-plan", headers=h, json={"theme": "黄金"}).json()
    assert body["kind"] == "research_plan"
    assert body["source"] == "local"
    assert "hypotheses" in body["analysis"]
    assert "不构成" in body["content"]


# ---------------- 30 天挑战 ----------------

def test_challenge_progress_auto(client, db_session):
    seed_sample_market_data(db_session)
    seed_default_challenge(db_session)
    h = _register(client, "abby")

    # 报名时还没产物 -> 0 完成
    prog = client.post(f"{BASE}/challenges/30d-research/enroll", headers=h).json()
    assert prog["total"] == 8
    assert prog["completed_count"] == 0
    assert any(r["code"] == "challenge-enroll" for r in prog.get("academy_rewards", []))
    again = client.post(f"{BASE}/challenges/30d-research/enroll", headers=h).json()
    assert not again.get("academy_rewards")

    # 造因子 -> first_factor 自动完成
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "mom", "template_type": "momentum", "params": {"window": 20}},
    ).json()["id"]
    prog = client.get(f"{BASE}/challenges/30d-research/progress", headers=h).json()
    done = {m["code"] for m in prog["milestones"] if m["completed"]}
    assert "first_factor" in done
    assert prog["completed_count"] >= 1
    first_ms = next(m for m in prog["milestones"] if m["code"] == "first_factor")
    assert first_ms.get("journey_key") == "factor"
    assert first_ms.get("journey_label")


def test_challenge_paper_milestones_auto(client, db_session):
    from backend.app.models.user import User, UserLevel
    from backend.app.services import membership_service as ms
    from sqlalchemy import select

    seed_sample_market_data(db_session)
    seed_default_challenge(db_session)
    h = _register(client, "paperch")
    user = db_session.execute(select(User).where(User.username == "paperch")).scalar_one()
    user.level = UserLevel.L4.value
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")

    client.post(f"{BASE}/challenges/30d-research/enroll", headers=h)
    proj = client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": "RB"}).json()
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "m", "template_type": "momentum", "params": {"window": 20}, "project_id": proj["id"]},
    ).json()["id"]
    client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "RB"})
    client.post(f"{BASE}/validations", headers=h, json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4})

    prog = client.get(f"{BASE}/challenges/30d-research/progress", headers=h).json()
    done_before = {m["code"] for m in prog["milestones"] if m["completed"]}
    assert "paper_graduated" in done_before

    created = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={"symbol": "RB", "side": "buy", "notional_cny": 50000, "factor_id": fid},
    )
    assert created.status_code == 201, created.text

    prog2 = client.get(f"{BASE}/challenges/30d-research/progress", headers=h).json()
    done = {m["code"] for m in prog2["milestones"] if m["completed"]}
    assert "first_paper_order" in done
    paper_ms = next(m for m in prog2["milestones"] if m["code"] == "first_paper_order")
    assert paper_ms.get("mastery_stage") == "paper"
    assert paper_ms.get("mastery_stage_label")


def test_challenge_list_and_unknown(client, db_session):
    seed_default_challenge(db_session)
    h = _register(client, "bella")
    lst = client.get(f"{BASE}/challenges", headers=h).json()
    assert any(c["code"] == "30d-research" for c in lst)
    assert client.get(f"{BASE}/challenges/nope/progress", headers=h).status_code == 404


def test_ecosystem_requires_auth(client):
    assert client.get(f"{BASE}/researchers/me").status_code == 403
    assert client.get(f"{BASE}/challenges").status_code == 403
