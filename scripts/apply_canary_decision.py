from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mlops_forecasting.config import settings
from mlops_forecasting.pipelines.canary_manager import evaluate_from_file
from mlops_forecasting.pipelines.rollout import build_rollout_commands, execute_rollout
from mlops_forecasting.telemetry import record_task_result


if __name__ == "__main__":
    task_name = os.getenv("TASK_NAME", "apply_canary_action")
    run_id = os.getenv("RUN_ID", "")
    try:
        decision = evaluate_from_file(settings.canary_metrics_path)
        namespace = os.getenv("K8S_NAMESPACE", "default")
        commands = build_rollout_commands(decision["decision"], namespace=namespace)

        if os.getenv("EXECUTE_ROLLOUT", "false").lower() == "true":
            payload = {"decision": decision, "actions": execute_rollout(commands)}
        else:
            payload = {"decision": decision, "planned_commands": [" ".join(c) for c in commands]}

        record_task_result(run_id, task_name, success=True)
        print(payload)
    except Exception:
        record_task_result(run_id, task_name, success=False)
        raise
