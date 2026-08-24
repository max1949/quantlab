# 10 — vn.py Phase 5 Delta Inventory

**Date:** 2026-08-24  
**Base:** Phase 0 inventory + Phase 1–4 code  

| REFERENCE | CURRENT_STATUS | USER_VISIBLE? | RUNTIME? | HISTORICAL? | ACTION | RESULT |
|-----------|----------------|---------------|----------|-------------|--------|--------|
| UI channel `<option vnpy>` | Active create path | Y | Y | N | Remove from selector; paper+qmt only | DONE |
| i18n `execChannelVnpy` etc. | Active labels | Y | N | Soft | Relabel as legacy historical | DONE |
| Admin `vnpy_orders` metric | Active count | Admin | Read | Y | Relabel 历史引擎订单 | DONE |
| `POST ... channel=vnpy` | Creates stub orders | API | Y | N | Reject NEW with VNPY_CHANNEL_RETIRED | DONE |
| `POST .../route-vnpy` | Routes paper→vnpy | API | Y | N | HTTP 410 Gone | DONE |
| `execution_config` channels list | Advertises vnpy | Y | Y | N | available=false, deprecated=true | DONE |
| Config `vnpy_gateway_*` | Still in Settings | N | Soft | Y | Keep keys for audit; unused for new | KEPT_DEPRECATED |
| `route_vnpy_order` | Stub callable | N | Soft | Y | Raises retired for new use; sync may read | RETIRED_CREATE |
| `import_vnpy_sqlite/mongo` | Opt-in scripts | Ops | Opt-in | Y | Archive scripts; keep shim DEPRECATED | ARCHIVED |
| scripts/import-vnpy-* | Ops | Ops | Opt-in | Y | Move under archive/legacy_vnpy/ | ARCHIVED |
| tests expecting create vnpy | Active | N | CI | Soft | Rewrite to expect reject/410 | DONE |
| README / product docs | Mentions future vn.py | Y | N | N | Rewrite: Nautilus only; vn.py retired | DONE |
| membership L3 copy | "vn.py 级深度" | Soft | N | N | Rephrase depth without vn.py | DONE |
| Migration docs Phase 0–4 | Mentions vn.py | Dev | N | Y | Allowed MIGRATION_DOC | KEEP |
| archive/legacy_vnpy | Placeholder | N | N | Y | Populate scripts + README | DONE |

## Acceptance counters (target)

```text
NEW_VNPY_USER_ACTIONS = 0
VNPY_ACTIVE_CHANNEL = 0   # not offered / not creatable
VNPY_HISTORICAL_AUDIT = PRESERVED  # channel='vnpy' rows untouched
```
