import numpy as np

from mlops_forecasting.drift import detect_drift


def test_drift_detector_identifies_shifted_distribution():
    rng = np.random.default_rng(42)
    ref = rng.normal(0, 1, size=500)
    cur = rng.normal(2, 1, size=500)

    result = detect_drift(ref, cur, threshold=0.15)
    assert result.drift_detected is True
    assert result.score > 0.15
