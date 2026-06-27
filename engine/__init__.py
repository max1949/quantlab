"""QuantLab 计算引擎 (纯函数库)。

设计约束 (重要):
  - 本包 **不依赖** FastAPI / SQLAlchemy / Celery / Redis 等 Web 与基础设施。
  - 只吃 pandas/numpy 数据结构, 只吐指标 / 序列 / dict。
  - 因此可脱离整个平台被独立单元测试 —— 这是"代码质量优先"的核心抓手。

模块 (骨架阶段仅声明契约, 不含实现):
  factor_engine  因子计算
  cost_model     成本模型 (手续费 / 滑点 / 冲击成本) —— 回测一等公民
  backtest       回测
  walk_forward   样本外 / Walk-Forward 验证
  scoring        Research Score (含 Decay 动态衰减)
"""
