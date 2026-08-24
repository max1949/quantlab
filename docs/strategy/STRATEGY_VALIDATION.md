# Strategy Validation

```text
Strategy Spec
 → Baseline Backtest
 → DATA_GATE
 → OOS / Walk-Forward / Sensitivity
 → robustness_score (existing engine.walk_forward)
 → VALIDATION_GATE
 → Lifecycle DRAFT…PAPER_READY
```

Binding: every validation result stores `strategy_spec_id` + `strategy_spec_version` + `spec_hash`.  
Changing EMA parameters requires a **new Spec version**; old ROBUSTNESS_PASS does not inherit.

`PAPER_READY` may be set; `PAPER_RUNTIME` remains OFF until Owner Gate 6.
