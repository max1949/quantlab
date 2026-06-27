"""因子实验室出入参 schema (Sprint 3)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---- 模板目录 ----
class ParamSpecOut(BaseModel):
    name: str
    default: int
    min: int
    max: int
    label: str


class FactorTemplateOut(BaseModel):
    code: str
    label: str
    description: str
    params: list[ParamSpecOut]
    requires: list[str]


# ---- 创建 ----
class TemplateFactorCreate(BaseModel):
    """创建模板因子 (L0+)。"""

    name: str = Field(min_length=1, max_length=120)
    template_type: str
    params: dict[str, int] = Field(default_factory=dict)


class StackComponent(BaseModel):
    factor_id: uuid.UUID
    weight: float


class StackFactorCreate(BaseModel):
    """创建因子组合器 (需 L1)。"""

    name: str = Field(min_length=1, max_length=120)
    components: list[StackComponent] = Field(min_length=1)


# ---- 出参 ----
class FactorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
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
