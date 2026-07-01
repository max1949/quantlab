"""学院任务业务逻辑 (Sprint 2)。

完成任务的核心流程:
1. 校验任务存在且 active;
2. 等级绑定权限: 用户等级 < task.min_level → 拒绝 (TaskLockedError);
3. 幂等: 已完成则不重复奖励 (TaskAlreadyCompletedError);
4. 记录 UserTask, 累加经验, 经阈值重算等级 (可能升级)。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.task import Task, TaskStatus, UserTask
from backend.app.models.user import User, UserLevel
from backend.app.services.leveling import level_for_experience


class TaskNotFoundError(Exception):
    pass


class TaskLockedError(Exception):
    """用户等级不足以完成该任务。"""

    def __init__(self, required: UserLevel) -> None:
        self.required = required
        super().__init__(f"requires level {required.name}")


class TaskAlreadyCompletedError(Exception):
    pass


def try_auto_complete(db: Session, user: User, code: str) -> dict | None:
    """事件驱动自动完成任务 (已做过/等级不足则静默跳过)。"""
    try:
        return complete_task(db, user, code)
    except (TaskNotFoundError, TaskLockedError, TaskAlreadyCompletedError):
        return None


def list_active_tasks(db: Session) -> list[Task]:
    stmt = (
        select(Task)
        .where(Task.is_active.is_(True))
        .order_by(Task.order_index, Task.created_at)
    )
    return list(db.execute(stmt).scalars().all())


def get_by_code(db: Session, code: str) -> Task | None:
    return db.execute(
        select(Task).where(Task.code == code)
    ).scalar_one_or_none()


def completed_task_ids(db: Session, user_id: uuid.UUID) -> set[uuid.UUID]:
    rows = db.execute(
        select(UserTask.task_id, UserTask.status).where(
            UserTask.user_id == user_id
        )
    ).all()
    return {tid for tid, status in rows if status == TaskStatus.COMPLETED.value}


def get_user_task(
    db: Session, user_id: uuid.UUID, task_id: uuid.UUID
) -> UserTask | None:
    return db.execute(
        select(UserTask).where(
            UserTask.user_id == user_id, UserTask.task_id == task_id
        )
    ).scalar_one_or_none()


def complete_task(db: Session, user: User, code: str) -> dict:
    """完成任务并结算成长。返回结算明细 (供路由组装响应)。"""
    task = get_by_code(db, code)
    if task is None or not task.is_active:
        raise TaskNotFoundError(code)

    if user.level < task.min_level:
        raise TaskLockedError(UserLevel(task.min_level))

    if get_user_task(db, user.id, task.id) is not None:
        raise TaskAlreadyCompletedError(code)

    previous_level = user.level

    db.add(
        UserTask(
            user_id=user.id,
            task_id=task.id,
            status=TaskStatus.COMPLETED.value,
        )
    )
    user.experience += task.xp_reward
    new_level = level_for_experience(user.experience)
    # 等级单调不降。
    if new_level.value > user.level:
        user.level = new_level.value

    db.commit()
    db.refresh(user)

    return {
        "task": task,
        "awarded_xp": task.xp_reward,
        "leveled_up": user.level > previous_level,
        "previous_level": previous_level,
        "user": user,
    }


# --------------------------------------------------------------------------
# 默认任务种子 (幂等): 一条 L0→L3 的成长主线。
# 经验阈值: L1=100, L2=300, L3=700, L4=1500 (见 leveling.LEVEL_THRESHOLDS)。
# --------------------------------------------------------------------------
DEFAULT_TASKS: list[dict] = [
    {
        "code": "welcome",
        "title": "欢迎来到 QuantLab",
        "description": "了解平台定位:量化研究员孵化器。阅读首页介绍即可完成。",
        "category": "onboarding",
        "min_level": UserLevel.L0.value,
        "xp_reward": 50,
        "order_index": 10,
    },
    {
        "code": "first-observation",
        "title": "第一次观察",
        "description": "浏览一个示例因子的表现,记录你的第一印象。",
        "category": "onboarding",
        "min_level": UserLevel.L0.value,
        "xp_reward": 50,
        "order_index": 20,
    },
    {
        "code": "use-template-factor",
        "title": "套用模板因子",
        "description": "使用平台模板因子完成一次配置 (L1 解锁组合器的前置)。",
        "category": "factor",
        "min_level": UserLevel.L1.value,
        "xp_reward": 100,
        "order_index": 30,
    },
    {
        "code": "combine-factors",
        "title": "组合你的因子",
        "description": "用因子组合器拼出一个多因子策略 (L2 解锁 Python 的前置)。",
        "category": "factor",
        "min_level": UserLevel.L2.value,
        "xp_reward": 200,
        "order_index": 40,
    },
    {
        "code": "write-python-factor",
        "title": "编写 Python 因子",
        "description": "在沙箱中提交一个自定义 Python 因子 (L3 进阶能力)。",
        "category": "factor",
        "min_level": UserLevel.L3.value,
        "xp_reward": 300,
        "order_index": 50,
    },
]


def seed_default_tasks(db: Session) -> dict:
    """幂等插入默认任务 (按 code 去重)。返回新增/已存在统计。"""
    created, existed = 0, 0
    for spec in DEFAULT_TASKS:
        if get_by_code(db, spec["code"]) is None:
            db.add(Task(**spec))
            created += 1
        else:
            existed += 1
    db.commit()
    return {"created": created, "existed": existed, "total": len(DEFAULT_TASKS)}
