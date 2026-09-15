# REAL_USER_GOLDEN_PATH_REACHABILITY (permanent Gate)

```text
PAGE_VISIBLE ≠ CAPABILITY_AVAILABLE
REAL_USER_ENTRY_REACHABILITY alone = INSUFFICIENT
REAL_USER_GOLDEN_PATH_REACHABILITY = REQUIRED before REAL_HUMAN_SESSION_COLLECTION
```

## Rule

Before any real-novice / controlled-human Factor Gym session:

1. `REAL_USER_ENTRY_REACHABILITY=PASS` — login, see nav (if allowlisted), open `/factor-gym`
2. **`REAL_USER_GOLDEN_PATH_REACHABILITY=PASS`** — same user completes:

```text
Idea → Memory Check → Hypothesis seal → Prediction → Experiment → Result
(STATUS / WHY / ONE_NEXT_ACTION present)
```

Do **not** start human observation if entry works but Idea submit is blocked.

## Canonical access

All of nav / page / API must use `resolve_factor_gym_access` (`FACTOR_GYM_ACCESS_RESOLVER`):

```text
allowed = GLOBAL_ENABLED OR ALLOWLIST_USER OR VALID_TEST_TOKEN
```

`QUANTLAB_FACTOR_GYM` stays **false** for controlled tests (not public rollout).

## Regression

`backend/tests/test_factor_gym_golden_path_access.py` CASE 1–4
