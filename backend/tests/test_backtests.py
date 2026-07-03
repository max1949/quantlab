"""回测系统接口测试 (eager 模式, 同步执行)。

覆盖: 数据集列表、创建回测→成功、指标/研究报告/净值、快照绑定、错误分支、鉴权。
"""

from __future__ import annotations

from backend.app.services.market_data import seed_sample_market_data

BASE = "/api/v1"

USER = {"email": "bt@quantlab.ai", "username": "bttester", "password": "s3cret-pass"}


def _auth(client) -> dict:
    client.post(f"{BASE}/auth/register", json=USER)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": USER["username"], "password": USER["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _make_factor(client, h, name="mom") -> str:
    return client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": name, "template_type": "momentum", "params": {"window": 10}},
    ).json()["id"]


def test_datasets_listed_after_seed(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    resp = client.get(f"{BASE}/datasets", headers=h)
    assert resp.status_code == 200
    symbols = {d["symbol"] for d in resp.json()}
    assert {"RB", "AU", "IF"} <= symbols


def test_create_backtest_runs_and_reports(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    fid = _make_factor(client, h)

    resp = client.post(
        f"{BASE}/backtests",
        headers=h,
        json={"factor_id": fid, "symbol": "RB", "fee_rate": 0.0005, "slippage_bps": 1.0},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "success"
    assert body["snapshot_id"]  # 绑定了数据快照
    assert body.get("market_regime", {}).get("regime") in ("low", "mid", "high")
    # 指标齐全
    assert set(body["metrics"]) >= {"sharpe", "max_drawdown", "annual_return", "trade_count"}
    # 研究报告: 假设/方法/结果/结论 + markdown
    rep = body["report"]
    assert set(rep) >= {"hypothesis", "method", "results", "conclusion", "grade", "markdown"}
    assert "研究报告" in rep["markdown"]
    # 净值曲线
    assert isinstance(body["equity_curve"], list) and len(body["equity_curve"]) > 0


def test_backtest_unknown_symbol_404(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    fid = _make_factor(client, h)
    resp = client.post(
        f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "NOPE"}
    )
    assert resp.status_code == 404


def test_backtest_unknown_factor_404(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    fake = "00000000-0000-0000-0000-000000000000"
    resp = client.post(
        f"{BASE}/backtests", headers=h, json={"factor_id": fake, "symbol": "RB"}
    )
    assert resp.status_code == 404


def test_list_and_get_backtest(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    fid = _make_factor(client, h)
    bid = client.post(
        f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "AU"}
    ).json()["id"]

    assert len(client.get(f"{BASE}/backtests", headers=h).json()) == 1
    detail = client.get(f"{BASE}/backtests/{bid}", headers=h)
    assert detail.status_code == 200
    assert detail.json()["symbol"] == "AU"


def test_costs_affect_results(client, db_session):
    h = _auth(client)
    seed_sample_market_data(db_session)
    f1 = _make_factor(client, h, "f-cheap")
    f2 = _make_factor(client, h, "f-pricey")
    cheap = client.post(
        f"{BASE}/backtests", headers=h,
        json={"factor_id": f1, "symbol": "RB", "fee_rate": 0.0, "slippage_bps": 0.0},
    ).json()["metrics"]["total_return"]
    pricey = client.post(
        f"{BASE}/backtests", headers=h,
        json={"factor_id": f2, "symbol": "RB", "fee_rate": 0.01, "slippage_bps": 50.0},
    ).json()["metrics"]["total_return"]
    assert pricey < cheap


def test_backtests_require_auth(client):
    assert client.get(f"{BASE}/backtests").status_code == 403
    assert client.get(f"{BASE}/datasets").status_code == 403
