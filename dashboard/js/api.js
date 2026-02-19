/**
 * Dashboard API client
 */
import { getApiBase } from './config.js';

export async function getDashboard() {
  const base = getApiBase();
  const [dashboardRes, healthRes] = await Promise.all([
    fetch(base + '/dashboard'),
    fetch(base + '/health'),
  ]);
  const d = await dashboardRes.json();
  const health = await healthRes.json();
  return { d, status: health.status || {} };
}

export async function getIncidentDetail(id) {
  const base = getApiBase();
  const r = await fetch(base + '/incidents/' + id);
  if (!r.ok) throw new Error('Incident not found');
  return r.json();
}

export async function postRemediate(id, execute = false) {
  const base = getApiBase();
  const url = execute ? base + '/remediate/' + id + '?execute=true' : base + '/remediate/' + id;
  const r = await fetch(url, { method: 'POST' });
  if (!r.ok) throw new Error(r.statusText);
  const data = await r.json();
  return data;
}

export async function getDetect() {
  const base = getApiBase();
  await fetch(base + '/detect');
}

export async function getPredict() {
  const base = getApiBase();
  await fetch(base + '/predict');
}

export async function postExplain(autoRemediate = false) {
  const base = getApiBase();
  const r = await fetch(base + '/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ auto_remediate: autoRemediate }),
  });
  if (!r.ok) throw new Error(r.statusText);
  return r.json();
}
