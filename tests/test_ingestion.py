import pandas as pd

from mlops_forecasting.data import ingest_from_csv


def test_ingest_from_csv_normalizes_columns(tmp_path):
    src = tmp_path / "input.csv"
    pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=5, freq="D"),
            "target": [1, 2, 3, 4, 5],
        }
    ).to_csv(src, index=False)

    out = ingest_from_csv(str(src), "timestamp", "target")

    assert list(out.columns) == ["ds", "y"]
    assert len(out) == 5
