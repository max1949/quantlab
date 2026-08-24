# QMT Soft Retirement (Phase 5.5)

## Policy

| Flag | Value |
|------|-------|
| CHINA_MARKET_PRIMARY | NO |
| VNPY | REMOVED |
| NAUTILUS | PRIMARY |
| QMT_NEW_CREATE | DENY |
| QMT_NEW_STRATEGY | DENY |
| QMT_NEW_BACKTEST | DENY |
| QMT_UI_SELECTABLE | NO |
| QMT_LEGACY_HISTORY | PRESERVE |
| QMT_LEGACY_AUDIT | PRESERVE |
| ACTIVE_CHINA_ENGINE_CHOICES | 0 |

## Rationale

QuantLab product strategy removes China-market primary engines from the **new-user path**. QMT follows the same soft-retirement pattern as vn.py:

- Historical `channel='qmt'` orders remain queryable and auditable.
- No new orders, routes, or UI selection for QMT.
- Generic importers should be labeled **External Strategy Import / Legacy Strategy Import** when QMT-specific tooling is reused.

## Code Changes

- `engine/execution_adapter.py`: `QmtChannelRetired`, `qmt_configured=False`, gateway list marks QMT deprecated.
- `backend/app/services/execution_service.py`: rejects new `channel=qmt` submissions.
- `backend/app/api/v1/routes/execution.py`: `route-qmt` returns HTTP 410 Gone.
- `frontend-react/src/components/PaperExecutionPanel.tsx`: QMT removed from channel selector.

## Migration Path

Users creating new strategies should use:

**Research Strategy Spec → PAPER_READY → PaperRun (Nautilus Sandbox)**

## Verification

```powershell
cd C:\Users\Administrator\quantlab
$env:PYTHONPATH = (Get-Location).Path
python -m pytest engine/tests/test_execution_adapter.py backend/tests/test_execution.py -q -k qmt
```

Expected:

- New QMT create/route → denied
- Legacy QMT order rows still readable in admin/ops metrics
