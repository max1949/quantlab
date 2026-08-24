"""Synthetic LiveMarketDataClient for offline / CI paper runs."""

from __future__ import annotations

import asyncio

from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.live.data_client import LiveMarketDataClient
from nautilus_trader.live.factories import LiveDataClientFactory
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.test_kit.providers import TestInstrumentProvider


class SyntheticDataClientConfig(LiveDataClientConfig, frozen=True, kw_only=True):
    instrument_id: str = "BTCUSDT.BINANCE"
    ticks: int = 80
    base_price: float = 60_000.0
    interval_ms: int = 50


class SyntheticLiveDataClient(LiveMarketDataClient):
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        client_id: ClientId,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
        config: SyntheticDataClientConfig,
    ) -> None:
        super().__init__(
            loop=loop,
            client_id=client_id,
            venue=Venue("BINANCE"),
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=InstrumentProvider(),
            config=config,
        )
        self._cfg = config
        self._instrument = TestInstrumentProvider.btcusdt_binance()
        self._feed_task: asyncio.Task | None = None
        self._bar_type = BarType.from_str(f"{self._instrument.id}-1-MINUTE-LAST-EXTERNAL")

    async def _connect(self) -> None:
        self._cache.add_instrument(self._instrument)
        self._feed_task = self.create_task(self._stream(), log_msg="synthetic_stream")


    async def _disconnect(self) -> None:
        if self._feed_task is not None and not self._feed_task.done():
            self._feed_task.cancel()
            try:
                await self._feed_task
            except asyncio.CancelledError:
                pass

    async def _stream(self) -> None:
        """Emit ticks + 1 bar/tick. Price path: downtrend then sharp uptrend → EMA cross."""
        price = float(self._cfg.base_price)
        n = int(self._cfg.ticks)
        for i in range(n):
            # First half drifts down; second half ramps up hard enough for fast/slow EMA cross.
            if i < n // 2:
                price = price * 0.9985
            else:
                price = price * 1.004
            ts = self._clock.timestamp_ns()
            # BTCUSDT.BINANCE: price_precision=2, size_precision=6
            tick = TradeTick(
                instrument_id=self._instrument.id,
                price=Price.from_str(f"{price:.2f}"),
                size=Quantity.from_str("0.010000"),
                aggressor_side=AggressorSide.BUYER if i % 2 == 0 else AggressorSide.SELLER,
                trade_id=TradeId(str(i + 1)),
                ts_event=ts,
                ts_init=ts,
            )
            self._handle_data(tick)
            bar = Bar(
                bar_type=self._bar_type,
                open=Price.from_str(f"{price * 0.999:.2f}"),
                high=Price.from_str(f"{price * 1.001:.2f}"),
                low=Price.from_str(f"{price * 0.998:.2f}"),
                close=Price.from_str(f"{price:.2f}"),
                volume=Quantity.from_str("1.000000"),
                ts_event=ts,
                ts_init=ts,
            )
            self._handle_data(bar)
            await asyncio.sleep(max(int(self._cfg.interval_ms), 1) / 1000.0)

    async def _subscribe_trade_ticks(self, command) -> None:  # noqa: ANN001
        return None

    async def _unsubscribe_trade_ticks(self, command) -> None:  # noqa: ANN001
        return None

    async def _subscribe_bars(self, command) -> None:  # noqa: ANN001
        return None

    async def _unsubscribe_bars(self, command) -> None:  # noqa: ANN001
        return None

    async def _subscribe_quote_ticks(self, command) -> None:  # noqa: ANN001
        return None

    async def _unsubscribe_quote_ticks(self, command) -> None:  # noqa: ANN001
        return None

    async def _subscribe_order_book_deltas(self, command) -> None:  # noqa: ANN001
        return None

    async def _unsubscribe_order_book_deltas(self, command) -> None:  # noqa: ANN001
        return None

    async def _subscribe_instrument(self, command) -> None:  # noqa: ANN001
        return None

    async def _unsubscribe_instrument(self, command) -> None:  # noqa: ANN001
        return None

    async def _subscribe_instruments(self, command) -> None:  # noqa: ANN001
        return None

    async def _unsubscribe_instruments(self, command) -> None:  # noqa: ANN001
        return None


class SyntheticLiveDataClientFactory(LiveDataClientFactory):
    @staticmethod
    def create(  # type: ignore[override]
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: SyntheticDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> SyntheticLiveDataClient:
        return SyntheticLiveDataClient(
            loop=loop,
            client_id=ClientId(name),
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=config,
        )
