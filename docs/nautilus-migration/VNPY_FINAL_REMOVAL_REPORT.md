# VNPY_FINAL_REMOVAL_REPORT

**Date:** 2026-08-24  
**Mode:** QUANTLAB_NAUTILUS_EVOLUTION_MODE / PHASE_5  

```text
ACTIVE_IMPORTS=0
ACTIVE_RUNTIME=0
ACTIVE_CHANNELS=0
ACTIVE_STRATEGIES=0
ACTIVE_BACKTESTS=0
ACTIVE_UI=0
ACTIVE_CONFIG=0
ACTIVE_DOCS=0
ACTIVE_TEST_DEPENDENCY=0

HISTORICAL_REFERENCES=YES
ARCHIVED=YES
```

## Remaining string hits (classified)

| Class | Examples | Allowed? |
|-------|----------|----------|
| ARCHIVE | `archive/legacy_vnpy/**` | YES |
| LEGACY_AUDIT | `channel=="vnpy"` metrics/history labels | YES |
| MIGRATION_DOC | `docs/nautilus-migration/**` | YES |
| TEST_FOR_LEGACY_COMPATIBILITY | reject/410 tests, `VnpyChannelRetired` | YES |
| DEPRECATED settings keys | `vnpy_gateway_url` unused | YES (kept for env compat) |
| Product “已退役” notices | README / UI historical label | YES |

## Evidence

- New `channel=vnpy` create → 422  
- `POST .../route-vnpy` → 410  
- UI channel selector: paper + qmt only  
- Import scripts copied under `archive/legacy_vnpy/scripts/`  
- Historical `paper_orders.channel='vnpy'` not rewritten  

```text
VNPY_REMOVAL=PASS
NEW_VNPY_USER_ACTIONS=0
VNPY_HISTORICAL_AUDIT=PRESERVED
```
