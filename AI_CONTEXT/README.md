# AI_CONTEXT — QuantLab

```text
DERIVED_CONTEXT=YES
CANONICAL_AUTHORITY=NO
REPO_WINS_ON_CONFLICT=YES
PARALLEL_GOVERNANCE=NO
CHAT_TRANSCRIPT_PERSISTED=NO
```

## Purpose

Fast recovery memory for replaceable AIs (ChatGPT, Cursor, Codex, Claude Code, future agents).

**Not** a second Constitution, Decision Ledger, Capability Ledger, or project database.

## Authority order

```text
Repo / code / runtime evidence
  > Canonical governance docs (docs/governance/**)
  > AI_CONTEXT (this folder)
  > Any chat session
```

If AI_CONTEXT disagrees with canonical sources or live repo state: **canonical / repo wins**. Refresh AI_CONTEXT; do not “correct” the repo from stale handoff text.

## What belongs here

| Keep | Do not keep |
|------|-------------|
| Current truth (phase, HEAD, gates, HOLDs) | Chat transcripts |
| Distilled WHY / next action | Chain-of-thought |
| Indexes into canonical docs | Full Constitution / Ledger copies |
| Failure → RCA → fix → regression pointers | Raw log dumps |
| Recent high-value iteration distillations | Timestamp-only noise diffs |

## Files

| File | Role |
|------|------|
| [BOOTSTRAP.md](./BOOTSTRAP.md) | **Start here** — 5–10 min recovery |
| [PROJECT_STATE.md](./PROJECT_STATE.md) | Current operational truth |
| [LAST_ITERATIONS.md](./LAST_ITERATIONS.md) | Recent valuable iterations (distilled) |
| [CHATGPT_HANDOFF.md](./CHATGPT_HANDOFF.md) | Reasoning / planning AI handoff |
| [CURSOR_HANDOFF.md](./CURSOR_HANDOFF.md) | Execution agent handoff |
| [DECISION_INDEX.md](./DECISION_INDEX.md) | Links to canonical decisions |
| [FAILURE_INDEX.md](./FAILURE_INDEX.md) | Links to failure / RCA / regression |
| [CAPABILITY_INDEX.md](./CAPABILITY_INDEX.md) | Links to capability / architecture |

## Update rule (material changes only)

Refresh AI_CONTEXT when any of these change:

- phase / gate / Owner Gate
- P0/P1 open or close
- capability or feature-flag / runtime / deploy
- architecture decision or significant HOLD
- important failure / RCA
- formal iteration closure

At end of each formal iteration, **check** whether these need refresh:

`PROJECT_STATE` · `LAST_ITERATIONS` · `CHATGPT_HANDOFF` · `CURSOR_HANDOFF`

Do **not** update for trivial edits, cosmetic commits, or to bump “last updated” alone.

## Freshness

Every state-bearing file must carry:

```text
DERIVED_CONTEXT=YES
CANONICAL_AUTHORITY=NO
AS_OF_COMMIT=<git short sha>
AS_OF_DATE=<YYYY-MM-DD>
```

When in doubt, re-read canonical paths listed in BOOTSTRAP — not prior chat memory.
