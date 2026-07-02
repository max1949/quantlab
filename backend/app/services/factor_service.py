"""因子实验室业务逻辑 (Sprint 3)。

调用 engine.factor_engine (纯函数) 完成校验与计算; 自身只负责持久化与权限。
等级绑定权限: 组合器 (stack) 需要 L1, 在路由层用 require_level 把关,
service 再做一次防御性校验 (避免被绕过)。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from engine import factor_engine as fe
from engine import formula as ff
from backend.app.core.locale import Locale
from backend.app.models.factor import Factor, FactorKind
from backend.app.models.project import ResearchProject
from backend.app.models.user import User, UserLevel


class FactorNotFoundError(Exception):
    pass


def _validated_project_id(
    db: Session, owner_id: uuid.UUID, project_id: uuid.UUID | None
) -> uuid.UUID | None:
    """若指定项目, 校验其归属当前用户; 否则返回 None (独立因子)。"""
    if project_id is None:
        return None
    proj = db.get(ResearchProject, project_id)
    if proj is None or proj.owner_id != owner_id:
        raise FactorValidationError("研究项目不存在或无权使用")
    return project_id


class FactorValidationError(Exception):
    """因子定义非法 (参数/组件错误)。"""


class FactorNameTakenError(Exception):
    pass


class StackPermissionError(Exception):
    """等级不足以使用组合器 (需 L1)。"""


STACK_MIN_LEVEL = UserLevel.L1


FACTOR_TEMPLATE_GATES: dict[str, dict[str, int]] = {
    "momentum": {"min_level": 0, "min_tier": 0},
    "volatility": {"min_level": 0, "min_tier": 0},
    "mean_reversion": {"min_level": 0, "min_tier": 0},
    "rsi": {"min_level": 0, "min_tier": 1},
    "sma_ratio": {"min_level": 1, "min_tier": 0},
}


def list_templates(tier: int = 0, level: int = 0, locale: Locale = "en") -> list[dict]:
    """平台模板因子目录 (来自 engine 注册表), 含锁定状态。"""
    from backend.app.i18n import content as i18n

    out = []
    for tpl in fe.TEMPLATES.values():
        gate = FACTOR_TEMPLATE_GATES.get(tpl.code, {"min_level": 0, "min_tier": 0})
        min_level = gate["min_level"]
        min_tier = gate["min_tier"]
        allowed = level >= min_level and tier >= min_tier
        overlay = i18n.FACTOR_TEMPLATES.get(tpl.code, {}).get(locale) or {}
        param_help_map = overlay.get("param_help") or {}
        out.append(
            {
                "code": tpl.code,
                "label": overlay.get("label", tpl.label),
                "description": overlay.get("description", tpl.description),
                "how_it_works": overlay.get("how_it_works", ""),
                "requires": list(tpl.requires),
                "min_level": min_level,
                "min_tier": min_tier,
                "allowed": allowed,
                "params": [
                    {
                        "name": p.name,
                        "default": p.default,
                        "min": p.min,
                        "max": p.max,
                        "label": overlay.get("params", {}).get(p.name, p.label),
                        "help": param_help_map.get(p.name),
                    }
                    for p in tpl.params
                ],
            }
        )
    return out


def list_factors(db: Session, owner_id: uuid.UUID) -> list[Factor]:
    stmt = (
        select(Factor)
        .where(Factor.owner_id == owner_id)
        .order_by(Factor.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_factor(db: Session, owner_id: uuid.UUID, factor_id: uuid.UUID) -> Factor:
    factor = db.get(Factor, factor_id)
    if factor is None or factor.owner_id != owner_id:
        raise FactorNotFoundError(str(factor_id))
    return factor


def _ensure_name_free(db: Session, owner_id: uuid.UUID, name: str) -> None:
    exists = db.execute(
        select(Factor.id).where(
            Factor.owner_id == owner_id, Factor.name == name
        )
    ).first()
    if exists:
        raise FactorNameTakenError(name)


def create_template_factor(
    db: Session, owner: User, name: str, template_type: str, params: dict,
    project_id: uuid.UUID | None = None,
) -> Factor:
    """创建模板因子 (L0+)。校验模板与参数。"""
    try:
        clean = fe.validate_template_params(template_type, params)
    except fe.FactorError as exc:
        raise FactorValidationError(str(exc))

    from backend.app.services import membership_service as ms

    tier = ms.current_tier(db, owner)
    meta = next(
        (t for t in list_templates(tier=tier, level=owner.level) if t["code"] == template_type),
        None,
    )
    if meta and not meta["allowed"]:
        raise FactorValidationError("该因子模板尚未解锁")

    pid = _validated_project_id(db, owner.id, project_id)
    _ensure_name_free(db, owner.id, name)
    factor = Factor(
        owner_id=owner.id,
        project_id=pid,
        name=name,
        kind=FactorKind.TEMPLATE.value,
        template_type=template_type,
        spec={"params": clean},
    )
    db.add(factor)
    db.commit()
    db.refresh(factor)
    from backend.app.services import task_service

    task_service.try_auto_complete(db, owner, "use-template-factor")
    return factor


def create_stack_factor(
    db: Session, owner: User, name: str, components: list[dict],
    project_id: uuid.UUID | None = None,
) -> Factor:
    """创建因子组合器 (需 L1)。组件须为本人已有因子。"""
    if owner.level < STACK_MIN_LEVEL:
        raise StackPermissionError

    if not components:
        raise FactorValidationError("组合器至少需要一个因子")

    clean_components = []
    for comp in components:
        fid = comp["factor_id"]
        # 组件必须是本人已存在的因子
        child = db.get(Factor, fid)
        if child is None or child.owner_id != owner.id:
            raise FactorValidationError(f"因子组件不存在或无权使用: {fid}")
        try:
            weight = float(comp["weight"])
        except (TypeError, ValueError, KeyError):
            raise FactorValidationError("权重必须为数值")
        clean_components.append({"factor_id": str(fid), "weight": weight})

    if sum(abs(c["weight"]) for c in clean_components) == 0:
        raise FactorValidationError("组合器权重不能全为 0")

    pid = _validated_project_id(db, owner.id, project_id)
    _ensure_name_free(db, owner.id, name)
    factor = Factor(
        owner_id=owner.id,
        project_id=pid,
        name=name,
        kind=FactorKind.STACK.value,
        template_type=None,
        spec={"components": clean_components},
    )
    db.add(factor)
    db.commit()
    db.refresh(factor)
    from backend.app.services import task_service

    task_service.try_auto_complete(db, owner, "combine-factors")
    return factor


def create_formula_factor(
    db: Session, owner: User, name: str, expr: str,
    project_id: uuid.UUID | None = None,
) -> Factor:
    """创建公式因子 (L2 + 研究员会员)。权益闸门在路由层 require_feature 把关。"""
    try:
        ff.validate(expr)
        # 在样本行情上试算一次, 提前暴露错误。
        ff.compute(fe.sample_price_frame(n=120), expr)
    except ff.FormulaError as exc:
        raise FactorValidationError(str(exc))

    pid = _validated_project_id(db, owner.id, project_id)
    _ensure_name_free(db, owner.id, name)
    factor = Factor(
        owner_id=owner.id,
        project_id=pid,
        name=name,
        kind=FactorKind.FORMULA.value,
        template_type=None,
        spec={"expr": expr.strip()},
    )
    db.add(factor)
    db.commit()
    db.refresh(factor)
    from backend.app.services import task_service

    task_service.try_auto_complete(db, owner, "write-formula-factor")
    return factor


def create_python_factor(
    db: Session, owner: User, name: str, source: str,
    project_id: uuid.UUID | None = None,
) -> Factor:
    """创建 Python 因子 (L3 + 研究员会员, 沙箱执行)。"""
    from sandbox.ast_guard import validate_source
    from sandbox.runner import SandboxError, run_user_factor

    src = (source or "").strip()
    ok, errors = validate_source(src)
    if not ok:
        raise FactorValidationError("; ".join(errors))
    try:
        run_user_factor(src, fe.sample_price_frame(n=120))
    except SandboxError as exc:
        raise FactorValidationError(str(exc))

    pid = _validated_project_id(db, owner.id, project_id)
    _ensure_name_free(db, owner.id, name)
    factor = Factor(
        owner_id=owner.id,
        project_id=pid,
        name=name,
        kind=FactorKind.PYTHON.value,
        template_type=None,
        spec={"source": src},
    )
    db.add(factor)
    db.commit()
    db.refresh(factor)
    from backend.app.services import task_service

    task_service.try_auto_complete(db, owner, "write-python-factor")
    return factor


def delete_factor(db: Session, owner_id: uuid.UUID, factor_id: uuid.UUID) -> None:
    factor = get_factor(db, owner_id, factor_id)
    db.delete(factor)
    db.commit()


# ---------------------------------------------------------------------------
# 预览: 在确定性样本行情上计算因子 (真行情 Sprint 4 接入)
# ---------------------------------------------------------------------------
def _compute_series(db: Session, owner_id: uuid.UUID, factor: Factor, market):
    """递归计算因子在给定行情上的 Series。"""
    if factor.kind == FactorKind.TEMPLATE.value:
        return fe.compute_template_factor(
            market, factor.template_type, factor.spec.get("params", {})
        )
    if factor.kind == FactorKind.FORMULA.value:
        try:
            return ff.compute(market, factor.spec.get("expr", ""))
        except ff.FormulaError as exc:
            raise FactorValidationError(str(exc))
    if factor.kind == FactorKind.PYTHON.value:
        from sandbox.runner import SandboxError, run_user_factor

        try:
            return run_user_factor(factor.spec.get("source", ""), market)
        except SandboxError as exc:
            raise FactorValidationError(str(exc))
    # stack: 取出各组件因子, 递归计算后加权组合
    items = []
    for comp in factor.spec.get("components", []):
        child = db.get(Factor, uuid.UUID(comp["factor_id"]))
        if child is None or child.owner_id != owner_id:
            raise FactorValidationError(
                f"组件因子缺失: {comp['factor_id']}"
            )
        items.append((_compute_series(db, owner_id, child, market), comp["weight"]))
    return fe.compute_factor_stack(items)


def preview(
    db: Session, owner_id: uuid.UUID, factor: Factor, sample_rows: int = 252
) -> dict:
    market = fe.sample_price_frame(n=sample_rows)
    try:
        series = _compute_series(db, owner_id, factor, market)
    except fe.FactorError as exc:
        raise FactorValidationError(str(exc))
    return {
        "factor_id": factor.id,
        "name": factor.name,
        "kind": factor.kind,
        "sample_rows": sample_rows,
        "stats": fe.summarize(series),
    }
