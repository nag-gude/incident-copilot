/**
 * Dashboard utility functions
 */
export function formatRelative(iso) {
  if (!iso) return 'Never';
  const d = new Date(iso);
  const sec = Math.floor((Date.now() - d) / 1000);
  if (sec < 60) return 'Just now';
  if (sec < 3600) return Math.floor(sec / 60) + ' min ago';
  if (sec < 86400) return Math.floor(sec / 3600) + ' h ago';
  return Math.floor(sec / 86400) + ' d ago';
}

export function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

export function scoreClass(p) {
  if (p < 30) return 'low';
  if (p < 70) return 'mid';
  return 'high';
}

export function severityBadge(s) {
  const map = { high: 'badge-danger', medium: 'badge-warning', low: 'badge-success' };
  return '<span class="badge ' + (map[s] || 'badge-info') + '">' + (s || 'medium') + '</span>';
}

export function logLevelClass(l) {
  const map = { error: 'log-level-error', warn: 'log-level-warn', warning: 'log-level-warn' };
  return map[l] || 'log-level-info';
}
