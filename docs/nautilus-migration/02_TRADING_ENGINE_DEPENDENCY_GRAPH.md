# 02 — Trading Engine Dependency Graph (Phase 0)

## Current graph (as-is)

```text
                    frontend-react
                          │
                          ▼
              /api/v1/execution  /backtests  /validations  /factors
                          │
          ┌───────────────┼───────────────────────────────┐
          ▼               ▼                               ▼
  execution_service   backtest service              validation service
          │               │                               │
          ▼               ▼                               ▼
  engine.execution_   engine.backtest               engine.walk_forward
  adapter             engine.factor_engine          engine.param_scan
          │               │                         engine.segment_robustness
          ▼               ▼
   HTTP stub OR        pandas OHLCV Parquet
   paper ledger        (market_data service)
          │
   ┌──────┴──────┐
   ▼             ▼
 channel=     channel=
 "vnpy"       "qmt"
 (optional    (optional
  gateway)     gateway)
```

## Important semantic fact

`engine/backtest.py` is **not** vn.py `BacktestingEngine`. It is QuantLab’s own vectorized signal backtester:

```text
signal → sign(position) → lag(1) returns − costs → metrics / equity
```

No order book, no fills model, no venue instrument model.

## Target graph (to-be)

```text
UI / AI Copilot
      │
      ▼
Application (Strategy / Research / Data / Validation / Backtest / Portfolio / Risk / Deployment / AI)
      │
      ▼
QuantLab Trading Abstraction
  StrategySpec, InstrumentRef, BacktestRequest, OrderIntent,
  PositionSnapshot, PortfolioSnapshot, RiskPolicy, ExecutionStatus
      │
      ▼
Nautilus Adapter Layer  (ONLY place that imports nautilus_trader)
      │
      ▼
NautilusTrader (pinned 1.231.0)
      │
      ▼
Venue / Broker (Phase ≥3)
```

## Dependency edges to cut / replace

| Edge | Today | Target |
|------|-------|--------|
| UI → channel `vnpy` | Direct option | Hide / remove; paper + later nautilus |
| execution_service → route_vnpy_order | Direct | Abstraction → adapter |
| market_data → import_vnpy_* | Direct | Data Normalization → Catalog |
| backtests → engine.backtest | Primary | Dual-run then NAUTILUS primary; keep engine.backtest as research baseline helper |
| docs → “vn.py 实盘” | Marketing | Nautilus / 模拟 / 研究 |

## Hard constraint

```text
BUSINESS_DIRECT_IMPORT_NAUTILUS = DENY (except adapter package)
```
