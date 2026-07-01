"""L3 高级研究工具.

包含三类研究员能力:
  - 因子正交化: 判断目标因子相对已有因子的新增信息量
  - 参数稳健性摘要: 判断表现是否依赖单一尖峰参数
  - 过拟合红旗检查: 汇总 IS/OOS/WF/敏感性风险
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _f(x) -> float | None:
    if x is None:
        return None
    xf = float(x)
    return None if (np.isnan(xf) or np.isinf(xf)) else xf


def orthogonalize(target: pd.Series, controls: dict[str, pd.Series]) -> dict:
    """把 target 对 controls 做线性回归, 返回残差与解释度.

    residual = target - X beta。残差保留的是不能被 controls 解释的部分。
    """
    if not controls:
        raise ValueError("至少需要一个控制因子")
    frame = pd.concat({"target": target, **controls}, axis=1).dropna()
    if frame.shape[0] < max(30, len(controls) + 5):
        raise ValueError("有效样本太少, 无法正交化")

    y = frame["target"].astype(float).to_numpy()
    x = frame.drop(columns=["target"]).astype(float).to_numpy()
    x = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    fitted = x @ beta
    resid = y - fitted
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    residual_series = pd.Series(resid, index=frame.index)
    corr_before = {
        name: _f(frame["target"].corr(frame[name]))
        for name in controls
    }
    corr_after = {
        name: _f(residual_series.corr(frame[name]))
        for name in controls
    }
    coefficients = {
        "intercept": _f(beta[0]),
        **{name: _f(beta[i + 1]) for i, name in enumerate(controls)},
    }
    return {
        "r2": _f(r2),
        "unique_ratio": _f(1.0 - r2),
        "coefficients": coefficients,
        "corr_before": corr_before,
        "corr_after": corr_after,
        "residual_stats": {
            "count": int(residual_series.shape[0]),
            "mean": _f(residual_series.mean()),
            "std": _f(residual_series.std()),
            "last": [_f(v) for v in residual_series.tail(5).tolist()],
        },
        "verdict": _orthogonal_verdict(r2),
    }


def _orthogonal_verdict(r2: float) -> str:
    if r2 >= 0.80:
        return "高度冗余: 目标因子大部分可被已有因子解释。"
    if r2 >= 0.50:
        return "部分冗余: 仍有新增信息, 但需警惕重复暴露。"
    return "新增信息较强: 目标因子与已有因子重合度较低。"


def robustness_verdict(points: list[dict], summary: dict) -> dict:
    """从敏感性点给出更直观的 L3 解释。"""
    sharpes = [float(p["sharpe"]) for p in points if p.get("sharpe") is not None]
    if not sharpes:
        return {"grade": "未知", "notes": ["没有足够有效结果。"]}
    mean = float(np.mean(sharpes))
    std = float(np.std(sharpes))
    positive = float(np.mean([s > 0 for s in sharpes]))
    peak = float(np.max(sharpes))
    median = float(np.median(sharpes))
    peakiness = peak - median

    notes = []
    if positive < 0.5:
        notes.append("多数参数变体夏普不为正, 稳健性较弱。")
    if peakiness > 1.0:
        notes.append("最佳参数明显高于中位数, 可能是参数尖峰。")
    if std > 1.0:
        notes.append("参数间表现波动大, 需要降低对单点参数的信任。")
    if not notes:
        notes.append("参数邻域表现相对平滑, 可进入更严格的样本外检查。")

    grade = "稳健" if positive >= 0.7 and peakiness <= 0.8 else "中等" if positive >= 0.5 else "脆弱"
    return {
        "grade": grade,
        "mean_sharpe": _f(mean),
        "std_sharpe": _f(std),
        "positive_ratio": _f(positive),
        "peakiness": _f(peakiness),
        "notes": notes,
        "raw_summary": summary,
    }


def overfit_check(oos: dict, walk_forward: dict, sensitivity: dict | None) -> dict:
    """汇总过拟合红旗。"""
    flags: list[dict] = []
    is_s = oos.get("in_sample", {}).get("sharpe")
    oos_s = oos.get("out_of_sample", {}).get("sharpe")
    degradation = oos.get("sharpe_degradation")
    wf_pos = walk_forward.get("summary", {}).get("positive_ratio", 0.0)
    sens_pos = (sensitivity or {}).get("summary", {}).get("positive_ratio", 0.0)

    if is_s is not None and oos_s is not None and is_s > 1.0 and oos_s <= 0:
        flags.append({"level": "high", "message": "样本内表现好, 样本外失效, 典型过拟合红旗。"})
    if degradation is not None and degradation > 0.8:
        flags.append({"level": "medium", "message": "样本外夏普相对样本内大幅衰减。"})
    if wf_pos < 0.5:
        flags.append({"level": "medium", "message": "Walk-Forward 多数分段不赚钱, 跨期一致性不足。"})
    if sensitivity and sens_pos < 0.5:
        flags.append({"level": "medium", "message": "参数扰动后多数变体失效, 可能依赖特定参数。"})
    if not flags:
        flags.append({"level": "low", "message": "未发现明显过拟合红旗, 但仍需更多标的/更长周期验证。"})

    risk_score = min(
        100,
        sum(40 if f["level"] == "high" else 25 if f["level"] == "medium" else 5 for f in flags),
    )
    if risk_score >= 70:
        grade = "高风险"
    elif risk_score >= 35:
        grade = "中风险"
    else:
        grade = "低风险"
    return {
        "risk_score": risk_score,
        "grade": grade,
        "flags": flags,
        "inputs": {
            "in_sample_sharpe": _f(is_s),
            "out_of_sample_sharpe": _f(oos_s),
            "sharpe_degradation": _f(degradation),
            "walk_forward_positive_ratio": _f(wf_pos),
            "sensitivity_positive_ratio": _f(sens_pos) if sensitivity else None,
        },
    }
