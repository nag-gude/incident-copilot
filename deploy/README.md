# Incident Copilot - Deployment

Deploy Incident Copilot AI to Linode Kubernetes Engine (LKE) or any Kubernetes cluster.

## Prerequisites

- Docker
- kubectl
- Helm 3
- (For LKE) Terraform, Linode API token

## Quick Deploy (Existing K8s)

```bash
# Build and deploy to current kubectl context
./deploy/deploy.sh dev build

# Or deploy pre-built images (set IMAGE_TAG)
IMAGE_TAG=latest ./deploy/deploy.sh dev
```

## Full LKE Provisioning

```bash
# 1. Set Linode token (from https://cloud.linode.com/profile/tokens)
export LINODE_TOKEN="your-token"

# 2. Provision LKE cluster
./deploy/provision-lke.sh dev

# 3. Configure kubectl
export KUBECONFIG=$(pwd)/kubeconfig-dev.yaml

# 4. Build and deploy
./deploy/build-and-push.sh dev
./deploy/deploy.sh dev
```

## Environments

| Env     | Values File         | Use Case              |
|---------|---------------------|------------------------|
| dev     | deploy/envs/dev.yaml | Local/dev cluster      |
| staging | deploy/envs/staging.yaml | Pre-production        |
| prod    | deploy/envs/prod.yaml | Production (LKE)      |

## Push to Container Registry

```bash
# GitHub Container Registry
export REGISTRY=ghcr.io/your-org
./deploy/build-and-push.sh prod

# Then deploy with registry prefix in Helm values
```

## Infrastructure as Code (Terraform)

Located in `iac/terraform/`:

- `main.tf` - LKE cluster definition
- `variables.tf` - environment, region, token
- `outputs.tf` - kubeconfig, cluster ID

```bash
cd iac/terraform
terraform init
terraform plan -var="environment=dev" -var="linode_token=$LINODE_TOKEN"
terraform apply
```

## Verify Deployment

```bash
kubectl get pods -n incident-copilot
kubectl get svc api-gateway -n incident-copilot
kubectl port-forward svc/api-gateway 8000:8000 -n incident-copilot
# Open http://localhost:8000/dashboard-page
```
