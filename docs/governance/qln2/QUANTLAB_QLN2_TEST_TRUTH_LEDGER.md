# QLN-2 Test Truth Ledger

```text
FOCUSED_QLN2=16_passed
DOMAIN_FOUNDATION_REGRESSION=19_passed
ENGINE_COLLECT_PRE_QLN2=155
ENGINE_COLLECT_POST_QLN2=171
NO_SILENT_TEST_LOSS=YES
```

## Coverage map

| Area | Tests |
|---|---|
| Migration + semantic drift 0 | parametrized goldens FX + BTC |
| Adapter parity v1↔v2 | `nautilus_params` equality |
| Package export/import/hash | roundtrip + tamper fail |
| Secrets | key/value patterns; package reject |
| Semantic diff classes | metadata / param|logic / risk |
| Lineage child kinds | parameter vs logic |
| Escape hatch | capabilities + respect flags |
| Fail closed | missing fields, LIVE, drawdown, contract, invariants, LIVE compile refuse |
| No Nautilus in v2 domain | source scan |

## Commands

```text
python -m pytest engine/tests/test_strategy_spec_v2.py -q
python -m pytest engine/tests/test_domain_foundation.py -q
python -m pytest engine/tests --collect-only -q
```
