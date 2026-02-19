# Incident Copilot AI - Environment Setup

Detailed setup instructions for each environment: Local, Dev, Staging, and Production.


## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Environment](#local-environment)
3. [Dev Environment (Kubernetes)](#dev-environment-kubernetes)
4. [Staging Environment](#staging-environment)
5. [Production Environment (LKE)](#production-environment-lke)
6. [Optional Integrations](#optional-integrations)
7. [See Also](#see-also)


## Prerequisites

See [PREREQUISITES.md](PREREQUISITES.md) for required tools, versions, install commands, and troubleshooting.


## Local Environment

### Purpose

Run Incident Copilot AI on your machine for development and testing. No cloud resources required.

### Setup Steps

**1. Clone and enter project**
```bash
cd Incident Copilot
```

**2. Create Python virtual environment**
```bash
python3.11 -m venv venv
source venv/bin/activate   # Linux/macOS
# or: venv\Scripts\activate   # Windows
```

**3. Install Python dependencies**
```bash
pip install fastapi uvicorn httpx pydantic sqlalchemy numpy typer rich
```

**4. Verify Docker**
```bash
docker --version
docker-compose --version
```

### Run Options

**Option A: Docker Compose (recommended)**
```bash
docker-compose up -d
# Services: localhost:8000 (API Gateway), 8001-8005 (microservices)
```

**Option B: Run services locally (for development)**
```bash
mkdir -p data
export DATABASE_URL="sqlite:///$(pwd)/data/incident-copilot.db"
export INGESTION_URL="http://localhost:8001"
export ANOMALY_URL="http://localhost:8002"
export PREDICTION_URL="http://localhost:8003"
export RECOMMENDATION_URL="http://localhost:8004"
export KNOWLEDGE_URL="http://localhost:8005"

./scripts/run_all_local.sh
```

**Option C: Individual services (for debugging)**
```bash
# Terminal 1
cd services/ingestion && uvicorn main:app --reload --port 8001

# Terminal 2
cd services/anomaly && uvicorn main:app --reload --port 8002

# ... repeat for prediction, recommendation, knowledge, api-gateway
```

### Seed Demo Data

Run from the **Incident Copilot root** directory:

```bash
cd Incident Copilot
python scripts/seed_demo_data.py
curl http://localhost:8002/detect   # Trigger anomaly detection
curl http://localhost:8003/predict  # Run prediction
```

### Verify Local Setup

```bash
curl http://localhost:8000/health
# Expected: {"status": {"ingestion": "ok", "anomaly": "ok", ...}}

# Open dashboard
open http://localhost:8000/dashboard-page
```


## Dev Environment (Kubernetes)

### Purpose

Deploy to a development Kubernetes cluster (Minikube, kind, or LKE dev cluster) for integration testing.

### Prerequisites

- Kubernetes cluster (Minikube, kind, or LKE)
- kubectl configured (`kubectl cluster-info`)

### Setup: Minikube

```bash
minikube start
kubectl config use-context minikube
```

### Setup: kind

```bash
kind create cluster --name incident-copilot
kubectl config use-context kind-incident-copilot
```

### Setup: LKE Dev Cluster

See [Production Environment (LKE)](#production-environment-lke) for provisioning. Use `./deploy/provision-lke.sh dev` and set `KUBECONFIG`.

### Deploy to Dev

```bash
# From Incident Copilot root
./deploy/deploy.sh dev build
```

This will:
1. Build all 6 microservice images
2. Install/upgrade Helm chart with `deploy/envs/dev.yaml`
3. Create namespace `incident-copilot` and deploy services

### Access Dev Deployment

```bash
# Port-forward API Gateway
kubectl port-forward svc/api-gateway 8000:8000 -n incident-copilot

# Or use Minikube service (if Minikube)
minikube service api-gateway -n incident-copilot
```

### Dev Environment Config

File: `deploy/envs/dev.yaml`

- 1 replica per service
- Ingress enabled (host: incident-copilot-dev.local)
- Resource limits: 500m CPU, 512Mi memory


## Staging Environment

### Purpose

Pre-production environment on LKE for final validation before production.

### Prerequisites

- LKE cluster for staging
- Container registry (optional, for image push)

### Provision Staging LKE Cluster

```bash
export LINODE_TOKEN="your-linode-api-token"
./deploy/provision-lke.sh staging

export KUBECONFIG=$(pwd)/kubeconfig-staging.yaml
```

### Deploy to Staging

```bash
# Build and push to registry (if using)
export REGISTRY=ghcr.io/your-org
./deploy/build-and-push.sh staging

# Deploy
./deploy/deploy.sh staging
```

### Staging Environment Config

File: `deploy/envs/staging.yaml`

- 1 replica per service
- Ingress with TLS
- Resource limits: 1 CPU, 1Gi memory
- imagePullPolicy: Always


## Production Environment (LKE)

### Purpose

Production deployment on Linode Kubernetes Engine (LKE) for the DeveloperWeek 2026 Hackathon submission.

### Prerequisites

1. **Linode Account**
   - Sign up: https://www.linode.com/
   - Claim $1,000 promotional credit: https://login.linode.com/signup?promo=akm-eve-dev-hack-1000-12126-M866

2. **API Token**
   - Create at: https://cloud.linode.com/profile/tokens
   - Scopes: Read/Write for Linode, LKE

3. **Terraform**
   ```bash
   terraform version  # 1.5+
   ```

### Step 1: Provision LKE Cluster

```bash
export LINODE_TOKEN="your-linode-api-token"
./deploy/provision-lke.sh prod
```

This runs Terraform in `iac/terraform/` and creates:
- LKE cluster: `incident-copilot-ai-prod`
- 2 nodes: g6-standard-2
- Region: us-east (configurable)

### Step 2: Save Kubeconfig

```bash
export KUBECONFIG=$(pwd)/kubeconfig-prod.yaml
kubectl get nodes  # Verify connectivity
```

### Step 3: Build and Push Images

```bash
# If using container registry (recommended for prod)
export REGISTRY=ghcr.io/your-username
./deploy/build-and-push.sh prod

# Or build locally and load (Minikube/kind)
eval $(minikube docker-env)  # For Minikube
./deploy/build-and-push.sh prod
```

### Step 4: Deploy

```bash
./deploy/deploy.sh prod
```

### Step 5: Expose API Gateway

```bash
# Get LoadBalancer external IP
kubectl get svc api-gateway -n incident-copilot -w

# Or use Ingress (configure DNS for ingress.host in deploy/envs/prod.yaml)
```

### Production Environment Config

File: `deploy/envs/prod.yaml`

- 2 replicas per service
- Ingress with TLS
- Resource limits: 2 CPU, 2Gi memory
- imagePullPolicy: Always

## Optional Integrations

### You.com API (Research-Backed Remediation)

```bash
export YOUCOM_API_KEY="your-youcom-api-key"
# Add to Kubernetes: create Secret and envFrom in recommendation deployment
```

### Sanity (Structured Knowledge Base)

```bash
export SANITY_PROJECT_ID="your-project-id"
export SANITY_DATASET="production"
export SANITY_TOKEN="your-token"  # Optional, for writes
```

### Cline CLI (Remediation Script Generation)

Install Cline CLI locally for `incident-copilot remediate` to generate real scripts. Without it, a mock output is returned.

For detailed integration setup, see [INTEGRATIONS.md](INTEGRATIONS.md).


## See Also

- [PREREQUISITES.md](PREREQUISITES.md) – Required tools, install commands, troubleshooting
- [INTEGRATIONS.md](INTEGRATIONS.md) – You.com, Cline CLI, Sanity (detailed setup)
- [DEPLOYMENT.md](DEPLOYMENT.md) – Deployment overview and guides
