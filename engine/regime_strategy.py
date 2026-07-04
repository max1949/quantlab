"""制度 × 策略风格适配评分 (机构级风控路由基础)。"""

from __future__ import annotations

# 策略风格 → 各波动制度下的适配分 (0–100)
_FIT: dict[str, dict[str, int]] = {
    "trend": {"low": 55, "mid": 85, "high": 35},
    "mean_reversion": {"low": 40, "mid": 70, "high": 88},
    "volatility": {"low": 50, "mid": 65, "high": 90},
    "generic": {"low": 60, "mid": 70, "high": 60},
}

_STYLE_LABELS = {
    "trend": "趋势/动量",
    "mean_reversion": "均值回归",
    "volatility": "波动率",
    "generic": "综合",
}

_TEMPLATE_MAP: dict[str, str] = {
    "momentum": "trend",
    "ma_cross": "trend",
    "mean_reversion": "mean_reversion",
    "rsi": "mean_reversion",
    "volatility": "volatility",
    "volume_surge": "trend",
}


def infer_strategy_style(
    *,
    kind: str | None = None,
    template_type: str | None = None,
    name: str | None = None,
) -> str:
    """从因子元数据推断策略风格。"""
    tt = (template_type or "").lower()
    if tt in _TEMPLATE_MAP:
        return _TEMPLATE_MAP[tt]

    nm = (name or "").lower()
    if any(k in nm for k in ("mom", "动量", "trend", "趋势")):
        return "trend"
    if any(k in nm for k in ("revert", "回归", "rsi", "超买")):
        return "mean_reversion"
    if any(k in nm for k in ("vol", "波动")):
        return "volatility"

    if kind in ("formula", "python", "stack"):
        return "generic"
    return "generic"


def score_regime_fit(regime: str, strategy_style: str) -> dict:
    """给定制度与策略风格, 返回适配评分与建议。"""
    style = strategy_style if strategy_style in _FIT else "generic"
    scores = _FIT[style]
    regime_key = regime if regime in scores else "mid"
    score = scores[regime_key]

    if score >= 75:
        verdict = "适合"
        hint = f"当前{ _STYLE_LABELS[style] }策略与{_regime_label(regime)}制度匹配度较高, 可继续验证与纸面跟踪。"
    elif score >= 55:
        verdict = "一般"
        hint = f"当前制度下{ _STYLE_LABELS[style] }策略表现可能分化, 建议加强样本外与成本敏感性检查。"
    else:
        verdict = "谨慎"
        hint = f"{_regime_label(regime)}制度下{ _STYLE_LABELS[style] }策略历史适配偏弱, 可考虑换风格或降低仓位。"

    return {
        "strategy_style": style,
        "strategy_label": _STYLE_LABELS[style],
        "fit_score": score,
        "fit_verdict": verdict,
        "fit_hint": hint,
    }


def _regime_label(regime: str) -> str:
    return {"low": "低波动", "mid": "中等波动", "high": "高波动"}.get(regime, "当前")
