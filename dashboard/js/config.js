/**
 * Dashboard configuration
 */
export const REFRESH_INTERVAL_MS = 15000;

export function getApiBase() {
  if (typeof window !== 'undefined' && window.INCIDENT_COPILOT_API) {
    return window.INCIDENT_COPILOT_API;
  }
  if (typeof window !== 'undefined' && window.location.origin.includes('localhost')) {
    return 'http://localhost:8000';
  }
  return '';
}
