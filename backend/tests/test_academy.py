"""学院系统接口测试: 任务列表 / 完成 / 经验升级 / 等级闸门 / 幂等。"""

from __future__ import annotations

from backend.app.services.task_service import seed_default_tasks

BASE = "/api/v1"

USER = {
    "email": "rookie@quantlab.ai",
    "username": "rookie",
    "password": "s3cret-pass",
}


def _auth_headers(client) -> dict:
    client.post(f"{BASE}/auth/register", json=USER)
    token = client.post(
        f"{BASE}/auth/login",
        json={"identifier": USER["username"], "password": USER["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_tasks_marks_lock_and_progress(client, db_session):
    seed_default_tasks(db_session)
    h = _auth_headers(client)
    resp = client.get(f"{BASE}/tasks", headers=h)
    assert resp.status_code == 200, resp.text
    tasks = {t["code"]: t for t in resp.json()}
    # L0 用户: L0 任务解锁, 更高等级任务锁定
    assert tasks["welcome"]["locked"] is False
    assert tasks["welcome"]["completed"] is False
    assert tasks["use-template-factor"]["locked"] is True  # min_level L1
    assert tasks["combine-factors"]["locked"] is True  # min_level L2


def test_complete_task_awards_xp_and_levels_up(client, db_session):
    seed_default_tasks(db_session)
    h = _auth_headers(client)

    # welcome: +50 -> exp 50, 仍 L0
    r1 = client.post(f"{BASE}/tasks/welcome/complete", headers=h).json()
    assert r1["awarded_xp"] == 50
    assert r1["leveled_up"] is False
    assert r1["user"]["experience"] == 50
    assert r1["user"]["level"] == 0

    # first-observation: +50 -> exp 100 -> 升到 L1
    r2 = client.post(
        f"{BASE}/tasks/first-observation/complete", headers=h
    ).json()
    assert r2["user"]["experience"] == 100
    assert r2["leveled_up"] is True
    assert r2["user"]["level"] == 1
    assert r2["previous_level"] == 0


def test_complete_is_idempotent(client, db_session):
    seed_default_tasks(db_session)
    h = _auth_headers(client)
    assert client.post(f"{BASE}/tasks/welcome/complete", headers=h).status_code == 200
    # 再次完成 -> 409
    assert client.post(f"{BASE}/tasks/welcome/complete", headers=h).status_code == 409


def test_level_gate_blocks_high_level_task(client, db_session):
    seed_default_tasks(db_session)
    h = _auth_headers(client)
    # L0 用户尝试完成 min_level=L2 的任务 -> 403
    resp = client.post(f"{BASE}/tasks/combine-factors/complete", headers=h)
    assert resp.status_code == 403


def test_unlock_after_levelup(client, db_session):
    seed_default_tasks(db_session)
    h = _auth_headers(client)
    # 先升到 L1
    client.post(f"{BASE}/tasks/welcome/complete", headers=h)
    client.post(f"{BASE}/tasks/first-observation/complete", headers=h)
    # 现在可完成 L1 任务 use-template-factor (+100 -> exp 200, 仍 L1)
    r = client.post(f"{BASE}/tasks/use-template-factor/complete", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["experience"] == 200
    assert body["user"]["level"] == 1
    assert body["user"]["experience_to_next_level"] == 100  # 距 L2(300)


def test_complete_unknown_task_404(client, db_session):
    seed_default_tasks(db_session)
    h = _auth_headers(client)
    assert (
        client.post(f"{BASE}/tasks/nope/complete", headers=h).status_code == 404
    )


def test_tasks_require_auth(client, db_session):
    seed_default_tasks(db_session)
    assert client.get(f"{BASE}/tasks").status_code == 403
