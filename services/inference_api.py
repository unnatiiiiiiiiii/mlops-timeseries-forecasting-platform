from fastapi import FastAPI, HTTPException
import mlflow
import pandas as pd
import time

from mlops_forecasting.config import settings


app = FastAPI(title="Registry Inference API", version="1.0.0")

MODEL_NAME = settings.mlflow_registered_model_name
MODEL_STAGE = settings.mlflow_model_stage

_model = None
_last_loaded = 0.0


def load_model():
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    return mlflow.pyfunc.load_model(model_uri=f"models:/{MODEL_NAME}/{MODEL_STAGE}")


def get_model():
    global _model, _last_loaded
    if _model is None or (time.time() - _last_loaded) > settings.registry_refresh_seconds:
        _model = load_model()
        _last_loaded = time.time()
    return _model


@app.get("/")
def health():
    return {"status": "ok", "model": MODEL_NAME, "stage": MODEL_STAGE}


@app.post("/predict")
def predict(data: dict):
    model = get_model()
    if model is None:
        raise HTTPException(status_code=503, detail="Model unavailable")

    df = pd.DataFrame([data])
    preds = model.predict(df)
    return {"prediction": preds.tolist()}
