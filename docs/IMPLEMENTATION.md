# Incident Copilot - Implementation Guide

Technical implementation details, architecture, and code structure.


## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Microservices](#microservices)
4. [Data Flow](#data-flow)
5. [Storage](#storage)
6. [Sponsor Integrations](#sponsor-integrations)
7. [Configuration](#configuration)

---

## Architecture Overview

```
                         ┌──────────────────────────────────────┐
                         │           API Gateway :8000           │
                         │  (Dashboard, health, aggregator)      │
                         └────────────────────┬─────────────────┘
                                              │
        ┌─────────────┬─────────────┬─────────┼─────────┬─────────────┐
        │             │             │         │         │             │
        ▼             ▼             ▼         ▼         ▼             ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
  │Ingestion │ │ Anomaly  │ │Prediction│ │Recommend.│ │Knowledge │
  │  :8001   │ │  :8002   │ │  :8003   │ │  :8004   │ │  :8005   │
  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
       │            │            │            │            │
       └────────────┴────────────┴────────────┴────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
              │ SQLite    │   │ You.com   │   │  Sanity   │
              │ (shared   │   │   API     │   │  (opt)    │
              │  PVC)     │   │           │   │           │
              └───────────┘   └───────────┘   └───────────┘
```

### Design Principles

- **Stateless microservices** where possible; shared SQLite/PostgreSQL for persistence
- **API Gateway** as single entry point for dashboard and CLI
- **Inter-service communication** via HTTP; K8s internal DNS for service discovery


## Project Structure

```
IncidentCopilot/
├── services/                 # Microservices
│   ├── ingestion/            # Logs, metrics ingestion
│   ├── anomaly/              # Anomaly detection
│   ├── prediction/           # Failure probability
│   ├── recommendation/       # You.com, Cline, root cause
│   ├── knowledge/            # Sanity, runbooks
│   └── api-gateway/          # Aggregator, dashboard
├── cli/                      # incident-copilot CLI
├── shared/                   # Shared models, config
├── dashboard/                # Static dashboard HTML
├── docker/                   # Dockerfiles per service
├── helm/                     # Helm chart
│   ├── templates/            # K8s manifests
│   └── values.yaml
├── deploy/                   # Deployment scripts
│   ├── envs/                 # dev, staging, prod values
│   ├── deploy.sh
│   ├── build-and-push.sh
│   └── provision-lke.sh
├── iac/
│   └── terraform/            # LKE provisioning
├── scripts/                  # Seed data, run local
├── docs/                     # Documentation
└── Incident_Copilot_SRS.md   # Requirements
```


## Microservices

### 1. Ingestion Service (port 8001)

**Purpose:** Ingest logs and metrics; store in SQLite.

**Endpoints:**
- `POST /ingest/logs` - Single log entry
- `POST /ingest/logs/batch` - Batch logs
- `POST /ingest/metrics` - Metric sample
- `GET /logs` - Retrieve logs
- `GET /metrics` - Retrieve metrics
- `GET /health` - Health check

**Dependencies:** None (writes to DB first)

**Database tables:** `logs`, `metrics`


### 2. Anomaly Service (port 8002)

**Purpose:** Detect anomalies using statistical methods (Z-score).

**Endpoints:**
- `GET /detect` - Fetch metrics from ingestion, run anomaly detection, store results
- `GET /anomalies` - List detected anomalies
- `GET /health` - Health check

**Dependencies:** Ingestion (fetches metrics via HTTP)

**Algorithm:** Z-score > 3.0 standard deviations marks anomaly

**Database tables:** `anomalies`


### 3. Prediction Service (port 8003)

**Purpose:** Compute failure probability (0–100%) from anomalies and logs.

**Endpoints:**
- `GET /predict` - Run prediction, return score and factors
- `GET /predictions` - List recent predictions
- `GET /health` - Health check

**Dependencies:** Ingestion, Anomaly

**Algorithm:** Heuristic scoring from anomaly count, severity, error log volume

**Database tables:** `predictions`


### 4. Recommendation Service (port 8004)

**Purpose:** Root cause analysis, You.com research, Cline CLI remediation.

**Endpoints:**
- `POST /explain` - Create incident, call You.com, return root cause and citations. Body may include `auto_remediate: true` to generate and optionally execute remediation.
- `POST /remediate/{incident_id}?execute=true` - Invoke Cline CLI for script generation; when `execute=true` and `AUTO_REMEDIATE_EXECUTE_ENABLED`, also run the script.
- `GET /incidents` - List incidents
- `GET /health` - Health check

**Dependencies:** Anomaly

**Sponsor integrations:**
- **You.com:** Search API for citation-backed remediation
- **CLINE:** Cline CLI subprocess for script generation (mock if not installed)

**Database tables:** `incidents`

### 5. Knowledge Service (port 8005)

**Purpose:** Structured incident/runbook storage; Sanity integration.

**Endpoints:**
- `GET /similar-incidents` - Query similar past incidents (includes outcome, remediation_used when present)
- `GET /incidents-by-service` - Incidents grouped by service
- `POST /sync-incident` - Sync incident from recommendation service
- `POST /feedback-incident` - Record learning feedback (outcome, remediation_used) for an incident
- `GET /runbooks`, `POST /runbooks` - Runbook CRUD
- `GET /health` - Health check

**Dependencies:** Recommendation (for sync)

**Sponsor integration:** **Sanity** – GROQ queries when `SANITY_PROJECT_ID` set

**Database tables:** `runbooks`, `incident_refs`


### 6. API Gateway (port 8000)

**Purpose:** Single entry point; aggregate data for dashboard; serve static dashboard.

**Endpoints:**
- `GET /` - Service info
- `GET /health` - Aggregated health of all services
- `GET /dashboard` - Aggregated data for dashboard
- `GET /status` - CLI status (services + latest prediction)
- `GET /logs`, `/anomalies`, `/predictions`, `/incidents` - Proxied
- `GET /incidents/{id}`, `PATCH /incidents/{id}`, `POST /incidents/{id}/feedback` - Proxied
- `POST /explain`, `POST /remediate/{id}` - Proxied
- `GET /predict` - Proxied
- `GET /dashboard-page` - Static dashboard HTML

**Dependencies:** All 5 backend services


## Data Flow

### Telemetry Pipeline

```
Logs/Metrics → Ingestion → SQLite
                    ↓
              Anomaly /detect (polls metrics)
                    ↓
              Anomaly → anomalies table
                    ↓
              Prediction /predict (uses anomalies + logs)
                    ↓
              Prediction → predictions table
```

### Incident and Remediation Flow

```
Anomaly detected → POST /explain (recommendation)
                        ↓
                  You.com API (search)
                        ↓
                  Incident created (root cause, citations)
                        ↓
                  POST /remediate/{id} [optionally ?execute=true] → Cline CLI (or mock)
                        ↓
                  Script returned; if execute=true and AUTO_REMEDIATE_EXECUTE_ENABLED, script is run
```

### Auto-Remediation Execution

1. **Remediate with execution** – `POST /remediate/{id}?execute=true` generates the script and, when `AUTO_REMEDIATE_EXECUTE_ENABLED` is set, runs it via subprocess. Response includes `execution` with `stdout`, `stderr`, `returncode`.

2. **Auto-remediate on explain** – `POST /explain` with body `{"auto_remediate": true}` creates the incident and immediately generates (and optionally executes) remediation. Response includes `remediation_script` and `remediation_execution`.

3. **Safety** – Execution is opt-in: set `AUTO_REMEDIATE_EXECUTE_ENABLED=true` in the recommendation service environment. Without it, `execute=true` returns a note that execution is disabled.

### Incident Learning Feedback Loop

When users resolve incidents or run remediation, they can submit **feedback** so future similar incidents get better recommendations.

1. **Close / resolve incident**  
   `PATCH /incidents/{id}` with `{"status": "resolved", "resolution_notes": "..."}`.

2. **Submit feedback**  
   `POST /incidents/{id}/feedback` with `{"outcome": "success"|"partial"|"failed", "remediation_used": "...", "notes": "..."}`.  
   - Recommendation service stores the feedback in `incident_feedback` and marks the incident resolved.  
   - It then calls Knowledge `POST /feedback-incident` so the incident ref is updated with `outcome` and `remediation_used`.

3. **Similar incidents**  
   `GET /similar-incidents` returns `outcome` and `remediation_used` when present. Results are ordered so **success** outcomes appear first.

4. **Explain uses learning**  
   When creating a new incident, `POST /explain` calls `GET /similar-incidents` (by service). If any similar incident has `outcome == "success"` and `remediation_used`, it adds a recommendation line:  
   `"Learning: similar incident resolved with: <remediation_used>"`.

**Tables:** Recommendation adds `incident_feedback`; Knowledge extends `incident_refs` with `outcome`, `remediation_used`, `resolved_at`.


## Storage

### SQLite (Default)

- **Path:** `/data/incident_copilot.db` (K8s) or `./data/incident_copilot.db` (local)
- **Tables:** logs, metrics, anomalies, predictions, incidents, incident_feedback, runbooks, incident_refs
- **Shared PVC:** All services that need persistence mount the same PVC in K8s

### PostgreSQL (Future)

Set `DATABASE_URL=postgresql://user:pass@host:5432/db` for production scale. Schema is compatible (SQLAlchemy ORM).


## Sponsor Integrations

| Sponsor | Service | Integration Point |
|---------|---------|-------------------|
| **Akamai** | All | LKE deployment, Terraform, Helm |
| **You.com** | recommendation | `youcom_search()` in `/explain` |
| **Sanity** | knowledge | `sanity_query()` for GROQ (when configured) |
| **CLINE** | recommendation | `invoke_cline_remediate()` in `/remediate` |


## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | sqlite:///./incident_copilot.db | Database connection |
| INGESTION_URL | http://localhost:8001 | Ingestion service URL |
| ANOMALY_URL | http://localhost:8002 | Anomaly service URL |
| PREDICTION_URL | http://localhost:8003 | Prediction service URL |
| RECOMMENDATION_URL | http://localhost:8004 | Recommendation service URL |
| KNOWLEDGE_URL | http://localhost:8005 | Knowledge service URL |
| YOUCOM_API_KEY | (empty) | You.com API key |
| AUTO_REMEDIATE_EXECUTE_ENABLED | false | If true, remediate with ?execute=true runs the script |
| SANITY_PROJECT_ID | (empty) | Sanity project ID |
| SANITY_DATASET | production | Sanity dataset |
| SANITY_TOKEN | (empty) | Sanity API token |
| CLOUDSENTINEL_API_URL | http://localhost:8000 | API URL for CLI |

### Kubernetes ConfigMap

All service URLs and `DATABASE_URL` are in `helm/templates/configmap.yaml`. Secrets (e.g. YOUCOM_API_KEY) should be in a K8s Secret and mounted as env.


## See Also

- [PREREQUISITES.md](PREREQUISITES.md) – Required tools and environment setup
- [INTEGRATIONS.md](INTEGRATIONS.md) – You.com, Cline CLI, Sanity (detailed integration docs)
- [DEPLOYMENT.md](DEPLOYMENT.md) – Deployment overview and guides
