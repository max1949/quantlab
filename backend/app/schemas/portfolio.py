"""L4 组合优化 / 模拟实盘 schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PortfolioOptimizeCreate(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: ["RB", "AU", "IF"], min_length=2)
    method: str = Field(default="risk_parity")


class PortfolioOptimizeOut(BaseModel):
    symbols: list[str]
    method: str
    weights: dict[str, float | None]
    expected: dict
    asset_stats: dict


class PaperSimulateCreate(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: ["RB", "AU", "IF"], min_length=2)
    weights: dict[str, float]
    rebalance: str = "monthly"


class PaperSimulateOut(BaseModel):
    symbols: list[str]
    weights: dict[str, float]
    rebalance: str
    metrics: dict
    equity_curve: list
