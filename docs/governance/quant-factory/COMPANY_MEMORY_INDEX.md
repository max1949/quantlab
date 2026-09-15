# Quant Factory — Company Memory Index (compacted)

```text
GATE=REALITY_EVIDENCE_GATE
PRODUCT_SCALE=HOLD
IMAGINED_USER_REFACTOR=DENY
```

## North star (do not dilute)

1. `FIRST_VALID_RESEARCH_COMPLETION`
2. `SECOND_EXPERIMENT_INTENT`

Not: registrations, pageviews, factor count, experiment count.

## Truth documents

| Doc | Use |
|-----|-----|
| [REALITY_EVIDENCE_GATE.md](./REALITY_EVIDENCE_GATE.md) | Current product gate |
| [REAL_HUMAN_FIRST_VALUE_PROTOCOL.md](./REAL_HUMAN_FIRST_VALUE_PROTOCOL.md) | How to run / score real sessions |
| [UX_FAILURE_PATTERN_MEMORY.md](./UX_FAILURE_PATTERN_MEMORY.md) | USER_FEEDBACK → PRODUCT_MEMORY |
| [QUANT_FACTORY_ITERATION_006_QF11A.md](./QUANT_FACTORY_ITERATION_006_QF11A.md) | Human gate infra |
| [QUANT_FACTORY_ITERATION_005_QF10.md](./QUANT_FACTORY_ITERATION_005_QF10.md) | Vault v0 |
| [QF11B_BLIND_EVALUATION_DESIGN.md](./QF11B_BLIND_EVALUATION_DESIGN.md) | Blind DESIGN_ONLY |
| [ENGINEERING_MEMORY_SCIENTIFIC_FIXTURES.md](./ENGINEERING_MEMORY_SCIENTIFIC_FIXTURES.md) | Fixture growth rule |
| [ENGINEERING_MEMORY_ACCESS_GATES.md](./ENGINEERING_MEMORY_ACCESS_GATES.md) | Flag≠entitlement; one resolver; no duplicate FE Gate |
| [FACTOR_GYM_OPEN_BETA.md](./FACTOR_GYM_OPEN_BETA.md) | Open Beta access (auth users; not formal GA) |

## Engineering surfaces (reuse, don't fork)

| Surface | Path |
|---------|------|
| Human session ledger | `engine/factor_gym/human_session.py` → `data/factor_gym/human_sessions.jsonl` |
| Pattern analysis | `engine/factor_gym/pattern_analysis.py` → `GET …/pattern-analysis` |
| Factor Registry (= Vault store) | `engine/factor_registry/` |
| Vault READ-THROUGH | `engine/factor_vault/` |
| Telemetry T0–T9 | `engine/factor_gym/telemetry.py` |

## Feedback rule

```text
USER_FEEDBACK → REAL_HUMAN_PATTERN_ANALYSIS → highest-leverage repeated fix
              → UX regression + UX_FAILURE_PATTERN_MEMORY
USER_FEEDBACK → RANDOM_FEATURES   # DENY
```

## Real evidence status

```text
REAL_HUMAN_SAMPLE_SIZE=0
REAL_HUMAN_EVIDENCE=PENDING
PRODUCT_FIRST_VALUE=UNPROVEN
REALITY_EVIDENCE=COLLECTING
MODE=REAL_HUMAN_SESSION_COLLECTION
FACTOR_GYM_OPEN_BETA=PASS
NEXT=run novice sessions per REAL_HUMAN_FIRST_VALUE_PROTOCOL.md
```
PRODUCT_FIRST_VALUE=UNPROVEN
FIRST_VALUE_PRODUCT_VALIDATED=NO
```
