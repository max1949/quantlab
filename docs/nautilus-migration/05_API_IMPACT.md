# 05 — API Impact (Phase 0)

## Existing APIs to preserve

All `/api/v1/*` routes remain. Especially:

- `/factors`, `/backtests`, `/validations`, `/research`, `/projects`
- `/auth`, `/users`, `/me`, billing, orgs, feed
- `/execution/*` (paper)

## vn.py-touching APIs

| Endpoint / schema | Impact | Migration plan |
|-------------------|--------|----------------|
| `POST .../execution/paper/orders` with `channel=vnpy` | Active | Soft-deprecate; prefer `paper`; later `nautilus_sandbox` |
| `POST .../paper/orders/{id}/route-vnpy` | Active | Keep until Phase 5; document DEPRECATED |
| execution config payload `vnpy_configured`, `min_regime_fit_vnpy` | Active | Alias → generic gateway fields |
| Admin ops metrics `vnpy_orders` | Active | Keep historical metric |

## Compatibility rule

```text
DO NOT BREAK frontend on master
New surfaces → /api/v1 extensions or /api/v2 when needed
Feature flags gate Nautilus endpoints
```

## Planned new APIs (later phases)

- Strategy Spec CRUD
- Spec → compile
- Nautilus backtest run
- AI strategy builder (draft + ambiguity)
- Chinese report generation

Phase 0: **none shipped**.
