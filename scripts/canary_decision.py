from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mlops_forecasting.config import settings
from mlops_forecasting.pipelines.canary_manager import evaluate_from_file
from mlops_forecasting.telemetry import record_business_kpis, record_task_result


def _compute_business_kpis(metrics_path: str) -> tuple[float, float]:
    payload = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
    stable_mape = float(payload["stable"]["mape"])
    canary_mape = float(payload["canary"]["mape"])

    forecast_accuracy_percent = max(0.0, 100.0 - canary_mape)
    if stable_mape == 0:
        model_impact_percent = 0.0
    else:
        model_impact_percent = ((stable_mape - canary_mape) / stable_mape) * 100.0

    return forecast_accuracy_percent, model_impact_percent


if __name__ == "__main__":
    task_name = os.getenv("TASK_NAME", "canary_gate_decision")
    run_id = os.getenv("RUN_ID", "")
    try:
        result = evaluate_from_file(settings.canary_metrics_path)
        accuracy, impact = _compute_business_kpis(settings.canary_metrics_path)
        record_business_kpis(run_id, forecast_accuracy_percent=accuracy, model_impact_percent=impact)
        record_task_result(run_id, task_name, success=True)
        print({**result, "forecast_accuracy_percent": round(accuracy, 4), "model_impact_percent": round(impact, 4)})
    except Exception:
        record_task_result(run_id, task_name, success=False)
        raise
