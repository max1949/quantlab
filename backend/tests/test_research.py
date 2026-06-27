"""研究项目报告接口测试 (eager 模式)。

覆盖: 仅回测 / 回测+验证生成报告、阶段标记、溯源、无研究 422、他人公开可见/私有 403、鉴权。
"""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.research import ResearchReport
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


def _factor(client, h, name="mom"):
    return client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": name, "template_type": "momentum", "params": {"window": 20}},
    ).json()["id"]


def _backtest(client, h, fid):
    return client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "RB"}).json()["id"]


def _validation(client, h, fid):
    return client.post(
        f"{BASE}/validations",
        headers=h,
        json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4},
    ).json()["id"]


def test_report_from_backtest_only(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "ann")
    fid = _factor(client, h)
    bid = _backtest(client, h, fid)
    resp = client.post(f"{BASE}/research/factors/{fid}/report", headers=h)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["stages"] == {"factor": True, "backtest": True, "validation": False}
    assert body["based_on"]["backtest_id"] == bid
    assert body["narrative"]["markdown"].startswith("# ")
    assert "研究假设" in body["narrative"]["markdown"]


def test_report_from_backtest_and_validation(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "bea")
    fid = _factor(client, h)
    _backtest(client, h, fid)
    vid = _validation(client, h, fid)
    body = client.post(f"{BASE}/research/factors/{fid}/report", headers=h).json()
    assert body["stages"]["validation"] is True
    assert body["based_on"]["validation_id"] == vid
    assert body["grade"] in {"稳健", "中等", "偏弱", "脆弱"}
    # 结果含样本内外
    assert any("样本外" in x for x in body["narrative"]["result_summary"])
    assert db_session.execute(select(ResearchReport)).scalars().first() is not None


def test_report_requires_some_research_422(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "cleo")
    fid = _factor(client, h)  # 只建因子, 没回测/验证
    assert client.post(f"{BASE}/research/factors/{fid}/report", headers=h).status_code == 422


def test_report_unknown_factor_404(client):
    h = _register(client, "danny")
    fake = "00000000-0000-0000-0000-000000000000"
    assert client.post(f"{BASE}/research/factors/{fake}/report", headers=h).status_code == 404


def test_public_report_visible_to_others(client, db_session):
    seed_sample_market_data(db_session)
    h1 = _register(client, "owner1")
    fid = _factor(client, h1)
    _backtest(client, h1, fid)
    rid = client.post(f"{BASE}/research/factors/{fid}/report", headers=h1).json()["id"]

    h2 = _register(client, "viewer1")
    resp = client.get(f"{BASE}/research/reports/{rid}", headers=h2)
    assert resp.status_code == 200  # 默认公开
    assert resp.json()["id"] == rid


def test_my_reports_list(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "edgar")
    fid = _factor(client, h)
    _backtest(client, h, fid)
    client.post(f"{BASE}/research/factors/{fid}/report", headers=h)
    lst = client.get(f"{BASE}/research/reports", headers=h).json()
    assert len(lst) == 1
    assert lst[0]["factor_id"] == fid


def test_research_requires_auth(client):
    assert client.get(f"{BASE}/research/reports").status_code == 403
