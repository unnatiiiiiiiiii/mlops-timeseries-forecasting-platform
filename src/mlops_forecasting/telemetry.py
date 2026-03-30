from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import time

from mlops_forecasting.config import settings


def ensure_path(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _lock_path() -> str:
    return f"{settings.telemetry_state_path}.lock"


def _acquire_lock(timeout_seconds: float = 10.0, poll_seconds: float = 0.1) -> int:
    ensure_path(_lock_path())
    start = time.time()
    while True:
        try:
            return os.open(_lock_path(), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if (time.time() - start) >= timeout_seconds:
                raise TimeoutError("Timeout acquiring telemetry state lock")
            time.sleep(poll_seconds)


def _release_lock(fd: int) -> None:
    try:
        os.close(fd)
    finally:
        try:
            Path(_lock_path()).unlink(missing_ok=True)
        except Exception:
            pass


def _default_state() -> dict:
    return {
        "promotion_lock_wait_seconds_sum": 0.0,
        "promotion_lock_wait_seconds_count": 0,
        "promotion_lock_acquired_total": 0,
        "promotion_lock_timeout_total": 0,
        "runs": {},
    }


def _load_state_unlocked() -> dict:
    path = Path(settings.telemetry_state_path)
    if not path.exists():
        return _default_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _default_state()

    base = _default_state()
    keys = (
        "promotion_lock_wait_seconds_sum",
        "promotion_lock_wait_seconds_count",
        "promotion_lock_acquired_total",
        "promotion_lock_timeout_total",
    )
    for k in keys:
        if k in data:
            base[k] = data[k]
    base["runs"] = data.get("runs", {}) if isinstance(data.get("runs", {}), dict) else {}
    return base


def _save_state_unlocked(state: dict) -> None:
    ensure_path(settings.telemetry_state_path)
    Path(settings.telemetry_state_path).write_text(json.dumps(state, indent=2), encoding="utf-8")


def _with_state(mutator) -> None:
    fd = _acquire_lock()
    try:
        state = _load_state_unlocked()
        mutator(state)
        _save_state_unlocked(state)
    finally:
        _release_lock(fd)


def _ensure_run(state: dict, run_id: str) -> dict:
    runs = state.setdefault("runs", {})
    return runs.setdefault(
        run_id,
        {
            "started_at": _now_iso(),
            "ended_at": None,
            "run_duration_seconds": 0.0,
            "tasks_success_total": 0,
            "tasks_failed_total": 0,
            "artifacts_created_total": 0,
            "model_rmse": None,
            "model_mae": None,
            "model_mape": None,
            "forecast_accuracy_percent": None,
            "model_impact_percent": None,
            "model_version_promoted": None,
        },
    )


def record_promotion_lock(wait_seconds: float, acquired: bool, timeout: bool) -> None:
    def mutator(state: dict) -> None:
        state["promotion_lock_wait_seconds_sum"] = float(state.get("promotion_lock_wait_seconds_sum", 0.0)) + float(wait_seconds)
        state["promotion_lock_wait_seconds_count"] = int(state.get("promotion_lock_wait_seconds_count", 0)) + 1
        if acquired:
            state["promotion_lock_acquired_total"] = int(state.get("promotion_lock_acquired_total", 0)) + 1
        if timeout:
            state["promotion_lock_timeout_total"] = int(state.get("promotion_lock_timeout_total", 0)) + 1

    _with_state(mutator)


def record_task_result(run_id: str, task_name: str, success: bool) -> None:
    if not run_id:
        return

    def mutator(state: dict) -> None:
        run = _ensure_run(state, run_id)
        if success:
            run["tasks_success_total"] = int(run.get("tasks_success_total", 0)) + 1
        else:
            run["tasks_failed_total"] = int(run.get("tasks_failed_total", 0)) + 1

        if success and task_name == "apply_canary_action":
            run["ended_at"] = _now_iso()
            start_dt = _parse_iso(run.get("started_at"))
            end_dt = _parse_iso(run.get("ended_at"))
            if start_dt and end_dt:
                run["run_duration_seconds"] = max((end_dt - start_dt).total_seconds(), 0.0)

    _with_state(mutator)


def record_artifacts_created(run_id: str, count: int = 1) -> None:
    if not run_id:
        return

    def mutator(state: dict) -> None:
        run = _ensure_run(state, run_id)
        run["artifacts_created_total"] = int(run.get("artifacts_created_total", 0)) + int(count)

    _with_state(mutator)


def record_model_metrics(run_id: str, rmse: float, mae: float, mape: float, model_version: str) -> None:
    if not run_id:
        return

    def mutator(state: dict) -> None:
        run = _ensure_run(state, run_id)
        run["model_rmse"] = float(rmse)
        run["model_mae"] = float(mae)
        run["model_mape"] = float(mape)
        run["forecast_accuracy_percent"] = max(0.0, 100.0 - float(mape))
        run["model_version_promoted"] = str(model_version)

    _with_state(mutator)


def record_business_kpis(run_id: str, forecast_accuracy_percent: float, model_impact_percent: float) -> None:
    if not run_id:
        return

    def mutator(state: dict) -> None:
        run = _ensure_run(state, run_id)
        run["forecast_accuracy_percent"] = float(forecast_accuracy_percent)
        run["model_impact_percent"] = float(model_impact_percent)

    _with_state(mutator)


def render_prometheus_metrics() -> str:
    state = _load_state_unlocked()
    lines: list[str] = []

    lines.append("# HELP promotion_lock_wait_seconds Time waiting for promotion lock")
    lines.append("# TYPE promotion_lock_wait_seconds summary")
    lines.append(f"promotion_lock_wait_seconds_sum {float(state.get('promotion_lock_wait_seconds_sum', 0.0))}")
    lines.append(f"promotion_lock_wait_seconds_count {int(state.get('promotion_lock_wait_seconds_count', 0))}")

    lines.append("# HELP promotion_lock_acquired_total Lock acquired count")
    lines.append("# TYPE promotion_lock_acquired_total counter")
    lines.append(f"promotion_lock_acquired_total {int(state.get('promotion_lock_acquired_total', 0))}")

    lines.append("# HELP promotion_lock_timeout_total Lock timeout count")
    lines.append("# TYPE promotion_lock_timeout_total counter")
    lines.append(f"promotion_lock_timeout_total {int(state.get('promotion_lock_timeout_total', 0))}")

    lines.append("# HELP run_duration_seconds Run duration in seconds")
    lines.append("# TYPE run_duration_seconds gauge")
    lines.append("# HELP tasks_success_total Successful tasks per run")
    lines.append("# TYPE tasks_success_total gauge")
    lines.append("# HELP tasks_failed_total Failed tasks per run")
    lines.append("# TYPE tasks_failed_total gauge")
    lines.append("# HELP artifacts_created_total Artifacts created per run")
    lines.append("# TYPE artifacts_created_total gauge")
    lines.append("# HELP model_rmse Model RMSE per run")
    lines.append("# TYPE model_rmse gauge")
    lines.append("# HELP model_mae Model MAE per run")
    lines.append("# TYPE model_mae gauge")
    lines.append("# HELP model_mape Model MAPE per run")
    lines.append("# TYPE model_mape gauge")
    lines.append("# HELP forecast_accuracy_percent Forecast accuracy (100 - MAPE)")
    lines.append("# TYPE forecast_accuracy_percent gauge")
    lines.append("# HELP model_impact_percent Relative canary impact vs stable MAPE")
    lines.append("# TYPE model_impact_percent gauge")
    lines.append("# HELP model_version_promoted Promoted model version marker")
    lines.append("# TYPE model_version_promoted gauge")

    runs = state.get("runs", {})
    for run_id, run in runs.items():
        safe_run = str(run_id).replace('"', '\\"')
        lines.append(f"run_duration_seconds{{run_id=\"{safe_run}\"}} {float(run.get('run_duration_seconds', 0.0) or 0.0)}")
        lines.append(f"tasks_success_total{{run_id=\"{safe_run}\"}} {int(run.get('tasks_success_total', 0) or 0)}")
        lines.append(f"tasks_failed_total{{run_id=\"{safe_run}\"}} {int(run.get('tasks_failed_total', 0) or 0)}")
        lines.append(f"artifacts_created_total{{run_id=\"{safe_run}\"}} {int(run.get('artifacts_created_total', 0) or 0)}")

        if run.get("model_rmse") is not None:
            lines.append(f"model_rmse{{run_id=\"{safe_run}\"}} {float(run['model_rmse'])}")
        if run.get("model_mae") is not None:
            lines.append(f"model_mae{{run_id=\"{safe_run}\"}} {float(run['model_mae'])}")
        if run.get("model_mape") is not None:
            lines.append(f"model_mape{{run_id=\"{safe_run}\"}} {float(run['model_mape'])}")
        if run.get("forecast_accuracy_percent") is not None:
            lines.append(f"forecast_accuracy_percent{{run_id=\"{safe_run}\"}} {float(run['forecast_accuracy_percent'])}")
        if run.get("model_impact_percent") is not None:
            lines.append(f"model_impact_percent{{run_id=\"{safe_run}\"}} {float(run['model_impact_percent'])}")

        version = run.get("model_version_promoted")
        if version not in (None, "", "unregistered"):
            safe_version = str(version).replace('"', '\\"')
            lines.append(f"model_version_promoted{{run_id=\"{safe_run}\",version=\"{safe_version}\"}} 1")

    return "\n".join(lines) + "\n"
