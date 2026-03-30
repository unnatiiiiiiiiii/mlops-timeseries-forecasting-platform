from prometheus_client import Counter, Histogram

PREDICTION_COUNTER = Counter(
    "forecast_predictions_total", "Total predictions generated", ["endpoint"]
)

LATENCY_SECONDS = Histogram(
    "forecast_prediction_latency_seconds", "Prediction latency in seconds", ["endpoint"]
)
