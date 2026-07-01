"""研究项目 / 图谱 / 项目报告 / Feed 接口测试 (eager 模式)。"""

from __future__ import annotations

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


def _project(client, h, title="黄金趋势研究", symbol="RB"):
    return client.post(
        f"{BASE}/projects",
        headers=h,
        json={"title": title, "symbol": symbol, "question": "趋势是否有延续性?"},
    ).json()


def _factor_in_project(client, h, pid, name="mom", window=20):
    return client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": name, "template_type": "momentum", "params": {"window": window}, "project_id": pid},
    ).json()["id"]


def test_create_project_and_factor_linked(client, db_session):
    h = _register(client, "pia")
    proj = _project(client, h)
    assert proj["status"] == "draft"
    fid = _factor_in_project(client, h, proj["id"])
    # 因子带上 project_id
    f = client.get(f"{BASE}/factors/{fid}", headers=h).json()
    assert f["project_id"] == proj["id"]


def test_project_report_and_graph(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "quentin")
    proj = _project(client, h)
    pid = proj["id"]
    fid = _factor_in_project(client, h, pid)
    client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "RB"})
    client.post(
        f"{BASE}/validations",
        headers=h,
        json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4},
    )

    # 生成项目报告
    rep = client.post(f"{BASE}/research/reports/generate", headers=h, json={"project_id": pid})
    assert rep.status_code == 201, rep.text
    body = rep.json()
    assert body["project_id"] == pid
    assert body["methodology"] and body["risk_analysis"] and body["improvement_suggestion"]
    assert body["grade"] in {"稳健", "中等", "偏弱", "脆弱"}

    # 研究路径图谱: 假设 -> 因子 -> 回测 -> 验证 -> 报告
    g = client.get(f"{BASE}/projects/{pid}/graph", headers=h).json()
    kinds = [n["kind"] for n in g["nodes"]]
    assert "hypothesis" in kinds and "experiment" in kinds
    assert "validation" in kinds and "result" in kinds
    assert len(g["edges"]) >= 3


def test_publish_requires_artifacts(client, db_session):
    h = _register(client, "rosa")
    proj = _project(client, h)
    # 空项目不能发布
    assert client.post(f"{BASE}/projects/{proj['id']}/publish", headers=h).status_code == 422
    _factor_in_project(client, h, proj["id"])
    assert client.post(f"{BASE}/projects/{proj['id']}/publish", headers=h).status_code == 200


def test_generate_report_for_empty_project_422(client, db_session):
    h = _register(client, "sam")
    proj = _project(client, h)
    assert client.post(f"{BASE}/research/reports/generate", headers=h, json={"project_id": proj["id"]}).status_code == 422


def test_feed_lists_public_reports(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "tara")
    proj = _project(client, h)
    fid = _factor_in_project(client, h, proj["id"])
    client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "RB"})
    client.post(f"{BASE}/research/reports/generate", headers=h, json={"project_id": proj["id"]})
    client.post(f"{BASE}/projects/{proj['id']}/publish", headers=h)
    feed = client.get(f"{BASE}/research/feed", headers=h).json()
    assert len(feed) >= 1
    feed_top = client.get(f"{BASE}/research/feed?sort=top", headers=h).json()
    assert len(feed_top) >= 1


def test_other_user_cannot_see_draft_project(client, db_session):
    h1 = _register(client, "ulla")
    proj = _project(client, h1)
    h2 = _register(client, "vince")
    assert client.get(f"{BASE}/projects/{proj['id']}", headers=h2).status_code == 403


def test_projects_require_auth(client):
    assert client.get(f"{BASE}/projects").status_code == 403
