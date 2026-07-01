"""因子实验室路由 (Sprint 3): 模板目录 / 创建模板因子 / 创建组合器 / 预览 / 列表 / 删除。

等级绑定权限: 组合器创建路由用 require_level(L1) 把关 (L0 模板 → L1 组合器)。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser, require_feature, require_level
from backend.app.core.database import get_db
from backend.app.core.locale import RequestLocale
from backend.app.models.user import User, UserLevel
from backend.app.schemas.factor import (
    FactorOut,
    FactorPreview,
    FactorTemplateOut,
    FormulaFactorCreate,
    FormulaHelpOut,
    StackFactorCreate,
    TemplateFactorCreate,
)
from backend.app.services import factor_service
from engine import formula as ff

router = APIRouter()


@router.get(
    "/templates",
    response_model=list[FactorTemplateOut],
    summary="模板因子目录 (L0 即可查看/使用)",
)
def list_templates(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    locale: RequestLocale,
) -> list[FactorTemplateOut]:
    from backend.app.services import membership_service as ms

    tier = ms.current_tier(db, current_user)
    return [
        FactorTemplateOut(**t)
        for t in factor_service.list_templates(tier=tier, level=current_user.level, locale=locale)
    ]


@router.get("", response_model=list[FactorOut], summary="我的因子列表")
def list_my_factors(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[FactorOut]:
    return [
        FactorOut.model_validate(f)
        for f in factor_service.list_factors(db, current_user.id)
    ]


@router.post(
    "/template",
    response_model=FactorOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建模板因子 (L0+)",
)
def create_template_factor(
    payload: TemplateFactorCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> FactorOut:
    try:
        factor = factor_service.create_template_factor(
            db, current_user, payload.name, payload.template_type, payload.params,
            project_id=payload.project_id,
        )
    except factor_service.FactorValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except factor_service.FactorNameTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="同名因子已存在"
        )
    return FactorOut.model_validate(factor)


@router.post(
    "/stack",
    response_model=FactorOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建因子组合器 (需 L1, 等级绑定权限)",
)
def create_stack_factor(
    payload: StackFactorCreate,
    # require_level(L1): 等级不足直接 403, 同时拿到当前用户
    current_user: Annotated[User, Depends(require_level(UserLevel.L1))],
    db: Annotated[Session, Depends(get_db)],
) -> FactorOut:
    try:
        factor = factor_service.create_stack_factor(
            db,
            current_user,
            payload.name,
            [c.model_dump() for c in payload.components],
            project_id=payload.project_id,
        )
    except factor_service.StackPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="组合器需要 L1 及以上"
        )
    except factor_service.FactorValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except factor_service.FactorNameTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="同名因子已存在"
        )
    return FactorOut.model_validate(factor)


@router.get(
    "/formula/help",
    response_model=FormulaHelpOut,
    summary="公式因子: 可用变量/函数/示例",
)
def formula_help() -> FormulaHelpOut:
    return FormulaHelpOut(
        variables=list(ff.ALLOWED_VARS),
        functions=[{"name": d["name"], "desc": d["desc"]} for d in ff.FUNC_DOCS],
        examples=[
            "(close - sma(close, 20)) / std(close, 20)",
            "rsi(close, 14) - 50",
            "mom(close, 20) * -1",
            "zscore(volume, 20)",
            "ema(close, 5) / ema(close, 20) - 1",
        ],
    )


@router.post(
    "/formula",
    response_model=FactorOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建公式因子 (需 L2 + 研究员会员)",
)
def create_formula_factor(
    payload: FormulaFactorCreate,
    # require_feature: 同时校验能力等级(L2)与付费档位(研究员卡)
    current_user: Annotated[User, Depends(require_feature("factor_formula"))],
    db: Annotated[Session, Depends(get_db)],
) -> FactorOut:
    try:
        factor = factor_service.create_formula_factor(
            db, current_user, payload.name, payload.expr, project_id=payload.project_id,
        )
    except factor_service.FactorValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    except factor_service.FactorNameTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="同名因子已存在"
        )
    return FactorOut.model_validate(factor)


@router.get("/{factor_id}", response_model=FactorOut, summary="因子详情")
def get_factor(
    factor_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> FactorOut:
    try:
        factor = factor_service.get_factor(
            db, current_user.id, uuid.UUID(factor_id)
        )
    except (factor_service.FactorNotFoundError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在"
        )
    return FactorOut.model_validate(factor)


@router.post(
    "/{factor_id}/preview",
    response_model=FactorPreview,
    summary="在样本行情上预览因子 (真行情 Sprint 4)",
)
def preview_factor(
    factor_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> FactorPreview:
    try:
        factor = factor_service.get_factor(
            db, current_user.id, uuid.UUID(factor_id)
        )
    except (factor_service.FactorNotFoundError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在"
        )
    try:
        result = factor_service.preview(db, current_user.id, factor)
    except factor_service.FactorValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return FactorPreview(**result)


@router.delete(
    "/{factor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除因子",
)
def delete_factor(
    factor_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        factor_service.delete_factor(
            db, current_user.id, uuid.UUID(factor_id)
        )
    except (factor_service.FactorNotFoundError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在"
        )
