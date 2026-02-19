#!/bin/bash
# Run all Incident Copilot services locally (development)
set -e
# Run from IncidentCopilot directory (parent of scripts/)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p data

# Check for port conflicts
CONFLICTS=""
for port in 8000 8001 8002 8003 8004 8005; do
  if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
    CONFLICTS="$CONFLICTS $port"
  fi
done
if [ -n "$CONFLICTS" ]; then
  echo "Port(s) in use:$CONFLICTS"
  echo "Free them with: for p in 8000 8001 8002 8003 8004 8005; do kill \$(lsof -ti :\$p) 2>/dev/null; done"
  exit 1
fi
export DATABASE_URL="sqlite:///${ROOT}/data/incident_copilot.db"
export INGESTION_URL="http://localhost:8001"
export ANOMALY_URL="http://localhost:8002"
export PREDICTION_URL="http://localhost:8003"
export RECOMMENDATION_URL="http://localhost:8004"
export KNOWLEDGE_URL="http://localhost:8005"

(cd services/ingestion && uvicorn main:app --host 0.0.0.0 --port 8001) &
(cd services/anomaly && uvicorn main:app --host 0.0.0.0 --port 8002) &
(cd services/prediction && uvicorn main:app --host 0.0.0.0 --port 8003) &
(cd services/recommendation && uvicorn main:app --host 0.0.0.0 --port 8004) &
(cd services/knowledge && uvicorn main:app --host 0.0.0.0 --port 8005) &
sleep 2
(cd services/api-gateway && uvicorn main:app --host 0.0.0.0 --port 8000) &

echo "All services starting. API Gateway: http://localhost:8000"
echo "Dashboard: open dashboard/index.html"
echo "Press Ctrl+C to stop."
wait
