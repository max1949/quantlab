"""研究质量闸门 + vn.py 导入测试。"""

from __future__ import annotations

from backend.app.services import market_data, research_quality_service as rq
from backend.tests.test_growth import BASE, _full_research, _register
from backend.app.services.market_data import seed_sample_market_data


def test_project_quality_endpoint(client, db_session):
    from backend.app.core.config import get_settings

    settings = get_settings()
    settings.research_gate_enabled = True
    try:
        seed_sample_market_data(db_session)
        h = _register(client, "quinn")
        proj = client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": "RB"}).json()
        q = client.get(f"{BASE}/projects/{proj['id']}/quality", headers=h).json()
        assert q["passed"] is False
        assert q["reasons"]
    finally:
        settings.research_gate_enabled = False


def test_vnpy_import_roundtrip(db_session, tmp_path):
    import sqlite3

    db_path = tmp_path / "vn.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE dbbardata (
        id INTEGER PRIMARY KEY, symbol TEXT, exchange TEXT, datetime TEXT, interval TEXT,
        volume REAL, turnover REAL, open_interest REAL,
        open_price REAL, high_price REAL, low_price REAL, close_price REAL)"""
    )
    conn.executemany(
        "INSERT INTO dbbardata VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (1, "RB99", "SHFE", "2024-01-02 09:00:00", "1m", 100, 0, 5000, 100, 101, 99, 100.5),
            (2, "RB99", "SHFE", "2024-01-02 09:01:00", "1m", 120, 0, 5010, 100.5, 102, 100, 101.5),
        ],
    )
    conn.commit()
    conn.close()

    info = market_data.import_vnpy_sqlite(db_session, db_path, symbol="RB99", interval="1m")
    assert info["rows"] == 2
    assert {d["timeframe"] for d in info["derived"]} >= {"5m", "15m"}
    df = market_data.load_ohlcv("RB99", "1m")
    assert "open_interest" in df.columns
    derived = market_data.materialize_derived_timeframes(db_session, ["RB99"])
    assert {d["timeframe"] for d in derived["datasets"]} >= {"5m", "15m"}
    assert market_data.get_dataset(db_session, "RB99", "5m") is not None


def test_publish_blocked_when_gate_enabled(client, db_session):
    from backend.app.core.config import get_settings

    settings = get_settings()
    settings.research_gate_enabled = True
    try:
        seed_sample_market_data(db_session)
        h = _register(client, "pax")
        proj = client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": "RB"}).json()
        fid = client.post(
            f"{BASE}/factors/template", headers=h,
            json={"name": "f", "template_type": "momentum", "params": {"window": 20}, "project_id": proj["id"]},
        ).json()["id"]
        client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "RB"})
        r = client.post(f"{BASE}/projects/{proj['id']}/publish", headers=h)
        assert r.status_code == 422
    finally:
        settings.research_gate_enabled = False
