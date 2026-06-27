"""研究报告生成 (Sprint 4)。

回测不只给数字, 还产出可读的"研究报告"(假设 / 方法 / 结果 / 结论)。
纯函数: 由因子元信息 + 成本配置 + 回测指标合成结构化报告 (dict) 与 Markdown 文本,
保证"研究过程 > 研究结果"且可复现。
"""

from __future__ import annotations

from typing import Any


def _verdict(metrics: dict) -> tuple[str, str]:
    """根据指标给出定性结论 (评级, 说明)。不是单看收益, 而是风险调整后表现。"""
    sharpe = metrics.get("sharpe")
    max_dd = metrics.get("max_drawdown")
    if sharpe is None:
        return "无法评估", "策略几乎不交易或波动为零, 无法计算风险调整收益。"
    if sharpe >= 1.5:
        grade = "优秀"
    elif sharpe >= 1.0:
        grade = "良好"
    elif sharpe >= 0.5:
        grade = "一般"
    elif sharpe >= 0:
        grade = "偏弱"
    else:
        grade = "无效"

    dd_txt = f"最大回撤 {max_dd:.1%}" if max_dd is not None else "回撤未知"
    note = (
        f"夏普 {sharpe:.2f}, {dd_txt}。"
        + (
            "风险调整后收益较好, 值得进一步做样本外/Walk-Forward 验证。"
            if sharpe >= 1.0
            else "风险调整后收益有限, 建议调整参数或更换因子假设后再试。"
        )
    )
    return grade, note


def build_research_report(
    *,
    factor_name: str,
    factor_kind: str,
    factor_spec: dict,
    symbol: str,
    cost_config: dict,
    metrics: dict,
    snapshot: dict | None = None,
) -> dict[str, Any]:
    """合成研究报告。返回含 sections 与 markdown 的 dict。"""
    grade, note = _verdict(metrics)

    hypothesis = (
        f"因子「{factor_name}」({factor_kind}) 对标的 {symbol} 的未来收益具有预测力, "
        "据其信号方向建立多/空仓位可获得风险调整后的正收益。"
    )
    method = (
        f"在数据快照上计算因子信号, 取符号生成仓位 (多/空/空仓), "
        f"以上期仓位乘当期收益计净值, 并扣除交易成本 "
        f"(手续费 {cost_config.get('fee_rate')}, 滑点 {cost_config.get('slippage_bps')}bp)。"
    )

    results_rows = [
        ("总收益", _pct(metrics.get("total_return"))),
        ("年化收益", _pct(metrics.get("annual_return"))),
        ("年化波动", _pct(metrics.get("annual_volatility"))),
        ("夏普比率", _num(metrics.get("sharpe"))),
        ("最大回撤", _pct(metrics.get("max_drawdown"))),
        ("胜率", _pct(metrics.get("win_rate"))),
        ("交易次数", str(metrics.get("trade_count"))),
        ("换手", _num(metrics.get("turnover"))),
    ]

    conclusion = f"评级: {grade}。{note}"

    sections = {
        "hypothesis": hypothesis,
        "method": method,
        "results": dict(results_rows),
        "conclusion": conclusion,
        "grade": grade,
    }

    lines = [
        f"# 研究报告: {factor_name}",
        "",
        "## 假设",
        hypothesis,
        "",
        "## 方法",
        method,
    ]
    if snapshot:
        lines += [
            "",
            "## 数据快照 (可复现)",
            f"- 标的: {snapshot.get('symbol')}",
            f"- 区间: {snapshot.get('start_date')} ~ {snapshot.get('end_date')}",
            f"- 行数: {snapshot.get('rows')}",
            f"- 内容哈希: `{snapshot.get('content_hash')}`",
        ]
    lines += ["", "## 结果"]
    lines += [f"- {k}: {v}" for k, v in results_rows]
    lines += ["", "## 结论", conclusion]

    sections["markdown"] = "\n".join(lines)
    return sections


def _pct(x) -> str:
    return "—" if x is None else f"{x:.2%}"


def _num(x) -> str:
    return "—" if x is None else f"{x:.3f}"
