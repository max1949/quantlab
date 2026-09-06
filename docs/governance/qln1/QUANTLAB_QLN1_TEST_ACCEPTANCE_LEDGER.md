# QUANTLAB_QLN1_TEST_ACCEPTANCE_LEDGER

```text
PHASE=QLN-1
OVERNIGHT_RUN=YES
FOCUSED_SUITE=engine/tests/test_domain_foundation.py
+ test_phase6_paper_sandbox.py
+ test_strategy_spec_parity.py
+ test_strategy_validation.py
+ test_nautilus_golden_backtest.py
```

| Metric | Value |
|---|---|
| Overnight focused result | **42 passed** |
| Engine collect before QLN-1 | 136 |
| Engine collect overnight close | **155** |
| Silent test loss | **NO** |
| Domain schema tests | PASS |
| Contract / hash / audit / legacy map | PASS |
| LIVE deny regression | PASS |
| SANDBOX compatibility | PASS |
| Nautilus independence of domain pkg | PASS |

```text
DOMAIN_SCHEMA_TESTS=PASS
CONTRACT_TESTS=PASS
FOCUSED_TESTS=PASS
RELEVANT_REGRESSION=PASS
NO_SILENT_TEST_LOSS=YES
```
