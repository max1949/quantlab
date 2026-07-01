"""纸面跟踪 API 与服务测试。"""

from __future__ import annotations

from backend.app.services import paper_tracking_service as pts
from backend.app.services.market_data import seed_sample_market_data
from backend.tests.test_growth import BASE, _register


def _template(client, h, project_id: str | None = None) -> str:
    body = {"name": "paper-mom", "template_type": "momentum", "params": {"window": 20}}
    if project_id:
        body["project_id"] = project_id
    return client.post(f"{BASE}/factors/template", headers=h, json=body).json()["id"]


def test_paper_history_after_validation(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "paper1")
    fid = _template(client, h)
    client.post(
        f"{BASE}/validations",
        headers=h,
        json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4},
    )
    hist = client.get(f"{BASE}/factors/{fid}/paper-history", headers=h)
    assert hist.status_code == 200, hist.text
    body = hist.json()
    assert body["factor_id"] == fid
    assert len(body["snapshots"]) >= 1
    assert body["latest_preview"] is not None


def test_paper_preview_endpoint(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "paper2")
    fid = _template(client, h)
    client.post(
        f"{BASE}/validations",
        headers=h,
        json={"factor_id": fid, "symbol": "RB"},
    )
    prev = client.get(f"{BASE}/factors/{fid}/paper-preview", headers=h)
    assert prev.status_code == 200
    assert prev.json()["nav_end"] > 0


def test_paper_decay_endpoint(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "paper4")
    fid = _template(client, h)
    client.post(f"{BASE}/validations", headers=h, json={"factor_id": fid, "symbol": "RB"})
    decay = client.get(f"{BASE}/factors/{fid}/paper-decay", headers=h)
    assert decay.status_code == 200
    body = decay.json()
    assert body["status"] in {"ok", "watch", "alert"}


def test_daily_batch(client, db_session):
    seed_sample_market_data(db_session)
    h = _register(client, "paper3")
    fid = _template(client, h)
    client.post(f"{BASE}/validations", headers=h, json={"factor_id": fid, "symbol": "RB"})
    result = pts.run_daily_paper_batch(db_session)
    assert result["recorded"] >= 1
