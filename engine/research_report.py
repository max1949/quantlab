"""研究项目报告自动生成 (Sprint 8.1 实现)。

把一个因子的研究全过程 (因子定义 + 回测 + 科学验证) **聚合成一篇人话研究报告**:
标题 / 研究假设 / 实验 / 样本内外结果 / 风险 / 下一步建议。

定位区别:
- `report.py` (Sprint 4): 单次"回测"的结构化报告 (偏指标)。
- `research_report.py` (本文件): 面向"研究项目"的叙事报告, 给小白看懂研究讲了什么、靠不靠谱、下一步做什么。

纯函数: 只吃 dict, 不碰 DB/网络。
"""

from __future__ import annotations

from typing import Any

TEMPLATE_LABELS = {
    "momentum": "动量 / 趋势延续",
    "sma_ratio": "均线偏离",
    "rsi": "强弱 (超买超卖)",
    "volatility": "波动率",
    "mean_reversion": "均值回归",
    "volume_surge": "成交量异动 / 放量突破",
}

TEMPLATE_HYPOTHESES = {
    "momentum": "价格趋势具有延续性: 过去 N 期表现强的品种, 未来一段时间倾向继续走强。",
    "sma_ratio": "价格相对均线的偏离会被修复: 偏离越大, 回归动力越强。",
    "rsi": "超买超卖会反转: RSI 过高或过低后, 价格倾向于回摆。",
    "volatility": "波动率蕴含信息: 波动状态的变化预示未来收益分布的变化。",
    "mean_reversion": "价格围绕均值波动: 远离均值后倾向于回归。",
    "volume_surge": "异常放量往往伴随信息冲击: 放量上涨倾向延续, 放量下跌倾向走弱。",
}


def _fmt_pct(x: Any) -> str:
    return "—" if x is None else f"{x:.2%}"


def _fmt_num(x: Any, nd: int = 2) -> str:
    return "—" if x is None else f"{float(x):.{nd}f}"


def _friendly_title(factor: dict, symbol: str) -> str:
    name = factor.get("name") or "未命名因子"
    tt = factor.get("template_type")
    window = (factor.get("spec") or {}).get("params", {}).get("window")
    if factor.get("kind") == "stack":
        return f"{symbol} · 组合因子「{name}」研究"
    label = TEMPLATE_LABELS.get(tt, tt or "因子")
    win = f"{window}日" if window else ""
    return f"{symbol} · {win}{label}「{name}」研究"


def _hypothesis(factor: dict) -> str:
    if factor.get("kind") == "stack":
        return "多个弱信号经标准化加权组合后, 能比单一因子更稳定地预测未来收益。"
    tt = factor.get("template_type")
    return TEMPLATE_HYPOTHESES.get(tt, "该因子对未来收益具有预测力, 据其信号建立多/空仓位可获得风险调整后正收益。")


def build_project_report(
    *,
    factor: dict,
    symbol: str,
    backtest_metrics: dict | None = None,
    validation: dict | None = None,
    snapshot: dict | None = None,
    ai_suggestions: list[str] | None = None,
) -> dict[str, Any]:
    """聚合研究项目报告。返回结构化 sections + markdown + stages。"""
    title = _friendly_title(factor, symbol)
    hypothesis = _hypothesis(factor)

    stages = {
        "factor": True,
        "backtest": backtest_metrics is not None,
        "validation": validation is not None,
    }

    # ---- 实验 ----
    if snapshot:
        experiment = (
            f"标的 {snapshot.get('symbol', symbol)}, 区间 {snapshot.get('start_date')} ~ "
            f"{snapshot.get('end_date')} ({snapshot.get('rows')} 根), "
            f"数据快照哈希 {str(snapshot.get('content_hash',''))[:12]}… (可复现)。"
        )
    else:
        experiment = f"标的 {symbol}, 在固定数据快照上回测并做科学验证。"

    # ---- 结果 ----
    results: dict[str, Any] = {}
    result_lines: list[str] = []
    if backtest_metrics:
        results["回测"] = {
            "年化收益": _fmt_pct(backtest_metrics.get("annual_return")),
            "夏普": _fmt_num(backtest_metrics.get("sharpe")),
            "最大回撤": _fmt_pct(backtest_metrics.get("max_drawdown")),
            "胜率": _fmt_pct(backtest_metrics.get("win_rate")),
        }
        result_lines.append(
            f"整体回测: 年化 {results['回测']['年化收益']}, 夏普 {results['回测']['夏普']}, "
            f"最大回撤 {results['回测']['最大回撤']}。"
        )

    grade = None
    if validation:
        oos = validation.get("oos") or {}
        is_s = (oos.get("in_sample") or {}).get("sharpe")
        oos_s = (oos.get("out_of_sample") or {}).get("sharpe")
        rob = validation.get("robustness") or {}
        grade = rob.get("grade")
        results["样本内夏普"] = _fmt_num(is_s)
        results["样本外夏普"] = _fmt_num(oos_s)
        results["稳健性"] = f"{rob.get('score','—')}/100 ({grade or '未知'})"
        result_lines.append(
            f"样本内夏普 {_fmt_num(is_s)} → 样本外夏普 {_fmt_num(oos_s)}; "
            f"稳健性 {results['稳健性']}。"
        )
        # 一句定性
        if oos_s is not None:
            if oos_s > 0.5:
                result_lines.append("结论: 收益在样本外仍然成立, 初步有效。")
            elif oos_s > 0:
                result_lines.append("结论: 样本外表现一般, 边际有效, 需谨慎。")
            else:
                result_lines.append("结论: 样本外失效, 样本内优势疑似过拟合。")

    # ---- 风险 ----
    risks: list[str] = []
    if validation:
        risks.extend((validation.get("robustness") or {}).get("notes", []) or [])
        wf = (validation.get("walk_forward") or {}).get("summary", {})
        if wf.get("positive_ratio") is not None and wf["positive_ratio"] < 0.5:
            risks.append("跨期一致性不足: 收益可能集中在个别行情段 (如单边趋势), 震荡期易失效。")
    if backtest_metrics:
        dd = backtest_metrics.get("max_drawdown")
        if dd is not None and abs(dd) > 0.3:
            risks.append(f"回撤偏大 ({_fmt_pct(dd)}): 实盘需配合仓位与止损管理。")
        to = backtest_metrics.get("turnover")
        if to is not None and to > 5:
            risks.append("换手较高: 成本与滑点敏感, 实盘收益会打折。")
    if not risks:
        risks.append("暂无显著风险信号, 但样本有限, 建议扩大品种与区间继续验证。")

    # ---- 下一步建议 ----
    next_steps: list[str] = list(ai_suggestions or [])
    if not next_steps:
        if not stages["backtest"]:
            next_steps.append("先完成一次回测, 看风险调整后收益是否值得深入。")
        elif not stages["validation"]:
            next_steps.append("做科学验证 (样本外 + Walk-Forward + 参数敏感性), 排除过拟合。")
        elif grade in {"脆弱", "偏弱"}:
            next_steps.append("增加过滤条件 (如波动/趋势过滤) 或更换因子假设后重做验证。")
            next_steps.append("尝试跨品种验证, 看优势是否只存在于单一品种。")
        else:
            next_steps.append("提交赛季参与排名, 并做跨品种验证增强外部有效性。")

    sections = {
        "title": title,
        "hypothesis": hypothesis,
        "experiment": experiment,
        "results": results,
        "result_summary": result_lines,
        "risks": risks,
        "next_steps": next_steps,
        "grade": grade,
        "stages": stages,
    }
    sections["markdown"] = _render_md(sections, factor, symbol)
    return sections


def _render_md(s: dict, factor: dict, symbol: str) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {x}" for x in items) if items else "- (无)"

    stage_txt = " → ".join(
        name
        for name, done, label in [
            ("因子", s["stages"]["factor"], "因子"),
            ("回测", s["stages"]["backtest"], "回测"),
            ("验证", s["stages"]["validation"], "验证"),
        ]
        if done
    ) or "因子"

    lines = [
        f"# {s['title']}",
        "",
        f"> 研究进度: {stage_txt}" + (f" · 稳健性评级: {s['grade']}" if s["grade"] else ""),
        "",
        "## 研究假设",
        s["hypothesis"],
        "",
        "## 实验",
        s["experiment"],
        "",
        "## 结果",
        bullets(s["result_summary"]) if s["result_summary"] else "- 尚无回测/验证结果。",
        "",
        "## 风险",
        bullets(s["risks"]),
        "",
        "## 下一步建议",
        bullets(s["next_steps"]),
    ]
    return "\n".join(lines)
