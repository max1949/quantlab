"""因子扫描 API schema。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from backend.app.schemas.task import AcademyRewardOut


class FactorScanRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    symbols: list[str] | None = Field(default=None, max_length=3)
    template_type: str = Field(default="momentum", min_length=1, max_length=64)
    timeframe: str = Field(default="1d", max_length=16)
    project_id: uuid.UUID | None = None
    steps: int = Field(default=8, ge=4, le=12)
    search_mode: str = Field(default="grid", pattern=r"^(grid|random)$")
    factor_ids: list[uuid.UUID] | None = Field(default=None, max_length=2)

    @model_validator(mode="after")
    def validate_scan_target(self) -> FactorScanRequest:
        if self.factor_ids is not None:
            if len(self.factor_ids) != 2:
                raise ValueError("组合权重扫描需要恰好 2 个因子")
            if self.symbols:
                raise ValueError("组合权重扫描暂不支持跨标的")
        return self


class ScanResultRow(BaseModel):
    rank: int
    params: dict
    label: str
    score: float | None = None
    sharpe: float | None = None
    oos_sharpe: float | None = None
    ic_mean: float | None = None
    turnover: float | None = None
    max_drawdown: float | None = None
    publish_promising: bool = False
    publish_hints: list[str] = Field(default_factory=list)
    symbol_breakdown: dict | None = None


class FactorScanOut(BaseModel):
    id: uuid.UUID
    symbol: str
    timeframe: str
    template_type: str
    project_id: uuid.UUID | None
    project_title: str | None = None
    results: list[ScanResultRow]
    best_params: dict | None
    best_score: float | None
    coach_summary: str
    applied_factor_id: uuid.UUID | None
    created_at: datetime
    academy_rewards: list[AcademyRewardOut] = Field(default_factory=list)


class FactorScanCompareOut(BaseModel):
    scan_a: FactorScanOut
    scan_b: FactorScanOut
    delta: dict[str, float | None]
    winner: str
    summary: str


class ApplyScanRequest(BaseModel):
    rank: int = Field(default=1, ge=1, le=50)
    name: str | None = Field(default=None, max_length=120)
