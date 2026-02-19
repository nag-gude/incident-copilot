# AI + Sanity – Build a Feature Only Structured Content Makes Possible

**Sponsor challenge:** AI + Sanity - Build a Feature Only Structured Content Makes Possible  
**Project:** Incident Copilot – DeveloperWeek 2026


## How Incident Copilot Uses Sanity (Structured Content)

We use **Sanity** as the structured content backend for **“Similar past incidents”** and **“Incidents by service.”** Those features are only possible with **queryable, structured content**: we need to store incidents with a consistent schema (service, root cause, outcome, remediation used) and query them by service or by root-cause pattern. Sanity’s **GROQ** and document model give us exactly that—so we can show “here are past incidents like this one” and “here’s what worked before,” which would be much harder with unstructured logs or a flat table.

The **AI** side is the recommendation engine: when we explain a new incident, we call **similar-incidents** (backed by Sanity or local sync) and surface **“Learning: similar incident resolved with: …”** in the recommendations. So the feature that **only structured content makes possible** is: **queryable incident history and learning from past resolutions.**


## What We Built

- **Integration point:** Knowledge service (`services/knowledge/main.py`).
- **Structured content features:**  
  1. **Similar past incidents** – `GET /similar-incidents` (optional `service`, `error_pattern`). When `SANITY_PROJECT_ID` is set, we run **GROQ** against Sanity (e.g. `*[_type == "incident"] | order(_createdAt desc)` and by service/pattern). Results are merged with local `incident_refs` and returned so the dashboard **Similar** section and the explain flow can use them.  
  2. **Incidents by service** – `GET /incidents-by-service` (structured grouping by service).  
  3. **Learning in explain** – When creating an incident, we call similar-incidents; if any past incident has `outcome == "success"` and `remediation_used`, we add a recommendation line: “Learning: similar incident resolved with: &lt;remediation_used&gt;.”

- **Schema:** We use (and deploy) an **incident** document type in Sanity with `service`, `rootCause`, and optional `incidentId`. The Knowledge service maps Sanity documents to a common shape and merges with local DB. Feedback (outcome, remediation_used) is synced to Sanity/local so future similar-incidents can surface “what worked.”

- **Deployment:** We provide a **Sanity Studio** in `sanity-studio/` with the incident schema and a **CLI deploy** (`make sanity-deploy` / `./scripts/sanity-deploy.sh`) so the structured content backend is deployable and editable via Studio.


## Technical Details

| Item | Detail |
|------|--------|
| **API** | Sanity GROQ: `https://<projectId>.api.sanity.io/v2024-01-01/data/query/<dataset>?query=<GROQ>` |
| **Schema** | `incident`: `service` (string), `rootCause` (text), `incidentId` (optional) |
| **GROQ examples** | By service: `*[_type == "incident" && service == $service]`; by pattern: `rootCause match $pattern` |
| **Config** | `SANITY_PROJECT_ID`, `SANITY_DATASET` (default `production`); optional `SANITY_TOKEN` |
| **Fallback** | When Sanity isn’t configured, similar-incidents uses local `incident_refs` and gateway fallback (recent incidents from recommendation service) so the product still works |


## Installation

1. **Create a Sanity project**  
   Go to [sanity.io/manage](https://www.sanity.io/manage) or [sanity.io/get-started](https://www.sanity.io/get-started) and create a project. Note the **Project ID** and **Dataset** (e.g. `production`).

2. **Set environment variables**  
   From the repo root:
   ```bash
   cp .env.example .env
   # Add to .env:
   #   SANITY_PROJECT_ID=your-project-id
   #   SANITY_DATASET=production
   ```

3. **Deploy Sanity Studio (optional but recommended)**  
   Deploys the repo’s Studio (incident schema) to Sanity hosting:
   ```bash
   npm install -g sanity && sanity login
   make sanity-deploy
   # or: ./scripts/sanity-deploy.sh
   ```
   Studio URL: `https://<SANITY_PROJECT_ID>.sanity.studio` (or the hostname you chose, e.g. `incidentcopilot.sanity.studio`).

4. **Wire Incident Copilot to Sanity**  
   Ensure the **knowledge** service sees the same env (e.g. in Docker Compose, `SANITY_PROJECT_ID` and `SANITY_DATASET` are in `.env`). Restart the stack:
   ```bash
   docker-compose down && docker-compose up -d
   ```

5. **Create content in Studio**  
   In the deployed Studio, add one or more **Incident** documents (service, root cause). They will appear in the dashboard **Similar** section and in similar-incidents API responses.


## Testing examples

**Check that Sanity is configured (knowledge service):**

```bash
curl -s http://localhost:8005/health | python3 -m json.tool
# Expect: "sanity_configured": true when SANITY_PROJECT_ID is set
```

**Fetch similar incidents (Knowledge API):**

```bash
curl -s "http://localhost:8005/similar-incidents" | python3 -m json.tool
# With service filter:
curl -s "http://localhost:8005/similar-incidents?service=api-gateway" | python3 -m json.tool
```

**Incidents by service:**

```bash
curl -s http://localhost:8005/incidents-by-service | python3 -m json.tool
```

**Dashboard aggregate (includes similar_incidents from gateway):**

```bash
curl -s http://localhost:8000/dashboard | python3 -c "import sys,json; d=json.load(sys.stdin); print('similar_incidents:', len(d.get('similar_incidents',[])))"
```

**GROQ from command line (optional, replace PROJECT_ID and DATASET):**

```bash
curl -s "https://PROJECT_ID.api.sanity.io/v2024-01-01/data/query/DATASET?query=*%5B_type%20%3D%3D%20%22incident%22%5D%5B0...5%5D" | python3 -m json.tool
```


## How to Verify (Demo / Judging)

1. **Configure Sanity:** Set `SANITY_PROJECT_ID` (and optionally `SANITY_DATASET`) in `.env`. Deploy the repo’s Studio: `make sanity-deploy`. Create a few **Incident** documents in the Studio (service, root cause).

2. **Similar incidents:** Open the Incident Copilot dashboard → **Similar** section. You should see those Sanity incidents (and any local ones). Create a new incident (Explain); in the recommendation list you may see “Learning: similar incident resolved with: …” when a similar past incident has resolution info.

3. **Structured content:** Show that the feature depends on **queryable structure** (service, root cause, outcome)—e.g. by inspecting the GROQ queries in the Knowledge service and the incident schema in `sanity-studio/schemaTypes/incident.ts`.

This demonstrates a **feature only structured content makes possible**: queryable incident history and AI recommendations that learn from past resolutions, powered by Sanity.


## Links

- **Repo:** [GitHub](https://github.com/nag-gude/incident-copilot)
- **Code:** `services/knowledge/main.py` – `sanity_query()`, `similar_incidents()`, `incidents_by_service()`, feedback sync.  
- **Studio:** `sanity-studio/` – incident schema, deploy via `scripts/sanity-deploy.sh`.  
- **Docs:** [INTEGRATIONS.md – Sanity](../INTEGRATIONS.md#sanity-structured-knowledge-base), [DEPLOYMENT-LOCAL.md – Sanity integration](../DEPLOYMENT-LOCAL.md#optional-sanity-integration).
