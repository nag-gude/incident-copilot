# Incident Copilot - Local Deployment (Docker Compose)

Step-by-step procedure for deploying Incident Copilot locally with Docker Compose.


## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Procedure](#procedure)
3. [Optional: Sanity integration](#optional-sanity-integration)
4. [Verify](#verify)
5. [Stop](#stop)
6. [Troubleshooting](#troubleshooting)
7. [See Also](#see-also)


## Prerequisites

- Docker and Docker Compose installed
- No cloud account required


## Procedure

```bash
cd IncidentCopilot

# Optional but recommended: set You.com API key so citations work (no "You.com API not configured" message)
# Copy .env.example to .env and add your key, or export before starting:
#   cp .env.example .env
#   # Edit .env and set YOUCOM_API_KEY=your-key
# Or one-time:
#   export YOUCOM_API_KEY=your-youcom-api-key
# Get a key: https://you.com/resources/hackathon

# Build and start all services
docker-compose up -d

# If you see "compose build requires buildx 0.17.0 or later", use:
# COMPOSE_DOCKER_CLI_BUILD=0 docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Seed demo data (optional)
python scripts/seed_demo_data.py
```


## Optional: Sanity integration

To power the **Similar incidents** section from Sanity (structured content) in local deployment:

1. **Create a Sanity project**  
   [https://www.sanity.io/manage](https://www.sanity.io/manage) or [get-started](https://www.sanity.io/get-started) — note your **Project ID** and **Dataset** (e.g. `production`).

2. **Deploy Sanity Studio from CLI (recommended)**  
   The repo includes a Studio in `sanity-studio/` with the `incident` schema. From the repo root:

   ```bash
   npm install -g sanity && sanity login
   echo "SANITY_PROJECT_ID=your-project-id" >> .env
   echo "SANITY_DATASET=production" >> .env
   make sanity-deploy
   # or: ./scripts/sanity-deploy.sh
   ```

   Studio URL: `https://<SANITY_PROJECT_ID>.sanity.studio`. Create **Incident** documents there. See [INTEGRATIONS.md – Deploy Sanity Studio from CLI](INTEGRATIONS.md#deploy-sanity-studio-from-cli-automated).

3. **Set environment variables for Incident Copilot**  
   Ensure `.env` has `SANITY_PROJECT_ID` and `SANITY_DATASET=production` (same as step 2 if you used the CLI).

4. **Restart the stack**  
   So the knowledge service picks up the new env:

   ```bash
   docker-compose down && docker-compose up -d
   ```

5. **Verify**  
   - `curl http://localhost:8005/health` — response should include `"sanity_configured": true`.  
   - Add one or more incident documents in Sanity Studio; the dashboard **Similar** section will merge them with local incident refs.

Without Sanity, the dashboard still works: **Similar** shows recent incidents from the recommendation service (fallback) or “No similar incidents yet” when empty.


## Troubleshooting

**"You.com API not configured" / "Set YOUCOM_API_KEY to enable live research-backed remediation"**

The recommendation service shows this when `YOUCOM_API_KEY` is not set. To enable live citation-backed search:

1. Get a You.com API key from [you.com/resources/hackathon](https://you.com/resources/hackathon) or the You.com Developer Portal.
2. **With Docker Compose:** Create a `.env` file in the project root (copy from `.env.example`) and set:
   ```bash
   YOUCOM_API_KEY=your-actual-api-key
   ```
   Then restart: `docker-compose down && docker-compose up -d`.
3. **Without .env:** Export the variable before starting Compose:
   ```bash
   export YOUCOM_API_KEY=your-actual-api-key
   docker-compose up -d
   ```
   Note: the variable must be in the same shell you use to run `docker-compose`; containers read it at startup.


**Error: "compose build requires buildx 0.17.0 or later"**

Use the legacy Docker builder instead:

```bash
COMPOSE_DOCKER_CLI_BUILD=0 docker-compose up -d
```

Or upgrade Docker Desktop (which bundles Buildx).


## Verify

```bash
curl http://localhost:8000/health
curl http://localhost:8000/dashboard
open http://localhost:8000/dashboard-page
```


## Stop

```bash
docker-compose down
# Optional: remove volumes
docker-compose down -v
```


## See Also

- [DEPLOYMENT.md](DEPLOYMENT.md) – Deployment overview and verification checklist
- [SETUP.md](SETUP.md) – Environment setup and prerequisites
