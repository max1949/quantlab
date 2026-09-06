# QUANTLAB_QLN0_TEST_TRUTH_LEDGER

```text
PHASE=QLN-0
MODE=READ_ONLY
REPO_HEAD=29078ad
FULL_SUITE_EXECUTED_THIS_SESSION=NO
FOCUSED_SUITE_EXECUTED=YES
```

## Inventory (collect-only)

| Suite | Collected | Method |
|---|---|---|
| `engine/tests` | **136** | `pytest engine/tests --collect-only` |
| `backend/tests` | **292** | `pytest tests --collect-only` from `backend/` |
| **Total inventoried** | **428** | Sum of above |

## Focused execution (this session)

| Suite | Result |
|---|---|
| `engine/tests/test_strategy_spec_parity.py` | included |
| `engine/tests/test_strategy_validation.py` | included |
| `engine/tests/test_phase6_paper_sandbox.py` | included |
| **Outcome** | **20 passed**, 2 Pandas deprecation warnings |

```text
FOCUSED_PASS=20
FOCUSED_FAIL=0
```

## Category notes (presence, not full rerun)

| Category | Presence | Notes |
|---|---|---|
| Nautilus-specific | YES | `test_nautilus_golden_backtest.py`, parity, phase6 |
| Paper-specific | YES | `test_paper_runs.py`, `test_phase6_paper_sandbox.py` |
| Migration | YES | `test_alembic_0032_paper_runs.py` still in git |
| Integration / E2E scripts | YES | `scripts/phase6_golden_e2e.py`, recovery scripts — **not re-run** this session |
| Legacy vn.py | YES | `test_vnpy_mongo_import.py` (historical) |
| Environment-dependent | YES | Nautilus venv, DB, Redis for many backend tests |
| Strategy validation | YES | decision/graveyard/overfit tests PASS in focused run |

## Regression truth claims

| Check | Status |
|---|---|
| NO_SILENT_TEST_LOSS | **UNKNOWN** vs frozen baseline hash; key Phase 6 tests still present |
| NO_HIDDEN_DESELECTION | No evidence of mass deselection in collect of engine+backend |
| NO_STALE_PASS_CLAIM | Historical docs claiming 20/20 **not** treated as current PASS without re-evidence |
| Historical Acceptance vs tests | Prefer current focused evidence; full suite pending optional Owner ask |

## Explicit non-claims

- Did **not** run full 428-test suite this session.
- Did **not** re-run production golden E2E on server.
- Did **not** mutate tests or golden snapshots.
