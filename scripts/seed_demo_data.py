#!/usr/bin/env python3
"""Seed demo data for Incident Copilot - logs and metrics for testing.

Run from IncidentCopilot root:
  cd IncidentCopilot
  python scripts/seed_demo_data.py

Or with custom ingestion URL:
  INGESTION_URL=http://localhost:8001 python scripts/seed_demo_data.py
"""

import os
import random

import httpx

INGESTION_URL = os.getenv("INGESTION_URL", "http://localhost:8001")


def main():
    print("Seeding demo data...")
    try:
        r = httpx.get(f"{INGESTION_URL}/health", timeout=3)
    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        print(f"Error: Cannot connect to Ingestion service at {INGESTION_URL}")
        print("  Start it first: ./scripts/run_all_local.sh")
        print("  Or: cd services/ingestion && uvicorn main:app --port 8001")
        raise SystemExit(1) from e

    # Logs - mix of levels
    logs = []
    for i in range(50):
        level = random.choice(["info", "info", "info", "warn", "error"])
        logs.append({
            "level": level,
            "message": f"Demo log message {i} - {level}",
            "source": "demo",
            "service": random.choice(["api", "worker", "ingestion"]),
        })
    r = httpx.post(f"{INGESTION_URL}/ingest/logs/batch", json=logs)
    print(f"Logs: {r.status_code}")

    # Metrics - some with anomalies (spike)
    base = 50.0
    for i in range(100):
        val = base + random.gauss(0, 10)
        if i > 80:
            val += random.uniform(30, 80)  # Simulate spike
        r = httpx.post(f"{INGESTION_URL}/ingest/metrics", json={
            "name": "cpu_usage",
            "value": max(0, min(100, val)),
            "service": "api",
        })
    print("Metrics: seeded")
    print("Done. Run anomaly detection: curl http://localhost:8002/detect")
    print("Run prediction: curl http://localhost:8003/predict")
    print("Dashboard: open dashboard/index.html with API at http://localhost:8000")


if __name__ == "__main__":
    main()
