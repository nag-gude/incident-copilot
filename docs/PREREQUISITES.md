# Incident Copilot - Prerequisites

Tools and versions required to run Incident Copilot across all environments.


## Table of Contents

1. [Required for All Environments](#required-for-all-environments)
2. [Required for Kubernetes Deployments](#required-for-kubernetes-deployments)
3. [Required for LKE (Linode) Provisioning](#required-for-lke-linode-provisioning)
4. [Install Commands](#install-commands)
5. [Troubleshooting](#troubleshooting)
6. [See Also](#see-also)


## Required for All Environments

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Services, CLI, scripts |
| Docker | 20.10+ | Container builds |
| Docker Compose | 2.0+ | Local orchestration |


## Required for Kubernetes Deployments

| Tool | Version | Purpose |
|------|---------|---------|
| kubectl | 1.28+ | Kubernetes CLI |
| Helm | 3.12+ | Chart deployment |

### Optional: Minikube or kind

- **Minikube** – Local Kubernetes (macOS, Linux, Windows)
- **kind** – Kubernetes in Docker


## Required for LKE (Linode) Provisioning

| Tool | Version | Purpose |
|------|---------|---------|
| Terraform | 1.5+ | Infrastructure as Code |
| Linode account | - | Akamai Cloud (Linode) |

### Linode Account Setup

1. **Sign up:** [https://www.linode.com/](https://www.linode.com/)
2. **Claim hackathon credit:** [https://login.linode.com/signup?promo=akm-eve-dev-hack-1000-12126-M866](https://login.linode.com/signup?promo=akm-eve-dev-hack-1000-12126-M866)
3. **API Token:** [https://cloud.linode.com/profile/tokens](https://cloud.linode.com/profile/tokens)  
   - Scopes: Read/Write for Linode, LKE


## Install Commands

### macOS (Homebrew)

```bash
brew install python@3.11 docker docker-compose kubectl helm terraform
```

**Minikube:**
```bash
brew install minikube
```

**kind:**
```bash
brew install kind
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv docker.io docker-compose-plugin
# kubectl, helm, terraform: follow official install docs
```

### Verify Installation

```bash
python3.11 --version
docker --version
docker-compose --version
kubectl version --client
helm version
terraform version
```


## Troubleshooting

### Local: "Connection refused" on API calls

- Ensure all services are running: `docker-compose ps` or check each uvicorn process
- API Gateway depends on all 5 backend services; start ingestion first, then others

### Local: SQLite "database is locked"

- Only one process should write to the SQLite file. Use a single ingestion instance or switch to PostgreSQL for multi-process

### Docker: "client version 1.41 is too old. Minimum supported API version is 1.44"

- **Cause:** Minikube's Docker daemon expects API 1.44; host Docker client is older
- **Fix:** Use `./deploy/deploy-minikube.sh dev` (builds with host Docker, loads into Minikube), or upgrade Docker Desktop to latest

### Kubernetes: ImagePullBackOff

- Images built locally: ensure `imagePullPolicy: IfNotPresent` in values
- For registry: set `REGISTRY` and push before deploy
- For Minikube: use `./deploy/deploy-minikube.sh dev` instead of `eval $(minikube docker-env)` + build

### Kubernetes: Pending pods

```bash
kubectl describe pod <pod-name> -n incident-copilot
# Check: PVC binding, resource limits, node capacity
```

### Terraform: "Error acquiring lock"

```bash
cd iac/terraform
terraform force-unlock <LOCK_ID>  # Use with caution
```

### LKE: Kubeconfig not working

```bash
# Regenerate kubeconfig from Linode dashboard or:
terraform output -raw kubeconfig > kubeconfig-prod.yaml
export KUBECONFIG=$(pwd)/kubeconfig-prod.yaml
```


## See Also

- [SETUP.md](SETUP.md) – Environment setup (Local, Dev, Staging, Production)
- [DEPLOYMENT-LOCAL.md](DEPLOYMENT-LOCAL.md) – Local deployment
- [DEPLOYMENT-MINIKUBE.md](DEPLOYMENT-MINIKUBE.md) – Minikube deployment
- [DEPLOYMENT-LKE.md](DEPLOYMENT-LKE.md) – LKE deployment
