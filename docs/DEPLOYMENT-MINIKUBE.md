# Incident Copilot AI - Minikube / kind Deployment

Step-by-step procedure for deploying Incident Copilot AI to Minikube or kind for local Kubernetes development.


## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Minikube - Recommended Flow](#minikube---recommended-flow)
3. [Minikube - Alternative Flow](#minikube---alternative-flow)
4. [kind](#kind)
5. [Verify](#verify)
6. [Troubleshooting](#troubleshooting)
7. [See Also](#see-also)


## Prerequisites

- Minikube or kind installed
- kubectl configured
- Docker installed (Docker Desktop or Docker Engine)


## Minikube - Recommended Flow

This flow builds images with your host Docker and loads them into Minikube. It avoids the Docker API version mismatch that can occur when using Minikube's Docker daemon.

```bash
# 1. Start cluster (do NOT run eval $(minikube docker-env))
minikube start

# 2. Build, load images, and deploy
cd Incident Copilot
./deploy/deploy-minikube.sh dev

# 3. Expose API Gateway
kubectl port-forward svc/api-gateway 8000:8000 -n incident-copilot
```


## Minikube - Alternative Flow

If your Docker client supports API 1.44 or later, you can build directly in Minikube's Docker daemon:

```bash
# 1. Start cluster
minikube start

# 2. Use Minikube Docker daemon (images built here are visible to Minikube)
eval $(minikube docker-env)

# 3. Build and deploy
cd Incident Copilot
./deploy/deploy.sh dev build

# 4. Expose API Gateway
kubectl port-forward svc/api-gateway 8000:8000 -n incident-copilot
```


## kind

```bash
# 1. Create cluster
kind create cluster --name incident-copilot

# 2. Build images (host Docker)
./deploy/build-and-push.sh dev

# 3. Load images into kind
kind load docker-image incident-copilot/ingestion:dev --name incident-copilot
kind load docker-image incident-copilot/anomaly:dev --name incident-copilot
kind load docker-image incident-copilot/prediction:dev --name incident-copilot
kind load docker-image incident-copilot/recommendation:dev --name incident-copilot
kind load docker-image incident-copilot/knowledge:dev --name incident-copilot
kind load docker-image incident-copilot/api-gateway:dev --name incident-copilot

# 4. Deploy
./deploy/deploy.sh dev

# 5. Port-forward
kubectl port-forward svc/api-gateway 8000:8000 -n incident-copilot
```


## Verify

```bash
kubectl get pods -n incident-copilot
kubectl get svc -n incident-copilot
curl http://localhost:8000/health
```


## Troubleshooting

### Error: "client version 1.41 is too old. Minimum supported API version is 1.44"

**Cause:** Minikube's Docker daemon expects API 1.44, but your host Docker client reports an older API version.

**Fix options:**

1. **Use the recommended flow** – Run `./deploy/deploy-minikube.sh dev` instead. This builds with host Docker and loads images into Minikube, avoiding the API mismatch.

2. **Upgrade Docker client** – Update Docker Desktop to the latest version (Docker Desktop → Check for Updates, or download from [docker.com](https://www.docker.com/products/docker-desktop)). Then the alternative flow with `eval $(minikube docker-env)` will work.


## See Also

- [DEPLOYMENT.md](DEPLOYMENT.md) – Deployment overview, rollback, and verification checklist
- [SETUP.md](SETUP.md) – Environment setup and prerequisites
