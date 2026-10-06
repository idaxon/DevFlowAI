/**
 * DevFlow AI - Dashboard Client Logic (Clean Light SaaS Theme)
 */

document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const promptParam = urlParams.get('prompt');
  if (promptParam) {
    document.getElementById('taskInput').value = decodeURIComponent(promptParam);
  }

  refreshDashboard();
  setInterval(refreshDashboard, 3000);
});

function seedSampleTask() {
  const samplePrompt = "My Flask API is returning HTTP 500 errors on /users. Find the root cause, suggest a fix, run the tests, and validate the application in Docker.";
  document.getElementById('taskInput').value = samplePrompt;
}

function switchPromptTab(tab) {
  document.querySelectorAll('.task-nav-btn').forEach(btn => btn.classList.remove('active'));
  if (tab === 'describe') {
    document.getElementById('tabDescribeBtn').classList.add('active');
  }
}

async function triggerWorkflowAction() {
  const taskInput = document.getElementById('taskInput').value.trim();
  const repoId = document.getElementById('repoSelect').value;

  if (!taskInput) {
    alert("Please describe your problem or task first.");
    return;
  }

  const btn = document.getElementById('btnRunWorkflow');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Running Workflow...';

  try {
    const response = await fetch('/api/workflows/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        request: taskInput,
        repository_id: parseInt(repoId) || 1
      })
    });

    const data = await response.json();
    if (data.status === 'success' && data.workflow) {
      window.location.href = `/workflows/${data.workflow.id}`;
    } else {
      alert("Error starting workflow: " + (data.error || "Unknown error"));
    }
  } catch (err) {
    alert("Network error: " + err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-play" style="font-size: 0.75rem;"></i> <span>Run AI Workflow</span>';
  }
}

async function runCheckupAction() {
  const repoId = document.getElementById('repoSelect').value || 1;
  const repoName = document.getElementById('repoSelect').selectedOptions[0]?.text || "selected repository";
  
  const checkupPrompt = `Perform comprehensive autonomous health checkup, security vulnerability scan, and code stability audit on ${repoName}.`;
  document.getElementById('taskInput').value = checkupPrompt;

  const btn = document.getElementById('btnCheckup');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Scanning...';

  try {
    const response = await fetch('/api/workflows/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        request: checkupPrompt,
        repository_id: parseInt(repoId) || 1
      })
    });

    const data = await response.json();
    if (data.status === 'success' && data.workflow) {
      window.location.href = `/workflows/${data.workflow.id}`;
    } else {
      alert("Error starting health check: " + (data.error || "Unknown error"));
    }
  } catch (err) {
    alert("Network error: " + err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-stethoscope text-success me-1"></i> <span>Check up</span>';
  }
}

async function analyzeRepositoryAction() {
  const repoId = document.getElementById('repoSelect').value || 1;
  const btn = event?.currentTarget;
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Indexing...';
  }

  try {
    const res = await fetch(`/api/repositories/${repoId}/index`, { method: 'POST' });
    const data = await res.json();
    alert(`RAG vector index ready: ${data.total_files || 0} files (${data.total_chunks || 0} chunks).`);
    refreshDashboard();
  } catch (err) {
    alert("Indexing error: " + err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-sliders text-muted me-1"></i> <span>Advanced</span>';
    }
  }
}

async function refreshDashboard() {
  try {
    const response = await fetch('/api/dashboard');
    if (!response.ok) return;
    const data = await response.json();

    // Metrics
    if (data.metrics) {
      document.getElementById('metricRepos').innerText = data.metrics.repositories;
      document.getElementById('metricActiveWf').innerText = data.metrics.active_workflows;
      document.getElementById('metricSuccessRate').innerText = data.metrics.success_rate;
      document.getElementById('metricAvgTime').innerText = data.metrics.avg_execution;
    }

    // Workflows Table
    const tbody = document.getElementById('workflowTableBody');
    if (data.recent_workflows && data.recent_workflows.length > 0) {
      tbody.innerHTML = data.recent_workflows.map(wf => {
        let statusBadge = `<span class="badge-pill gray">${wf.status}</span>`;
        if (wf.status === 'RUNNING') statusBadge = `<span class="badge-pill gray"><span class="pulse-dot" style="width:5px; height:5px;"></span> RUNNING</span>`;
        if (wf.status === 'SUCCESS' || wf.status === 'APPROVED') statusBadge = `<span class="badge-pill green">SUCCESS</span>`;
        if (wf.status === 'AWAITING_APPROVAL') statusBadge = `<span class="badge-pill amber">APPROVAL REQ</span>`;
        if (wf.status === 'FAILED') statusBadge = `<span class="badge-pill red">FAILED</span>`;

        const startedFormatted = wf.started_at ? wf.started_at.split('T')[1]?.substring(0, 8) || 'Just now' : 'Just now';

        return `
          <tr>
            <td><a href="/workflows/${wf.id}" class="text-dark fw-bold text-decoration-none">#${wf.id}</a></td>
            <td>
              <a href="/workflows/${wf.id}" class="text-dark fw-medium text-decoration-none d-block text-truncate" style="max-width: 200px;">
                ${wf.request}
              </a>
            </td>
            <td><span class="small text-secondary"><i class="fa-brands fa-github text-muted me-1"></i>${wf.repository_name || 'repo'}</span></td>
            <td>${statusBadge}</td>
            <td><span class="small text-secondary">${wf.current_step}</span></td>
            <td><span class="small text-secondary fw-semibold">${wf.execution_time}s</span></td>
            <td><span class="small text-muted">${startedFormatted}</span></td>
          </tr>
        `;
      }).join('');
    }

    // Live Logs
    const logContainer = document.getElementById('terminalLogContainer');
    if (data.recent_logs && data.recent_logs.length > 0) {
      logContainer.innerHTML = data.recent_logs.slice(0, 30).map(l => {
        let msgClass = 'log-msg-info';
        if (l.level === 'SUCCESS') msgClass = 'log-msg-success';
        if (l.level === 'ERROR') msgClass = 'log-msg-error';
        if (l.level === 'WARN') msgClass = 'log-msg-warn';
        return `<div class="log-line"><span class="log-time">[${l.timestamp}]</span> <span class="log-source">${l.source}</span> <span class="${msgClass}">${l.message}</span></div>`;
      }).join('');
    }

    // Repository Selector
    if (data.repositories_list && data.repositories_list.length > 0) {
      const sel = document.getElementById('repoSelect');
      const currentVal = sel.value;
      sel.innerHTML = data.repositories_list.map(r => `
        <option value="${r.id}" ${r.id == currentVal ? 'selected' : ''}>${r.name} (${r.branch})</option>
      `).join('');
    }

  } catch (err) {
    console.error("Dashboard refresh error:", err);
  }
}
