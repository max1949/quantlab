"""失败案例教练 — 把质量闸门拒绝原因转成可学习的修复指引。"""

from __future__ import annotations

from backend.app.core.locale import Locale

_PLAYBOOK: list[dict] = [
    {
        "keys": ["科学验证", "validation"],
        "title": {"en": "Run full validation first", "zh": "先完成科学验证"},
        "tip": {
            "en": "Backtest Sharpe alone is not enough. Run OOS + walk-forward before paper or publish.",
            "zh": "回测夏普好看不等于能上线。先跑样本外 + Walk-Forward，再考虑 Paper 或发布。",
        },
        "action": "validate",
    },
    {
        "keys": ["样本外", "OOS", "oos"],
        "title": {"en": "Out-of-sample too weak", "zh": "样本外表现偏弱"},
        "tip": {
            "en": "Try a longer lookback, a different template, or fewer parameters in your scan grid.",
            "zh": "可试更长窗口、换模板，或缩小参数扫描范围，避免过拟合某一组参数。",
        },
        "action": "validate",
    },
    {
        "keys": ["稳健性", "robustness"],
        "title": {"en": "Robustness below bar", "zh": "稳健性未达标"},
        "tip": {
            "en": "Run robustness test in L3 tools. Prefer stable grades「稳健/中等」before going live.",
            "zh": "在 L3 工具跑稳健性测试。毕业前尽量达到「稳健 / 中等」评级。",
        },
        "action": "graduate",
    },
    {
        "keys": ["换手", "turnover"],
        "title": {"en": "Turnover too high", "zh": "换手率过高"},
        "tip": {
            "en": "High turnover eats returns after fees. Use the「Cost Stress」playbook or longer windows.",
            "zh": "换手太高会被手续费吃掉。试「成本压力测试」Playbook 或加大回看窗口。",
        },
        "action": "backtest",
    },
    {
        "keys": ["holdout", "封印"],
        "title": {"en": "Sealed holdout failed", "zh": "封印段未通过"},
        "tip": {
            "en": "The sealed segment was not used for tuning — if it still fails, the edge may not be real.",
            "zh": "封印段未参与调参仍表现差，说明优势可能不真实。建议换假设或模板重来。",
        },
        "action": "validate",
    },
    {
        "keys": ["IC", "ic"],
        "title": {"en": "Low predictive IC", "zh": "因子 IC 偏低"},
        "tip": {
            "en": "Weak IC means limited forecasting power. Try stacking factors or switching template family.",
            "zh": "IC 低代表预测力有限。可试因子组合，或换一类模板（趋势 / 均值回归）。",
        },
        "action": "backtest",
    },
    {
        "keys": ["适配", "regime", "fit"],
        "title": {"en": "Regime mismatch", "zh": "市况适配不足"},
        "tip": {
            "en": "Current volatility regime may not suit this factor style. Check the regime banner and pick a matching playbook.",
            "zh": "当前波动制度可能不适合这类因子。看项目页制度提示，选「制度感知」类 Playbook。",
        },
        "action": "paper",
    },
    {
        "keys": ["回测"],
        "title": {"en": "Backtest missing or weak", "zh": "回测未通过"},
        "tip": {
            "en": "Run a successful backtest on your project symbol before validation.",
            "zh": "请先在项目标的上跑通一次成功回测，再进入验证阶段。",
        },
        "action": "backtest",
    },
    {
        "keys": ["衰减", "走弱", "回撤", "decay", "drawdown"],
        "title": {"en": "Paper performance decaying", "zh": "纸面表现衰减"},
        "tip": {
            "en": "Live paper metrics diverged from validation. Tweak the factor in the lab, then re-run OOS validation.",
            "zh": "模拟盘指标已偏离验证期基准。回因子实验室调参，再跑一次样本外验证。",
        },
        "action": "revalidate",
    },
]


def coach_from_reasons(reasons: list[str], locale: Locale = "en") -> list[dict]:
    """根据闸门原因返回去重后的教练卡片 (最多 4 条)。"""
    if not reasons:
        return []
    loc = locale if locale in ("en", "zh") else "en"
    seen_actions: set[str] = set()
    out: list[dict] = []
    blob = " ".join(reasons).lower()
    for item in _PLAYBOOK:
        if not any(k.lower() in blob for k in item["keys"]):
            continue
        action = item["action"]
        if action in seen_actions:
            continue
        seen_actions.add(action)
        out.append(
            {
                "title": item["title"][loc],
                "tip": item["tip"][loc],
                "action": action,
            }
        )
        if len(out) >= 4:
            break
    return out


def coach_from_decay(decay: dict | None, locale: Locale = "en") -> list[dict]:
    """纸面衰减告警 → 回到实验室重新验证的教练卡片。"""
    if not decay or decay.get("status") not in ("watch", "alert"):
        return []
    loc = locale if locale in ("en", "zh") else "en"
    status = decay["status"]
    reasons = decay.get("reasons") or []
    if status == "alert":
        title = {"en": "Paper decay alert", "zh": "纸面衰减告警"}
        tip = {
            "en": "Paper Sharpe or drawdown diverged sharply from validation. Re-validate before trusting this factor.",
            "zh": "纸面夏普或回撤明显偏离验证期。请回实验室调参并重新验证，再决定是否继续跟踪。",
        }
    else:
        title = {"en": "Paper performance weakening", "zh": "纸面表现走弱"}
        tip = {
            "en": "Early warning — review factor logic and run a fresh validation pass.",
            "zh": "早期预警信号 — 建议复查因子逻辑并补跑一次验证。",
        }
    if reasons:
        tip = {**tip, loc: f"{tip[loc]} ({reasons[0]})"}
    return [{"title": title[loc], "tip": tip[loc], "action": "revalidate"}]
