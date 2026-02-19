# Incident Copilot

![Incident Copilot Logo](assets/Thumbnail.png)

**Tagline:** Turn alerts into root cause, citations, and remediation scripts.

AI-powered observability platform that analyzes logs, metrics, and traces to detect anomalies, predict failures, and recommend remediation before outages occur.

## Architecture

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                     API Gateway (port 8000)              │
                    └─────────────────────────────────────────────────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         │                    │                │                │                   │
         ▼                    ▼                ▼                ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Ingestion     │ │    Anomaly      │ │  Prediction │ │ Recommendation  │ │    Knowledge    │
│   Service       │ │    Service      │ │   Service   │ │    Service      │ │    Service      │
│   (8001)        │ │    (8002)       │ │   (8003)    │ │    (8004)       │ │    (8005)       │
└────────┬────────┘ └────────┬────────┘ └──────┬──────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                  │                 │                   │
         └───────────────────┴──────────────────┴─────────────────┴───────────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    │  PostgreSQL / SQLite  │  Sanity  │  You.com API   │
                    └──────────────────────────────────────────────────┘
```

## Microservices

| Service | Port | Purpose |
|---------|------|---------|
| api-gateway | 8000 | Single entry point; aggregates data; serves dashboard at /dashboard-page |
| ingestion | 8001 | Ingest logs, metrics, traces |
| anomaly | 8002 | Detect anomalies (statistical + ML) |
| prediction | 8003 | Failure probability scoring |
| recommendation | 8004 | You.com research, Cline CLI, root cause |
| knowledge | 8005 | Sanity integration for runbooks/incidents |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for full stack)
- (Optional) You.com API key, Sanity project, Cline CLI

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install fastapi uvicorn httpx pydantic sqlalchemy numpy typer rich

# Option A: Run with Docker Compose
# Optional: set YOUCOM_API_KEY for live You.com citations (see .env.example)
docker-compose up -d

# Option B: Run all services locally
./scripts/run_all_local.sh

# Option C: Run services individually (in separate terminals)
export DATABASE_URL=sqlite:///./data/incident_copilot.db
cd services/ingestion && uvicorn main:app --reload --port 8001
cd services/anomaly && uvicorn main:app --reload --port 8002
# ... etc for prediction, recommendation, knowledge, api-gateway

# Seed demo data (run from IncidentCopilot root, after ingestion is running)
python scripts/seed_demo_data.py
# Or: ./scripts/run_seed.sh

# Run CLI (from IncidentCopilot directory)
cd cli && pip install -e . && incident-copilot status
```

### CLI Commands

```bash
incident-copilot status
incident-copilot anomalies
incident-copilot predict
incident-copilot explain <incident_id>
incident-copilot remediate <incident_id>
```

### Deploy to Kubernetes / LKE

```bash
# Option 1: Provision LKE + deploy (requires LINODE_TOKEN)
export LINODE_TOKEN="your-token"
./deploy/provision-lke.sh dev
export KUBECONFIG=$(pwd)/kubeconfig-dev.yaml
./deploy/deploy.sh dev build

# Option 2: Deploy to existing cluster
./deploy/deploy.sh dev build

# Option 3: Helm only (pre-built images)
helm upgrade --install incident-copilot ./helm -n incident-copilot --create-namespace -f deploy/envs/dev.yaml
```

See [deploy/README.md](deploy/README.md) for full deployment docs.

## Documentation

Detailed documentation is in the [`docs/`](docs/) directory:

| Document | Contents |
|----------|----------|
| [docs/SETUP.md](docs/SETUP.md) | Prerequisites, environment setup (Local, Dev, Staging, Prod), troubleshooting |
| [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) | Architecture, microservices, data flow, sponsor integrations |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Step-by-step deployment procedures, CI/CD, rollback, verification |
| [docs/REALTIME_DATA_INGESTION.md](docs/REALTIME_DATA_INGESTION.md) | Real-time data ingestion for pre-prod and prod testing |
| [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md) | You.com API, Cline CLI, Sanity - detailed integration docs |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | sqlite:///./incident_copilot.db |
| YOUCOM_API_KEY | You.com API key (optional) | - |
| SANITY_PROJECT_ID | Sanity project ID (optional); enables Similar incidents from Sanity | - |
| SANITY_DATASET | Sanity dataset | production |
| SANITY_TOKEN | Sanity API token (optional) | - |

For local/Docker: copy `.env.example` to `.env` and set `YOUCOM_API_KEY` and optionally `SANITY_PROJECT_ID`. See [docs/DEPLOYMENT-LOCAL.md](docs/DEPLOYMENT-LOCAL.md) and [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md).

## Deployment Environments

| Environment | Target | IaC / Deploy |
|-------------|--------|--------------|
| **Local** | Docker Compose | `make local` or `docker-compose up -d` |
| **Dev** | Minikube / LKE | `./deploy/deploy.sh dev build` |
| **Staging** | LKE | `./deploy/deploy.sh staging build` |
| **Prod** | LKE | `./deploy/deploy.sh prod build` |

**Infrastructure (Terraform):** `iac/terraform/` provisions Linode LKE.  
**Scripts:** `deploy/provision-lke.sh` creates cluster; `deploy/deploy.sh` deploys via Helm.

## Sanity Studio (optional)

Deploy Sanity Studio for **Similar incidents** from the CLI:

```bash
# One-time: sanity login; add SANITY_PROJECT_ID to .env
make sanity-deploy
# or: ./scripts/sanity-deploy.sh
```

See [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md#deploy-sanity-studio-from-cli-automated) and [docs/DEPLOYMENT-LOCAL.md](docs/DEPLOYMENT-LOCAL.md#optional-sanity-integration).


**Setup (quick):**
```bash
# Local: Docker Compose
docker-compose up -d

# Minikube (LKE-ready when Linode account available)
minikube start
./deploy/deploy-minikube.sh dev
kubectl port-forward svc/api-gateway 8000:8000 -n incident-copilot
```

**LKE-ready:** Same Helm chart deploys to Minikube or LKE. Use `./deploy/deploy-minikube.sh dev` when Linode account unavailable; use `./deploy/deploy.sh prod build` for LKE.
