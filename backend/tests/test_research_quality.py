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
        assert "paper_ready" in q
        assert "mastery" in q
        assert q["mastery"]["stage"] == "start"
        assert "academy_milestones" in q
        assert isinstance(q["academy_milestones"], list)
        assert "feed_preview" in q
        assert "publish_ready" in q["feed_preview"]
    finally:
        settings.research_gate_enabled = False


def test_project_quality_includes_regime_fit(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "regqual")
    proj, _ = _full_research(client, h, db_session)
    q = client.get(f"{BASE}/projects/{proj['id']}/quality", headers=h).json()
    assert q.get("regime") is not None
    assert q["regime"].get("fit_score") is not None
    assert q["regime"].get("strategy_style")
    assert q["regime"].get("regime_label")


def test_paper_readiness_stricter_than_publish():
    from engine.research_quality import assess_paper_readiness, assess_publish_readiness

    metrics = {"sharpe": 0.2, "turnover": 70.0}
    oos = {"out_of_sample": {"sharpe": 0.3}}
    rob = {
        "score": 56.0,
        "grade": "中等",
        "factor_ic": {"ic_mean": 0.03},
        "sealed_holdout": {"metrics": {"sharpe": 0.1}},
    }
    pub = assess_publish_readiness(
        backtest_metrics=metrics,
        validation_status="success",
        validation_oos=oos,
        validation_robustness=rob,
    )
    paper = assess_paper_readiness(
        backtest_metrics=metrics,
        validation_status="success",
        validation_oos=oos,
        validation_robustness=rob,
        regime_fit_score=30,
    )
    assert pub.passed is True
    assert paper.passed is False
    assert any("换手" in r or "turnover" in r.lower() or "适配" in r for r in paper.reasons)


def test_mastery_stage_progression():
    from backend.app.services.research_quality_service import compute_mastery_stage

    s0 = compute_mastery_stage(
        has_factor=True,
        has_backtest=False,
        has_validation=False,
        publish_passed=False,
        paper_passed=False,
        has_paper_order=False,
        is_published=False,
    )
    assert s0["stage"] == "start"
    assert s0["next_action"] == "backtest"

    s3 = compute_mastery_stage(
        has_factor=True,
        has_backtest=True,
        has_validation=True,
        publish_passed=True,
        paper_passed=False,
        has_paper_order=False,
        is_published=False,
    )
    assert s3["stage"] == "graduate"
    assert s3["next_action"] == "paper"

    s4 = compute_mastery_stage(
        has_factor=True,
        has_backtest=True,
        has_validation=True,
        publish_passed=True,
        paper_passed=True,
        has_paper_order=True,
        is_published=False,
    )
    assert s4["stage"] == "track"

    s_decay = compute_mastery_stage(
        has_factor=True,
        has_backtest=True,
        has_validation=True,
        publish_passed=True,
        paper_passed=True,
        has_paper_order=True,
        is_published=False,
        decay_status="alert",
    )
    assert s_decay["stage"] == "track"
    assert s_decay["next_action"] == "revalidate"
    assert s_decay["decay_attention"] is True


def test_failure_coach_from_reasons():
    from backend.app.services.failure_coach_service import coach_from_decay, coach_from_reasons

    tips = coach_from_reasons(["样本外夏普 0.10 低于门槛 0.25", "换手率 75 超过发布门槛"], "zh")
    assert len(tips) >= 1
    assert any("样本外" in t["title"] or "换手" in t["title"] for t in tips)

    decay_tips = coach_from_decay(
        {"status": "alert", "reasons": ["纸面夏普较验证样本外下降 0.40"]},
        "zh",
    )
    assert len(decay_tips) == 1
    assert decay_tips[0]["action"] == "revalidate"


def test_advanced_templates_auto_seed(db_session):
    from backend.app.services.template_service import list_templates, DEFAULT_TEMPLATES

    rows = list_templates(db_session)
    codes = {t.code for t in rows}
    assert "cost-stress-rb" in codes
    assert "volume-surge-rb" in codes
    assert len(codes) >= len(DEFAULT_TEMPLATES)


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


def test_dataset_quality_endpoint(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "dq1")
    r = client.get(f"{BASE}/datasets/quality", headers=h, params={"symbol": "RB", "timeframe": "1d"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["symbol"] == "RB"
    assert "passed" in body
    assert "grade" in body
    assert body["stats"]["rows"] >= 20
