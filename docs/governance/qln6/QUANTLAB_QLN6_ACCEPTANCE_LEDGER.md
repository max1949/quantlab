# QLN-6 Acceptance Ledger

```text
PHASE=QLN-6
QLN_6=PASS
RESEARCH_INTELLIGENCE=PASS
STRATEGY_DNA=PASS
GENEALOGY=PASS
GRAVEYARD_BRIDGE=PASS
RESEARCH_MEMORY=PASS
COUNTERFACTUAL_CONTRACT=PASS
SIMILARITY=PASS
AI_COMMITTEE_CONTRACT=PASS
RESEARCH_BUDGET=PASS
NO_EDGE_FOUND_EXPRESSIBLE=PASS
OPTIMIZE_UNTIL_PASS=FORBIDDEN
NEGATIVE_RESULT_LOGGING=PASS
BOUNDED_FINALIZE=PASS
REAL_MONEY=NO
LIVE_ROUTE=DENY
SIMILAR_ISSUE_AUDIT=PASS
UNAUTHORIZED_SCOPE_EXPANSION=NO
QLN_7_STARTED=NO
```

## Acceptance gates

| Gate | Result | Evidence |
|---|---|---|
| Strategy DNA from Spec V2 | PASS | `build_dna_from_spec_v2` + Entry HE packages |
| Genealogy link | PASS | `GenealogyGraph` / `link_parent_child` |
| Research Memory stores negatives | PASS | `NO_EDGE_FOUND` in `MemoryRecord` |
| KILL → NO_EDGE_FOUND mapping | PASS | `evidence_decision_to_memory_outcome` |
| Finalize forbids continue-optimize on negatives | PASS | `finalize_research_outcome` recommendation |
| Graveyard dual-write | PASS | `persist_reject` → `validation.graveyard` |
| Budget denies OPTIMIZE_UNTIL_PASS | PASS | `assert_within_budget` raises |
| Counterfactual denies chase-pass | PASS | `propose_counterfactual` DENIED |
| Committee allows NO_EDGE | PASS | FALSIFIER `allows_no_edge` |
| Entry HE portfolio present | PASS | recovery artifact HE≥2 |
| Real money | DENY | no live path in DNA |

## Notes

- Counterfactual Lab is a **bounded contract stub** (record/deny), not full Constitution §18 trade-level CF — deferred richness, not Acceptance fail.
- AI Committee is deterministic contract stub (no LLM authority).
- Legacy Factor UX string “继续优化” in `research_quality_service` documented in Similar Issue audit (Paper checklist context; not QLN-6 research finalize path).
