"""行情数据分级策略测试。"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import select

from backend.app.models.user import User
from backend.app.services import market_data, membership_service as ms
from backend.app.services import market_data_policy as mdp

BASE = "/api/v1"

USER = {"email": "mdp@quantlab.ai", "username": "mdpuser", "password": "s3cret-pass"}


def _auth(client) -> dict:
    client.post(f"{BASE}/auth/register", json=USER)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": USER["username"], "password": USER["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _user(db_session) -> User:
    return db_session.execute(
        select(User).where(User.username == USER["username"])
    ).scalar_one()


def test_free_tier_daily_only_and_capped(client, db_session):
    h = _auth(client)
    seed = market_data.seed_sample_market_data(db_session)
    df_1m = market_data.generate_sample_ohlcv("RB", n=10_000)
    market_data.register_dataset(db_session, "RB", df_1m, "1m")

    resp = client.get(f"{BASE}/datasets", headers=h)
    assert resp.status_code == 200
    rows = resp.json()
    tfs = {d["timeframe"] for d in rows if d["symbol"] == "RB"}
    assert tfs == {"1d"}
    rb_1d = next(d for d in rows if d["symbol"] == "RB" and d["timeframe"] == "1d")
    assert rb_1d["effective_rows"] == 252
    assert rb_1d["tier_cap"] == 252
    assert rb_1d["rows"] == seed["datasets"][0]["rows"]


def test_free_user_cannot_backtest_1m(client, db_session):
    h = _auth(client)
    market_data.seed_sample_market_data(db_session)
    df_1m = market_data.generate_sample_ohlcv("RB", n=1000)
    market_data.register_dataset(db_session, "RB", df_1m, "1m")
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "m", "template_type": "momentum", "params": {"window": 5}},
    ).json()["id"]
    resp = client.post(
        f"{BASE}/backtests",
        headers=h,
        json={"factor_id": fid, "symbol": "RB", "timeframe": "1m"},
    )
    assert resp.status_code == 403


def test_plus_tier_gets_minute_and_longer_daily(client, db_session):
    h = _auth(client)
    market_data.seed_sample_market_data(db_session)
    n = 60_000
    idx = pd.date_range("2023-01-02", periods=n, freq="min")
    df_1m = pd.DataFrame({"close": range(n)}, index=idx)
    df_1m["open"] = df_1m["close"]
    df_1m["high"] = df_1m["close"]
    df_1m["low"] = df_1m["close"]
    df_1m["volume"] = 1000
    market_data.register_dataset(db_session, "RB", df_1m, "1m")
    user = _user(db_session)
    ms.grant(db_session, user, tier=1, period_days=30, plan_code="plus_monthly", source="test")

    resp = client.get(f"{BASE}/datasets", headers=h)
    tfs = {d["timeframe"] for d in resp.json() if d["symbol"] == "RB"}
    assert tfs == {"1d", "1m"}
    rb_1m = next(d for d in resp.json() if d["symbol"] == "RB" and d["timeframe"] == "1m")
    assert rb_1m["effective_rows"] == 50_000
    assert rb_1m["tier_cap"] == 50_000


def test_trim_and_effective_rows():
    df = pd.DataFrame({"close": range(1000)})
    trimmed = mdp.trim_ohlcv(df, 252)
    assert len(trimmed) == 252
    assert mdp.effective_rows(1000, 0, "1d") == 252
    assert mdp.effective_rows(1000, 2, "1m") == 1000


def test_load_ohlcv_tail_reads_only_recent_rows(db_session, tmp_path):
    from backend.app.core.config import get_settings

    settings = get_settings()
    prev = settings.market_data_dir
    settings.market_data_dir = str(tmp_path)
    try:
        n = 60_000
        cap = 50_000
        idx = pd.date_range("2023-01-02", periods=n, freq="min")
        df = pd.DataFrame(
            {
                "open": range(n),
                "high": range(n),
                "low": range(n),
                "close": range(n),
                "volume": 1000,
            },
            index=idx,
        )
        path = market_data.dataset_path("RB", "1m")
        df.to_parquet(path)
        loaded = market_data.load_ohlcv("RB", "1m", max_rows=cap)
        assert len(loaded) == cap
        assert int(loaded["close"].iloc[0]) == n - cap
    finally:
        settings.market_data_dir = prev


def test_expired_tier_blocks_paper_preview(client, db_session):
    h = _auth(client)
    market_data.seed_sample_market_data(db_session)
    n = 500
    idx = pd.date_range("2023-01-02", periods=n, freq="min")
    df_1m = pd.DataFrame(
        {"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1000},
        index=idx,
    )
    df_1m.to_parquet(market_data.dataset_path("RB", "1m"))
    market_data.register_dataset(db_session, "RB", df_1m, "1m")
    user = _user(db_session)
    ms.grant(db_session, user, tier=1, period_days=30, plan_code="plus_monthly", source="test")
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "m", "template_type": "momentum", "params": {"window": 5}},
    ).json()["id"]
    resp = client.post(
        f"{BASE}/validations",
        headers=h,
        json={"factor_id": fid, "symbol": "RB", "timeframe": "1m"},
    )
    assert resp.status_code == 201
    # 模拟会员过期: 删除订阅
    from backend.app.models.membership import Subscription

    for sub in db_session.execute(__import__("sqlalchemy").select(Subscription)).scalars():
        db_session.delete(sub)
    db_session.commit()
    prev = client.get(f"{BASE}/factors/{fid}/paper-preview", headers=h)
    assert prev.status_code == 403
