"""Prediction service - failure probability scoring."""

import os
import uuid
from datetime import datetime
from pathlib import Path

import sys
_here = Path(__file__).resolve().parent
_root = _here.parents[2] if len(_here.parents) >= 3 else _here
shared_dir = _root / "shared"
if shared_dir.exists():
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./incident_copilot.db")
INGESTION_URL = os.getenv("INGESTION_URL", "http://localhost:8001")
ANOMALY_URL = os.getenv("ANOMALY_URL", "http://localhost:8002")
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class PredictionRecord(Base):
    __tablename__ = "predictions"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    service = Column(String, nullable=True)
    failure_probability = Column(Float)
    time_to_failure_minutes = Column(Float, nullable=True)
    contributing_factors_json = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Incident Copilot Prediction Service", version="1.0.0")


def compute_failure_probability(anomalies: list, error_log_count: int, metric_trend: float) -> float:
    """
    Heuristic failure probability 0-100 based on:
    - Number and severity of anomalies
    - Error log volume
    - Metric trend (positive = degrading)
    """
    score = 0.0
    for a in anomalies:
        sev = a.get("severity", "medium")
        dev = a.get("deviation_score", 0)
        if sev == "high":
            score += 25 + min(dev * 5, 20)
        else:
            score += 10 + min(dev * 3, 15)
    score += min(error_log_count * 2, 20)
    if metric_trend > 0:
        score += min(metric_trend * 10, 15)
    return min(100.0, score)


@app.get("/predict")
async def run_prediction(service: str | None = None):
    """Compute failure probability from anomalies and ingestion data."""
    async with httpx.AsyncClient() as client:
        anom_resp = await client.get(f"{ANOMALY_URL}/anomalies?limit=50")
        if anom_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Anomaly service unavailable")
        anomalies = anom_resp.json()

        logs_resp = await client.get(f"{INGESTION_URL}/logs?limit=200")
        logs = logs_resp.json() if logs_resp.status_code == 200 else []
        error_logs = [l for l in logs if l.get("level") == "error"]
        error_count = len(error_logs)

    # Simple trend: assume recent anomalies indicate degradation
    metric_trend = len(anomalies) * 0.1 if anomalies else 0
    prob = compute_failure_probability(anomalies, error_count, metric_trend)
    factors = []
    if anomalies:
        factors.append(f"{len(anomalies)} anomalies detected")
    if error_count:
        factors.append(f"{error_count} error logs")
    ttf = max(0, 60 - prob) if prob > 50 else None  # rough estimate

    pid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        record = PredictionRecord(
            id=pid,
            service=service,
            failure_probability=prob,
            time_to_failure_minutes=ttf,
            contributing_factors_json=str(factors),
        )
        db.add(record)
        db.commit()
    finally:
        db.close()

    return {
        "id": pid,
        "service": service,
        "failure_probability": round(prob, 1),
        "time_to_failure_minutes": ttf,
        "contributing_factors": factors,
    }


@app.get("/predictions")
async def get_predictions(limit: int = 20, service: str | None = None):
    """Retrieve recent predictions."""
    db = SessionLocal()
    try:
        q = db.query(PredictionRecord).order_by(PredictionRecord.timestamp.desc()).limit(limit)
        if service:
            q = q.filter(PredictionRecord.service == service)
        rows = q.all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "service": r.service,
                "failure_probability": r.failure_probability,
                "time_to_failure_minutes": r.time_to_failure_minutes,
            }
            for r in rows
        ]
    finally:
        db.close()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "prediction"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
