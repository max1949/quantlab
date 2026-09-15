# CURSOR_HANDOFF — QuantLab (execution)

```text
DERIVED_CONTEXT=YES
CANONICAL_AUTHORITY=NO
AS_OF_COMMIT=c9c8b72
AS_OF_DATE=2026-09-15
AUDIENCE=Cursor / Codex / Claude Code / coding agents
```

## REPO

```text
PATH=C:\Users\Administrator\quantlab
BRANCH=master
HEAD=c9c8b72 (re-verify: git rev-parse HEAD)
```

## ARCHITECTURE (map only)

| Area | Path |
|------|------|
| API | `backend/app/` (`/api/v1`) |
| Science engine | `engine/` |
| Factor Gym | `engine/factor_gym/`, `backend/app/api/v1/routes/factor_gym.py`, `frontend-react/src/pages/FactorGym.tsx` |
| Factor IR / Registry / Vault | `engine/factor_ir/`, `engine/factor_registry/`, `engine/factor_vault/` |
| Scientific baseline | `engine/scientific_baseline/` |
| Research memory | `engine/research_memory/`, `data/research_memory/` |
| UI canonical | `frontend-react/` (legacy `frontend/` deprecated demo) |
| Governance SSOT | `docs/governance/` |
| This pack | `AI_CONTEXT/` |

## CURRENT PHASE / GATE

```text
GATE=REALITY_EVIDENCE_GATE
GOLDEN_PATH_EXPANSION=HOLD
IMAGINED_USER_REFACTOR=DENY
QLN_11=HOLD (Owner-only)
```

## ACTIVE CONTRACTS (do not break)

- Live / real-money / broker credential activation without Owner + gates  
- Pro Evidence OS routes/behavior regression  
- Scientific goldens PASS / canaries expected FAIL  
- Factor Registry as Vault store — no second parallel main factor table  
- `QUANTLAB_FACTOR_GYM` default false in production-shaped configs  
- Constitution / Amendment semantics (docs edits need Owner-grade care)

## FEATURE FLAGS

| Flag | Default | Notes |
|------|---------|-------|
| `QUANTLAB_FACTOR_GYM` | `false` | Enable only sandbox/dev |
| Live trading | DENY | `quantlab_live=False` |

Source: `backend/app/core/config.py`

## TEST COMMANDS (high value)

```powershell
# Scientific baseline
.\.venv\Scripts\python.exe -m pytest engine/tests/test_scientific_baseline_golden_factors.py -q

# Factor Gym / First Value / Vault (when touching Gym)
.\.venv\Scripts\python.exe -m pytest engine/tests/test_factor_gym_first_value_qf09a.py engine/tests/test_factor_vault_v0.py engine/tests/test_human_session_qf11a.py -q

# Backend API gym (when touching routes)
cd backend; ..\.venv\Scripts\python.exe -m pytest tests/test_factor_gym_api.py -q
```

Adjust to changed surfaces; prefer targeted suites over full monolith unless regression risk is broad.

## GOLDEN / CANARY

- Location: `engine/scientific_baseline/`  
- Rule: goldens must PASS; canaries must FAIL as designed  
- Fixture growth: only via BUG → RCA → fixture (`ENGINEERING_MEMORY_SCIENTIFIC_FIXTURES.md`)

## ALLOWED NOW (safe)

- Regression hardening, vault evidence consistency, reproduce determinism  
- Telemetry integrity, human-session tooling (no fake samples)  
- Blind Evaluation **DESIGN_ONLY** docs  
- Documentation / AI_CONTEXT refresh on material change  
- Bugfix with fixture when real RCA exists

## HOLD / DO_NOT_TOUCH (without Owner)

- Golden Path feature expansion / speculative UX redesign  
- BYOK, AI Tutor/Miner, Research Director, Challenge scale, public rollout  
- QLN-11 start, Live enable, real money  
- Parallel factor store / second SSOT governance tree  
- Inventing real-human session data to mark Product First Value PASS

## OWNER GATE

```text
OWNER_DECISION_REQUIRED=NO for Reality Gate safe maintenance
PRODUCT_ADVANCE=needs real novice sessions (Owner recruitment)
QLN_11=explicit Owner authorization required
```

## NEXT_TASK (default if Owner says “continue Factory”)

Support real-session recording + pattern analysis; fix only repeated First Value blockers with UX regression + `UX_FAILURE_PATTERN_MEMORY` entry.

If Owner asks unrelated engineering: re-check gate; do not silently expand scope.

## STOP CONDITIONS

- Any request implying Live / real money / auto next QLN  
- Product scale while `REAL_HUMAN_EVIDENCE=PENDING`  
- AI_CONTEXT conflicting with repo — **repo wins**; refresh handoff  
- Missing tests for scientific / First Value surfaces you changed

## REPORT FORMAT (iteration close)

Distill into governance stamp + refresh AI_CONTEXT if material:

```text
PROBLEM=
ACTION=
EVIDENCE/TESTS=
REGRESSION=
STATE_CHANGE=
NEXT=
```

No chat transcript. No thought dump.
