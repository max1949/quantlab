"""因子参数扫描 API 测试。"""

from __future__ import annotations

from backend.app.services.market_data import seed_sample_market_data
from backend.app.services.task_service import seed_default_tasks
from backend.tests.test_growth import BASE, _register


def test_factor_scan_run_and_apply(client, db_session):
    seed_default_tasks(db_session)
    seed_sample_market_data(db_session)
    h = _register(client, "scan1")
    # L1 for factor_param_scan
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    user = db_session.execute(select(User).where(User.username == "scan1")).scalar_one()
    user.level = UserLevel.L1
    user.experience = 100
    db_session.commit()

    proj = client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": "RB"}).json()
    scan = client.post(
        f"{BASE}/factors/scan",
        headers=h,
        json={
            "symbol": "RB",
            "template_type": "momentum",
            "timeframe": "1d",
            "project_id": proj["id"],
            "steps": 6,
        },
    )
    assert scan.status_code == 201, scan.text
    body = scan.json()
    assert body["results"]
    assert body["best_params"]
    assert body["coach_summary"]
    top = body["results"][0]
    assert "publish_hints" in top
    assert "publish_promising" in top
    sid = body["id"]
    assert any(r.get("code") == "first-factor-scan" for r in body.get("academy_rewards", []))

    applied = client.post(
        f"{BASE}/factors/scans/{sid}/apply",
        headers=h,
        json={"rank": 1, "name": "scan-best"},
    )
    assert applied.status_code == 200, applied.text
    assert applied.json()["name"] == "scan-best"

    lst = client.get(f"{BASE}/factors/scans", headers=h)
    assert lst.status_code == 200
    assert any(s["id"] == sid for s in lst.json())
    assert lst.json()[0].get("project_title") is not None

    filtered = client.get(
        f"{BASE}/factors/scans",
        headers=h,
        params={"symbol": "RB", "template_type": "momentum", "limit": 10},
    )
    assert filtered.status_code == 200
    assert all(s["symbol"] == "RB" for s in filtered.json())

    scan2 = client.post(
        f"{BASE}/factors/scan",
        headers=h,
        json={
            "symbol": "RB",
            "template_type": "mean_reversion",
            "timeframe": "1d",
            "project_id": proj["id"],
            "steps": 6,
        },
    )
    assert scan2.status_code == 201
    sid2 = scan2.json()["id"]

    cmp_res = client.get(
        f"{BASE}/factors/scans/compare",
        headers=h,
        params={"scan_a": sid, "scan_b": sid2},
    )
    assert cmp_res.status_code == 200, cmp_res.text
    assert cmp_res.json()["winner"] in {"a", "b", "tie"}

    ai_res = client.post(f"{BASE}/ai/scans/{sid}/review", headers=h)
    assert ai_res.status_code == 201, ai_res.text
    assert ai_res.json()["content"]


def test_factor_scan_requires_l1(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "scan0")
    res = client.post(
        f"{BASE}/factors/scan",
        headers=h,
        json={"symbol": "RB", "template_type": "momentum", "timeframe": "1d"},
    )
    assert res.status_code == 403


def test_multi_symbol_scan(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "ms1")
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    user = db_session.execute(select(User).where(User.username == "ms1")).scalar_one()
    user.level = UserLevel.L1
    user.experience = 100
    db_session.commit()

    res = client.post(
        f"{BASE}/factors/scan",
        headers=h,
        json={
            "symbol": "RB",
            "symbols": ["RB", "AU"],
            "template_type": "momentum",
            "timeframe": "1d",
            "steps": 6,
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert "RB,AU" == body["symbol"] or "AU,RB" in body["symbol"] or "," in body["symbol"]
    assert body["results"][0].get("symbol_breakdown")


def test_batch_scan_ai_review(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "batch1")
    from backend.app.models.user import User, UserLevel
    from sqlalchemy import select

    user = db_session.execute(select(User).where(User.username == "batch1")).scalar_one()
    user.level = UserLevel.L1
    user.experience = 100
    db_session.commit()

    ids = []
    for tpl in ("momentum", "mean_reversion"):
        r = client.post(
            f"{BASE}/factors/scan",
            headers=h,
            json={"symbol": "RB", "template_type": tpl, "timeframe": "1d", "steps": 6},
        )
        assert r.status_code == 201
        ids.append(r.json()["id"])
    batch = client.post(
        f"{BASE}/ai/scans/review-batch",
        headers=h,
        json={"scan_ids": ids},
    )
    assert batch.status_code == 201, batch.text
    assert batch.json()["content"]
