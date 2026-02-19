/**
 * Sanity Studio config for Incident Copilot.
 * projectId/dataset come from projectId.generated.ts (written by scripts/sanity-deploy.sh from .env).
 */
import React from 'react'
import { defineConfig } from 'sanity'
import { structureTool } from 'sanity/structure'
import { schemaTypes } from './schemaTypes'
import { projectId, dataset } from './projectId.generated'

export default defineConfig({
  name: 'incident-copilot',
  title: 'Incident Copilot',
  projectId,
  dataset,
  plugins: [structureTool()],
  schema: {
    types: schemaTypes,
  },
})
