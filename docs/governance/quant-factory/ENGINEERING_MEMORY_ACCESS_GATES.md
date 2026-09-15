# Engineering Memory — Access Gates & Entitlements

**Status:** BINDING regression memory (Quant Factory / Factor Gym)  
**Scope:** Feature flags vs capability entitlement; FE/API Gate unity  
**Not:** Scientific fixtures (see `ENGINEERING_MEMORY_SCIENTIFIC_FIXTURES.md`)

```text
PAGE_VISIBLE ≠ CAPABILITY_USABLE
FEATURE_FLAG ≠ ENTITLEMENT
ONE_CANONICAL_RESOLVER = YES
DUPLICATE_FRONTEND_GATE = DENY
```

## ENG_RULE_CANONICAL_ACCESS_RESOLVER

All of: nav visibility, page mount, Idea submit, Memory / Hypothesis / Experiment /
Vault / telemetry API — MUST consume **one** backend decision:

```text
FACTOR_GYM_ACCESS_ALLOWED  (alias: allowed)
```

Resolver SSOT: `backend/app/services/factor_gym_access.py`  
Frontend helper: `frontend-react/src/lib/factorGymAccess.ts` → `isFactorGymAccessAllowed`

**Forbidden:**

- Nav Gate A + page Gate B + API Gate C with different predicates
- FE re-checking `/status.enabled` (or any non-canonical field) before calling ideas/run
- Treating global feature flag alone as “user may use the product path”

Regression:

- `backend/tests/test_factor_gym_controlled_entry.py`
- `backend/tests/test_factor_gym_api.py`
- `backend/tests/test_factor_gym_golden_path_access.py`

## ENG_RULE_FEATURE_FLAG_VS_ENTITLEMENT

| Concept | Meaning | Factor Gym field |
|---------|---------|------------------|
| Feature flag (legacy) | Platform / formal-on switch | `enabled` / `global_enabled` / `QUANTLAB_FACTOR_GYM` |
| Entitlement / access | **May this authenticated principal use the capability now?** | `FACTOR_GYM_ACCESS_ALLOWED` |
| Emergency kill | Deny everyone | `QUANTLAB_FACTOR_GYM_KILL` |
| Open Beta | All authenticated users (not formal GA) | `QUANTLAB_FACTOR_GYM_OPEN_BETA` |
| Internal QA only | Not a product dependency | allowlist / test token when Open Beta off |

```text
FEATURE_FLAG_OFF ⇏ ACCESS_DENIED   # Open Beta / allowlist / token may still allow
FEATURE_FLAG_ON  ⇏ PUBLIC_ROLLOUT  # public_rollout stays false until Owner says so
ACCESS_ALLOWED   ⇏ PRODUCT_FIRST_VALUE=PASS
```

## ENG_RULE_NO_DUPLICATE_FRONTEND_GATE

**Incident (2026-09-15 prod P0):** Controlled tester saw Factor Gym nav and page, but Idea
submit showed 「研究入门路径尚未开启…证据系统」.

**RCA:** Old FE gated twice on `status.enabled` (global flag) while nav/entry already
used a broader predicate. Backend allowlist already returned usable status; browser
never reached `/ideas` (or hit legacy copy). Bundle `index-D1R7Ecmn.js` had:

```text
if (!e.enabled) → 「研究入门路径尚未开启…」
submitIdea: if (!(await status).data.enabled) → 「…证据系统」专业模式
```

**Fix (preserved):** Single resolver; FE uses `FACTOR_GYM_ACCESS_ALLOWED` /
`isFactorGymAccessAllowed` only; no pre-submit status Gate; invite-only copy removed
under Open Beta. See `FACTOR_GYM_GOLDEN_PATH_GATE_FIX.md`, `FACTOR_GYM_OPEN_BETA.md`.

**Regression forever:** Never reintroduce `if (!status.enabled)` as the product access
check for Factor Gym (or any controlled capability).

## ENG_RULE_ENTRY_NE_GOLDEN_PATH

Before any real-human observation session:

```text
REAL_USER_ENTRY_REACHABILITY=PASS
REAL_USER_GOLDEN_PATH_REACHABILITY=PASS
```

Minimum: real user Idea → Memory → Hypothesis → Prediction → Experiment → Result.  
Doc: `REAL_USER_GOLDEN_PATH_REACHABILITY.md`.

## Ledger

| Date | Rule / RCA | Regression |
|------|------------|------------|
| 2026-09-15 | Duplicate FE Gate on `enabled` vs allowlist entitlement | `test_factor_gym_*` + Open Beta cases |
| 2026-09-15 | Canonical `FACTOR_GYM_ACCESS_ALLOWED` | `factor_gym_access.py` + `factorGymAccess.ts` |
| 2026-09-15 | Feature flag ≠ entitlement; Open Beta auth-all | `FACTOR_GYM_OPEN_BETA.md` |
