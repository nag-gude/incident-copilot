/**
 * Dashboard UI helpers - toasts, modal, health pills
 */
export function showToast(msg, type = '') {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.className = 'toast ' + type;
  t.style.display = 'block';
  setTimeout(() => {
    t.style.display = 'none';
  }, 4000);
}

export function openModal(content) {
  const body = document.getElementById('modalBody');
  const overlay = document.getElementById('modal');
  if (body) body.textContent = content;
  if (overlay) overlay.style.display = 'flex';
}

export function closeModal() {
  const overlay = document.getElementById('modal');
  if (overlay) overlay.style.display = 'none';
}

export function updateHealthPills(status) {
  const el = document.getElementById('health');
  if (!el) return;
  const names = ['ingestion', 'anomaly', 'prediction', 'recommendation', 'knowledge'];
  el.innerHTML = names
    .map((n) => {
      const s = status[n] || 'down';
      return '<span class="health-pill ' + s + '"><span class="dot"></span>' + n + '</span>';
    })
    .join('');
}

export function setLastRefresh(text) {
  const el = document.getElementById('lastRefresh');
  if (el) el.textContent = text;
}

export function setContentLoading(loading) {
  const el = document.getElementById('content');
  if (!el) return;
  el.innerHTML = loading ? '<span class="loading">Loading...</span>' : '';
}

export function setContentError(message) {
  const el = document.getElementById('content');
  if (el) el.innerHTML = '<p class="error-msg">Failed to load: ' + message + '</p>';
}

export function setRefreshIntervalLabelVisible(visible) {
  const el = document.getElementById('refreshIntervalLabel');
  if (el) el.style.display = visible ? '' : 'none';
}
