# engine — QuantLab 计算引擎(纯函数库)

> 关键原则:本目录与 `backend/` **同级**,且**不依赖** Web 框架 / 数据库 / 队列。
> 它只接收 `pandas`/`numpy` 数据,返回指标与序列,因此可被 Worker、沙箱复用,并能独立做单元测试。

## 模块

| 文件 | 职责 | 落地 Sprint |
|---|---|---|
| `factor_engine.py` | 因子计算(模板 / 组合器 / Python) | Sprint 3 |
| `cost_model.py` | 成本模型(手续费 / 滑点 / 冲击成本) | Sprint 4 |
| `backtest.py` | 回测(收益 / 风险 / 交易指标 + 净值) | Sprint 4 |
| `walk_forward.py` | OOS / Walk-Forward / 敏感性 / 衰减 | Sprint 5 |
| `scoring.py` | Research Score + 动态衰减(Decay) | Sprint 5–6 |

## 测试

引擎层每个模块都应有对应的 `tests/`(纯函数,易于断言)。骨架阶段仅占位。

```bash
cd backend && pytest ../engine/tests
```
