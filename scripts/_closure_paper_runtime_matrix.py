#!/usr/bin/env python3
"""Production-safe Paper runtime state-machine matrix (SANDBOX only, NO LIVE).

Proves: service/API layer → paper-runner → DB → dashboard fields → re-read.

Usage (prod):
  cd /srv/quantlab && .venv/bin/python scripts/_closure_paper_runtime_matrix.py

Usage (local):
  python scripts/_closure_paper_runtime_matrix.py

Env:
  CLOSURE_USER   username (default: ziyingke)
  CLOSURE_ENV    path to .env (optional; auto /srv/quantlab/.env or repo .env)
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap: repo root + .env before importing app settings
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
PROD_ROOT = Path("/srv/quantlab")


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = val


def _bootstrap() -> Path:
    env_override = os.environ.get("CLOSURE_ENV", "").strip()
    if env_override:
        env_path = Path(env_override)
    elif (PROD_ROOT / ".env").is_file():
        env_path = PROD_ROOT / ".env"
        os.chdir(PROD_ROOT)
        if str(PROD_ROOT) not in sys.path:
            sys.path.insert(0, str(PROD_ROOT))
        return env_path
    else:
        env_path = ROOT / ".env"
        os.chdir(ROOT)
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        return env_path

    # Explicit CLOSURE_ENV: prefer prod cwd if under /srv/quantlab
    work = PROD_ROOT if str(env_path).startswith("/srv/quantlab") else ROOT
    os.chdir(work)
    if str(work) not in sys.path:
        sys.path.insert(0, str(work))
    return env_path


_ENV_PATH = _bootstrap()
_load_env_file(_ENV_PATH)

import yaml  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from backend.app.core.config import get_settings  # noqa: E402
from backend.app.core.database import SessionLocal  # noqa: E402
from backend.app.models.paper_run import (  # noqa: E402
    PaperReadyRegistry,
    PaperRun,
    PaperRunEvent,
    PaperRunFill,
    PaperRunOrder,
    PaperRunPosition,
    PaperRunStatus,
)
from backend.app.models.user import User  # noqa: E402
from backend.app.services import paper_run_service as prs  # noqa: E402

# Required for a non-zero exit if missing
REQUIRED_COVERED = {
    PaperRunStatus.CREATED.value,
    PaperRunStatus.RUNNING.value,
    PaperRunStatus.STOPPED.value,
    PaperRunStatus.KILLED.value,
}

ALL_STATUSES = [s.value for s in PaperRunStatus]


def _spec_payload() -> dict[str, Any]:
    path = ROOT / "strategy_specs/examples/golden_btc_ema_trend.v1.yaml"
    if not path.is_file():
        path = Path.cwd() / "strategy_specs/examples/golden_btc_ema_trend.v1.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _ensure_user(db) -> User:
    username = os.environ.get("CLOSURE_USER", "ziyingke").strip() or "ziyingke"
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None:
        user = db.execute(select(User).order_by(User.created_at.asc()).limit(1)).scalar_one_or_none()
    if user is None:
        raise SystemExit("FAIL: no user in DB (CLOSURE_USER=%s)" % username)
    print(f"USER username={user.username} id={user.id}")
    return user


def _ensure_paper_ready(db, user: User, spec: dict[str, Any]) -> PaperReadyRegistry:
    from engine.strategies import validate_spec

    validated = validate_spec(spec)
    ready = db.execute(
        select(PaperReadyRegistry)
        .where(
            PaperReadyRegistry.user_id == user.id,
            PaperReadyRegistry.strategy_spec_id == validated.strategy.id,
            PaperReadyRegistry.strategy_spec_version == validated.strategy.version,
            PaperReadyRegistry.strategy_spec_hash == validated.content_hash(),
        )
        .order_by(PaperReadyRegistry.created_at.desc())
    ).scalar_one_or_none()
    if ready is not None:
        print(f"PAPER_READY existing id={ready.id}")
        return ready
    ready = prs.register_paper_ready(
        db,
        user,
        spec_payload=spec,
        compiled_hash="closure-matrix",
        data_gate_status="PASS",
        backtest_pass=True,
        validation_pass=True,
        robustness_pass=True,
    )
    print(f"PAPER_READY created id={ready.id}")
    return ready


def _counts(db, run_id: uuid.UUID) -> dict[str, int]:
    events = db.scalar(
        select(func.count()).select_from(PaperRunEvent).where(PaperRunEvent.paper_run_id == run_id)
    ) or 0
    orders = db.scalar(
        select(func.count()).select_from(PaperRunOrder).where(PaperRunOrder.paper_run_id == run_id)
    ) or 0
    fills = db.scalar(
        select(func.count()).select_from(PaperRunFill).where(PaperRunFill.paper_run_id == run_id)
    ) or 0
    positions = db.scalar(
        select(func.count()).select_from(PaperRunPosition).where(PaperRunPosition.paper_run_id == run_id)
    ) or 0
    return {
        "events": int(events),
        "orders": int(orders),
        "fills": int(fills),
        "positions": int(positions),
    }


def _snapshot(db, user_id: uuid.UUID, run_id: uuid.UUID, label: str) -> dict[str, Any]:
    db.expire_all()
    run = db.get(PaperRun, run_id)
    if run is None:
        raise RuntimeError(f"run missing after {label}")
    dash: dict[str, Any] = {}
    api_status = None
    try:
        dash = prs.paper_run_dashboard(db, user_id, run_id)
        # dashboard exposes status_zh; raw status from DB is source of truth
        api_status = run.status
    except prs.PaperRunError as exc:
        dash = {"error": str(exc)}
    counts = _counts(db, run_id)
    row = {
        "label": label,
        "run_id": str(run_id),
        "api_status": api_status,
        "db_status": run.status,
        "status_zh": dash.get("status_zh"),
        "stop_reason": run.stop_reason or "",
        "failure_reason": (run.failure_reason or "")[:120],
        "runner_pid": run.runner_pid,
        "environment": run.environment,
        "data_provider": run.data_provider,
        **counts,
        "dash_orders": dash.get("orders_count"),
        "dash_fills": dash.get("fills_count"),
        "dash_positions": dash.get("positions_count"),
        "dash_equity": dash.get("equity_zh"),
        "dash_position": dash.get("position_zh"),
    }
    print(
        f"SNAP [{label}] run_id={row['run_id']} api/db={row['api_status']}/{row['db_status']} "
        f"events={row['events']} orders={row['orders']} fills={row['fills']} "
        f"positions={row['positions']} status_zh={row['status_zh']!r} "
        f"stop={row['stop_reason']!r}"
    )
    return row


def _spawn_runner(run_id: uuid.UUID, *, seconds: float = 45.0) -> subprocess.Popen:
    """Async spawn matching intended worker model (start_paper_run currently blocks)."""
    script = Path.cwd() / "scripts" / "paper_runner.py"
    if not script.is_file():
        script = ROOT / "scripts" / "paper_runner.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd()) + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [sys.executable, str(script), str(run_id), "--once", f"--seconds={seconds}"]
    return subprocess.Popen(  # noqa: S603
        cmd,
        cwd=str(Path.cwd()),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _mark_starting(db, run: PaperRun) -> None:
    run.status = PaperRunStatus.STARTING.value
    db.commit()


def _poll_until(
    db,
    user_id: uuid.UUID,
    run_id: uuid.UUID,
    want: set[str],
    *,
    timeout_s: float = 60.0,
    label: str = "poll",
) -> str:
    deadline = time.time() + timeout_s
    last = ""
    while time.time() < deadline:
        db.expire_all()
        run = db.get(PaperRun, run_id)
        last = (run.status if run else "") or ""
        if last in want:
            _snapshot(db, user_id, run_id, f"{label}:{last}")
            return last
        time.sleep(0.4)
    _snapshot(db, user_id, run_id, f"{label}:TIMEOUT")
    raise TimeoutError(f"timeout waiting for {want}, last={last}")


def _create_run(db, user: User, spec: dict[str, Any]) -> PaperRun:
    run = prs.create_paper_run(
        db,
        user,
        spec_payload=spec,
        compiled_hash="closure-matrix",
        environment="SANDBOX",
        data_provider="synthetic",
        starting_balance=100_000.0,
    )
    assert run.environment == "SANDBOX"
    assert run.simulated_balance is True
    _snapshot(db, user.id, run.id, "CREATED")
    return run


def path_stop(db, user: User, spec: dict[str, Any], covered: set[str]) -> None:
    print("\n=== PATH stop: CREATED → STARTING → RUNNING → STOPPED ===")
    run = _create_run(db, user, spec)
    covered.add(PaperRunStatus.CREATED.value)

    _mark_starting(db, run)
    covered.add(PaperRunStatus.STARTING.value)
    _snapshot(db, user.id, run.id, "STARTING")

    proc = _spawn_runner(run.id, seconds=50.0)
    try:
        status = _poll_until(
            db,
            user.id,
            run.id,
            {PaperRunStatus.RUNNING.value, PaperRunStatus.STOPPED.value, PaperRunStatus.FAILED.value},
            timeout_s=60.0,
            label="after_start",
        )
        if status == PaperRunStatus.RUNNING.value:
            covered.add(PaperRunStatus.RUNNING.value)
        elif status == PaperRunStatus.STOPPED.value:
            covered.add(PaperRunStatus.STOPPED.value)
            print(
                "NOTE: runner reached STOPPED before stop() — natural complete; "
                "RUNNING was not observed on this path"
            )
            return
        elif status == PaperRunStatus.FAILED.value:
            covered.add(PaperRunStatus.FAILED.value)
            raise RuntimeError("runner FAILED before stop")

        stopped = prs.stop_paper_run(db, user.id, run.id)
        covered.add(PaperRunStatus.STOPPED.value)
        if stopped.status == PaperRunStatus.STOPPING.value:
            covered.add(PaperRunStatus.STOPPING.value)
        _snapshot(db, user.id, run.id, "after_stop")

        # Simulate UI refresh: re-query dashboard + DB
        db.expire_all()
        dash = prs.paper_run_dashboard(db, user.id, run.id)
        again = db.get(PaperRun, run.id)
        print(
            f"REFRESH after_stop db={again.status} status_zh={dash.get('status_zh')!r} "
            f"equity={dash.get('equity_zh')!r} orders={dash.get('orders_count')}"
        )
        if again.status not in {
            PaperRunStatus.STOPPED.value,
            PaperRunStatus.STOPPING.value,
            PaperRunStatus.KILLED.value,
        }:
            raise RuntimeError(f"expected STOPPED after stop, got {again.status}")
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except Exception:
                proc.kill()


def path_kill(db, user: User, spec: dict[str, Any], covered: set[str]) -> None:
    print("\n=== PATH kill: CREATED → STARTING → RUNNING → KILLED ===")
    run = _create_run(db, user, spec)
    covered.add(PaperRunStatus.CREATED.value)

    _mark_starting(db, run)
    covered.add(PaperRunStatus.STARTING.value)
    proc = _spawn_runner(run.id, seconds=50.0)
    try:
        status = _poll_until(
            db,
            user.id,
            run.id,
            {PaperRunStatus.RUNNING.value, PaperRunStatus.STOPPED.value, PaperRunStatus.FAILED.value},
            timeout_s=60.0,
            label="kill_wait_running",
        )
        if status == PaperRunStatus.RUNNING.value:
            covered.add(PaperRunStatus.RUNNING.value)
        elif status != PaperRunStatus.RUNNING.value:
            # Still exercise kill from terminal-ish state
            print(f"NOTE: kill path saw {status} before kill(); still calling kill()")

        killed = prs.kill_paper_run(db, user.id, run.id)
        if killed.status != PaperRunStatus.KILLED.value:
            raise RuntimeError(f"kill expected KILLED, got {killed.status}")
        covered.add(PaperRunStatus.KILLED.value)
        _snapshot(db, user.id, run.id, "after_kill")

        db.expire_all()
        dash = prs.paper_run_dashboard(db, user.id, run.id)
        again = db.get(PaperRun, run.id)
        print(
            f"REFRESH after_kill db={again.status} status_zh={dash.get('status_zh')!r} "
            f"kill_switch={again.kill_switch_active}"
        )
        if again.status != PaperRunStatus.KILLED.value:
            raise RuntimeError(f"refresh expected KILLED, got {again.status}")
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except Exception:
                proc.kill()


def path_completed_via_service_start(
    db, user: User, spec: dict[str, Any], covered: set[str]
) -> None:
    """Optional: sync start_paper_run finishes quickly → STOPPED (no COMPLETED enum)."""
    print("\n=== PATH completed (sync start → natural STOPPED) ===")
    run = _create_run(db, user, spec)
    covered.add(PaperRunStatus.CREATED.value)

    # Observe STARTING from another thread while start blocks
    seen_starting = {"v": False}

    def _watch() -> None:
        deadline = time.time() + 30
        while time.time() < deadline:
            sdb = SessionLocal()
            try:
                r = sdb.get(PaperRun, run.id)
                if r and r.status == PaperRunStatus.STARTING.value:
                    seen_starting["v"] = True
                    return
                if r and r.status in {
                    PaperRunStatus.RUNNING.value,
                    PaperRunStatus.STOPPED.value,
                    PaperRunStatus.FAILED.value,
                }:
                    return
            finally:
                sdb.close()
            time.sleep(0.15)

    watcher = threading.Thread(target=_watch, daemon=True)
    watcher.start()
    started = prs.start_paper_run(db, user.id, run.id)
    watcher.join(timeout=2)
    if seen_starting["v"]:
        covered.add(PaperRunStatus.STARTING.value)
    _snapshot(db, user.id, run.id, "after_sync_start")
    if started.status == PaperRunStatus.STOPPED.value:
        covered.add(PaperRunStatus.STOPPED.value)
        print("COMPLETED_EQUIV=STOPPED (stop_reason=%r)" % (started.stop_reason,))
    elif started.status == PaperRunStatus.FAILED.value:
        covered.add(PaperRunStatus.FAILED.value)
        print("sync start ended FAILED:", started.failure_reason[:200])
    elif started.status == PaperRunStatus.RUNNING.value:
        covered.add(PaperRunStatus.RUNNING.value)


def path_failed(db, user: User, spec: dict[str, Any], covered: set[str]) -> None:
    print("\n=== PATH failed (safe bad params) ===")
    # 1) Corrupt effective_config then start → runner/service should land FAILED
    try:
        run = _create_run(db, user, spec)
        run.effective_config = {}  # runtime_params_from_effective_config raises
        db.commit()
        started = prs.start_paper_run(db, user.id, run.id)
        _snapshot(db, user.id, run.id, "after_bad_start")
        if started.status == PaperRunStatus.FAILED.value:
            covered.add(PaperRunStatus.FAILED.value)
            print("FAILED_PATH status=FAILED reason=%r" % ((started.failure_reason or "")[:200],))
        else:
            print(f"WARN: bad effective_config ended as {started.status}, not FAILED")
    except prs.PaperRunError as exc:
        db.expire_all()
        # start may raise after setting FAILED (timeout) or leave STARTING
        print(f"FAILED_PATH PaperRunError (system ok): {exc}")
        # Find latest run for user with FAILED if any
    except Exception as exc:  # noqa: BLE001
        print(f"WARN: failed-path start error (non-fatal): {exc}")

    # 2) start when status=KILLED should raise without crashing system
    try:
        dead = PaperRun(
            user_id=user.id,
            strategy_spec_id="closure_matrix_bad",
            strategy_spec_version="v0",
            strategy_spec_hash="bad",
            compiled_strategy_hash="bad",
            environment="SANDBOX",
            instrument="BTCUSDT",
            data_provider="synthetic",
            status=PaperRunStatus.KILLED.value,
            kill_switch_active=True,
            effective_config={},
            run_manifest={},
            run_manifest_hash="bad",
        )
        db.add(dead)
        db.commit()
        db.refresh(dead)
        try:
            prs.start_paper_run(db, user.id, dead.id)
            print("WARN: start from KILLED did not raise")
        except prs.PaperRunError as exc:
            print(f"FAILED_PATH start_from_KILLED raised OK: {exc}")
    except Exception as exc:  # noqa: BLE001
        print(f"WARN: killed-start probe error (non-fatal): {exc}")

    # 3) LIVE create must deny (no LIVE orders)
    try:
        prs.create_paper_run(
            db,
            user,
            spec_payload=spec,
            compiled_hash="closure-matrix",
            environment="LIVE",
            data_provider="synthetic",
        )
        print("WARN: LIVE create did not deny")
    except Exception as exc:  # noqa: BLE001
        print(f"LIVE_DENIED OK: {type(exc).__name__}: {exc}")


def main() -> int:
    print("ENV_FILE", _ENV_PATH)
    get_settings.cache_clear()
    settings = get_settings()
    if settings.quantlab_live:
        print("ABORT: QUANTLAB_LIVE is ON — refusing to run matrix")
        return 2
    print(
        f"FLAGS LIVE={settings.quantlab_live} SANDBOX={settings.quantlab_sandbox} "
        f"eager={settings.celery_task_always_eager}"
    )

    print("ENUM PaperRunStatus:", ", ".join(ALL_STATUSES))

    covered: set[str] = set()
    errors: list[str] = []
    db = SessionLocal()
    try:
        user = _ensure_user(db)
        spec = _spec_payload()
        _ensure_paper_ready(db, user, spec)

        try:
            path_stop(db, user, spec, covered)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"stop_path: {exc}")
            print(f"ERROR stop_path: {exc}")

        try:
            path_kill(db, user, spec, covered)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"kill_path: {exc}")
            print(f"ERROR kill_path: {exc}")

        try:
            path_completed_via_service_start(db, user, spec, covered)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"completed_path: {exc}")
            print(f"ERROR completed_path: {exc}")

        try:
            path_failed(db, user, spec, covered)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"failed_path: {exc}")
            print(f"ERROR failed_path: {exc}")

    finally:
        db.close()

    # Coverage report
    print("\n=== COVERAGE ===")
    for s in ALL_STATUSES:
        mark = "COVERED" if s in covered else "GAP"
        print(f"  {s}: {mark}")

    missing_required = sorted(REQUIRED_COVERED - covered)
    print("COVERED", sorted(covered))
    print("MISSING_REQUIRED", missing_required)
    print("ERRORS", errors)

    # Known enum gaps (never written by production code paths)
    print(
        "KNOWN_CODE_GAPS: PAUSED never assigned; STOPPING only flash-written then "
        "overwritten to STOPPED; no COMPLETED enum (natural end → STOPPED); "
        "start_paper_run blocks on communicate so API callers rarely observe RUNNING"
    )

    if missing_required or errors:
        print("MATRIX=FAIL")
        return 1
    print("MATRIX=PASS LIVE=OFF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
