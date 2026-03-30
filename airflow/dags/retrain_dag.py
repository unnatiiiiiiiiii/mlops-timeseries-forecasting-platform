from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

from mlops_forecasting.alerts import send_slack_alert


default_args = {
    "owner": "mlops",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "execution_timeout": timedelta(minutes=45),
}


def _notify_failure(context):
    dag_id = context.get("dag").dag_id if context.get("dag") else "unknown_dag"
    task_id = context.get("task_instance").task_id if context.get("task_instance") else "unknown_task"
    run_id = context.get("run_id", "unknown_run")
    send_slack_alert(f"Airflow task failed: dag={dag_id} task={task_id} run_id={run_id}")


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
    "CANDIDATE_MODELS": "xgboost",
    "RUN_ID": "{{ run_id }}",
    "DATA_PATH": "data/runs/{{ run_id }}/timeseries.csv",
    "MODEL_FILE": "models/{{ run_id }}/latest_model.pkl",
    "PROMOTION_LOCK_FILE": "models/registry_promotion.lock",
    "TELEMETRY_STATE_PATH": "monitoring/telemetry_state.json",
}

with DAG(
    dag_id="forecasting_retrain_dag",
    default_args=default_args,
    description="Scheduled retraining pipeline for forecasting model",
    schedule="0 2 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=2,
    dagrun_timeout=timedelta(hours=2),
    tags=["forecasting", "mlops"],
    on_failure_callback=_notify_failure,
) as dag:
    ingest_data = BashOperator(
        task_id="ingest_data",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            f"{BOOTSTRAP_VENV} && "
            "DATA_SOURCE_URI=data/raw/timeseries.csv "
            "DATA_SOURCE_TIMESTAMP_FIELD=ds "
            "DATA_SOURCE_TARGET_FIELD=y "
            f"{PYTHON_BIN} scripts/ingest_data.py"
        ),
        env={**TASK_ENV, "TASK_NAME": "ingest_data"},
        append_env=True,
        max_active_tis_per_dag=2,
    )

    train_model = BashOperator(
        task_id="train_model",
        bash_command=f"cd {PROJECT_DIR} && {BOOTSTRAP_VENV} && {PYTHON_BIN} scripts/train_pipeline.py",
        env={**TASK_ENV, "TASK_NAME": "train_model"},
        append_env=True,
        max_active_tis_per_dag=1,
    )

    drift_check = BashOperator(
        task_id="run_drift_check",
        bash_command=f"cd {PROJECT_DIR} && {BOOTSTRAP_VENV} && {PYTHON_BIN} scripts/run_drift_check.py",
        env={**TASK_ENV, "TASK_NAME": "run_drift_check"},
        append_env=True,
        max_active_tis_per_dag=2,
    )

    canary_gate = BashOperator(
        task_id="canary_gate_decision",
        bash_command=f"cd {PROJECT_DIR} && {BOOTSTRAP_VENV} && {PYTHON_BIN} scripts/canary_decision.py",
        env={**TASK_ENV, "TASK_NAME": "canary_gate_decision"},
        append_env=True,
        max_active_tis_per_dag=1,
    )

    apply_canary_action = BashOperator(
        task_id="apply_canary_action",
        bash_command=f"cd {PROJECT_DIR} && {BOOTSTRAP_VENV} && {PYTHON_BIN} scripts/apply_canary_decision.py",
        env={**TASK_ENV, "TASK_NAME": "apply_canary_action", "EXECUTE_ROLLOUT": "false"},
        append_env=True,
        max_active_tis_per_dag=1,
    )

    ingest_data >> train_model >> drift_check >> canary_gate >> apply_canary_action
