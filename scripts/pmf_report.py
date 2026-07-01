r"""QuantLab AI — PMF 只读分析脚本 (Product Validation Phase)。

定位: v1.0 冻结期的"自我观测"。**只读** —— 仅对现有库做 SELECT 聚合,
不新增表、不新增 API、不改任何业务逻辑。

产出 (北极星 + PMF 三角中可算的两角):
  - RCR        研究闭环完成率 (北极星)
  - Activation 激活率 (注册 -> 出首份报告)
  - Share      分享率 (share / 激活用户)
  - 5 步漏斗 (注册 -> 项目 -> 回测成功 -> 报告 -> 分享)
  - 事件埋点概览 (来自 user_events)
留存 (Day7 等) 因缺 login/session 事件, 显示"待数据", 不臆造。

用法 (仓库根目录):
  $env:PYTHONPATH=(Get-Location).Path
  .\.venv\Scripts\python.exe scripts\pmf_report.py            # 全量
  .\.venv\Scripts\python.exe scripts\pmf_report.py --exclude-test   # 排除测试账号
"""

from __future__ import annotations

import re
import sys

from sqlalchemy import select

from backend.app.core.database import SessionLocal
from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.factor import Factor
from backend.app.models.growth import ResearchShare, UserEvent
from backend.app.models.project import ResearchProject
from backend.app.models.research import ResearchReport
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus

# 看起来像测试/冒烟账号的用户名前缀 (仅用于可选过滤, 不删除任何数据)。
TEST_PATTERN = re.compile(r"^(s9btester|uitester|smoke|test|demo)", re.IGNORECASE)

# PMF 三角及格线。
TH_ACTIVATION = 0.40
TH_RETENTION = 0.25
TH_SHARE = 0.15
MIN_SAMPLE = 30  # 低于此真实用户数, 一律判"数据不足"


def _owner_ids(db, model, where=None) -> set:
    stmt = select(model.owner_id).distinct()
    if where is not None:
        stmt = stmt.where(where)
    return {row[0] for row in db.execute(stmt).all()}


def pct(n: int, d: int) -> float:
    return (n / d) if d else 0.0


def fmt(p: float) -> str:
    return f"{p * 100:.1f}%"


def color(value: float, threshold: float) -> str:
    return "🟢" if value >= threshold else "🔴"


def main() -> None:
    exclude_test = "--exclude-test" in sys.argv
    db = SessionLocal()
    try:
        users = db.execute(select(User.id, User.username)).all()
        all_ids = {u.id for u in users}
        test_ids = {u.id for u in users if TEST_PATTERN.match(u.username or "")}
        universe = (all_ids - test_ids) if exclude_test else all_ids

        # 各阶段达成用户集合 (以业务表为权威, 比前端埋点可靠)。
        s_project = _owner_ids(db, ResearchProject) & universe
        s_factor = _owner_ids(db, Factor) & universe
        s_bt = _owner_ids(db, Backtest, Backtest.status == BacktestStatus.SUCCESS.value) & universe
        s_val = _owner_ids(db, Validation, Validation.status == ValidationStatus.SUCCESS.value) & universe
        s_report = _owner_ids(db, ResearchReport) & universe
        s_share = _owner_ids(db, ResearchShare) & universe

        registered = len(universe)
        rcr_users = s_project & s_factor & s_bt & s_val & s_report & s_share

        rcr = pct(len(rcr_users), registered)
        activation = pct(len(s_report), registered)
        share_rate = pct(len(s_share), len(s_report))

        line = "=" * 56
        print(line)
        print(" QuantLab AI — PMF 只读分析  (v1.0 冻结期 · 仅观测)")
        print(line)
        print(f" 统计口径   : {'排除测试账号' if exclude_test else '全量(含测试账号)'}")
        print(f" 注册用户   : {registered}   (疑似测试账号 {len(test_ids)} 个)")
        print(line)
        print(" 北极星 + PMF 三角")
        print(f"   北极星 RCR (研究闭环完成率) : {fmt(rcr)}  ({len(rcr_users)}/{registered})")
        print(f"   Activation (注册→首份报告)  : {fmt(activation)}  {color(activation, TH_ACTIVATION)} (线 {fmt(TH_ACTIVATION)})")
        print(f"   Retention  (Day7 回访)      : 待数据 ⚠  (缺 login/session 埋点, 无法计算)")
        print(f"   Share      (报告→分享)      : {fmt(share_rate)}  {color(share_rate, TH_SHARE)} (线 {fmt(TH_SHARE)})")
        print(line)
        print(" 5 步漏斗 (严格子集, 每步在前序基础上累计达成 / 转化率)")
        f_project = s_project
        f_bt = f_project & s_bt
        f_report = f_bt & s_report
        f_share = f_report & s_share
        steps = [
            ("① 注册", registered),
            ("② 创建项目", len(f_project)),
            ("③ +回测成功", len(f_bt)),
            ("④ +生成报告", len(f_report)),
            ("⑤ +生成分享", len(f_share)),
        ]
        prev = None
        for name, cnt in steps:
            conv = "" if prev is None else f"  (转化 {fmt(pct(cnt, prev))})"
            print(f"   {name:<12}: {cnt}{conv}")
            prev = cnt
        print(line)
        print(" 事件埋点概览 (user_events)")
        ev = db.execute(
            select(UserEvent.event, UserEvent.user_id)
        ).all()
        agg: dict[str, list[int]] = {}
        for event, uid in ev:
            a = agg.setdefault(event, [0, 0])
            a[0] += 1
            if uid is not None:
                a[1] += 1
        if agg:
            for event in sorted(agg):
                total, with_user = agg[event]
                print(f"   {event:<22}: {total:>5} 次  (具名 {with_user})")
        else:
            print("   (暂无埋点事件)")
        print(line)
        print(" PMF 判定")
        real_n = len(all_ids - test_ids)
        if real_n < MIN_SAMPLE:
            print(f"   ⚪ 数据不足: 真实用户 {real_n} < {MIN_SAMPLE}, 结论不可信。")
            print("      → 当前只能确认'系统跑得通', 不能确认'产品成立'。")
        else:
            ok_act = activation >= TH_ACTIVATION
            ok_share = share_rate >= TH_SHARE
            if ok_act and ok_share:
                print("   🟡/🟢 Activation 与 Share 达标; 留存待补齐 login 埋点后方可定 GREEN。")
            elif ok_act:
                print("   🟡 YELLOW: 有价值但传播弱 (改漏斗, 别加功能)。")
            else:
                print("   🔴 RED: 激活不足, 核心体验未成立。")
        print(line)
        print(" 说明: 本脚本只读, 不改任何业务数据/结构 (符合 v1.0 冻结)。")
        print("       留存与'访问→注册'需先补 login/session 埋点 (events 体系内追加)。")
        print(line)
    finally:
        db.close()


if __name__ == "__main__":
    main()
