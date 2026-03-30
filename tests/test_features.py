import pandas as pd

from mlops_forecasting.features import create_features


def test_create_features_generates_expected_columns():
    df = pd.DataFrame(
        {
            "ds": pd.date_range("2025-01-01", periods=60, freq="D"),
            "y": [float(i) for i in range(60)],
        }
    )
    out = create_features(df, "ds", "y")

    assert "lag_7" in out.columns
    assert "roll_mean_14" in out.columns
    assert len(out) > 0
