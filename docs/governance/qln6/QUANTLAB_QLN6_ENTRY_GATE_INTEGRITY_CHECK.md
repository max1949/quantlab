# QLN-6 Entry Gate Integrity Check

```text
ACTIVITY=QLN_6_ENTRY_GATE_INTEGRITY_CHECK
QLN_6_ENTRY_GATE_INTEGRITY=HOLD
QLN_6_ENTRY_GATE=HOLD
QLN_6_STARTED=NO
CAMPAIGN_CONTINUES=NO
THRESHOLD_RELAXATION=NO
RULES_CHANGED=NO
PARAMS_RETUNED=NO
EVIDENCE_PIPELINE_RERUN=NO
```

## Per-strategy classification

| strategy_id | hist universe | evidence | class | derived |
|---|---|---|---|---|
| hist_fl_momentum_w20 | AU, RB | CU | CROSS_INSTRUMENT_VALIDATION → DERIVED | `derived/hist_fl_momentum_w20_cu` @v1.1 |
| hist_fl_momentum_w250 | IF | CU | CROSS_INSTRUMENT_VALIDATION → DERIVED | `derived/hist_fl_momentum_w250_cu` @v1.1 |
| hist_fl_mean_reversion_w20 | RB | MA | CROSS_INSTRUMENT_VALIDATION → DERIVED | `derived/hist_fl_mean_reversion_w20_ma` @v1.1 |
| hist_fl_rsi_w14 | AU | CU | CROSS_INSTRUMENT_VALIDATION → DERIVED | `derived/hist_fl_rsi_w14_cu` @v1.1 |

```text
instrument/universe ∈ Strategy identity = YES (QLN-2; instruments change = breaking_semantic)
explicitly_instrument_agnostic = NO (Factor Lab backtests were symbol-bound)
ORIGINAL_STRATEGY_REPRODUCTION = 0
CROSS_INSTRUMENT_VALIDATION = 4
DERIVED_VERSION_COUNT = 4
```

## HE recount

Prior `HIGHER_EVIDENCE_STRATEGY_COUNT=2` was attributed to Specs whose `universe` silently claimed CU/MA while history was AU/RB/IF → **wrong identity**.

Under correct identity:

```text
HIGHER_EVIDENCE_ON_DERIVED_IDENTITY=2  # informational; same frozen gates, derived IDs
HIGHER_EVIDENCE_STRATEGY_COUNT=0       # Entry count: do not credit mislabeled originals
```

```text
QLN_6_ENTRY_GATE=HOLD
```

Artifact: `docs/governance/qln6/artifacts/entry_gate_integrity_check.json`
