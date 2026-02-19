# Incident Copilot - Deployment Guide

Step-by-step deployment procedures for each environment.


## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Deployment Guides](#deployment-guides)
3. [CI/CD (GitHub Actions)](#cicd-github-actions)
4. [Rollback and Maintenance](#rollback-and-maintenance)
5. [Verification Checklist](#verification-checklist)
6. [See Also](#see-also)


## Deployment Overview

| Environment | Method | Build | Registry | Duration (approx) |
|-------------|--------|-------|----------|-------------------|
| Local | Docker Compose | Yes | No | 2–3 min |
| Dev (Minikube / kind) | Helm + K8s | Yes | Optional | 5–10 min |
| Staging | Helm + LKE | Yes | Recommended | 15–20 min |
| Prod | Helm + LKE | Yes | Required | 20–30 min |


## Deployment Guides

| Environment | Guide | Key Commands |
|-------------|-------|--------------|
| **Local** | [DEPLOYMENT-LOCAL.md](DEPLOYMENT-LOCAL.md) | `docker-compose up -d` |
| **Minikube / kind** | [DEPLOYMENT-MINIKUBE.md](DEPLOYMENT-MINIKUBE.md) | `./deploy/deploy-minikube.sh dev` |
| **Staging (LKE)** | [DEPLOYMENT-LKE.md](DEPLOYMENT-LKE.md) | `./deploy/provision-lke.sh staging` |
| **Production (LKE)** | [DEPLOYMENT-LKE.md](DEPLOYMENT-LKE.md) | `./deploy/provision-lke.sh prod` |


## CI/CD (GitHub Actions)

### Workflow: `.github/workflows/deploy.yml`

- **Trigger:** Manual (`workflow_dispatch`)
- **Inputs:** Environment (dev, staging, prod)
- **Secrets:** `KUBECONFIG` (base64-encoded kubeconfig)

### Setup

1. Encode kubeconfig:
   ```bash
   cat kubeconfig-prod.yaml | base64 -w0
   ```

2. Add GitHub secret:
   - Repo → Settings → Secrets → Actions
   - New secret: `KUBECONFIG` = base64 output

3. Run workflow:
   - Actions → Deploy → Run workflow → Select environment

### Note

The workflow deploys existing images. For full CI/CD with build, add a separate build job or use registry images built elsewhere.


## Rollback and Maintenance

### Rollback Helm Release

```bash
helm history incident-copilot -n incident-copilot
helm rollback incident-copilot <revision> -n incident-copilot
```

### Scale Down

```bash
helm upgrade incident-copilot ./helm -n incident-copilot \
  --set ingestion.replicaCount=0 \
  --set anomaly.replicaCount=0 \
  # ... etc
```

### Delete Deployment

```bash
helm uninstall incident-copilot -n incident-copilot
kubectl delete pvc incident-copilot-data -n incident-copilot
kubectl delete namespace incident-copilot
```

### Destroy LKE Infrastructure

```bash
cd iac/terraform
terraform destroy -var="environment=prod" -var="linode_token=$LINODE_TOKEN"
```


## Verification Checklist

After deployment, verify:

| Check | Command | Expected |
|-------|---------|----------|
| Pods running | `kubectl get pods -n incident-copilot` | All Running |
| API health | `curl $URL/health` | All services "ok" |
| Dashboard | `curl $URL/dashboard` | JSON with anomalies, predictions, etc. |
| CLI status | `incident-copilot status` | Services ok, prediction % |
| Ingress (if enabled) | `curl -H Host: $INGRESS_HOST $URL` | 200 |


## See Also

- [PREREQUISITES.md](PREREQUISITES.md) – Required tools and troubleshooting
- [SETUP.md](SETUP.md) – Environment setup
- [INTEGRATIONS.md](INTEGRATIONS.md) – You.com, Cline CLI, Sanity
- [IMPLEMENTATION.md](IMPLEMENTATION.md) – Architecture and microservices
