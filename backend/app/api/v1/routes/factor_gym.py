"""Factor Gym API — Guided Golden Path (feature-flagged) + controlled test entry."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from backend.app.auth.deps import get_current_user
from backend.app.models.user import User
from backend.app.services.factor_gym_access import (
    DENIED_DETAIL_INVITE_ONLY,
    resolve_factor_gym_access,
)
from engine.factor_gym import (
    HypothesisStore,
    UserPrediction,
    draft_from_idea,
    run_gym_experiment,
    seal_and_save,
)
from engine.factor_gym.hypothesis import HypothesisContract
from engine.factor_gym.reproduce import reproduce_from_ir_dict
from engine.research_memory import append_hit_ledger, memory_check, memory_metrics_snapshot

router = APIRouter()


def _token_from_request(request: Request) -> str | None:
    return request.headers.get("X-Factor-Gym-Test-Token") or request.query_params.get("test_token")


def require_gym_access(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Canonical API gate — same resolver as GET /status (no second Gate)."""
    access = resolve_factor_gym_access(user, test_token=_token_from_request(request))
    if not access["FACTOR_GYM_ACCESS_ALLOWED"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=access.get("denied_detail") or DENIED_DETAIL_INVITE_ONLY,
        )
    return access


GymAccess = Annotated[dict[str, Any], Depends(require_gym_access)]


class IdeaIn(BaseModel):
    idea: str = Field(min_length=4, max_length=2000)


class SealIn(BaseModel):
    hypothesis_id: str
    research_question: str
    economic_rationale: str = ""
    expected_direction: Literal["positive", "negative", "unknown"] = "unknown"
    falsification_condition: str = ""
    version: int = 1


class MemoryCheckIn(BaseModel):
    idea: str = Field(min_length=4, max_length=2000)
    hypothesis_id: str | None = None


class MemoryDecisionIn(BaseModel):
    hit_id: str
    decision: Literal["continue", "view_history", "skip", "revalidate"]
    hypothesis_id: str | None = None


class RunIn(BaseModel):
    hypothesis_id: str
    predicted_direction: Literal["positive", "negative", "unclear"]
    predicted_strength: Literal["weak", "moderate", "strong"] = "moderate"
    notes: str = ""
    memory_hit_id: str | None = None
    force_despite_duplicate: bool = False


class ReproduceIn(BaseModel):
    ir: dict[str, Any]
    seed: int = 42


_DRAFTS: dict[str, Any] = {}
_MEMORY_HITS: dict[str, Any] = {}
_DRAFT_DIR = Path("data") / "factor_gym" / "drafts"


def _persist_draft(draft: Any) -> None:
    """Cross-worker draft share (uvicorn --workers > 1)."""
    _DRAFTS[draft.hypothesis_id] = draft
    _DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    (_DRAFT_DIR / f"{draft.hypothesis_id}.json").write_text(
        draft.model_dump_json(), encoding="utf-8"
    )


def _load_draft(hypothesis_id: str) -> Any | None:
    if hypothesis_id in _DRAFTS:
        return _DRAFTS[hypothesis_id]
    path = _DRAFT_DIR / f"{hypothesis_id}.json"
    if not path.is_file():
        return None
    draft = HypothesisContract.model_validate_json(path.read_text(encoding="utf-8"))
    _DRAFTS[hypothesis_id] = draft
    return draft


def _drop_draft(hypothesis_id: str) -> None:
    _DRAFTS.pop(hypothesis_id, None)
    path = _DRAFT_DIR / f"{hypothesis_id}.json"
    if path.is_file():
        path.unlink()


def _load_memory_hit(hit_id: str) -> dict[str, Any] | None:
    if hit_id in _MEMORY_HITS:
        return _MEMORY_HITS[hit_id]
    from engine.research_memory import DEFAULT_HIT_LEDGER
    import json

    path = Path(DEFAULT_HIT_LEDGER)
    if not path.is_file():
        return None
    found: dict[str, Any] | None = None
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("hit_id") == hit_id:
                found = row
    if not found:
        return None
    meta = {
        "idea": found.get("query") or "",
        "classification": found.get("classification"),
        "block_rerun": found.get("classification") == "EXACT_DUPLICATE",
        "user_id": None,
    }
    _MEMORY_HITS[hit_id] = meta
    return meta


@router.get("/status")
def gym_status(
    request: Request,
    response: Response,
    _user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    from engine.factor_gym.telemetry import emit as emit_telemetry

    # Prevent browser/CDN caching a denied payload over an allowlisted session.
    response.headers["Cache-Control"] = "no-store"
    access = resolve_factor_gym_access(_user, test_token=_token_from_request(request))
    if access["FACTOR_GYM_ACCESS_ALLOWED"]:
        emit_telemetry(
            "factor_gym_test_entry_opened" if access["test_entry"] else "factor_gym_opened",
            {
                "user_id": str(_user.id),
                "mode": access["mode"],
                "test_entry": access["test_entry"],
            },
        )
    access_allowed = bool(access["FACTOR_GYM_ACCESS_ALLOWED"])
    return {
        # Canonical access decision — FE/nav/API must use this, never global enabled alone.
        "FACTOR_GYM_ACCESS_ALLOWED": access_allowed,
        "allowed": access_allowed,
        "enabled": bool(access["enabled"]),  # legacy flag only
        "global_enabled": bool(access["global_enabled"]),
        "open_beta": bool(access.get("open_beta")),
        "test_entry": bool(access["test_entry"]),
        "mode": access["mode"],
        "label": access["label"],
        "public_rollout": False,
        "owner_token_fallback": "DENY",
        "path": "idea→memory_check→hypothesis→prediction→IR→experiment→next_action",
        "byok": "DEFER_UNTIL_SECRET_VAULT_READY",
        "semantic_similarity": "DEFER",
        "memory_metrics": memory_metrics_snapshot(),
        "controlled_test_entry": False,
        "denied_detail": access.get("denied_detail"),
    }




@router.post("/memory-check")
def api_memory_check(
    body: MemoryCheckIn,
    user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    check = memory_check(body.idea)
    hit_id = append_hit_ledger(
        idea=body.idea,
        check=check,
        hypothesis_id=body.hypothesis_id,
        user_decision=None,
        experiment_executed=None,
    )
    public = check.to_public()
    _MEMORY_HITS[hit_id] = {
        "idea": body.idea,
        "classification": check.classification,
        "block_rerun": check.block_rerun,
        "user_id": str(user.id),
    }
    return public


@router.post("/memory-decision")
def api_memory_decision(
    body: MemoryDecisionIn,
    user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    meta = _load_memory_hit(body.hit_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="memory hit not found")
    check = memory_check(meta["idea"])
    append_hit_ledger(
        idea=meta["idea"],
        check=check,
        hypothesis_id=body.hypothesis_id,
        user_decision=body.decision,
        experiment_executed=body.decision == "continue",
    )
    return {
        "ok": True,
        "decision": body.decision,
        "allow_experiment": body.decision in ("continue", "revalidate")
        or not meta.get("block_rerun"),
        "user_id": str(user.id),
    }


@router.post("/ideas")
def create_idea(
    body: IdeaIn,
    user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    from engine.factor_gym.telemetry import emit as emit_telemetry

    emit_telemetry("idea_submitted", {"user_id": str(user.id)})
    draft = draft_from_idea(body.idea, author_user_id=str(user.id), ai_assistance=False)
    _persist_draft(draft)
    check = memory_check(body.idea)
    hit_id = append_hit_ledger(
        idea=body.idea,
        check=check,
        hypothesis_id=draft.hypothesis_id,
    )
    from engine.factor_gym.telemetry import emit as emit_telemetry

    emit_telemetry(
        "memory_check_seen",
        {
            "user_id": str(user.id),
            "classification": check.classification,
            "hit_id": hit_id,
        },
    )
    _MEMORY_HITS[hit_id] = {
        "idea": body.idea,
        "classification": check.classification,
        "block_rerun": check.block_rerun,
        "user_id": str(user.id),
    }
    return {
        "hypothesis_id": draft.hypothesis_id,
        "branch_id": draft.branch_id,
        "research_question": draft.research_question,
        "economic_rationale": draft.economic_rationale,
        "expected_direction": draft.expected_direction,
        "falsification_condition": draft.falsification_condition,
        "sealed": draft.sealed,
        "prompt": "先看看以前有没有类似研究，再写下你对结果的预测。",
        "rule_plain": "系统已把你的想法转换成可测试规则。",
        "memory_check": check.to_public(),
    }


@router.post("/hypotheses/seal")
def seal_hypothesis(
    body: SealIn,
    user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    draft = _load_draft(body.hypothesis_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="draft hypothesis not found; POST /ideas first")
    updated = draft.model_copy(
        update={
            "research_question": body.research_question.strip(),
            "economic_rationale": body.economic_rationale,
            "expected_direction": body.expected_direction,
            "falsification_condition": body.falsification_condition
            or draft.falsification_condition,
            "author_user_id": str(user.id),
            "version": body.version,
        }
    )
    store = HypothesisStore()
    sealed = seal_and_save(updated, store)
    _drop_draft(body.hypothesis_id)
    return sealed.model_dump()


@router.post("/experiments/run")
def run_experiment(
    body: RunIn,
    user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    if body.memory_hit_id:
        meta = _load_memory_hit(body.memory_hit_id)
        if meta and meta.get("block_rerun") and not body.force_despite_duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EXACT_DUPLICATE",
                    "message": "完全相同实验已存在。请查看历史或 REPRODUCE；强制重跑需 force_despite_duplicate=true。",
                },
            )
    store = HypothesisStore()
    contract = store.get_latest(body.hypothesis_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="sealed hypothesis not found")
    pred = UserPrediction(
        hypothesis_id=body.hypothesis_id,
        predicted_direction=body.predicted_direction,
        predicted_strength=body.predicted_strength,
        notes=body.notes,
    )
    result = run_gym_experiment(contract, pred, store=store)
    if body.memory_hit_id:
        check = memory_check(contract.research_question)
        append_hit_ledger(
            idea=contract.research_question,
            check=check,
            hypothesis_id=contract.hypothesis_id,
            user_decision="continue",
            experiment_executed=True,
            eventual_result=result.status,
        )
    from engine.factor_gym.acceptance import novice_status_label, save_feedback

    return {
        "status": result.status,
        "status_label": novice_status_label(result.status),
        "why": result.why,
        "next_best_action": result.next_best_action,
        "primary_failure": result.primary_failure,
        "experiment_id": result.experiment_id,
        "hypothesis_id": result.hypothesis_id,
        "save_feedback": save_feedback(result.status),
        "rule_plain": "系统已把你的想法转换成可测试规则。",
        "metrics_folded": result.metrics_folded,
        "author_user_id": str(user.id),
        "reproduce_hint": "如需复现，可在专业数据中使用 reproduce。",
    }


class EventIn(BaseModel):
    event: str
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/events")
def api_events(
    body: EventIn,
    user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    """First Value telemetry (result_acknowledged, second_experiment_started, …)."""
    from engine.factor_gym.telemetry import EVENT_NAMES, emit as emit_telemetry

    allowed = set(EVENT_NAMES) | {"hypothesis_created", "factor_gym_test_entry_opened"}
    if body.event not in allowed:
        raise HTTPException(status_code=400, detail="unknown event")
    payload = {**body.payload, "user_id": str(user.id)}
    emit_telemetry(body.event, payload)
    return {"ok": True, "event": body.event}


@router.post("/reproduce")
def api_reproduce(
    body: ReproduceIn,
    _user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    return reproduce_from_ir_dict(body.ir, seed=body.seed)


@router.get("/vault")
def api_vault_list(_user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    """Factor Vault v0 — list latest factor identities (asset surface)."""
    from engine.factor_gym.hypothesis import HypothesisStore
    from engine.factor_registry import FactorRegistry
    from engine.factor_vault import vault_list

    root = HypothesisStore().root
    reg = FactorRegistry(root / "factor_registry.jsonl")
    cards = vault_list(registry=reg, gym_root=root)
    # Hide IR blobs in list view
    slim = [{k: v for k, v in c.items() if k != "factor_ir"} for c in cards]
    return {"items": slim, "count": len(slim)}


@router.get("/vault/{factor_id}")
def api_vault_get(
    factor_id: str,
    _user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    from engine.factor_gym.hypothesis import HypothesisStore
    from engine.factor_registry import FactorRegistry
    from engine.factor_vault import vault_get

    root = HypothesisStore().root
    reg = FactorRegistry(root / "factor_registry.jsonl")
    card = vault_get(factor_id, registry=reg, gym_root=root)
    if card is None:
        raise HTTPException(status_code=404, detail="factor not found")
    return card


@router.post("/vault/{factor_id}/reproduce")
def api_vault_reproduce(
    factor_id: str,
    _user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    from engine.factor_gym.hypothesis import HypothesisStore
    from engine.factor_registry import FactorRegistry
    from engine.factor_vault import vault_reproduce

    root = HypothesisStore().root
    reg = FactorRegistry(root / "factor_registry.jsonl")
    try:
        return vault_reproduce(factor_id, registry=reg, gym_root=root)
    except KeyError:
        raise HTTPException(status_code=404, detail="factor not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/vault/{factor_id}/revalidate")
def api_vault_revalidate(
    factor_id: str,
    _user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    """REVALIDATION_BRANCH — new experiment evidence + new version; never overwrite."""
    from engine.factor_gym.hypothesis import HypothesisStore
    from engine.factor_registry import FactorRegistry
    from engine.factor_vault import vault_revalidate

    root = HypothesisStore().root
    reg = FactorRegistry(root / "factor_registry.jsonl")
    try:
        return vault_revalidate(factor_id, registry=reg, gym_root=root)
    except KeyError:
        raise HTTPException(status_code=404, detail="factor not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/vault/{factor_id}/lineage")
def api_vault_lineage(
    factor_id: str,
    _user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    from engine.factor_gym.hypothesis import HypothesisStore
    from engine.factor_registry import FactorRegistry
    from engine.factor_vault import vault_lineage

    root = HypothesisStore().root
    reg = FactorRegistry(root / "factor_registry.jsonl")
    rows = vault_lineage(factor_id, registry=reg, gym_root=root)
    slim = [{k: v for k, v in r.items() if k != "factor_ir"} for r in rows]
    return {"factor_id": factor_id, "versions": slim, "count": len(slim)}


@router.get("/vault-graveyard")
def api_vault_graveyard(_user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    """Failed factors remain queryable (identity never deleted)."""
    from engine.factor_gym.hypothesis import HypothesisStore
    from engine.factor_registry import FactorRegistry
    from engine.factor_vault import vault_failed

    root = HypothesisStore().root
    reg = FactorRegistry(root / "factor_registry.jsonl")
    items = vault_failed(registry=reg, gym_root=root)
    slim = [{k: v for k, v in c.items() if k != "factor_ir"} for c in items]
    return {"items": slim, "count": len(slim)}


@router.get("/human-sessions/template")
def api_human_session_template(_user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    """Observer clipboard template — QF-11A (no teaching)."""
    from engine.factor_gym.human_session import observer_template

    return {"template": observer_template(), "brief": "请用这个工具研究一个你觉得市场上可能存在的规律。"}


@router.get("/human-sessions/aggregate")
def api_human_session_aggregate(_user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    """Real-human evidence aggregate — never invents samples."""
    from engine.factor_gym.human_session import aggregate_human_evidence, load_sessions

    return aggregate_human_evidence(load_sessions())


@router.get("/human-sessions/pattern-analysis")
def api_human_pattern_analysis(_user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    """REAL_HUMAN_PATTERN_ANALYSIS — aggregate before any UX fix."""
    from engine.factor_gym.human_session import load_sessions
    from engine.factor_gym.pattern_analysis import analyze_human_patterns

    return analyze_human_patterns(load_sessions())


@router.post("/human-sessions")
def api_human_session_append(
    body: dict[str, Any],
    _user: Annotated[User, Depends(get_current_user)],
    _access: GymAccess,
) -> dict[str, Any]:
    """Append one observed real-human session (Owner/observer only in practice)."""
    from engine.factor_gym.human_session import HumanSession, append_session, gate_checks

    session = HumanSession.model_validate(body)
    saved = append_session(session)
    return {
        "session": saved.model_dump(),
        "gate": gate_checks(saved),
        "REAL_SESSION_FIRST_VALUE": saved.real_session_first_value,
    }
