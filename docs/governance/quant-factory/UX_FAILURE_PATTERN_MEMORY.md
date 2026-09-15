# UX Failure Pattern Memory (Company Memory)

Every real-novice confusion must become a reusable rule + regression — not a one-off copy tweak.

## Workflow

```text
USER_CONFUSION → RCA → UX_FAILURE_PATTERN → MINIMAL_FIX → E2E/UX REGRESSION → COMPANY MEMORY
```

## Priority

| Pri | Symptom | Action |
|-----|---------|--------|
| P0 | Cannot complete path | Fix immediately |
| P1 | Cannot understand result | Fix immediately |
| P1 | No next action | Fix immediately |
| P2 | Jargon hesitation | Fix this cycle |
| P3 | Visual polish | BACKLOG |

## Seed rules (pre-human; enforce in product)

### UX_RULE_HYPOTHESIS_PLAIN_LANGUAGE

Never lead with「假设 / Hypothesis」 alone for novices.

Prefer: 「你想验证的市场规律」 / 「研究问题」.

Regression: Factor Gym idea step copy must not require knowing the word Hypothesis.

### UX_RULE_ONE_NEXT_ACTION

Result surface always shows exactly one next action in plain language.

Regression: `next_best_action` non-empty + UI amber block present (QF-09A).

### UX_RULE_RESEARCH_PERSISTED

After experiment, tell user research is saved for later verification — without Registry/Vault jargon.

Regression: `save_feedback` contains 「已经保存」.

### UX_RULE_NO_DEFAULT_PRO_METRICS

IC / IR / Size exposure folded behind「查看专业数据」.

### UX_RULE_NO_COACHED_FIRST_VALUE

Observer must not explain Factor/IC/IR/Memory/Scientific Core unless stuck; assist → `HUMAN_ASSIST_REQUIRED=YES`.

### UX_RULE_SINGLE_ACCESS_GATE

Never gate Factor Gym (or similar) on global `enabled` in the frontend while nav/API
use a different predicate. Consume only `FACTOR_GYM_ACCESS_ALLOWED` /
`isFactorGymAccessAllowed`. See `ENGINEERING_MEMORY_ACCESS_GATES.md`.

## Log template

```yaml
pattern_id: UX_FAILURE_…
observed_in_sessions: []
stage:
user_words:
rca:
minimal_fix:
regression_test:
status: OPEN|FIXED
```

## Observed patterns (fill from real sessions)

### UX_FAILURE_SUCCESS_PLUS_FATAL_TOAST (2026-09-15)

```yaml
pattern_id: UX_FAILURE_SUCCESS_PLUS_FATAL_TOAST
observed_in_sessions: [prod_factor_scan_2026-09-15]
stage: factor_scan
user_words: 结果出来了但又弹红错「不会创建真实订单」
rca: |
  MAIN POST /factors/scan 500 on stack mode — template_type stack:uuid,uuid
  exceeds VARCHAR(64). FE mapped 5xx to trading copy + kept stale lastScan.
minimal_fix: |
  store template_type=stack; domain-scoped apiErrorMessage; clear stale
  results/errors on mutate; AI aux errors scoped. See FACTOR_SCAN_ERROR_SCOPE_FIX.md
regression_test: test_factor_scan_ux_consistency.py + errorScope.regression.mjs
status: FIXED
```

### UX_FAILURE_DUPLICATE_FRONTEND_GATE (2026-09-15)

```yaml
pattern_id: UX_FAILURE_DUPLICATE_FRONTEND_GATE
observed_in_sessions: [prod_ziyingke_controlled_entry_2026-09-15]
stage: idea_submit
user_words: 研究入门路径尚未开启。请联系管理员，或先使用「证据系统」专业模式。
rca: |
  ENTRY_AUTH=PASS (nav + /factor-gym) but GOLDEN_PATH_AUTH=FAIL.
  FE submitIdea / mount re-gated on status.enabled (global flag OFF) while
  allowlist entitlement already allowed. Duplicate Gate ≠ canonical resolver.
  Old bundle index-D1R7Ecmn.js; feature-flag mistaken for entitlement.
minimal_fix: |
  resolve_factor_gym_access → FACTOR_GYM_ACCESS_ALLOWED; FE isFactorGymAccessAllowed;
  no pre-submit enabled check; Open Beta later auth-all. Preserve gate fix.
  ENGINEERING_MEMORY_ACCESS_GATES.md + FACTOR_GYM_GOLDEN_PATH_GATE_FIX.md
regression_test: |
  test_factor_gym_controlled_entry.py
  test_factor_gym_api.py
  test_factor_gym_golden_path_access.py
status: FIXED
```

### UX_FAILURE_ENTRY_NOT_FINDABLE

```yaml
pattern_id: UX_FAILURE_ENTRY_NOT_FINDABLE
observed_in_sessions: [pre_session_blocker]
stage: entry
user_words: REAL_USER_CANNOT_FIND_FACTOR_GYM=YES
rca: QUANTLAB_FACTOR_GYM=false + prod route undeployed/404; Gym buried or unavailable — not novice skill failure
minimal_fix: |
  Controlled test entry then Open Beta (FACTOR_GYM_OPEN_BETA) for authenticated users;
  nav label Factor Gym（测试版）. Allowlist no longer product dependency.
regression_test: backend/tests/test_factor_gym_controlled_entry.py + test_factor_gym_api.py + test_factor_gym_golden_path_access.py
status: FIXED
```
