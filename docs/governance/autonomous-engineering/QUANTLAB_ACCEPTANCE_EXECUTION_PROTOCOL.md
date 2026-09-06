# QUANTLAB ACCEPTANCE EXECUTION PROTOCOL v1.0

## 1. Acceptance-first engineering

No phase begins with "build features".

It begins with a machine-readable or structured Acceptance Ledger.

Each criterion receives:

- ID
- requirement
- evidence source
- current state
- blocker
- implementation dependency
- test dependency
- final disposition

## 2. Required ledgers

### A. Phase Scope Ledger
What is authorized and forbidden.

### B. Capability Asset Ledger
Existing assets classified:
KEEP / HARDEN / MERGE / MIGRATE / SOFT_RETIRE / ARCHIVE

### C. Acceptance Ledger
One row per acceptance criterion.

### D. Defect / Gap Ledger
Every discovered gap tied to acceptance or marked out-of-scope.

### E. Similar-Issue Ledger
Patterns and analogous affected locations.

### F. Change Ledger
Files, schemas, services, migrations, runtime effects.

### G. Test Ledger
Focused, integration, regression, E2E, migration, recovery and security evidence.

## 3. Work ordering

Priority:
1. safety / authority blockers
2. architecture semantic drift
3. data/schema correctness
4. deterministic runtime correctness
5. acceptance-critical product path
6. recovery/reconciliation
7. UX correctness
8. documentation
9. optional polish

## 4. Iteration rule

One iteration should be:

`GAP -> MINIMAL CHANGE -> FOCUSED TEST -> BROADER TEST -> PATTERN AUDIT -> RECONCILE`

Do not batch unrelated speculative improvements.

## 5. Regression truth

Required checks:
- no silent test deletion
- no unexpected deselection
- no skipped failing suite without documented external cause
- no snapshot/golden update used merely to make changed behavior pass
- no mock-only acceptance when real integration evidence is required

## 6. Semantic parity

Where multiple environments exist (backtest/paper/shadow/live), compare:
- Strategy Spec
- parameters
- data semantics
- clock/session semantics
- orders
- fills
- positions
- risk decisions
- PnL semantics

A route working is not semantic parity.

## 7. Migration acceptance

If migrations are authorized:
- upgrade PASS
- downgrade or documented irreversible policy PASS
- clean database PASS
- existing database PASS
- migration head reconciliation PASS
- rollback/restore plan documented
- historical data preserved unless explicitly approved otherwise

## 8. Closure report

Final report must state at minimum:

QLN_PHASE=
OWNER_SCOPE=
ACCEPTANCE_TOTAL=
PASS=
FAIL=
BLOCKED=
NOT_APPLICABLE=
SIMILAR_ISSUE_AUDIT=
REGRESSION=
MIGRATION=
PRODUCTION_CHANGE=
LIVE_CHANGE=
REAL_MONEY_CHANGE=
UNAUTHORIZED_SCOPE_EXPANSION=
CURRENT_PHASE_ENGINEERING_CLOSED=
NEXT_PHASE_AUTO_ENTER=NO
STOP=YES

Any FAIL in a mandatory criterion =>
`CURRENT_PHASE_ENGINEERING_CLOSED=NO`
and STOP for Owner disposition rather than self-expanding scope.
