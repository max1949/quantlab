"""AI 研究助手业务逻辑 (Sprint 7)。

取数据库里的研究产物 (验证/回测) → engine 构造提示词 + 本地确定性分析 →
若已接入外部 LLM 则用其生成自然语言回复, 否则 (或调用失败) 降级用本地分析文本 →
落库为 AiInsight 并返回。

设计要点: LLM 是"增强"而非"依赖"。无 Key / 网络异常都不影响功能, 只是回复换成本地规则版。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from engine import ai_advisor
from backend.app.models.ai import AiInsight, InsightKind, InsightSource
from backend.app.models.backtest import Backtest, BacktestStatus
from backend.app.models.factor import Factor
from backend.app.models.user import User
from backend.app.models.validation import Validation, ValidationStatus
from backend.app.services import llm_client


class TargetNotReadyError(Exception):
    """目标不存在 / 非本人 / 未成功。"""


def ai_status() -> dict:
    enabled = llm_client.is_enabled()
    return {
        "enabled": enabled,
        "model": llm_client.model_name() if enabled else None,
        "fallback": "local",
    }


def _factor_brief(f: Factor | None) -> dict:
    if f is None:
        return {}
    return {
        "name": f.name,
        "kind": f.kind,
        "template_type": f.template_type,
        "spec": f.spec,
    }


def _generate(prompt: dict, local: dict) -> tuple[str, str, str | None]:
    """优先 LLM, 失败/未启用则降级本地。返回 (content, source, model)。"""
    if llm_client.is_enabled():
        try:
            text = llm_client.complete(prompt["system"], prompt["user"])
            if text:
                return text, InsightSource.LLM.value, llm_client.model_name()
        except llm_client.LLMError:
            pass  # 降级
    return local["markdown"], InsightSource.LOCAL.value, None


def _persist(
    db: Session,
    owner: User,
    kind: str,
    target_type: str,
    target_id: uuid.UUID,
    content: str,
    source: str,
    model: str | None,
    analysis: dict,
) -> AiInsight:
    insight = AiInsight(
        owner_id=owner.id,
        kind=kind,
        target_type=target_type,
        target_id=target_id,
        source=source,
        model=model,
        content=content,
        analysis=analysis,
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


def review_validation(db: Session, owner: User, validation_id: uuid.UUID) -> AiInsight:
    v = db.get(Validation, validation_id)
    if v is None or v.owner_id != owner.id or v.status != ValidationStatus.SUCCESS.value:
        raise TargetNotReadyError(str(validation_id))

    context = {
        "factor": _factor_brief(db.get(Factor, v.factor_id)),
        "symbol": v.symbol,
        "oos": v.oos,
        "walk_forward": v.walk_forward,
        "sensitivity": v.sensitivity,
        "robustness": v.robustness,
    }
    local = ai_advisor.local_validation_review(context)
    prompt = ai_advisor.build_validation_review_prompt(context)
    content, source, model = _generate(prompt, local)

    return _persist(
        db, owner, InsightKind.VALIDATION_REVIEW.value, "validation",
        validation_id, content, source, model, local,
    )


def summarize_backtest(db: Session, owner: User, backtest_id: uuid.UUID) -> AiInsight:
    b = db.get(Backtest, backtest_id)
    if b is None or b.owner_id != owner.id or b.status != BacktestStatus.SUCCESS.value:
        raise TargetNotReadyError(str(backtest_id))

    context = {
        "factor": _factor_brief(db.get(Factor, b.factor_id)),
        "symbol": b.symbol,
        "metrics": b.metrics,
        "report": b.report,
        "cost_config": b.cost_config,
    }
    local = ai_advisor.local_backtest_summary(context)
    prompt = ai_advisor.build_backtest_summary_prompt(context)
    content, source, model = _generate(prompt, local)

    return _persist(
        db, owner, InsightKind.BACKTEST_SUMMARY.value, "backtest",
        backtest_id, content, source, model, local,
    )


def review_scan(db: Session, owner: User, scan_id: uuid.UUID) -> AiInsight:
    from backend.app.services import factor_scan_service as fss

    scan = fss.get_scan(db, owner.id, scan_id)
    if scan is None:
        raise TargetNotReadyError(str(scan_id))

    out = fss.scan_to_out(scan)
    context = {
        "symbol": scan.symbol,
        "timeframe": scan.timeframe,
        "template_type": scan.template_type,
        "results": out.get("results") or [],
        "coach_summary": scan.coach_summary,
    }
    local = ai_advisor.local_scan_review(context)
    prompt = ai_advisor.build_scan_review_prompt(context)
    content, source, model = _generate(prompt, local)

    return _persist(
        db, owner, InsightKind.SCAN_REVIEW.value, "factor_scan",
        scan_id, content, source, model, local,
    )


def review_scans_batch(
    db: Session, owner: User, scan_ids: list[uuid.UUID]
) -> AiInsight:
    from backend.app.services import factor_scan_service as fss

    if not scan_ids:
        raise TargetNotReadyError("empty")
    if len(scan_ids) > 5:
        scan_ids = scan_ids[:5]
    scans_out: list[dict] = []
    for sid in scan_ids:
        scan = fss.get_scan(db, owner.id, sid)
        if scan is None:
            raise TargetNotReadyError(str(sid))
        row = fss.scan_to_out(scan)
        row["id"] = str(scan.id)
        scans_out.append(row)
    context = {"scans": scans_out}
    local = ai_advisor.local_batch_scan_review(context)
    prompt = ai_advisor.build_batch_scan_review_prompt(context)
    content, source, model = _generate(prompt, local)
    batch_id = uuid.uuid5(uuid.NAMESPACE_DNS, ":".join(sorted(str(i) for i in scan_ids)))
    return _persist(
        db,
        owner,
        "scan_batch_review",
        "factor_scan_batch",
        batch_id,
        content,
        source,
        model,
        local,
    )


def research_plan(db: Session, owner: User, theme: str) -> AiInsight:
    """AI 研究指导: 给方向 -> 研究假设 + 推荐因子 + 实验计划 (不给交易建议)。"""
    local = ai_advisor.local_research_plan(theme)
    prompt = ai_advisor.build_research_plan_prompt(theme)
    content, source, model = _generate(prompt, local)
    # 主题没有业务 uuid, 用 uuid5 派生一个稳定 id 作为 target。
    target_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"theme:{theme}")
    return _persist(
        db, owner, "research_plan", "theme", target_id, content, source, model, local,
    )


def mentor_next(db: Session, user: User, locale: str = "en") -> dict:
    """AI 研究导师: 基于当前进度给"下一步"提醒 (确定性, 复用 onboarding 路线)。

    定位: 提醒/引导, 不给交易建议、不承诺收益。
    """
    from backend.app.core.locale import Locale
    from backend.app.i18n import content as i18n
    from backend.app.services import onboarding_service

    loc: Locale = "zh" if locale == "zh" else "en"
    step = onboarding_service.next_step(db, user, loc)
    message = f"{step['title']} — {step['action']}"
    if step["stage"] == "keep_going":
        message = i18n.MENTOR_KEEP_GOING_PREFIX[loc] + step["action"]
    regime_pick = step.get("regime_pick")
    if regime_pick and regime_pick.get("template_title"):
        fmt = i18n.MENTOR_REGIME_APPEND.get(loc) or i18n.MENTOR_REGIME_APPEND["en"]
        message += fmt.format(
            symbol=regime_pick.get("symbol") or "RB",
            regime=regime_pick.get("regime_label") or regime_pick.get("regime") or "",
            coach=regime_pick.get("coach_hint") or "",
            title=regime_pick["template_title"],
            verdict=regime_pick.get("fit_verdict") or "",
            score=regime_pick.get("fit_score") or 0,
        )

    from backend.app.services import regime_alert_service

    attention_alerts = regime_alert_service.list_attention_alerts(db, user, loc, max_projects=3)
    if attention_alerts:
        summary = "；".join(a["title"] for a in attention_alerts[:2])
        append_fmt = i18n.MENTOR_ATTENTION_APPEND.get(loc) or i18n.MENTOR_ATTENTION_APPEND["en"]
        message += append_fmt.format(summary=summary)

    return {
        "stage": step["stage"],
        "title": step["title"],
        "action": step["action"],
        "cta_path": step["cta_path"],
        "message": message,
        "recommended_template": step.get("recommended_template"),
        "regime_pick": regime_pick,
        "attention_alerts": attention_alerts,
        "disclaimer": i18n.DISCLAIMER[loc],
    }


def list_insights(db: Session, owner_id: uuid.UUID, limit: int = 50) -> list[AiInsight]:
    return list(
        db.execute(
            select(AiInsight)
            .where(AiInsight.owner_id == owner_id)
            .order_by(AiInsight.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
