"""QLN-6 Strategy DNA / memory / genealogy / finalize tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.strategies.v2.errors import SpecV2Error
from engine.strategies.v2.package import import_package
from engine.strategy_dna import (
    GenealogyGraph,
    MemoryRecord,
    ResearchBudget,
    ResearchMemory,
    assert_within_budget,
    build_dna_from_spec_v2,
    committee_review,
    evidence_decision_to_memory_outcome,
    finalize_research_outcome,
    link_parent_child,
)
from engine.strategy_dna.counterfactual import CounterfactualRequest, propose_counterfactual
from engine.strategy_dna.similarity import dna_similarity
from engine.validation.graveyard import list_rejects


ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "strategy_specs" / "historical_reconstructed" / "hist_fl_momentum_w250.v2.package.json"
PKG2 = ROOT / "strategy_specs" / "historical_reconstructed" / "hist_fl_rsi_w14.v2.package.json"
HE_PKG = ROOT / "strategy_specs" / "historical_reconstructed" / "hist_fl_momentum_w20.v2.package.json"


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


def test_budget_optimize_until_pass_raises():
    with pytest.raises(SpecV2Error, match="OPTIMIZE_UNTIL_PASS"):
        assert_within_budget(ResearchBudget(optimize_until_pass=True), created=0)


def test_budget_exceed_raises():
    with pytest.raises(SpecV2Error, match="research budget exceeded"):
        assert_within_budget(ResearchBudget(max_new_candidates=2), created=3)


def test_committee_allows_no_edge():
    opinions = committee_review({"decision": "KILL", "reasons": ["hard fail: oos"]})
    roles = {o.role for o in opinions}
    assert roles == {"RESEARCHER", "SKEPTIC", "FALSIFIER"}
    assert any(o.allows_no_edge for o in opinions)


def test_kill_maps_to_no_edge_found():
    assert evidence_decision_to_memory_outcome("KILL") == "NO_EDGE_FOUND"
    assert evidence_decision_to_memory_outcome("PROMOTE") == "PROMOTE"


def test_finalize_kill_persists_memory_and_graveyard(tmp_path):
    mem_path = tmp_path / "memory.jsonl"
    gy_path = tmp_path / "rejects.jsonl"
    result = finalize_research_outcome(
        strategy_id="hist_fl_mean_reversion_w20",
        version="v1",
        evidence_decision="KILL",
        reasons=["hard gate fail: oos"],
        gates={"oos": "FAIL"},
        market="RB",
        memory=ResearchMemory(mem_path),
        persist_graveyard_path=gy_path,
        persist=True,
    )
    assert result.memory_outcome == "NO_EDGE_FOUND"
    assert result.negative_result is True
    assert result.recommendation["continue_optimize"] is False
    assert "继续优化" not in result.recommendation.get("message", "")
    assert result.memory_persisted and result.graveyard_persisted
    negs = ResearchMemory(mem_path).negative_results()
    assert len(negs) == 1
    assert negs[0].outcome == "NO_EDGE_FOUND"
    rejects = list_rejects(path=gy_path)
    assert len(rejects) == 1
    assert rejects[0]["strategy_id"] == "hist_fl_mean_reversion_w20"


def test_finalize_promote_no_graveyard(tmp_path):
    result = finalize_research_outcome(
        strategy_id="hist_fl_rsi_w14",
        version="v1",
        evidence_decision="PROMOTE",
        reasons=["gates pass"],
        memory=ResearchMemory(tmp_path / "m.jsonl"),
        persist_graveyard_path=tmp_path / "g.jsonl",
    )
    assert result.memory_outcome == "PROMOTE"
    assert result.graveyard_persisted is False
    assert not (tmp_path / "g.jsonl").exists()


def test_entry_he_packages_exist():
    assert HE_PKG.exists() and PKG2.exists()
    art = ROOT / "docs" / "governance" / "qln6" / "artifacts" / "original_recovery_and_derived_research.json"
    assert art.exists()
    data = json.loads(art.read_text(encoding="utf-8"))
    assert data["TOTAL_HIGHER_EVIDENCE_STRATEGY_COUNT"] >= 2
    assert data["QLN_6_ENTRY_GATE"] == "PASS"
