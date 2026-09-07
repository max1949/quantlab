# QLN-6 Similar Issue Audit

```text
PHASE=QLN-6
SIMILAR_ISSUE_AUDIT=PASS
```

| Issue | Risk | Disposition |
|---|---|---|
| Dual graveyard (`validation.graveyard` vs `strategy_dna.graveyard`) | Split persistence | **Mitigated** — `persist_reject` dual-writes to validation JSONL SSOT |
| Evidence decisions only PROMOTE/HOLD/KILL | NO_EDGE not in Evidence enum | **Accepted** — Memory maps KILL→`NO_EDGE_FOUND` at research finalize; Evidence SSOT unchanged |
| Legacy `research_quality_service` “继续优化” hint | Constitution: failure must not hide as optimize | **Documented HOLD** — Paper graduation checklist UX only; QLN-6 `finalize_research_outcome` returns `continue_optimize=False` for negatives |
| Counterfactual stub vs full §18 Lab | Incomplete CF richness | **Deferred** — contract DENY optimize-until-pass is Acceptance-critical; full CF deferred |
| DNA fingerprint vs full §15 behavioral DNA | Partial richness | **Deferred** — Spec-derived DNA sufficient for QLN-6 foundation seal |
| Phase-A CU/MA HE mislabel | Instrument identity | **Closed** — Integrity HOLD + Original Recovery on real AU/RB/IF |
