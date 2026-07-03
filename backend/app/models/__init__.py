# ORM 模型包。
# 模型需在此导入, 以便 Alembic autogenerate 能发现 (env.py 会 import 本包)。
from backend.app.models.organization import (  # noqa: F401
    OrgFactorShare,
    OrgMember,
    OrgRole,
    ResearchOrg,
)
from backend.app.models.audit import AuditEvent  # noqa: F401
from backend.app.models.ai import (  # noqa: F401
    AiInsight,
    InsightKind,
    InsightSource,
)
from backend.app.models.backtest import Backtest, BacktestStatus  # noqa: F401
from backend.app.models.challenge import Challenge, ChallengeProgress  # noqa: F401
from backend.app.models.competition import (  # noqa: F401
    Season,
    SeasonStatus,
    Submission,
)
from backend.app.models.project import (  # noqa: F401
    NodeKind,
    ProjectStatus,
    ResearchEdge,
    ResearchNode,
    ResearchProject,
)
from backend.app.models.factor import Factor, FactorKind  # noqa: F401
from backend.app.models.factor_scan import FactorScan  # noqa: F401
from backend.app.models.growth import (  # noqa: F401
    Referral,
    ReferralStatus,
    ResearchShare,
    ResearchTemplate,
    UserEvent,
    UserFollow,
)
from backend.app.models.market import DataSnapshot, MarketDataset  # noqa: F401
from backend.app.models.membership import (  # noqa: F401
    RedeemCode,
    Subscription,
    SubscriptionStatus,
)
from backend.app.models.paper import PaperSnapshot  # noqa: F401
from backend.app.models.research import ResearchReport  # noqa: F401
from backend.app.models.task import Task, TaskStatus, UserTask  # noqa: F401
from backend.app.models.user import User, UserLevel, UserType  # noqa: F401
from backend.app.models.validation import Validation, ValidationStatus  # noqa: F401

__all__ = [
    "AuditEvent",
    "User",
    "UserLevel",
    "Task",
    "UserTask",
    "TaskStatus",
    "Factor",
    "FactorKind",
    "MarketDataset",
    "DataSnapshot",
    "Backtest",
    "BacktestStatus",
    "Validation",
    "ValidationStatus",
    "Season",
    "SeasonStatus",
    "Submission",
    "AiInsight",
    "InsightKind",
    "InsightSource",
    "ResearchReport",
    "ResearchProject",
    "ResearchNode",
    "ResearchEdge",
    "ProjectStatus",
    "NodeKind",
    "Challenge",
    "ChallengeProgress",
    "UserType",
    "Referral",
    "ReferralStatus",
    "ResearchTemplate",
    "ResearchShare",
    "UserFollow",
    "UserEvent",
    "Subscription",
    "SubscriptionStatus",
    "RedeemCode",
    "PaperSnapshot",
    "FactorScan",
    "ResearchOrg",
    "OrgMember",
    "OrgFactorShare",
    "OrgRole",
]
