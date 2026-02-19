# Incident Copilot - Documentation

Documentation for setup, implementation, and deployment of Incident Copilot.


## Documentation Index

### Prerequisites

| Document | Description |
|----------|-------------|
| [PREREQUISITES.md](PREREQUISITES.md) | Required tools, versions, install commands, troubleshooting |

### Setup

| Document | Description |
|----------|-------------|
| [SETUP.md](SETUP.md) | Environment setup: Local, Dev, Staging, Production, optional integrations |

### Integrations

| Document | Description |
|----------|-------------|
| [INTEGRATIONS.md](INTEGRATIONS.md) | You.com API, Cline CLI, Sanity (Structured Knowledge Base) – detailed integration docs |
| [REALTIME_DATA_INGESTION.md](REALTIME_DATA_INGESTION.md) | Real-time data ingestion for pre-production and production testing |

### Deployment

| Document | Description |
|----------|-------------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment overview, CI/CD, rollback, verification checklist |
| [DEPLOYMENT-LOCAL.md](DEPLOYMENT-LOCAL.md) | Local (Docker Compose) deployment |
| [DEPLOYMENT-MINIKUBE.md](DEPLOYMENT-MINIKUBE.md) | Minikube / kind deployment |
| [DEPLOYMENT-LKE.md](DEPLOYMENT-LKE.md) | Linode LKE (Staging, Production) deployment |

### Implementation

| Document | Description |
|----------|-------------|
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | Architecture, project structure, microservices, data flow, storage, sponsor integrations |

### Submission (Sponsor Prizes)

| Document | Description |
|----------|-------------|
| [submission/README.md](submission/README.md) | Index of per-sponsor submission write-ups |
| [submission/SPONSOR-YOUCOM.md](submission/SPONSOR-YOUCOM.md) | You.com – Build Intelligent Applications with You.com APIs |
| [submission/SPONSOR-AKAMAI.md](submission/SPONSOR-AKAMAI.md) | Akamai – Build the Most Creative Open-Source Solution on Linode |
| [submission/SPONSOR-CLINE.md](submission/SPONSOR-CLINE.md) | CLINE – Cline CLI as Infrastructure |
| [submission/SPONSOR-SANITY.md](submission/SPONSOR-SANITY.md) | AI + Sanity – Build a Feature Only Structured Content Makes Possible |


## Quick Reference

### Prerequisites

See [PREREQUISITES.md](PREREQUISITES.md) for tools, versions, and install commands.

### Setup by Environment

| Environment | Doc Section | Key Commands |
|-------------|-------------|--------------|
| **Local** | [SETUP.md § Local](SETUP.md#local-environment) | `docker-compose up -d` |
| **Dev** | [SETUP.md § Dev](SETUP.md#dev-environment-kubernetes) | `./deploy/deploy-minikube.sh dev` |
| **Staging** | [SETUP.md § Staging](SETUP.md#staging-environment) | `./deploy/provision-lke.sh staging` |
| **Prod** | [SETUP.md § Production](SETUP.md#production-environment-lke) | `./deploy/provision-lke.sh prod` |

### Deployment by Environment

| Environment | Guide | Key Commands |
|-------------|-------|--------------|
| **Local** | [DEPLOYMENT-LOCAL.md](DEPLOYMENT-LOCAL.md) | `docker-compose up -d` |
| **Minikube / kind** | [DEPLOYMENT-MINIKUBE.md](DEPLOYMENT-MINIKUBE.md) | `./deploy/deploy-minikube.sh dev` |
| **Staging** | [DEPLOYMENT-LKE.md](DEPLOYMENT-LKE.md) | `./deploy/deploy.sh staging` |
| **Prod** | [DEPLOYMENT-LKE.md](DEPLOYMENT-LKE.md) | See full procedure |

### Integrations

See [INTEGRATIONS.md](INTEGRATIONS.md) for You.com, Cline CLI, and Sanity setup.

### Implementation

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for:
- Service architecture diagram
- Microservice descriptions and endpoints
- Data flow
- Storage and configuration
