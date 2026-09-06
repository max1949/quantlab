# QuantLab Autonomous Engineering Pack

Version: v1.0  
Status: **CANONICAL** (Owner-approved; governance-ingested)  
Canonical path: `docs/governance/autonomous-engineering/`  
Purpose: Standard autonomous engineering loop for all future QLN implementation phases.

## Governance priority (binding)

This pack is **subordinate** to, in order:

1. Owner explicit instruction
2. `docs/governance/QUANTLAB_CONSTITUTION.md`
3. Current QLN phase acceptance criteria

Then this pack applies. It MUST NOT override or reinterpret the Constitution.

## Permanent invocation rule

Whenever Owner explicitly approves a QLN phase for engineering, the executing agent MUST, **before any code modification**, automatically load:

1. `docs/governance/QUANTLAB_CONSTITUTION.md`
2. Current QLN phase definition and Acceptance
3. `QUANTLAB_AUTONOMOUS_ENGINEERING_CONTRACT.md`
4. `QUANTLAB_CHANGE_CLASS_MATRIX.md`
5. `QUANTLAB_ACCEPTANCE_EXECUTION_PROTOCOL.md`
6. `QUANTLAB_AUTONOMOUS_STOP_RULES.md`

Confirm:

```text
AUTONOMOUS_ENGINEERING_PROTOCOL_LOADED=YES
```

Otherwise:

```text
ENGINEERING_START=DENY
```

Then: build Phase Work Ledger → run bounded autonomous loop → Closure Report → **STOP**.

## Within-phase autonomy (when Owner has approved that QLN)

```text
AUTO_DISCOVER_WITHIN_PHASE=YES
AUTO_PLAN_WITHIN_PHASE=YES
AUTO_IMPLEMENT_APPROVED_SCOPE=YES
AUTO_TEST=YES
AUTO_REGRESSION=YES
AUTO_SIMILAR_ISSUE_AUDIT=YES
AUTO_REPAIR_TEST_FAILURES=YES
AUTO_RECHECK=YES
AUTO_DOCUMENT=YES
```

## Permanently forbidden autos

```text
AUTO_NEW_FEATURE_OUTSIDE_SCOPE=NO
AUTO_SCOPE_EXPANSION=NO
AUTO_CONSTITUTION_CHANGE=NO
AUTO_ACCEPTANCE_WEAKENING=NO
AUTO_NEXT_QLN=NO
AUTO_LIVE_ENABLE=NO
AUTO_REAL_MONEY=NO
AUTO_BROKER_CREDENTIAL_ACTIVATION=NO
NEXT_PHASE_AUTO_ENTER=NO
```

After current QLN completion: Closure Report → STOP → wait for Owner. Never auto-enter the next QLN because the current phase PASSed.

## Files

- [`QUANTLAB_AUTONOMOUS_ENGINEERING_CONTRACT.md`](./QUANTLAB_AUTONOMOUS_ENGINEERING_CONTRACT.md)
- [`QUANTLAB_CHANGE_CLASS_MATRIX.md`](./QUANTLAB_CHANGE_CLASS_MATRIX.md)
- [`QUANTLAB_ACCEPTANCE_EXECUTION_PROTOCOL.md`](./QUANTLAB_ACCEPTANCE_EXECUTION_PROTOCOL.md)
- [`QUANTLAB_AUTONOMOUS_STOP_RULES.md`](./QUANTLAB_AUTONOMOUS_STOP_RULES.md)
