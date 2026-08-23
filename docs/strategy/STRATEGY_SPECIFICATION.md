# Strategy Specification

Source of truth for trading strategies in QuantLab AI Quant OS.

## Rules

- Strategy body is the **Strategy Specification**, not an ad-hoc `.py` file.
- Any change to entry/exit/risk/sizing/regime/execution → **new version**.
- Never overwrite historical versions.
- AI may draft specs; AI cannot approve LIVE.
- Ambiguous specs: `ambiguous=true`, `deployable=false`.

## Layout

```text
strategy_specs/examples/*.yaml|json
engine/strategies/spec.py
engine/strategies/validate.py
engine/strategies/compiler.py
generated/strategies/   # compiled artifacts (later)
```

## Compile path

```text
StrategySpec → validate → compile_spec → CompiledStrategy → NautilusBacktestAdapter
```
