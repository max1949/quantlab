# BOOTSTRAP — QuantLab (read first)

```text
DERIVED_CONTEXT=YES
CANONICAL_AUTHORITY=NO
AS_OF_COMMIT=c9c8b72
AS_OF_DATE=2026-09-15
TARGET_RECOVERY=5_TO_10_MIN
```

## 60-second orientation

```text
PROJECT=QuantLab
MISSION=Strategy Research & Evidence OS (Nautilus kernel) + Quant Factory / Factor Gym guided surface
CURRENT_PRODUCT_GATE=REALITY_EVIDENCE_GATE
QLN_CAMPAIGN=QLN-0..QLN-10 PASS; QLN-11 HOLD (Owner-only)
PRODUCTION_CHANGE=DENY (default)
LIVE_TRADING=DENY
REAL_MONEY=DENY
FACTOR_GYM_DEFAULT=OFF (QUANTLAB_FACTOR_GYM=false)
PRODUCT_FIRST_VALUE=UNPROVEN (REAL_HUMAN_SAMPLE_SIZE=0)
NEXT_SAFE_ACTION=Schedule 1–3 real non-quant novice sessions; record human_sessions; pattern-analysis only — no Golden Path expansion from imagined UX
```

## Read order (do not skip)

1. This file  
2. [PROJECT_STATE.md](./PROJECT_STATE.md)  
3. [CURSOR_HANDOFF.md](./CURSOR_HANDOFF.md) *(if executing)* or [CHATGPT_HANDOFF.md](./CHATGPT_HANDOFF.md) *(if planning)*  
4. [LAST_ITERATIONS.md](./LAST_ITERATIONS.md)  
5. Only then open linked **canonical** docs below as needed  

Stop after step 4 unless the task requires deeper detail. Do **not** re-read months of chat or every QLN folder.

## Canonical sources (authority)

| Need | Canonical path |
|------|----------------|
| Root SSOT | `docs/governance/QUANTLAB_CONSTITUTION.md` |
| Governance index | `docs/governance/README.md` |
| Amendments | `docs/governance/amendments/` |
| Quant Factory domain | `docs/governance/quant-factory/` (**not** parallel SSOT) |
| Current product gate | `docs/governance/quant-factory/REALITY_EVIDENCE_GATE.md` |
| Capability truth | `docs/governance/quant-factory/CURRENT_CAPABILITY_LEDGER.md` |
| Company memory (compact) | `docs/governance/quant-factory/COMPANY_MEMORY_INDEX.md` |
| QLN campaign state | `docs/governance/campaigns/QUANTLAB_QLN3_TO_10_CAMPAIGN_LEDGER.md` |
| Precedence stamp | `docs/governance/quant-factory/QUANT_FACTORY_GOVERNANCE_RECONCILIATION.md` |

```text
PRECEDENCE=ROOT_CONSTITUTION > QLN_SAFETY > QUANT_FACTORY_DOMAIN_RULES > IMPLEMENTATION
SECOND_PARALLEL_SSOT=NO
```

## Recovery checklist (must answer without hunting)

After this pack, you should output:

```text
PROJECT=
CURRENT_PHASE=
CURRENT_HEAD=
CURRENT_RUNTIME_STATE=
CURRENT_OWNER_GATE=
TOP_3_CURRENT_PRIORITIES=
KNOWN_P0_P1=
CURRENT_HOLDS=
DO_NOT_TOUCH=
NEXT_SAFE_ACTION=
CANONICAL_SOURCES=
```

If you cannot fill these from AI_CONTEXT + linked canonicals alone → bootstrap is incomplete; distill further. Do not invent answers from chat memory.

## Stale-doc warning

`docs/governance/README.md` “Current defaults (§43)” can lag campaign / Factory reality. Prefer:

- Campaign ledger for QLN status  
- `REALITY_EVIDENCE_GATE.md` + latest `QUANT_FACTORY_ITERATION_*.md` for Factory product track  
- Live `git rev-parse HEAD` + feature flags in `backend/app/core/config.py` for runtime  

On conflict: **canonical + live repo win**; update AI_CONTEXT.
