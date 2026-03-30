from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mlops_forecasting.config import settings
from mlops_forecasting.data import (
    ingest_from_csv,
    ingest_from_http,
    ingest_from_postgres,
    persist_ingested,
)
from mlops_forecasting.telemetry import record_artifacts_created, record_task_result


def run_ingestion() -> dict:
    source = settings.data_source_type.lower()

    if source == "csv":
        df = ingest_from_csv(
            settings.data_source_uri,
            settings.data_source_timestamp_field,
            settings.data_source_target_field,
        )
    elif source == "http":
        df = ingest_from_http(
            settings.data_source_uri,
            settings.data_source_api_timestamp_key,
            settings.data_source_api_target_key,
        )
    elif source in {"postgres", "postgresql"}:
        df = ingest_from_postgres(
            settings.database_url,
            settings.data_source_table,
            settings.data_source_query,
            settings.data_source_timestamp_field,
            settings.data_source_target_field,
        )
    else:
        raise ValueError(f"Unsupported DATA_SOURCE_TYPE: {settings.data_source_type}")

    out = persist_ingested(df, settings.data_path)
    return {"rows": int(len(df)), "output_path": out, "source": source}


if __name__ == "__main__":
    task_name = os.getenv("TASK_NAME", "ingest_data")
    run_id = os.getenv("RUN_ID", "")
    try:
        result = run_ingestion()
        record_artifacts_created(run_id, count=1)
        record_task_result(run_id, task_name, success=True)
        print(result)
    except Exception:
        record_task_result(run_id, task_name, success=False)
        raise
