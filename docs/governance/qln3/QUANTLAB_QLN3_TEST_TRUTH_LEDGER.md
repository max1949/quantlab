# QLN-3 Test Truth Ledger

```text
FOCUSED_QLN3=9_passed
QLN1_2_REGRESSION=44_passed_combined_with_qln3
ENGINE_COLLECT_PRE_QLN3=171
ENGINE_COLLECT_POST_QLN3=180
NO_SILENT_TEST_LOSS=YES
```

## Coverage

| Area | Tests |
|---|---|
| Seal + hashes | `test_golden_experiment_seals_and_hashes` |
| Ledger immutability | `test_ledger_append_only_immutable` |
| Reproduce PASS | `test_reproduce_pass_same_seed` |
| Drift detection | `test_reproduce_detects_param_drift` |
| Trust fail closed | empty / naive index / seal without PASS |
| Tolerances predeclared | version pin |

## Commands

```text
python -m pytest engine/tests/test_experiment_ledger_qln3.py -q
python -m pytest engine/tests/test_strategy_spec_v2.py engine/tests/test_domain_foundation.py -q
python -m pytest engine/tests --collect-only -q
```
