# AI_CONTEXT_PROTOCOL_V1.1 — portable method (not project state)

```text
PROTOCOL=AI_CONTEXT_PROTOCOL_V1.1
DERIVED_CONTEXT_LAYER=YES
CANONICAL_AUTHORITY=NO
COPY_PROJECT_STATE_ACROSS_REPOS=NO
SELF_REFERENTIAL_HEAD_REFRESH=DENY
STATIC_CURRENT_HEAD_IN_TRACKED_CONTEXT=DENY
CURRENT_REPO_HEAD_RUNTIME_DERIVED=YES
```

## Goal

Replaceable AIs recover **80–90% current effective context in 5–10 minutes** from repo files — not from chat.

```text
Repo / runtime evidence > Canonical governance > AI_CONTEXT > Chat
```

## Minimum tree

```text
AI_CONTEXT/
├─ README.md
├─ BOOTSTRAP.md
├─ PROJECT_STATE.md
├─ CHATGPT_HANDOFF.md
├─ CURSOR_HANDOFF.md
├─ LAST_ITERATIONS.md
├─ DECISION_INDEX.md
├─ FAILURE_INDEX.md
├─ CAPABILITY_INDEX.md
└─ AI_CONTEXT_PROTOCOL_V1.md   # or AI_CONTEXT_PROTOCOL.md
```

## HEAD model (never conflate)

| Symbol | Meaning | In tracked files? |
|--------|---------|-------------------|
| `CONTEXT_BASE_HEAD` | State this snapshot was distilled against | YES |
| `CURRENT_REPO_HEAD` | Live `git rev-parse HEAD` | NO — runtime only |
| `PROD_RUNTIME_HEAD` | Production evidence (when applicable) | YES when known |

```text
SELF_REFERENTIAL_HEAD_REFRESH=DENY
# Never commit solely so stored HEAD == new HEAD
```

## Freshness algorithm

1. Read `CONTEXT_BASE_HEAD`  
2. Derive `CURRENT_REPO_HEAD` live  
3. Inspect changes since base  
4. If **material** canonical/runtime/product/deploy changed → `AI_CONTEXT_STALE=YES`  
5. If only `AI_CONTEXT/**` / continuity rule / AI_CONTEXT reports changed → **not** auto-stale  

Material sources: constitution, governance, architecture, capability/decision/failure ledgers, production/runtime truth, business/product code, deployment state.

## Hard rules

1. Index, don’t fork canonical bodies.  
2. Material updates only (not HEAD-equality chores).  
3. No chat / CoT / log pastes.  
4. Headers: `DERIVED_CONTEXT=YES`, `CANONICAL_AUTHORITY=NO`, `CONTEXT_BASE_HEAD`, `AS_OF_DATE`, `PROD_RUNTIME_HEAD` when applicable.  
5. Conflict → canonical wins.  
6. Recovery drill ≤10 min.  
7. Cursor always-apply continuity rule with V1.1 freshness.

## BOOTSTRAP checklist

```text
PROJECT=
CURRENT_PHASE=
CONTEXT_BASE_HEAD=
CURRENT_REPO_HEAD=   # live git
PROD_RUNTIME_HEAD=
CONTEXT_FRESHNESS=
CURRENT_RUNTIME_STATE=
CURRENT_OWNER_GATE=
TOP_3_CURRENT_PRIORITIES=
KNOWN_P0_P1=
CURRENT_HOLDS=
DO_NOT_TOUCH=
NEXT_SAFE_ACTION=
CANONICAL_SOURCES=
```

## Reference implementations

- QuantLab `AI_CONTEXT/` @ protocol land `c759bc4` + V1.1 correction  
- TMOS `AI_CONTEXT/` @ V1 `4ef4d900`/`784f7e7b` + V1.1 correction  
