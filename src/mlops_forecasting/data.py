from pathlib import Path
import pandas as pd
import requests
from sqlalchemy import create_engine


def load_timeseries(path: str, ts_col: str, y_col: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df[ts_col] = pd.to_datetime(df[ts_col])
    df = df.sort_values(ts_col).dropna(subset=[y_col])
    return df


def ensure_path(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _normalize(df: pd.DataFrame, ts_col: str, y_col: str) -> pd.DataFrame:
    out = df.rename(columns={ts_col: "ds", y_col: "y"})[["ds", "y"]].copy()
    out["ds"] = pd.to_datetime(out["ds"])
    out["y"] = pd.to_numeric(out["y"], errors="coerce")
    out = out.dropna(subset=["ds", "y"]).sort_values("ds").drop_duplicates(subset=["ds"])
    return out.reset_index(drop=True)


def ingest_from_csv(path: str, ts_col: str, y_col: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return _normalize(df, ts_col, y_col)


def ingest_from_http(url: str, ts_key: str, y_key: str) -> pd.DataFrame:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        rows = payload.get("data", [])
    else:
        rows = payload
    df = pd.DataFrame(rows)
    return _normalize(df.rename(columns={ts_key: "ds", y_key: "y"}), "ds", "y")


def ingest_from_postgres(conn_str: str, table: str, query: str, ts_col: str, y_col: str) -> pd.DataFrame:
    engine = create_engine(conn_str)
    sql = query.strip() or f"SELECT {ts_col}, {y_col} FROM {table}"
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    return _normalize(df, ts_col, y_col)


def persist_ingested(df: pd.DataFrame, out_path: str) -> str:
    ensure_path(out_path)
    df.to_csv(out_path, index=False)
    return out_path


def upsert_timeseries_rows(rows: list[dict], out_path: str, mode: str = "merge") -> tuple[int, str]:
    incoming = _normalize(pd.DataFrame(rows), "ds", "y")

    if mode == "replace" or not Path(out_path).exists():
        final_df = incoming
    else:
        existing = load_timeseries(out_path, "ds", "y")
        existing = existing.rename(columns={"ds": "ds", "y": "y"})[["ds", "y"]]
        final_df = (
            pd.concat([existing, incoming], ignore_index=True)
            .sort_values("ds")
            .drop_duplicates(subset=["ds"], keep="last")
            .reset_index(drop=True)
        )

    ensure_path(out_path)
    final_df.to_csv(out_path, index=False)
    return int(len(final_df)), out_path
