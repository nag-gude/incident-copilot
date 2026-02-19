# Akamai Technologies – Build the Most Creative Open-Source Solution on Linode

**Sponsor challenge:** Akamai Technologies - Build the Most Creative Open-Source Solution on Linode  
**Project:** Incident Copilot – DeveloperWeek 2026


## How Incident Copilot Addresses the Challenge

Incident Copilot is a **fully open-source** observability and incident-response stack that runs on **Linode Kubernetes Engine (LKE)** and on **Minikube** with the same deployment path. We use a single **Helm chart** and **Terraform** for LKE provisioning, so the “most creative” aspect is a **unified pipeline**: ingest → detect → predict → explain (with You.com) → remediate (with Cline) → learn (with Sanity), all deployable on Linode or locally with one set of manifests.

The solution is creative in bringing together four sponsor technologies into one product and making it easy to run on Linode (or Minikube when an Linode account isn’t available).


## What We Built

- **Stack:** Python 3.11+, FastAPI, SQLite (PostgreSQL-ready), vanilla JS dashboard. All dependencies are open-source (e.g. scikit-learn, numpy for ML).
- **Deployment:**
  - **Linode (LKE):** Terraform in `iac/terraform/` for LKE cluster provisioning; `deploy/provision-lke.sh`; `deploy/deploy.sh` with envs (dev/staging/prod) for build-and-deploy. Images can be built and pushed to a registry, then deployed via Helm.
  - **Minikube:** Same Helm chart; `deploy/deploy-minikube.sh` (or equivalent) so the project runs without a Linode account.
  - **Helm:** `helm/` with templates for all services (ingestion, anomaly, prediction, recommendation, knowledge, api-gateway), ConfigMap, PVC, optional Ingress. One chart for both LKE and Minikube.
- **Public repo:** Code, Dockerfiles, Helm charts, and docs are in the open for judges and the community.


## Technical Details

| Item | Detail |
|------|--------|
| **Orchestration** | Kubernetes (LKE or Minikube) |
| **Package manager** | Helm 3; values in `helm/values.yaml`, env-specific in `deploy/envs/*.yaml` |
| **IaC** | Terraform for LKE (e.g. cluster, node pool); `LINODE_TOKEN` for provider |
| **Containers** | Dockerfiles per service under `docker/`; build/push via `deploy/build-and-push.sh` |
| **Data** | Shared SQLite (or PostgreSQL) via PVC; no proprietary databases |


## Installation

**Option A – Docker Compose (fastest, no K8s):**

```bash
cd IncidentCopilot
docker-compose up -d
# Dashboard: http://localhost:8000/dashboard-page
```

**Option B – Minikube (K8s, no Linode):**

```bash
minikube start
./deploy/deploy-minikube.sh dev   # or: helm upgrade --install incident-copilot ./helm -n incident-copilot --create-namespace -f deploy/envs/dev.yaml
kubectl port-forward svc/api-gateway 8000:8000 -n incident-copilot
# Dashboard: http://localhost:8000/dashboard-page
```

**Option C – Linode LKE:**

```bash
export LINODE_TOKEN=your-token
./deploy/provision-lke.sh dev
export KUBECONFIG=$(pwd)/kubeconfig-dev.yaml
./deploy/deploy.sh dev build
# Access via LoadBalancer or: kubectl port-forward svc/api-gateway 8000:8000 -n incident-copilot
```

**Prerequisites:** Docker (and Docker Compose for Option A); Minikube + kubectl for Option B; Linode account + Terraform for Option C. See [PREREQUISITES.md](../PREREQUISITES.md) and [DEPLOYMENT-LOCAL.md](../DEPLOYMENT-LOCAL.md).


## Testing examples

**Health check (all services):**

```bash
# Via gateway (Compose or port-forward)
curl -s http://localhost:8000/health | python3 -m json.tool
# Expect: "status": { "ingestion": "ok", "anomaly": "ok", ... }
```

**Dashboard payload (aggregated data):**

```bash
curl -s http://localhost:8000/dashboard | python3 -m json.tool
# Expect: anomalies, predictions, incidents, logs, similar_incidents
```

**Service health (single service):**

```bash
curl -s http://localhost:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',{}))"
```

**Minikube / K8s: list pods:**

```bash
kubectl get pods -n incident-copilot
```


## How to Verify (Demo / Judging)

1. **Minikube (no Linode):**  
   `minikube start` → deploy with the Helm chart (e.g. `./deploy/deploy-minikube.sh dev` or `helm upgrade --install incident-copilot ./helm -n incident-copilot --create-namespace -f deploy/envs/dev.yaml`) → `kubectl port-forward svc/api-gateway 8000:8000` → open dashboard at `http://localhost:8000/dashboard-page`.

2. **LKE (Linode):**  
   Set `LINODE_TOKEN` → run Terraform/provision script → set `KUBECONFIG` → run `./deploy/deploy.sh dev build` (or equivalent) → access via LoadBalancer or Ingress.

3. **Local (Docker Compose):**  
   `docker-compose up -d` → dashboard at `http://localhost:8000/dashboard-page`.

In all cases, the same open-source code and Helm chart are used; only the target (LKE vs Minikube vs Compose) changes.


## Links

- **Repo:** [GitHub](https://github.com/nag-gude/incident-copilot)
- **Helm:** `helm/`, `deploy/envs/`  
- **Terraform:** `iac/terraform/`  
- **Docs:** [DEPLOYMENT-LOCAL.md](../DEPLOYMENT-LOCAL.md), [DEPLOYMENT-MINIKUBE.md](../DEPLOYMENT-MINIKUBE.md), [DEPLOYMENT-LKE.md](../DEPLOYMENT-LKE.md), [IMPLEMENTATION.md](../IMPLEMENTATION.md).
