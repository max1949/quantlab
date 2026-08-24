"""Prove Alembic 0032 defines complete paper_run schema (no ORM create_all required)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, MetaData, String, Table, create_engine, inspect
from sqlalchemy.types import Uuid


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "backend" / "migrations" / "versions" / "0032_paper_runs.py"

REQUIRED_TABLES = {
    "paper_runs",
    "paper_ready_registry",
    "paper_run_orders",
    "paper_run_fills",
    "paper_run_positions",
    "paper_signal_decisions",
    "paper_run_events",
}


def _load_migration():
    spec = importlib.util.spec_from_file_location("rev_0032_paper_runs", MIGRATION)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_alembic_0032_upgrade_downgrade_complete():
    engine = create_engine("sqlite://")
    # FK target stub
    meta = MetaData()
    Table("users", meta, Column("id", Uuid(), primary_key=True), Column("email", String(120)))
    meta.create_all(engine)

    mod = _load_migration()
    import alembic.op as alembic_op

    def _run_upgrade(conn):
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)
        for name in ("create_table", "create_index", "drop_table", "drop_index", "f", "get_bind"):
            if hasattr(op, name):
                setattr(alembic_op, name, getattr(op, name))
        mod.upgrade()

    def _run_downgrade(conn):
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)
        for name in ("create_table", "create_index", "drop_table", "drop_index", "f", "get_bind"):
            if hasattr(op, name):
                setattr(alembic_op, name, getattr(op, name))
        mod.downgrade()

    with engine.begin() as conn:
        _run_upgrade(conn)
        tables = set(inspect(conn).get_table_names())
        missing = REQUIRED_TABLES - tables
        assert not missing, f"0032 missing tables: {missing}"

        order_idx = {i["name"] for i in inspect(conn).get_indexes("paper_run_orders")}
        assert "ix_paper_run_orders_paper_run_id" in order_idx
        assert "ix_paper_run_orders_client_order_id" in order_idx

        _run_downgrade(conn)
        tables_after = set(inspect(conn).get_table_names())
        leftover = REQUIRED_TABLES & tables_after
        assert not leftover, f"0032 downgrade left tables: {leftover}"

        _run_upgrade(conn)
        tables_re = set(inspect(conn).get_table_names())
        missing_re = REQUIRED_TABLES - tables_re
        assert not missing_re, f"0032 re-upgrade missing tables: {missing_re}"


def test_orm_models_match_required_tables():
    from backend.app.models.paper_run import (
        PaperReadyRegistry,
        PaperRun,
        PaperRunEvent,
        PaperRunFill,
        PaperRunOrder,
        PaperRunPosition,
        SignalDecisionRecord,
    )

    names = {
        PaperRun.__tablename__,
        PaperReadyRegistry.__tablename__,
        PaperRunOrder.__tablename__,
        PaperRunFill.__tablename__,
        PaperRunPosition.__tablename__,
        SignalDecisionRecord.__tablename__,
        PaperRunEvent.__tablename__,
    }
    assert names == REQUIRED_TABLES
