# Factor Gym Open Beta — Owner Decision Stamp

```text
DATE=2026-09-15
FACTOR_GYM_OPEN_BETA=PASS
AUTHENTICATED_USER_ACCESS=PASS
ANONYMOUS_ACCESS=DENY
ALLOWLIST_PRODUCT_DEPENDENCY_REMOVED=YES
TEST_TOKEN_PRODUCT_DEPENDENCY_REMOVED=YES
EMERGENCY_KILL_SWITCH=YES (QUANTLAB_FACTOR_GYM_KILL)
PRO_MODE_REGRESSION=PASS
SCIENTIFIC_REGRESSION=PASS
REAL_MONEY=DENY
PUBLIC_ROLLOUT=NO
PRODUCT_FIRST_VALUE=UNPROVEN
REALITY_EVIDENCE=COLLECTING
OWNER_DECISION=OPEN_BETA_AUTHENTICATED_USERS
NEXT=REAL_HUMAN_SESSION_COLLECTION
```

## Access rule (canonical)

```text
FACTOR_GYM_ACCESS_ALLOWED =
  authenticated
  AND NOT QUANTLAB_FACTOR_GYM_KILL
  AND (OPEN_BETA OR legacy QUANTLAB_FACTOR_GYM OR internal QA allowlist/token)
```

Allowlist / test token are **not** product gates under Open Beta; they remain for internal QA when `OPEN_BETA=false`.

## Explicit non-goals

- BYOK / AI Miner / Research Director / Challenge expansion / Live / Real Money: unchanged DENY / out of scope
- Scientific Core / Vault / Graveyard / telemetry: unchanged
- PRODUCT_FIRST_VALUE is **not** auto-PASS
