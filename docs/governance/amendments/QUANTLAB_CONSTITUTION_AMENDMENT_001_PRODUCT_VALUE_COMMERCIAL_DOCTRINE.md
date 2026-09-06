# QuantLab Constitution v2

## Amendment No. 1 — Product Value & Commercial Doctrine

**Status:** Owner-approved · **CANONICAL**  
**Amendment ID:** `CONSTITUTION_AMENDMENT_001`  
**Canonical path:** `docs/governance/amendments/QUANTLAB_CONSTITUTION_AMENDMENT_001_PRODUCT_VALUE_COMMERCIAL_DOCTRINE.md`  
**Relationship:** 本 Amendment 从属于并补充 `docs/governance/QUANTLAB_CONSTITUTION.md`，不修改既有 QLN-0→QLN-12 阶段顺序、安全权限、Live Gate 或 Autonomous Engineering 边界。

```text
ENGINEERING_AUTHORIZATION=NONE
PRODUCTION_CHANGE=DENY
LIVE_CHANGE=DENY
NEXT_PHASE_AUTO_ENTER=NO
COMMERCIALIZATION_AUTO_ENTER=NO
QLN_0_STARTED=NO
```

---

# A. 第一性主要矛盾

QuantLab 长期解决的主要矛盾正式定义为：

> **AI 与自动化正在使策略想法、代码与回测结果的生产成本快速趋近于零，但真正可信、可复现、可反证、可经受现实世界验证并值得获得真实资本的策略仍然极度稀缺。**

因此：

`STRATEGY_SUPPLY=ABUNDANT`

`TRUSTWORTHY_STRATEGY_EVIDENCE=SCARCE`

QuantLab 不以扩大策略供给为主要使命。

QuantLab 的主要使命是：

> **提高策略验证能力、反证能力、淘汰能力、现实验证能力与长期证据质量。**

---

# B. 核心产品哲学

QuantLab 的核心行为原则正式定义为：

> **先证明，再下注。**  
> **Prove Before Capital.**

任何策略不得因为：

* AI生成；
* 回测漂亮；
* 单一指标优秀；
* 用户主观喜欢；
* 最近表现好；

而自动取得真实资本权限。

资本权限必须依赖逐层积累的证据。

QuantLab 的价值不是帮助更多策略生存。

QuantLab 的价值包括：

> **主动、尽早、可解释地杀死错误策略。**

---

# C. QuantLab 的干预对象

TMOS 主要干预 Trader Behavior。

QuantLab 主要干预：

> **Strategy Research Behavior + Strategy Lifecycle Behavior**

重点识别和干预至少包括：

1. False Edge；
2. Overfitting；
3. Data Snooping；
4. Research Bias；
5. 参数追逐；
6. 样本不足；
7. 数据质量问题；
8. 手续费与滑点低估；
9. Backtest–Paper Reality Gap；
10. Paper–Shadow–Live Divergence；
11. Market Regime Mismatch；
12. Strategy Decay；
13. Portfolio Crowding；
14. False Diversification；
15. 一次亏损后无证据调参；
16. AI重复生成历史已失败研究；
17. 已失效策略因沉没成本继续获得资本。

核心循环：

`HYPOTHESIS → TEST → FALSIFY → VALIDATE → PROMOTE → OBSERVE → REDUCE/KILL → LEARN`

---

# D. 用户最终购买的结果

QuantLab 不以“策略收益率”作为可承诺产品结果。

QuantLab 核心改善：

> **Strategy Decision Confidence**

以及：

> **Capital Allocation Quality**

系统长期必须越来越可靠地帮助用户回答：

1. 这个策略值得继续研究吗？
2. 当前证据是真的吗？
3. 是否存在明显过拟合？
4. 是否值得进入 Paper？
5. 是否值得进入 Shadow？
6. 是否值得获得第一笔小额真实资本？
7. 是否值得扩大资本？
8. 当前是否仍值得继续获得资本？
9. 是否应该 Reduce / Suspend / Kill？
10. 为什么？

---

# E. 核心客户与高价值场景

QuantLab 核心 ICP 不定义为“所有想学量化的人”。

核心客户优先定义为：

> **需要对真实资本负责的人。**

优先包括：

* 独立职业交易者；
* 系统交易者；
* 管理较大自有资金的交易者；
* 小型交易团队；
* 策略负责人；
* Prop Trading Team；
* 后期的小型基金、Family Office 或研究团队。

非核心高价值 ICP：

* 只想找神指标的人；
* 只想生成策略玩一玩的人；
* 没有真实研究流程的人；
* 没有资本决策场景且只追求免费回测的人。

QuantLab 不得为了扩大注册量而偏离核心责任场景。

---

# F. 高客单价值来源

QuantLab 高客单价不得建立在：

* 页面数量；
* 指标数量；
* AI Token；
* 单纯回测次数；
* 策略生成次数；

之上。

高价值应来自以下结果：

## F1. Capital Exposure Avoided

坏策略在获得真实资本前被 Evidence Gate 拒绝。

## F2. Research Waste Avoided

减少重复研究、无效实验、已经证明失败的方向和无界限 AI Search。

## F3. Research Time Reduction

自动化完成研究、反证、验证、比较与总结中可安全自动完成的工作。

## F4. Institutional Research Memory

长期保存：

* Experiment Ledger；
* Strategy Genealogy；
* Graveyard；
* 参数历史；
* 数据版本；
* 失败原因；
* Paper/Shadow/Live Evidence。

## F5. Strategy Governance

回答：

> 为什么这个策略当前允许获得这些资本？

而不是依赖某个人的一句“我觉得不错”。

## F6. Key-Person Risk Reduction

将策略知识从：

`PERSONAL MEMORY`

转化为：

`ORGANIZATIONAL ASSET`

## F7. Continuous Strategy Governance

一次验证解决首次购买价值。

长期持续监控：

* Edge Decay；
* Reality Divergence；
* Risk Drift；
* Regime Mismatch；
* Capacity Change；
* Portfolio Crowding；

构成长期续费价值。

---

# G. 商业定位

QuantLab 不应以：

> AI Strategy Generator

作为最终市场定位。

推荐长期定义：

> **面向真实资本的 Strategy Research & Evidence Infrastructure。**

用户语言：

> **在真钱进入策略之前，尽可能证明它值得；在真钱进入之后，持续证明它仍然值得。**

QuantLab 的收费逻辑应逐渐随：

* Capital Responsibility；
* Strategy Complexity；
* Team Size；
* Governance Requirements；
* Evidence Depth；
* Private Infrastructure Requirements；

增加，而不是机械依赖回测次数。

---

# H. 与 TMOS 的更高层统一

TMOS：

> 降低 Human Error，提高 Trader Quality。

QuantLab：

> 降低 Strategy / Research Error，提高 Strategy Quality。

长期共同解决：

> **Capital Allocation Error**

最终系统应逐渐回答：

> **什么样的人，用什么策略，在什么环境下，应该承担多少资本和风险。**

长期结构：

`Trader Quality × Strategy Quality × Trader–Strategy Fit × Portfolio Governance → Better Capital Allocation`

---

# I. 产品发力优先级

长期开发资源按以下优先级执行：

## P0-A

**Strategy Evidence Pipeline**

包括 Promotion / Hold / Kill。

## P0-B

**Experiment Ledger + Reproducibility + Data/Reality Trust**

## P0-C

**Backtest → Paper → Shadow → Live Divergence + Risk Governance**

以上三项是核心价值主干。

---

AI Strategy Scientist 定位：

> **Multiplier，非产品本体。**

AI 的重要职责尤其包括：

* 提出假设；
* 设计实验；
* 寻找反例；
* 检测过拟合；
* 参数敏感性分析；
* 搜索历史失败研究；
* 解释证据；
* 尝试证明策略不存在 Edge。

QuantLab 必须允许 AI 最终结论为：

> **NO EDGE FOUND**

而不是必须生成可交易策略。

其中 **Skeptic / Falsification** 能力优先于单纯 Strategy Generator。

---

UI 定位：

> **Usability Layer，非核心护城河。**

中文 UI、No-Code、Dashboard、图表和模板均服务于 Evidence Workflow，不得反向主导产品路线。

---

# J. New Capability 八问 Admission Gate

任何大型新功能、产品线或工程提案，在进入建设前必须回答：

### Q1 — 主要矛盾

它解决 Strategy Evidence 稀缺这一主要矛盾吗？

### Q2 — 明确用户

它主要帮助“需要对真实资本负责的人”吗？

### Q3 — 痛点

不解决这个问题，会造成明显：

* Capital Risk；
* Research Waste；
* Evidence Blindness；
* Governance Failure；

之一吗？

### Q4 — 最终结果

它能改善：

`Strategy Decision Confidence`

或：

`Capital Allocation Quality`

吗？

### Q5 — Evidence Impact

它增加真正的证据，还是仅增加内容、页面、策略数量或复杂度？

### Q6 — Promotion / Kill Impact

它是否帮助系统更准确：

`PROMOTE / HOLD / REDUCE / KILL`

策略？

### Q7 — Long-Term Asset

它是否积累：

* Research Memory；
* Evidence；
* Strategy History；
* Trader–Strategy Intelligence；

等长期资产？

### Q8 — Complexity / Owner Cost

它带来的长期维护、监管、人工、服务器和 Owner Attention 是否值得？

若上述关键问题不能得到清晰 YES：

`FEATURE_ADMISSION=HOLD`

不得因为：

`AI_CAN_BUILD_IT=YES`

而推出能力。

---

# K. 商业价值验证指标

早期不得以 ARPU 或策略数量证明 QuantLab 成功。

优先建立：

`BAD_STRATEGY_REJECTION_RATE`

`FALSE_POSITIVE_RATE`

`RESEARCH_TIME_REDUCTION`

`RESEARCH_WASTE_AVOIDED`

`BACKTEST_PAPER_DIVERGENCE`

`PAPER_SHADOW_DIVERGENCE`

`SHADOW_LIVE_DIVERGENCE`

`STRATEGY_SURVIVAL_RATE`

`CAPITAL_EXPOSURE_AVOIDED`

`EVIDENCE_REPRODUCIBILITY_RATE`

在没有真实证据前，不得虚构：

* 避免损失金额；
* 保护资本金额；
* 收益改善；
* ROI。

---

# L. Product Wedge

QuantLab 初期商业切入口优先考虑：

> **Pre-Capital Strategy Review / 策略上线前审查**

用户不是首先要求系统：

> 帮我制造更多策略。

而是：

> **这是我的策略。在我拿真钱运行之前，请尽最大努力证明它哪里有问题。**

完成审查后的输出应是：

`PROMOTE / HOLD / KILL`

以及：

* 为什么；
* 证据缺什么；
* 哪些问题可修；
* 下一步最小验证是什么。

QuantLab 不得成为只会否决的“评分器”。

必须形成：

`DETECT → EXPLAIN → MINIMAL REMEDIATION → REVALIDATE → DECIDE`

---

# M. 持续价值

首次审查解决：

> **Should I fund this strategy?**

长期产品解决：

> **Should I continue funding this strategy?**

因此 QuantLab 必须把持续 Evidence Monitoring 视为长期价值核心，而不是附加 Dashboard。

---

# N. Amendment Governance

本 Amendment：

* 不改变 QLN-0→QLN-12；
* 不授权任何新工程；
* 不开放 Production；
* 不开放 Live；
* 不改变 `NEXT_PHASE_AUTO_ENTER=NO`；
* 不改变 Autonomous Engineering 权限；
* 不因商业价值定义完成而自动进入 Commercialization。

其作用是：

> **锁定 QuantLab 为什么存在、为谁存在、什么才算高价值，以及未来什么值得开发。**
