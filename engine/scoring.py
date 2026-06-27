"""Research Score —— 动态评分 (Sprint 6 实现)。

维度权重 (注意: 不是收益排名, 而是研究质量与稳健性):
  样本外表现 30% | 稳定性 25% | 风险控制 20% | 跨品种验证 15% | 研究质量 10%

动态衰减 (Dynamic Research Score):
  市场会变, 老因子会失效。最终分 = 基础分 × 衰减因子,
  衰减因子由近期 (最近一段) 表现决定, 防止排行榜被失效老因子长期占据。

纯函数: 输入 Sprint 5 验证结果 (oos / walk_forward / sensitivity 等 dict), 输出评分明细。
"""

from __future__ import annotations

import math

WEIGHTS = {
    "oos": 0.30,
    "stability": 0.25,
    "risk": 0.20,
    "cross_symbol": 0.15,
    "quality": 0.10,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _dimensions(validation: dict) -> dict[str, float]:
    oos = validation.get("oos") or {}
    wf = (validation.get("walk_forward") or {}).get("summary", {})
    sens = (validation.get("sensitivity") or {}).get("summary", {})
    oos_block = oos.get("out_of_sample", {}) or {}

    oos_sharpe = oos_block.get("sharpe")
    max_dd = oos_block.get("max_drawdown")

    dim_oos = _clamp((oos_sharpe or 0.0) / 1.5)
    dim_stability = _clamp(wf.get("positive_ratio", 0.0))
    # 风险控制: 回撤越小越好。-50% 回撤 -> 0 分, 0 回撤 -> 1 分。
    dim_risk = _clamp(1.0 - abs(max_dd or 0.0) / 0.5)
    # 跨品种 (V1 代理): 用参数敏感性的稳定性近似 (多品种验证后续接入)。
    dim_cross = _clamp(sens.get("positive_ratio", 0.0))
    # 研究质量: 验证流程完整度 (跑齐 OOS / WF / 敏感性)。
    completeness = sum(
        1 for k in ("oos", "walk_forward", "sensitivity") if validation.get(k)
    ) / 3.0
    dim_quality = _clamp(completeness)

    return {
        "oos": dim_oos,
        "stability": dim_stability,
        "risk": dim_risk,
        "cross_symbol": dim_cross,
        "quality": dim_quality,
    }


def _recent_performance(validation: dict) -> float:
    """近期表现: 取 Walk-Forward 最后一段的夏普 (最近时间窗)。"""
    folds = (validation.get("walk_forward") or {}).get("folds") or []
    if not folds:
        return 0.0
    last = folds[-1].get("sharpe")
    return float(last) if last is not None else 0.0


def apply_decay(base_score: float, recent_performance: float) -> float:
    """衰减因子 ∈ [0.4, 1.0]: 近期表现好 -> 接近 1; 差 -> 向 0.4 衰减。"""
    decay_factor = _clamp(0.7 + 0.3 * math.tanh(recent_performance), 0.4, 1.0)
    return decay_factor


def research_score(validation: dict) -> dict:
    """由验证结果计算 Research Score 明细 (base / decay / final + 各维度)。"""
    dims = _dimensions(validation)
    base = 100.0 * sum(WEIGHTS[k] * dims[k] for k in WEIGHTS)

    recent = _recent_performance(validation)
    decay_factor = apply_decay(base, recent)
    final = base * decay_factor

    return {
        "base_score": round(base, 2),
        "decay_factor": round(decay_factor, 4),
        "final_score": round(final, 2),
        "dimensions": {k: round(v, 4) for k, v in dims.items()},
        "weights": WEIGHTS,
        "recent_performance": round(recent, 4),
    }
