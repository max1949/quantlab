"""学院任务路由 (Sprint 2): 列表 / 详情 / 完成。

所有接口需登录。列表/详情标注当前用户的 completed / locked 状态;
完成接口结算经验与升级,并按 min_level 执行等级绑定权限。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.deps import CurrentUser
from backend.app.core.database import get_db
from backend.app.schemas.task import (
    CompleteTaskResult,
    TaskWithProgress,
)
from backend.app.schemas.user import UserOut
from backend.app.services import task_service

router = APIRouter()


def _with_progress(task, completed_ids, user_task_map, user_level) -> TaskWithProgress:
    ut = user_task_map.get(task.id)
    return TaskWithProgress(
        id=task.id,
        code=task.code,
        title=task.title,
        description=task.description,
        category=task.category,
        min_level=task.min_level,
        xp_reward=task.xp_reward,
        order_index=task.order_index,
        completed=task.id in completed_ids,
        locked=user_level < task.min_level,
        completed_at=ut.completed_at if ut else None,
    )


@router.get(
    "",
    response_model=list[TaskWithProgress],
    summary="任务列表 (含当前用户进度/锁定状态)",
)
def list_tasks(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> list[TaskWithProgress]:
    tasks = task_service.list_active_tasks(db)
    completed_ids = task_service.completed_task_ids(db, current_user.id)
    user_task_map = {
        ut.task_id: ut
        for t in tasks
        if (ut := task_service.get_user_task(db, current_user.id, t.id))
    }
    return [
        _with_progress(t, completed_ids, user_task_map, current_user.level)
        for t in tasks
    ]


@router.get(
    "/{code}",
    response_model=TaskWithProgress,
    summary="任务详情",
)
def get_task(
    code: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> TaskWithProgress:
    task = task_service.get_by_code(db, code)
    if task is None or not task.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在"
        )
    completed_ids = task_service.completed_task_ids(db, current_user.id)
    ut = task_service.get_user_task(db, current_user.id, task.id)
    user_task_map = {ut.task_id: ut} if ut else {}
    return _with_progress(task, completed_ids, user_task_map, current_user.level)


@router.post(
    "/{code}/complete",
    response_model=CompleteTaskResult,
    summary="完成任务 (结算经验, 可能升级; 受 min_level 等级闸门约束)",
)
def complete_task(
    code: str,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CompleteTaskResult:
    try:
        result = task_service.complete_task(db, current_user, code)
    except task_service.TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在"
        )
    except task_service.TaskLockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"需要等级 {exc.required.name} ({exc.required.label}) 才能完成此任务",
        )
    except task_service.TaskAlreadyCompletedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="任务已完成, 不可重复领取"
        )

    return CompleteTaskResult(
        task=result["task"],
        awarded_xp=result["awarded_xp"],
        leveled_up=result["leveled_up"],
        previous_level=result["previous_level"],
        user=UserOut.model_validate(result["user"]),
    )
