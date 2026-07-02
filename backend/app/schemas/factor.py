"""因子实验室出入参 schema (Sprint 3)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---- 模板目录 ----
class ParamHelpOut(BaseModel):
    tip: str
    low_hint: str = ""
    high_hint: str = ""
    suggested: str = ""


class ParamSpecOut(BaseModel):
    name: str
    default: int
    min: int
    max: int
    label: str
    help: ParamHelpOut | None = None


class FactorTemplateOut(BaseModel):
    code: str
    label: str
    description: str
    how_it_works: str = ""
    params: list[ParamSpecOut]
    requires: list[str]
    min_level: int = 0
    min_tier: int = 0
    allowed: bool = True


# ---- 创建 ----
class TemplateFactorCreate(BaseModel):
    """创建模板因子 (L0+)。"""

    name: str = Field(min_length=1, max_length=120)
    template_type: str
    params: dict[str, int] = Field(default_factory=dict)
    project_id: uuid.UUID | None = None  # 可选: 归入某研究项目


class TemplateEvaluateRequest(BaseModel):
    """模板因子快评 (不创建因子)。"""

    template_type: str = Field(min_length=1, max_length=64)
    params: dict[str, int] = Field(default_factory=dict)
    symbol: str = Field(min_length=1, max_length=32)
    timeframe: str = Field(default="1d", max_length=16)


class TemplateEvaluateOut(BaseModel):
    template_type: str
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
    coach_summary: str = ""


class StackComponent(BaseModel):
    factor_id: uuid.UUID
    weight: float


class StackFactorCreate(BaseModel):
    """创建因子组合器 (需 L1)。"""

    name: str = Field(min_length=1, max_length=120)
    components: list[StackComponent] = Field(min_length=1)
    project_id: uuid.UUID | None = None  # 可选: 归入某研究项目


class FormulaFactorCreate(BaseModel):
    """创建公式因子 (L2 + 研究员会员)。"""

    name: str = Field(min_length=1, max_length=120)
    expr: str = Field(min_length=1, max_length=500)
    project_id: uuid.UUID | None = None


class FormulaEvaluateRequest(BaseModel):
    """公式因子快评 (不创建因子)。"""

    expr: str = Field(min_length=1, max_length=500)
    symbol: str = Field(min_length=1, max_length=32)
    timeframe: str = Field(default="1d", max_length=16)


class FormulaEvaluateOut(BaseModel):
    expr: str
    score: float | None = None
    sharpe: float | None = None
    oos_sharpe: float | None = None
    ic_mean: float | None = None
    turnover: float | None = None
    max_drawdown: float | None = None
    publish_promising: bool = False
    publish_hints: list[str] = Field(default_factory=list)
    coach_summary: str = ""


class PythonFactorCreate(BaseModel):
    """创建 Python 因子 (L3 + 研究员会员)。"""

    name: str = Field(min_length=1, max_length=120)
    source: str = Field(min_length=1, max_length=8000)
    project_id: uuid.UUID | None = None


class PythonEvaluateRequest(BaseModel):
    """Python 因子快评 (不创建因子)。"""

    source: str = Field(min_length=1, max_length=8000)
    symbol: str = Field(min_length=1, max_length=32)
    timeframe: str = Field(default="1d", max_length=16)


class PythonEvaluateOut(BaseModel):
    source: str
    score: float | None = None
    sharpe: float | None = None
    oos_sharpe: float | None = None
    ic_mean: float | None = None
    turnover: float | None = None
    max_drawdown: float | None = None
    publish_promising: bool = False
    publish_hints: list[str] = Field(default_factory=list)
    coach_summary: str = ""


class PythonFactorHelpOut(BaseModel):
    template: str
    variables: list[str]
    notes: list[str]


class PaperSnapshotOut(BaseModel):
    as_of_date: str
    symbol: str
    timeframe: str
    bars: int
    nav_end: float
    metrics: dict
    equity_tail: list


class PaperHistoryOut(BaseModel):
    factor_id: str
    snapshots: list[PaperSnapshotOut]
    latest_preview: dict | None = None
    decay: dict | None = None


class FormulaFnDoc(BaseModel):
    name: str
    desc: str


class FormulaHelpOut(BaseModel):
    variables: list[str]
    functions: list[FormulaFnDoc]
    examples: list[str]


# ---- 出参 ----
class FactorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    project_id: uuid.UUID | None
    name: str
    kind: str
    template_type: str | None
    spec: dict
    version: int
    created_at: datetime


class FactorPreview(BaseModel):
    """因子在样本数据上的预览统计 (真行情见 Sprint 4)。"""

    factor_id: uuid.UUID
    name: str
    kind: str
    sample_rows: int
    stats: dict
    academy_rewards: list = Field(default_factory=list)
