"""AI 研究助手 —— 提示词构造 + 确定性本地分析 (Sprint 7 实现)。

设计原则:
- engine 层**不依赖网络/数据库**。这里只做两件纯计算的事:
  1. `build_*_prompt`: 把研究产物 (验证/回测) 拼成给外部 LLM 的结构化提示词;
  2. `local_*`: 一套**确定性的规则分析**, 在没有配置 LLM(或调用失败)时也能给出
     有价值、可复现的研究建议/报告总结 —— 保证系统"无 Key 也可用 + 可测"。
- 助手强调**研究过程与稳健性**, 给的是改进建议而非买卖信号。

外部 LLM 的实际网络调用在 `backend/app/services/llm_client.py`。
"""

from __future__ import annotations

import json
from typing import Any

MENTOR_SYSTEM = (
    "你是 QuantLab 的量化研究导师。你的职责是基于给定的研究数据, 评估研究的"
    "稳健性与方法论, 指出过拟合等风险, 并给出可执行的改进建议。"
    "强调研究过程与可复现性, 用简洁中文分点回答。"
    "绝不提供具体买卖点位或投资建议。"
)


def _fmt_pct(x: Any) -> str:
    return "—" if x is None else f"{x:.2%}"


def _fmt_num(x: Any, nd: int = 3) -> str:
    return "—" if x is None else f"{float(x):.{nd}f}"


# --------------------------------------------------------------------------- #
# 验证复盘 (Validation Review)
# --------------------------------------------------------------------------- #

def local_validation_review(context: dict) -> dict:
    """由验证结果 (oos/walk_forward/sensitivity/robustness) 生成确定性复盘。

    返回结构化字段 + 渲染好的 markdown 文本 (无 LLM 时直接作为助手回复)。
    """
    factor = context.get("factor", {})
    symbol = context.get("symbol", "?")
    oos = context.get("oos") or {}
    wf = (context.get("walk_forward") or {}).get("summary", {})
    sens = (context.get("sensitivity") or {}).get("summary", {})
    rob = context.get("robustness") or {}

    oos_block = oos.get("out_of_sample", {}) or {}
    is_block = oos.get("in_sample", {}) or {}
    oos_sharpe = oos_block.get("sharpe")
    is_sharpe = is_block.get("sharpe")
    degradation = oos.get("sharpe_degradation")
    wf_pos = wf.get("positive_ratio")
    sens_pos = sens.get("positive_ratio")
    score = rob.get("score")
    grade = rob.get("grade", "未知")

    strengths: list[str] = []
    risks: list[str] = []
    suggestions: list[str] = []

    if oos_sharpe is not None and oos_sharpe > 0.5:
        strengths.append(f"样本外夏普 {oos_sharpe:.2f}, 收益在样本外仍成立。")
    if oos_sharpe is not None and oos_sharpe <= 0:
        risks.append("样本外夏普非正: 样本内表现未能延续到样本外, 高度疑似过拟合。")
        suggestions.append("降低参数复杂度 / 扩大样本区间, 优先验证因子逻辑而非调参。")
    if degradation is not None and degradation > 0.5:
        risks.append(
            f"样本内→样本外夏普衰减 {degradation:.2f} (IS {_fmt_num(is_sharpe,2)} → OOS {_fmt_num(oos_sharpe,2)}), 衰减明显。"
        )
        suggestions.append("用更长的样本外窗口或多段 Walk-Forward 复核, 警惕曲线拟合。")

    if wf_pos is not None:
        if wf_pos >= 0.6:
            strengths.append(f"Walk-Forward 跨期一致性好 (盈利分段占比 {wf_pos:.0%})。")
        elif wf_pos < 0.5:
            risks.append(f"跨期一致性不足 (仅 {wf_pos:.0%} 分段盈利): 可能依赖特定行情。")
            suggestions.append("做分段归因, 检查收益是否集中在某一段极端行情。")

    if sens_pos is not None and sens.get("n_variants", 0) > 1:
        if sens_pos >= 0.6:
            strengths.append(f"参数敏感性低 (稳定变体占比 {sens_pos:.0%}): 非单点尖峰。")
        elif sens_pos < 0.5:
            risks.append(f"参数敏感 (仅 {sens_pos:.0%} 变体稳定): 换参数就失效。")
            suggestions.append("做参数高原分析, 选稳健区间的中值而非最优尖峰。")

    if grade in {"稳健", "中等"} and not risks:
        suggestions.append("可提交赛季参与排名, 并尝试跨品种验证以增强外部有效性。")
    if not suggestions:
        suggestions.append("补齐样本外 / Walk-Forward / 参数敏感性三类验证后再下结论。")

    verdict = f"稳健性评分 {score if score is not None else '—'}/100 ({grade})。"
    if grade in {"脆弱", "偏弱"}:
        headline = f"因子「{factor.get('name','?')}」在 {symbol} 上稳健性不足, 暂不建议投入更多资源。"
    elif grade == "中等":
        headline = f"因子「{factor.get('name','?')}」在 {symbol} 上有一定稳健性, 仍需补强后再推进。"
    else:
        headline = f"因子「{factor.get('name','?')}」在 {symbol} 上较为稳健, 可进入竞争性评估。"

    markdown = _render_review_md(headline, verdict, strengths, risks, suggestions)
    return {
        "headline": headline,
        "verdict": verdict,
        "strengths": strengths,
        "risks": risks,
        "suggestions": suggestions,
        "markdown": markdown,
    }


def _render_review_md(
    headline: str,
    verdict: str,
    strengths: list[str],
    risks: list[str],
    suggestions: list[str],
) -> str:
    def _bullets(items: list[str]) -> str:
        return "\n".join(f"- {x}" for x in items) if items else "- (无)"

    return "\n".join(
        [
            f"**结论**: {headline}",
            f"\n{verdict}",
            "\n**优点**",
            _bullets(strengths),
            "\n**风险**",
            _bullets(risks),
            "\n**改进建议**",
            _bullets(suggestions),
        ]
    )


def build_validation_review_prompt(context: dict) -> dict:
    """构造验证复盘的 LLM 提示词 (system + user)。"""
    payload = {
        "因子": context.get("factor", {}),
        "标的": context.get("symbol"),
        "样本外": context.get("oos"),
        "WalkForward": (context.get("walk_forward") or {}).get("summary"),
        "参数敏感性": (context.get("sensitivity") or {}).get("summary"),
        "稳健性": context.get("robustness"),
    }
    user = (
        "请基于以下因子科学验证结果, 给出研究复盘:\n"
        "1) 一句话总体结论; 2) 优点; 3) 主要风险 (尤其过拟合); 4) 可执行的改进建议。\n\n"
        + json.dumps(payload, ensure_ascii=False, default=str, indent=2)
    )
    return {"system": MENTOR_SYSTEM, "user": user}


# --------------------------------------------------------------------------- #
# 回测报告总结 (Backtest Summary)
# --------------------------------------------------------------------------- #

def local_backtest_summary(context: dict) -> dict:
    """由回测指标生成确定性的报告总结 (无 LLM 时直接使用)。"""
    factor = context.get("factor", {})
    symbol = context.get("symbol", "?")
    m = context.get("metrics") or {}
    report = context.get("report") or {}

    sharpe = m.get("sharpe")
    annual = m.get("annual_return")
    max_dd = m.get("max_drawdown")
    win = m.get("win_rate")
    turnover = m.get("turnover")
    grade = report.get("grade", "未知")

    highlights: list[str] = []
    caveats: list[str] = []
    next_steps: list[str] = []

    highlights.append(
        f"年化收益 {_fmt_pct(annual)}, 夏普 {_fmt_num(sharpe, 2)}, 最大回撤 {_fmt_pct(max_dd)}。"
    )
    if win is not None:
        highlights.append(f"胜率 {_fmt_pct(win)}。")

    if max_dd is not None and abs(max_dd) > 0.3:
        caveats.append(f"回撤偏大 ({_fmt_pct(max_dd)}): 注意资金管理与杠杆。")
    if turnover is not None and turnover > 5:
        caveats.append(f"换手较高 (turnover {_fmt_num(turnover,2)}): 成本与滑点敏感, 实盘易打折。")
    if sharpe is not None and sharpe < 0.5:
        caveats.append("风险调整后收益有限, 单凭回测不足以判定有效。")

    if sharpe is not None and sharpe >= 1.0:
        next_steps.append("进入科学验证: 样本外 + Walk-Forward + 参数敏感性, 排除过拟合。")
    else:
        next_steps.append("调整因子假设或参数后重测, 不要直接用历史最优参数。")
    next_steps.append("固定数据快照, 保证复盘可复现。")

    headline = (
        f"因子「{factor.get('name','?')}」在 {symbol} 的回测评级: {grade}。"
    )
    markdown = "\n".join(
        [
            f"**回测总结**: {headline}",
            "\n**关键表现**",
            "\n".join(f"- {x}" for x in highlights),
            "\n**注意事项**",
            "\n".join(f"- {x}" for x in caveats) if caveats else "- (无明显异常)",
            "\n**下一步**",
            "\n".join(f"- {x}" for x in next_steps),
        ]
    )
    return {
        "headline": headline,
        "grade": grade,
        "highlights": highlights,
        "caveats": caveats,
        "next_steps": next_steps,
        "markdown": markdown,
    }


def build_backtest_summary_prompt(context: dict) -> dict:
    """构造回测总结的 LLM 提示词 (system + user)。"""
    payload = {
        "因子": context.get("factor", {}),
        "标的": context.get("symbol"),
        "成本": context.get("cost_config"),
        "指标": context.get("metrics"),
        "研究报告结论": (context.get("report") or {}).get("conclusion"),
    }
    user = (
        "请用通俗语言总结这份回测研究报告, 面向刚入门的交易员:\n"
        "1) 一句话结论; 2) 关键表现; 3) 风险/注意事项; 4) 下一步该做什么。\n\n"
        + json.dumps(payload, ensure_ascii=False, default=str, indent=2)
    )
    return {"system": MENTOR_SYSTEM, "user": user}


# --------------------------------------------------------------------------- #
# 研究指导 (Research Plan) —— 给方向, 出可执行研究计划
# --------------------------------------------------------------------------- #

DISCLAIMER = "本计划仅为研究方法建议, 不构成任何交易建议, 不承诺收益。"

# 候选研究假设库: 假设 -> 对应模板因子。
_PLAN_HYPOTHESES = [
    {
        "name": "趋势延续假设",
        "factor_template": "momentum",
        "rationale": "若该品种存在趋势惯性, 过去强势未来可能延续, 用动量因子捕捉。",
    },
    {
        "name": "均值回归假设",
        "factor_template": "mean_reversion",
        "rationale": "若价格围绕均值波动, 偏离后倾向回归, 用均值回归因子捕捉。",
    },
    {
        "name": "波动率状态假设",
        "factor_template": "volatility",
        "rationale": "若波动率变化预示收益分布变化, 用波动率因子作为状态/过滤信号。",
    },
]

_PLAN_EXPERIMENTS = [
    "窗口周期测试: 对因子窗口参数 (如 MA/动量周期) 做网格扫描, 找稳健区间而非单点最优。",
    "参数敏感性测试: 在最优附近扰动参数, 确认表现不是尖峰 (抗过拟合)。",
    "样本外 + Walk-Forward 验证: 检验收益在样本外与不同时间段是否稳定。",
    "跨品种验证: 在其它相关品种上复跑, 检验逻辑的外部有效性而非单一品种巧合。",
]


def local_research_plan(theme: str) -> dict:
    """由研究方向 (品种/主题) 生成确定性研究计划 (无 LLM 时直接使用)。"""
    theme = (theme or "目标品种").strip()
    hypotheses = _PLAN_HYPOTHESES
    experiments = _PLAN_EXPERIMENTS

    lines = [f"# 研究计划: {theme}", "", "## 研究假设"]
    for i, h in enumerate(hypotheses, 1):
        lines.append(f"{i}. **{h['name']}** (因子: {h['factor_template']}) — {h['rationale']}")
    lines += ["", "## 推荐实验"]
    lines += [f"- {e}" for e in experiments]
    lines += ["", "## 建议路径",
              "先用单因子跑通 回测 → 样本外验证, 再考虑组合因子; 全程固定数据快照保证可复现。",
              "", f"> {DISCLAIMER}"]

    return {
        "theme": theme,
        "hypotheses": hypotheses,
        "experiments": experiments,
        "disclaimer": DISCLAIMER,
        "markdown": "\n".join(lines),
    }


def build_research_plan_prompt(theme: str) -> dict:
    """构造研究指导的 LLM 提示词。强约束: 只给研究方法, 不给交易建议。"""
    user = (
        f"我想研究「{theme}」。请作为量化研究导师, 给出一份研究计划:\n"
        "1) 2-3 个研究假设, 每个对应可量化的因子方向;\n"
        "2) 推荐的实验步骤 (参数测试 / 敏感性 / 样本外 / 跨品种);\n"
        "3) 一句话研究路径建议。\n"
        "要求: 只给研究方法与因子方向, 不要给具体买卖点位, 不要承诺收益。"
    )
    return {"system": MENTOR_SYSTEM, "user": user}


# --------------------------------------------------------------------------- #
# 因子参数扫描复盘 (Scan Review)
# --------------------------------------------------------------------------- #

def local_scan_review(context: dict) -> dict:
    """由参数扫描结果生成确定性解读。"""
    symbol = context.get("symbol", "?")
    timeframe = context.get("timeframe", "?")
    template = context.get("template_type", "?")
    results = context.get("results") or []
    coach = context.get("coach_summary", "")

    strengths: list[str] = []
    risks: list[str] = []
    suggestions: list[str] = []

    if not results:
        headline = f"「{template}」在 {symbol}·{timeframe} 上扫描无有效结果。"
        return {
            "headline": headline,
            "strengths": [],
            "risks": ["参数网格未产生可排序结果"],
            "suggestions": ["换更大周期或简化模板参数范围后重扫"],
            "markdown": f"**结论**: {headline}\n\n请换标的/周期后重试。",
        }

    top = results[0]
    score = top.get("score")
    oos = top.get("oos_sharpe")
    ic = top.get("ic_mean")
    turnover = top.get("turnover")

    if score is not None and score >= 0.55:
        strengths.append(f"最优参数 {top.get('label')} 综合分 {score:.2f}，排名靠前。")
    if oos is not None and oos >= 0.4:
        strengths.append(f"样本外夏普 {_fmt_num(oos, 2)}，初步具备延续性。")
    if ic is not None and abs(ic) >= 0.03:
        strengths.append(f"IC {_fmt_num(ic, 3)}，因子与远期收益有一定相关性。")

    if oos is not None and oos < 0.2:
        risks.append(f"样本外夏普仅 {_fmt_num(oos, 2)}，疑似过拟合窗口。")
        suggestions.append("缩小搜索范围或固定逻辑后做完整科学验证。")
    if ic is not None and abs(ic) < 0.02:
        risks.append("IC 偏低，预测力有限。")
        suggestions.append("尝试组合因子或换模板类型。")
    if turnover is not None and turnover > 40:
        risks.append(f"换手率 {_fmt_num(turnover, 1)} 偏高，实盘成本敏感。")
        suggestions.append("加长窗口或换 15m/30m 等更低频周期。")

    if len(results) >= 3:
        suggestions.append("可用「实验对比」比较两次扫描，确认最优区间是否稳定。")
    suggestions.append("满意后一键载入因子 → 回测 → 科学验证，再考虑发布。")

    headline = (
        f"「{template}」在 {symbol}·{timeframe} 扫描完成，"
        f"推荐参数 {top.get('label')}（综合分 {score if score is not None else '—'}）。"
    )
    markdown = _render_review_md(
        headline,
        coach or "参数扫描教练摘要见上。",
        strengths,
        risks,
        suggestions,
    )
    return {
        "headline": headline,
        "strengths": strengths,
        "risks": risks,
        "suggestions": suggestions,
        "markdown": markdown,
    }


def build_scan_review_prompt(context: dict) -> dict:
    payload = {
        "标的": context.get("symbol"),
        "周期": context.get("timeframe"),
        "模板": context.get("template_type"),
        "前5组结果": (context.get("results") or [])[:5],
        "教练摘要": context.get("coach_summary"),
    }
    user = (
        "请基于以下因子参数扫描结果，给出研究解读:\n"
        "1) 一句话结论; 2) 优点; 3) 风险 (过拟合/换手/IC); 4) 下一步建议。\n\n"
        + json.dumps(payload, ensure_ascii=False, default=str, indent=2)
    )
    return {"system": MENTOR_SYSTEM, "user": user}
