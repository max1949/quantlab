"""paper_runs domain tables for Phase 6 sandbox (complete).

Revision ID: 0032_paper_runs
Revises: 0031_org_research_alert_webhook
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0032_paper_runs"
down_revision: Union[str, None] = "0031_org_research_alert_webhook"
branch_labels: Union[tuple[str, ...], None] = None
depends_on: Union[tuple[str, ...], None] = None


def _ts_default():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return sa.text("now()")
    return sa.text("CURRENT_TIMESTAMP")


def _json_default(raw: str):
    return sa.text(f"'{raw}'")


def upgrade() -> None:
    ts = _ts_default()
    json_obj = _json_default("{}")
    json_arr = _json_default("[]")
    op.create_table(
        "paper_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("strategy_spec_id", sa.String(length=120), nullable=False),
        sa.Column("strategy_spec_version", sa.String(length=32), nullable=False),
        sa.Column("compiled_strategy_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("strategy_spec_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("environment", sa.String(length=16), nullable=False, server_default="SANDBOX"),
        sa.Column("instrument", sa.String(length=32), nullable=False, server_default="BTCUSDT"),
        sa.Column("venue", sa.String(length=32), nullable=False, server_default="BINANCE"),
        sa.Column("data_provider", sa.String(length=32), nullable=False, server_default="synthetic"),
        sa.Column("starting_balance", sa.Numeric(18, 4), nullable=False, server_default="100000"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USDT"),
        sa.Column("simulated_balance", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("risk_policy_id", sa.String(length=64), nullable=False, server_default="default_paper_v1"),
        sa.Column("risk_policy_version", sa.String(length=16), nullable=False, server_default="v1"),
        sa.Column("risk_policy_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="CREATED"),
        sa.Column("data_gate_status", sa.String(length=8), nullable=False, server_default=""),
        sa.Column("last_market_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("market_data_age_seconds", sa.Float(), nullable=True),
        sa.Column("realized_pnl", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("unrealized_pnl", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("current_balance", sa.Numeric(18, 4), nullable=False, server_default="100000"),
        sa.Column("position_side", sa.String(length=8), nullable=True),
        sa.Column("position_qty", sa.Numeric(18, 8), nullable=False, server_default="0"),
        sa.Column("engine", sa.String(length=32), nullable=False, server_default="NAUTILUS_SANDBOX"),
        sa.Column("engine_version", sa.String(length=16), nullable=False, server_default="1.231.0"),
        sa.Column("run_manifest_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("run_manifest", sa.JSON(), nullable=False, server_default=json_obj),
        sa.Column("effective_config", sa.JSON(), nullable=False, server_default=json_obj),
        sa.Column("runner_pid", sa.Integer(), nullable=True),
        sa.Column("restart_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("kill_switch_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("global_kill_switch", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("strategy_kill_switch", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("risk_paused", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("data_stale", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("stop_reason", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("failure_reason", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("metrics", sa.JSON(), nullable=False, server_default=json_obj),
        sa.Column("alerts", sa.JSON(), nullable=False, server_default=json_arr),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=ts, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=ts, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_runs_user_id", "paper_runs", ["user_id"])
    op.create_index("ix_paper_runs_status", "paper_runs", ["status"])
    op.create_index("ix_paper_runs_strategy_spec_id", "paper_runs", ["strategy_spec_id"])

    op.create_table(
        "paper_ready_registry",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("strategy_spec_id", sa.String(length=120), nullable=False),
        sa.Column("strategy_spec_version", sa.String(length=32), nullable=False),
        sa.Column("strategy_spec_hash", sa.String(length=64), nullable=False),
        sa.Column("compiled_strategy_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("gates", sa.JSON(), nullable=False, server_default=json_obj),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=ts, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "strategy_spec_id",
            "strategy_spec_version",
            "strategy_spec_hash",
            name="uq_paper_ready_user_spec_version_hash",
        ),
    )
    op.create_index("ix_paper_ready_registry_user_id", "paper_ready_registry", ["user_id"])
    op.create_index("ix_paper_ready_registry_strategy_spec_id", "paper_ready_registry", ["strategy_spec_id"])

    op.create_table(
        "paper_run_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paper_run_id", sa.Uuid(), nullable=False),
        sa.Column("client_order_id", sa.String(length=64), nullable=False),
        sa.Column("instrument", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 8), nullable=False),
        sa.Column("price", sa.Numeric(18, 8), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OrderInitialized"),
        sa.Column("lifecycle_events", sa.JSON(), nullable=False, server_default=json_arr),
        sa.Column("signal_reason", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=ts, nullable=False),
        sa.ForeignKeyConstraint(["paper_run_id"], ["paper_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("paper_run_id", "client_order_id", name="uq_paper_run_client_order_id"),
    )
    op.create_index("ix_paper_run_orders_paper_run_id", "paper_run_orders", ["paper_run_id"])
    op.create_index("ix_paper_run_orders_client_order_id", "paper_run_orders", ["client_order_id"])

    op.create_table(
        "paper_run_fills",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paper_run_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("instrument", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 8), nullable=False),
        sa.Column("price", sa.Numeric(18, 8), nullable=False),
        sa.Column("fee", sa.Numeric(18, 8), nullable=False, server_default="0"),
        sa.Column("simulated", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("filled_at", sa.DateTime(timezone=True), server_default=ts, nullable=False),
        sa.ForeignKeyConstraint(["paper_run_id"], ["paper_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["paper_run_orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_run_fills_paper_run_id", "paper_run_fills", ["paper_run_id"])
    op.create_index("ix_paper_run_fills_order_id", "paper_run_fills", ["order_id"])

    op.create_table(
        "paper_run_positions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paper_run_id", sa.Uuid(), nullable=False),
        sa.Column("instrument", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 8), nullable=False, server_default="0"),
        sa.Column("avg_price", sa.Numeric(18, 8), nullable=False, server_default="0"),
        sa.Column("unrealized_pnl", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=ts, nullable=False),
        sa.ForeignKeyConstraint(["paper_run_id"], ["paper_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_run_positions_paper_run_id", "paper_run_positions", ["paper_run_id"])
    op.create_index("ix_paper_run_positions_open", "paper_run_positions", ["paper_run_id", "is_open"])

    op.create_table(
        "paper_signal_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paper_run_id", sa.Uuid(), nullable=False),
        sa.Column("strategy_version", sa.String(length=32), nullable=False),
        sa.Column("instrument", sa.String(length=32), nullable=False),
        sa.Column("decision", sa.String(length=8), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("conditions", sa.JSON(), nullable=False, server_default=json_arr),
        sa.Column("condition_values", sa.JSON(), nullable=False, server_default=json_obj),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=ts, nullable=False),
        sa.ForeignKeyConstraint(["paper_run_id"], ["paper_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_signal_decisions_paper_run_id", "paper_signal_decisions", ["paper_run_id"])
    op.create_index("ix_paper_signal_decisions_decided_at", "paper_signal_decisions", ["decided_at"])

    op.create_table(
        "paper_run_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("paper_run_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("message_zh", sa.Text(), nullable=False, server_default=""),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=json_obj),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=ts, nullable=False),
        sa.ForeignKeyConstraint(["paper_run_id"], ["paper_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_run_events_paper_run_id", "paper_run_events", ["paper_run_id"])
    op.create_index("ix_paper_run_events_code", "paper_run_events", ["code"])


def downgrade() -> None:
    op.drop_index("ix_paper_run_events_code", table_name="paper_run_events")
    op.drop_index("ix_paper_run_events_paper_run_id", table_name="paper_run_events")
    op.drop_table("paper_run_events")

    op.drop_index("ix_paper_signal_decisions_decided_at", table_name="paper_signal_decisions")
    op.drop_index("ix_paper_signal_decisions_paper_run_id", table_name="paper_signal_decisions")
    op.drop_table("paper_signal_decisions")

    op.drop_index("ix_paper_run_positions_open", table_name="paper_run_positions")
    op.drop_index("ix_paper_run_positions_paper_run_id", table_name="paper_run_positions")
    op.drop_table("paper_run_positions")

    op.drop_index("ix_paper_run_fills_order_id", table_name="paper_run_fills")
    op.drop_index("ix_paper_run_fills_paper_run_id", table_name="paper_run_fills")
    op.drop_table("paper_run_fills")

    op.drop_index("ix_paper_run_orders_client_order_id", table_name="paper_run_orders")
    op.drop_index("ix_paper_run_orders_paper_run_id", table_name="paper_run_orders")
    op.drop_table("paper_run_orders")

    op.drop_index("ix_paper_ready_registry_strategy_spec_id", table_name="paper_ready_registry")
    op.drop_index("ix_paper_ready_registry_user_id", table_name="paper_ready_registry")
    op.drop_table("paper_ready_registry")

    op.drop_index("ix_paper_runs_strategy_spec_id", table_name="paper_runs")
    op.drop_index("ix_paper_runs_status", table_name="paper_runs")
    op.drop_index("ix_paper_runs_user_id", table_name="paper_runs")
    op.drop_table("paper_runs")
