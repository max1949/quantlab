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
    PaperHistoryOut,
    PythonFactorCreate,
    PythonFactorHelpOut,
    StackFactorCreate,
    TemplateFactorCreate,
)
from backend.app.schemas.factor_scan import (
    ApplyScanRequest,
    FactorScanCompareOut,
    FactorScanOut,
    FactorScanRequest,
)
from backend.app.services import factor_service
from backend.app.services import market_data_policy as mdp
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


@router.get(
    "/python/help",
    response_model=PythonFactorHelpOut,
    summary="Python 因子: 模板与约束",
)
def python_help() -> PythonFactorHelpOut:
    return PythonFactorHelpOut(
        template=(
            "def compute(ohlcv):\n"
            "    close = ohlcv[\"close\"]\n"
            "    return (close - close.rolling(20).mean()) / close.rolling(20).std()"
        ),
        variables=["open", "high", "low", "close", "volume", "open_interest"],
        notes=[
            "必须定义 compute(ohlcv) 并返回 pandas Series",
            "可使用 pd / np, 禁止 import 与文件/网络操作",
            "在沙箱内执行, 有超时与复杂度限制",
        ],
    )


@router.post(
    "/python",
    response_model=FactorOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建 Python 因子 (需 L3 + 研究员会员)",
)
def create_python_factor(
    payload: PythonFactorCreate,
    current_user: Annotated[User, Depends(require_feature("factor_python"))],
    db: Annotated[Session, Depends(get_db)],
) -> FactorOut:
    try:
        factor = factor_service.create_python_factor(
            db, current_user, payload.name, payload.source, project_id=payload.project_id,
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
    "/scan",
    response_model=FactorScanOut,
    status_code=status.HTTP_201_CREATED,
    summary="模板因子参数网格扫描",
)
def run_factor_scan(
    payload: FactorScanRequest,
    current_user: Annotated[User, Depends(require_feature("factor_param_scan"))],
    db: Annotated[Session, Depends(get_db)],
) -> FactorScanOut:
    from backend.app.services import factor_scan_service as fss
    from backend.app.services.market_data_policy import MarketDataAccessError

    try:
        scan = fss.run_scan(
            db,
            current_user,
            symbol=payload.symbol,
            symbols=payload.symbols,
            template_type=payload.template_type,
            timeframe=payload.timeframe,
            project_id=payload.project_id,
            steps=payload.steps,
        )
    except MarketDataAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    except fss.ScanError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    payload = fss.scan_to_out(scan)
    payload["academy_rewards"] = getattr(scan, "academy_rewards", []) or []
    return FactorScanOut(**payload)


@router.get("/scans", response_model=list[FactorScanOut], summary="我的因子扫描实验")
def list_factor_scans(
    current_user: Annotated[User, Depends(require_feature("factor_param_scan"))],
    db: Annotated[Session, Depends(get_db)],
    project_id: str | None = None,
    symbol: str | None = None,
    template_type: str | None = None,
    limit: int = 50,
) -> list[FactorScanOut]:
    from backend.app.services import factor_scan_service as fss

    pid = None
    if project_id:
        try:
            pid = uuid.UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="无效项目 ID")
    scans = fss.list_scans(
        db,
        current_user.id,
        project_id=pid,
        symbol=symbol,
        template_type=template_type,
        limit=limit,
    )
    titles = fss.project_titles_for(db, scans)
    return [
        FactorScanOut(**fss.scan_to_out(s, project_title=titles.get(s.project_id)))
        for s in scans
    ]


@router.get("/scans/compare", response_model=FactorScanCompareOut, summary="对比两次扫描实验")
def compare_factor_scans(
    scan_a: str,
    scan_b: str,
    current_user: Annotated[User, Depends(require_feature("factor_param_scan"))],
    db: Annotated[Session, Depends(get_db)],
) -> FactorScanCompareOut:
    from backend.app.services import factor_scan_service as fss

    try:
        sid_a = uuid.UUID(scan_a)
        sid_b = uuid.UUID(scan_b)
        data = fss.compare_scans(db, current_user.id, sid_a, sid_b)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="扫描不存在")
    except fss.ScanError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return FactorScanCompareOut(**data)


@router.get("/scans/{scan_id}", response_model=FactorScanOut, summary="扫描详情")
def get_factor_scan(
    scan_id: str,
    current_user: Annotated[User, Depends(require_feature("factor_param_scan"))],
    db: Annotated[Session, Depends(get_db)],
) -> FactorScanOut:
    from backend.app.services import factor_scan_service as fss

    try:
        sid = uuid.UUID(scan_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="扫描不存在")
    scan = fss.get_scan(db, current_user.id, sid)
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="扫描不存在")
    titles = fss.project_titles_for(db, [scan])
    return FactorScanOut(
        **fss.scan_to_out(scan, project_title=titles.get(scan.project_id))
    )


@router.post(
    "/scans/{scan_id}/apply",
    response_model=FactorOut,
    summary="将扫描结果载入为项目因子",
)
def apply_factor_scan(
    scan_id: str,
    payload: ApplyScanRequest,
    current_user: Annotated[User, Depends(require_feature("factor_param_scan"))],
    db: Annotated[Session, Depends(get_db)],
) -> FactorOut:
    from backend.app.services import factor_scan_service as fss

    try:
        sid = uuid.UUID(scan_id)
        _, factor = fss.apply_scan(
            db, current_user, sid, rank=payload.rank, name=payload.name
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="扫描不存在")
    except fss.ScanError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except factor_service.FactorValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except factor_service.FactorNameTakenError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="同名因子已存在")
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


@router.get("/{factor_id}/paper-preview", summary="模拟跟踪预览 (验证后最近行情)")
def paper_preview(
    factor_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    from backend.app.services.research_quality_service import ResearchQualityError, paper_nav_preview

    try:
        from backend.app.services.research_quality_service import ResearchQualityError, paper_preview_with_decay

        return paper_preview_with_decay(db, uuid.UUID(factor_id), current_user.id)
    except (factor_service.FactorNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在")
    except ResearchQualityError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.reasons)
    except mdp.MarketDataAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.get("/{factor_id}/paper-decay", summary="纸面衰减评估")
def paper_decay(
    factor_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    from backend.app.services import paper_tracking_service as pts

    try:
        return pts.assess_factor_decay(db, uuid.UUID(factor_id), current_user.id)
    except (factor_service.FactorNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在")
    except mdp.MarketDataAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.get("/{factor_id}/paper-history", response_model=PaperHistoryOut, summary="纸面跟踪历史")
def paper_history(
    factor_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PaperHistoryOut:
    from backend.app.services import paper_tracking_service as pts

    try:
        payload = pts.snapshot_history_payload(db, uuid.UUID(factor_id), current_user.id)
    except (factor_service.FactorNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在")
    except mdp.MarketDataAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return PaperHistoryOut(**payload)


@router.post("/{factor_id}/paper-track/refresh", summary="立即刷新纸面快照")
def paper_refresh(
    factor_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    from backend.app.services import paper_tracking_service as pts
    from backend.app.services.paper_tracking_service import PaperTrackingError

    try:
        row = pts.record_snapshot(db, uuid.UUID(factor_id), current_user.id)
    except (factor_service.FactorNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="因子不存在")
    except PaperTrackingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    except mdp.MarketDataAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    if row is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="无法记录快照")
    return {
        "as_of_date": row.as_of_date.isoformat(),
        "nav_end": row.nav_end,
        "metrics": row.metrics,
    }


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
    from backend.app.services import academy_hooks

    rewards = academy_hooks.on_factor_preview(db, current_user)
    preview = FactorPreview(**result)
    return preview.model_copy(update={"academy_rewards": rewards})


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
