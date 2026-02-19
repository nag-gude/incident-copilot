"""Ingestion service - ingests logs, metrics, and traces."""

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
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./incident_copilot.db")
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class LogRecord(Base):
    __tablename__ = "logs"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String, default="info")
    message = Column(Text)
    source = Column(String, default="unknown")
    service = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)


class MetricRecord(Base):
    __tablename__ = "metrics"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    name = Column(String)
    value = Column(Float)
    labels_json = Column(Text, nullable=True)
    service = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Incident Copilot Ingestion Service", version="1.0.0")


class LogIn(BaseModel):
    level: str = "info"
    message: str
    source: str = "unknown"
    service: str | None = None
    metadata: dict = Field(default_factory=dict)


class MetricIn(BaseModel):
    name: str
    value: float
    labels: dict = Field(default_factory=dict)
    service: str | None = None


@app.post("/ingest/logs")
async def ingest_logs(log: LogIn):
    """Ingest a log entry."""
    db = SessionLocal()
    try:
        record = LogRecord(
            id=str(uuid.uuid4()),
            level=log.level,
            message=log.message,
            source=log.source,
            service=log.service,
            metadata_json=str(log.metadata) if log.metadata else None,
        )
        db.add(record)
        db.commit()
        return {"id": record.id, "status": "ok"}
    finally:
        db.close()


@app.post("/ingest/logs/batch")
async def ingest_logs_batch(logs: list[LogIn]):
    """Ingest multiple log entries."""
    db = SessionLocal()
    try:
        ids = []
        for log in logs:
            record = LogRecord(
                id=str(uuid.uuid4()),
                level=log.level,
                message=log.message,
                source=log.source,
                service=log.service,
                metadata_json=str(log.metadata) if log.metadata else None,
            )
            db.add(record)
            ids.append(record.id)
        db.commit()
        return {"ids": ids, "count": len(ids)}
    finally:
        db.close()


@app.post("/ingest/metrics")
async def ingest_metrics(metric: MetricIn):
    """Ingest a metric sample."""
    db = SessionLocal()
    try:
        record = MetricRecord(
            id=str(uuid.uuid4()),
            name=metric.name,
            value=metric.value,
            labels_json=str(metric.labels) if metric.labels else None,
            service=metric.service,
        )
        db.add(record)
        db.commit()
        return {"id": record.id, "status": "ok"}
    finally:
        db.close()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ingestion"}


@app.get("/logs")
async def get_logs(limit: int = 100, service: str | None = None):
    """Retrieve recent logs."""
    db = SessionLocal()
    try:
        q = db.query(LogRecord).order_by(LogRecord.timestamp.desc()).limit(limit)
        if service:
            q = q.filter(LogRecord.service == service)
        rows = q.all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "level": r.level,
                "message": r.message,
                "source": r.source,
                "service": r.service,
            }
            for r in rows
        ]
    finally:
        db.close()


@app.get("/metrics")
async def get_metrics(limit: int = 1000, name: str | None = None, service: str | None = None):
    """Retrieve recent metrics."""
    db = SessionLocal()
    try:
        q = db.query(MetricRecord).order_by(MetricRecord.timestamp.desc()).limit(limit)
        if name:
            q = q.filter(MetricRecord.name == name)
        if service:
            q = q.filter(MetricRecord.service == service)
        rows = q.all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "name": r.name,
                "value": r.value,
                "service": r.service,
            }
            for r in rows
        ]
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
