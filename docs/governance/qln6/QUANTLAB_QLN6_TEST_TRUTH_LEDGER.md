# QLN-6 Test Truth Ledger

```text
PHASE=QLN-6
SUITE=engine/tests/test_strategy_dna_qln6.py
RESULT=PASS
```

## Focused suite

| Check | Count |
|---|---|
| Collected | 10 |
| Passed | 10 |
| Failed | 0 |

Commands:

```text
PYTHONPATH=. .venv/Scripts/python.exe -m pytest engine/tests/test_strategy_dna_qln6.py -q
```

## Coverage vs Acceptance

| Contract | Test |
|---|---|
| DNA + genealogy + similarity | `test_dna_and_genealogy_from_reconstructed_packages` |
| Memory NO_EDGE_FOUND | `test_research_memory_allows_negative_results` |
| Counterfactual deny chase-pass | `test_budget_and_counterfactual_forbid_optimize_until_pass` |
| Budget OPTIMIZE_UNTIL_PASS raise | `test_budget_optimize_until_pass_raises` |
| Budget exceed raise | `test_budget_exceed_raises` |
| Committee NO_EDGE | `test_committee_allows_no_edge` |
| KILL→NO_EDGE map | `test_kill_maps_to_no_edge_found` |
| Finalize + graveyard bridge | `test_finalize_kill_persists_memory_and_graveyard` |
| Promote no false graveyard | `test_finalize_promote_no_graveyard` |
| Entry HE artifact | `test_entry_he_packages_exist` |
