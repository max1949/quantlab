"""Growth OS 出入参 schema (Sprint 9A)。"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.user import UserType


# ---- onboarding ----
class ChooseTypeRequest(BaseModel):
    user_type: UserType


class NextStepOut(BaseModel):
    user_type: str
    user_type_label: str
    intro: str
    stage: str
    title: str
    action: str
    cta_path: str
    recommended_template: str | None = None
    active_project_id: uuid.UUID | None = None
    regime_pick: dict | None = None


class JourneyStepOut(BaseModel):
    key: str
    label: str
    done: bool
    challenge_milestones: list[dict] = Field(default_factory=list)


class MasteryGoalOut(BaseModel):
    paper_graduated_count: int = 0
    paper_tracking_count: int = 0
    on_leaderboard: bool = False
    leaderboard_rank: int | None = None
    mastery_stage: str | None = None
    mastery_next_action: str | None = None
    mastery_progress_pct: int = 0
    paper_ready: bool = False
    publish_ready: bool = False
    hint: str = ""
    challenge_paper_milestones: list[dict] = Field(default_factory=list)
    board_limit: int = 50
    cutoff_graduated: int | None = None
    graduated_needed: int | None = None
    needs_tracking_boost: bool = False
    ranks_outside_board: int | None = None


class AttentionAlertOut(BaseModel):
    kind: str
    alert_key: str
    title: str
    message: str
    project_id: uuid.UUID | None = None
    symbol: str | None = None
    action: str
    cta_path: str
    severity: str = "info"
    challenge_hint: str | None = None


class ChallengePaperCoachingOut(BaseModel):
    enrolled: bool = True
    next_code: str
    next_day: int
    next_title: str
    message: str
    cta_path: str
    cta_action: str
    attention_linked: bool = False
    linked_alert_kinds: list[str] = Field(default_factory=list)


class UpgradeCoachingOut(BaseModel):
    current_tier: int
    current_tier_name: str
    target_tier: int
    target_tier_name: str
    plan_code: str
    plan_name: str
    price_cny: int
    reason: str
    message: str
    cta_path: str
    stripe_available: bool = False
    unlock_features: str = ""


class MarketDataCoachingOut(BaseModel):
    symbol: str
    timeframe: str
    current_tier: int
    current_summary: str
    target_tier: int
    target_summary: str
    plan_code: str
    plan_name: str
    price_cny: int
    reason: str
    message: str
    effective_rows: int | None = None
    total_rows: int | None = None
    quality_grade: str | None = None
    quality_warnings: list[str] = Field(default_factory=list)
    cta_path: str
    stripe_available: bool = False


class CheckoutCoachingOut(BaseModel):
    plan_code: str
    plan_name: str
    tier: int
    tier_name: str
    reason: str
    message: str
    unlock_features: str
    cta_action: str
    cta_path: str
    active_project_id: uuid.UUID | None = None
    receipt_email_hint: str | None = None


class QuickstartGuideStepOut(BaseModel):
    key: str
    done: bool
    label: str
    hint: str
    cta_path: str
    cta_action: str


class QuickstartGuideOut(BaseModel):
    title: str
    subtitle: str
    current_badge: str
    steps: list[QuickstartGuideStepOut]
    current_index: int
    progress: int
    total: int


class FirstReportCoachingOut(BaseModel):
    reason: str
    badge: str
    message: str
    celebrate: str
    unlock_features: str
    cta_action: str
    cta_path: str
    active_project_id: uuid.UUID | None = None
    paper_ready: bool = False


class DismissAttentionAlertRequest(BaseModel):
    alert_key: str = Field(min_length=1, max_length=128)


class DismissAttentionAlertOut(BaseModel):
    alert_key: str
    cooldown_days: int
    dismissed_at: str


class AttentionAlertHistoryItemOut(BaseModel):
    alert_key: str
    kind: str
    kind_label: str
    ref_label: str | None = None
    dismissed_at: str
    expires_at: str
    days_remaining: int


class AttentionAlertHistoryOut(BaseModel):
    cooldown_days: int
    items: list[AttentionAlertHistoryItemOut] = Field(default_factory=list)


class RestoreAttentionAlertRequest(BaseModel):
    alert_key: str = Field(min_length=1, max_length=128)


class RestoreAttentionAlertOut(BaseModel):
    alert_key: str
    restored: bool = True


class ResearchJourneyOut(BaseModel):
    done_count: int
    total: int
    steps: list[JourneyStepOut]
    active_project_id: uuid.UUID | None = None
    challenge_enrolled: bool = False
    challenge_code: str | None = None
    challenge_completed_count: int = 0
    challenge_total: int = 0
    mastery_goal: MasteryGoalOut = Field(default_factory=MasteryGoalOut)
    attention_alerts: list[AttentionAlertOut] = Field(default_factory=list)
    challenge_paper_coaching: ChallengePaperCoachingOut | None = None
    upgrade_coaching: UpgradeCoachingOut | None = None
    market_data_coaching: MarketDataCoachingOut | None = None
    checkout_coaching: CheckoutCoachingOut | None = None
    quickstart_guide: QuickstartGuideOut | None = None
    first_report_coaching: FirstReportCoachingOut | None = None


# ---- 研究模板 ----
class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    title: str
    symbol: str
    factor_template: str
    default_params: dict
    hypothesis: str
    description: str
    tags: list
    min_level: int = 0
    min_tier: int = 0
    allowed: bool = True
    lock_hint: str | None = None
    track: str = "beginner"
    suitable_for: str = ""
    factor_template_label: str = ""
    factor_note: str = ""
    how_it_works: str = ""
    learning_steps: list[str] = Field(default_factory=list)


class TemplateRegimePickOut(BaseModel):
    code: str
    title: str
    symbol: str
    fit_score: int
    fit_verdict: str
    fit_hint: str
    allowed: bool
    track: str = "beginner"


class TemplateRegimePicksOut(BaseModel):
    symbol: str
    regime: str | None = None
    regime_label: str | None = None
    coach_hint: str = ""
    picks: list[TemplateRegimePickOut] = Field(default_factory=list)


class StartTemplateRequest(BaseModel):
    with_factor: bool = True


class StartTemplateResult(BaseModel):
    project_id: uuid.UUID
    factor_id: uuid.UUID | None
    template_code: str


# ---- 分享卡片 ----
class ShareOut(BaseModel):
    token: str
    share_path: str
    card: dict
    views: int
    academy_rewards: list = Field(default_factory=list)


class ShareCardOut(BaseModel):
    """公开 (免登录) 分享页数据。"""

    token: str
    card: dict
    views: int
    created_at: datetime


# ---- 多维榜单 ----
class LeaderRow(BaseModel):
    rank: int
    user_id: str
    username: str
    level: int
    metric_label: str
    metric_value: float | int | str


class PaperMasteryCutoffOut(BaseModel):
    rank: int
    user_id: str
    username: str | None = None
    graduated: int
    tracking: int


class PaperMasteryMetaOut(BaseModel):
    board_limit: int
    total_ranked: int
    board_full: bool
    cutoff: PaperMasteryCutoffOut | None = None


# ---- 邀请 ----
class ReferralOut(BaseModel):
    code: str
    share_path: str
    invited: int
    activated: int
    reward_points_earned: int


# ---- 埋点 ----
class EventIn(BaseModel):
    event: str = Field(min_length=1, max_length=64)
    props: dict = Field(default_factory=dict)


# ---- AI 导师 ----
class MentorOut(BaseModel):
    stage: str
    title: str
    action: str
    cta_path: str
    message: str
    recommended_template: str | None = None
    regime_pick: dict | None = None
    attention_alerts: list[AttentionAlertOut] = Field(default_factory=list)
    disclaimer: str
