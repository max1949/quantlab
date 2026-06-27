# engine — QuantLab 计算引擎(纯函数库)

> 关键原则:本目录与 `backend/` **同级**,且**不依赖** Web 框架 / 数据库 / 队列。
> 它只接收 `pandas`/`numpy` 数据,返回指标与序列,因此可被 Worker、沙箱复用,并能独立做单元测试。

## 模块

| 文件 | 职责 | 落地 Sprint |
|---|---|---|
| `factor_engine.py` | 因子计算(模板 / 组合器 / Python) | Sprint 3 ✅ |
| `cost_model.py` | 成本模型(手续费 / 滑点 / 冲击成本) | Sprint 4 ✅ |
| `backtest.py` | 回测(收益 / 风险 / 交易指标 + 净值) | Sprint 4 ✅ |
| `report.py` | 研究报告(假设 / 方法 / 结果 / 结论) | Sprint 4 ✅ |
| `walk_forward.py` | OOS / Walk-Forward / 敏感性 / 稳健性评分 | Sprint 5 ✅ |
| `scoring.py` | Research Score 五维加权 + 动态衰减(Decay) | Sprint 6 ✅ |
| `ai_advisor.py` | LLM 提示词构造 + 确定性本地分析(无网络) | Sprint 7 ✅ |
| `research_report.py` | 研究项目报告(因子+回测+验证→叙事) | Sprint 8 ✅ |

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

## cost_model / backtest / report（Sprint 4 已实现）

- `cost_model.CostConfig(fee_rate, slippage_bps)` + `apply_costs(positions, cfg)`:按换手量计交易成本(成本是回测一等公民)。
- `backtest.run_backtest(signal, ohlcv, cost_config)`:信号取符号成仓位(上期仓位避免前视),
  扣成本算净值,输出 `metrics`(总/年化收益、年化波动、夏普、最大回撤、胜率、交易次数、换手)+ `equity_curve`。
- `report.build_research_report(...)`:由因子元信息 + 成本 + 指标 + 数据快照合成研究报告
  (假设/方法/结果/结论 + Markdown),评级看风险调整后表现而非单看收益。

## walk_forward（Sprint 5 已实现）

把"一次回测"升级为"可信验证",抑制过拟合。输入 `compute_signal(df)->Series` 闭包,
在各切片上**独立**算信号(避免泄漏):

- `evaluate_oos(...)`:样本内/样本外 holdout 对比 + 夏普衰减。
- `walk_forward(..., n_splits)`:时间线分段逐段回测,看跨期一致性(positive_ratio)。
- `sensitivity(variants, ...)`:参数扰动下表现是否稳定(而非单点尖峰)。
- `robustness_score(oos, wf, sens)`:综合 0–100 稳健性评分 + 评级(稳健/中等/偏弱/脆弱)。

## scoring（Sprint 6 已实现）

把验证结果转成可排名的 **Research Score**,强调研究质量与稳健性,而非裸收益。

- `research_score(validation)`:五维加权(样本外 30% · 稳定性 25% · 风控 20% · 跨品种 15% · 研究质量 10%),
  各维归一到 0–1,加权得 0–100 基础分;输出 `base_score / decay_factor / final_score / dimensions`。
- `apply_decay(base, recent_performance)`:**动态衰减** ∈ [0.4, 1.0],由近期(Walk-Forward 最后一段)表现决定。
  市场会变、老因子会失效 → `final = base × decay`,防止失效老因子长期霸榜。

## ai_advisor（Sprint 7 已实现）

引擎层只做**纯计算**(不联网):把研究产物拼成提示词,并给出一套确定性的规则分析,
保证"没配 LLM 也能用、且可测"。真正的网络调用在 `backend/app/services/llm_client.py`。

- `build_validation_review_prompt(ctx)` / `build_backtest_summary_prompt(ctx)`:构造 `system`+`user` 提示词。
- `local_validation_review(ctx)`:由 OOS/WF/敏感性/稳健性推导优点 / 风险(尤其过拟合) / 改进建议 + markdown。
- `local_backtest_summary(ctx)`:由回测指标给通俗总结(关键表现 / 注意事项 / 下一步)。
- `local_research_plan(theme)` / `build_research_plan_prompt(theme)`(Sprint 8):**研究指导** ——
  给一个方向,产出研究假设(对应可量化因子)+ 推荐实验(窗口/敏感性/样本外/跨品种)+ markdown。
- 强调研究过程与稳健性,只给研究方法 / 改进建议,**不给买卖信号、不承诺收益**。

## research_report（Sprint 8.1 已实现）

把一个因子的研究全过程(因子定义 + 回测 + 科学验证)**聚合成一篇人话研究报告**:

- `build_project_report(factor, symbol, backtest_metrics, validation, snapshot, ai_suggestions)`
  → 标题(自动,如「RB · 20日动量「mom20」研究」)/ 研究假设 / 实验(含可复现快照)/
  结果(样本内外对比 + 评级)/ 风险 / 下一步建议 + 完整 markdown + 阶段完成度。
- 与 `report.py`(单次回测的指标报告)分工:这里面向**研究项目**,给小白看懂"研究讲了什么、靠不靠谱、下一步做什么"。
- `TEMPLATE_LABELS`:模板类型→中文方向标签(供研究员主页方向标签聚合复用)。

## 测试

引擎层每个模块都应有对应的 `tests/`(纯函数,易于断言)。

```bash
cd backend && pytest            # 已把 ../engine/tests 纳入默认 testpaths
# 或仅跑引擎: cd backend && pytest ../engine/tests
```
