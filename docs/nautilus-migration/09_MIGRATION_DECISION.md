# 09 — Migration Decision (Phase 0 Gate)

## Decisions locked

```text
QUANTLAB_CORE_DIRECTION = AI_NATIVE_QUANT_OS
TRADING_ENGINE = NAUTILUSTRADER
VNPY_PRIMARY = REMOVED (policy); residual = stub channel + data importers
MT5 = ALPHA_LAB_AND_MIGRATION_SOURCE (later)
STRATEGY_SOURCE_OF_TRUTH = STRATEGY_SPECIFICATION (to build)
AI_DIRECT_LIVE_AUTHORITY = DENY
RESEARCH_OS = PRESERVE_AND_EXTEND
FIRST_GOAL = NATURAL_LANGUAGE_TO_VALIDATED_BACKTEST
LIVE_TRADING = LATER_GATE
```

## Nautilus version decision

| Field | Value |
|-------|-------|
| Pin | **1.231.0** |
| Channel | released |
| Python | >=3.12,<3.15 (CI/target 3.12; workstation has 3.13 OK) |
| Rejected | 2.0.0rc*, nightly, floating `>=` |
| File | `config/nautilus-version.yaml` |

## vn.py migration matrix (semantic, not string-replace)

| VNPY_COMPONENT | CURRENT_USE | TARGET | MIGRATION_REQUIRED | DATA_MIGRATION | TEST_REQUIRED | DELETE_AFTER_PASS |
|----------------|-------------|--------|--------------------|----------------|---------------|-------------------|
| HTTP channel `vnpy` | Paper route stub | Paper / Nautilus sandbox adapter | YES | Keep historical channel values | YES | YES (code path) |
| Config `vnpy_gateway_*` | Settings | Deprecated secrets path | YES | N | YES | YES |
| `import_vnpy_sqlite/mongo` | Bar ingest | QuantLab Data Normalization → Catalog | YES | Provenance metadata | YES | Move to `archive/legacy_vnpy/` |
| UI / i18n "vn.py" | Labels | Hide / 中文通用名 | YES | N | Soft | YES |
| Docs L3 "vn.py 实盘" | Product copy | Research + Nautilus path | YES | N | N | YES |
| Real VeighNa engine | **Absent** | N/A | NO | N | N | N/A |

## Architecture boundary decision

Create packages under existing repo (match current layout, do not invent monorepo):

```text
engine/nautilus/          # adapter implementations (ONLY nautilus imports)
engine/trading/           # QuantLab abstractions (no nautilus imports)
strategy_specs/           # YAML/JSON specs (Phase 2+)
generated/strategies/     # compiled output (Phase 2+)
config/nautilus-version.yaml
```

## Rewrite denial

No rewrite of Factor Lab, Validation, Auth, Billing, Research Feed, or vectorized backtest in Phase 1. Phase 1 adds **parallel** Nautilus minimal loop behind flags.

## Blockers for Phase 0 → Phase 1

| Blocker | Status |
|---------|--------|
| Unknown architecture | CLEARED |
| Unknown vn.py surface | CLEARED |
| Production destructive migration needed | NONE |
| Live / broker credentials | NOT REQUIRED for Phase 1 |
| Accidental file wipe | RESTORED from HEAD |

## Phase 0 Gate

```text
PHASE_0_COMPLETE = YES
ARCHITECTURE_KNOWN = YES
VNPY_INVENTORY_COMPLETE = YES
NO_DESTRUCTIVE_CHANGES = YES
NEXT = PHASE_1 (Nautilus minimal backtest loop)
```
