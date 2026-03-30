from datetime import UTC, datetime
import json
from pathlib import Path

from mlops_forecasting.config import settings


def _ratio_delta(canary_value: float, stable_value: float) -> float:
    if stable_value == 0:
        return 0.0
    return (canary_value - stable_value) / stable_value


def evaluate_canary(
    canary_error: float,
    stable_error: float,
    canary_latency_ms: float,
    stable_latency_ms: float,
    canary_requests: int,
) -> dict:
    error_delta = _ratio_delta(canary_error, stable_error)
    latency_delta = _ratio_delta(canary_latency_ms, stable_latency_ms)

    if canary_requests < settings.canary_min_requests:
        decision = "hold"
        reason = "insufficient_traffic"
    elif error_delta > settings.canary_max_error_delta:
        decision = "rollback"
        reason = "error_regression"
    elif latency_delta > settings.canary_max_latency_delta:
        decision = "rollback"
        reason = "latency_regression"
    else:
        decision = "promote"
        reason = "canary_healthy"

    return {
        "decision": decision,
        "reason": reason,
        "error_delta": round(error_delta, 4),
        "latency_delta": round(latency_delta, 4),
        "canary_requests": canary_requests,
        "checked_at": datetime.now(UTC).isoformat(),
    }


def evaluate_from_file(path: str) -> dict:
    payload = json.loads(Path(path).read_text())
    canary = payload["canary"]
    stable = payload["stable"]
    return evaluate_canary(
        canary_error=float(canary["mape"]),
        stable_error=float(stable["mape"]),
        canary_latency_ms=float(canary["p95_latency_ms"]),
        stable_latency_ms=float(stable["p95_latency_ms"]),
        canary_requests=int(canary["requests"]),
    )


if __name__ == "__main__":
    print(evaluate_from_file(settings.canary_metrics_path))
