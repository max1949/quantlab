"""学院任务与因子创建联动。"""

from __future__ import annotations

from backend.app.services.market_data import seed_sample_market_data
from backend.app.services.task_service import seed_default_tasks
from backend.tests.test_growth import BASE, _register


def test_template_factor_auto_completes_task(client, db_session):
    seed_default_tasks(db_session)
    h = _register(client, "acad1")
    # 升到 L1 才能领 use-template-factor
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
