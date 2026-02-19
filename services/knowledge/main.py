"""Knowledge service - Sanity integration for runbooks and incident history."""

import os
import json
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


class FeedbackIncidentBody(BaseModel):
    outcome: str
    remediation_used: str | None = None
    notes: str | None = None
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./incident_copilot.db")
SANITY_PROJECT_ID = os.getenv("SANITY_PROJECT_ID", "")
SANITY_DATASET = os.getenv("SANITY_DATASET", "production")
SANITY_TOKEN = os.getenv("SANITY_TOKEN", "")
RECOMMENDATION_URL = os.getenv("RECOMMENDATION_URL", "http://localhost:8004")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class RunbookRecord(Base):
    """Local cache of runbook entries (Sanity sync or standalone)."""
    __tablename__ = "runbooks"
    id = Column(String, primary_key=True)
    service = Column(String)
    error_pattern = Column(String)
    remediation_steps = Column(Text)
    sanity_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class IncidentRefRecord(Base):
    """Structured incident reference for 'similar past incidents' and learning feedback."""
    __tablename__ = "incident_refs"
    id = Column(String, primary_key=True)
    service = Column(String)
    root_cause = Column(String)
    incident_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Learning feedback loop: outcome and remediation that worked
    outcome = Column(String, nullable=True)  # success | partial | failed
    remediation_used = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Incident Copilot Knowledge Service", version="1.0.0")


SANITY_GROQ = "https://{project}.api.sanity.io/v2024-01-01/data/query/{dataset}"


async def sanity_query(query: str, params: dict | None = None) -> list[dict]:
    """Execute GROQ query against Sanity."""
    if not SANITY_PROJECT_ID:
        return []
    url = SANITY_GROQ.format(project=SANITY_PROJECT_ID, dataset=SANITY_DATASET)
    request_params: dict = {"query": query}
    if params:
        request_params.update(params)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=request_params)
        if resp.status_code != 200:
            return []
        data = resp.json()
        return data.get("result", [])


def _normalize_sanity_incident(r: dict) -> dict:
    """Convert Sanity incident to standard format."""
    return {
        "id": r.get("_id", r.get("id", "")),
        "service": r.get("service", "unknown"),
        "root_cause": r.get("rootCause", r.get("root_cause", "")),
        "incident_id": r.get("incidentId", r.get("incident_id", r.get("_id", ""))),
        "created_at": r.get("_createdAt", r.get("created_at", "")),
        "source": "sanity",
    }


@app.get("/similar-incidents")
async def similar_incidents(service: str | None = None, error_pattern: str | None = None):
    """
    Structured content feature: Show similar past incidents.
    Uses local DB; when SANITY_PROJECT_ID is set, also queries Sanity via GROQ and merges results.
    """
    results: list[dict] = []
    seen_ids: set[str] = set()

    # Query Sanity when configured (structured content - sponsor requirement)
    if SANITY_PROJECT_ID:
        if service:
            groq = '*[_type == "incident" && service == $service] | order(_createdAt desc) [0...20] { _id, service, rootCause, "incidentId": _id, _createdAt }'
            sanity_results = await sanity_query(groq, {"$service": service})
        elif error_pattern:
            pattern = f"*{error_pattern}*"
            groq = '*[_type == "incident" && rootCause match $pattern] | order(_createdAt desc) [0...20] { _id, service, rootCause, "incidentId": _id, _createdAt }'
            sanity_results = await sanity_query(groq, {"$pattern": pattern})
        else:
            groq = '*[_type == "incident"] | order(_createdAt desc) [0...20] { _id, service, rootCause, "incidentId": _id, _createdAt }'
            sanity_results = await sanity_query(groq)
        for r in sanity_results:
            norm = _normalize_sanity_incident(r)
            if norm["id"] and norm["id"] not in seen_ids:
                seen_ids.add(norm["id"])
                results.append(norm)

    # Query local DB
    db = SessionLocal()
    try:
        q = db.query(IncidentRefRecord).order_by(IncidentRefRecord.created_at.desc()).limit(20)
        if service:
            q = q.filter(IncidentRefRecord.service == service)
        if error_pattern:
            q = q.filter(IncidentRefRecord.root_cause.ilike(f"%{error_pattern}%"))
        rows = q.all()
        for r in rows:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                results.append({
                    "id": r.id,
                    "service": r.service,
                    "root_cause": r.root_cause,
                    "incident_id": r.incident_id,
                    "created_at": r.created_at.isoformat(),
                    "source": "local",
                    "outcome": r.outcome,
                    "remediation_used": r.remediation_used,
                    "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                })
    finally:
        db.close()

    # Learning: sort so successful outcomes surface first
    def order_key(x):
        if x.get("outcome") == "success":
            return (0, x.get("created_at") or "")
        if x.get("outcome") == "partial":
            return (1, x.get("created_at") or "")
        return (2, x.get("created_at") or "")

    results.sort(key=order_key)
    return results[:20]


@app.get("/incidents-by-service")
async def incidents_by_service():
    """Structured content feature: All incidents grouped by service."""
    db = SessionLocal()
    try:
        rows = db.query(IncidentRefRecord).all()
        by_service: dict[str, list] = {}
        for r in rows:
            if r.service not in by_service:
                by_service[r.service] = []
            by_service[r.service].append({
                "id": r.id,
                "root_cause": r.root_cause,
                "incident_id": r.incident_id,
            })
        return by_service
    finally:
        db.close()


@app.post("/sync-incident")
async def sync_incident_from_recommendation(incident_id: str):
    """Sync an incident from recommendation service into knowledge base."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RECOMMENDATION_URL}/incidents")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Recommendation service unavailable")
        incidents = resp.json()
    incident = next((i for i in incidents if i["id"] == incident_id), None)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    db = SessionLocal()
    try:
        existing = db.query(IncidentRefRecord).filter(IncidentRefRecord.incident_id == incident_id).first()
        if existing:
            existing.service = incident.get("service") or existing.service
            existing.root_cause = incident.get("root_cause") or existing.root_cause
            db.commit()
            return {"id": existing.id, "status": "updated"}
        rid = str(uuid.uuid4())
        record = IncidentRefRecord(
            id=rid,
            service=incident.get("service") or "unknown",
            root_cause=incident.get("root_cause") or "unknown",
            incident_id=incident_id,
        )
        db.add(record)
        db.commit()
        return {"id": rid, "status": "synced"}
    finally:
        db.close()


@app.post("/feedback-incident")
async def feedback_incident(incident_id: str, body: FeedbackIncidentBody):
    """
    Learning feedback loop: record outcome and remediation used for an incident.
    Updates or creates incident_ref so similar-incidents can surface "what worked".
    """
    if body.outcome not in ("success", "partial", "failed"):
        raise HTTPException(status_code=400, detail="outcome must be success, partial, or failed")
    # Fetch incident from recommendation to ensure we have ref
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RECOMMENDATION_URL}/incidents/{incident_id}")
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Incident not found")
        incident = resp.json()
    db = SessionLocal()
    try:
        ref = db.query(IncidentRefRecord).filter(IncidentRefRecord.incident_id == incident_id).first()
        if ref:
            ref.outcome = body.outcome
            ref.remediation_used = body.remediation_used
            ref.resolved_at = datetime.utcnow()
            db.commit()
            return {"id": ref.id, "status": "feedback_recorded"}
        # Create ref if not yet synced (e.g. feedback before sync)
        rid = str(uuid.uuid4())
        ref = IncidentRefRecord(
            id=rid,
            service=incident.get("service") or "unknown",
            root_cause=incident.get("root_cause") or "unknown",
            incident_id=incident_id,
            outcome=body.outcome,
            remediation_used=body.remediation_used,
            resolved_at=datetime.utcnow(),
        )
        db.add(ref)
        db.commit()
        return {"id": rid, "status": "feedback_recorded"}
    finally:
        db.close()


@app.get("/runbooks")
async def get_runbooks(service: str | None = None):
    """Get runbooks - from local DB or Sanity."""
    db = SessionLocal()
    try:
        q = db.query(RunbookRecord).order_by(RunbookRecord.created_at.desc()).limit(50)
        if service:
            q = q.filter(RunbookRecord.service == service)
        rows = q.all()
        return [
            {
                "id": r.id,
                "service": r.service,
                "error_pattern": r.error_pattern,
                "remediation_steps": r.remediation_steps,
            }
            for r in rows
        ]
    finally:
        db.close()


@app.post("/runbooks")
async def add_runbook(service: str, error_pattern: str, remediation_steps: str):
    """Add a runbook entry (local; can sync to Sanity if configured)."""
    rid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        record = RunbookRecord(
            id=rid,
            service=service,
            error_pattern=error_pattern,
            remediation_steps=remediation_steps,
        )
        db.add(record)
        db.commit()
        return {"id": rid, "status": "created"}
    finally:
        db.close()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "knowledge", "sanity_configured": bool(SANITY_PROJECT_ID)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
