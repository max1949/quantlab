# QUANTLAB_QLN1_ENGINE_BOUNDARY_LEDGER

```text
PHASE=QLN-1
ENGINE_RESPONSIBILITY_BOUNDARY=PASS
```

## Required architecture

```text
Web / Product / Research OS
        ↓
QuantLab Domain (engine/domain)
        ↓
Engine Interface contracts (BacktestEngineContract / PaperRuntimeContract)
        ↓
Adapters (engine/nautilus/*, research vectorized ports)
        ↓
NautilusTrader OR Factor Lab simulator
```

## Forbidden

```text
Web/Product → nautilus_trader internal classes
```

Verified: `engine/domain/**` AST-scan has **zero** `nautilus_trader` imports.

## Responsibility matrix

| Stack | Allowed | Forbidden to become |
|---|---|---|
| Factor Lab / vectorized | exploration, screening, fast research, Factor validations | Second Evidence/Paper/Live/capital authority OS |
| Nautilus path | Spec semantics, higher-fidelity BT, Paper runtime, future Shadow/Live kernel | Product domain definitions bound to Nautilus internals |

## Ports

| Port | Implementation |
|---|---|
| BacktestEngineContract | `engine/nautilus/domain_adapter.py` → `NautilusBacktestAdapter` (lazy) |
| PaperRuntimeContract | Defined; PaperRun continues via existing runner (wire-through later QLN-5) |
| Shared field semantics | `SHARED_STRATEGY_FIELD_SEMANTICS` in `engine_contracts.py` |

```text
QUANTLAB_DOMAIN_INDEPENDENT_OF_NAUTILUS_INTERNAL_API=YES
```
