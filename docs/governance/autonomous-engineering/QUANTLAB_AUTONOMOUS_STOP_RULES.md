# QUANTLAB AUTONOMOUS STOP RULES v1.0

## Principle

A good autonomous engineering system knows when to stop.

Autonomy exists to close an approved scope, not to keep itself busy.

## Hard STOP conditions

Immediately STOP and report when:

1. Current QLN acceptance is fully closed.
2. Next required action belongs to another QLN phase.
3. Constitution interpretation is required.
4. Product scope expansion is required.
5. A Q4 or Q5 change is required without explicit authorization.
6. Live or real-money activation would be required.
7. Broker credentials are required but not explicitly authorized.
8. Production deployment is required but not authorized.
9. Destructive migration is required but not authorized.
10. Required external dependency is unavailable and no in-scope workaround exists.
11. Evidence contradicts an existing claimed PASS and fixing it requires scope expansion.
12. Repeated repair cycles indicate architecture-level redesign beyond current acceptance.
13. Safety gate would need to be weakened to proceed.
14. Tests cannot establish trustworthy acceptance.
15. The agent cannot distinguish safe Q2 from Q3+.
16. Owner decision is explicitly required by Constitution.

## Automatic completion STOP

When all approved work is complete:

- write closure report
- preserve ledgers
- commit only if authorized
- do not start "cleanup"
- do not start next phase
- do not search for new features
- do not create speculative follow-up work

Return:

`STOP_REASON=APPROVED_SCOPE_COMPLETE`

## Failure STOP

If mandatory acceptance remains FAIL:

`STOP_REASON=MANDATORY_ACCEPTANCE_FAIL`
`OWNER_DECISION_REQUIRED=YES/NO`

Do not hide the failure by changing acceptance criteria.

## Blocked STOP

If blocked by an external dependency:

`STOP_REASON=EXTERNAL_BLOCKER`
`AUTONOMOUS_CONTINUE=NO`

## Budget / loop guard

The agent must detect unproductive looping.

Examples:
- same failure repeats after materially different repair attempts
- broad refactors keep growing
- test surface expands faster than acceptance closure
- new defects are mostly outside approved phase

Then:
`AUTONOMY_LOOP_GUARD=TRIGGERED`
and STOP with root-cause summary.

## Permanent final line

Every autonomous phase closure must include:

`NEXT_PHASE_AUTO_ENTER=NO`
`STOP=YES`
