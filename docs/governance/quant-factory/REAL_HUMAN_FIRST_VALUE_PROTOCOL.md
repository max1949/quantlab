# Real Human First Value — QF-11A Protocol

```text
PHASE=QF-11A
REAL_HUMAN_EVIDENCE=PENDING
PRODUCT_FIRST_VALUE=UNPROVEN
FIRST_VALUE_PRODUCT_VALIDATED=NO
ENGINEERING_FIRST_VALUE=YES
ENGINEERING_CONTINUE=YES
PRODUCT_SCALE=HOLD
PUBLIC_FACTOR_GYM_ROLLOUT=HOLD
BYOK_PUBLIC_ROLLOUT=HOLD
AI_MINER=HOLD
RESEARCH_DIRECTOR=HOLD
CHALLENGE_SCALE=HOLD
REAL_MONEY=DENY
```

## Behavior acceptance (not interview)

Cohort: 1–3 non-quant novices (undergrad OK; no Python; no prior guide).

Brief only:

> 请用这个工具研究一个你觉得市场上可能存在的规律。

Do **not** explain Factor / Hypothesis / IC / IR / Size / Memory / Scientific Core unless user is stuck.
Any help → `HUMAN_ASSIST_REQUIRED=YES` + `ASSIST_STAGE=`.

Coached completion ≠ true First Value.

## Pre-session Gate (mandatory)

```text
REAL_USER_ENTRY_REACHABILITY=PASS
REAL_USER_GOLDEN_PATH_REACHABILITY=PASS   # see REAL_USER_GOLDEN_PATH_REACHABILITY.md
```

Page visible ≠ Golden Path usable. Do not begin observation until controlled tester completes Idea→Experiment→Result.

## Session ledger

Use `engine.factor_gym.human_session` → `data/factor_gym/human_sessions.jsonl`

API:

- `GET /factor-gym/human-sessions/template`
- `POST /factor-gym/human-sessions`
- `GET /factor-gym/human-sessions/aggregate`

Timing fields: START → IDEA → MEMORY → HYPOTHESIS → PREDICTION → EXPERIMENT start/complete → RESULT_ACK → NEXT_ACTION → SECOND_EXPERIMENT → END

Also: FIRST_CONFUSION_STAGE, FIRST_DEAD_END_STAGE, ASSIST_*, JARGON_CONFUSION_COUNT, BACKTRACK_COUNT, ABANDONED_STAGE, USER_UNDERSTANDS_RESEARCH_PERSISTED

## REAL_SESSION_FIRST_VALUE=PASS only if all

```text
PATH_COMPLETED=YES
USER_CAN_STATE_WHAT_THEY_TESTED=YES
USER_CAN_EXPLAIN_RESULT_IN_PLAIN_LANGUAGE=YES
USER_CAN_STATE_ONE_NEXT_ACTION=YES
NO_PYTHON_REQUIRED=YES
SCIENTIFIC_RESULT_NOT_MANUALLY_INTERPRETED_FOR_USER=YES
TIME_TO_FIRST_VALID_EXPERIMENT <= 20 MINUTES
NO_COACHED_COMPLETION=YES
```

## Five questions only

1. 你刚才研究了什么？
2. 系统最后告诉你什么？
3. 为什么这个想法可能还不可靠？
4. 下一步你会做什么？
5. 你愿不愿意现在再研究一个想法？

Aha: SECOND_EXPERIMENT_INTENT / STARTED / SELF_GENERATED_SECOND_IDEA → AHA_SIGNAL

## Evidence labels (n<5 never statistically validated)

PENDING | EARLY_POSITIVE | EARLY_NEGATIVE | MIXED

Never: FULLY_VALIDATED from small n.

Min unlock (n≥3): ≥2 PASS, dead-end≤33%, result/next comprehension≥67%, ≥1 second-intent.

Stronger early validation (n≥5): see section O in master directive → `PRODUCT_FIRST_VALUE=VALIDATED_EARLY` only.

## Assetize confusion

See `UX_FAILURE_PATTERN_MEMORY.md`.

## Parallel HOLD / ALLOW

ALLOW: Vault evidence, lineage, reproduce, protocol metadata, graveyard, golden/canary from bugs, telemetry, Blind DESIGN_ONLY, Owner Alpha Shelf DESIGN_ONLY.

HOLD: BYOK, AI Tutor/Miner, Research Director, bounty, public challenge/launch/acquisition, marketplace, real money.

## Blind (QF-11B)

DESIGN only until EARLY_POSITIVE — `QF11B_BLIND_EVALUATION_DESIGN.md`.
