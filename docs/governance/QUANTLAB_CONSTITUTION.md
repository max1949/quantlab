# QuantLab Constitution v2.0

**Document status:** Owner-approved · Canonical SSOT  
**Canonical path:** `docs/governance/QUANTLAB_CONSTITUTION.md`  
**Subtitle:** Strategy Research & Evidence OS — NautilusTrader Kernel  
**Effective:** Constitution v2.0 recorded in-repo (governance ingest only)

```text
Canonical intent: 将 QuantLab 从“量化功能集合 / Nautilus 中文界面”升级为长期可积累的 Strategy Research & Evidence OS（策略研究与证据操作系统）。

Owner direction: APPROVED AS STRATEGIC DIRECTION
Repository merge status: GOVERNANCE DOCS ONLY (this ingest)
Engineering execution: HOLD UNTIL SEPARATELY AUTHORIZED
Production change: DENY
Live trading: DENY
Autonomous expansion: DENY
Next executable step when authorized: QLN-0 READ_ONLY RECONCILIATION
```

---

## 0. 宪法效力与解释顺序

本宪法定义 QuantLab 的长期使命、边界、系统架构、证据标准、风险原则与开发顺序。

本宪法不抹掉历史 Roadmap、Sprint、Phase、生产数据和已完成代码；历史工作全部视为待复用资产。

旧 `QUANTLAB_NAUTILUS_EVOLUTION` Phase 0–7 保留为**历史路线编号**，不再作为未来阶段编号继续扩展。

自本宪法生效后，新建设统一采用 `QLN-0` → `QLN-12` 编号，避免与历史 Phase 混淆。

若旧 Roadmap、旧文档、历史实现与本宪法冲突：

- 事实记录以真实生产/代码/数据库证据为准；
- 产品方向与未来开发权限以本宪法为准。

任何阶段均不得因“已经写了很多代码”而自动取得下一阶段权限。

Silence ≠ Approval。Previous work ≠ Permission to continue。

每个阶段完成后默认状态为 STOP / HOLD，必须重新过 Gate 才能进入下一阶段。

---

## 1. 使命、终局与北极星

### 1.1 产品终局

QuantLab 的长期定位**不是**：

- NautilusTrader 中文版；
- AI 自动赚钱机器人；
- 策略信号商城；
- 交易所或 Broker 替代品；
- 为了展示技术而不断增加功能的量化平台。

QuantLab 的终局定位是：

**Strategy Research & Evidence OS**  
负责策略从“研究假设”到“可复现证据、Paper、Shadow、Canary、Live、长期退化监控、淘汰与知识沉淀”的完整生命周期。

NautilusTrader 的定位是：

**Trading / Backtest / Execution Kernel**  
提供事件驱动内核、策略运行、回测、订单、成交、Portfolio、RiskEngine、ExecutionEngine、DataEngine、MessageBus、适配器和 Live 状态恢复等底层能力。

QuantLab 必须始终拥有自己的领域层，不允许把产品定义绑定在 Nautilus 内部 API 上。

### 1.2 北极星

QuantLab 不以以下数字为北极星：

- AI 生成了多少策略；
- 跑了多少次回测；
- 策略库有多少条；
- UI 有多少页面；
- 支持多少指标。

真正北极星是：

**Evidence Density：** 单位策略所拥有的可重现、可反证、可解释、可长期追踪的真实证据密度。

长期应关注：

- 可100%重现实验比例；
- OOS / Walk Forward / Stress / Paper / Shadow 各层通过率；
- 被主动淘汰的无效策略数量；
- Paper→Live 漂移率；
- Live 策略稳定存活时间；
- 实盘与理论行为差异；
- 研究成本 / 晋级策略；
- 失败研究被未来复用的比例；
- 用户从“想法”到“可信结论”的时间。

---

## 2. 与 Growth OS / TMOS 的长期关系

三套系统不得互相重复造轮子。

### 2.1 Growth OS

职责：发现、归因、获客、入口与增长。

### 2.2 TMOS

职责：**Trader Evidence OS**

长期积累：

- 交易员计划；
- 执行行为；
- 风险行为；
- 复盘质量；
- 纪律性；
- 长期业绩证据；
- 人才成长与验证履历。

### 2.3 QuantLab

职责：**Strategy Evidence OS**

长期积累：

- 策略假设；
- Strategy Spec；
- 实验记录；
- 参数版本；
- 数据版本；
- OOS / Walk Forward；
- Paper / Shadow / Live；
- 策略退化；
- 容量；
- 市场环境；
- 淘汰原因；
- 组合关系。

### 2.4 长期协同终局

最终形成：

**Trader Intelligence × Strategy Intelligence × Track Record × Risk Behavior × Capital**

未来重要能力：

**Trader–Strategy Fit** — 回答：什么样的人，更适合执行什么样的策略？

**Strategy Adherence** — 比较：策略要求怎么做；交易员实际怎么做。输出策略遵循度，而不是只输出盈亏。

**Loss Attribution** — 将亏损尽可能归因于：

- 正常策略损失；
- 策略缺陷；
- 参数失配；
- 数据异常；
- 滑点/成交问题；
- Broker 故障；
- 软件缺陷；
- 人工干预；
- 纪律偏差；
- 组合集中风险。

QuantLab 与 TMOS 的融合必须以结构化证据为接口，不允许形成强耦合数据库泥团。

---

## 3. 非目标（NON-GOALS）

以下事项默认不属于 QuantLab 当前目标：

- 不承诺任何策略赚钱。
- 不宣称 AI 能发现“稳赢策略”。
- 不以预测涨跌、荐股、喊单作为核心产品价值。
- 不默认替用户托管交易资金。
- 不自建交易所。
- 不重新发明完整交易执行内核。
- 不为追求功能数量重复实现 Nautilus 已稳定提供的底层组件。
- 不一开始建设 Strategy Marketplace。
- 不允许 AI 生成代码后直接进入真实资金执行。
- 不允许无界限的“自主研发直到找到赚钱策略”。
- 不允许因为回测曲线漂亮跳过 OOS / Paper / Shadow。
- 不允许因为用户愿意承担风险而绕过系统安全 Gate。
- 不允许将 Backtest/Paper/Shadow 业绩包装为 Live Track Record。
- 不允许任何 UI 直接持有 Broker 私钥或直接下发交易所订单。

---

## 4. 核心架构宪法

Canonical architecture：

```text
Web UI → QuantLab Domain API → Governance/Evidence/Risk → Engine Interface → Nautilus Adapter → NautilusTrader → Data/Broker
```

严禁：

- React/UI → Nautilus internal class 直接耦合。

### 4.1 四个平面

**Control Plane** 负责：

- Strategy Spec；
- 参数；
- 策略版本；
- 实验定义；
- Gate；
- 调度；
- 权限；
- 部署状态。

**Data Plane** 负责：

- 历史行情；
- 实时行情；
- 自定义数据；
- 数据版本；
- Data Trust；
- 数据 provenance。

**Execution/Event Plane** 负责：

- Signal；
- Command；
- Order；
- Fill；
- Position；
- Portfolio；
- Risk Event；
- Replay Event。

**Secret Plane**

Broker/API/AI/Data 凭证必须独立管理。

原则：

- 前端永远不返回完整 secret；
- Strategy Package 永不携带 secret；
- Secret 具备权限、轮换、失效和审计；
- 用户删除/撤销后必须能确认失效。

---

## 5. Engine Abstraction Constitution

QuantLab 永远通过自己的 Engine Interface 调用 Nautilus。

建议抽象：

- BacktestEngineAdapter
- PaperEngineAdapter
- ShadowEngineAdapter
- LiveEngineAdapter
- DataCatalogAdapter
- BrokerCapabilityAdapter
- ExecutionReportAdapter

### 5.1 目的

- 防止 Nautilus v1/v2 API 变化扩散到 UI 与业务层。
- 允许 Golden Strategy 做旧/新 Engine parity test。
- 保留未来替换研究引擎或增加专用研究内核的可能性。
- 不允许为“多引擎”而设计过度抽象；Nautilus 是默认主内核。

### 5.2 Engine Compatibility Lab

任何 Nautilus 大版本升级前必须：

- 固定 Golden Datasets；
- 固定 Golden Strategies；
- 固定 Golden Experiment Specs；
- 旧引擎、新引擎并行运行；
- 对比 signals/orders/fills/positions/PnL/risk decisions；
- 只有 `ENGINE_PARITY=PASS` 才可升级。

---

## 6. Strategy Spec v2 — 策略的 Canonical Truth

策略的唯一真相不得是某个 Python 文件。

必须存在独立、稳定、版本化的 Strategy Spec。

建议至少包含：

### 6.1 Identity

- strategy_id
- name
- owner
- version
- parent_version
- created_at
- status
- tags

### 6.2 Thesis

- edge hypothesis
- intended market behavior
- expected source of return
- invalidation logic

### 6.3 Universe / Instrument

- venue class
- instruments
- quote/base currency
- synthetic instrument formula（如有）

### 6.4 Data Requirements

- data type
- timeframe
- bar/tick/book requirement
- warmup
- custom data
- timezone policy
- trading calendar

### 6.5 Signal Logic

- entry conditions
- exit conditions
- filters
- state machine
- signal priority

### 6.6 Position Sizing

- fixed quantity
- risk-based sizing
- volatility sizing
- capital allocation ceiling

### 6.7 Risk

- risk per trade
- stop logic
- max concurrent positions
- daily loss limit
- drawdown limits
- exposure limits
- leverage limits

### 6.8 Execution

- order types
- time in force
- reduce-only
- slippage model
- latency assumptions
- contingency order requirements

### 6.9 Regime

- intended regimes
- forbidden regimes
- regime classifier reference

### 6.10 Capacity Assumptions

- expected turnover
- liquidity requirements
- participation rate assumptions
- estimated capital capacity

### 6.11 Compatibility

- required broker capabilities
- required data capabilities
- required engine features

### 6.12 Implementation Reference

Spec 可引用实现，但实现不能取代 Spec。

---

## 7. Strategy Contract / Invariants

每个正式策略必须有一份机器可执行的 Strategy Contract。

至少定义：

- WHAT：做什么；
- WHY：理论依据；
- WHEN：什么时候允许运行；
- WHEN NOT：什么时候禁止运行；
- RISK：允许承担什么风险；
- EXPECTED：正常表现区间；
- ABNORMAL：异常定义；
- INVALIDATION：什么证据代表假设失效；
- RETIREMENT：何时永久淘汰。

### 7.1 Invariants 示例

- 不允许 Martingale；
- 不允许亏损摊平（除非策略定义明确且通过专门审批）；
- 单笔风险不得突破上限；
- 数据过期不得开仓；
- 账户状态 UNKNOWN 不得开仓；
- reconciliation 未通过不得恢复；
- 超出 Broker capability 不得启动；
- 风险 Gate 不得被 Strategy 自己绕过。

Invariant 必须高于策略逻辑。

---

## 8. Strategy Package — 策略必须可移植

每个策略应支持导入/导出为独立包，例如：

```text
manifest.yaml
strategy_spec.json
risk_contract.json
parameters.json
data_requirements.json
validation_summary.json
lineage.json
README.md
```

规则：

- 不包含 secret；
- 可 hash；
- 可签名；
- 可 Git/version control；
- 可跨服务器迁移；
- 十年后仍可解释；
- 包格式版本独立于 Nautilus 版本。

---

## 9. Experiment Ledger — 所有结果必须可重现

任何回测、参数搜索、OOS、Walk Forward、Stress、Paper evaluation 都必须产生不可变 Experiment Record。

至少记录：

- experiment_id；
- strategy_spec_hash；
- strategy implementation hash；
- code commit；
- engine name/version；
- adapter version；
- dataset ID/version/hash；
- instrument metadata version；
- timezone/calendar/bar aggregation rule；
- fee model；
- slippage model；
- latency/execution assumptions；
- parameters；
- random seed；
- start/end；
- environment；
- AI model/prompt version（若AI参与）；
- CPU/runtime/resource usage；
- AI cost；
- market data cost；
- output metrics；
- artifact hashes；
- parent experiment；
- final decision。

### 9.1 One-click Reproduce

任何保存的实验必须尽可能支持：一键重现实验。

无法重现的漂亮结果不得晋级高 Evidence Level。

---

## 10. Time Governance

系统 canonical timestamp 统一使用 UTC 高精度时间。

UI 再进行本地化显示。

实验必须固定并记录：

- timezone；
- trading session；
- calendar；
- DST handling；
- bar boundary；
- funding time；
- holiday/session policy。

任何时间规则变化都必须触发新版本或重新验证。

---

## 11. Data Trust Gate

任何实验在计算收益前先证明数据可信。

至少检查：

- schema；
- monotonic time；
- duplicate records；
- missing intervals；
- outliers；
- impossible prices；
- timezone；
- instrument metadata；
- symbol mapping；
- corporate actions（适用时）；
- futures roll（适用时）；
- funding（适用时）；
- data source provenance。

只有：

`DATA_TRUST_GATE=PASS`

才允许产生高可信 Evidence。

数据不完美时可以继续研究，但必须显式降级证据，而不是静默忽略。

---

## 12. Evidence Pipeline — 策略晋级/淘汰主骨架

Canonical lifecycle：

```text
IDEA → DRAFT → STATIC_VALIDATED → DATA_VALIDATED → BACKTEST → OOS → WALK_FORWARD → STRESS → PAPER → SHADOW → CANARY → LIVE → MATURE / DEGRADED / RETIRED
```

### 12.1 任何阶段均允许 KILL

失败不是产品失败。

主动淘汰错误策略就是 QuantLab 的价值。

### 12.2 禁止自动跳级

不得：

- Backtest→Live；
- Paper→大资金 Live；
- AI Generated→Live；
- Owner 手工点击绕过安全 Gate。

### 12.3 Evidence Levels

可建立：

- E0：Idea/Draft
- E1：Backtest reproducible
- E2：OOS + robustness
- E3：Walk Forward + stress
- E4：Paper verified
- E5：Shadow verified
- E6：Canary live verified
- E7：Mature live evidence

最终级别以真实实现与统计要求再固化，不允许为了让策略升级而降低门槛。

---

## 13. Reality Score

回测报告除了收益必须提供“现实可信度”。

维度可以包括：

- data quality；
- fee realism；
- slippage realism；
- liquidity constraint；
- fill realism；
- latency assumption；
- sample length；
- OOS quality；
- parameter stability；
- capacity realism。

Reality Score 不是营销分数，而是证据质量表达。

低 Reality Score 的高收益回测不得进入高等级 Evidence。

---

## 14. Research Debt

每个策略必须显示尚未完成的验证债务。

例如：

- 没做 OOS；
- 没做 Walk Forward；
- 没做 fee stress；
- 没做 parameter stability；
- 没做 extreme regime test；
- 没做 Paper；
- 没验证容量。

Research Debt：`LOW` / `MEDIUM` / `HIGH` / `BLOCKING`。

存在 `BLOCKING` debt 时，后续 Stage 自动 DENY。

---

## 15. Strategy DNA

每个策略生成长期结构化画像：

- style；
- timeframe；
- turnover；
- direction；
- edge source；
- average holding；
- return skew；
- win rate/payoff；
- tail profile；
- best/worst regime；
- factor exposure；
- correlation；
- drawdown；
- capacity；
- liquidity dependency；
- behavioral requirements。

用途：

- 策略比较；
- 策略去重；
- 组合构建；
- Trader–Strategy Fit；
- AI Research Memory。

---

## 16. Strategy Genealogy

所有策略必须保留祖先和唯一变量变化。

系统应能回答：

> v8 相对 v7 到底改了什么？为什么结果改变？

规则：

- Strategy clone 必须建立 parent link；
- 参数变化形成 diff；
- 逻辑变化形成 semantic diff；
- AI 派生也必须建立 lineage；
- 禁止制造无法追溯的“策略1、策略2、策略3”。

---

## 17. Strategy Graveyard / Negative Result Database

淘汰策略不得删除。

必须记录：

- 失败在哪一 Gate；
- 失败原因；
- 使用数据；
- 关键实验；
- 是否未来允许重新研究；
- 与其他失败研究的关系。

长期价值：

AI 生成想法会越来越便宜，真正稀缺的是知道什么已经失败过、为什么失败。

Research Agent 在创建新研究前必须先查 Graveyard / Research Memory，避免重复浪费。

---

## 18. Counterfactual Lab

允许对单笔交易或阶段表现做“如果当时……”分析，但必须防止单笔 hindsight overfit。

例如：

- 止损 2ATR→2.5ATR；
- entry delay；
- position size；
- filter on/off。

任何局部反事实必须同时给出全样本影响。

系统应明确区分：

- “这一笔会更好”
- 与
- “整体策略会更好”。

---

## 19. Market Regime Layer

QuantLab 不把 Regime 用作“预测必涨必跌”。

Regime 的主要用途：判断当前环境与策略历史有效环境是否匹配。

可包括：

- trend/chop；
- high/low volatility；
- liquidity state；
- correlation regime；
- extreme/dislocation。

策略必须能记录：

- best regimes；
- weak regimes；
- forbidden regimes。

---

## 20. Capacity Estimation

策略不能只看收益率。

必须逐步估计：

- turnover；
- liquidity；
- market participation；
- slippage elasticity；
- capital scaling curve；
- estimated capacity band。

长期比较策略必须加入“能承载多少资本”，而不是只排名 CAGR。

---

## 21. Portfolio Governor

QuantLab 风控不能停留在“每个策略各自有止损”。

Portfolio Governor 负责：

- capital allocation；
- total exposure；
- leverage；
- correlated strategy cluster；
- instrument concentration；
- venue concentration；
- factor/style concentration；
- drawdown budget；
- liquidity budget；
- dynamic de-risking。

用户未来更适合输入：我愿意承担多大组合风险。

系统再反推各策略预算，而不是用户机械给每个机器人分配资金。

### 21.1 Strategy Crowding / Risk Clustering

18个策略不等于18种风险。

系统应聚类实际风险来源，识别例如：

- Crypto Momentum；
- Trend；
- Mean Reversion；
- Carry；
- Relative Value。

Portfolio Governor 控制的是实际风险暴露，而不是策略数量。

---

## 22. Broker Capability Matrix

每个 Broker/Venue Adapter 必须维护能力矩阵。

包括但不限于：

- order types；
- OCO/OTO/OUO；
- reduce-only；
- hedge mode；
- trailing stop；
- GTD；
- native TP/SL；
- position modes；
- rate limits；
- reconciliation support；
- sandbox/testnet support。

策略启动前必须：

`STRATEGY_REQUIREMENTS ⊆ BROKER_CAPABILITIES`

否则：

`BROKER_COMPATIBILITY_GATE=DENY`

---

## 23. 参数变更治理

参数分为：

- **Class A — 展示参数**：可即时修改，不改变交易行为。
- **Class B — Strategy Behavior**：必须形成新策略版本，并至少重新跑规定验证。
- **Class C — Risk-Critical**：必须新版本 + 审计 + Risk Gate + 权限确认。
- **Class D — Broker/Execution/Secret**：高权限，不允许普通 UI 热修改。

原则：

绝不“覆盖旧策略”。所有实质变化产生新版本。

---

## 24. 四种执行模式

策略产品语义必须区分：

- **MANUAL** — 系统提供规则/验证，人执行。
- **ADVISORY** — 系统提供建议与检查，不发单。
- **ASSISTED** — 人确认，机器执行。
- **AUTOMATED** — 机器根据已批准 Strategy Contract 自动执行。

这使 QuantLab 可服务 TMOS 手工交易员，而不是强迫所有人变成量化机器人用户。

---

## 25. Simulation / Live Evidence 必须永久分离

所有 UI、报告、Passport 强制标识：

- BACKTEST
- OOS
- WALK_FORWARD
- PAPER
- SHADOW
- CANARY
- LIVE

禁止：

- 将模拟收益混入真实业绩；
- 在聚合报表中弱化证据来源；
- 用 Backtest Equity 伪装 Track Record。

证据来源是一级字段，不是 UI 小标签。

---

## 26. AI Strategy Scientist

AI 不能只是一个聊天框。

建议内部角色：

- Researcher
- Risk Officer
- Overfit Hunter
- Execution Analyst
- Portfolio Manager
- Skeptic

### 26.1 AI Committee

策略晋级可以输出：

- Research：PASS/HOLD/FAIL
- Risk：PASS/HOLD/FAIL
- Overfit：PASS/HOLD/FAIL
- Execution：PASS/HOLD/FAIL
- Portfolio：PASS/HOLD/FAIL

AI 的结论只是分析层，最终机器 Gate 仍由可验证规则裁决。

### 26.2 Autonomous Research Loop

允许：

```text
Hypothesis → Experiments → Analysis → Counter-test → Next experiment → STOP
```

但必须满足：

- bounded scope；
- experiment budget；
- CPU budget；
- AI token budget；
- data budget；
- maximum iterations；
- explicit stopping rule。

合法结论包括：

`NO EDGE FOUND` / `EVIDENCE INSUFFICIENT`。

严禁 AI 无限优化直到得到漂亮曲线。

---

## 27. Research Cost Attribution

每个实验逐步记录：

- CPU cost；
- storage cost；
- market data cost；
- AI cost；
- wall time。

长期形成：

- cost per experiment；
- cost per validated hypothesis；
- cost per promoted strategy；
- Research ROI。

一人公司模式要求研究自动化必须有成本上限。

---

## 28. Data Plugin / Custom Data

QuantLab 应在稳定主干后支持结构化插件：

- Funding；
- OI；
- Liquidations；
- Book imbalance；
- Options IV/Greeks；
- On-chain；
- Macro；
- Sentiment；
- 用户 custom signal。

插件必须通过 Data Contract、Schema、Time Governance、Data Trust Gate。

不允许第三方数据插件直接拥有执行权限。

---

## 29. Synthetic Lab

后期可以提供可视化 Synthetic Instrument Builder：

- ratios；
- spreads；
- baskets；
- beta-neutral combinations；
- cross-venue spreads。

Synthetic 是研究资产，不应成为早期建设优先级。

---

## 30. Shadow Twin — 策略数字孪生

任何重要实盘策略长期应拥有只读 Shadow Twin。

比较：

- theoretical signal vs live signal；
- theoretical order vs live order；
- theoretical fill vs actual fill；
- theoretical position vs actual position；
- theoretical PnL vs actual PnL。

检测：

- SIGNAL_DIVERGENCE；
- ORDER_DIVERGENCE；
- POSITION_DIVERGENCE；
- PNL_DIVERGENCE。

其目的不是制造第二套交易，而是证明 Live 行为仍符合研究证据。

---

## 31. Flight Recorder / Replay

任何 Paper/Shadow/Canary/Live 重大事件必须能重放。

记录至少包括：

- market event；
- signal；
- strategy decision；
- risk decision；
- order command；
- broker acknowledgement；
- fill；
- position；
- reconciliation event；
- manual intervention。

并绑定：

- strategy version；
- config hash；
- code hash；
- data version；
- engine version；
- adapter version。

事故分析优先 Replay，不允许依赖猜测。

---

## 32. Live Safety Constitution

Live 是最后阶段，不是产品 MVP。

### 32.1 Reconciliation First

任何 Live 启动或恢复：

- internal orders；
- broker orders；
- internal positions；
- broker positions；
- account state；

必须对齐。

`RECONCILIATION != PASS` → `NEW_RISK = DENY`

### 32.2 Dead-Man Switch

控制层失联、数据异常、健康证明失效时：

- 默认禁止新增风险；
- 根据策略契约决定保持/减仓/退出；
- 绝不在 UNKNOWN 状态自动扩大风险。

### 32.3 Kill Switch

必须具备：

- strategy stop；
- no-new-position；
- reduce-only；
- account/global halt。

### 32.4 One Runtime Ownership

每个 live runtime 必须有明确单一 owner/process/service，禁止隐形重复运行。

### 32.5 Secrets

任何 live secret 不得进入：

- Git；
- Strategy Package；
- Experiment artifacts；
- frontend logs；
- AI prompts。

---

## 33. Chaos Lab

进入真实资金前必须主动破坏：

- market data disconnect；
- broker disconnect；
- network latency；
- API timeout；
- rate limit；
- duplicate event；
- out-of-order event；
- process crash；
- server reboot；
- cache outage；
- database outage；
- disk full；
- partial fill；
- unknown order outcome；
- reconciliation discrepancy。

验证：

- 是否重复下单；
- 是否产生幽灵仓位；
- 是否在未知状态恢复交易；
- 是否绕过 Risk Gate；
- 是否能安全恢复。

没有 Chaos acceptance，不得进入 Live Gate。

---

## 34. Private Strategy Vault

策略默认私有。

权限层级可逐步支持：

- PRIVATE
- TEAM
- ORGANIZATION
- PUBLIC

原则：

- 源码、参数、Secret、Evidence 权限可分离；
- 默认最小可见；
- 管理员能力也必须审计；
- 不以“平台可以读取全部策略”作为默认商业模型。

Strategy Marketplace 明确后置。

---

## 35. BYO 原则

长期优先支持：

- BYOK — Bring Your Own AI Key
- BYOD — Bring Your Own Data
- BYOB — Bring Your Own Broker
- BYOS — Bring Your Own Strategy

QuantLab 应主要收费于：

研究、验证、治理、证据、工作流、协作与长期资产。

而不是无限承担用户 AI、行情与执行成本。

---

## 36. UX 宪法

### 36.1 中文优先

普通用户看到：

- 中文名称；
- 中文风险说明；
- 中文证据等级；
- 中文异常解释。

内部代码可保留英文 canonical key。

### 36.2 SIMPLE / PROFESSIONAL 双模式

**Simple Mode** 只展示：

- 市场；
- 周期；
- 策略；
- 风险；
- 数据；
- 回测；
- 证据状态。

**Professional Mode** 开放：

- execution model；
- fill model；
- latency；
- slippage；
- custom data；
- OMS；
- risk policy；
- advanced config。

### 36.3 Schema-Driven UI

Strategy Spec/Risk Contract 尽可能驱动表单，避免每增加字段就手工重写 UI。

### 36.4 Code Escape Hatch

No-Code 不得锁死专业用户。

允许受控：

- Custom Python component；
- 后期 Rust component。

自定义代码必须进入 sandbox、权限和 Evidence Gate。

---

## 37. Strategy Evidence Passport

经过足够验证后，策略可拥有 Passport：

- Strategy ID；
- lineage；
- Data provenance；
- Backtest；
- OOS；
- Walk Forward；
- Stress；
- Paper；
- Shadow；
- Canary；
- Live days；
- Live trades；
- Backtest/Live divergence；
- Evidence Level；
- current status。

Passport 只陈述证据，不保证未来收益。

---

## 38. 开发治理原则

- Reuse before rebuild.
- Evidence before feature.
- Adapter before coupling.
- Version before mutation.
- Gate before promotion.
- Paper before Live.
- Shadow before Scale.
- Fail closed when state is unknown.
- Negative result is a valid result.
- No silent semantic drift.
- No hidden auto-expansion.
- No next phase by momentum.

---

## 39. 新旧路线映射

历史资产不废弃：

- 旧 Phase 1 Nautilus golden backtest → QLN-2/3 复用；
- 旧 Phase 2 Strategy Spec → QLN-2 升级为 v2；
- 旧 Phase 3 中文 AI builder → QLN-6 复用/治理；
- 旧 Phase 4 NL→Spec→Nautilus→中文报告 → QLN-3/4 复用；
- 旧 Phase 5 Data Gate / Spec validation / Simple UX → QLN-3/4/UX 宪法复用；
- 旧 Phase 6 Paper Sandbox → QLN-5 收口，不重写；
- 旧 Phase 7 Shadow/Live readiness → 拆分到 QLN-8/9/10，禁止一次性跨越。

所有旧实现进入 QLN-0 Capability Ledger：

- KEEP
- HARDEN
- MIGRATE
- MERGE
- SOFT_RETIRE
- ARCHIVE
- DELETE_CANDIDATE

没有证据不得删除历史资产。

---

## 40. 开发路线：QLN-0 → QLN-12

### QLN-0 — Read-Only Reconciliation & Capability Ledger

**目标**

在任何新施工前重新确认当前真实代码、生产、DB、Nautilus 版本、Paper 状态和历史遗留。

**必做**

- repo HEAD / production HEAD；
- active routes；
- migrations；
- current Strategy Spec；
- backtest engines；
- Nautilus adapter；
- legacy vectorized engine；
- paper runtimes；
- QMT/vn.py residuals；
- data catalog；
- AI builder；
- risk modules；
- existing tests；
- production exposure；
- secrets path；
- live code reachability。

**特别检查**

- backtest/paper 参数语义漂移；
- 多 execution kernels；
- migration drift；
- inactive/legacy code 是否仍可被调用；
- Live/Broker real-money path 是否真正 DENY。

**产物**

`QUANTLAB_NAUTILUS_CAPABILITY_LEDGER.md`

**Gate**

`QLN0_RECONCILIATION=PASS`

**禁止**

- 改代码；
- 改DB；
- 部署；
- 修复；
- 顺手重构。

**STOP**

交付 Ledger 后 STOP，等待 Owner 决策。

### QLN-1 — Constitutional / Domain Foundation

**Entry**

QLN-0 PASS + Owner GO。

**目标**

让“什么是策略、实验、证据、运行、版本”在代码层只有一个定义。

**建设**

- canonical domain IDs；
- Strategy lifecycle enum；
- Evidence stage enum；
- Environment enum；
- execution mode enum；
- version semantics；
- immutable identifiers；
- hash policy；
- audit event schema；
- engine interface contracts。

**Acceptance**

- 无同义重复状态；
- 无 Backtest/Paper 对同一字段不同解释；
- domain contracts 有 schema tests；
- legacy mapping documented。

**STOP**

Domain foundation PASS 即停，不进入 UI 扩张。

### QLN-2 — Strategy Spec v2 / Strategy Contract / Portable Package

**目标**

形成长期不依赖 Nautilus 内部版本的策略资产格式。

**建设**

- Spec v2 schema；
- Spec migration v1→v2；
- Strategy Contract；
- Invariants；
- Strategy Package；
- semantic diff；
- version/lineage；
- code escape hatch contract；
- Nautilus adapter compiler。

**Acceptance**

- golden strategy v1→v2 无语义漂移；
- spec→adapter deterministic；
- export→import hash一致；
- package 无 secret；
- invalid spec fail closed。

**STOP**

不得因为 Spec 完成自动启动 Paper/Live。

### QLN-3 — Experiment Ledger / Data Trust / Reproducibility Core

**目标**

建立 QuantLab 最核心的长期研究资产。

**建设**

- Experiment immutable ledger；
- dataset version/hash；
- time governance；
- data provenance；
- fee/slippage/execution assumptions；
- engine/version logging；
- cost attribution；
- random seed；
- artifact hashes；
- one-click reproduce；
- Data Trust Gate。

**Acceptance**

同一 Golden Experiment：`REPRODUCE=PASS`

允许的小数误差必须预先定义，不得临时解释。

**STOP**

只有实验可重现后才进入高级验证。

### QLN-4 — Evidence Validation Core

**目标**

把“回测”升级成“证据流水线”。

**建设**

- canonical Backtest；
- OOS；
- Walk Forward；
- fee stress；
- slippage stress；
- parameter sensitivity；
- regime split；
- extreme period test；
- Reality Score；
- Research Debt；
- promotion rules；
- kill rules。

**Acceptance**

策略能明确得到：`PROMOTE`；`HOLD`；`KILL`。并能解释原因。

**禁止**

为了产生 PASS 调低门槛。

### QLN-5 — Paper Sandbox Canonical Closure

**目标**

收口历史 Paper Sandbox，不再存在多条含义冲突的 Paper 路径。

**优先原则**

修/并/退役，不重写。

**建设**

- reconcile legacy paper_orders；
- canonical PaperRun；
- Spec→Paper 语义完全一致；
- orders/fills/positions/equity；
- kill switch；
- restart recovery；
- migration truth；
- Chinese Paper UX；
- Paper evaluation→Experiment Ledger；
- performance feedback→Research。

**Acceptance**

- `BACKTEST_PAPER_SEMANTIC_PARITY=PASS`；
- `RESTART_RECOVERY=PASS`；
- `REAL_MONEY_PATH=0`；
- `LIVE_ROUTE=DENY`；
- migration up/down tests PASS；
- Paper evaluation reproducible。

**STOP**

Paper PASS 后默认冻结观察，不自动进入 Shadow。

### QLN-6 — Research Intelligence & Bounded AI Scientist

**Entry**

Evidence Core + Paper 已稳定，且有真实研究需求。

**建设**

- Strategy DNA；
- Genealogy；
- Graveyard；
- Research Memory；
- Counterfactual Lab；
- duplicate/similarity detection；
- AI Committee；
- bounded autonomous research；
- research budget；
- negative-result support。

**Acceptance**

AI 必须能输出：`NO_EDGE_FOUND`

且不得把失败隐藏为“继续优化建议”。

**STOP**

AI 研究权限不得包含真实资金执行。

### QLN-7 — Portfolio Intelligence & Governor

**Entry**

至少存在多个经过较高 Evidence Level 的策略。

**建设**

- strategy correlation；
- risk clusters；
- factor/style exposure；
- capital budgets；
- instrument/venue limits；
- drawdown budget；
- liquidity/capacity；
- portfolio de-risking；
- strategy crowding。

**Acceptance**

Portfolio Governor 的任何动作必须：可解释；可审计；可回放；不绕过 strategy invariants。

### QLN-8 — Shadow Twin / Flight Recorder / Replay / Attribution

**Entry**

有稳定 Paper 策略，且 Shadow 有实际用途。

**建设**

- Shadow Twin；
- signal/order/position divergence；
- Flight Recorder；
- replay engine；
- manual intervention logging；
- Loss Attribution；
- strategy behavior parity report。

**Acceptance**

任一选定事件可以完整回答：当时看到了什么、为什么做出决定、风险如何裁决、实际发生了什么。

### QLN-9 — Reliability / Security / Chaos Readiness

**Entry**

Shadow 栈稳定。

**建设**

- secrets plane；
- credential rotation；
- RBAC；
- audit；
- dead-man switch；
- reconciliation hardening；
- crash recovery；
- node/service ownership；
- chaos scenarios；
- backup/restore；
- engine compatibility lab；
- broker capability matrix。

**Acceptance**

- `CHAOS_ACCEPTANCE=PASS`；
- `RECONCILIATION=PASS`；
- `DUPLICATE_ORDER_ON_RECOVERY=0`；
- `UNKNOWN_STATE_NEW_RISK=0`；
- `SECRET_LEAK=0`。

**STOP**

仍然不自动授权真实资金。

### QLN-10 — Canary Live Readiness Gate

**目标**

证明系统具备进入极小规模真实环境的工程资格，而不是实际开始 Live。

**建设**

- broker-specific acceptance；
- capability compatibility；
- canary capital contract；
- max-loss envelope；
- rollback/runbook；
- operator action card；
- alerting；
- production observability；
- emergency stop drill；
- owner approval artifact。

**必须输出**

`LIVE_READINESS=PASS/HOLD/DENY`

**规则**

即使 PASS，也只是“有资格请求 Live Owner Approval”。

### QLN-11 — Limited Live Pilot

**Entry**

仅在 Owner 单独明确授权后。

**初始范围**

- 1 venue；
- 1 account；
- 1–极少策略；
- 极小 capital envelope；
- low leverage / preferably none；
- pre-defined max loss；
- mandatory Shadow Twin；
- mandatory reconciliation；
- mandatory Flight Recorder。

**自动降级条件**

- divergence；
- unknown state；
- drawdown threshold；
- reconciliation failure；
- data health failure；
- broker anomaly；
- contract violation。

**Acceptance**

不是看赚不赚钱，而是看：execution correctness；safety；divergence；recovery；Evidence integrity。

### QLN-12 — Evidence Passport / TMOS Link / Commercialization

**Entry**

有真实稳定证据后。

**建设**

- Strategy Passport；
- public/private evidence views；
- Trader–Strategy Fit；
- Strategy Adherence；
- Loss Attribution integration；
- team/org sharing；
- BYOK/BYOD/BYOB/BYOS；
- billing boundaries；
- private vault；
- optional API/SDK。

**Marketplace**

仍默认 HOLD。

只有当：Evidence system成熟；rights/licensing清楚；privacy/security成熟；commercial demand真实存在；才单独提案。

---

## 41. 各阶段统一 Gate 模板

每个阶段报告至少必须输出：

```text
PHASE=QLN-X
SCOPE_LOCKED=YES/NO
ENTRY_GATE=PASS/HOLD/DENY
CODE_CHANGE=...
DB_CHANGE=...
PRODUCTION_CHANGE=...
LIVE_CHANGE=...
SECRETS_TOUCHED=YES/NO
REUSED_EXISTING_ASSETS=...
NEW_CAPABILITIES=...
TESTS=...
MIGRATION=...
SECURITY=...
SEMANTIC_PARITY=...
REGRESSION=...
OPEN_P0=...
OPEN_P1=...
OPEN_P2=...
ACCEPTANCE=PASS/HOLD/DENY
NEXT_PHASE_AUTO_ENTER=NO
OWNER_DECISION_REQUIRED=YES/NO
STOP=YES
```

任何报告不得只写“基本完成”“大致可用”。

---

## 42. 触发式开发，而非持续施工

QuantLab 不因为路线长就必须连续建设到 QLN-12。

后续阶段必须由真实 Trigger 驱动。

允许 Trigger：

- **A. Owner 自用** — 开始真实系统化研究多个策略，现有能力成为明显瓶颈。
- **B. TMOS 用户需求** — 真实交易员需要策略验证、Strategy Adherence、研究工具。
- **C. QuantLab 使用证据** — 已有用户持续使用，并真实卡在某个下一阶段能力。
- **D. 商业验证** — 有人愿意为研究/验证/Evidence/团队能力付款。
- **E. 工程条件** — 前一阶段稳定，且 Owner Attention 不会被新工程战线拖垮。

没有 Trigger：

`ENGINEERING=FROZEN`

---

## 43. 当前时间点的默认治理决定

本宪法完成并记录后：

```text
QUANTLAB_DIRECTION=APPROVED
NAUTILUS_KERNEL_DIRECTION=APPROVED
STRATEGY_EVIDENCE_OS=CANONICAL_TARGET
LEGACY_ASSETS=PRESERVE_AND_RECONCILE
NEW_PHASE_NUMBERING=QLN_0_TO_12
FULL_BUILD_NOW=DENY
PRODUCTION_CHANGE=DENY
LIVE_TRADING=DENY
AUTONOMOUS_EXPANSION=DENY
NEXT_ALLOWED_WHEN_OWNER_AUTHORIZES=QLN_0_READ_ONLY
NEXT_PHASE_AUTO_ENTER=NO
```

原因：

- 方向长期价值高；
- 已有 QuantLab 资产需要先复用和收口；
- Nautilus 正好适合作为内核而非产品层；
- 当前不需要为了“想法很好”立即开启无限开发；
- 真实用户/商业/研究触发应优先于工程冲动。

---

## 44. 建议 Canonical 文档结构

建议未来仓库采用：

```text
docs/governance/
  QUANTLAB_CONSTITUTION.md
  QUANTLAB_NAUTILUS_CAPABILITY_LEDGER.md
  QUANTLAB_PHASE_GATE_LEDGER.md
  QUANTLAB_LIVE_AUTHORITY.md

docs/architecture/
  STRATEGY_SPEC_V2.md
  STRATEGY_CONTRACT.md
  STRATEGY_PACKAGE.md
  ENGINE_ADAPTER_CONTRACT.md
  EXPERIMENT_LEDGER.md
  EVIDENCE_PIPELINE.md
  PORTFOLIO_GOVERNOR.md
  SHADOW_TWIN.md
  FLIGHT_RECORDER.md
  SECRET_PLANE.md
  TIME_GOVERNANCE.md
  BROKER_CAPABILITY_MATRIX.md

schemas/
  strategy_spec_v2.*
  strategy_contract.*
  experiment_record.*
  strategy_passport.*
```

本宪法是 WHY / WHAT / BOUNDARY / ORDER 的 SSOT。

实现细节不得反向修改宪法目标；需要修改使命、权限、Live边界、证据定义时，必须形成新的 Owner-approved Amendment。

---

## 45. Cursor / Autonomous Engineering Contract

未来把本宪法交给 Cursor 时，默认追加以下约束：

- 先读 Constitution、当前 Phase、Capability Ledger。
- 只执行被明确批准的一个 QLN Phase。
- 先做 inventory，再做 change。
- 有旧能力先复用，禁止平行造第二套。
- 发现同类问题可以举一反三审计，但：
  - 属于本 Phase：修复；
  - 超范围：登记 HOLD；
  - 不得借机扩展产品范围。
- 禁止提前进入下一 Phase。
- 禁止因为测试通过自行部署 Live。
- 禁止创建 Broker real-money path，除非当前 Phase 明确授权。
- Secrets 不打印、不提交、不写报告。
- DB migration 必须可升级/可回退/有测试。
- 所有语义变化必须有 before/after evidence。
- 每阶段完成必须写 Acceptance Report + Ledger。
- PASS 后也必须 STOP。
- Owner 只批准方向，不等于批准所有后续实施。

### Companion protocol pointer (non-amending)

Operational autonomous-engineering detail for an **Owner-approved** QLN phase is maintained in:

[`docs/governance/autonomous-engineering/`](./autonomous-engineering/) (pack **v1.0**)

That companion pack does **not** amend this Constitution’s meaning, Live boundaries, Evidence definitions, or `NEXT_PHASE_AUTO_ENTER=NO`. It remains subordinate to Owner explicit instruction, this Constitution, and the current QLN acceptance criteria. Before any code change in an approved QLN phase: `AUTONOMOUS_ENGINEERING_PROTOCOL_LOADED=YES`, else `ENGINEERING_START=DENY`.

---

## 46. 最高层一句话

QuantLab 不负责制造更多策略；QuantLab 负责让策略的产生、验证、淘汰、运行和长期证据变得可信。

以及：

TMOS 验证人；QuantLab 验证策略；NautilusTrader 负责可靠地计算与执行。

这三句话是未来所有产品和工程决策的最终裁决标准。
