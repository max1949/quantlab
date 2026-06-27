"""完整用户路径集成测试 (Research OS 闭环, eager 模式)。

注册 → 创建项目 → 创建因子 → 回测 → 验证 → 生成报告 → 提交赛季 → 进入排行榜
→ 研究主页积分回填 → 30 天挑战进度推进 → 研究 Feed 可见。

这是产品的"北极星"路径: 一个小白能否走完第一个研究项目。
"""

from __future__ import annotations

from backend.app.services.challenge_service import seed_default_challenge
from backend.app.services.competition_service import seed_default_season
from backend.app.services.market_data import seed_sample_market_data

BASE = "/api/v1"


def test_full_research_os_journey(client, db_session):
    # 平台预置: 行情 / 赛季 / 挑战
    seed_sample_market_data(db_session)
    season_id = seed_default_season(db_session)["id"]
    seed_default_challenge(db_session)

    # 1) 注册 + 登录
    client.post(
        f"{BASE}/auth/register",
        json={"email": "newbie@quantlab.ai", "username": "newbie", "password": "s3cret-pass"},
    )
    tok = client.post(
        f"{BASE}/auth/login",
        json={"identifier": "newbie", "password": "s3cret-pass"},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    # 2) 报名 30 天挑战
    prog = client.post(f"{BASE}/challenges/30d-research/enroll", headers=h).json()
    assert prog["completed_count"] == 0

    # 3) 创建研究项目
    proj = client.post(
        f"{BASE}/projects",
        headers=h,
        json={"title": "螺纹钢趋势研究", "symbol": "RB", "question": "趋势是否有延续性?"},
    ).json()
    pid = proj["id"]

    # 4) 在项目下创建因子
    fid = client.post(
        f"{BASE}/factors/template",
        headers=h,
        json={"name": "rb-mom", "template_type": "momentum", "params": {"window": 20}, "project_id": pid},
    ).json()["id"]

    # 5) 回测
    bt = client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "RB"}).json()
    assert bt["status"] == "success"

    # 6) 科学验证
    val = client.post(
        f"{BASE}/validations",
        headers=h,
        json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4},
    ).json()
    assert val["status"] == "success"
    vid = val["id"]

    # 7) 生成研究报告 (项目级)
    rep = client.post(f"{BASE}/research/reports/generate", headers=h, json={"project_id": pid})
    assert rep.status_code == 201, rep.text
    assert rep.json()["project_id"] == pid

    # 8) 发布项目 -> 出现在 Feed
    assert client.post(f"{BASE}/projects/{pid}/publish", headers=h).status_code == 200
    feed = client.get(f"{BASE}/research/feed", headers=h).json()
    assert any(r["project_id"] == pid for r in feed)

    # 9) 提交赛季 -> 进入排行榜
    sub = client.post(f"{BASE}/seasons/{season_id}/submissions", headers=h, json={"validation_id": vid})
    assert sub.status_code == 201, sub.text
    final = sub.json()["final_score"]
    lb = client.get(f"{BASE}/seasons/{season_id}/leaderboard", headers=h).json()
    assert lb[0]["username"] == "newbie"

    # 10) 研究主页: 积分回填 + 统计
    prof = client.get(f"{BASE}/researchers/me", headers=h).json()
    assert prof["research_score"] == final
    assert prof["project_count"] == 1 and prof["factor_count"] == 1 and prof["validation_count"] == 1

    # 11) 研究路径图谱完整: 假设 -> 因子 -> 回测 -> 验证 -> 报告
    g = client.get(f"{BASE}/projects/{pid}/graph", headers=h).json()
    kinds = {n["kind"] for n in g["nodes"]}
    assert {"hypothesis", "experiment", "validation", "result"} <= kinds

    # 12) 挑战进度推进: 至少 first_factor + first_oos 完成
    prog2 = client.get(f"{BASE}/challenges/30d-research/progress", headers=h).json()
    done = {m["code"] for m in prog2["milestones"] if m["completed"]}
    assert {"first_factor", "first_oos", "first_report"} <= done
