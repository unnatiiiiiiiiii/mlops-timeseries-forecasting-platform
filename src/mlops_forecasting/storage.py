from datetime import datetime
from sqlalchemy import create_engine, String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from mlops_forecasting.config import settings


class Base(DeclarativeBase):
    pass


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_version: Mapped[str] = mapped_column(String(64))
    prediction: Mapped[float] = mapped_column(Float)
    endpoint: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


engine = create_engine(settings.database_url, future=True)


def init_db():
    Base.metadata.create_all(engine)


def log_prediction(model_version: str, prediction: float, endpoint: str):
    with Session(engine) as session:
        session.add(
            PredictionLog(
                model_version=model_version,
                prediction=prediction,
                endpoint=endpoint,
            )
        )
        session.commit()
