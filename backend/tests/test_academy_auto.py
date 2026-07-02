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
