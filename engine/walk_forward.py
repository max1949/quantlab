"""样本外 / Walk-Forward 验证 (契约占位, Sprint 5 实现)。

按训练/测试滚动窗口 (如 训练 500 周期 / 测试 120 周期) 评估因子的样本外稳定性,
并支持参数敏感性、多品种、因子衰减分析所需的中间结果。
"""

# def walk_forward(factor_def, ohlcv, train=500, test=120, step=...) -> list[dict]: ...
