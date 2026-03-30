from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class RealtimePredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latest_values: list[float] = Field(min_length=30, max_length=10000)


class BatchPredictionRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ds: datetime
    y: float


class BatchPredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: list[BatchPredictionRow] = Field(min_length=35, max_length=20000)


class IngestTimeseriesRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ds: datetime
    y: float


class IngestTimeseriesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["merge", "replace"] = "merge"
    rows: list[IngestTimeseriesRow] = Field(min_length=1, max_length=50000)


class PredictionResponse(BaseModel):
    prediction: float
    model_version: str
    timestamp: datetime


class IngestResponse(BaseModel):
    rows_received: int
    rows_written: int
    mode: str
    output_path: str
    timestamp: datetime
