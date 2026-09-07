"""QLN-6 Strategy DNA / memory / genealogy tests."""

from __future__ import annotations

import json
from pathlib import Path

from engine.strategy_dna import (
    GenealogyGraph,
    ResearchBudget,
    ResearchMemory,
    MemoryRecord,
    assert_within_budget,
    build_dna_from_spec_v2,
    link_parent_child,
)
from engine.strategy_dna.committee import committee_review
from engine.strategy_dna.counterfactual import CounterfactualRequest, propose_counterfactual
from engine.strategy_dna.similarity import dna_similarity
from engine.strategies.v2.package import import_package


ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "strategy_specs" / "historical_reconstructed" / "hist_fl_momentum_w250.v2.package.json"
PKG2 = ROOT / "strategy_specs" / "historical_reconstructed" / "hist_fl_rsi_w14.v2.package.json"


def test_dna_and_genealogy_from_reconstructed_packages():
    assert PKG.exists() and PKG2.exists()
    a = import_package(PKG).strategy_spec
    b = import_package(PKG2).strategy_spec
    da = build_dna_from_spec_v2(a, origin="historical_reconstruction")
    db = build_dna_from_spec_v2(b, origin="historical_reconstruction")
    assert da.signal_kinds
    assert da.content_hash == a.content_hash()
    g = GenealogyGraph()
    link_parent_child(g, da, db, relation="derived_from")
    assert len(g.nodes) == 2
    sim = dna_similarity(da, db)
    assert sim["near_duplicate"] is False


def test_research_memory_allows_negative_results(tmp_path):
    mem = ResearchMemory(tmp_path / "memory.jsonl")
    mem.append(
        MemoryRecord(
            strategy_id="hist_fl_momentum_w20",
            version="v1",
            outcome="NO_EDGE_FOUND",
            reasons=["KILL under frozen gates"],
            negative_result=True,
        )
    )
    mem.append(
        MemoryRecord(
            strategy_id="hist_fl_rsi_w14",
            version="v1",
            outcome="PROMOTE",
            reasons=["gates pass"],
            negative_result=False,
        )
    )
    assert len(mem.negative_results()) == 1


def test_budget_and_counterfactual_forbid_optimize_until_pass():
    budget = ResearchBudget(max_new_candidates=5, max_counterfactuals_per_strategy=2)
    assert_within_budget(budget, created=5)
    pkg = import_package(PKG)
    dna = build_dna_from_spec_v2(pkg.strategy_spec, origin="historical_reconstruction")
    ok = propose_counterfactual(
        dna,
        CounterfactualRequest(
            base_strategy_id=dna.strategy_id,
            change_description="widen window",
            changed_params={"window": 30},
        ),
        budget=budget,
        already_run=0,
    )
    assert ok.status == "RECORDED"
    denied = propose_counterfactual(
        dna,
        CounterfactualRequest(
            base_strategy_id=dna.strategy_id,
            change_description="chase pass",
            must_not_optimize_until_pass=False,
        ),
        budget=budget,
        already_run=0,
    )
    assert denied.status == "DENIED"


def test_committee_allows_no_edge():
    opinions = committee_review({"decision": "KILL", "reasons": ["hard fail: oos"]})
    roles = {o.role for o in opinions}
    assert roles == {"RESEARCHER", "SKEPTIC", "FALSIFIER"}
    assert any(o.allows_no_edge for o in opinions)


def test_phase_a_results_artifact_exists():
    p = ROOT / "docs" / "governance" / "qln6" / "artifacts" / "phase_a_evidence_results.json"
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["GENUINE_HISTORICAL_STRATEGIES_RECOVERED"] == 4
    assert data["HIGHER_EVIDENCE_STRATEGY_COUNT"] >= 2
