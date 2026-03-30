from datetime import datetime
from mlops_forecasting.config import settings
from mlops_forecasting.data import load_timeseries
from mlops_forecasting.drift import detect_drift


def run_drift_check(window: int = 90):
    df = load_timeseries(settings.data_path, settings.timestamp_column, settings.target_column)
    if len(df) < window * 2:
        return {"status": "insufficient_data"}

    reference = df[settings.target_column].iloc[-window * 2 : -window].to_numpy()
    current = df[settings.target_column].iloc[-window:].to_numpy()
    result = detect_drift(reference, current, settings.drift_threshold)

    return {
        "checked_at": datetime.utcnow().isoformat(),
        "drift_score": result.score,
        "drift_detected": result.drift_detected,
        "threshold": settings.drift_threshold,
    }


if __name__ == "__main__":
    print(run_drift_check())
