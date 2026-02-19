"""Recommendation service - You.com research, Cline CLI, root cause analysis."""

import os
import subprocess
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


class ExplainBody(BaseModel):
    anomaly_ids: list[str] | None = None
    service: str | None = None
    auto_remediate: bool = False


class UpdateIncidentBody(BaseModel):
    status: str | None = None
    resolution_notes: str | None = None


class FeedbackBody(BaseModel):
    outcome: str  # success | partial | failed
    remediation_used: str | None = None
    notes: str | None = None


import httpx
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./incident_copilot.db")
ANOMALY_URL = os.getenv("ANOMALY_URL", "http://localhost:8002")
KNOWLEDGE_URL = os.getenv("KNOWLEDGE_URL", "http://localhost:8005")
YOUCOM_API_KEY = os.getenv("YOUCOM_API_KEY", "")
YOUCOM_API_URL = "https://ydc-index.io/v1/search"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class IncidentRecord(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    anomaly_ids_json = Column(Text)
    service = Column(String, nullable=True)
    root_cause = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)
    recommendations_json = Column(Text, nullable=True)
    youcom_citations_json = Column(Text, nullable=True)
    status = Column(String, default="open")
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)


class IncidentFeedbackRecord(Base):
    """Learning feedback: outcome and remediation used for an incident."""
    __tablename__ = "incident_feedback"
    id = Column(String, primary_key=True)
    incident_id = Column(String, nullable=False)
    outcome = Column(String, nullable=False)  # success | partial | failed
    remediation_used = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Incident Copilot Recommendation Service", version="1.0.0")


async def youcom_search(query: str) -> list[dict]:
    """Call You.com API for research-backed results (citation-backed)."""
    if not YOUCOM_API_KEY:
        return [
            {
                "title": "You.com API not configured",
                "url": "https://you.com/resources/hackathon",
                "snippet": "Set YOUCOM_API_KEY to enable live research-backed remediation.",
            }
        ]
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            YOUCOM_API_URL,
            params={"query": query, "count": 5},
            headers={"X-API-Key": YOUCOM_API_KEY},
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = []
        # You.com returns results in results.web and results.news
        raw = data.get("results", {})
        items = (raw.get("web", []) or [])[:5]
        for r in items:
            snips = r.get("snippets") or []
            snippet = snips[0] if snips else r.get("description", "")
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": snippet,
            })
        return results


AUTO_REMEDIATE_EXECUTE_ENABLED = os.getenv("AUTO_REMEDIATE_EXECUTE_ENABLED", "false").lower() in ("true", "1", "yes")


def run_remediation_script(script: str, timeout_sec: int = 60) -> dict:
    """
    Execute remediation script in a subprocess.
    Returns {stdout, stderr, returncode, error} (error set if exception).
    """
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(script)
            path = f.name
        try:
            result = subprocess.run(
                ["bash", path],
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=os.getcwd(),
            )
            return {
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "returncode": result.returncode,
            }
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    except subprocess.TimeoutExpired as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "error": "timeout"}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "error": str(e)}


def invoke_cline_remediate(error_type: str, service: str, context: str) -> str:
    """
    Invoke Cline CLI to generate remediation script.
    Falls back to mock output if Cline CLI is not installed.
    """
    try:
        result = subprocess.run(
            ["cline", "generate", f"--context=error:{error_type},service:{service}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Fallback mock for demo when Cline CLI not available
    return f'''# Remediation script for {error_type} (service: {service})
# Generated by Incident Copilot AI - Cline CLI integration (mock when CLI not installed)
kubectl scale deployment/{service or "example"} --replicas=2
kubectl rollout restart deployment/{service or "example"}
# Check rollout status
kubectl rollout status deployment/{service or "example"}
'''


@app.post("/explain")
async def explain_incident(body: ExplainBody | None = None):
    """Create incident, fetch anomalies, compute root cause, call You.com for citations."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{ANOMALY_URL}/anomalies?limit=20")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Anomaly service unavailable")
        anomalies = resp.json()

    body = body or ExplainBody()
    if body.anomaly_ids:
        anomalies = [a for a in anomalies if a["id"] in body.anomaly_ids]
    if body.service:
        anomalies = [a for a in anomalies if a.get("service") == body.service]
    if not anomalies:
        anomalies = [{"id": "none", "metric_or_log": "no_anomaly", "severity": "low"}]

    # Root cause heuristics
    metric_names = [a.get("metric_or_log", "unknown") for a in anomalies]
    root_cause = f"Detected anomalies in: {', '.join(set(metric_names))}. Possible resource exhaustion or configuration drift."
    evidence = [f"Anomaly: {a.get('metric_or_log')} (deviation: {a.get('deviation_score', 0)})" for a in anomalies[:5]]

    # You.com integration - research-backed remediation
    search_query = f"Kubernetes {metric_names[0] if metric_names else 'OOM'} remediation runbook"
    citations = await youcom_search(search_query)
    recommendations = [
        "Scale up replicas for affected service",
        "Check resource limits (CPU/memory)",
        "Review recent deployments for config drift",
    ]
    if citations:
        recommendations.append(f"See: {citations[0].get('url', '')}")

    # Learning feedback loop: enrich from similar past incidents that were resolved successfully
    try:
        async with httpx.AsyncClient() as client:
            sim_resp = await client.get(
                f"{KNOWLEDGE_URL}/similar-incidents",
                params={"service": body.service} if body.service else {},
                timeout=3.0,
            )
        if sim_resp.status_code == 200:
            similar = sim_resp.json()
            for s in similar[:5]:
                if s.get("outcome") == "success" and s.get("remediation_used"):
                    recommendations.append(
                        f"Learning: similar incident resolved with: {s.get('remediation_used', '')[:120]}"
                    )
                    break
    except Exception:
        pass

    # Default service when not provided: first anomaly's service or "general"
    incident_service = body.service
    if not incident_service and anomalies:
        incident_service = next((a.get("service") for a in anomalies if a.get("service")), None)
    if not incident_service:
        incident_service = "general"

    iid = str(uuid.uuid4())
    db = SessionLocal()
    try:
        import json
        record = IncidentRecord(
            id=iid,
            anomaly_ids_json=json.dumps([a.get("id") for a in anomalies]),
            service=incident_service,
            root_cause=root_cause,
            evidence_json=json.dumps(evidence),
            recommendations_json=json.dumps(recommendations),
            youcom_citations_json=json.dumps(citations),
        )
        db.add(record)
        db.commit()
    finally:
        db.close()

    # Sync incident to Knowledge for similar-incidents / incidents-by-service (best-effort)
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{KNOWLEDGE_URL}/sync-incident", params={"incident_id": iid}, timeout=5.0)
    except Exception:
        pass

    resp = {
        "id": iid,
        "root_cause": root_cause,
        "evidence": evidence,
        "recommendations": recommendations,
        "youcom_citations": citations,
    }
    # Auto-remediate: generate and optionally execute remediation script
    if body.auto_remediate:
        script = invoke_cline_remediate(root_cause[:50], incident_service, str([a.get("id") for a in anomalies]))
        resp["remediation_script"] = script
        if AUTO_REMEDIATE_EXECUTE_ENABLED:
            resp["remediation_execution"] = run_remediation_script(script)
        else:
            resp["remediation_execution"] = {"note": "Execution disabled. Set AUTO_REMEDIATE_EXECUTE_ENABLED=true."}
    return resp


@app.post("/remediate/{incident_id}")
async def remediate(incident_id: str, execute: bool = False):
    """
    Generate remediation script via Cline CLI for the incident.
    When execute=true and AUTO_REMEDIATE_EXECUTE_ENABLED is set, also run the script.
    """
    db = SessionLocal()
    try:
        row = db.query(IncidentRecord).filter(IncidentRecord.id == incident_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Incident not found")
        import json
        anomaly_ids = json.loads(row.anomaly_ids_json or "[]")
        error_type = row.root_cause or "unknown"
        service = row.service or "example"
        script = invoke_cline_remediate(error_type[:50], service, str(anomaly_ids))
        out = {"incident_id": incident_id, "script": script}
        if execute and AUTO_REMEDIATE_EXECUTE_ENABLED:
            exec_result = run_remediation_script(script)
            out["execution"] = exec_result
        elif execute and not AUTO_REMEDIATE_EXECUTE_ENABLED:
            out["execution"] = {"error": "Execution disabled. Set AUTO_REMEDIATE_EXECUTE_ENABLED=true to enable."}
        return out
    finally:
        db.close()


@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Return full incident details including recommendations and citations."""
    db = SessionLocal()
    try:
        row = db.query(IncidentRecord).filter(IncidentRecord.id == incident_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Incident not found")
        import json
        return {
            "id": row.id,
            "timestamp": row.timestamp.isoformat(),
            "service": row.service,
            "root_cause": row.root_cause,
            "status": row.status,
            "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
            "resolution_notes": row.resolution_notes,
            "recommendations": json.loads(row.recommendations_json or "[]"),
            "youcom_citations": json.loads(row.youcom_citations_json or "[]"),
            "evidence": json.loads(row.evidence_json or "[]"),
        }
    finally:
        db.close()


@app.get("/incidents")
async def get_incidents(limit: int = 20):
    db = SessionLocal()
    try:
        rows = db.query(IncidentRecord).order_by(IncidentRecord.timestamp.desc()).limit(limit).all()
        import json
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "service": r.service,
                "root_cause": r.root_cause,
                "status": r.status,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                "resolution_notes": r.resolution_notes,
            }
            for r in rows
        ]
    finally:
        db.close()


@app.patch("/incidents/{incident_id}")
async def update_incident(incident_id: str, body: UpdateIncidentBody):
    """Update incident status (e.g. close/resolve) for the learning loop."""
    db = SessionLocal()
    try:
        row = db.query(IncidentRecord).filter(IncidentRecord.id == incident_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Incident not found")
        if body.status is not None:
            row.status = body.status
            if body.status == "resolved" and row.resolved_at is None:
                row.resolved_at = datetime.utcnow()
        if body.resolution_notes is not None:
            row.resolution_notes = body.resolution_notes
        db.commit()
        return {"id": incident_id, "status": row.status}
    finally:
        db.close()


@app.post("/incidents/{incident_id}/feedback")
async def submit_feedback(incident_id: str, body: FeedbackBody):
    """
    Submit learning feedback: outcome (success/partial/failed) and optional remediation used.
    Updates incident status to resolved and pushes feedback to Knowledge for similar-incident learning.
    """
    if body.outcome not in ("success", "partial", "failed"):
        raise HTTPException(status_code=400, detail="outcome must be success, partial, or failed")
    db = SessionLocal()
    try:
        row = db.query(IncidentRecord).filter(IncidentRecord.id == incident_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="Incident not found")
        fid = str(uuid.uuid4())
        feedback = IncidentFeedbackRecord(
            id=fid,
            incident_id=incident_id,
            outcome=body.outcome,
            remediation_used=body.remediation_used,
            notes=body.notes,
        )
        db.add(feedback)
        row.status = "resolved"
        if row.resolved_at is None:
            row.resolved_at = datetime.utcnow()
        if body.notes:
            row.resolution_notes = body.notes
        db.commit()
    finally:
        db.close()

    # Push feedback to Knowledge so similar-incidents can surface "what worked"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{KNOWLEDGE_URL}/feedback-incident",
                params={"incident_id": incident_id},
                json={
                    "outcome": body.outcome,
                    "remediation_used": body.remediation_used,
                    "notes": body.notes,
                },
                timeout=5.0,
            )
    except Exception:
        pass

    return {"id": fid, "incident_id": incident_id, "outcome": body.outcome, "status": "resolved"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "recommendation"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
