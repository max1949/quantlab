# Factor Scan Error Scope Fix (P1) — 2026-09-15

```text
PATTERN_ID=UX_FAILURE_SUCCESS_PLUS_FATAL_TOAST
CASE=A+B+C (composite)
MAIN_SCAN_REQUEST_STATUS=500 (stack) / 201 (template)
AUXILIARY_FAILED_REQUEST=NONE (for the fatal toast)
HTTP_STATUS=500
ERROR_SOURCE=BACKEND (primary) + FRONTEND (copy + stale state)
```

## Evidence (production nginx + uvicorn)

Project `efcbb279-fc85-4128-967e-d5e63396c334` around 21:45–21:46 CST:

| Time | Request | Status |
|------|---------|--------|
| 21:45:08 | POST `/api/v1/factors/scan` | **500** |
| 21:45:17 | POST `/api/v1/factors/scan` | **500** |
| 21:45:49 | POST `/api/v1/factors/scan` | **500** |
| 21:45:53 | POST `/api/v1/factors/scan` | **201** |
| 21:46:17 | POST `/api/v1/factors/scan` | **500** |

Uvicorn traceback (21:46:17):

```text
psycopg.errors.StringDataRightTruncation: value too long for type character varying(64)
template_type='stack:{uuid},{uuid}'  # length 79 > 64
```

Template scans succeed (201). Stack-weight scans compute ranking/IC then fail on INSERT → HTTP 500.

Frontend maps any 5xx via `apiErrorMessage` to paper-trading copy including「不会创建真实订单」, and leaves prior `lastScan` visible → user sees results + fatal toast.

## Root Cause

1. **Backend (blocking):** `factor_scans.template_type VARCHAR(64)` cannot store `stack:uuid,uuid` (79 chars). Postgres rejects INSERT after scan work completes.
2. **Frontend CASE B:** new scan start did not clear stale `lastScan` / error toasts → prior SUCCESS results coexist with new FATAL toast.
3. **Frontend CASE C / copy:** generic 5xx mapper reused trading real-order warning on research/scan.

## Fix (no DB migration)

- Persist stack scans as `template_type="stack"`; factor IDs remain in `results[].params.weights` for apply.
- Accept legacy `stack:` prefix in apply/display helpers.
- Domain-scoped `apiErrorMessage(..., domain)` — scan/auxiliary never get real-order copy; trading keeps it.
- FactorScanPanel: clear stale errors + results on mutate; AI failures scoped (info + inline), not global fatal.
- Rule: `SUCCESS_RESULT_AND_FATAL_ERROR_COEXIST=DENY`

## Similar pattern scan

| Finding | Action |
|---------|--------|
| FactorScanPanel AI/compare → global error toast | Fixed scoped |
| Experiments.tsx AI/batch same pattern | Fixed scoped |
| PaperTrading intentional real-order copy | KEEP (`domain=trading`) |
| Generic 5xx default still said real-order | REMOVE from generic; trading-only |
| Validation/Backtest AI review still global error | HOLD (non-scan; not same SUCCESS+fatal coexistence on scan click) |
| Tab pollution via shared toast store | Mitigated via `clearErrorToasts` on new scan |

```text
SIMILAR_ERROR_SCOPE_ISSUES_FOUND=5
FIXED_SAFE=4
HOLD=1
```

## Regression

- `backend/tests/test_factor_scan.py::test_stack_weight_scan`
- `backend/tests/test_factor_scan_ux_consistency.py`
- `node frontend-react/src/api/errorScope.regression.mjs`
