from contextlib import contextmanager
from datetime import UTC, datetime
import os
from pathlib import Path
import time

import joblib
import pandas as pd

from mlops_forecasting.config import settings
from mlops_forecasting.data import ensure_path, load_timeseries
from mlops_forecasting.evaluate import regression_metrics
from mlops_forecasting.features import create_features, split_train_test
from mlops_forecasting.telemetry import (
    record_artifacts_created,
    record_model_metrics,
    record_promotion_lock,
)


LOWER_IS_BETTER = {"rmse", "mae", "mape"}


@contextmanager
def _promotion_lock(lock_path: str, timeout_seconds: int = 180, poll_seconds: float = 1.0):
    ensure_path(lock_path)
    lockfile = Path(lock_path)
    start = time.time()
    lock_wait_start = time.time()
    fd = None
    run_label = settings.run_id or "unknown"
    announced_wait = False

    while True:
        try:
            fd = os.open(str(lockfile), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            metadata = f"pid={os.getpid()} run_id={run_label} ts={datetime.now(UTC).isoformat()}\n"
            os.write(fd, metadata.encode("utf-8"))
            wait_seconds = time.time() - lock_wait_start
            print(f"Acquired promotion lock: {lock_path} (run_id={run_label})")
            record_promotion_lock(wait_seconds=wait_seconds, acquired=True, timeout=False)
            break
        except FileExistsError:
            if not announced_wait:
                print(f"Waiting for promotion lock: {lock_path} (run_id={run_label})")
                announced_wait = True
            elapsed = time.time() - start
            if elapsed >= timeout_seconds:
                record_promotion_lock(wait_seconds=elapsed, acquired=False, timeout=True)
                raise TimeoutError(f"Timed out acquiring promotion lock: {lock_path}")
            time.sleep(poll_seconds)

    try:
        yield
    finally:
        try:
            if fd is not None:
                os.close(fd)
        finally:
            try:
                lockfile.unlink(missing_ok=True)
                print(f"Released promotion lock: {lock_path} (run_id={run_label})")
            except Exception:
                pass


def _init_model(model_type: str):
    model_type = model_type.lower()
    if model_type == "xgboost":
        from xgboost import XGBRegressor

        return XGBRegressor(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
        )

    if model_type == "lightgbm":
        from lightgbm import LGBMRegressor

        return LGBMRegressor(
            n_estimators=500,
            learning_rate=0.05,
            num_leaves=31,
            random_state=42,
        )

    if model_type == "prophet":
        from prophet import Prophet

        return Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)

    raise ValueError(f"Unsupported model type: {model_type}")


def _fit_predict_prophet(df_train, df_test, ts_col, y_col):
    model = _init_model("prophet")
    prophet_train = df_train[[ts_col, y_col]].rename(columns={ts_col: "ds", y_col: "y"})
    model.fit(prophet_train)
    future = df_test[[ts_col]].rename(columns={ts_col: "ds"})
    forecast = model.predict(future)
    y_pred = forecast["yhat"].values
    return model, y_pred


def _train_one_model(model_name: str, df: pd.DataFrame) -> dict:
    metric_name = settings.primary_metric.lower()
    if model_name == "prophet":
        train_df, test_df = split_train_test(df, settings.forecast_horizon)
        model, y_pred = _fit_predict_prophet(
            train_df, test_df, settings.timestamp_column, settings.target_column
        )
        y_true = test_df[settings.target_column].values
        metrics = regression_metrics(y_true, y_pred)
        artifact_obj = model
        artifact_kind = "prophet"
        feature_cols = []
    else:
        feat_df = create_features(df, settings.timestamp_column, settings.target_column)
        train_df, test_df = split_train_test(feat_df, settings.forecast_horizon)

        feature_cols = [
            c for c in train_df.columns if c not in [settings.timestamp_column, settings.target_column]
        ]
        x_train = train_df[feature_cols]
        y_train = train_df[settings.target_column]
        x_test = test_df[feature_cols]
        y_test = test_df[settings.target_column]

        model = _init_model(model_name)
        model.fit(x_train, y_train)
        y_pred = model.predict(x_test)
        metrics = regression_metrics(y_test, y_pred)
        artifact_obj = {"model": model, "feature_cols": feature_cols}
        artifact_kind = "regressor"

    primary_value = float(metrics.get(metric_name, metrics["rmse"]))
    return {
        "model_name": model_name,
        "metrics": metrics,
        "primary_metric": metric_name,
        "primary_value": primary_value,
        "artifact_kind": artifact_kind,
        "artifact_obj": artifact_obj,
        "feature_cols": feature_cols,
    }


def _pick_champion(results: list[dict]) -> tuple[dict, dict | None]:
    metric_name = settings.primary_metric.lower()
    if metric_name in LOWER_IS_BETTER:
        ordered = sorted(results, key=lambda r: r["primary_value"])
    else:
        ordered = sorted(results, key=lambda r: r["primary_value"], reverse=True)
    champion = ordered[0]
    challenger = ordered[1] if len(ordered) > 1 else None
    return champion, challenger


def _register_and_alias_model(run_id: str) -> str:
    import mlflow

    with _promotion_lock(
        settings.promotion_lock_file,
        timeout_seconds=settings.promotion_lock_timeout_seconds,
    ):
        model_uri = f"runs:/{run_id}/model"
        result = mlflow.register_model(model_uri=model_uri, name=settings.mlflow_registered_model_name)
        model_version = str(result.version)

        client = mlflow.tracking.MlflowClient(tracking_uri=settings.mlflow_tracking_uri)
        try:
            client.set_registered_model_alias(
                name=settings.mlflow_registered_model_name,
                alias="champion",
                version=model_version,
            )
        except Exception:
            pass

        return model_version


def train_and_log() -> dict:
    import mlflow
    import mlflow.sklearn

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)

    df = load_timeseries(settings.data_path, settings.timestamp_column, settings.target_column)
    candidates = [m.strip().lower() for m in settings.candidate_models.split(",") if m.strip()]
    if not candidates:
        candidates = [settings.model_type.lower()]

    with mlflow.start_run(run_name="champion_challenger_training") as parent_run:
        mlflow.log_params(
            {
                "candidate_models": ",".join(candidates),
                "forecast_horizon": settings.forecast_horizon,
                "target_column": settings.target_column,
                "timestamp_column": settings.timestamp_column,
                "primary_metric": settings.primary_metric,
                "run_id": settings.run_id or "",
                "model_file": settings.model_file,
            }
        )

        results: list[dict] = []
        for model_name in candidates:
            with mlflow.start_run(run_name=f"candidate_{model_name}", nested=True):
                outcome = _train_one_model(model_name, df)
                mlflow.log_param("candidate_model", model_name)
                mlflow.log_metrics(outcome["metrics"])
                results.append(outcome)

        champion, challenger = _pick_champion(results)

        ensure_path(settings.model_file)
        joblib.dump(champion["artifact_obj"], settings.model_file)
        mlflow.log_artifact(settings.model_file, artifact_path="bundle")
        record_artifacts_created(settings.run_id, count=1)

        model_version = "unregistered"
        if champion["artifact_kind"] == "regressor":
            try:
                mlflow.sklearn.log_model(champion["artifact_obj"]["model"], artifact_path="model")
                model_version = _register_and_alias_model(parent_run.info.run_id)
            except Exception as exc:
                mlflow.set_tag("model_registry_status", "skipped")
                mlflow.set_tag("model_registry_reason", str(exc)[:240])
        else:
            model_version = "prophet-bundle-only"

        mlflow.log_metrics(
            {
                "champion_mae": champion["metrics"]["mae"],
                "champion_rmse": champion["metrics"]["rmse"],
                "champion_mape": champion["metrics"]["mape"],
            }
        )

        if challenger is not None:
            mlflow.log_metrics(
                {
                    "challenger_mae": challenger["metrics"]["mae"],
                    "challenger_rmse": challenger["metrics"]["rmse"],
                    "challenger_mape": challenger["metrics"]["mape"],
                }
            )
            delta = challenger["primary_value"] - champion["primary_value"]
            mlflow.log_metric("champion_advantage", float(delta))
            mlflow.set_tag("challenger_model", challenger["model_name"])

        mlflow.set_tags(
            {
                "stage": "training",
                "trained_at": datetime.now(UTC).isoformat(),
                "model_file": settings.model_file,
                "champion_model": champion["model_name"],
                "pipeline_run_id": settings.run_id or "",
            }
        )

    record_model_metrics(
        run_id=settings.run_id,
        rmse=float(champion["metrics"]["rmse"]),
        mae=float(champion["metrics"]["mae"]),
        mape=float(champion["metrics"]["mape"]),
        model_version=str(model_version),
    )

    return {
        "run_id": parent_run.info.run_id,
        "model_version": model_version,
        "champion": champion["model_name"],
        "challenger": challenger["model_name"] if challenger else None,
        "metrics": champion["metrics"],
    }


if __name__ == "__main__":
    output = train_and_log()
    print(output)
