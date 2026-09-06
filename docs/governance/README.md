# QuantLab Governance Index

This directory holds Owner-approved governance SSOT documents.

## Canonical documents

| Document | Status | Role |
|---|---|---|
| [QUANTLAB_CONSTITUTION.md](./QUANTLAB_CONSTITUTION.md) | **CANONICAL** | WHY / WHAT / BOUNDARY / ORDER — Strategy Research & Evidence OS |
| `QUANTLAB_NAUTILUS_CAPABILITY_LEDGER.md` | Not yet created | Planned QLN-0 output |
| `QUANTLAB_PHASE_GATE_LEDGER.md` | Not yet created | Planned phase gate ledger |
| `QUANTLAB_LIVE_AUTHORITY.md` | Not yet created | Planned Live authority ledger |

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
ENGINEERING=FROZEN
QLN_0_STARTED=NO
```

## Historical assets (preserved, not superseded as facts)

- Sprint / product history: [`README.md`](../../README.md), [`README_PRODUCT.md`](../../README_PRODUCT.md)
- Nautilus Evolution Phase 0–7: [`docs/nautilus-migration/`](../nautilus-migration/)
- Acceptance / surface ledgers: [`docs/QUANTLAB_PRODUCTION_FUNCTIONAL_ACCEPTANCE.md`](../QUANTLAB_PRODUCTION_FUNCTIONAL_ACCEPTANCE.md), related `docs/QUANTLAB_*` ledgers
- Architecture snapshot: [`docs/architecture/QUANTLAB_AI_QUANT_OS.md`](../architecture/QUANTLAB_AI_QUANT_OS.md)

If historical docs conflict with this Constitution on **future direction or permissions**, the Constitution wins. Historical **facts** remain as recorded evidence.
