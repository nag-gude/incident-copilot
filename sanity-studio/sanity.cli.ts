/**
 * Sanity CLI configuration.
 * projectId and dataset can be overridden by env: SANITY_PROJECT_ID, SANITY_DATASET
 */
export default {
  api: {
    projectId: process.env.SANITY_PROJECT_ID || '',
    dataset: process.env.SANITY_DATASET || 'production',
  },
  /** Avoid hostname prompt on deploy (matches https://incidentcopilot.sanity.studio) */
  studioHost: 'incidentcopilot',
}
