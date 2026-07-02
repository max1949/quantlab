"""研究质量闸门 — 判断因子是否达到「可发布 / 可分享」标准。

目标: 把「回测好看」和「可能经得起样本外 + 封印段检验」分开,
减少广场上的幻觉因子。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityThresholds:
    min_oos_sharpe: float = 0.15
    min_robustness_score: float = 50.0
    min_backtest_sharpe: float = 0.0
    require_sealed_holdout_positive: bool = True
    min_sealed_holdout_sharpe: float = 0.0
    max_turnover: float | None = 80.0
    min_abs_ic: float | None = None
    allowed_robustness_grades: frozenset[str] = frozenset({"稳健", "中等"})


@dataclass
class QualityVerdict:
    passed: bool
    reasons: list[str]
    scorecard: dict


def evaluate_sealed_holdout_metrics(sealed: dict | None) -> float | None:
    if not sealed or sealed.get("skipped"):
        return None
    metrics = sealed.get("metrics") or {}
    s = metrics.get("sharpe")
    return float(s) if s is not None else None


def assess_publish_readiness(
    *,
    backtest_metrics: dict | None,
    validation_status: str | None,
    validation_oos: dict | None,
    validation_robustness: dict | None,
    thresholds: QualityThresholds | None = None,
) -> QualityVerdict:
    """根据最新回测 + 验证结果给出是否允许公开发布。"""
    th = thresholds or QualityThresholds()
    reasons: list[str] = []

    if validation_status != "success":
        reasons.append("需要完成并通过科学验证")

    oos_sharpe = None
    if validation_oos:
        oos_sharpe = (validation_oos.get("out_of_sample") or {}).get("sharpe")
    if oos_sharpe is None:
        reasons.append("缺少样本外夏普结果")
    elif float(oos_sharpe) < th.min_oos_sharpe:
        reasons.append(f"样本外夏普 {float(oos_sharpe):.2f} 低于门槛 {th.min_oos_sharpe:.2f}")

    rob_score = None
    rob_grade = None
    if validation_robustness:
        rob_score = validation_robustness.get("score")
        rob_grade = validation_robustness.get("grade")
    if rob_score is None:
        reasons.append("缺少稳健性评分")
    elif float(rob_score) < th.min_robustness_score:
        reasons.append(
            f"稳健性评分 {float(rob_score):.1f} ({rob_grade or '?'}) "
            f"低于发布门槛 {th.min_robustness_score:.1f}"
        )
    elif rob_grade and rob_grade not in th.allowed_robustness_grades:
        allowed = "、".join(sorted(th.allowed_robustness_grades))
        reasons.append(f"稳健性评级「{rob_grade}」未达发布标准 (需 {allowed})")

    bt_sharpe = (backtest_metrics or {}).get("sharpe")
    if bt_sharpe is None:
        reasons.append("需要成功的回测结果")
    elif float(bt_sharpe) < th.min_backtest_sharpe:
        reasons.append(f"全样本回测夏普 {float(bt_sharpe):.2f} 需 ≥ {th.min_backtest_sharpe:.2f}")

    bt_turnover = (backtest_metrics or {}).get("turnover")
    if th.max_turnover is not None and bt_turnover is not None:
        if float(bt_turnover) > th.max_turnover:
            reasons.append(
                f"回测换手率 {float(bt_turnover):.1f} 超过发布门槛 {th.max_turnover:.1f} "
                "（中频成本敏感，实盘易打折）"
            )

    ic_mean = None
    if validation_robustness:
        ic_block = validation_robustness.get("factor_ic") or {}
        ic_mean = ic_block.get("ic_mean")
    if th.min_abs_ic is not None:
        if ic_mean is None:
            reasons.append("缺少因子 IC 结果")
        elif abs(float(ic_mean)) < th.min_abs_ic:
            reasons.append(
                f"因子 IC {float(ic_mean):.3f} 绝对值低于门槛 {th.min_abs_ic:.3f}（预测力偏弱）"
            )

    sealed = (validation_robustness or {}).get("sealed_holdout")
    sealed_sharpe = evaluate_sealed_holdout_metrics(sealed)
    if th.require_sealed_holdout_positive:
        if sealed_sharpe is None:
            reasons.append("封印 holdout 段数据不足或尚未计算")
        elif sealed_sharpe < th.min_sealed_holdout_sharpe:
            reasons.append(
                f"封印 holdout 段夏普 {sealed_sharpe:.2f} 未达门槛 "
                f"{th.min_sealed_holdout_sharpe:.2f}（该段未参与调参）"
            )

    scorecard = {
        "backtest_sharpe": bt_sharpe,
        "backtest_turnover": bt_turnover,
        "oos_sharpe": oos_sharpe,
        "robustness_score": rob_score,
        "robustness_grade": rob_grade,
        "sealed_holdout_sharpe": sealed_sharpe,
        "ic_mean": ic_mean,
    }
    return QualityVerdict(passed=len(reasons) == 0, reasons=reasons, scorecard=scorecard)
