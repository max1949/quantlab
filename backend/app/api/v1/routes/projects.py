"""研究项目路由 (Sprint 8): 项目 CRUD / 发布 / 研究路径图谱。

项目是 Research OS 闭环的起点: 用户先建项目 (定一个研究主题), 在项目下造因子→回测→验证→报告。
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.core.locale import RequestLocale
from backend.app.i18n.content import overlay_project_fields
from backend.app.models.project import ProjectStatus
from backend.app.schemas.project import GraphOut, ProjectCreate, ProjectOut
from backend.app.services import project_service

router = APIRouter()


def _project_out(project, locale: RequestLocale) -> ProjectOut:
    base = ProjectOut.model_validate(project)
    overlay = overlay_project_fields(
        base.title, base.question, base.description, list(base.tags or []), locale
    )
    if overlay:
        return base.model_copy(update=overlay)
    return base


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED, summary="创建研究项目")
def create_project(
    payload: ProjectCreate,
    current_user: CurrentUser,
    locale: RequestLocale,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectOut:
    project = project_service.create_project(
        db, current_user, payload.title, payload.symbol, payload.question,
        payload.description, payload.tags,
    )
    return _project_out(project, locale)


@router.get("", response_model=list[ProjectOut], summary="我的研究项目")
def list_my_projects(
    current_user: CurrentUser,
    locale: RequestLocale,
    db: Annotated[Session, Depends(get_db)],
) -> list[ProjectOut]:
    return [_project_out(p, locale) for p in project_service.list_my_projects(db, current_user.id)]


def _load_visible(db, current_user, project_id: str):
    try:
        p = project_service.get_project(db, uuid.UUID(project_id))
    except (project_service.ProjectNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if p.owner_id != current_user.id and p.status != ProjectStatus.PUBLISHED.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="该项目未公开")
    return p


@router.get("/{project_id}", response_model=ProjectOut, summary="项目详情 (公开项目他人可见)")
def get_project(
    project_id: str,
    current_user: CurrentUser,
    locale: RequestLocale,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectOut:
    return _project_out(_load_visible(db, current_user, project_id), locale)


@router.get("/{project_id}/quality", summary="发布质量评估 (是否达广场门槛)")
def project_quality(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    from backend.app.services import research_quality_service as rq

    project_service.get_owned_project(db, current_user.id, uuid.UUID(project_id))
    verdict = rq.assess_project(db, uuid.UUID(project_id))
    return {"passed": verdict.passed, "reasons": verdict.reasons, "scorecard": verdict.scorecard}


@router.post("/{project_id}/publish", response_model=ProjectOut, summary="发布项目到研究 Feed")
def publish_project(
    project_id: str,
    current_user: CurrentUser,
    locale: RequestLocale,
    db: Annotated[Session, Depends(get_db)],
) -> ProjectOut:
    try:
        p = project_service.publish_project(db, current_user.id, uuid.UUID(project_id))
    except (project_service.ProjectNotFoundError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    except project_service.ProjectNotPublishableError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="项目还没有任何研究产物 (先在项目下造因子), 不能发布",
        )
    except project_service.ProjectQualityRejectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "研究质量未达发布门槛", "reasons": exc.reasons},
        )
    return _project_out(p, locale)


@router.get("/{project_id}/graph", response_model=GraphOut, summary="研究路径图谱 (假设→实验→验证→结果)")
def project_graph(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> GraphOut:
    p = _load_visible(db, current_user, project_id)
    return GraphOut(**project_service.build_graph(db, p))
