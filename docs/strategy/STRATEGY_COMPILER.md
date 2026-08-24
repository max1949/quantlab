# Strategy Compiler

```text
StrategySpec → validate → compile_spec → CompiledStrategy → NautilusBacktestAdapter
```

- Generator: `spec_compiler_v1`
- Phase support: `ema_cross` template
- Kind: `SPEC_COMPILED_STRATEGY` (vs future `CUSTOM_STRATEGY`)
- Deterministic via `compile_deterministic()` (excludes timestamp)
- Refuses ambiguous or LIVE/deployable specs
