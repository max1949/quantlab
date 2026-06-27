"""竞技系统接口测试 (eager 模式)。

覆盖: 赛季创建 L3 闸门、提交算分、排行榜排序、回填 user.research_score、错误分支、鉴权。
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from backend.app.models.user import User
from backend.app.services.competition_service import seed_default_season
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


def _set_level(db_session, username, level):
    u = db_session.execute(select(User).where(User.username == username)).scalar_one()
    u.level = level
    db_session.commit()


def _validated_factor(client, h, name, template_type="momentum", window=20, symbol="RB"):
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": name, "template_type": template_type, "params": {"window": window}},
    ).json()["id"]
    v = client.post(
        f"{BASE}/validations",
        headers=h,
        json={"factor_id": fid, "symbol": symbol, "oos_ratio": 0.3, "n_splits": 4},
    ).json()
    assert v["status"] == "success"
    return fid, v["id"]


def test_create_season_requires_l3(client, db_session):
    h = _register(client, "rookie")
    # L0 创建赛季 -> 403
    assert client.post(f"{BASE}/seasons", headers=h, json={"name": "S-x"}).status_code == 403
    _set_level(db_session, "rookie", 3)
    assert client.post(f"{BASE}/seasons", headers=h, json={"name": "S-x"}).status_code == 201


def test_submit_and_leaderboard(client, db_session):
    seed_sample_market_data(db_session)
    sid = seed_default_season(db_session)["id"]

    h = _register(client, "alice")
    fid, vid = _validated_factor(client, h, "mom20", window=20)
    resp = client.post(f"{BASE}/seasons/{sid}/submissions", headers=h, json={"validation_id": vid})
    assert resp.status_code == 201, resp.text
    sub = resp.json()
    assert sub["final_score"] == pytest.approx(sub["base_score"] * sub["decay_factor"], abs=0.01)
    assert set(sub["dimensions"]) >= {"oos", "stability", "risk", "cross_symbol", "quality"}

    # 回填 user.research_score
    u = db_session.execute(select(User).where(User.username == "alice")).scalar_one()
    assert u.research_score == sub["final_score"]

    # 排行榜
    lb = client.get(f"{BASE}/seasons/{sid}/leaderboard", headers=h).json()
    assert len(lb) == 1
    assert lb[0]["rank"] == 1 and lb[0]["username"] == "alice"


def test_leaderboard_ordering(client, db_session):
    seed_sample_market_data(db_session)
    sid = seed_default_season(db_session)["id"]
    h = _register(client, "bob")
    # 两个不同因子 -> 两次验证 -> 两次提交, 校验按 final_score 降序
    _, v1 = _validated_factor(client, h, "f-a", window=10)
    _, v2 = _validated_factor(client, h, "f-b", window=40)
    client.post(f"{BASE}/seasons/{sid}/submissions", headers=h, json={"validation_id": v1})
    client.post(f"{BASE}/seasons/{sid}/submissions", headers=h, json={"validation_id": v2})
    lb = client.get(f"{BASE}/seasons/{sid}/leaderboard", headers=h).json()
    assert len(lb) == 2
    assert lb[0]["final_score"] >= lb[1]["final_score"]
    assert [r["rank"] for r in lb] == [1, 2]


def test_submit_duplicate_validation_409(client, db_session):
    seed_sample_market_data(db_session)
    sid = seed_default_season(db_session)["id"]
    h = _register(client, "carol")
    _, vid = _validated_factor(client, h, "dup")
    assert client.post(f"{BASE}/seasons/{sid}/submissions", headers=h, json={"validation_id": vid}).status_code == 201
    assert client.post(f"{BASE}/seasons/{sid}/submissions", headers=h, json={"validation_id": vid}).status_code == 409


def test_submit_unknown_validation_422(client, db_session):
    seed_sample_market_data(db_session)
    sid = seed_default_season(db_session)["id"]
    h = _register(client, "dave")
    fake = "00000000-0000-0000-0000-000000000000"
    assert client.post(f"{BASE}/seasons/{sid}/submissions", headers=h, json={"validation_id": fake}).status_code == 422


def test_seasons_require_auth(client):
    assert client.get(f"{BASE}/seasons").status_code == 403
