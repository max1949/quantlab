"""PaperRun API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PaperReadyIn(BaseModel):
    spec: dict[str, Any]
    compiled_hash: str = ""
    data_gate_status: str = "PASS"
    backtest_pass: bool = True
    validation_pass: bool = True
    robustness_pass: bool = True


class PaperRunCreateIn(BaseModel):
    spec: dict[str, Any]
    compiled_hash: str = ""
    environment: str = Field(default="SANDBOX", pattern=r"^(BACKTEST|SANDBOX|PAPER|SHADOW)$")
    instrument: str = "BTCUSDT"
    data_provider: str = "synthetic"
    starting_balance: float = Field(default=100_000.0, gt=0)


class PaperRunOut(BaseModel):
    id: str
    strategy_spec_id: str
    strategy_spec_version: str
    environment: str
    instrument: str
    status: str
    simulated_balance: bool
    starting_balance: float
    current_balance: float
    realized_pnl: float
    data_gate_status: str = ""
    data_stale: bool = False
    run_manifest_hash: str = ""
    created_at: str | None = None
    started_at: str | None = None
    ended_at: str | None = None


class PaperDashboardOut(BaseModel):
    id: str
    title_zh: str
    disclaimer_zh: str
    strategy_name: str
    strategy_version: str
    status_zh: str
    uptime_zh: str
    simulated_balance_zh: str
    starting_balance_zh: str
    today_pnl_zh: str
    total_pnl_zh: str
    position_zh: str
    risk_zh: str
    data_connection_zh: str
    last_quote_zh: str
    alert_count: int
    environment: str
    instrument: str
    orders_count: int
    fills_count: int
    positions_count: int
    recent_signals: list[dict[str, Any]] = Field(default_factory=list)
    orders_zh: list[dict[str, str]] = Field(default_factory=list)
    fills_zh: list[dict[str, str]] = Field(default_factory=list)
    equity_zh: str = ""
    unrealized_pnl_zh: str = ""
    max_drawdown_zh: str = ""
    performance_summary: dict[str, Any] = Field(default_factory=dict)
    equity_curve: list[dict[str, Any]] = Field(default_factory=list)
    parity_status: str = ""
    research_feedback_zh: list[str] = Field(default_factory=list)
    data_provider: str = ""
    official_execution_path: str = "NAUTILUSTRADER"
    backtest_vs_paper_zh: list[str] = Field(default_factory=list)


class PaperAnalystIn(BaseModel):
    question: str = Field(max_length=500)


class PaperAnalystOut(BaseModel):
    answer_zh: str
    evidence: list[str] = Field(default_factory=list)


class BacktestPaperCompareOut(BaseModel):
    strategy_spec_id: str
    strategy_spec_version: str
    signal_frequency_backtest: float
    signal_frequency_paper: float
    entry_distribution_delta: dict[str, float] = Field(default_factory=dict)
    avg_holding_period_backtest: float = 0.0
    avg_holding_period_paper: float = 0.0
    slippage_paper: float = 0.0
    fill_delay_paper_ms: float = 0.0
    pnl_backtest: float = 0.0
    pnl_paper: float = 0.0
    win_rate_backtest: float = 0.0
    win_rate_paper: float = 0.0
    exposure_backtest: float = 0.0
    exposure_paper: float = 0.0
    orders_backtest: int = 0
    orders_paper: int = 0
    fills_paper: int = 0
    parity_status: str = "INVALID_COMPARISON"
    summary_zh: list[str] = Field(default_factory=list)
