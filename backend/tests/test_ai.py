"""AI 研究助手接口测试。

默认 LLM 未配置 -> 走本地规则分析 (source=local)。
另用 monkeypatch 模拟 LLM 启用/调用成功与失败两条路径。
"""

from __future__ import annotations

from sqlalchemy import select

from backend.app.models.ai import AiInsight
from backend.app.services import ai_service, llm_client
from backend.app.services.market_data import seed_sample_market_data

BASE = "/api/v1"
USER = {"email": "ai@quantlab.ai", "username": "aitester", "password": "s3cret-pass"}


def _auth(client) -> dict:
    client.post(f"{BASE}/auth/register", json=USER)
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": USER["username"], "password": USER["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _make_validation(client, h) -> str:
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "mom", "template_type": "momentum", "params": {"window": 20}},
    ).json()["id"]
    return client.post(
        f"{BASE}/validations",
        headers=h,
        json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4},
    ).json()["id"]


def _make_backtest(client, h) -> str:
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "mom-bt", "template_type": "momentum", "params": {"window": 20}},
    ).json()["id"]
    ds = client.get(f"{BASE}/datasets", headers=h).json()
    return client.post(
        f"{BASE}/backtests",
        headers=h,
        json={"factor_id": fid, "symbol": "RB"},
    ).json()["id"]


def test_status_disabled_by_default(client, monkeypatch):
    h = _auth(client)
    monkeypatch.setattr(llm_client, "is_enabled", lambda: False)
    s = client.get(f"{BASE}/ai/status", headers=h).json()
    assert s["enabled"] is False
    assert s["model"] is None
    assert s["fallback"] == "local"


def test_validation_review_local_fallback(client, db_session, monkeypatch):
    monkeypatch.setattr(llm_client, "is_enabled", lambda: False)
    h = _auth(client)
    seed_sample_market_data(db_session)
    vid = _make_validation(client, h)
    resp = client.post(f"{BASE}/ai/validations/{vid}/review", headers=h)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["source"] == "local"
    assert body["model"] is None
    assert body["content"].startswith("**结论**")
    assert "suggestions" in body["analysis"] and body["analysis"]["suggestions"]
    # 落库
    assert db_session.execute(select(AiInsight)).scalars().first() is not None


def test_validation_review_uses_llm_when_enabled(client, db_session, monkeypatch):
    monkeypatch.setattr(llm_client, "is_enabled", lambda: True)
    monkeypatch.setattr(llm_client, "model_name", lambda: "mock-model")
    monkeypatch.setattr(llm_client, "complete", lambda system, user: "LLM 复盘: 该因子样本外失效。")
    h = _auth(client)
    seed_sample_market_data(db_session)
    vid = _make_validation(client, h)
    body = client.post(f"{BASE}/ai/validations/{vid}/review", headers=h).json()
    assert body["source"] == "llm"
    assert body["model"] == "mock-model"
    assert body["content"] == "LLM 复盘: 该因子样本外失效。"


def test_llm_failure_falls_back_to_local(client, db_session, monkeypatch):
    def _boom(system, user):
        raise llm_client.LLMError("network down")

    monkeypatch.setattr(llm_client, "is_enabled", lambda: True)
    monkeypatch.setattr(llm_client, "model_name", lambda: "mock-model")
    monkeypatch.setattr(llm_client, "complete", _boom)
    h = _auth(client)
    seed_sample_market_data(db_session)
    vid = _make_validation(client, h)
    body = client.post(f"{BASE}/ai/validations/{vid}/review", headers=h).json()
    assert body["source"] == "local"  # 调用失败 -> 降级
    assert body["content"].startswith("**结论**")


def test_backtest_summary_local(client, db_session, monkeypatch):
    monkeypatch.setattr(llm_client, "is_enabled", lambda: False)
    h = _auth(client)
    seed_sample_market_data(db_session)
    bid = _make_backtest(client, h)
    body = client.post(f"{BASE}/ai/backtests/{bid}/summary", headers=h).json()
    assert body["source"] == "local"
    assert body["kind"] == "backtest_summary"
    assert "next_steps" in body["analysis"]


def test_review_unknown_validation_422(client, monkeypatch):
    monkeypatch.setattr(llm_client, "is_enabled", lambda: False)
    h = _auth(client)
    fake = "00000000-0000-0000-0000-000000000000"
    assert client.post(f"{BASE}/ai/validations/{fake}/review", headers=h).status_code == 422


def test_insights_list(client, db_session, monkeypatch):
    monkeypatch.setattr(llm_client, "is_enabled", lambda: False)
    h = _auth(client)
    seed_sample_market_data(db_session)
    vid = _make_validation(client, h)
    client.post(f"{BASE}/ai/validations/{vid}/review", headers=h)
    lst = client.get(f"{BASE}/ai/insights", headers=h).json()
    assert len(lst) == 1
    assert lst[0]["target_id"] == vid


def test_ai_requires_auth(client):
    assert client.get(f"{BASE}/ai/status").status_code == 403
