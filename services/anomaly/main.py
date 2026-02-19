"""Anomaly detection service - detects deviations in logs and metrics."""

import os
import uuid
from datetime import datetime, timedelta
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
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import numpy as np

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./incident_copilot.db")
INGESTION_URL = os.getenv("INGESTION_URL", "http://localhost:8001")
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class AnomalyRecord(Base):
    __tablename__ = "anomalies"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_or_log = Column(String)
    expected_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)
    deviation_score = Column(Float)
    service = Column(String, nullable=True)
    severity = Column(String, default="medium")


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Incident Copilot Anomaly Service", version="1.0.0")


def detect_metric_anomaly(values: list[float], threshold_std: float = 3.0) -> tuple[bool, float, float | None]:
    """Statistical anomaly detection: flag if value exceeds mean + threshold_std * std."""
    if len(values) < 5:
        return False, 0.0, None
    arr = np.array(values)
    mean, std = arr.mean(), arr.std()
    if std == 0:
        return False, 0.0, None
    latest = values[-1]
    z = abs(latest - mean) / std if std else 0
    return z > threshold_std, z, float(latest)


@app.get("/detect")
async def run_anomaly_detection(service: str | None = None):
    """Fetch recent metrics from ingestion, detect anomalies, store and return."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{INGESTION_URL}/metrics?limit=500")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Ingestion service unavailable")
        metrics = resp.json()

    # Group by (name, service)
    by_key: dict[tuple[str, str | None], list[float]] = {}
    for m in metrics:
        key = (m["name"], m.get("service"))
        if key not in by_key:
            by_key[key] = []
        by_key[key].append(m["value"])

    anomalies = []
    db = SessionLocal()
    try:
        for (name, svc), values in by_key.items():
            if service and svc != service:
                continue
            is_anomaly, score, actual = detect_metric_anomaly(values)
            if is_anomaly:
                arr = np.array(values)
                expected = float(arr.mean())
                sev = "high" if score > 5 else "medium"
                aid = str(uuid.uuid4())
                record = AnomalyRecord(
                    id=aid,
                    metric_or_log=name,
                    expected_value=expected,
                    actual_value=actual,
                    deviation_score=float(score),
                    service=svc,
                    severity=sev,
                )
                db.add(record)
                anomalies.append({
                    "id": aid,
                    "metric_or_log": name,
                    "expected_value": expected,
                    "actual_value": actual,
                    "deviation_score": float(score),
                    "service": svc,
                    "severity": sev,
                })
        db.commit()
    finally:
        db.close()

    return {"anomalies": anomalies, "count": len(anomalies)}


@app.get("/anomalies")
async def get_anomalies(limit: int = 50, service: str | None = None):
    """Retrieve detected anomalies."""
    db = SessionLocal()
    try:
        q = db.query(AnomalyRecord).order_by(AnomalyRecord.timestamp.desc()).limit(limit)
        if service:
            q = q.filter(AnomalyRecord.service == service)
        rows = q.all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "metric_or_log": r.metric_or_log,
                "expected_value": r.expected_value,
                "actual_value": r.actual_value,
                "deviation_score": r.deviation_score,
                "service": r.service,
                "severity": r.severity,
            }
            for r in rows
        ]
    finally:
        db.close()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "anomaly"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
