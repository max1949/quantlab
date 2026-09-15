# Factor Gym Golden Path Gate Fix — Production Stamp

```text
DATE=2026-09-15
FACTOR_GYM_GLOBAL=false
CONTROLLED_TEST_ENTRY=PASS
CONTROLLED_TEST_GOLDEN_PATH=PASS
REAL_USER_ENTRY_REACHABILITY=PASS
REAL_USER_GOLDEN_PATH_REACHABILITY=PASS
ALLOWLIST_FULL_PATH=PASS
TEST_TOKEN_FULL_PATH=PASS
NON_TEST_USER_HIDDEN=PASS
NON_TEST_USER_API_DENIED=PASS
CANONICAL_ACCESS_RESOLVER=YES
DUPLICATE_GATE_LOGIC=REMOVED_OR_RECONCILED
PUBLIC_ROLLOUT=NO
OWNER_DECISION_REQUIRED=NO
NEXT=REAL_HUMAN_SESSION_COLLECTION
```

## Root Cause

```text
ENTRY_AUTH_RESULT=PASS (allowlist status + nav)
GOLDEN_PATH_AUTH_RESULT=FAIL (pre-fix)
BLOCKING_GATE=FRONTEND_DUPLICATE_STATUS_CHECK (submitIdea re-checked /status)
BLOCKING_ENDPOINT=N/A client-side (ideas never called) / historical ideas 503 before allowlist warm
ROOT_CAUSE=
  1) FE submitIdea duplicated Gate: if (!status.data.enabled) show 「研究入门路径尚未开启…证据系统」
     even when nav already proved allowlist access — status cache/stale/false-negative blocked Idea.
  2) API denied used 503 + legacy「尚未开启」copy instead of invite-only 403.
  3) get_settings lru_cache could stale allowlist until restart — resolver now overlays live env.
```

## Fix

- Single `resolve_factor_gym_access` for status + all `/factor-gym/*`
- FE removes pre-submit status Gate; 403 → invite-only copy
- Status `Cache-Control: no-store`
- Permanent Gate doc: `REAL_USER_GOLDEN_PATH_REACHABILITY.md`
- E2E CASE 1–4 in `test_factor_gym_golden_path_access.py`
