"""Research Score —— 动态评分 (契约占位, Sprint 5/6 实现)。

维度权重 (注意: 不是收益排名):
  样本外表现 30% | 稳定性 25% | 风险控制 20% | 跨品种验证 15% | 研究质量 10%

动态衰减 (Dynamic Research Score):
  市场会变, 老因子会失效。最终分需乘以"近期有效性"衰减:
      final_score = base_score * decay_factor
  其中 decay_factor 由因子近期(滚动窗口)表现计算, 防止排行榜被失效老因子占满。
"""

# def research_score(backtest_result, validation_runs) -> dict: ...
# def apply_decay(base_score, recent_performance) -> float: ...
