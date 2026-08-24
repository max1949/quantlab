"""REALTIME_DATA_GATE for paper sandbox."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from engine.paper.realtime_data_policy import RealtimeDataPolicy

GateStatus = Literal["PASS", "WARN", "FAIL"]


@dataclass
class RealtimeDataGateResult:
    status: GateStatus
    last_event_timestamp: str | None = None
    receive_timestamp: str | None = None
    event_age_seconds: float | None = None
    stream_gap_seconds: float | None = None
    duplicate_events: int = 0
    sequence_anomalies: int = 0
    instrument_loaded: bool = False
    quote_or_trade_stream_active: bool = False
    clock_sane: bool = True
    data_fresh: bool = False
    detail_zh: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_realtime_data_gate(
    *,
    last_event_ts: datetime | None,
    receive_ts: datetime | None = None,
    instrument_loaded: bool = False,
    stream_active: bool = False,
    duplicate_events: int = 0,
    sequence_anomalies: int = 0,
    policy: RealtimeDataPolicy | None = None,
    now: datetime | None = None,
) -> RealtimeDataGateResult:
    pol = policy or RealtimeDataPolicy()
    now = now or datetime.now(timezone.utc)
    recv = receive_ts or now
    detail: list[str] = []

    if not instrument_loaded:
        detail.append("合约元数据未加载")
    if not stream_active:
        detail.append("行情流未激活")

    event_age = None
    if last_event_ts is not None:
        event_age = max(0.0, (recv - last_event_ts).total_seconds())
        if pol.is_stale(event_age):
            detail.append(f"行情过期 {event_age:.1f}s > {pol.max_event_age_seconds}s")
        elif pol.is_warn(event_age):
            detail.append(f"行情偏旧 {event_age:.1f}s")

    if duplicate_events:
        detail.append(f"重复事件 {duplicate_events}")
    if sequence_anomalies:
        detail.append(f"序列异常 {sequence_anomalies}")

    clock_sane = last_event_ts is None or last_event_ts <= recv
    if not clock_sane:
        detail.append("时钟异常：事件时间晚于接收时间")

    data_fresh = (
        instrument_loaded
        and stream_active
        and last_event_ts is not None
        and event_age is not None
        and not pol.is_stale(event_age)
        and clock_sane
    )

    if not instrument_loaded or not stream_active or not clock_sane:
        status: GateStatus = "FAIL"
    elif not data_fresh:
        status = "WARN" if event_age and pol.is_warn(event_age) else "FAIL"
    elif event_age and pol.is_warn(event_age):
        status = "WARN"
    else:
        status = "PASS"

    return RealtimeDataGateResult(
        status=status,
        last_event_timestamp=last_event_ts.isoformat() if last_event_ts else None,
        receive_timestamp=recv.isoformat(),
        event_age_seconds=event_age,
        stream_gap_seconds=event_age,
        duplicate_events=duplicate_events,
        sequence_anomalies=sequence_anomalies,
        instrument_loaded=instrument_loaded,
        quote_or_trade_stream_active=stream_active,
        clock_sane=clock_sane,
        data_fresh=data_fresh,
        detail_zh=detail or ["实时数据门通过"],
    )
