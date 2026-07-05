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
    rows = _list_active_tasks_raw(db)
    if len(rows) < len(DEFAULT_TASKS):
        seed_default_tasks(db)
        rows = _list_active_tasks_raw(db)
    return rows


def _list_active_tasks_raw(db: Session) -> list[Task]:
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


def user_task_map(
    db: Session, user_id: uuid.UUID, task_ids: list[uuid.UUID]
) -> dict[uuid.UUID, UserTask]:
    if not task_ids:
        return {}
    rows = db.execute(
        select(UserTask).where(
            UserTask.user_id == user_id,
            UserTask.task_id.in_(task_ids),
        )
    ).scalars().all()
    return {ut.task_id: ut for ut in rows}


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
        "code": "challenge-enroll",
        "title": "报名 30 天挑战",
        "description": "首次报名 30 天研究挑战后自动完成 — 里程碑会随你的研究进度点亮。",
        "category": "onboarding",
        "min_level": UserLevel.L0.value,
        "xp_reward": 60,
        "order_index": 15,
    },
    {
        "code": "first-observation",
        "title": "第一次观察",
        "description": "预览因子或完成首次回测后自动完成 (查看因子在样本行情上的统计)。",
        "category": "onboarding",
        "min_level": UserLevel.L0.value,
        "xp_reward": 50,
        "order_index": 20,
    },
    {
        "code": "first-backtest",
        "title": "第一次回测",
        "description": "完成首次因子回测后自动完成 — 查看夏普、回撤与胜率。",
        "category": "research",
        "min_level": UserLevel.L0.value,
        "xp_reward": 75,
        "order_index": 25,
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
        "code": "first-validation",
        "title": "第一次科学验证",
        "description": "完成首次样本外 + Walk-Forward 验证后自动完成。",
        "category": "research",
        "min_level": UserLevel.L0.value,
        "xp_reward": 100,
        "order_index": 32,
    },
    {
        "code": "first-factor-scan",
        "title": "第一次参数扫描",
        "description": "完成首次模板因子参数网格扫描后自动完成。",
        "category": "factor",
        "min_level": UserLevel.L1.value,
        "xp_reward": 75,
        "order_index": 31,
    },
    {
        "code": "first-report",
        "title": "第一份研究报告",
        "description": "首次生成研究报告后自动完成 — 把因子、回测与验证写成结论。",
        "category": "research",
        "min_level": UserLevel.L0.value,
        "xp_reward": 125,
        "order_index": 33,
    },
    {
        "code": "first-publish",
        "title": "首次发布研究",
        "description": "首次将项目发布到研究广场后自动完成。",
        "category": "research",
        "min_level": UserLevel.L0.value,
        "xp_reward": 150,
        "order_index": 34,
    },
    {
        "code": "first-share",
        "title": "首次分享研究",
        "description": "首次生成研究分享卡片后自动完成。",
        "category": "research",
        "min_level": UserLevel.L0.value,
        "xp_reward": 75,
        "order_index": 35,
    },
    {
        "code": "first-paper-order",
        "title": "第一笔 Paper 模拟单",
        "description": "通过 Paper 毕业线后提交首笔模拟订单，开启真实跟踪后自动完成。",
        "category": "research",
        "min_level": UserLevel.L1.value,
        "xp_reward": 125,
        "order_index": 36,
    },
    {
        "code": "paper-decay-review",
        "title": "衰减后复查",
        "description": "已有 Paper 单后重新跑科学验证 — 纸面衰减时系统会指引你完成此步。",
        "category": "research",
        "min_level": UserLevel.L1.value,
        "xp_reward": 100,
        "order_index": 37,
    },
    {
        "code": "write-formula-factor",
        "title": "编写公式因子",
        "description": "在因子实验室创建公式因子后自动完成 (L2 + 研究员会员)。",
        "category": "factor",
        "min_level": UserLevel.L2.value,
        "xp_reward": 150,
        "order_index": 45,
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


# 学院任务 ↔ 大师路径阶段映射 (供 UI 联动高亮)。
MASTERY_STAGE_BY_TASK_CODE: dict[str, str] = {
    "welcome": "start",
    "challenge-enroll": "start",
    "first-observation": "start",
    "first-backtest": "backtest",
    "first-validation": "validate",
    "first-factor-scan": "validate",
    "first-paper-order": "paper",
    "paper-decay-review": "track",
    "first-report": "share",
    "first-publish": "share",
    "first-share": "share",
    "use-template-factor": "start",
    "combine-factors": "graduate",
    "write-formula-factor": "graduate",
    "write-python-factor": "graduate",
}

MASTERY_STAGE_TASK_CODES: dict[str, list[str]] = {
    "start": ["welcome", "challenge-enroll", "first-observation", "use-template-factor"],
    "backtest": ["first-backtest"],
    "validate": ["first-validation", "first-factor-scan"],
    "graduate": ["combine-factors", "write-formula-factor"],
    "paper": ["first-paper-order"],
    "track": ["paper-decay-review"],
    "share": ["first-report", "first-publish", "first-share"],
}


def mastery_stage_for_task(code: str) -> str | None:
    return MASTERY_STAGE_BY_TASK_CODE.get(code)


def mastery_milestones_for_user(db: Session, user_id: uuid.UUID) -> list[dict]:
    """大师路径各阶段关联的学院任务进度 (项目质量页 / 仪表盘联动)。"""
    tasks = list_active_tasks(db)
    by_code = {t.code: t for t in tasks}
    completed_ids = completed_task_ids(db, user_id)
    out: list[dict] = []
    for stage, codes in MASTERY_STAGE_TASK_CODES.items():
        for code in codes:
            task = by_code.get(code)
            if task is None:
                continue
            out.append(
                {
                    "code": code,
                    "title": task.title,
                    "mastery_stage": stage,
                    "xp_reward": task.xp_reward,
                    "completed": task.id in completed_ids,
                }
            )
    return out


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
