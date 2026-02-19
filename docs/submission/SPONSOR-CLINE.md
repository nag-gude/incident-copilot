# CLINE: Cline CLI as Infrastructure

**Sponsor challenge:** CLINE - Cline CLI as Infrastructure  
**Project:** Incident Copilot – DeveloperWeek 2026


## How Incident Copilot Uses Cline CLI as Infrastructure

We treat **Cline CLI** as a **piece of infrastructure** in the incident-response pipeline: when a user asks for remediation, we don’t call a generic “AI API”—we **invoke the Cline CLI** with structured context (error type, service name) and use its output as the **remediation script**. That script is then shown in the dashboard and CLI and can optionally be **executed** (when enabled) so the system goes from “what’s wrong” to “what we ran.”

Cline is thus **infrastructure**: a subprocess that we orchestrate, with a clear contract (context in → script out) and a fallback (mock script) when the CLI isn’t installed.


## What We Built

- **Integration point:** Recommendation service (`services/recommendation/main.py`).
- **Trigger:** `POST /remediate/<incident_id>` (dashboard “Remediate” / “Execute” or CLI `incident-copilot remediate <id>`).
- **Flow:**  
  1. Load incident from DB (root cause, service).  
  2. Call `invoke_cline_remediate(error_type, service, context)` which runs:  
     `cline generate --context=error:<error_type>,service:<service>` (or equivalent) via `subprocess.run(..., capture_output=True, timeout=30)`.  
  3. If Cline returns success and stdout, that is the script; otherwise we return a **mock script** (e.g. kubectl scale/restart) so the demo always shows a script.  
  4. Optional: when `execute=true` and `AUTO_REMEDIATE_EXECUTE_ENABLED` is set, we **execute** the script in a subprocess and return stdout/stderr/returncode.

- **User-visible outcome:**  
  - **Remediate:** Modal (or CLI) shows the Cline-generated (or mock) script.  
  - **Execute:** Same, plus execution result (returncode, stdout, stderr).  
  - **Auto-remediate on create:** Explain can optionally generate and optionally run remediation right after creating the incident.


## Technical Details

| Item | Detail |
|------|--------|
| **Invocation** | `subprocess.run(["cline", "generate", "--context=error:<type>,service:<service>"], capture_output=True, text=True, timeout=30)` |
| **Input** | Error type (from incident root cause), service name, optional context string |
| **Output** | Script text (stdout); on failure or missing CLI, mock script returned |
| **Execution** | Optional; `run_remediation_script(script)` runs script via bash in a temp file; controlled by `AUTO_REMEDIATE_EXECUTE_ENABLED` |
| **CLI** | `incident-copilot remediate <id>` and `incident-copilot remediate <id> --execute` |


## Installation

**Cline CLI (optional – for real script generation):**

- Install: `npm install -g cline` (or per [Cline docs](https://github.com/Anysphere/cline)); ensure Node 20+.
- Auth: `cline auth`.
- Ensure `cline` is in PATH: `which cline` (or add npm global bin to PATH).

If Cline is not installed, Incident Copilot returns a **mock script** (kubectl scale/restart) so the flow still works.

**Incident Copilot CLI (to run remediate from the shell):**

```bash
cd IncidentCopilot/cli
pip install -e .
# Optional: set API base if gateway is not on localhost:8000
export INCIDENT_COPILOT_API_URL=http://localhost:8000
```

**Enable script execution (optional):**  
Set `AUTO_REMEDIATE_EXECUTE_ENABLED=true` in the recommendation service environment (e.g. in `.env` for Docker) to allow `?execute=true` and “Execute” in the dashboard to run the script.


## Testing examples

**Create an incident, then get remediation script (curl, no CLI):**

```bash
# 1) Create incident
RESP=$(curl -s -X POST http://localhost:8004/explain -H "Content-Type: application/json" -d '{}')
ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
echo "Incident ID: $ID"

# 2) Get remediation script (recommendation service, or use gateway :8000)
curl -s -X POST "http://localhost:8004/remediate/$ID" | python3 -m json.tool
# Expect: "script": "<script text>", optionally "execution": { "stdout", "stderr", "returncode" }
```

**Print only the script:**

```bash
curl -s -X POST "http://localhost:8004/remediate/$ID" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('script',''))"
```

**Using the Incident Copilot CLI:**

```bash
incident-copilot remediate $ID
# With execution (if enabled):
incident-copilot remediate $ID --execute
```

**Via gateway (port 8000):**

```bash
curl -s -X POST "http://localhost:8000/remediate/$ID"
curl -s -X POST "http://localhost:8000/remediate/$ID?execute=true"
```


## How to Verify (Demo / Judging)

1. **With Cline CLI installed:**  
   Create an incident (e.g. via dashboard “Create incident”), then click **Remediate** for that incident (or run `incident-copilot remediate <incident_id>`). You should see a script that was produced by Cline (or the mock, if Cline isn’t in PATH or fails).

2. **Execute (optional):**  
   Click **Execute** in the dashboard (or use `--execute` in the CLI). If execution is enabled, the response (or modal) should include returncode and stdout/stderr from running the script.

3. **Architecture:**  
   Show that the recommendation service code invokes Cline as a subprocess (see `invoke_cline_remediate` in `services/recommendation/main.py`) and that the rest of the pipeline (incident → context → script → optional execution) is built around that.

This demonstrates **Cline CLI as Infrastructure**: a programmatic, orchestrated use of the CLI with a clear contract and fallback.


## Links

- **Repo:** [GitHub](https://github.com/nag-gude/incident-copilot)
- **Code:** `services/recommendation/main.py` – `invoke_cline_remediate()`, `run_remediation_script()`, `POST /remediate/{incident_id}`.  
- **Docs:** [INTEGRATIONS.md – Cline CLI](../INTEGRATIONS.md#cline-cli), [IMPLEMENTATION.md – Auto-Remediation Execution](../IMPLEMENTATION.md#auto-remediation-execution).
