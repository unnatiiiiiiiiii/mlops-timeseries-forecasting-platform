from datetime import datetime, timedelta
import json

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import ShortCircuitOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator


PROJECT_DIR = "/opt/airflow/project"
BASE_PYTHON = "/usr/local/bin/python"
PYTHON_BIN = "/opt/airflow/mlenv/bin/python"
BOOTSTRAP_VENV = (
    f"if [ ! -x {PYTHON_BIN} ] || ! {PYTHON_BIN} -c 'import pandas' >/dev/null 2>&1; then "
    f"{BASE_PYTHON} -m venv /opt/airflow/mlenv && "
    "/opt/airflow/mlenv/bin/python -m pip install --upgrade pip && "
    "/opt/airflow/mlenv/bin/pip install -r /opt/airflow/project/requirements.api.txt; "
    "fi"
)


TASK_ENV = {
    "PYTHONPATH": f"{PROJECT_DIR}/src",
    "MLFLOW_TRACKING_URI": "http://mlflow:5000",
    "RUN_ID": "{{ run_id }}",
    "DATA_PATH": "data/raw/timeseries.csv",
    "TELEMETRY_STATE_PATH": "monitoring/telemetry_state.json",
    "TASK_NAME": "run_drift_check",
}


def _should_trigger_retrain(**context) -> bool:
    payload_raw = context["ti"].xcom_pull(task_ids="check_data_drift")
    if not payload_raw:
        print("Drift monitor: no payload returned by check_data_drift")
        return False

    try:
        payload = json.loads(payload_raw)
    except json.JSONDecodeError:
        print(f"Drift monitor: invalid JSON payload: {payload_raw}")
        return False

    detected = bool(payload.get("drift_detected", False))
    print(f"Drift monitor decision: drift_detected={detected} payload={payload}")
    return detected


with DAG(
    dag_id="drift_monitor_trigger_dag",
    description="Monitors drift and auto-triggers forecasting retrain DAG",
    start_date=datetime(2025, 1, 1),
    schedule="@hourly",
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "mlops", "retries": 1, "retry_delay": timedelta(minutes=5)},
    tags=["forecasting", "mlops", "drift", "autonomous"],
) as dag:
    check_data_drift = BashOperator(
        task_id="check_data_drift",
        bash_command=f"cd {PROJECT_DIR} && {BOOTSTRAP_VENV} && {PYTHON_BIN} scripts/run_drift_check.py",
        env=TASK_ENV,
        append_env=True,
        do_xcom_push=True,
    )

    drift_gate = ShortCircuitOperator(
        task_id="drift_detected_gate",
        python_callable=_should_trigger_retrain,
    )

    trigger_retrain = TriggerDagRunOperator(
        task_id="trigger_forecasting_retrain",
        trigger_dag_id="forecasting_retrain_dag",
        conf={"trigger_reason": "data_drift_detected"},
        wait_for_completion=False,
        reset_dag_run=False,
    )

    check_data_drift >> drift_gate >> trigger_retrain
