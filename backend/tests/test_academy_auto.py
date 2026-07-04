"""学院任务与因子创建联动。"""

from __future__ import annotations

from backend.app.services.market_data import seed_sample_market_data
from backend.app.services.task_service import seed_default_tasks
from backend.app.services.template_service import seed_default_templates
from backend.tests.test_growth import BASE, _register


def test_template_factor_auto_completes_task(client, db_session):
    seed_default_tasks(db_session)
    h = _register(client, "acad1")
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    user = db_session.execute(select(User).where(User.username == "acad1")).scalar_one()
    user.level = UserLevel.L1
    user.experience = 100
    db_session.commit()

    client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "m", "template_type": "momentum", "params": {"window": 20}},
    )
    tasks = {t["code"]: t for t in client.get(f"{BASE}/tasks", headers=h).json()}
    assert tasks["use-template-factor"]["completed"] is True


def test_first_backtest_auto_completes_academy_tasks(client, db_session):
    seed_default_tasks(db_session)
    seed_sample_market_data(db_session)
    h = _register(client, "acad_bt")
    proj = client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": "RB"}).json()
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={
            "name": "f1",
            "template_type": "momentum",
            "params": {"window": 20},
            "project_id": proj["id"],
        },
    ).json()["id"]
    bt = client.post(
        f"{BASE}/backtests",
        headers=h,
        json={"factor_id": fid, "symbol": "RB"},
    )
    assert bt.status_code == 201, bt.text
    body = bt.json()
    if body["status"] == "success":
        assert any(r["code"] == "first-backtest" for r in body.get("academy_rewards", []))
    tasks = {t["code"]: t for t in client.get(f"{BASE}/tasks", headers=h).json()}
    assert tasks["first-backtest"]["completed"] is True


def test_factor_preview_auto_completes_first_observation(client, db_session):
    seed_default_tasks(db_session)
    h = _register(client, "acad_pv")
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "pv", "template_type": "momentum", "params": {"window": 10}},
    ).json()["id"]
    res = client.post(f"{BASE}/factors/{fid}/preview", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    assert any(r["code"] == "first-observation" for r in body.get("academy_rewards", []))
    tasks = {t["code"]: t for t in client.get(f"{BASE}/tasks", headers=h).json()}
    assert tasks["first-observation"]["completed"] is True


def test_template_start_auto_welcome(client, db_session):
    seed_default_tasks(db_session)
    seed_default_templates(db_session)
    h = _register(client, "acad_wel")
    out = client.post(
        f"{BASE}/research/templates/gold-trend/start",
        headers=h,
        json={"with_factor": True},
    ).json()
    assert out["project_id"]
    tasks = {t["code"]: t for t in client.get(f"{BASE}/tasks", headers=h).json()}
    assert tasks["welcome"]["completed"] is True


def test_first_report_auto_completes(client, db_session):
    from backend.tests.test_growth import _full_research

    seed_default_tasks(db_session)
    seed_sample_market_data(db_session)
    h = _register(client, "acad_rep")
    proj, rep = _full_research(client, h, db_session)
    assert any(r["code"] == "first-report" for r in rep.get("academy_rewards", []))
    tasks = {t["code"]: t for t in client.get(f"{BASE}/tasks", headers=h).json()}
    assert tasks["first-report"]["completed"] is True


def test_first_publish_auto_completes(client, db_session):
    from backend.tests.test_growth import _full_research

    seed_default_tasks(db_session)
    seed_sample_market_data(db_session)
    h = _register(client, "acad_pub")
    proj, _ = _full_research(client, h, db_session)
    pid = proj["id"]
    pub = client.post(f"{BASE}/projects/{pid}/publish", headers=h)
    assert pub.status_code == 200, pub.text
    body = pub.json()
    assert any(r["code"] == "first-publish" for r in body.get("academy_rewards", []))
    tasks = {t["code"]: t for t in client.get(f"{BASE}/tasks", headers=h).json()}
    assert tasks["first-publish"]["completed"] is True


def test_first_share_auto_completes(client, db_session):
    from backend.tests.test_growth import _full_research

    seed_default_tasks(db_session)
    seed_sample_market_data(db_session)
    h = _register(client, "acad_sh")
    proj, rep = _full_research(client, h, db_session)
    pub = client.post(f"{BASE}/projects/{proj['id']}/publish", headers=h)
    assert pub.status_code == 200, pub.text
    share = client.post(f"{BASE}/research/reports/{rep['id']}/share", headers=h)
    assert share.status_code == 201, share.text
    body = share.json()
    assert any(r["code"] == "first-share" for r in body.get("academy_rewards", []))
    tasks = {t["code"]: t for t in client.get(f"{BASE}/tasks", headers=h).json()}
    assert tasks["first-share"]["completed"] is True
    # Re-share should not re-award XP
    again = client.post(f"{BASE}/research/reports/{rep['id']}/share", headers=h)
    assert again.status_code == 201, again.text
    assert not again.json().get("academy_rewards")


def test_tasks_include_mastery_stage(client, db_session):
    seed_default_tasks(db_session)
    h = _register(client, "acad_ms")
    tasks = client.get(f"{BASE}/tasks", headers=h).json()
    by_code = {t["code"]: t for t in tasks}
    assert by_code["first-backtest"]["mastery_stage"] == "backtest"
    assert by_code["first-paper-order"]["mastery_stage"] == "paper"


def test_first_paper_order_auto_completes_academy(client, db_session):
    from backend.app.models.user import User, UserLevel
    from backend.app.services import membership_service as ms
    from backend.app.services.market_data import seed_sample_market_data
    from sqlalchemy import select

    seed_default_tasks(db_session)
    seed_sample_market_data(db_session)
    h = _register(client, "acad_po")
    user = db_session.execute(select(User).where(User.username == "acad_po")).scalar_one()
    user.level = UserLevel.L4
    db_session.commit()
    ms.grant(db_session, user, ms.TIER_PRO, 30, "pro_monthly")

    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "po", "template_type": "momentum", "params": {"window": 10}},
    ).json()["id"]
    created = client.post(
        f"{BASE}/execution/paper/orders",
        headers=h,
        json={"symbol": "RB", "side": "buy", "notional_cny": 50000, "factor_id": fid},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert any(r["code"] == "first-paper-order" for r in body.get("academy_rewards", []))
    tasks = {t["code"]: t for t in client.get(f"{BASE}/tasks", headers=h).json()}
    assert tasks["first-paper-order"]["completed"] is True
