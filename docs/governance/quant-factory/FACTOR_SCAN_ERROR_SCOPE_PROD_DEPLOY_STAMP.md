# Factor Scan Error Scope — Production Deploy Stamp

```text
DATE=2026-09-15
COMMIT=a773ae1
PRODUCTION_ACCEPTANCE=PASS
ROLLBACK_POINT=/srv/quantlab/frontend-react/dist.bak_scan + prior factor_scan_service.py
```

## Evidence

```text
MAIN_SCAN_REQUEST_STATUS=201   # stack (was 500 StringDataRightTruncation)
TEMPLATE_SCAN_STATUS=201
SCAN_RESULT_RETURNED=YES
template_type=stack (len=5 <= 64)
APPLY_STATUS=200 kind=stack
GLOBAL_FATAL_TOAST_ON_SUCCESS=NO  # FE: clear stale + domain-scoped copy
AUXILIARY_ERROR_SCOPED=YES
STALE_ERROR_CLEARED=YES
UNRELATED_REAL_ORDER_COPY=NO on scan domain (trading domain KEEP)
SCAN_LOGIC_CHANGED=NO
SCIENTIFIC_RESULT_CHANGED=NO
NORMAL_REGRESSION=PASS
SCIENTIFIC_REGRESSION=PASS (stack apply + template scan)
PRO_MODE_REGRESSION=PASS (health ok; research-os untouched)
SIMILAR_PATTERN_SCAN=PASS
OWNER_DECISION_REQUIRED=NO
```

FE asset live: `/app/assets/index-D1R7Ecmn.js` contains `扫描暂时未完成` and domain-scoped 5xx mapper.
