# QuantLab AI — AI-native Quant Operating System

QuantLab is **not** “NautilusTrader 中文版” and **not** a vn.py replacement.

## Positioning

> 不会编程，也能把交易想法变成可以研究、验证、模拟和安全执行的量化策略。

## Architecture boundary

```text
UI (SIMPLE / PRO / DEV)
  → Application services
  → QuantLab trading abstractions (engine/trading, strategy_specs)
  → Nautilus adapter (engine/nautilus) ONLY
  → NautilusTrader 1.231.0
```

## Research assets (preserve)

Factor Lab, Validation (OOS/WF/sensitivity), Research Reports, Auth, Billing, Feed.

## Trading core

- Engine: NautilusTrader (pinned)
- Strategy source of truth: Strategy Specification
- AI: draft + research only; `AI_DIRECT_LIVE=DENY`
- vn.py: retired from active paths; historical audit preserved

## Lifecycle (this release)

```text
DRAFT → BACKTESTED → VALIDATED → ROBUST → PAPER_READY
PAPER_RUNTIME=OFF
LIVE=HOLD
```
