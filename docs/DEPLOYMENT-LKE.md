# Incident Copilot AI - Linode LKE Deployment

Step-by-step procedure for deploying Incident Copilot AI to Linode Kubernetes Engine (LKE) for staging and production.


## Table of Contents

1. [Staging (LKE)](#staging-lke)
2. [Production (LKE)](#production-lke)
3. [See Also](#see-also)


## Staging (LKE)

### Prerequisites

- Linode account and API token
- Terraform installed
- kubectl and Helm installed

### Procedure

```bash
cd Incident Copilot

# 1. Provision LKE cluster
export LINODE_TOKEN="your-linode-api-token"
./deploy/provision-lke.sh staging

# 2. Configure kubectl
export KUBECONFIG=$(pwd)/kubeconfig-staging.yaml
kubectl get nodes

# 3. (Optional) Push images to registry
export REGISTRY=ghcr.io/your-org
./deploy/build-and-push.sh staging

# 4. Deploy
./deploy/deploy.sh staging

# 5. Get LoadBalancer IP
kubectl get svc api-gateway -n incident-copilot
# Or port-forward: kubectl port-forward svc/api-gateway 8000:8000 -n incident-copilot
```

### Staging-Specific Configuration

- Values: `deploy/envs/staging.yaml`
- Ingress host: `incident-copilot-staging.example.com` (update for your domain)
- TLS: enabled (ensure certificate/secret exists)


## Production (LKE)

### Prerequisites

- Linode account with $1,000 hackathon credit
- API token with LKE permissions
- Container registry (GHCR, Docker Hub, or Linode Registry)
- Domain (optional, for Ingress)

### Procedure

**Step 1: Provision LKE cluster**

```bash
export LINODE_TOKEN="your-linode-api-token"
./deploy/provision-lke.sh prod

# Save kubeconfig
export KUBECONFIG=$(pwd)/kubeconfig-prod.yaml
kubectl get nodes
```

**Step 2: Build and push images**

```bash
# Login to registry (example: GitHub Container Registry)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and push
export REGISTRY=ghcr.io/your-org
./deploy/build-and-push.sh prod
```

**Step 3: Update Helm values for registry**

Edit `deploy/envs/prod.yaml` or pass override:

```bash
helm upgrade --install incident-copilot ./helm \
  -n incident-copilot --create-namespace \
  -f ./helm/values.yaml \
  -f ./deploy/envs/prod.yaml \
  --set imageRegistry=ghcr.io/your-org/ \
  --set imageTag=prod \
  --wait --timeout 5m
```

Or use deploy script with env:

```bash
export IMAGE_TAG=prod
export REGISTRY=ghcr.io/your-org
./deploy/deploy.sh prod
```

**Step 4: Configure Ingress (optional)**

1. Install NGINX Ingress Controller if not present:
   ```bash
   helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
   helm install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace
   ```

2. Update `deploy/envs/prod.yaml` with your domain and TLS secret
3. Redeploy: `./deploy/deploy.sh prod`

**Step 5: Verify**

```bash
kubectl get pods -n incident-copilot
kubectl get svc api-gateway -n incident-copilot
# Test external IP or Ingress URL
```

## See Also

- [DEPLOYMENT.md](DEPLOYMENT.md) – Deployment overview, rollback, and verification checklist
- [SETUP.md](SETUP.md) – Environment setup and prerequisites
