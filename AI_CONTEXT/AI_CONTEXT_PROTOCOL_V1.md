# AI_CONTEXT_PROTOCOL_V1 — portable method (not project state)

```text
PROTOCOL=AI_CONTEXT_PROTOCOL_V1
DERIVED_CONTEXT_LAYER=YES
CANONICAL_AUTHORITY=NO
COPY_PROJECT_STATE_ACROSS_REPOS=NO
```

## Goal

Replaceable AIs recover **80–90% current effective context in 5–10 minutes** from repo files — not from chat.

```text
Repo / runtime evidence > Canonical governance > AI_CONTEXT > Chat
```

## Minimum tree (every adopting repo)

```text
AI_CONTEXT/
├─ README.md              # boundary + update rules
├─ BOOTSTRAP.md           # first read + recovery checklist
├─ PROJECT_STATE.md       # current truth (short)
├─ CHATGPT_HANDOFF.md     # planning AI
├─ CURSOR_HANDOFF.md      # execution AI
├─ LAST_ITERATIONS.md     # last ~5–10 valuable iterations distilled
├─ DECISION_INDEX.md      # links only
├─ FAILURE_INDEX.md       # links only
└─ CAPABILITY_INDEX.md    # links only
```

Optional: acceptance report under that repo’s existing governance path (not a second SSOT).

## Hard rules

1. **Index, don’t fork** — never copy Constitution / Ledgers into AI_CONTEXT bodies.  
2. **Material updates only** — phase, gate, P0/P1, Owner decision, capability/runtime/deploy, architecture, HOLD, failure/RCA, iteration close.  
3. **No chat / CoT / log pastes.**  
4. **Freshness headers** on state files: `DERIVED_CONTEXT=YES`, `CANONICAL_AUTHORITY=NO`, `AS_OF_COMMIT`, `AS_OF_DATE`.  
5. **Conflict → canonical wins**; refresh AI_CONTEXT.  
6. **Recovery drill** before calling ADOPT PASS: cold agent fills BOOTSTRAP checklist in ≤10 min.  
7. **Cursor rule**: always-apply continuity rule with the same material-update policy.

## BOOTSTRAP checklist (must be answerable)

```text
PROJECT=
CURRENT_PHASE=
CURRENT_HEAD=
CURRENT_RUNTIME_STATE=
CURRENT_OWNER_GATE=
TOP_3_CURRENT_PRIORITIES=
KNOWN_P0_P1=
CURRENT_HOLDS=
DO_NOT_TOUCH=
NEXT_SAFE_ACTION=
CANONICAL_SOURCES=
```

## Adopt procedure (per repo)

1. Read-only inventory of that repo’s canonical docs.  
2. Create empty AI_CONTEXT skeleton.  
3. Distill **that repo’s** truth into PROJECT_STATE / handoffs / indexes (links to **its** paths).  
4. Add project rule.  
5. Run recovery drill.  
6. Write local adoption report.  

Do **not** paste QuantLab phase/gate/HEAD into other repos.

## Reference implementation

QuantLab: `AI_CONTEXT/` + `.cursor/rules/ai-context-continuity.mdc`  
Acceptance: `docs/governance/quant-factory/QUANTLAB_AI_CONTEXT_PROTOCOL_REPORT.md`
