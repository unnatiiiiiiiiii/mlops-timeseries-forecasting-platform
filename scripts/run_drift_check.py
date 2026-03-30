from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mlops_forecasting.pipelines.retrain import run_drift_check
from mlops_forecasting.telemetry import record_task_result


if __name__ == "__main__":
    task_name = os.getenv("TASK_NAME", "run_drift_check")
    run_id = os.getenv("RUN_ID", "")
    try:
        result = run_drift_check()
        record_task_result(run_id, task_name, success=True)
        print(json.dumps(result))
    except Exception:
        record_task_result(run_id, task_name, success=False)
        raise
