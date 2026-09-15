# PROJECT_STATE — QuantLab

```text
DERIVED_CONTEXT=YES
CANONICAL_AUTHORITY=NO
AS_OF_COMMIT=c9c8b72
AS_OF_DATE=2026-09-15
BRANCH=master
```

## Identity

| Field | Value |
|-------|-------|
| PROJECT | QuantLab |
| REPO | `C:\Users\Administrator\quantlab` |
| MISSION | Strategy Research & Evidence OS; Factor Gym as guided additive surface on shared scientific core |

## Dual tracks (do not conflate)

| Track | Current phase | Status |
|-------|---------------|--------|
| **QLN Evidence OS** | QLN-10 closed | QLN-0…10 **PASS**; **QLN-11 HOLD** (Owner-only; no auto-enter) |
| **Quant Factory / Factor Gym** | **REALITY_EVIDENCE_GATE** | Engineering First Value yes; **Product First Value UNPROVEN** |

Canonical:  
- QLN: `docs/governance/campaigns/QUANTLAB_QLN3_TO_10_CAMPAIGN_LEDGER.md`  
- Factory: `docs/governance/quant-factory/REALITY_EVIDENCE_GATE.md`

## Git / deploy

```text
CURRENT_HEAD=c9c8b72e90b2f587d2cd7f616c86b75202420595
CURRENT_HEAD_SHORT=c9c8b72
CURRENT_HEAD_MSG=fix(ui): responsive header capacity model for ZH/EN without overlap
QLN10_SEAL_COMMIT=1a1d36f (campaign ledger)
WORKING_TREE=DIRTY — large uncommitted Factor Gym / QF governance / engine packages present at AS_OF_DATE
PRODUCTION_CHANGE_DEFAULT=DENY
```

Re-verify HEAD with `git rev-parse HEAD` before any deploy claim. Do not treat chat “last deploy” as truth.

## Runtime / flags

```text
QUANTLAB_FACTOR_GYM=false (default; sandbox/dev enable only)
quantlab_live=False
LIVE_TRADING=DENY
REAL_MONEY=DENY
OPENAPI_IN_PRODUCTION=disabled (by design)
UI_CANONICAL=frontend-react/
ENGINE_SCIENCE=engine/
API=/api/v1 (FastAPI backend/)
```

Canonical flag source: `backend/app/core/config.py`.

## Completed (high signal)

- QLN-0…QLN-10 campaign closed; Live Readiness PASS; real money still DENY  
- Quant Factory Phase 0 PASS; scientific golden/canary baseline exists  
- QF-09A First Value engineering acceptance (simulated + E2E); Product First Value still PENDING  
- QF-10 Factor Vault v0 (Registry READ-THROUGH; no parallel store)  
- QF-11A human-session ledger + gate infra (sample size still 0)  
- Reality Evidence Gate + pattern-analysis tooling  
- UI: Challenge dead-click / Paper BTC 500 / responsive header fixes (recent commits)

## In progress / pending evidence

```text
REAL_HUMAN_SAMPLE_SIZE=0
REAL_HUMAN_EVIDENCE=PENDING
PRODUCT_FIRST_VALUE=UNPROVEN
FIRST_VALUE_PRODUCT_VALIDATED=NO
```

## HOLDs (binding)

| Item | Status |
|------|--------|
| Golden Path feature expansion | HOLD |
| Imagined-user UX refactor | DENY |
| BYOK / AI Tutor / AI Miner / Research Director | HOLD |
| Challenge / leaderboard scale / public Factor Gym rollout | HOLD |
| QLN-11 Owner Live Pilot | HOLD (preconditions incomplete) |
| Live / real money / broker credentials | DENY |
| Auto next QLN / `NEXT_PHASE_AUTO_ENTER` | NO |

## Owner Gate

```text
OWNER_DECISION_REQUIRED=NO (for current Reality Gate safe maintenance)
OWNER_ACTION_TO_ADVANCE_PRODUCT=Recruit 1–3 non-quant novices; observer records only; POST /factor-gym/human-sessions
QLN_11=OWNER_ONLY (do not start without explicit Owner authorization)
```

## Current bottleneck (single highest leverage)

**Obtain 1–3 real novice First Value sessions** → pattern analysis → fix only repeated blockers.  
Not: more features, Blind implementation, BYOK, or QLN-11.

## Risks / P0–P1 watch

| ID | Severity | Note |
|----|----------|------|
| Product First Value unproven | P0 product | Engineering path ≠ human proof |
| Working-tree Factor Gym not fully committed | P1 continuity | Large `??` tree; treat committed HEAD vs WT carefully |
| Stale governance README defaults | P2 docs | Prefer campaign + Reality Gate over §43 block if conflict |
| Live / money accidental enable | P0 safety | Permanently DENY without Owner + gates |

## Next highest-leverage safe actions

1. Run real human sessions per `REAL_HUMAN_FIRST_VALUE_PROTOCOL.md`  
2. Safe maintenance only (regression, vault evidence consistency, fixtures from real bugs)  
3. Keep Pro Evidence OS / Factor Lab paths non-regressing  
4. Do **not** start QF-11B Blind **implementation** until EARLY_POSITIVE human evidence  

## Indexes

- Decisions → [DECISION_INDEX.md](./DECISION_INDEX.md)  
- Failures → [FAILURE_INDEX.md](./FAILURE_INDEX.md)  
- Capabilities → [CAPABILITY_INDEX.md](./CAPABILITY_INDEX.md)
