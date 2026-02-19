/**
 * Dashboard render - builds and updates DOM from data
 */
import { state } from './state.js';
import {
  formatRelative,
  escapeHtml,
  scoreClass,
  severityBadge,
  logLevelClass,
} from './utils.js';

export function render(d, callbacks = {}) {
  const { onIncidentClick, onRemediateClick, onNavigateToSection } = callbacks;
  const preds = d.predictions || [];
  const pred = preds[0];
  const prob = pred ? (pred.failure_probability ?? 0) : 0;
  const spark = preds.map((p) => p.failure_probability ?? 0).reverse();
  const anom = d.anomalies || [];
  const inc = d.incidents || [];
  const logs = d.logs || [];
  const similar = d.similar_incidents || [];
  const openIncidents = inc.filter((i) => i.status === 'open');
  const lastTs = (pred && pred.timestamp) || (inc[0] && inc[0].timestamp) || null;

  let high = anom.filter((a) => (a.severity || '').toLowerCase() === 'high').length;
  let medium = anom.filter((a) => (a.severity || '').toLowerCase() === 'medium').length;
  let low = anom.filter((a) => (a.severity || '').toLowerCase() === 'low').length;
  if (anom.length && high + medium + low === 0) medium = anom.length;
  const totalSev = high + medium + low || 1;
  const pctH = (high / totalSev) * 100;
  const pctM = (medium / totalSev) * 100;
  const doughnutBg = anom.length
    ? 'conic-gradient(var(--danger) 0deg ' +
      pctH * 3.6 +
      'deg, var(--warning) ' +
      pctH * 3.6 +
      'deg ' +
      (pctH + pctM) * 3.6 +
      'deg, var(--success) ' +
      (pctH + pctM) * 3.6 +
      'deg 360deg)'
    : 'var(--border)';

  const content = document.getElementById('content');
  if (!content) return;

  const summaryEl = document.getElementById('summaryBanner');
  const kpiEl = document.getElementById('kpiRow');
  if (summaryEl) {
    summaryEl.innerHTML =
      '<strong>Overview.</strong> Run anomaly detection and prediction to see failure probability. Create an incident to get root cause analysis, You.com citations, and remediation scripts.';
  }
  if (kpiEl) {
    kpiEl.innerHTML =
      '<div class="kpi-card" data-nav="dashboard"><div class="kpi-value ' +
      scoreClass(prob) +
      '">' +
      Math.round(prob) +
      '%</div><div class="kpi-label">Failure probability</div></div>' +
      '<div class="kpi-card" data-nav="anomalies"><div class="kpi-value">' +
      anom.length +
      '</div><div class="kpi-label">Anomalies</div></div>' +
      '<div class="kpi-card" data-nav="incidents"><div class="kpi-value">' +
      openIncidents.length +
      '</div><div class="kpi-label">Open incidents</div></div>' +
      '<div class="kpi-card"><div class="kpi-value" style="font-size:1.1rem">' +
      formatRelative(lastTs) +
      '</div><div class="kpi-label">Last update</div></div>';
  }

  const activityItems = [];
  inc.slice(0, 5).forEach((i) => {
    activityItems.push({
      type: 'incident',
      text: (i.service || 'Incident') + ': ' + (i.root_cause || '').slice(0, 40),
      time: i.timestamp,
    });
  });
  logs.slice(0, 5).forEach((l) => {
    activityItems.push({
      type: 'log',
      text: (l.level || 'info') + ': ' + (l.message || '').slice(0, 45),
      time: l.timestamp,
    });
  });
  activityItems.sort((a, b) => new Date(b.time || 0) - new Date(a.time || 0));
  const activityList = activityItems.slice(0, 8);

  let dashboardHtml =
    '<div id="section-dashboard" class="section active">' +
    '<div class="grid">' +
    '<div class="card col-4"><div class="card-header"><span class="card-title">Failure probability</span></div>' +
    '<div class="gauge-wrap"><div class="gauge" style="--prob:' +
    prob +
    '"><span class="gauge-value ' +
    scoreClass(prob) +
    '">' +
    Math.round(prob) +
    '%</span></div>' +
    '<span class="gauge-label">Latest prediction</span>' +
    (spark.length > 1
      ? '<div class="trend-chart">' +
        spark
          .map((v) => {
            const max = Math.max(...spark);
            return (
              '<span class="bar" style="height:' +
              (max ? (v / max) * 70 : 4) +
              'px" title="' +
              Math.round(v) +
              '%"></span>'
            );
          })
          .join('') +
        '</div>'
      : '') +
    '</div></div>' +
    '<div class="card col-4"><div class="card-header"><span class="card-title">Anomalies by severity</span></div>' +
    '<div class="severity-doughnut" style="background:' +
    doughnutBg +
    '">' +
    '<div class="center">' +
    anom.length +
    '</div></div>' +
    '<div style="display:flex;justify-content:center;gap:1rem;margin-top:0.5rem;font-size:0.75rem">' +
    '<span style="color:var(--danger)">High ' +
    high +
    '</span><span style="color:var(--warning)">Med ' +
    medium +
    '</span><span style="color:var(--success)">Low ' +
    low +
    '</span></div></div>' +
    '<div class="card col-4"><div class="card-header"><span class="card-title">Recent activity</span></div>' +
    (activityList.length
      ? '<ul class="activity-list">' +
        activityList
          .map(
            (a) =>
              '<li><span class="icon">' +
              (a.type === 'incident' ? '🔔' : '📜') +
              '</span><div><div>' +
              escapeHtml(a.text) +
              '</div><div class="time">' +
              formatRelative(a.time) +
              '</div></div></li>'
          )
          .join('') +
        '</ul>'
      : '<div class="empty-state">No recent activity</div>') +
    '</div>' +
    '<div class="card col-12"><div class="card-header"><span class="card-title">Critical incidents</span></div>' +
    (openIncidents.length
      ? '<div class="critical-list">' +
        openIncidents
          .slice(0, 5)
          .map(
            (i) =>
              '<div class="item"><div class="item-title">' +
              escapeHtml(i.service || 'Incident') +
              '</div><div class="item-meta">' +
              escapeHtml((i.root_cause || '').slice(0, 80)) +
              '</div></div>'
          )
          .join('') +
        '</div>'
      : '<div class="empty-state">No open incidents</div>') +
    '</div></div></div>';

  const ex = state.expandedIncident;
  let anomaliesHtml =
    '<div id="section-anomalies" class="section"><div class="section-title">Anomalies</div><div class="card"><div class="card-header"><span class="card-title">Detected anomalies</span><span class="badge badge-info">' +
    anom.length +
    '</span></div>' +
    (anom.length
      ? '<table><tr><th>Metric</th><th>Value</th><th>Severity</th></tr>' +
        anom
          .slice(0, 20)
          .map(
            (a) =>
              '<tr><td>' +
              escapeHtml(a.metric_or_log || '') +
              '</td><td>' +
              escapeHtml(String(a.actual_value ?? '')) +
              '</td><td>' +
              severityBadge(a.severity) +
              '</td></tr>'
          )
          .join('') +
        '</table>'
      : '<div class="empty-state">No anomalies. Run Detect anomalies.</div>') +
    '</div></div>';

  let incidentsHtml =
    '<div id="section-incidents" class="section"><div class="section-title">Incidents</div><div class="card"><div class="card-header"><span class="card-title">Incidents</span></div>' +
    (inc.length
      ? '<table><tr><th>Service</th><th>Root cause</th><th>Status</th><th></th></tr>' +
        inc
          .map((i) => {
            const expanded = ex === i.id;
            let row =
              '<tr class="incident-row' +
              (expanded ? ' incident-expanded' : '') +
              '" data-id="' +
              i.id +
              '"><td>' +
              escapeHtml(i.service || 'general') +
              '</td><td>' +
              escapeHtml((i.root_cause || '').slice(0, 60)) +
              (i.root_cause && i.root_cause.length > 60 ? '…' : '') +
              '</td><td>' +
              severityBadge(i.status === 'open' ? 'high' : 'low') +
              '</td><td><button class="btn btn-ghost btn-remediate" style="padding:0.2rem 0.5rem;font-size:0.75rem" data-remediate-id="' +
              i.id +
              '">Remediate</button> <button class="btn btn-ghost btn-execute" style="padding:0.2rem 0.5rem;font-size:0.75rem;color:var(--accent)" data-execute-id="' +
              i.id +
              '">Execute</button></td></tr>';
            if (expanded) {
              row +=
                '<tr class="incident-expanded" data-id="' +
                i.id +
                '"><td colspan="4"><div class="incident-detail" id="detail-' +
                i.id +
                '"><span class="loading">Loading...</span></div></td></tr>';
            }
            return row;
          })
          .join('') +
        '</table>'
      : '<div class="empty-state">No incidents. Click Create incident to analyze.</div>') +
    '</div></div>';

  const logsHtml =
    '<div id="section-logs" class="section"><div class="section-title">Recent logs</div><div class="card"><div class="card-header"><span class="card-title">Logs</span></div>' +
    (logs.length
      ? '<table><tr><th>Level</th><th>Message</th></tr>' +
        logs
          .slice(0, 25)
          .map(
            (l) =>
              '<tr><td><span class="' +
              logLevelClass(l.level) +
              '">' +
              escapeHtml(l.level || 'info') +
              '</span></td><td>' +
              escapeHtml((l.message || '').slice(0, 80)) +
              ((l.message || '').length > 80 ? '…' : '') +
              '</td></tr>'
          )
          .join('') +
        '</table>'
      : '<div class="empty-state">No logs</div>') +
    '</div></div>';

  const similarHtml =
    '<div id="section-similar" class="section"><div class="section-title">Similar incidents</div><div class="card"><div class="card-header"><span class="card-title">Similar past incidents</span></div>' +
    (similar.length
      ? '<table><tr><th>Service</th><th>Root cause</th></tr>' +
        similar
          .slice(0, 15)
          .map(
            (s) =>
              '<tr><td>' +
              escapeHtml(s.service || 'general') +
              '</td><td>' +
              escapeHtml((s.root_cause || '').slice(0, 60)) +
              '</td></tr>'
          )
          .join('') +
        '</table>'
      : '<div class="empty-state">No similar incidents yet. Create an incident (Explain) or refresh — recent incidents will appear here. Resolve incidents with feedback to improve future recommendations.</div>') +
    '</div></div>';

  content.innerHTML = dashboardHtml + anomaliesHtml + incidentsHtml + logsHtml + similarHtml;

  content.querySelectorAll('.incident-row').forEach((row) => {
    row.addEventListener('click', () => {
      const id = row.dataset.id;
      if (typeof onIncidentClick === 'function') onIncidentClick(id);
    });
  });
  content.querySelectorAll('[data-remediate-id]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-remediate-id');
      if (typeof onRemediateClick === 'function') onRemediateClick(id, false);
    });
  });
  content.querySelectorAll('[data-execute-id]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.getAttribute('data-execute-id');
      if (typeof onRemediateClick === 'function') onRemediateClick(id, true);
    });
  });

  // KPI cards: click to navigate to section (e.g. Open incidents -> Incidents)
  const kpiRow = document.getElementById('kpiRow');
  if (kpiRow && typeof onNavigateToSection === 'function') {
    kpiRow.querySelectorAll('.kpi-card[data-nav]').forEach((card) => {
      card.style.cursor = 'pointer';
      card.addEventListener('click', () => onNavigateToSection(card.getAttribute('data-nav')));
    });
  }
}

export function restoreActiveSection() {
  const section = state.currentSection;
  document.querySelectorAll('.sidebar .nav-link').forEach((l) => {
    l.classList.toggle('active', l.getAttribute('data-section') === section);
  });
  document.querySelectorAll('.section').forEach((s) => {
    s.classList.toggle('active', s.id === 'section-' + section);
  });
}

export function fillIncidentDetail(id, data) {
  const el = document.getElementById('detail-' + id);
  if (!el) return;
  let h = '<section><h4>Root cause</h4><p>' + escapeHtml(data.root_cause || '-') + '</p></section>';
  if (data.evidence && data.evidence.length) {
    h += '<section><h4>Evidence</h4><ul>' + data.evidence.map((e) => '<li>' + escapeHtml(e) + '</li>').join('') + '</ul></section>';
  }
  if (data.recommendations && data.recommendations.length) {
    h += '<section><h4>Recommendations</h4><ul>' + data.recommendations.map((r) => '<li>' + escapeHtml(r) + '</li>').join('') + '</ul></section>';
  }
  if (data.youcom_citations && data.youcom_citations.length) {
    h +=
      '<section><h4>Citations</h4>' +
      data.youcom_citations
        .map(
          (c) =>
            '<div class="citation"><a href="' +
            escapeHtml(c.url || '#') +
            '" target="_blank" rel="noopener">' +
            escapeHtml(c.title || 'Link') +
            '</a><p style="margin:0.3rem 0 0 0;font-size:0.8rem;color:var(--text-muted)">' +
            escapeHtml((c.snippet || '').slice(0, 120)) +
            '…</p></div>'
        )
        .join('') +
      '</section>';
  }
  el.innerHTML = h;
}
