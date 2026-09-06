# QUANTLAB AUTONOMOUS ENGINEERING CONTRACT v1.0

## 0. Authority

This contract governs autonomous engineering inside an Owner-approved QuantLab QLN phase.

Order of authority:

1. Owner explicit instruction
2. `QUANTLAB_CONSTITUTION.md`
3. Current QLN phase acceptance criteria
4. This contract
5. Implementation plans / tickets / local task ledgers

Conflict => fail closed and STOP.

## 1. Purpose

The goal is NOT unlimited autonomous coding.

The goal is:

> Within one explicitly approved QLN phase, autonomously discover implementation gaps, plan, implement, test, inspect analogous defects, repair failures, verify acceptance criteria, document evidence, and stop.

## 2. Mandatory invocation

For every engineering-capable QLN phase, before modifying code:

`AUTONOMOUS_ENGINEERING_PROTOCOL_LOADED=YES`

The agent MUST read:
- QuantLab Constitution
- current QLN phase scope
- current acceptance criteria
- Change Class Matrix
- Acceptance Execution Protocol
- Autonomous Stop Rules

If any is missing:
`ENGINEERING_START=DENY`

## 3. Scope model

Every autonomous run must establish:

- `QLN_PHASE`
- `OWNER_AUTHORIZATION`
- `IN_SCOPE`
- `OUT_OF_SCOPE`
- `ALLOWED_CHANGE_CLASSES`
- `PRODUCTION_PERMISSION`
- `DATABASE_PERMISSION`
- `MIGRATION_PERMISSION`
- `DEPLOY_PERMISSION`
- `LIVE_PERMISSION`
- `REAL_MONEY_PERMISSION`
- `NEXT_PHASE_AUTO_ENTER=NO`

No inferred authorization.

Silence is not approval.

## 4. Standard autonomous loop

1. Reconcile current state.
2. Build capability/gap ledger.
3. Map each gap to an acceptance criterion.
4. Classify each proposed change.
5. Prioritize blockers first.
6. Implement smallest coherent change.
7. Run focused tests.
8. Run integration tests.
9. Run relevant regression.
10. Perform same-pattern / analogous-issue audit.
11. Fix newly confirmed in-scope defects.
12. Re-run affected tests.
13. Reconcile implementation against acceptance criteria.
14. Repeat only while unresolved in-scope acceptance gaps remain.
15. Produce closure report.
16. STOP.

## 5. Required autonomous capabilities

Allowed within approved scope:

- read code/docs/tests/config
- inspect schemas and migrations
- create implementation ledger
- create tests before/with fixes
- deterministic refactors required by acceptance
- fix regressions caused by current work
- same-pattern audit
- remove duplicate implementation created by current phase
- update technical documentation
- update acceptance evidence
- create rollback notes
- create migration safety notes
- run local/test/staging validation when authorized

## 6. Forbidden autonomous expansion

The system MUST NOT autonomously:

- add a product feature not required by current acceptance
- reinterpret product mission
- widen current QLN scope
- modify Constitution
- lower acceptance thresholds
- remove a safety gate to make tests pass
- weaken test assertions
- hide test failures
- mark UNKNOWN as PASS
- convert FAIL to HOLD without evidence
- enter next QLN
- enable Live
- enable real-money execution
- add broker credentials
- deploy production unless explicitly authorized
- perform destructive data migration unless explicitly authorized
- create a parallel engine when an existing canonical engine can be hardened
- rewrite a subsystem merely for elegance
- replace evidence with assumption

## 7. Anti-sprawl rule

Before adding any new subsystem, table, service, worker, queue, route, model, or runtime:

1. Search for existing equivalent capability.
2. Classify existing asset as KEEP / HARDEN / MERGE / MIGRATE / SOFT_RETIRE / ARCHIVE.
3. Prove why extension is insufficient.
4. Record justification in the phase ledger.

Default:
`REUSE_EXISTING=YES`

## 8. Same-pattern audit

Every confirmed defect that may represent a class of defects triggers:

`SIMILAR_ISSUE_AUDIT=REQUIRED`

The audit must:
- define the defect pattern
- search relevant system surface
- list affected instances
- fix in-scope instances
- mark out-of-scope instances HOLD with rationale
- add regression coverage for the pattern where feasible

No "fix only the reported page" behavior.

## 9. Testing doctrine

A code change is not complete because a focused test passes.

Minimum layers, as applicable:
- unit
- schema/config validation
- integration
- API
- migration
- engine parity
- deterministic replay
- regression
- security boundary
- restart/recovery
- acceptance-level E2E

Tests must validate semantics, not only status codes.

## 10. Evidence doctrine

Every acceptance item must resolve to one of:

- PASS — proven with evidence
- FAIL — proven not satisfied
- BLOCKED — cannot be completed because of an external/non-authorized dependency
- NOT_APPLICABLE — criterion truly does not apply, with rationale

UNKNOWN is not PASS.

## 11. Loop bounds

Autonomy is bounded by:
- current QLN phase
- current acceptance criteria
- current authorization
- stop rules
- safety gates

The loop may perform multiple repair/test cycles, but only to close currently approved acceptance gaps.

It must not invent new goals to remain active.

## 12. Completion

A phase may claim autonomous engineering closure only if:

- all mandatory acceptance criteria are PASS or explicitly Owner-approved exception
- no unresolved newly introduced regression
- no hidden/de-selected test loss
- no unauthorized scope expansion
- no safety boundary weakened
- migration state reconciled
- docs/evidence updated
- working tree/repo state reconciled
- production state reconciled if production work was authorized
- closure report created

Then:

`CURRENT_PHASE_ENGINEERING_CLOSED=YES`
`NEXT_PHASE_AUTO_ENTER=NO`
`STOP=YES`
