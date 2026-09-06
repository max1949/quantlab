# QuantLab Governance Index

This directory holds Owner-approved governance SSOT documents.

## Canonical documents

| Document | Status | Role |
|---|---|---|
| [QUANTLAB_CONSTITUTION.md](./QUANTLAB_CONSTITUTION.md) | **CANONICAL** | WHY / WHAT / BOUNDARY / ORDER — Strategy Research & Evidence OS |
| [amendments/](./amendments/) | **CANONICAL registry** | Owner-approved Constitution Amendments (supplement; do not auto-authorize engineering) |
| [Amendment No. 1](./amendments/QUANTLAB_CONSTITUTION_AMENDMENT_001_PRODUCT_VALUE_COMMERCIAL_DOCTRINE.md) | **CANONICAL** | Product Value & Commercial Doctrine — Prove Before Capital |
| [qln0/](./qln0/) | **QLN-0 PASS** (read-only) | Capability / fragmentation / gap / test / alignment ledgers + reconciliation report |
| [autonomous-engineering/](./autonomous-engineering/) (pack **v1.0**) | **CANONICAL** | Bounded autonomous engineering loop for Owner-approved QLN phases only |
| `QUANTLAB_NAUTILUS_CAPABILITY_LEDGER.md` | Superseded location | Use `qln0/QUANTLAB_QLN0_CAPABILITY_ASSET_LEDGER.md` as QLN-0 output |
| `QUANTLAB_PHASE_GATE_LEDGER.md` | Not yet created | Planned phase gate ledger |
| `QUANTLAB_LIVE_AUTHORITY.md` | Not yet created | Planned Live authority ledger |

## Interpretation order (binding)

1. Owner explicit instruction
2. `QUANTLAB_CONSTITUTION.md` + Owner-approved Amendments
3. Current QLN phase acceptance criteria
4. Autonomous Engineering Pack

Amendments lock **why / for whom / what counts as high value / what is worth building**. They do **not** by themselves start QLN work, open Production/Live, weaken gates, or enter Commercialization.

## Autonomous Engineering Pack — authority & invoke

Pack index: [`autonomous-engineering/README.md`](./autonomous-engineering/README.md)

**Priority (pack is lower than all of the following):**

1. Owner explicit instruction
2. `QUANTLAB_CONSTITUTION.md`
3. Current QLN phase acceptance criteria

**Permanent invoke rule:** when Owner explicitly approves a QLN phase for engineering, the agent MUST load Constitution + that QLN Acceptance + all four pack contracts **before any code modification**, and confirm `AUTONOMOUS_ENGINEERING_PROTOCOL_LOADED=YES`. Otherwise `ENGINEERING_START=DENY`.

Within an approved phase, bounded auto discover/plan/implement/test/regression/similar-issue audit/repair/recheck/document is allowed. Permanent forbid: auto next QLN, scope expansion, Constitution/acceptance weakening, Live / real-money / broker-credential activation. `NEXT_PHASE_AUTO_ENTER=NO` forever unless Owner amends the Constitution.

## Phase numbering (binding)

| Numbering system | Scope | Rule |
|---|---|---|
| Historical Sprint 1–9+ | Early product roadmap in root `README.md` | **PRESERVED** as factual history; do not rewrite |
| Historical `QUANTLAB_NAUTILUS_EVOLUTION` **Phase 0–7** | `docs/nautilus-migration/` reports & related Acceptance docs | **HISTORICAL ROUTE ONLY** — do not extend with Phase 8+ |
| Future construction **QLN-0 → QLN-12** | Constitution §40 | **CANONICAL** for all new engineering phases |

Mixing old Phase numbers for new work is **FORBIDDEN**.

## Current defaults (Constitution §43)

```text
QUANTLAB_DIRECTION=APPROVED
NAUTILUS_KERNEL_DIRECTION=APPROVED
STRATEGY_EVIDENCE_OS=CANONICAL_TARGET
LEGACY_ASSETS=PRESERVE_AND_RECONCILE
NEW_PHASE_NUMBERING=QLN_0_TO_12
FULL_BUILD_NOW=DENY
PRODUCTION_CHANGE=DENY
LIVE_TRADING=DENY
AUTONOMOUS_EXPANSION=DENY
NEXT_ALLOWED_WHEN_OWNER_AUTHORIZES=QLN_0_READ_ONLY
NEXT_PHASE_AUTO_ENTER=NO
AUTO_NEXT_QLN=NO
AUTO_LIVE_ENABLE=NO
AUTO_REAL_MONEY=NO
ENGINEERING=FROZEN
QLN_0_STARTED=NO
AUTONOMOUS_ENGINEERING_PACK=CANONICAL
CONSTITUTION_AMENDMENT_001=CANONICAL
FEATURE_ADMISSION_GATE=EIGHT_QUESTIONS
COMMERCIALIZATION_AUTO_ENTER=NO
```

## Historical assets (preserved, not superseded as facts)

- Sprint / product history: [`README.md`](../../README.md), [`README_PRODUCT.md`](../../README_PRODUCT.md)
- Nautilus Evolution Phase 0–7: [`docs/nautilus-migration/`](../nautilus-migration/)
- Acceptance / surface ledgers: [`docs/QUANTLAB_PRODUCTION_FUNCTIONAL_ACCEPTANCE.md`](../QUANTLAB_PRODUCTION_FUNCTIONAL_ACCEPTANCE.md), related `docs/QUANTLAB_*` ledgers
- Architecture snapshot: [`docs/architecture/QUANTLAB_AI_QUANT_OS.md`](../architecture/QUANTLAB_AI_QUANT_OS.md)

If historical docs conflict with this Constitution on **future direction or permissions**, the Constitution wins. Historical **facts** remain as recorded evidence.
