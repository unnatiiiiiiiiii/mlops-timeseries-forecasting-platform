import pandas as pd


LAGS = [1, 2, 3, 7, 14, 28]
ROLL_WINDOWS = [7, 14]


def create_features(df: pd.DataFrame, ts_col: str, y_col: str) -> pd.DataFrame:
    out = df.copy()
    out[ts_col] = pd.to_datetime(out[ts_col])
    out["day_of_week"] = out[ts_col].dt.dayofweek
    out["day_of_month"] = out[ts_col].dt.day
    out["month"] = out[ts_col].dt.month
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)

    for lag in LAGS:
        out[f"lag_{lag}"] = out[y_col].shift(lag)

    for window in ROLL_WINDOWS:
        out[f"roll_mean_{window}"] = out[y_col].shift(1).rolling(window).mean()
        out[f"roll_std_{window}"] = out[y_col].shift(1).rolling(window).std()

    return out.dropna().reset_index(drop=True)


def split_train_test(df: pd.DataFrame, test_horizon: int):
    split = len(df) - test_horizon
    return df.iloc[:split], df.iloc[split:]
