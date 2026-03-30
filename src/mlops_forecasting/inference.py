from datetime import datetime
import joblib
import pandas as pd

from mlops_forecasting.config import settings
from mlops_forecasting.features import create_features


class ForecastService:
    def __init__(self, model_path: str = settings.model_file):
        self.bundle = joblib.load(model_path)
        self.is_prophet = self.bundle.__class__.__name__.lower() == "prophet"

    def predict_from_latest_values(self, values: list[float]) -> float:
        if self.is_prophet:
            # Prophet requires explicit future timestamps; for API default use last known trend.
            return float(values[-1])

        model = self.bundle["model"]
        feature_cols = self.bundle["feature_cols"]
        end = pd.Timestamp(datetime.utcnow().date())
        ts = pd.date_range(end=end, periods=len(values), freq=settings.frequency)
        df = pd.DataFrame({settings.timestamp_column: ts, settings.target_column: values})
        feat_df = create_features(df, settings.timestamp_column, settings.target_column)
        x = feat_df[feature_cols].tail(1)
        return float(model.predict(x)[0])

    def predict_batch(self, rows: list[dict]) -> list[float]:
        if self.is_prophet:
            return [float(r.get(settings.target_column, 0.0)) for r in rows]

        model = self.bundle["model"]
        feature_cols = self.bundle["feature_cols"]
        df = pd.DataFrame(rows)
        df[settings.timestamp_column] = pd.to_datetime(df[settings.timestamp_column])
        feat_df = create_features(df, settings.timestamp_column, settings.target_column)
        pred = model.predict(feat_df[feature_cols])
        return [float(p) for p in pred]
