"""QLN-6 Entry Gate Integrity Check — instrument identity vs evidence dataset.

Does NOT re-run Evidence thresholds. Corrects Spec universe/lineage and recounts HE.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from engine.domain.versioning import VersionBump, next_strategy_version
from engine.strategies.v2.contract import StrategyContract, validate_contract
from engine.strategies.v2.invariants import default_research_invariants, validate_invariants
from engine.strategies.v2.lineage import LineageRecord, derive_child_lineage, lineage_from_spec
from engine.strategies.v2.package import StrategyPackage, build_package, export_package, import_package
from engine.strategies.v2.semantic_diff import semantic_diff
from engine.strategies.v2.spec_v2 import StrategySpecV2, validate_spec_v2

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "strategy_specs" / "historical_reconstructed"
DERIVED_DIR = PKG_DIR / "derived"
ART = ROOT / "docs" / "governance" / "qln6" / "artifacts"
OUT = ART / "entry_gate_integrity_check.json"

# Prior evidence attribution (from Phase A) — do not recompute gates
PRIOR_EVIDENCE = {
    "hist_fl_momentum_w20": {
        "decision": "KILL",
        "higher_evidence": False,
        "evidence_instrument": "CU",
        "historical_symbols": ["AU", "RB"],
    },
    "hist_fl_momentum_w250": {
        "decision": "HOLD",
        "higher_evidence": True,
        "evidence_instrument": "CU",
        "historical_symbols": ["IF"],
    },
    "hist_fl_mean_reversion_w20": {
        "decision": "KILL",
        "higher_evidence": False,
        "evidence_instrument": "MA",
        "historical_symbols": ["RB"],
    },
    "hist_fl_rsi_w14": {
        "decision": "PROMOTE",
        "higher_evidence": True,
        "evidence_instrument": "CU",
        "historical_symbols": ["AU"],
    },
}


def _primary_historical(symbols: list[str]) -> list[str]:
    # Preserve all historical symbols as universe (multi-symbol history = still not CU/MA)
    return list(symbols)


def restore_original_identity(pkg: StrategyPackage, hist_symbols: list[str]) -> StrategySpecV2:
    """Original historical Spec: universe = historical symbols only; strip evidence remap."""
    data = pkg.strategy_spec.model_dump(mode="json")
    data["universe"]["instruments"] = _primary_historical(hist_symbols)
    vals = data["parameters"]["values"]
    vals.pop("evidence_instrument", None)
    vals["historical_symbols"] = hist_symbols
    vals["instrument_agnostic"] = False
    vals["identity_note"] = "universe is Strategy identity; Factor Lab backtests were symbol-bound"
    data["metadata"]["change_reason"] = "integrity_restore_historical_universe"
    data["metadata"]["description"] = (
        data["metadata"].get("description") or ""
    ) + " [INTEGRITY] universe restored to historical symbols; CU/MA evidence is not original reproduction."
    data["identity"]["version"] = "v1"
    data["identity"]["parent_version"] = None
    # Keep derived_from provenance of reconstruction source
    if not data["identity"].get("derived_from"):
        data["identity"]["derived_from"] = "factor_lab_historical_backtest"
    return validate_spec_v2(data)


def build_derived(
    parent: StrategySpecV2,
    *,
    evidence_instrument: str,
) -> tuple[StrategySpecV2, LineageRecord]:
    """Instrument change → breaking_semantic → derived version (QLN-1/2)."""
    child_data = parent.model_dump(mode="json")
    new_ver = next_strategy_version(parent.identity.version, VersionBump.MINOR)
    child_data["identity"]["version"] = new_ver
    child_data["identity"]["parent_version"] = parent.identity.version
    child_data["identity"]["derived_from"] = f"{parent.identity.strategy_id}@{parent.identity.version}"
    child_data["identity"]["name"] = f"{parent.identity.name} [{evidence_instrument} derived]"
    child_data["universe"]["instruments"] = [evidence_instrument]
    child_data["parameters"]["values"]["evidence_instrument"] = evidence_instrument
    child_data["parameters"]["values"]["validation_class"] = "DERIVED_STRATEGY_VERSION"
    child_data["parameters"]["values"]["cross_instrument_of"] = parent.universe.instruments
    child_data["metadata"]["change_reason"] = "instrument_universe_change_breaking_semantic"
    child_data["metadata"]["tags"] = list(
        dict.fromkeys(
            (child_data["metadata"].get("tags") or [])
            + ["DERIVED_STRATEGY_VERSION", "CROSS_INSTRUMENT_VALIDATION", evidence_instrument]
        )
    )
    child_data["metadata"]["description"] = (
        f"Derived from {parent.identity.strategy_id}@{parent.identity.version} by changing "
        f"universe {parent.universe.instruments} → [{evidence_instrument}]. "
        f"Trading rules/params unchanged. NOT original reproduction."
    )
    child = validate_spec_v2(child_data)
    diff = semantic_diff(parent, child)
    assert any(
        c.change_class == "breaking_semantic" and "instruments" in c.path for c in diff.changes
    ), "expected breaking_semantic on instruments"
    lin = derive_child_lineage(parent, child, kind="logic_changing_child")
    return child, lin


def export_fixed(
    spec: StrategySpecV2,
    *,
    parent_pkg: StrategyPackage | None,
    lineage: LineageRecord,
    path: Path,
    readme: str,
) -> None:
    sid = spec.identity.strategy_id
    ver = spec.identity.version
    contract = validate_contract(
        StrategyContract(
            contract_id=f"{sid}:{ver}:contract",
            strategy_id=sid,
            version=ver,
            what=parent_pkg.strategy_contract.what if parent_pkg else f"{sid} timing",
            why="integrity-corrected identity / derived instrument version",
            when=["env:BACKTEST", "env:PAPER", "data:historical_parquet"],
            when_not=["env:LIVE", "claim_original_reproduction_on_wrong_instrument=true"],
            risk="Unit ±1; historical FactorLab costs; no stop",
            invalidation=[
                "universe instruments change without new derived version",
                "labeling cross-instrument evidence as ORIGINAL_STRATEGY_REPRODUCTION",
            ],
            expected=["positions follow sign(factor)", "instrument matches Spec universe for reproduction claims"],
            abnormal=["lookahead fills", "silent instrument remap"],
            retirement=["superseded by Spec revision"],
        )
    )
    inv = validate_invariants(default_research_invariants(strategy_id=sid, version=ver))
    pkg = build_package(spec=spec, contract=contract, invariants=inv, lineage=lineage, readme=readme)
    path.parent.mkdir(parents=True, exist_ok=True)
    export_package(pkg, path)


def classify_evidence(hist: list[str], evid: str) -> str:
    if evid in hist:
        return "ORIGINAL_STRATEGY_REPRODUCTION"
    # Factor Lab engine is portable but Spec identity is not instrument-agnostic
    return "CROSS_INSTRUMENT_VALIDATION"


def main() -> dict[str, Any]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    original_repro = 0
    cross = 0
    derived_n = 0
    he_valid = 0

    prior_he_depended_on_wrong_identity = False

    for sid, meta in PRIOR_EVIDENCE.items():
        pkg_path = PKG_DIR / f"{sid}.v2.package.json"
        pkg = import_package(pkg_path)
        hist = list(meta["historical_symbols"])
        evid = meta["evidence_instrument"]
        evid_class = classify_evidence(hist, evid)

        # Spec as previously written claimed evidence instrument in universe
        claimed = list(pkg.strategy_spec.universe.instruments)
        identity_mismatch = set(claimed) != set(hist) and evid in claimed and evid not in hist

        instrument_in_identity = True  # QLN-2: universe is Spec identity
        instrument_agnostic = False  # no explicit agnostic contract; backtests symbol-bound

        if evid_class == "ORIGINAL_STRATEGY_REPRODUCTION":
            original_repro += 1
        else:
            cross += 1

        if identity_mismatch or evid_class != "ORIGINAL_STRATEGY_REPRODUCTION":
            # Prior HE on this sid was attributed under wrong/original-labeled identity
            if meta["higher_evidence"]:
                prior_he_depended_on_wrong_identity = True

        # Restore original
        original = restore_original_identity(pkg, hist)
        orig_lin = lineage_from_spec(original)
        export_fixed(
            original,
            parent_pkg=pkg,
            lineage=orig_lin,
            path=pkg_path,
            readme=f"# {original.identity.name}\n\nORIGINAL historical identity (universe={hist}).\n",
        )

        # Derived version for evidence instrument (required: instruments = breaking_semantic)
        derived_spec, derived_lin = build_derived(original, evidence_instrument=evid)
        derived_path = DERIVED_DIR / f"{sid}_{evid.lower()}.v2.package.json"
        export_fixed(
            derived_spec,
            parent_pkg=pkg,
            lineage=derived_lin,
            path=derived_path,
            readme=(
                f"# {derived_spec.identity.name}\n\n"
                f"DERIVED_STRATEGY_VERSION from {sid}@v1; "
                f"CROSS_INSTRUMENT_VALIDATION {hist} → {evid}. Not original reproduction.\n"
            ),
        )
        derived_n += 1

        # HE only counts when evidence instrument matches Spec universe identity
        # → attribute prior gates to DERIVED identity (same frozen results; no retune)
        he_for_derived = bool(meta["higher_evidence"]) and evid == derived_spec.universe.instruments[0]
        if he_for_derived:
            he_valid += 1

        rows.append(
            {
                "strategy_id": sid,
                "instrument_in_strategy_identity": instrument_in_identity,
                "explicitly_instrument_agnostic": instrument_agnostic,
                "historical_symbols": hist,
                "prior_spec_universe": claimed,
                "restored_original_universe": original.universe.instruments,
                "evidence_instrument": evid,
                "evidence_class": evid_class,
                "requires_derived_version": evid_class != "ORIGINAL_STRATEGY_REPRODUCTION",
                "derived_strategy_id": derived_spec.identity.strategy_id,
                "derived_version": derived_spec.identity.version,
                "derived_package": str(derived_path.relative_to(ROOT)),
                "lineage": derived_lin.model_dump(mode="json"),
                "prior_decision": meta["decision"],
                "prior_higher_evidence_on_mislabeled_identity": meta["higher_evidence"],
                "higher_evidence_on_derived_identity": he_for_derived,
                "identity_mismatch_before_fix": identity_mismatch,
            }
        )

    # Integrity: PASS only if no mislabeling remained unaddressed AND recount is coherent
    # Finding wrong HE attribution ⇒ integrity HOLD for the pre-check state; after fix we report facts.
    multiple_he = he_valid >= 2
    real_demand = True

    if prior_he_depended_on_wrong_identity:
        # Per Owner instruction: HE depended on wrong instrument identity → GATE HOLD
        # until correct genuine evidence under correct identity is accepted.
        # Derived packages + reattribution exist, but Entry must not keep PASS on the
        # mislabeled original count. Require HOLD for Entry; campaign does not start QLN-6.
        integrity = "HOLD"
        entry_gate = "HOLD"
        qln6_started = False
        campaign_continues = False
        # HE under correct identity (derived) is recorded but Entry stays HOLD
        # until a subsequent seal accepts derived HE explicitly — do not rubber-stamp PASS.
        he_for_entry = 0
    else:
        integrity = "PASS"
        he_for_entry = he_valid
        entry_gate = "PASS" if (multiple_he and real_demand) else "HOLD"
        qln6_started = entry_gate == "PASS"
        campaign_continues = entry_gate == "PASS"

    summary = {
        "QLN_6_ENTRY_GATE_INTEGRITY": integrity,
        "PRIOR_HE_DEPENDED_ON_WRONG_INSTRUMENT_IDENTITY": prior_he_depended_on_wrong_identity,
        "ORIGINAL_REPRODUCTION_COUNT": original_repro,
        "CROSS_INSTRUMENT_VALIDATION_COUNT": cross,
        "DERIVED_VERSION_COUNT": derived_n,
        "HIGHER_EVIDENCE_ON_DERIVED_IDENTITY": he_valid,
        "HIGHER_EVIDENCE_STRATEGY_COUNT": he_for_entry,
        "QLN_6_ENTRY_GATE": entry_gate,
        "QLN_6_STARTED": "YES" if qln6_started else "NO",
        "CAMPAIGN_CONTINUES": "YES" if campaign_continues else "NO",
        "REAL_RESEARCH_DEMAND": "YES",
        "THRESHOLD_RELAXATION": "NO",
        "RULES_CHANGED": "NO",
        "PARAMS_RETUNED": "NO",
        "strategies": rows,
        "notes": [
            "universe.instruments is Strategy identity (QLN-2); change = breaking_semantic (semantic_diff).",
            "Factor Lab engine is portable across symbols, but recovered Specs were NOT declared instrument-agnostic; historical backtests were symbol-bound.",
            "CU/MA tests are CROSS_INSTRUMENT_VALIDATION → DERIVED_STRATEGY_VERSION; not ORIGINAL_STRATEGY_REPRODUCTION.",
            "Prior HE=2 was attributed to Specs whose universe silently claimed CU/MA while history was AU/RB/IF.",
            "Derived packages written under strategy_specs/historical_reconstructed/derived/; original packages restored to historical universe.",
            "Entry GATE=HOLD because HE count depended on wrong identity; do not start QLN-6 until Entry re-evaluation accepts derived HE under correct IDs.",
        ],
    }
    ART.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in [
        "QLN_6_ENTRY_GATE_INTEGRITY",
        "ORIGINAL_REPRODUCTION_COUNT",
        "CROSS_INSTRUMENT_VALIDATION_COUNT",
        "DERIVED_VERSION_COUNT",
        "HIGHER_EVIDENCE_STRATEGY_COUNT",
        "QLN_6_ENTRY_GATE",
        "QLN_6_STARTED",
        "CAMPAIGN_CONTINUES",
        "HIGHER_EVIDENCE_ON_DERIVED_IDENTITY",
        "PRIOR_HE_DEPENDED_ON_WRONG_INSTRUMENT_IDENTITY",
    ]}, indent=2))
    return summary


if __name__ == "__main__":
    main()
