# 06 — UI Impact (Phase 0)

## Current UI surface mentioning vn.py

| Surface | File | User-visible? |
|---------|------|---------------|
| Paper execution channel select | `PaperExecutionPanel.tsx` | YES |
| i18n ZH/EN strings | `dictionaries.ts` | YES |
| Admin ops vn.py order count | `AdminOps.tsx` | Admin YES |

## Target UX (product mandate)

Ordinary users must **never** need to see: NautilusTrader, Python, Rust, vn.py, Parquet, PyO3.

### Modes (future)

- **SIMPLE:** 首页 / AI创建策略 / 我的策略 / 回测 / 模拟 / 真实交易 / 资金与风险
- **PROFESSIONAL:** Data / Factor / Regime / Robustness / …
- **DEVELOPER:** Spec / Generated code / Adapter / Logs

## Phase 0 UI actions

```text
NO_UI_CODE_CHANGE = TRUE (inventory only)
```

## Later cleanup

1. Remove/hide `vnpy` option from SIMPLE mode
2. Relabel admin metrics
3. Rebuild `frontend-react/dist` after source changes
