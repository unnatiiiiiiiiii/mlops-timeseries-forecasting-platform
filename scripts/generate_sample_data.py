import numpy as np
import pandas as pd


def main():
    rng = np.random.default_rng(42)
    days = 550
    ds = pd.date_range(start="2024-01-01", periods=days, freq="D")
    trend = np.linspace(100, 170, days)
    weekly = 8 * np.sin(np.arange(days) * (2 * np.pi / 7))
    yearly = 12 * np.sin(np.arange(days) * (2 * np.pi / 365))
    noise = rng.normal(0, 2.0, size=days)
    y = trend + weekly + yearly + noise

    normalized = pd.DataFrame({"ds": ds, "y": y.round(3)})
    normalized.to_csv("data/raw/timeseries.csv", index=False)

    source_like = normalized.rename(columns={"ds": "timestamp", "y": "target"})
    source_like.to_csv("data/raw/timeseries_input.csv", index=False)

    print("Wrote data/raw/timeseries.csv")
    print("Wrote data/raw/timeseries_input.csv")


if __name__ == "__main__":
    main()
