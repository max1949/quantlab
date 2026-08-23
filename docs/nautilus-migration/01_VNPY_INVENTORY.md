# 01 — vn.py Inventory (Phase 0)

**Search date:** 2026-08-24  
**Freeze commit:** `bc98198`  

## Executive summary

| Metric | Value |
|--------|-------|
| `import vnpy` / `from vnpy` in production code | **0** |
| `vnpy` package in requirements | **0** (only `pymongo` comment mentions vn.py) |
| VeighNa / CtaTemplate / MainEngine / EventEngine / vt_symbol | **0** |
| Active product references to "vn.py" as channel / docs / UI | **YES** (adapter + UI + scripts) |
| Recommended classification | **Gateway stub + data importer brand**, not embedded engine |

**Implication:** Cleanup is primarily **semantic de-branding + channel migration + archive of import tools**, not deleting a VeighNa runtime.

## Inventory table

| FILE | LINE (approx) | REFERENCE | TYPE | ACTIVE? | RUNTIME? | MIGRATION_REQUIRED? | CLASS | ACTION |
|------|---------------|-----------|------|---------|----------|---------------------|-------|--------|
| `engine/execution_adapter.py` | 1–231 | CHANNEL_VNPY, route_vnpy_order, vnpy_gateway_* | Python | Y | Y (stub/HTTP) | Y | A/B | Replace channel with nautilus/paper-only; keep QMT until separate decision |
| `backend/app/core/config.py` | 82–87 | vnpy_gateway_url/token, min_regime_fit_vnpy | Config | Y | Y | Y | A/C | Rename or deprecate settings behind feature flag |
| `backend/app/services/execution_service.py` | multi | route_vnpy_order / CHANNEL_VNPY | Python | Y | Y | Y | B | Route through trading abstraction |
| `backend/app/services/execution_risk.py` | 36 | execution_min_regime_fit_vnpy | Python | Y | Y | Y | B | Generalize to channel risk policy |
| `backend/app/api/v1/routes/execution.py` | 113–129 | `/route-vnpy`, audit `execution.vnpy.route` | API | Y | Y | Y | C | Keep API temporarily; add `/route-nautilus` later; deprecate path |
| `backend/app/schemas/execution.py` | 18–34 | channel pattern `paper\|vnpy\|qmt` | Schema | Y | Y | Y | C | Extend pattern; mark vnpy legacy |
| `backend/app/services/ops_metrics_service.py` | 82–125 | vnpy_orders counts | Python | Y | Y | Y | B | Keep historical counts; stop new vnpy |
| `backend/app/services/market_data.py` | 334+ | import_vnpy_sqlite | Python | Y | Opt-in script | Y | B | Archive → `archive/legacy_vnpy/` after Nautilus catalog path exists |
| `backend/app/services/vnpy_mongo_import.py` | all | Mongo bar import | Python | Y | Opt-in | Y | B | Archive after Parquet provenance documented |
| `backend/requirements.txt` | 30 | pymongo comment "vn.py" | Deps | Y | Opt-in | Soft | E | Keep pymongo if still needed; rewrite comment |
| `scripts/import-vnpy-*.py/ps1` | all | Import helpers | Scripts | Y | Offline | Y | B/F | Move to archive after replacement |
| `scripts/sync-vnpy-to-oracle.ps1` | all | Sync pipeline | Scripts | Y | Ops | Y | B | Retarget to generic import |
| `scripts/register-parquet-oracle.sh` | 11 | imports vnpy_mongo_import | Scripts | Y | Ops | Y | B | Decouple naming |
| `backend/tests/test_execution.py` | multi | vnpy channel tests | Tests | Y | CI | Y | A | Keep until channel removed; then rewrite |
| `engine/tests/test_execution_adapter.py` | multi | route_vnpy_order | Tests | Y | CI | Y | A | Same |
| `backend/tests/test_vnpy_mongo_import.py` | all | import unit tests | Tests | Y | CI | Y | A | Move with archive |
| `backend/tests/test_research_quality.py` | 179+ | import_vnpy_sqlite | Tests | Y | CI | Y | A | Replace fixture with generic parquet |
| `frontend-react/src/components/PaperExecutionPanel.tsx` | 20–153 | channel vnpy option | UI | Y | Y | Y | D→C | Hide under DEVELOPER or remove from SIMPLE |
| `frontend-react/src/i18n/dictionaries.ts` | multi | "vn.py" strings | UI copy | Y | Y | Y | D | Rewrite to 执行通道 / 已弃用 |
| `frontend-react/src/api/types.ts` | 1006+ | min_regime_fit_vnpy | Types | Y | Y | Y | C | Align with schema |
| `frontend-react/src/api/endpoints.ts` | 1137 | comment | Comment | Y | N | Soft | E | Update |
| `frontend-react/src/api/adminOps.ts` | 43 | vnpy_orders | Types | Y | Y | Soft | C | Keep metric name or alias |
| `frontend-react/src/pages/AdminOps.tsx` | 173 | Stat vnpy orders | UI | Y | Y | Soft | D | Relabel |
| `backend/app/models/user.py` | 4 | L3 vn.py comment | Comment | N | N | Soft | E | Update membership copy |
| `backend/app/services/membership_service.py` | 90 | "vn.py 级深度" | Copy | Y | N | Soft | D | Rephrase |
| `backend/app/api/v1/__init__.py` | 74 | future vn.py comment | Comment | N | N | Soft | E | Update roadmap comment |
| `backend/README.md` / `README.md` / `README_PRODUCT.md` | multi | product docs | Docs | Y | N | Y | E | Rewrite: Nautilus core; vn.py denied |
| `frontend-react/dist/**` | bundled | stale strings | Build artifact | Y | Served if deployed | Soft | D | Rebuild after source change |
| `archive/legacy_vnpy/README.md` | — | placeholder | Archive | Y | N | — | F | READ_ONLY target |

## Classification legend

- **A** Active runtime dependency (stub/HTTP/channel code paths in CI)
- **B** Active business logic
- **C** Active API/schema
- **D** UI wording
- **E** Documentation / comments
- **F** Historical/archive
- **G** Dead code — *none found for real VeighNa*

## Searched terms with zero engine hits

`VeighNa`, `CtaTemplate`, `CtaEngine`, `CtaStrategy`, `PortfolioStrategy`, `BacktestingEngine` (vn.py), `MainEngine`, `EventEngine`, `BaseGateway`, `OrderRequest`, `SubscribeRequest`, `CancelRequest`, `vt_symbol`, `vt_orderid`, `vt_tradeid`, `CTP` gateway classes.

`QMT` appears as a **parallel stub channel** (not vn.py). Retain for now; out of Phase 0 deletion scope.

## Final acceptance counters (current, not yet removal)

```text
ACTIVE_IMPORTS_VNPY_PACKAGE = 0
ACTIVE_RUNTIME_GATEWAY_CHANNEL = 1   # "vnpy" string channel
ACTIVE_DATA_IMPORT_TOOLS = 1
ACTIVE_UI_REFERENCE = 1
ACTIVE_DOC_REFERENCE = 1
ACTIVE_TEST_DEPENDENCY = 1
```

Target after Phase 5:

```text
VN_PY_RUNTIME_DEPENDENCY = 0
VN_PY_PRODUCTION_PATH = 0
... archived under archive/legacy_vnpy/ only
```
