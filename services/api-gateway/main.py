"""API Gateway - single entry point for dashboard and CLI."""

import os
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx

INGESTION_URL = os.getenv("INGESTION_URL", "http://localhost:8001")
ANOMALY_URL = os.getenv("ANOMALY_URL", "http://localhost:8002")
PREDICTION_URL = os.getenv("PREDICTION_URL", "http://localhost:8003")
RECOMMENDATION_URL = os.getenv("RECOMMENDATION_URL", "http://localhost:8004")
KNOWLEDGE_URL = os.getenv("KNOWLEDGE_URL", "http://localhost:8005")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Incident Copilot API Gateway",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount dashboard if available (docker: /app/dashboard, local: ../../dashboard)
_dashboard_path = Path(__file__).resolve().parent / "dashboard"
if not _dashboard_path.exists():
    _dashboard_path = Path(__file__).resolve().parents[2] / "dashboard"
if _dashboard_path.exists():
    @app.get("/dashboard-page")
    async def dashboard_page():
        return FileResponse(_dashboard_path / "index.html")
    # Serve static assets from dashboard if any
    app.mount("/static", StaticFiles(directory=str(_dashboard_path)), name="static")


async def fetch(url: str, path: str = ""):
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(f"{url}{path}")
        if r.status_code != 200:
            return None
        return r.json()


@app.get("/")
async def root():
    return {"service": "Incident Copilot API Gateway", "version": "1.0.0"}


@app.get("/health")
async def health():
    status = {}
    for name, url in [
        ("ingestion", INGESTION_URL),
        ("anomaly", ANOMALY_URL),
        ("prediction", PREDICTION_URL),
        ("recommendation", RECOMMENDATION_URL),
        ("knowledge", KNOWLEDGE_URL),
    ]:
        try:
            r = await fetch(url, "/health")
            status[name] = "ok" if r else "error"
        except Exception:
            status[name] = "down"
    return {"status": status}


@app.get("/dashboard")
async def dashboard():
    """Aggregate data for dashboard: status, anomalies, predictions, incidents."""
    data = {}
    try:
        anomalies = await fetch(ANOMALY_URL, "/anomalies?limit=20")
        data["anomalies"] = anomalies or []
    except Exception:
        data["anomalies"] = []

    try:
        predictions = await fetch(PREDICTION_URL, "/predictions?limit=5")
        data["predictions"] = predictions or []
    except Exception:
        data["predictions"] = []

    try:
        incidents = await fetch(RECOMMENDATION_URL, "/incidents?limit=10")
        data["incidents"] = incidents if isinstance(incidents, list) else []
    except Exception:
        data["incidents"] = []

    try:
        logs = await fetch(INGESTION_URL, "/logs?limit=20")
        data["logs"] = logs or []
    except Exception:
        data["logs"] = []

    try:
        similar = await fetch(KNOWLEDGE_URL, "/similar-incidents")
        data["similar_incidents"] = similar if isinstance(similar, list) and similar else []
    except Exception:
        data["similar_incidents"] = []

    # Fallback: when no similar incidents from knowledge (e.g. fresh deploy, no Sanity),
    # show recent incidents so the Similar section is not empty
    incidents_list = data.get("incidents") if isinstance(data.get("incidents"), list) else []
    if not data["similar_incidents"] and incidents_list:
        data["similar_incidents"] = [
            {"service": i.get("service"), "root_cause": i.get("root_cause"), "id": i.get("id")}
            for i in incidents_list
        ]

    return data


@app.get("/status")
async def status():
    """CLI status - cluster health overview."""
    h = await health()
    pred = await fetch(PREDICTION_URL, "/predict")
    return {
        "services": h["status"],
        "latest_prediction": pred,
    }


@app.get("/logs")
async def logs(limit: int = 100):
    return await fetch(INGESTION_URL, f"/logs?limit={limit}") or []


@app.get("/anomalies")
async def anomalies(limit: int = 50):
    return await fetch(ANOMALY_URL, f"/anomalies?limit={limit}") or []


@app.get("/predictions")
async def predictions(limit: int = 20):
    return await fetch(PREDICTION_URL, f"/predictions?limit={limit}") or []


@app.get("/incidents")
async def incidents(limit: int = 20):
    return await fetch(RECOMMENDATION_URL, f"/incidents?limit={limit}") or []


@app.get("/incidents/{incident_id}")
async def incident_detail(incident_id: str):
    data = await fetch(RECOMMENDATION_URL, f"/incidents/{incident_id}")
    if data is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return data


@app.patch("/incidents/{incident_id}")
async def update_incident(incident_id: str, request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.patch(
            f"{RECOMMENDATION_URL}/incidents/{incident_id}",
            json={"status": payload.get("status"), "resolution_notes": payload.get("resolution_notes")},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


@app.post("/incidents/{incident_id}/feedback")
async def incident_feedback(incident_id: str, request: Request):
    """Submit learning feedback (outcome, remediation_used) for an incident."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    outcome = payload.get("outcome")
    if not outcome:
        raise HTTPException(status_code=400, detail="outcome required (success, partial, failed)")
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{RECOMMENDATION_URL}/incidents/{incident_id}/feedback",
            json={
                "outcome": outcome,
                "remediation_used": payload.get("remediation_used"),
                "notes": payload.get("notes"),
            },
        )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


@app.post("/explain")
async def explain(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    json_body = {
        "anomaly_ids": payload.get("anomaly_ids") or [],
        "service": payload.get("service"),
        "auto_remediate": bool(payload.get("auto_remediate")),
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(
            f"{RECOMMENDATION_URL}/explain",
            json=json_body,
        )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


@app.post("/remediate/{incident_id}")
async def remediate(incident_id: str, execute: bool = False):
    async with httpx.AsyncClient(timeout=60.0) as client:
        url = f"{RECOMMENDATION_URL}/remediate/{incident_id}"
        if execute:
            url += "?execute=true"
        r = await client.post(url)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()


@app.get("/detect")
async def run_detect(service: str | None = None):
    """Trigger anomaly detection on ingestion metrics."""
    data = await fetch(ANOMALY_URL, f"/detect?service={service}" if service else "/detect")
    if data is None:
        raise HTTPException(status_code=502, detail="Anomaly service unavailable")
    return data


@app.get("/predict")
async def run_predict():
    pred = await fetch(PREDICTION_URL, "/predict")
    if pred is None:
        raise HTTPException(status_code=502, detail="Prediction service unavailable")
    return pred


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
