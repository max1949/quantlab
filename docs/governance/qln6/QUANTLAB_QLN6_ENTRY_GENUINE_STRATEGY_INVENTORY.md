# GENUINE Strategy Inventory — QLN-6 Entry Evidence Accumulation

```text
ACTIVITY=QLN_6_ENTRY_EVIDENCE_ACCUMULATION
QLN_6_STARTED=NO
FAKE_STRATEGY=NO
FAKE_DEMAND=NO
SYNTHETIC_AS_REAL=NO
GOLDEN_AS_REAL=NO
THRESHOLD_RELAXATION=NO
QLN_6_GATE_BYPASS=NO
LIVE=NO
REAL_MONEY=NO
INVENTORY_SCOPE=workstation_repo + local data artifacts
PROD_DB_PROBE=FAIL_SSH_CLOSED (144.22.40.92)
```

## Classification rules

| Class | Counts toward QLN-6 Entry? |
|---|---|
| Owner / human-created Strategy Spec | YES |
| Genuine historical research Strategy Spec | YES |
| Imported user Strategy Spec | YES |
| User-generated Strategy Spec | YES |
| Golden test strategy | **NO** |
| Synthetic fixture / golden OHLCV yardstick | **NO** |
| Demo / template baseline library | **NO** |
| Test-only / Phase-6 e2e PaperRun debris | **NO** |

## Inventory results

### A. Strategy Spec library (`strategy_specs/`)

| Asset | Class | Eligible |
|---|---|---|
| `golden_01_ema_trend` v1/v2 + package | golden test | NO |
| `golden_btc_ema_trend` v1/v2 + package | golden test | NO |

```text
GENUINE_STRATEGY_SPEC_COUNT=0
```

### B. Validation Baseline Library (`engine/validation/baselines.py` + batch_001)

10 baselines (`baseline_ema_cross_trend`, `baseline_ema_cross_btc`, …).  
Documented purpose: **yardstick**, datasets from `dataset_resolver` → `golden_synthetic` / `quantlab_golden`.  
Batch_001: PROMOTED=0, REJECTED=10; best Sharpe on synthetic BTC with TRADE_COUNT=1 → OVERFIT.

| Asset class | Eligible |
|---|---|
| demo/template + synthetic fixture yardstick | **NO** |

```text
BASELINE_YARDSTICK_COUNT=10
BASELINE_COUNTED_AS_GENUINE=0
```

### C. Local PaperRun artifacts (`data/paper_runs/`)

~20 UUID dirs; health/snapshots are Phase-6 sandbox / e2e debris. Observed Nautilus `EMACross` / BTCUSDT golden-path runs — **not** Owner research Strategy Spec portfolio.

```text
LOCAL_PAPER_RUN_DIRS≈20
PAPER_QUALIFIED_GENUINE_STRATEGIES=0
```

### D. Experiment Ledger

```text
data/experiment_ledger/experiments.jsonl = ABSENT
GENUINE_REPRODUCIBLE_EXPERIMENTS=0
```

### E. Production DB

```text
PROD_DB_PROBE=FAIL (SSH connection closed)
FACTORS_COUNT=UNKNOWN
USER_STRATEGY_SPECS=UNKNOWN
RESEARCH_PROJECTS=UNKNOWN
```

No local `.env` / DB on workstation. Cannot invent prod demand from failed probe.

### F. Factor Lab adjacency

Backend has `Factor` / `ResearchProject` models (Factor Lab stack). These are **not** Strategy Spec v2 assets and are **not** automatically higher-Evidence strategies. Without prod rows, demand remains unproven.

---

## GENUINE_STRATEGY_INVENTORY summary

```text
GENUINE_STRATEGY_COUNT=0
EXCLUDED_GOLDEN=2_families
EXCLUDED_BASELINE_YARDSTICK=10
EXCLUDED_SYNTHETIC_VALIDATION_BATCH=YES
STRATEGIES_FULLY_EVALUATED=0
PROMOTE=0
HOLD=0
KILL=0
HIGHER_EVIDENCE_STRATEGY_COUNT=0
MULTIPLE_HIGHER_EVIDENCE_STRATEGIES=NO
```

No eligible genuine strategy existed to run through Experiment Ledger → Evidence Pipeline → PaperRun without violating `SYNTHETIC_AS_REAL` / `GOLDEN_AS_REAL`.
