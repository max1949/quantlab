# 03 — Research Asset Inventory (PRESERVE)

**Rule:** `REUSE > EXTEND > MIGRATE > REWRITE`

## Asset table

| Asset | Location | Status | Nautilus impact |
|-------|----------|--------|-----------------|
| Factor templates | `engine/factor_engine.py` | ACTIVE | Map NL concepts → registry; keep calc |
| Factor model + version | `backend/app/models/factor.py` | ACTIVE | Spec may reference factor_ids |
| Formula / Python factors | `engine/formula*`, `sandbox/` | ACTIVE | Keep; not replace with Nautilus |
| Backtest results | `backtests` table | ACTIVE | Add `engine` field later (`VECTORIZED_LEGACY` / `NAUTILUS`) without rewriting history |
| Validation OOS/WF/sensitivity/robustness | `validations` + engine modules | ACTIVE | Keep gates; feed Robustness Gate |
| Research reports | `research_reports` | ACTIVE | Chinese UX reuse |
| Research projects | projects models/services | ACTIVE | Keep |
| Data snapshots / Parquet | `data/`, market models | ACTIVE | Normalize → Nautilus catalog |
| Data quality | `engine/data_quality.py` | ACTIVE | Extend DATA_GATE |
| Regime | `engine/regime*.py` | ACTIVE | Versioned regime defs later |
| AI advisor / summaries | `engine/ai_advisor.py`, `ai` routes | ACTIVE | No live authority |
| Cost model | `engine/cost_model.py` | ACTIVE | Feed backtest config |
| Paper orders | `paper_orders` | ACTIVE | Separate from Nautilus live |
| Auth / users / membership | auth models | ACTIVE | Untouched |
| Billing / orgs / growth / feed | growth stack | ACTIVE | Untouched (YAGNI: no expansion) |
| Academy / challenges | tasks, challenges | ACTIVE | Untouched |

## Explicit non-assets (do not invent)

- No dedicated `Evidence` / `Claim` ORM tables (TMOS concept). QuantLab uses `ResearchReport.based_on` + validation JSON.
- No Strategy Specification yet.
- No MT5 importer yet (Phase later).

## Protection acceptance targets

```text
EXISTING_RESEARCH_OS = PASS (must remain)
FACTOR_ASSETS = PASS
EXISTING_USERS = PASS
EXISTING_AUTH = PASS
EXISTING_REPORTS = PASS
EXISTING_DATA = PASS
```
