/**
 * Dashboard application - wires API, render, UI and auto-refresh
 */
import { getApiBase, REFRESH_INTERVAL_MS } from './config.js';
import { state } from './state.js';
import * as api from './api.js';
import * as render from './render.js';
import * as ui from './ui.js';

let autoRefreshId = null;

async function refresh() {
  ui.setContentLoading(true);
  ui.setLastRefresh('Refreshing...');
  try {
    const { d, status } = await api.getDashboard();
    ui.updateHealthPills(status);
    ui.setLastRefresh('Updated ' + new Date().toLocaleTimeString());
    state.lastData = { dashboard: d, status };

    render.render(d, {
      onNavigateToSection(section) {
        state.currentSection = section;
        document.querySelectorAll('.sidebar .nav-link').forEach((l) => l.classList.remove('active'));
        const link = document.querySelector('.sidebar .nav-link[data-section="' + section + '"]');
        if (link) link.classList.add('active');
        document.querySelectorAll('.section').forEach((s) => s.classList.remove('active'));
        const el = document.getElementById('section-' + section);
        if (el) el.classList.add('active');
      },
      onIncidentClick(id) {
        state.expandedIncident = state.expandedIncident === id ? null : id;
        refresh();
      },
      onRemediateClick(id, execute = false) {
        ui.showToast(execute ? 'Executing remediation...' : 'Generating remediation script...', '');
        api
          .postRemediate(id, execute)
          .then((data) => {
            let content = data.script || 'No script generated';
            if (data.execution) {
              const ex = data.execution;
              if (ex.error) content += '\n\n--- Execution ---\n' + ex.error;
              else {
                content += '\n\n--- Execution result ---\nreturncode: ' + (ex.returncode ?? '-');
                if (ex.stdout) content += '\n\nstdout:\n' + ex.stdout;
                if (ex.stderr) content += '\n\nstderr:\n' + ex.stderr;
              }
            }
            ui.openModal(content);
            if (execute) ui.showToast('Remediation ' + (data.execution?.returncode === 0 ? 'completed' : 'finished'), data.execution?.returncode === 0 ? 'success' : '');
          })
          .catch((e) => ui.showToast('Remediation failed: ' + e.message, 'error'));
      },
    });

    render.restoreActiveSection();

    if (state.expandedIncident) {
      const el = document.getElementById('detail-' + state.expandedIncident);
      if (el) {
        try {
          const data = await api.getIncidentDetail(state.expandedIncident);
          render.fillIncidentDetail(state.expandedIncident, data);
        } catch {
          el.innerHTML = '<p class="error-msg">Failed to load details</p>';
        }
      }
    }
  } catch (e) {
    ui.setContentError(e.message);
    ui.setLastRefresh('Error');
    state.lastData = null;
  }
}

function startAutoRefresh() {
  stopAutoRefresh();
  autoRefreshId = setInterval(refresh, REFRESH_INTERVAL_MS);
}

function stopAutoRefresh() {
  if (autoRefreshId) {
    clearInterval(autoRefreshId);
    autoRefreshId = null;
  }
}

function setupNav() {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;
  sidebar.addEventListener('click', (e) => {
    const link = e.target.closest('.nav-link');
    if (!link) return;
    e.preventDefault();
    const section = link.getAttribute('data-section');
    state.currentSection = section;
    document.querySelectorAll('.sidebar .nav-link').forEach((l) => l.classList.remove('active'));
    link.classList.add('active');
    document.querySelectorAll('.section').forEach((s) => s.classList.remove('active'));
    const el = document.getElementById('section-' + section);
    if (el) el.classList.add('active');
  });
}

function setupAutoRefreshToggle() {
  const toggle = document.getElementById('autoRefreshToggle');
  if (!toggle) return;
  toggle.addEventListener('change', () => {
    if (toggle.checked) {
      startAutoRefresh();
      ui.setRefreshIntervalLabelVisible(true);
    } else {
      stopAutoRefresh();
      ui.setRefreshIntervalLabelVisible(false);
    }
  });
}

function setupModalClose() {
  const closeBtn = document.querySelector('.modal-close');
  if (closeBtn) closeBtn.addEventListener('click', ui.closeModal);
}

function setupActionButtons() {
  document.querySelector('[data-action="detect"]')?.addEventListener('click', async () => {
    ui.showToast('Running anomaly detection...', '');
    try {
      await api.getDetect();
      ui.showToast('Anomaly detection complete', 'success');
      refresh();
    } catch (e) {
      ui.showToast('Detection failed: ' + e.message, 'error');
    }
  });
  document.querySelector('[data-action="predict"]')?.addEventListener('click', async () => {
    ui.showToast('Running prediction...', '');
    try {
      await api.getPredict();
      ui.showToast('Prediction complete', 'success');
      refresh();
    } catch (e) {
      ui.showToast('Prediction failed: ' + e.message, 'error');
    }
  });
  document.querySelector('[data-action="explain"]')?.addEventListener('click', async () => {
    const autoRemediate = document.getElementById('autoRemediateToggle')?.checked ?? false;
    ui.showToast(autoRemediate ? 'Creating incident & remediating...' : 'Creating incident (Explain)...', '');
    try {
      const data = await api.postExplain(autoRemediate);
      let msg = 'Incident created: ' + (data.id || '').slice(0, 8) + '…';
      if (autoRemediate && data.remediation_script) {
        msg += ' Script generated.';
        if (data.remediation_execution?.returncode === 0) msg += ' Execution succeeded.';
        else if (data.remediation_execution?.returncode !== undefined && data.remediation_execution?.returncode !== -1)
          msg += ' Execution finished (rc=' + data.remediation_execution.returncode + ').';
      }
      ui.showToast(msg, 'success');
      state.expandedIncident = data.id;
      if (autoRemediate && data.remediation_script) {
        let content = data.remediation_script;
        if (data.remediation_execution) {
          const ex = data.remediation_execution;
          if (ex.error) content += '\n\n--- Execution ---\n' + ex.error;
          else if (ex.note) content += '\n\n' + ex.note;
          else {
            content += '\n\n--- Execution result ---\nreturncode: ' + (ex.returncode ?? '-');
            if (ex.stdout) content += '\n\nstdout:\n' + ex.stdout;
            if (ex.stderr) content += '\n\nstderr:\n' + ex.stderr;
          }
        }
        ui.openModal(content);
      }
      refresh();
    } catch (e) {
      ui.showToast('Explain failed: ' + e.message, 'error');
    }
  });
  document.querySelector('[data-action="refresh"]')?.addEventListener('click', () => refresh());
}

function init() {
  setupNav();
  setupAutoRefreshToggle();
  setupModalClose();
  setupActionButtons();
  refresh();
  startAutoRefresh();
}

init();
