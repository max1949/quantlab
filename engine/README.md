# engine — QuantLab 计算引擎(纯函数库)

> 关键原则:本目录与 `backend/` **同级**,且**不依赖** Web 框架 / 数据库 / 队列。
> 它只接收 `pandas`/`numpy` 数据,返回指标与序列,因此可被 Worker、沙箱复用,并能独立做单元测试。

## 模块

| 文件 | 职责 | 落地 Sprint |
|---|---|---|
| `factor_engine.py` | 因子计算(模板 / 组合器 / Python) | Sprint 3 ✅ |
| `cost_model.py` | 成本模型(手续费 / 滑点 / 冲击成本) | Sprint 4 |
| `backtest.py` | 回测(收益 / 风险 / 交易指标 + 净值) | Sprint 4 |
| `walk_forward.py` | OOS / Walk-Forward / 敏感性 / 衰减 | Sprint 5 |
| `scoring.py` | Research Score + 动态衰减(Decay) | Sprint 5–6 |

## factor_engine（Sprint 3 已实现）

模板因子(`TEMPLATES` 注册表,均输出与行情索引对齐的 `Series`):

| code | 说明 | 参数 |
|---|---|---|
| `momentum` | 过去 N 期收益率 | `window` |
| `sma_ratio` | 价格相对 N 期均线偏离 | `window` |
| `rsi` | 相对强弱指标 0–100 | `window` |
| `volatility` | 收益率滚动标准差 | `window` |
| `mean_reversion` | 价格对均值的负向 z-score | `window` |

核心函数:

- `compute_template_factor(df, factor_type, params)` — 计算模板因子
- `validate_template_params(factor_type, params)` — 参数校验/补默认
- `standardize(series)` — z-score(组合前归一化)
- `compute_factor_stack([(series, weight), ...])` — 组合器:标准化后按权重(绝对值归一)线性组合
- `summarize(series)` — JSON 友好的摘要统计
- `sample_price_frame(n, seed)` — **确定性**样本行情(真行情 Sprint 4 接 Parquet)

## 测试

引擎层每个模块都应有对应的 `tests/`(纯函数,易于断言)。

```bash
cd backend && pytest            # 已把 ../engine/tests 纳入默认 testpaths
# 或仅跑引擎: cd backend && pytest ../engine/tests
```
