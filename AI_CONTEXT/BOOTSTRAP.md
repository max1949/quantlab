# BOOTSTRAP — QuantLab (read first)

```text
DERIVED_CONTEXT=YES
CANONICAL_AUTHORITY=NO
AI_CONTEXT_PROTOCOL_VERSION=1.1
CONTEXT_BASE_HEAD=c759bc4
PROD_RUNTIME_HEAD=NOT_STAMPED_IN_PACK
CURRENT_REPO_HEAD=RUNTIME_DERIVED
SELF_REFERENTIAL_HEAD_REFRESH=DENY
AS_OF_DATE=2026-09-15
DISTILL_PARENT_FOR_PRODUCT_TRUTH=c9c8b72
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

## Freshness (do this first)

1. `CONTEXT_BASE_HEAD=c759bc4` (AI_CONTEXT protocol land)  
2. `CURRENT_REPO_HEAD=$(git rev-parse HEAD)` live  
3. Diff since base: **AI_CONTEXT-only** → `CONTEXT_FRESHNESS=OK`  
4. Material constitution/governance/product/runtime change → `AI_CONTEXT_STALE=YES`; canonical wins  

Do **not** commit solely to equalize stored HEAD with live HEAD.

## Read order

1. This file  
2. [PROJECT_STATE.md](./PROJECT_STATE.md)  
3. [CURSOR_HANDOFF.md](./CURSOR_HANDOFF.md) or [CHATGPT_HANDOFF.md](./CHATGPT_HANDOFF.md)  
4. [LAST_ITERATIONS.md](./LAST_ITERATIONS.md)  
5. Linked canonicals only as needed  

## Canonical sources

| Need | Canonical path |
|------|----------------|
| Root SSOT | `docs/governance/QUANTLAB_CONSTITUTION.md` |
| Governance index | `docs/governance/README.md` |
| Amendments | `docs/governance/amendments/` |
| Quant Factory domain | `docs/governance/quant-factory/` |
| Current product gate | `docs/governance/quant-factory/REALITY_EVIDENCE_GATE.md` |
| Capability truth | `docs/governance/quant-factory/CURRENT_CAPABILITY_LEDGER.md` |
| Company memory | `docs/governance/quant-factory/COMPANY_MEMORY_INDEX.md` |
| QLN campaign | `docs/governance/campaigns/QUANTLAB_QLN3_TO_10_CAMPAIGN_LEDGER.md` |
| Protocol | [AI_CONTEXT_PROTOCOL_V1.md](./AI_CONTEXT_PROTOCOL_V1.md) |

```text
PRECEDENCE=ROOT_CONSTITUTION > QLN_SAFETY > QUANT_FACTORY_DOMAIN_RULES > IMPLEMENTATION
SECOND_PARALLEL_SSOT=NO
```

## Recovery checklist

```text
PROJECT=
CURRENT_PHASE=
CONTEXT_BASE_HEAD=
CURRENT_REPO_HEAD=
PROD_RUNTIME_HEAD=
CONTEXT_FRESHNESS=
CURRENT_RUNTIME_STATE=
CURRENT_OWNER_GATE=
TOP_3_CURRENT_PRIORITIES=
KNOWN_P0_P1=
CURRENT_HOLDS=
DO_NOT_TOUCH=
NEXT_SAFE_ACTION=
CANONICAL_SOURCES=
```

## Stale-doc warning

Prefer campaign ledger + Reality Gate + live `git`/`config.py` over lagged governance README §43. Canonical wins.
