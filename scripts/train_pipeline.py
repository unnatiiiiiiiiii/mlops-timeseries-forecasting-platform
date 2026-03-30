from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mlops_forecasting.telemetry import record_task_result
from mlops_forecasting.train import train_and_log


if __name__ == "__main__":
    task_name = os.getenv("TASK_NAME", "train_model")
    run_id = os.getenv("RUN_ID", "")
    try:
        result = train_and_log()
        record_task_result(run_id, task_name, success=True)
        print("Training completed:")
        print(result)
    except Exception:
        record_task_result(run_id, task_name, success=False)
        raise
