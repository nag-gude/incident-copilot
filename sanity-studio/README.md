# Incident Copilot – Sanity Studio

Minimal Sanity Studio for **Similar past incidents**. Deploy from the repo root with the Sanity CLI.

## Quick start (from repo root)

```bash
# Prerequisites: Node 18+, sanity login
export SANITY_PROJECT_ID=your-project-id   # or set in ../.env
make sanity-deploy
# or: ../scripts/sanity-deploy.sh
```

Studio URL after deploy: `https://<SANITY_PROJECT_ID>.sanity.studio`

## Local dev

The deploy script creates `projectId.generated.ts` from `.env` so the built Studio uses your real project ID. For local dev you need that file:

- Run `make sanity-deploy` from repo root once (creates it), or
- Copy `projectId.generated.ts.example` to `projectId.generated.ts` and set your `projectId` and `dataset`.

Then:

```bash
npm install
npm run dev
```

## Schema

- **incident** – `service`, `rootCause`, `incidentId` (optional). Used by the Knowledge service GROQ for similar-incidents.

See [../docs/INTEGRATIONS.md](../docs/INTEGRATIONS.md) for configuration and [../docs/DEPLOYMENT-LOCAL.md](../docs/DEPLOYMENT-LOCAL.md) for local deployment with Sanity.
