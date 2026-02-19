# You.com – Build Intelligent Applications with You.com APIs

**Sponsor challenge:** You.com - Build Intelligent Applications with You.com APIs  
**Project:** Incident Copilot – DeveloperWeek 2026


## How Incident Copilot Uses You.com

Incident Copilot uses the **You.com API** to power **intelligent, citation-backed remediation**. When we create an incident from anomalies, we don’t just show a generic “scale up” message—we call You.com’s search API with a query derived from the root cause (e.g. “Kubernetes OOM remediation runbook”) and surface **live web results** (runbooks, docs, Stack Overflow) with **titles and URLs** so every recommendation is grounded in real documentation.

This turns the product into an **intelligent application**: the AI assistant uses live data from You.com to deliver reliable, citation-backed answers instead of unsourced suggestions.


## What We Built

- **Integration point:** Recommendation service (`services/recommendation/main.py`).
- **Trigger:** Every `POST /explain` (incident creation) runs a You.com search based on the detected root cause and metric context.
- **Flow:**  
  1. Anomalies → root cause summary (e.g. “Detected anomalies in: cpu_usage, memory”).  
  2. Search query built from root cause (e.g. “Kubernetes &lt;metric&gt; remediation runbook”).  
  3. **You.com API** called: `GET https://ydc-index.io/v1/search` with `query` and `count`, header `X-API-Key: YOUCOM_API_KEY`.  
  4. Response parsed: `results.web` → title, url, snippet/description.  
  5. These are returned as **youcom_citations** on the incident and shown in the dashboard under **Citations** with clickable links.

- **User-visible outcome:** In the dashboard, each incident has a **Citations** section with You.com-sourced links (title + URL + snippet). Recommendations are explicitly backed by “live” search results, not static text.


## Technical Details

| Item | Detail |
|------|--------|
| **API** | You.com Search (YDC), base URL `https://ydc-index.io/v1/search` |
| **Auth** | `X-API-Key` header; key from [you.com/resources/hackathon](https://you.com/resources/hackathon) or You.com Developer Portal |
| **Request** | GET, query params: `query` (required), `count` (e.g. 5) |
| **Response** | We use `results.web`; each item: `title`, `url`, `snippets` / `description` |
| **Config** | `YOUCOM_API_KEY` in env (or `.env` for Docker Compose) |

Without an API key, we return a single placeholder citation that tells the user to set `YOUCOM_API_KEY`, so the integration point and UI are always visible.


## Installation

1. **Get a You.com API key**  
   Sign up at [you.com/resources/hackathon](https://you.com/resources/hackathon) or the [You.com Developer Portal](https://you.com/) and copy your API key.

2. **Configure the app**  
   From the repo root:
   ```bash
   cp .env.example .env
   # Edit .env and set:
   #   YOUCOM_API_KEY=your-actual-api-key
   ```

3. **Start the stack**  
   - **Docker Compose:** `docker-compose up -d` (reads `.env` automatically).  
   - **Local services:** Export the key then start the recommendation service (port 8004):
     ```bash
     export YOUCOM_API_KEY=your-actual-api-key
     cd services/recommendation && uvicorn main:app --port 8004
     ```

4. **Restart after adding the key**  
   If the stack was already running: `docker-compose down && docker-compose up -d`.


## Testing examples

**Create an incident and inspect You.com citations (API):**

```bash
# Create incident (triggers You.com search inside recommendation service)
curl -s -X POST http://localhost:8004/explain \
  -H "Content-Type: application/json" -d '{}' | python3 -m json.tool
```

In the JSON response, check:

- `youcom_citations`: array of `{ "title", "url", "snippet" }` from You.com (live runbooks/docs).  
- If the key is missing, you’ll see a single placeholder citation: *"You.com API not configured"*.

**Extract only citations:**

```bash
curl -s -X POST http://localhost:8004/explain -H "Content-Type: application/json" -d '{}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print(c.get('title'), c.get('url')) for c in d.get('youcom_citations',[])]"
```

**Direct You.com API test (optional):**

```bash
curl -s "https://ydc-index.io/v1/search?query=Kubernetes+remediation+runbook&count=3" \
  -H "X-API-Key: $YOUCOM_API_KEY" | python3 -m json.tool
```


## How to Verify (Demo / Judging)

1. Set `YOUCOM_API_KEY` in `.env` (or export it), then start the stack (e.g. `docker-compose up -d`).
2. In the dashboard, click **Create incident** (Explain).
3. Open the new incident and expand it; check the **Citations** section.
4. You should see one or more entries with **title**, **URL**, and **snippet** from You.com (runbooks/docs). Click a URL to confirm it’s a real, live source.

This demonstrates an **intelligent application** built with You.com APIs: live, citation-backed remediation inside an AI observability assistant.


## Links

- **Repo:** [GitHub](https://github.com/nag-gude/incident-copilot)
- **Code:** `services/recommendation/main.py` – `youcom_search()`, used in `explain_incident()`.
- **Docs:** [INTEGRATIONS.md – You.com API](../INTEGRATIONS.md#youcom-api), [DEPLOYMENT-LOCAL.md – YOUCOM_API_KEY](../DEPLOYMENT-LOCAL.md).
