"""Chinese explanations for backtest metrics (no hype, no guaranteed returns)."""

from __future__ import annotations

from typing import Any


DISCLAIMER_ZH = (
    "以上为历史回测或模拟结果，不代表未来表现；策略可能失效，"
    "不得理解为稳赚、保证盈利或 AI 预测。"
)


def explain_backtest_zh(
    *,
    metrics: dict[str, Any],
    strategy_name: str,
    fill_count: int | None = None,
    ambiguous: bool = False,
) -> dict[str, Any]:
    sharpe = metrics.get("sharpe")
    max_dd = metrics.get("max_drawdown")
    ann = metrics.get("annual_return") or metrics.get("annualized_return")
    win_rate = metrics.get("win_rate")
    trade_count = fill_count
    if trade_count is None:
        trade_count = metrics.get("trade_count") or metrics.get("fill_count")

    bullets: list[str] = []
    if trade_count is not None:
        bullets.append(f"本次回测成交/调仓相关记录约 {trade_count} 笔。")
    if ann is not None:
        bullets.append(
            f"年化收益（回测口径）约为 {_pct(ann)}。这是历史样本上的结果，不是承诺。"
        )
    if max_dd is not None:
        bullets.append(
            "最大回撤（Max Drawdown）约为 "
            f"{_pct(abs(float(max_dd)))}："
            "意思是历史上从高点到低点，账户曾最多跌这么多。"
        )
    if sharpe is not None:
        bullets.append(
            f"夏普比率（Sharpe）约为 {float(sharpe):.2f}："
            "衡量收益相对波动是否划算；仍可能过拟合。"
        )
    if win_rate is not None:
        bullets.append(f"胜率约为 {_pct(win_rate)}。胜率高不等于期望值为正。")

    strong = (
        sharpe is not None
        and float(sharpe) > 0.5
        and trade_count is not None
        and int(trade_count) >= 10
    )
    if ambiguous:
        verdict = (
            f"「{strategy_name}」草稿仍有歧义或假设参数，"
            "只适合作为研究候选，不能进入模拟/实盘。"
        )
        next_step = "请先确认品种、周期、入场、止损等关键规则，再考虑稳健性验证。"
    elif strong:
        verdict = f"「{strategy_name}」目前有一定研究价值，但还不建议直接真钱运行。"
        next_step = (
            "建议进入样本外 / Walk-Forward / 成本压力等稳健性测试，"
            "而不是继续微调参数。"
        )
    else:
        verdict = f"「{strategy_name}」回测信号偏弱或样本不足，研究价值有限。"
        next_step = "建议修改规则或更换数据区间后重测，不要据此下真实订单。"

    return {
        "verdict_zh": verdict,
        "bullets_zh": bullets,
        "next_step_zh": next_step,
        "disclaimer_zh": DISCLAIMER_ZH,
        "terms_zh": {
            "max_drawdown": "最大回撤（Max Drawdown）",
            "sharpe": "夏普比率（Sharpe）",
            "win_rate": "胜率（Win Rate）",
            "annual_return": "年化收益（Annualized Return）",
        },
    }


def _pct(x: Any) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "未知"
    if abs(v) <= 1.5:
        return f"{v * 100:.1f}%"
    return f"{v:.1f}%"
