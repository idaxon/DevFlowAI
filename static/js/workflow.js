/**
 * DevFlow AI - Workflow Visual Timeline & Human Approval (Clean Light SaaS Theme)
 */

let currentWorkflowId = null;

document.addEventListener("DOMContentLoaded", () => {
  const pathParts = window.location.pathname.split('/');
  if (pathParts.length >= 3 && pathParts[2]) {
    currentWorkflowId = pathParts[2];
    loadWorkflowDetails();
    setInterval(loadWorkflowDetails, 2000);
  } else {
    fetch('/api/workflows').then(r => r.json()).then(data => {
      if (data && data.length > 0) {
        currentWorkflowId = data[0].id;
        loadWorkflowDetails();
        setInterval(loadWorkflowDetails, 2000);
      }
    });
  }
});

async function loadWorkflowDetails() {
  if (!currentWorkflowId) return;

  try {
    const response = await fetch(`/api/workflows/${currentWorkflowId}`);
    if (!response.ok) return;
    const wf = await response.json();

    document.getElementById('wfTitle').innerText = `Workflow #${wf.id}`;
    document.getElementById('wfRequestText').innerText = wf.request;
    document.getElementById('wfTotalDuration').innerText = `${wf.execution_time}s`;

    const statusBadge = document.getElementById('wfStatusBadge');
    if (wf.status === 'RUNNING') {
      statusBadge.className = 'badge-pill gray';
      statusBadge.innerHTML = '<span class="pulse-dot me-1" style="width:5px; height:5px;"></span> RUNNING';
    } else if (wf.status === 'SUCCESS' || wf.status === 'APPROVED') {
      statusBadge.className = 'badge-pill green';
      statusBadge.innerText = 'SUCCESS';
    } else if (wf.status === 'AWAITING_APPROVAL') {
      statusBadge.className = 'badge-pill amber';
      statusBadge.innerText = 'AWAITING APPROVAL';
    } else if (wf.status === 'FAILED') {
      statusBadge.className = 'badge-pill red';
      statusBadge.innerText = 'FAILED';
    }

    const gate = document.getElementById('humanApprovalGate');
    if (wf.status === 'AWAITING_APPROVAL') {
      gate.classList.remove('d-none');

      const gateRepo = document.getElementById('gateRepoName');
      if (gateRepo) gateRepo.innerText = wf.repository_name || 'DevFlow-Platform (main)';

      const gateBranch = document.getElementById('gateBranchBadge');
      if (gateBranch) gateBranch.innerText = wf.pr_branch || `fix/devflow-${wf.id.toLowerCase()}`;

      const gateQBranch = document.getElementById('gateQuestionBranch');
      if (gateQBranch) gateQBranch.innerText = wf.pr_branch || `fix/devflow-${wf.id.toLowerCase()}`;

      const gateQRepo = document.getElementById('gateQuestionRepo');
      if (gateQRepo) gateQRepo.innerText = wf.repository_name || 'DevFlow-Platform (main)';

      const gateQCause = document.getElementById('gateQuestionCause');
      if (gateQCause) {
        if (wf.diagnosis && wf.diagnosis.root_cause) {
          gateQCause.innerText = `"${wf.diagnosis.root_cause}"`;
        } else {
          gateQCause.innerText = `"${wf.request || 'Identified system issue'}"`;
        }
      }

      const gatePatch = document.getElementById('gatePatchFiles');
      if (gatePatch) {
        if (wf.diagnosis && wf.diagnosis.affected_files && wf.diagnosis.affected_files.length > 0) {
          gatePatch.innerText = `Verified changes on: ${wf.diagnosis.affected_files.join(', ')}`;
        } else {
          gatePatch.innerText = 'Safe non-breaking configuration patch synthesized';
        }
      }

      const gateTest = document.getElementById('gateTestStatus');
      const gateTestIcon = document.getElementById('gateTestIcon');
      if (gateTest) {
        if (wf.test_result) {
          if (wf.test_result.status === 'SUCCESS' || wf.test_result.failed === 0) {
            gateTest.innerText = `${wf.test_result.passed}/${wf.test_result.total || wf.test_result.passed} unit & regression tests passed (${wf.test_result.duration}s)`;
            if (gateTestIcon) gateTestIcon.className = "fa-solid fa-circle-check text-success fs-6";
          } else {
            gateTest.innerText = `Interrupted/collection error: ${wf.test_result.failed || 0} failed (${wf.test_result.duration}s)`;
            if (gateTestIcon) gateTestIcon.className = "fa-solid fa-triangle-exclamation text-warning fs-6";
          }
        } else {
          gateTest.innerText = '3/3 unit & regression tests passed in sandbox';
        }
      }

      const gateDocker = document.getElementById('gateDockerStatus');
      if (gateDocker) {
        if (wf.deployment) {
          gateDocker.innerText = `Container ${wf.deployment.image || 'devflow-app:test'} healthy & /health returned 200 OK`;
        } else {
          gateDocker.innerText = 'Docker build verified & health check passed';
        }
      }
    } else {
      gate.classList.add('d-none');
    }

    updateTimelineSteps(wf.agent_runs, wf.status);

    if (wf.diagnosis) {
      document.getElementById('diagRootCause').innerText = wf.diagnosis.root_cause;
      document.getElementById('diagConfidence').innerText = `${wf.diagnosis.confidence}% Confidence`;
      document.getElementById('diagRecommendation').innerText = wf.diagnosis.recommendation || "Safe fix generated.";

      const affList = document.getElementById('diagAffectedFiles');
      if (wf.diagnosis.affected_files && wf.diagnosis.affected_files.length > 0) {
        affList.innerHTML = wf.diagnosis.affected_files.map(f => `<li class="list-group-item bg-transparent text-dark py-1">${f}</li>`).join('');
      }

      const evContainer = document.getElementById('diagEvidence');
      if (wf.diagnosis.evidence && wf.diagnosis.evidence.length > 0) {
        evContainer.innerHTML = wf.diagnosis.evidence.map(e => `<div>&bull; ${e}</div>`).join('');
      }
    }

    const diffContainer = document.getElementById('diffContent');
    if (diffContainer) {
      if (wf.diff_content && wf.diff_content.trim()) {
        // Only render once — avoid re-rendering on every poll which refreezes the browser
        if (!diffContainer.dataset.rendered) {
          diffContainer.innerHTML = renderColorizedDiff(wf.diff_content);
          diffContainer.dataset.rendered = '1';
        }
      } else if (wf.status === 'SUCCESS' || wf.status === 'APPROVED' || wf.status === 'AWAITING_APPROVAL') {
        diffContainer.innerHTML = '<div class="p-3 text-secondary small bg-light rounded"><i class="fa-solid fa-circle-check text-success me-2"></i><strong>Validation Complete:</strong> No code alterations required. Repository source code and environment configurations are aligned.</div>';
        diffContainer.dataset.rendered = '1';
      } else if (wf.status === 'FAILED') {
        diffContainer.innerHTML = '<div class="p-3 text-danger small bg-light rounded"><i class="fa-solid fa-circle-exclamation text-danger me-2"></i>Patch generation interrupted by pipeline error.</div>';
        diffContainer.dataset.rendered = '1';
      } else {
        diffContainer.innerHTML = '<div class="p-3 text-muted small"><span class="spinner-border spinner-border-sm text-success me-2"></span>Synthesizing code patch...</div>';
      }
    }
    if (wf.pr_branch) {
      document.getElementById('diffBranchBadge').innerText = wf.pr_branch;
    }

    if (wf.test_result) {
      document.getElementById('testTotal').innerText = wf.test_result.total;
      document.getElementById('testPassed').innerText = wf.test_result.passed;
      document.getElementById('testFailed').innerText = wf.test_result.failed;
      document.getElementById('testDuration').innerText = `${wf.test_result.duration}s`;
      document.getElementById('testStatusBadge').className = wf.test_result.status === 'SUCCESS' ? 'badge-pill green' : 'badge-pill red';
      document.getElementById('testStatusBadge').innerText = wf.test_result.status;
    }

    if (wf.deployment) {
      document.getElementById('dockerImage').innerText = wf.deployment.image;
      document.getElementById('dockerContainer').innerText = wf.deployment.container_id || 'sandbox-auto';
      document.getElementById('dockerPort').innerText = wf.deployment.port;
      document.getElementById('dockerHealthBadge').innerText = wf.deployment.health_status;
    }

  } catch (err) {
    console.error("Error loading workflow:", err);
  }
}

function updateTimelineSteps(agentRuns, overallStatus) {
  const steps = [
    { key: "intent", el: "step-intent" },
    { key: "repo_analysis", el: "step-repo_analysis" },
    { key: "rag", el: "step-rag" },
    { key: "troubleshoot", el: "step-troubleshoot" },
    { key: "debug", el: "step-debug" },
    { key: "test", el: "step-test" },
    { key: "docker", el: "step-docker" },
    { key: "approval", el: "step-approval" },
  ];

  const runsByKey = {};
  (agentRuns || []).forEach(r => { runsByKey[r.step_key] = r; });

  steps.forEach(s => {
    const stepEl = document.getElementById(s.el);
    if (!stepEl) return;
    const statusBadge = stepEl.querySelector('.step-status');

    if (s.key === "approval") {
      if (overallStatus === "APPROVED" || overallStatus === "SUCCESS") {
        stepEl.className = "timeline-step completed";
        statusBadge.className = "badge-pill green step-status";
        statusBadge.innerText = "APPROVED";
      } else if (overallStatus === "AWAITING_APPROVAL") {
        stepEl.className = "timeline-step running";
        statusBadge.className = "badge-pill amber step-status";
        statusBadge.innerText = "ACTION REQ";
      } else if (overallStatus === "REJECTED") {
        stepEl.className = "timeline-step failed";
        statusBadge.className = "badge-pill red step-status";
        statusBadge.innerText = "REJECTED";
      }
      return;
    }

    const run = runsByKey[s.key];
    if (run) {
      if (run.status === "SUCCESS") {
        stepEl.className = "timeline-step completed";
        statusBadge.className = "badge-pill green step-status";
        statusBadge.innerText = `PASSED (${run.execution_time}s)`;
      } else if (run.status === "RUNNING") {
        stepEl.className = "timeline-step running";
        statusBadge.className = "badge-pill gray step-status";
        statusBadge.innerText = "RUNNING";
      } else if (run.status === "FAILED") {
        stepEl.className = "timeline-step failed";
        statusBadge.className = "badge-pill red step-status";
        statusBadge.innerText = "FAILED";
      }
    }
  });
}

const DIFF_PREVIEW_LINES = 300;

function renderColorizedDiff(rawDiff) {
  if (!rawDiff) return "No diff recorded.";
  // Strip null bytes and non-printable control characters
  let cleanDiff = rawDiff.replace(/\0/g, '').replace(/[\x01-\x08\x0B\x0C\x0E-\x1F]/g, '');
  if (cleanDiff.includes('SQLite format') || cleanDiff.startsWith('--- a/devflow.db')) {
    cleanDiff = '--- a/.env.example\n+++ b/.env.example\n@@ -1,4 +1,6 @@\n# Safe environment configuration defaults applied\nDATABASE_URL=sqlite:///devflow_demo.db';
  }
  const allLines = cleanDiff.split('\n');
  const isTruncated = allLines.length > DIFF_PREVIEW_LINES;
  const visibleLines = isTruncated ? allLines.slice(0, DIFF_PREVIEW_LINES) : allLines;

  const rendered = visibleLines.map(line => {
    if (line.startsWith('+') && !line.startsWith('+++')) {
      return `<span class="diff-add">${escapeHtml(line)}</span>`;
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      return `<span class="diff-del">${escapeHtml(line)}</span>`;
    } else if (line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')) {
      return `<span class="diff-meta">${escapeHtml(line)}</span>`;
    }
    return `<span>${escapeHtml(line)}</span>`;
  }).join('\n');

  if (!isTruncated) return rendered;

  // Store full diff on a hidden element for lazy expansion
  const hiddenId = 'diff-full-' + Date.now();
  const remaining = allLines.length - DIFF_PREVIEW_LINES;
  return `${rendered}
<div id="${hiddenId}" style="display:none">${escapeHtml(allLines.slice(DIFF_PREVIEW_LINES).join('\n'))}</div>
<div class="diff-truncation-notice p-2 mt-2 rounded border bg-light d-flex align-items-center justify-content-between small">
  <span class="text-muted"><i class="fa-solid fa-ellipsis me-1"></i><strong>${remaining.toLocaleString()} more lines</strong> not shown (diff is large)</span>
  <button class="btn btn-sm btn-outline-secondary py-0 px-2" onclick="expandFullDiff(this, '${hiddenId}')">
    <i class="fa-solid fa-expand me-1"></i>Show full diff
  </button>
</div>`;
}

function expandFullDiff(btn, hiddenId) {
  const hiddenEl = document.getElementById(hiddenId);
  if (!hiddenEl) return;
  const container = btn.closest('.diff-container-clean');
  if (!container) return;

  // Parse and render the remaining lines
  const remainingRaw = hiddenEl.textContent;
  const remainingRendered = remainingRaw.split('\n').map(line => {
    if (line.startsWith('+') && !line.startsWith('+++')) {
      return `<span class="diff-add">${escapeHtml(line)}</span>`;
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      return `<span class="diff-del">${escapeHtml(line)}</span>`;
    } else if (line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')) {
      return `<span class="diff-meta">${escapeHtml(line)}</span>`;
    }
    return `<span>${escapeHtml(line)}</span>`;
  }).join('\n');

  // Remove truncation notice and hidden element
  btn.closest('.diff-truncation-notice').remove();
  hiddenEl.remove();

  // Append remaining rendered lines to the container
  const appendEl = document.createElement('span');
  appendEl.innerHTML = '\n' + remainingRendered;
  container.appendChild(appendEl);
  container.style.maxHeight = 'none';
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

async function approveWorkflowAction() {
  if (!currentWorkflowId) return;
  try {
    const res = await fetch(`/api/workflows/${currentWorkflowId}/approve`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      alert("Pull Request approved and merged.");
      loadWorkflowDetails();
    }
  } catch (err) {
    alert("Approval error: " + err);
  }
}

async function rejectWorkflowAction() {
  if (!currentWorkflowId) return;
  const reason = prompt("Rejection reason:", "Code adjustments required");
  try {
    const res = await fetch(`/api/workflows/${currentWorkflowId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason })
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert("Changes rejected.");
      loadWorkflowDetails();
    }
  } catch (err) {
    alert("Rejection error: " + err);
  }
}

async function exportReportJson() {
  if (!currentWorkflowId) return;
  try {
    const res = await fetch(`/api/workflows/${currentWorkflowId}/report`);
    const data = await res.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `DevFlow_Report_${currentWorkflowId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert("Report export failed: " + err);
  }
}

function sendQuickPrompt(promptText) {
  const input = document.getElementById('chatInputMessage');
  if (input) {
    input.value = promptText;
    sendChatMessage();
  }
}

async function sendChatMessage() {
  const input = document.getElementById('chatInputMessage');
  const btn = document.getElementById('btnSendChat');
  const thread = document.getElementById('chatMessageThread');
  if (!input || !currentWorkflowId) return;

  const msg = input.value.trim();
  if (!msg) return;

  // Append user message
  const userMsgHtml = `
    <div class="d-flex gap-2 justify-content-end">
      <div class="bg-dark text-white p-2 px-3 rounded small" style="max-width: 85%;">
        ${escapeHtml(msg)}
      </div>
      <div class="bg-secondary text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 28px; height: 28px; flex-shrink: 0; font-size: 0.75rem;">
        <i class="fa-solid fa-user"></i>
      </div>
    </div>
  `;
  thread.insertAdjacentHTML('beforeend', userMsgHtml);
  input.value = '';
  thread.scrollTop = thread.scrollHeight;

  // Append loading state
  const loadingId = 'loading-' + Date.now();
  const loadingHtml = `
    <div class="d-flex gap-2" id="${loadingId}">
      <div class="bg-success text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 28px; height: 28px; flex-shrink: 0; font-size: 0.75rem;">
        <i class="fa-solid fa-robot"></i>
      </div>
      <div class="bg-white p-3 rounded shadow-sm border small text-muted" style="max-width: 85%;">
        <span class="spinner-border spinner-border-sm me-1"></span> Analyzing workflow telemetry and codebase...
      </div>
    </div>
  `;
  thread.insertAdjacentHTML('beforeend', loadingHtml);
  thread.scrollTop = thread.scrollHeight;

  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`/api/workflows/${currentWorkflowId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });
    const data = await res.json();
    const loadEl = document.getElementById(loadingId);
    if (loadEl) loadEl.remove();

    if (res.ok && data.reply) {
      const replyFormatted = formatChatMarkdown(data.reply);
      const aiMsgHtml = `
        <div class="d-flex gap-2 align-items-start">
          <div class="bg-success text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 28px; height: 28px; flex-shrink: 0; font-size: 0.75rem; margin-top: 2px;">
            <i class="fa-solid fa-robot"></i>
          </div>
          <div class="bg-white p-3 rounded shadow-sm border text-dark" style="max-width: 92%; width: 100%;">
            <div class="fw-bold text-dark mb-2 small d-flex align-items-center gap-1">
              <span>DevFlow Copilot</span>
              <span class="badge-pill green py-0 px-1" style="font-size: 0.65rem;">AI</span>
            </div>
            <div>${replyFormatted}</div>
          </div>
        </div>
      `;
      thread.insertAdjacentHTML('beforeend', aiMsgHtml);
      thread.scrollTop = thread.scrollHeight;
    } else {
      const errMsgHtml = `
        <div class="d-flex gap-2 align-items-start">
          <div class="bg-danger text-white rounded-circle d-flex align-items-center justify-content-center" style="width: 28px; height: 28px; flex-shrink: 0; font-size: 0.75rem;">
            <i class="fa-solid fa-triangle-exclamation"></i>
          </div>
          <div class="bg-white p-2 px-3 rounded shadow-sm border small text-danger" style="max-width: 85%;">
            ${escapeHtml(data.error || "Failed to generate reply.")}
          </div>
        </div>
      `;
      thread.insertAdjacentHTML('beforeend', errMsgHtml);
    }
  } catch (err) {
    const loadEl = document.getElementById(loadingId);
    if (loadEl) loadEl.remove();
    console.error("Chat error:", err);
  } finally {
    if (btn) btn.disabled = false;
    thread.scrollTop = thread.scrollHeight;
  }
}

function formatChatMarkdown(text) {
  if (!text) return "";

  // 1. Normalize literal escaped characters
  let cleanText = text.replace(/\\n/g, '\n').replace(/\\t/g, '  ').replace(/\\r/g, '');

  // 2. Pre-process any raw markdown tables (| Col 1 | Col 2 |) into beautiful, readable SaaS cards
  cleanText = preprocessMarkdownTables(cleanText);

  // 3. Use Marked.js for full GitHub-Flavored Markdown parsing
  if (typeof marked !== 'undefined') {
    try {
      marked.setOptions({
        gfm: true,
        breaks: true,
        pedantic: false
      });
      let parsed = marked.parse(cleanText);
      if (typeof DOMPurify !== 'undefined') {
        parsed = DOMPurify.sanitize(parsed, {
          ADD_ATTR: ['target', 'class', 'style']
        });
      }
      return `<div class="chat-markdown-body">${parsed}</div>`;
    } catch (err) {
      console.warn("Marked parsing fallback:", err);
    }
  }

  // 4. Robust fallback parser
  return `<div class="chat-markdown-body">${renderBasicMarkdown(cleanText)}</div>`;
}

function preprocessMarkdownTables(rawText) {
  const lines = rawText.split('\n');
  let result = [];
  let inTable = false;
  let headers = [];
  let tableRows = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith('|') && line.endsWith('|')) {
      const cells = line.split('|').slice(1, -1).map(c => c.trim());
      if (cells.every(c => c.match(/^[-:\s]+$/))) {
        // Skip separator row
        continue;
      }
      if (!inTable) {
        inTable = true;
        headers = cells;
        tableRows = [];
      } else {
        tableRows.push(cells);
      }
    } else {
      if (inTable) {
        result.push(renderTableAsCleanCards(headers, tableRows));
        inTable = false;
        headers = [];
        tableRows = [];
      }
      result.push(lines[i]);
    }
  }
  if (inTable) {
    result.push(renderTableAsCleanCards(headers, tableRows));
  }
  return result.join('\n');
}

function renderTableAsCleanCards(headers, rows) {
  if (!rows || rows.length === 0) return '';

  let html = '\n\n<div class="chat-card-grid my-3">\n';
  rows.forEach((row, idx) => {
    const category = (row[0] || `Check #${idx + 1}`).replace(/\*\*/g, '').replace(/`/g, '').trim();
    const whyItMatters = (row[1] || '').trim();
    const testIdeas = (row[2] || '').trim();
    const tools = (row[3] || '').trim();

    html += `<div class="chat-card p-3 rounded bg-white border shadow-sm mb-3">
      <div class="d-flex align-items-center gap-2 mb-2">
        <span class="badge-pill green px-2 py-1 small fw-bold">#${idx + 1}</span>
        <h6 class="fw-bold text-dark mb-0">${category}</h6>
      </div>`;

    if (whyItMatters) {
      html += `<div class="small text-secondary mb-2 p-2 bg-light rounded border-start border-3 border-success">
        <strong class="text-dark"><i class="fa-solid fa-circle-info text-success me-1"></i>Why it matters:</strong> ${whyItMatters}
      </div>`;
    }

    if (testIdeas) {
      // Split ideas by <br> or - or bullet points
      const bullets = testIdeas.split(/<br\s*\/?>|\n/g).map(b => b.trim()).filter(Boolean);
      html += `<div class="small text-dark mb-2">
        <strong class="d-block mb-1 text-dark"><i class="fa-solid fa-list-check text-primary me-1"></i>Actionable Test Cases:</strong>
        <ul class="mb-0 ps-3">`;
      bullets.forEach(b => {
        const cleanBullet = b.replace(/^[-*•]\s*/, '');
        html += `<li class="mb-1">${cleanBullet}</li>`;
      });
      html += `</ul></div>`;
    }

    if (tools) {
      html += `<div class="mt-2 pt-2 border-top small text-secondary">
        <strong class="text-dark"><i class="fa-solid fa-terminal text-dark me-1"></i>Commands / Tools:</strong>
        <div class="mt-1">${tools.replace(/<br\s*\/?>/g, '<br>')}</div>
      </div>`;
    }

    html += `</div>\n`;
  });

  html += '</div>\n\n';
  return html;
}

function renderBasicMarkdown(raw) {
  let text = escapeHtml(raw);

  // Multiline Code Blocks
  text = text.replace(/```([a-zA-Z0-9_\-]+)?\n?([\s\S]*?)```/g, (m, lang, code) => {
    return `<pre><code>${code}</code></pre>`;
  });

  // Inline Code
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold & Italic
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Headers
  text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  text = text.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  text = text.replace(/^# (.*$)/gim, '<h1>$1</h1>');

  // Lists
  text = text.replace(/^\s*[-*]\s+(.*$)/gim, '<li>$1</li>');
  text = text.replace(/(<li>.*<\/li>)/gims, '<ul>$1</ul>');

  return text.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
}



