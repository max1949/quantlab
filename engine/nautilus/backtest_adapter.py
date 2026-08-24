"""Nautilus backtest adapter — config/data/strategy stay behind this facade."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from engine.nautilus.availability import nautilus_available, nautilus_version
from engine.trading import BacktestRequest, BacktestResult, InstrumentRef

PINNED_VERSION = "1.231.0"
GOLDEN_STRATEGY_ID = "golden_01_ema_trend"
GOLDEN_STRATEGY_VERSION = "v1"


def build_golden_ohlcv(n: int = 400, seed: int = 42) -> pd.DataFrame:
    """Deterministic synthetic 15m OHLCV for golden regression."""
    idx = pd.date_range("2024-01-01", periods=n, freq="15min", tz="UTC")
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    price = 1.10 + 0.00005 * t + 0.001 * np.sin(t / 8) + rng.normal(0, 0.00005, size=n)
    df = pd.DataFrame(index=idx)
    df["open"] = np.array(price, dtype=np.float64, copy=True)
    df["high"] = np.array(price + 0.0002, dtype=np.float64, copy=True)
    df["low"] = np.array(price - 0.0002, dtype=np.float64, copy=True)
    df["close"] = np.array(price, dtype=np.float64, copy=True)
    df["volume"] = np.array(np.full(n, 1000.0), dtype=np.float64, copy=True)
    return df


class NautilusBacktestAdapter:
    """Thin facade: QuantLab BacktestRequest → Nautilus BacktestEngine → BacktestResult."""

    def __init__(self, *, require_pinned: bool = True) -> None:
        if not nautilus_available():
            raise RuntimeError(
                "nautilus_trader is not installed. Use .venv-nautilus or "
                "backend/requirements-nautilus.txt (pinned)."
            )
        ver = nautilus_version()
        if require_pinned and ver != PINNED_VERSION:
            raise RuntimeError(
                f"NAUTILUS_VERSION_PINNED expected {PINNED_VERSION}, got {ver}"
            )
        self.engine_version = ver or "unknown"

    def run_compiled_ema(
        self,
        compiled_params: dict[str, Any],
        ohlcv: pd.DataFrame | None = None,
        *,
        strategy_id: str,
        strategy_version: str,
        persist_dir: str | Path | None = None,
    ) -> BacktestResult:
        """Run EMA path from compiler output params (multi-instrument)."""
        from engine.data.dataset_resolver import build_btc_golden_ohlcv, resolve_dataset

        instrument = str(compiled_params.get("instrument") or "EUR/USD")
        if ohlcv is None:
            _ref, ohlcv = resolve_dataset(instrument)
            if ohlcv is None:
                ohlcv = (
                    build_golden_ohlcv()
                    if "EUR" in instrument.upper()
                    else build_btc_golden_ohlcv()
                )
        return self.run_ema_for_instrument(
            instrument=instrument,
            ohlcv=ohlcv,
            fast_ema=int(compiled_params.get("fast_ema", 10)),
            slow_ema=int(compiled_params.get("slow_ema", 20)),
            trade_size=str(compiled_params.get("trade_size", "1000000")),
            persist_dir=persist_dir,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
        )

    def run_ema_golden(
        self,
        ohlcv: pd.DataFrame | None = None,
        *,
        fast_ema: int = 10,
        slow_ema: int = 20,
        trade_size: str = "1000000",
        persist_dir: str | Path | None = None,
        strategy_id: str = GOLDEN_STRATEGY_ID,
        strategy_version: str = GOLDEN_STRATEGY_VERSION,
    ) -> BacktestResult:
        """Golden strategy 01: EMA trend (official EMACross example strategy)."""
        from nautilus_trader.backtest.config import BacktestEngineConfig
        from nautilus_trader.backtest.engine import BacktestEngine
        from nautilus_trader.config import LoggingConfig
        from nautilus_trader.examples.strategies.ema_cross import EMACross, EMACrossConfig
        from nautilus_trader.model import BarType, Money, Venue
        from nautilus_trader.model.enums import AccountType, OmsType
        from nautilus_trader.model.identifiers import TraderId
        from nautilus_trader.persistence.wranglers import BarDataWrangler
        from nautilus_trader.test_kit.providers import TestInstrumentProvider

        request = BacktestRequest(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            instrument=InstrumentRef(symbol="EUR/USD", venue="SIM", asset_class="FX"),
            parameters={"fast_ema": fast_ema, "slow_ema": slow_ema, "trade_size": trade_size},
        )
        df = ohlcv if ohlcv is not None else build_golden_ohlcv()
        instrument = TestInstrumentProvider.default_fx_ccy("EUR/USD")
        bar_type = BarType.from_str(f"{instrument.id}-15-MINUTE-LAST-EXTERNAL")
        bars = BarDataWrangler(bar_type, instrument).process(df)

        engine = BacktestEngine(
            config=BacktestEngineConfig(
                trader_id=TraderId("QL-GOLDEN-001"),
                logging=LoggingConfig(log_level="ERROR"),
            )
        )
        try:
            engine.add_venue(
                venue=Venue("SIM"),
                oms_type=OmsType.NETTING,
                account_type=AccountType.MARGIN,
                base_currency=instrument.quote_currency,
                starting_balances=[Money(1_000_000, instrument.quote_currency)],
            )
            engine.add_instrument(instrument)
            engine.add_data(bars)
            engine.add_strategy(
                EMACross(
                    config=EMACrossConfig(
                        instrument_id=instrument.id,
                        bar_type=bar_type,
                        trade_size=Decimal(trade_size),
                        fast_ema_period=fast_ema,
                        slow_ema_period=slow_ema,
                    )
                )
            )
            engine.run()
            fills = engine.trader.generate_order_fills_report()
            positions = engine.trader.generate_positions_report()
            fill_count = 0 if fills is None else int(len(fills))
            position_count = 0 if positions is None else int(len(positions))
            metrics = {
                "bar_count": len(bars),
                "fill_count": fill_count,
                "position_count": position_count,
                "fast_ema": fast_ema,
                "slow_ema": slow_ema,
            }
            result = BacktestResult(
                engine="NAUTILUS",
                engine_version=self.engine_version,
                strategy_id=request.strategy_id,
                strategy_version=request.strategy_version,
                status="success",
                fill_count=fill_count,
                position_count=position_count,
                metrics=metrics,
                artifacts={
                    "instrument_id": str(instrument.id),
                    "bar_type": str(bar_type),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception as exc:  # noqa: BLE001 — surface as structured result
            result = BacktestResult(
                engine="NAUTILUS",
                engine_version=self.engine_version,
                strategy_id=request.strategy_id,
                strategy_version=request.strategy_version,
                status="failed",
                fill_count=0,
                position_count=0,
                error=str(exc),
            )
        finally:
            engine.dispose()

        if persist_dir is not None and result.status == "success":
            self.persist_result(result, persist_dir)
        return result

    def run_ema_for_instrument(
        self,
        *,
        instrument: str,
        ohlcv: pd.DataFrame,
        fast_ema: int = 10,
        slow_ema: int = 20,
        trade_size: str = "1000000",
        strategy_id: str = GOLDEN_STRATEGY_ID,
        strategy_version: str = GOLDEN_STRATEGY_VERSION,
        persist_dir: str | Path | None = None,
    ) -> BacktestResult:
        """Multi-instrument EMA path (EUR/USD + BTCUSDT golden)."""
        from nautilus_trader.backtest.config import BacktestEngineConfig
        from nautilus_trader.backtest.engine import BacktestEngine
        from nautilus_trader.config import LoggingConfig
        from nautilus_trader.examples.strategies.ema_cross import EMACross, EMACrossConfig
        from nautilus_trader.model import BarType, Money, Venue
        from nautilus_trader.model.enums import AccountType, OmsType
        from nautilus_trader.model.identifiers import TraderId
        from nautilus_trader.persistence.wranglers import BarDataWrangler
        from nautilus_trader.test_kit.providers import TestInstrumentProvider

        inst_key = instrument.upper().replace(" ", "")
        if inst_key in {"EUR/USD", "EURUSD"}:
            nt_instrument = TestInstrumentProvider.default_fx_ccy("EUR/USD")
            venue = Venue("SIM")
            account_type = AccountType.MARGIN
            balance = Money(1_000_000, nt_instrument.quote_currency)
            size = trade_size
            asset_class = "FX"
        elif inst_key in {"BTCUSDT", "BTC/USDT"}:
            nt_instrument = TestInstrumentProvider.btcusdt_binance()
            venue = Venue("BINANCE")
            account_type = AccountType.MARGIN
            balance = Money(1_000_000, nt_instrument.quote_currency)
            size = "0.1" if trade_size == "1000000" else trade_size
            asset_class = "CRYPTO"
        else:
            return BacktestResult(
                engine="NAUTILUS",
                engine_version=self.engine_version,
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                status="failed",
                fill_count=0,
                position_count=0,
                error=f"unsupported_instrument:{instrument}",
            )

        request = BacktestRequest(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            instrument=InstrumentRef(symbol=str(nt_instrument.id), venue=str(venue), asset_class=asset_class),
            parameters={"fast_ema": fast_ema, "slow_ema": slow_ema, "trade_size": size},
        )
        bar_type = BarType.from_str(f"{nt_instrument.id}-15-MINUTE-LAST-EXTERNAL")
        bars = BarDataWrangler(bar_type, nt_instrument).process(ohlcv)
        engine = BacktestEngine(
            config=BacktestEngineConfig(
                trader_id=TraderId("QL-MULTI-001"),
                logging=LoggingConfig(log_level="ERROR"),
            )
        )
        try:
            engine.add_venue(
                venue=venue,
                oms_type=OmsType.NETTING,
                account_type=account_type,
                base_currency=nt_instrument.quote_currency,
                starting_balances=[balance],
            )
            engine.add_instrument(nt_instrument)
            engine.add_data(bars)
            engine.add_strategy(
                EMACross(
                    config=EMACrossConfig(
                        instrument_id=nt_instrument.id,
                        bar_type=bar_type,
                        trade_size=Decimal(size),
                        fast_ema_period=fast_ema,
                        slow_ema_period=slow_ema,
                    )
                )
            )
            engine.run()
            fills = engine.trader.generate_order_fills_report()
            positions = engine.trader.generate_positions_report()
            fill_count = 0 if fills is None else int(len(fills))
            position_count = 0 if positions is None else int(len(positions))
            result = BacktestResult(
                engine="NAUTILUS",
                engine_version=self.engine_version,
                strategy_id=request.strategy_id,
                strategy_version=request.strategy_version,
                status="success",
                fill_count=fill_count,
                position_count=position_count,
                metrics={
                    "bar_count": len(bars),
                    "fill_count": fill_count,
                    "position_count": position_count,
                    "fast_ema": fast_ema,
                    "slow_ema": slow_ema,
                    "instrument": str(nt_instrument.id),
                },
                artifacts={
                    "instrument_id": str(nt_instrument.id),
                    "bar_type": str(bar_type),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            result = BacktestResult(
                engine="NAUTILUS",
                engine_version=self.engine_version,
                strategy_id=request.strategy_id,
                strategy_version=request.strategy_version,
                status="failed",
                fill_count=0,
                position_count=0,
                error=str(exc),
            )
        finally:
            engine.dispose()

        if persist_dir is not None and result.status == "success":
            self.persist_result(result, persist_dir)
        return result

    @staticmethod
    def persist_result(result: BacktestResult, persist_dir: str | Path) -> Path:
        out = Path(persist_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{result.strategy_id}_{result.strategy_version}.json"
        path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def run_request(self, request: BacktestRequest, **kwargs: Any) -> BacktestResult:
        """Dispatch known golden strategies; expand in later phases."""
        if request.strategy_id == GOLDEN_STRATEGY_ID:
            return self.run_ema_golden(
                fast_ema=int(request.parameters.get("fast_ema", 10)),
                slow_ema=int(request.parameters.get("slow_ema", 20)),
                trade_size=str(request.parameters.get("trade_size", "1000000")),
                **kwargs,
            )
        raise ValueError(f"Unsupported strategy_id for Phase 1: {request.strategy_id}")
