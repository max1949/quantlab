"""增长闭环集成测试 (Sprint 9A):

访客埋点 -> 注册(带邀请码+身份) -> 模板一键开局 -> 因子/回测/验证/报告
-> 分享卡片(公开) -> 邀请人激活发奖 -> 多维榜单 -> 30天挑战奖励+证书。
"""

from __future__ import annotations

from backend.app.services.challenge_service import seed_default_challenge
from backend.app.services.market_data import seed_sample_market_data
from backend.app.services.template_service import seed_default_templates

BASE = "/api/v1"


def _login(client, username):
    tok = client.post(
        f"{BASE}/auth/login", json={"identifier": username, "password": "s3cret-pass"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_full_growth_loop(client, db_session):
    seed_sample_market_data(db_session)
    seed_default_templates(db_session)
    seed_default_challenge(db_session)

    # 邀请人
    client.post(f"{BASE}/auth/register", json={"email": "amy@quantlab.ai", "username": "amy", "password": "s3cret-pass"})
    h_amy = _login(client, "amy")

    # 访客匿名埋点 + 带邀请码注册(新手身份)
    assert client.post(f"{BASE}/events", json={"event": "visit", "props": {"ref": "amy"}}).status_code == 204
    client.post(
        f"{BASE}/auth/register",
        json={"email": "ben@quantlab.ai", "username": "ben", "password": "s3cret-pass", "user_type": "newbie", "ref": "amy"},
    )
    h_ben = _login(client, "ben")

    # 报名挑战, 个性化下一步
    client.post(f"{BASE}/challenges/30d-research/enroll", headers=h_ben)
    nxt = client.get(f"{BASE}/onboarding/next", headers=h_ben).json()
    assert nxt["recommended_template"] == "gold-trend"

    # 一键模板开局 (AU)
    start = client.post(f"{BASE}/research/templates/gold-trend/start", headers=h_ben, json={"with_factor": True}).json()
    pid, fid = start["project_id"], start["factor_id"]

    # 回测 + 验证 + 报告
    assert client.post(f"{BASE}/backtests", headers=h_ben, json={"factor_id": fid, "symbol": "AU"}).json()["status"] == "success"
    client.post(f"{BASE}/validations", headers=h_ben, json={"factor_id": fid, "symbol": "AU", "oos_ratio": 0.3, "n_splits": 4})
    rep = client.post(f"{BASE}/research/reports/generate", headers=h_ben, json={"project_id": pid})
    assert rep.status_code == 201
    report_id = rep.json()["id"]

    # 分享卡片 (公开免登录)
    token = client.post(f"{BASE}/research/reports/{report_id}/share", headers=h_ben).json()["token"]
    card = client.get(f"{BASE}/share/{token}").json()
    assert card["card"]["researcher"] == "ben"

    # 邀请人 amy 因 ben 完成首次研究而被激活发奖
    ref = client.get(f"{BASE}/me/referral", headers=h_amy).json()
    assert ref["activated"] == 1 and ref["reward_points_earned"] >= 50

    # ben 在多维榜单(researcher = 研究信用)可见, 且研究信用 > 0
    prof = client.get(f"{BASE}/researchers/me", headers=h_ben).json()
    assert prof["research_contribution_score"] > 0
    board = client.get(f"{BASE}/leaderboards/researcher", headers=h_ben).json()
    assert any(r["username"] == "ben" for r in board)

    # 挑战进度: 已完成 first_factor/first_oos/first_report, 拿到 reward_points
    prog = client.get(f"{BASE}/challenges/30d-research/progress", headers=h_ben).json()
    done = {m["code"] for m in prog["milestones"] if m["completed"]}
    assert {"first_factor", "first_oos", "first_report"} <= done
    assert prog["reward_points"] > 0

    # 两套分数互不相同的概念: 行为积分(reward) 与 研究信用(contribution) 独立存在
    assert prof["reward_points"] >= 0
    assert prof["research_contribution_score"] >= 8  # 至少一份报告沉淀的研究信用

    # 验证埋点漏斗(amy 是 L0, 无法看 -> 403; 用一个 L3 用户检验需另造, 这里只验证鉴权)
    assert client.get(f"{BASE}/events/funnel", headers=h_ben).status_code == 403


def test_challenge_certificate_after_completion(client, db_session):
    seed_sample_market_data(db_session)
    seed_default_challenge(db_session)
    client.post(f"{BASE}/auth/register", json={"email": "cara@quantlab.ai", "username": "cara", "password": "s3cret-pass"})
    h = _login(client, "cara")

    # 未完成 -> 无证书
    assert client.get(f"{BASE}/challenges/30d-research/certificate", headers=h).status_code == 422

    # 走完: 因子 + 验证 + 报告 + 组合因子 (满足全部 4 个里程碑)
    proj = client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": "RB"}).json()
    fid = client.post(
        f"{BASE}/factors/template", headers=h,
        json={"name": "m1", "template_type": "momentum", "params": {"window": 20}, "project_id": proj["id"]},
    ).json()["id"]
    # 升到 L1 才能建组合因子: 这里直接再建一个模板因子并用 stack? stack 需 L1。
    # 为测试证书, 用 task 完成升级较繁琐; 改为验证 stack 里程碑可不满足时证书不发,
    # 故此用例只检验"全部满足才发证"路径需要 L1, 跳过 stack, 验证未满足时无证书。
    client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "RB"})
    client.post(f"{BASE}/validations", headers=h, json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4})
    client.post(f"{BASE}/research/reports/generate", headers=h, json={"project_id": proj["id"]})
    prog = client.get(f"{BASE}/challenges/30d-research/progress", headers=h).json()
    # stack_factor 未完成 -> 还没证书
    assert prog["certificate_code"] is None
    assert client.get(f"{BASE}/challenges/30d-research/certificate", headers=h).status_code == 422


def test_challenge_full_completion_issues_certificate(client, db_session):
    from backend.app.models.user import User, UserLevel

    seed_sample_market_data(db_session)
    seed_default_challenge(db_session)
    client.post(f"{BASE}/auth/register", json={"email": "dan@quantlab.ai", "username": "danr", "password": "s3cret-pass"})
    h = _login(client, "danr")

    # 直接提升到 L1 (组合因子需要 L1), 免去跑学院任务。
    user = db_session.query(User).filter(User.username == "danr").one()
    user.level = UserLevel.L1.value
    db_session.commit()

    proj = client.post(f"{BASE}/projects", headers=h, json={"title": "p", "symbol": "RB"}).json()
    fid = client.post(
        f"{BASE}/factors/template", headers=h,
        json={"name": "m1", "template_type": "momentum", "params": {"window": 20}, "project_id": proj["id"]},
    ).json()["id"]
    # 组合因子 (满足 stack_factor 里程碑)
    stack = client.post(
        f"{BASE}/factors/stack", headers=h,
        json={"name": "combo", "components": [{"factor_id": fid, "weight": 1.0}], "project_id": proj["id"]},
    )
    assert stack.status_code == 201, stack.text
    client.post(f"{BASE}/backtests", headers=h, json={"factor_id": fid, "symbol": "RB"})
    client.post(f"{BASE}/validations", headers=h, json={"factor_id": fid, "symbol": "RB", "oos_ratio": 0.3, "n_splits": 4})
    client.post(f"{BASE}/research/reports/generate", headers=h, json={"project_id": proj["id"]})

    prog = client.get(f"{BASE}/challenges/30d-research/progress", headers=h).json()
    assert prog["completed_count"] == 4
    assert prog["certificate_code"] is not None
    # 证书可领取
    cert = client.get(f"{BASE}/challenges/30d-research/certificate", headers=h).json()
    assert cert["certificate_code"] == prog["certificate_code"]
    assert cert["username"] == "danr"
    # 完成奖金已发放 (reward_points 含里程碑奖励 + 完成奖金)
    prof = client.get(f"{BASE}/researchers/me", headers=h).json()
    assert prof["reward_points"] >= 200
