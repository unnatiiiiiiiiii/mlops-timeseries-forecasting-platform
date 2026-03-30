from contextlib import asynccontextmanager
from datetime import UTC, datetime
from time import perf_counter

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from mlops_forecasting.config import settings
from mlops_forecasting.data import upsert_timeseries_rows
from mlops_forecasting.inference import ForecastService
from mlops_forecasting.monitoring import LATENCY_SECONDS, PREDICTION_COUNTER
from mlops_forecasting.schemas import (
    BatchPredictRequest,
    IngestResponse,
    IngestTimeseriesRequest,
    PredictionResponse,
    RealtimePredictRequest,
)
from mlops_forecasting.storage import init_db, log_prediction


service: ForecastService | None = None
MODEL_VERSION = "unknown"


@asynccontextmanager
async def lifespan(_: FastAPI):
    global service
    init_db()
    try:
        service = ForecastService(settings.model_file)
    except FileNotFoundError:
        service = None
    yield


app = FastAPI(title="Time-Series Forecasting API", version="1.1.1", lifespan=lifespan)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": service is not None,
        "time": datetime.now(UTC).isoformat(),
    }


@app.post("/ingest/timeseries", response_model=IngestResponse)
def ingest_timeseries(payload: IngestTimeseriesRequest):
    rows = [row.model_dump(mode="json") for row in payload.rows]
    rows_written, out_path = upsert_timeseries_rows(rows, settings.data_path, mode=payload.mode)
    return IngestResponse(
        rows_received=len(rows),
        rows_written=rows_written,
        mode=payload.mode,
        output_path=out_path,
        timestamp=datetime.now(UTC),
    )


@app.post("/predict/realtime", response_model=PredictionResponse)
def predict_realtime(payload: RealtimePredictRequest):
    if service is None:
        raise HTTPException(status_code=503, detail="Model not available. Train first.")

    start = perf_counter()
    pred = service.predict_from_latest_values(payload.latest_values)
    duration = perf_counter() - start

    PREDICTION_COUNTER.labels(endpoint="realtime").inc()
    LATENCY_SECONDS.labels(endpoint="realtime").observe(duration)
    log_prediction(MODEL_VERSION, pred, "realtime")

    return PredictionResponse(
        prediction=pred,
        model_version=MODEL_VERSION,
        timestamp=datetime.now(UTC),
    )


@app.post("/predict/batch")
def predict_batch(payload: BatchPredictRequest):
    if service is None:
        raise HTTPException(status_code=503, detail="Model not available. Train first.")

    start = perf_counter()
    rows = [row.model_dump(mode="json") for row in payload.rows]
    preds = service.predict_batch(rows)
    duration = perf_counter() - start

    PREDICTION_COUNTER.labels(endpoint="batch").inc(len(preds))
    LATENCY_SECONDS.labels(endpoint="batch").observe(duration)

    for p in preds:
        log_prediction(MODEL_VERSION, p, "batch")

    return {
        "predictions": preds,
        "model_version": MODEL_VERSION,
        "count": len(preds),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
