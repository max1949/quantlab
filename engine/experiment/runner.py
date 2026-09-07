"""Deterministic Golden EMA experiment runner (domain-level, Nautilus-independent).

Produces sealed ExperimentRecords for QLN-3 reproducibility Acceptance.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from engine.data.data_gate import DataProvenance
from engine.domain.hashing import HashKind, compute_hash
from engine.experiment.assumptions import CostAttribution, ExecutionAssumptions
from engine.experiment.data_trust import require_data_trust_pass, run_data_trust_gate
from engine.experiment.record import ExperimentRecord, build_experiment_record
from engine.experiment.time_governance import TimeGovernance
from engine.nautilus.backtest_adapter import build_golden_ohlcv

ENGINE_NAME = "quantlab_domain_ema"
ENGINE_VERSION = "1.0.0"
ADAPTER_VERSION = "experiment_runner_v1"
GOLDEN_DATASET_ID = "dst_golden_eurusd_15m_synth"
GOLDEN_STRATEGY_ID = "golden_01_ema_trend"
GOLDEN_STRATEGY_VERSION = "v1"


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak.replace(0, np.nan)
    return float(dd.min()) if len(dd) else 0.0


def run_domain_ema_backtest(
    ohlcv: pd.DataFrame,
    *,
    fast: int,
    slow: int,
    fee_rate: float,
    slippage_bps: float,
) -> dict[str, Any]:
    """Pure-Python EMA cross long/flat with turnover costs — deterministic."""
    close = ohlcv["close"].astype(float)
    fast_s = _ema(close, fast)
    slow_s = _ema(close, slow)
    signal = (fast_s > slow_s).astype(float)
    # Position from prior bar signal (no lookahead)
    position = signal.shift(1).fillna(0.0)
    ret = close.pct_change().fillna(0.0)
    turnover = position.diff().abs().fillna(position.abs())
    cost = turnover * (fee_rate + slippage_bps / 1e4)
    pnl = position * ret - cost
    equity = (1.0 + pnl).cumprod()
    trades = int((turnover > 0).sum())
    # Sharpe (bar-level, annualization omitted for determinism simplicity)
    mu = float(pnl.mean())
    sigma = float(pnl.std(ddof=0))
    sharpe = (mu / sigma) if sigma > 1e-15 else 0.0
    return {
        "total_return": float(equity.iloc[-1] - 1.0) if len(equity) else 0.0,
        "final_equity": float(equity.iloc[-1]) if len(equity) else 1.0,
        "max_drawdown": abs(_max_drawdown(equity)),
        "trade_count": trades,
        "sharpe": sharpe,
        "bars": int(len(ohlcv)),
    }


def run_golden_ema_experiment(
    *,
    seed: int = 42,
    n_bars: int = 400,
    fast: int = 10,
    slow: int = 20,
    fee_rate: float = 0.0005,
    slippage_bps: float = 1.0,
    experiment_id: str | None = None,
) -> ExperimentRecord:
    """One-shot golden experiment: trust gate → run → seal record."""
    ohlcv = build_golden_ohlcv(n=n_bars, seed=seed)
    tg = TimeGovernance(timezone="UTC", require_tz_aware=True)
    trust = require_data_trust_pass(
        run_data_trust_gate(
            ohlcv,
            provenance=DataProvenance(
                provider="quantlab_synthetic",
                instrument="EUR/USD",
                symbol="EUR/USD",
                venue="SIM",
                timezone="UTC",
                frequency="15m",
                price_type="last",
            ),
            time_governance=tg,
            dataset_version="v1",
            timeframe="15m",
        )
    )

    metrics = run_domain_ema_backtest(
        ohlcv, fast=fast, slow=slow, fee_rate=fee_rate, slippage_bps=slippage_bps
    )
    config = {
        "fast_ema": fast,
        "slow_ema": slow,
        "n_bars": n_bars,
        "instrument": "EUR/USD",
        "timeframe": "15m",
        "seed": seed,
    }
    strategy_def = {
        "strategy_id": GOLDEN_STRATEGY_ID,
        "version": GOLDEN_STRATEGY_VERSION,
        "kind": "ema_cross",
        "params": {"fast": fast, "slow": slow},
    }
    strategy_hash = compute_hash(HashKind.STRATEGY_DEFINITION, strategy_def)
    metrics_hash = compute_hash(HashKind.ARTIFACT, metrics)
    assumptions = ExecutionAssumptions(
        fee_rate=fee_rate,
        slippage_bps=slippage_bps,
        fee_model="turnover_fee_rate",
        slippage_model="turnover_bps",
    )
    return build_experiment_record(
        experiment_id=experiment_id,
        strategy_id=GOLDEN_STRATEGY_ID,
        strategy_version=GOLDEN_STRATEGY_VERSION,
        strategy_definition_hash=strategy_hash,
        dataset_id=GOLDEN_DATASET_ID,
        dataset_version=trust.dataset_version,
        dataset_hash=str(trust.dataset_hash),
        time_governance=tg,
        execution_assumptions=assumptions,
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        adapter_version=ADAPTER_VERSION,
        random_seed=seed,
        config=config,
        metrics=metrics,
        artifact_hashes={"metrics": metrics_hash, "dataset": str(trust.dataset_hash)},
        data_trust_status=trust.status,
        data_trust=trust.to_dict(),
        cost_attribution=CostAttribution(
            compute_units=1.0,
            market_data_units=0.0,
            ai_tokens=0.0,
            estimated_cost=0.0,
            notes="synthetic golden; no external market data cost",
        ),
        notes="QLN-3 golden EMA domain experiment",
    )
