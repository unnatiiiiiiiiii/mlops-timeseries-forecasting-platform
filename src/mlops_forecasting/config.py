from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "local")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow_experiment_name: str = os.getenv("MLFLOW_EXPERIMENT_NAME", "ts_forecasting")
    mlflow_registered_model_name: str = os.getenv("MLFLOW_REGISTERED_MODEL_NAME", "forecasting-model")
    mlflow_model_stage: str = os.getenv("MLFLOW_MODEL_STAGE", "Production")
    registry_refresh_seconds: int = int(os.getenv("REGISTRY_REFRESH_SECONDS", "60"))

    data_path: str = os.getenv("DATA_PATH", "data/raw/timeseries.csv")
    model_dir: str = os.getenv("MODEL_DIR", "models")
    model_file: str = os.getenv("MODEL_FILE", "models/latest_model.pkl")
    model_type: str = os.getenv("MODEL_TYPE", "xgboost")
    target_column: str = os.getenv("TARGET_COLUMN", "y")
    timestamp_column: str = os.getenv("TIMESTAMP_COLUMN", "ds")
    frequency: str = os.getenv("FREQUENCY", "D")
    forecast_horizon: int = int(os.getenv("FORECAST_HORIZON", "14"))

    data_source_type: str = os.getenv("DATA_SOURCE_TYPE", "csv")
    data_source_uri: str = os.getenv("DATA_SOURCE_URI", "data/raw/timeseries_input.csv")
    data_source_table: str = os.getenv("DATA_SOURCE_TABLE", "forecast_series")
    data_source_query: str = os.getenv("DATA_SOURCE_QUERY", "")
    data_source_timestamp_field: str = os.getenv("DATA_SOURCE_TIMESTAMP_FIELD", "ds")
    data_source_target_field: str = os.getenv("DATA_SOURCE_TARGET_FIELD", "y")
    data_source_api_timestamp_key: str = os.getenv("DATA_SOURCE_API_TIMESTAMP_KEY", "ds")
    data_source_api_target_key: str = os.getenv("DATA_SOURCE_API_TARGET_KEY", "y")

    candidate_models: str = os.getenv("CANDIDATE_MODELS", "xgboost,lightgbm,prophet")
    primary_metric: str = os.getenv("PRIMARY_METRIC", "rmse")

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./mlops.db")

    drift_threshold: float = float(os.getenv("DRIFT_THRESHOLD", "0.15"))
    canary_max_error_delta: float = float(os.getenv("CANARY_MAX_ERROR_DELTA", "0.1"))
    canary_max_latency_delta: float = float(os.getenv("CANARY_MAX_LATENCY_DELTA", "0.2"))
    canary_min_requests: int = int(os.getenv("CANARY_MIN_REQUESTS", "100"))
    canary_metrics_path: str = os.getenv("CANARY_METRICS_PATH", "monitoring/canary_metrics.json")

    run_id: str = os.getenv("RUN_ID", "")
    promotion_lock_file: str = os.getenv("PROMOTION_LOCK_FILE", "models/registry_promotion.lock")
    promotion_lock_timeout_seconds: int = int(os.getenv("PROMOTION_LOCK_TIMEOUT_SECONDS", "180"))
    telemetry_state_path: str = os.getenv("TELEMETRY_STATE_PATH", "monitoring/telemetry_state.json")


settings = Settings()
