# Strategy Validation Batch 001 — Baseline Library

```text
MODE=STRATEGY_VALIDATION
BATCH=001
ENGINEERING_MODE=MAINTENANCE_ONLY
LIVE_EXECUTION=DENY
PHASE_7=DENY
```

## Purpose

Establish QuantLab’s **yardstick**, not find a holy grail. Families covered:
trend, mean reversion, momentum, volatility (10 baselines).

## Machine summary

See `data/strategy_validation/batch_001/REPORT.txt` and `summary.json`.

```text
STRATEGIES_TESTED=10
PROMOTED=0
HELD=0
REJECTED=10

OOS_PASS=2
WALK_FORWARD_PASS=3
ROBUSTNESS_PASS=2
COST_STRESS_PASS=2
PAPER_PASS=0

BEST_STRATEGY=baseline_ema_cross_btc
BEST_STRATEGY_VERSION=v1
BEST_MARKET=BTCUSDT
BEST_TIMEFRAME=15m

MAX_DRAWDOWN=-0.0029 (full-sample; not promotion evidence)
SHARPE≈7.87 (full-sample; TRADE_COUNT=1 → OVERFIT_RISK=HIGH)
SORTINO≈16.44
CALMAR≈29.0
PROFIT_FACTOR=99.0
TRADE_COUNT=1

BACKTEST_PAPER_PARITY=INSUFFICIENT
OVERFIT_RISK=HIGH

LIVE_EXECUTION=DENY
PHASE_7=DENY
```

## Interpretation

- **No PROMOTE** is correct: Paper + Backtest/Paper parity were marked
  `INSUFFICIENT` (no skip-level). Also several OOS/WF/cost failures.
- **Best full-sample Sharpe** (`baseline_ema_cross_btc`) is **not** a valid
  strategy: 1 trade on synthetic golden BTC → `OVERFIT_RISK=HIGH` → REJECT /
  graveyard. This is exactly why `BACKTEST_PROFITABLE ≠ STRATEGY_VALID`.
- Rejects are archived under `data/strategy_graveyard/rejects.jsonl`.

## Next validation steps (research only)

1. Longer / multi-regime datasets (not only golden synthetic).
2. Dedicated Paper windows for survivors of OOS+WF+cost (none this batch).
3. Do **not** retune rejected specs to chase a PASS.

```text
DO_NOT_ENTER_PHASE_7
DO_NOT_ENABLE_LIVE
```
