"""Phase 6 PaperRun domain models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.core.database import Base


class PaperRunStatus(str, enum.Enum):
    CREATED = "CREATED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    KILLED = "KILLED"


class PaperRun(Base):
    __tablename__ = "paper_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    strategy_spec_id: Mapped[str] = mapped_column(String(120), nullable=False)
    strategy_spec_version: Mapped[str] = mapped_column(String(32), nullable=False)
    compiled_strategy_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    strategy_spec_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    environment: Mapped[str] = mapped_column(String(16), nullable=False, default="SANDBOX")
    instrument: Mapped[str] = mapped_column(String(32), nullable=False, default="BTCUSDT")
    venue: Mapped[str] = mapped_column(String(32), nullable=False, default="BINANCE")
    data_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="synthetic")

    starting_balance: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=100_000)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USDT")
    simulated_balance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    risk_policy_id: Mapped[str] = mapped_column(String(64), nullable=False, default="default_paper_v1")
    risk_policy_version: Mapped[str] = mapped_column(String(16), nullable=False, default="v1")
    risk_policy_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    status: Mapped[str] = mapped_column(String(16), nullable=False, default=PaperRunStatus.CREATED.value)
    data_gate_status: Mapped[str] = mapped_column(String(8), nullable=False, default="")
    last_market_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    market_data_age_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    realized_pnl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    current_balance: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=100_000)

    position_side: Mapped[str | None] = mapped_column(String(8), nullable=True)
    position_qty: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)

    engine: Mapped[str] = mapped_column(String(32), nullable=False, default="NAUTILUS_SANDBOX")
    engine_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.231.0")
    run_manifest_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    run_manifest: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    effective_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    runner_pid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    restart_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kill_switch_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    global_kill_switch: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    strategy_kill_switch: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    risk_paused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_stale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stop_reason: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    failure_reason: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    alerts: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PaperRunOrder(Base):
    __tablename__ = "paper_run_orders"
    __table_args__ = (
        UniqueConstraint("paper_run_id", "client_order_id", name="uq_paper_run_client_order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    paper_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("paper_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    client_order_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    instrument: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    price: Mapped[float | None] = mapped_column(Numeric(18, 8), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OrderInitialized")
    lifecycle_events: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    signal_reason: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PaperRunFill(Base):
    __tablename__ = "paper_run_fills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    paper_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("paper_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("paper_run_orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    instrument: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    fee: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    filled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PaperRunPosition(Base):
    __tablename__ = "paper_run_positions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    paper_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("paper_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    instrument: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    avg_price: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SignalDecisionRecord(Base):
    __tablename__ = "paper_signal_decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    paper_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("paper_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    instrument: Mapped[str] = mapped_column(String(32), nullable=False)
    decision: Mapped[str] = mapped_column(String(8), nullable=False)
    reason: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    conditions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    condition_values: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PaperRunEvent(Base):
    __tablename__ = "paper_run_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    paper_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("paper_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    message_zh: Mapped[str] = mapped_column(Text, nullable=False, default="")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PaperReadyRegistry(Base):
    """Bind PAPER_READY to a specific strategy spec version + hash."""

    __tablename__ = "paper_ready_registry"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "strategy_spec_id",
            "strategy_spec_version",
            "strategy_spec_hash",
            name="uq_paper_ready_user_spec_version_hash",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    strategy_spec_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    strategy_spec_version: Mapped[str] = mapped_column(String(32), nullable=False)
    strategy_spec_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    compiled_strategy_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    gates: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
