"""QLN-6 Phase A: recover Factor Lab historical strategies (platform sign(signal) semantics).

FULL_STRATEGY_SEMANTICS_RECOVERABLE when:
  - factor kind=template with known template_type + params
  - execution rule = engine.backtest.signal_to_positions (historical platform contract)
  - instrument/universe + cost from backtest row
Does NOT invent entry/exit beyond the documented historical engine contract.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from engine.backtest import signal_to_positions
from engine.cost_model import CostConfig
from engine.evidence import run_evidence_pipeline
from engine.experiment.assumptions import CostAttribution, ExecutionAssumptions
from engine.experiment.data_trust import run_data_trust_gate
from engine.experiment.ledger import ExperimentLedger
from engine.experiment.record import build_experiment_record
from engine.experiment.time_governance import TimeGovernance
from engine.factor_engine import compute_template_factor
from engine.strategies.v2.contract import StrategyContract, validate_contract
from engine.strategies.v2.invariants import default_research_invariants, validate_invariants
from engine.strategies.v2.lineage import lineage_from_spec
from engine.strategies.v2.package import build_package, export_package
from engine.strategies.v2.spec_v2 import (
    CompatibilityV2,
    ConditionV2,
    DataRequirementsV2,
    ExecutionV2,
    IdentityV2,
    MetadataV2,
    ParametersV2,
    PositionSizingV2,
    RiskV2,
    SignalLogicV2,
    StrategySpecV2,
    TimeframeV2,
    UniverseV2,
    AssumptionsV2,
    validate_spec_v2,
)

SQL_DUMP = Path(r"C:\Users\Administrator\quantlab_business_inserts_pg10.sql")
OUT_DIR = Path("strategy_specs/historical_reconstructed")
LEDGER_DIR = Path("data/experiment_ledger")
RESULTS_PATH = Path("docs/governance/qln6/artifacts/phase_a_evidence_results.json")

# Distinct historical definitions (deduped from 23 backtests)
SEED_DEFINITIONS: list[dict[str, Any]] = [
    {
        "strategy_id": "hist_fl_momentum_w20",
        "name": "Historical FactorLab Momentum w20 (sign)",
        "template_type": "momentum",
        "params": {"window": 20},
        "historical_symbols": ["AU", "RB"],
        "evidence_instrument": "CU",
        "evidence_parquet": "data/market_data/CU_1d.parquet",
        "timeframe": "1d",
        "source_factor_examples": ["mom_011624", "momentum-AU-ee317d", "动量因子"],
    },
    {
        "strategy_id": "hist_fl_momentum_w250",
        "name": "Historical FactorLab Momentum w250 (sign)",
        "template_type": "momentum",
        "params": {"window": 250},
        "historical_symbols": ["IF"],
        "evidence_instrument": "CU",
        "evidence_parquet": "data/market_data/CU_1d.parquet",
        "timeframe": "1d",
        "source_factor_examples": ["动量因子@IF"],
    },
    {
        "strategy_id": "hist_fl_mean_reversion_w20",
        "name": "Historical FactorLab Mean Reversion w20 (sign)",
        "template_type": "mean_reversion",
        "params": {"window": 20},
        "historical_symbols": ["RB"],
        "evidence_instrument": "MA",
        "evidence_parquet": "data/market_data/MA_1d.parquet",
        "timeframe": "1d",
        "source_factor_examples": ["mean_reversion-RB-0d702b"],
    },
    {
        "strategy_id": "hist_fl_rsi_w14",
        "name": "Historical FactorLab RSI w14 (sign of raw RSI)",
        "template_type": "rsi",
        "params": {"window": 14},
        "historical_symbols": ["AU"],
        "evidence_instrument": "CU",
        "evidence_parquet": "data/market_data/CU_1d.parquet",
        "timeframe": "1d",
        "source_factor_examples": ["RSI 强弱"],
        "notes": "Historical engine used np.sign(raw RSI); RSI∈(0,100) ⇒ nearly always +1. Preserved as ORIGINAL.",
    },
]


def split_sql_values(values_blob: str) -> list:
    out: list[str | None] = []
    i = 0
    n = len(values_blob)
    while i < n:
        while i < n and values_blob[i] in " \t\n\r,":
            i += 1
        if i >= n:
            break
        if values_blob.startswith("NULL", i) and (i + 4 >= n or values_blob[i + 4] in ",)"):
            out.append(None)
            i += 4
            continue
        if values_blob[i] == "'":
            i += 1
            buf: list[str] = []
            while i < n:
                ch = values_blob[i]
                if ch == "'" and i + 1 < n and values_blob[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                if ch == "'":
                    i += 1
                    break
                buf.append(ch)
                i += 1
            out.append("".join(buf))
            continue
        j = i
        while j < n and values_blob[j] not in ",)":
            j += 1
        out.append(values_blob[i:j].strip())
        i = j
    return out


def load_backtest_count() -> int:
    text = SQL_DUMP.read_text(encoding="utf-8", errors="replace")
    return sum(1 for ln in text.splitlines() if "INSERT INTO quantlab.backtests" in ln)


def build_spec_v2(defn: dict[str, Any]) -> StrategySpecV2:
    tt = defn["template_type"]
    params = dict(defn["params"])
    inst = defn["evidence_instrument"]
    notes = defn.get("notes") or ""
    return validate_spec_v2(
        StrategySpecV2(
            identity=IdentityV2(
                strategy_id=defn["strategy_id"],
                version="v1",
                name=defn["name"],
                family_id=f"factorlab_{tt}",
                derived_from="factor_lab_historical_backtest",
            ),
            metadata=MetadataV2(
                description=(
                    f"Reconstructed from Factor Lab historical backtests. "
                    f"Signal={tt}{params}; execution=sign(signal) per engine.backtest "
                    f"(ORIGINAL platform contract). Historical symbols={defn['historical_symbols']}. "
                    f"{notes}"
                ),
                author="quantlab_reconstruction",
                tags=["GENUINE_HISTORICAL_STRATEGY", "factor_lab", tt],
                created_by="qln6_phase_a_reconstruction",
                change_reason="historical_semantics_recovery",
            ),
            universe=UniverseV2(
                instruments=[inst],
                venue="CN_FUTURES_RESEARCH",
                asset_class="FUTURES",
            ),
            timeframe=TimeframeV2(timeframe=defn["timeframe"], timezone="UTC"),
            data_requirements=DataRequirementsV2(
                required=["bars"],
                warmup=int(params.get("window", 20)) + 5,
                frequency=defn["timeframe"],
                source_policy="HISTORICAL_PARQUET_MARKET_DATA",
            ),
            signal_logic=SignalLogicV2(
                entry_long=[
                    ConditionV2(
                        type="factor_sign",
                        params={"template_type": tt, "params": params, "side": "long"},
                    )
                ],
                entry_short=[
                    ConditionV2(
                        type="factor_sign",
                        params={"template_type": tt, "params": params, "side": "short"},
                    )
                ],
                exit=[
                    ConditionV2(
                        type="factor_sign_flat_or_flip",
                        params={"template_type": tt, "params": params},
                    )
                ],
                allowed_direction="both",
            ),
            position_sizing=PositionSizingV2(type="fixed", trade_size="1"),
            risk=RiskV2(max_open_positions=1),
            execution=ExecutionV2(
                order_type="MARKET",
                assumptions=AssumptionsV2(
                    fee_model="turnover_fee_rate",
                    slippage_model="turnover_bps",
                    fill_model="lagged_position_bar_return",
                    latency_assumption="signal_t_affects_position_t_plus_1",
                ),
            ),
            compatibility=CompatibilityV2(
                permitted_environments=["BACKTEST", "PAPER"],
                required_engine_features=["factor_sign", tt],
            ),
            parameters=ParametersV2(
                values={
                    "template_type": tt,
                    **{f"param_{k}": v for k, v in params.items()},
                    "execution_rule": "sign(signal)",
                    "execution_rule_source": "engine.backtest.signal_to_positions",
                    "historical_symbols": defn["historical_symbols"],
                    "evidence_instrument": inst,
                }
            ),
        )
    )


def make_compute(defn: dict[str, Any]):
    tt = defn["template_type"]
    params = dict(defn["params"])

    def _fn(df: pd.DataFrame) -> pd.Series:
        sig = compute_template_factor(df, tt, params)
        return signal_to_positions(sig)

    return _fn


def load_ohlcv(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if not isinstance(df.index, pd.DatetimeIndex):
        if "datetime" in df.columns:
            df = df.set_index(pd.to_datetime(df["datetime"]))
        else:
            raise ValueError(f"no datetime index: {path}")
    if df.index.tz is None:
        # Explicit research assumption: naive CN futures timestamps treated as UTC for Trust Gate
        df = df.copy()
        df.index = df.index.tz_localize("UTC")
    return df


def neighborhood_for(defn: dict[str, Any]) -> list[tuple[str, Any]]:
    tt = defn["template_type"]
    w = int(defn["params"].get("window", 20))
    # Factor engine caps window at 250 for templates
    candidates = sorted({max(5, w - 5), w, min(250, w + 5), min(250, max(10, int(w * 1.2)))})
    variants = []
    for ww in candidates:
        d = {**defn, "params": {**defn["params"], "window": int(ww)}}
        variants.append((f"{tt}_w{ww}", make_compute(d)))
    return variants


@dataclass
class EvalRow:
    strategy_id: str
    decision: str
    reality_score: float
    research_debt: float
    gates: dict[str, Any]
    reasons: list[str]
    data_trust: str
    higher_evidence: bool


def run_phase_a() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    ledger = ExperimentLedger(LEDGER_DIR / "experiments.jsonl")

    inspected = load_backtest_count()
    rows: list[EvalRow] = []
    packages: list[str] = []

    for defn in SEED_DEFINITIONS:
        spec = build_spec_v2(defn)
        contract = validate_contract(
            StrategyContract(
                contract_id=f"{defn['strategy_id']}:v1:contract",
                strategy_id=defn["strategy_id"],
                version="v1",
                what=f"FactorLab {defn['template_type']} → sign(signal) timing on futures",
                why="Recovered from historical Factor Lab user/project backtests; platform execution contract preserved",
                when=["env:BACKTEST", "env:PAPER", "data:historical_parquet"],
                when_not=["env:LIVE", "ambiguous=true", "invented_rules=true"],
                risk="Unit ±1 position; fee/slippage via CostConfig; no stop in historical engine",
                invalidation=[
                    "factor template semantics change",
                    "execution rule no longer sign(signal)",
                    "data trust fail on research dataset",
                ],
                expected=["positions follow sign(factor)", "lagged returns avoid lookahead"],
                abnormal=["lookahead fills", "rules not matching engine.backtest"],
                retirement=["superseded by Spec revision", "hypothesis invalidated"],
            )
        )
        inv = validate_invariants(
            default_research_invariants(strategy_id=defn["strategy_id"], version="v1")
        )
        pkg = build_package(
            spec=spec,
            contract=contract,
            invariants=inv,
            lineage=lineage_from_spec(spec),
            readme=f"# {defn['name']}\n\nGENUINE_HISTORICAL_STRATEGY reconstruction.\n",
        )
        pkg_path = OUT_DIR / f"{defn['strategy_id']}.v2.package.json"
        export_package(pkg, pkg_path)
        packages.append(str(pkg_path))

        ohlcv = load_ohlcv(defn["evidence_parquet"])
        from engine.data.data_gate import DataProvenance

        trust = run_data_trust_gate(
            ohlcv,
            provenance=DataProvenance(
                provider="local_market_data_parquet",
                instrument=defn["evidence_instrument"],
                symbol=defn["evidence_instrument"],
                venue="CN_FUTURES",
                timezone="UTC",
                frequency=defn["timeframe"],
                price_type="last",
            ),
            time_governance=TimeGovernance(timezone="UTC"),
            dataset_version="parquet_v1",
            timeframe=defn["timeframe"],
        )
        if trust.status != "PASS":
            rows.append(
                EvalRow(
                    strategy_id=defn["strategy_id"],
                    decision="HOLD",
                    reality_score=0.0,
                    research_debt=100.0,
                    gates={"data_trust": trust.status},
                    reasons=[f"DATA_TRUST={trust.status}"] + trust.issues[:5],
                    data_trust=trust.status,
                    higher_evidence=False,
                )
            )
            continue

        report = run_evidence_pipeline(
            strategy_id=defn["strategy_id"],
            strategy_version="v1",
            ohlcv=ohlcv,
            compute_signal=make_compute(defn),
            neighborhood=neighborhood_for(defn),
            param_count=1,
        )
        # Seal experiment (metrics only; not claiming historical equity reproduce on AU/RB seed)
        rec = build_experiment_record(
            strategy_id=defn["strategy_id"],
            strategy_version="v1",
            strategy_definition_hash=spec.content_hash(),
            dataset_id=f"parquet:{defn['evidence_instrument']}_1d",
            dataset_version="v1",
            dataset_hash=str(trust.dataset_hash),
            time_governance=TimeGovernance(timezone="UTC"),
            execution_assumptions=ExecutionAssumptions(
                fee_rate=0.0005,
                slippage_bps=1.0,
                notes="historical FactorLab cost_config default",
            ),
            engine_name="quantlab_factor_lab_sign",
            engine_version="1.0.0",
            adapter_version="qln6_phase_a_v1",
            random_seed=0,
            config={
                "template_type": defn["template_type"],
                "params": defn["params"],
                "execution_rule": "sign(signal)",
                "evidence_instrument": defn["evidence_instrument"],
                "historical_symbols": defn["historical_symbols"],
            },
            metrics={
                "decision": report.decision,
                "reality_score": report.reality_score.get("score"),
                "research_debt": report.research_debt.get("score"),
                **{f"gate_{k}": v for k, v in report.gates.items()},
            },
            artifact_hashes={"spec": spec.content_hash(), "dataset": str(trust.dataset_hash)},
            data_trust_status="PASS",
            data_trust=trust.to_dict(),
            cost_attribution=CostAttribution(notes="phase_a reconstruction evidence"),
            evidence_stage="E1_BACKTEST",
            notes="Historical semantics recovered; evidence on genuine parquet (not AU/RB seed)",
        )
        ledger.append(rec)

        # Higher evidence: OOS and WF not FAIL, decision not KILL-only from hard fail,
        # and at least one of OOS/WF PASS (E2/E3-ish), on genuine data.
        gates = report.gates
        higher = (
            trust.status == "PASS"
            and gates.get("oos") != "FAIL"
            and gates.get("walk_forward") != "FAIL"
            and gates.get("backtest") == "PASS"
            and (
                gates.get("oos") == "PASS"
                or gates.get("walk_forward") == "PASS"
            )
        )
        rows.append(
            EvalRow(
                strategy_id=defn["strategy_id"],
                decision=report.decision,
                reality_score=float(report.reality_score.get("score") or 0),
                research_debt=float(report.research_debt.get("score") or 0),
                gates=dict(gates),
                reasons=list(report.reasons),
                data_trust=trust.status,
                higher_evidence=higher,
            )
        )

    summary = {
        "HISTORICAL_BACKTESTS_INSPECTED": inspected,
        "DISTINCT_DEFINITIONS_RECOVERED": len(SEED_DEFINITIONS),
        "GENUINE_HISTORICAL_STRATEGIES_RECOVERED": len(SEED_DEFINITIONS),
        "packages": packages,
        "evaluations": [asdict(r) for r in rows],
        "PROMOTE": sum(1 for r in rows if r.decision == "PROMOTE"),
        "HOLD": sum(1 for r in rows if r.decision == "HOLD"),
        "KILL": sum(1 for r in rows if r.decision == "KILL"),
        "HIGHER_EVIDENCE_STRATEGY_COUNT": sum(1 for r in rows if r.higher_evidence),
        "STRATEGIES_FULLY_EVALUATED": len(rows),
        "NO_EDGE_FOUND": sum(1 for r in rows if r.decision == "KILL"),
    }
    RESULTS_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(run_phase_a(), indent=2, ensure_ascii=False))
