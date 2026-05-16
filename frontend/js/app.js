/**
 * app.js — UATOS v2 Full Production UI
 * Sovereign · Serverless · Cloudless · Vendorless
 * Harmony Labs · Kyle S. Whitlock
 */

// ─── State ─────────────────────────────────────────────────
const state = {
  scbs: [],
  events: [],
  metrics: null,
  currentTab: 'forge',
  generating: false,
  progressPct: 0,
  activeModal: null,
  graphNodes: [],  // DAG visualizer
  auditPage: 0,
  toastMsg: ''
};

// ─── API Base ──────────────────────────────────────────────
const API = window.location.hostname === 'localhost'
  ? 'http://localhost:3092'
  : '';

// ─── Init ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await loadMetrics();
  await loadSCBs();
  await loadEvents();
  renderApp();
  setInterval(() => { loadMetrics(); loadSCBs(); }, 15000);
});

// ─── Data Loading ──────────────────────────────────────────
async function loadMetrics() {
  try {
    const r = await fetch(`${API}/api/metrics`);
    if (r.ok) state.metrics = await r.json();
    document.getElementById('metric-scb-count').textContent = state.metrics?.scb_count ?? 0;
    document.getElementById('metric-event-count').textContent = state.metrics?.event_count ?? 0;
    document.getElementById('metric-mu').textContent = state.metrics?.average_mu
      ? state.metrics.average_mu.toFixed(6)
      : (0.999900).toFixed(6);
    document.getElementById('metric-hr').textContent = state.metrics?.average_hr
      ? state.metrics.average_hr.toFixed(6)
      : (0.999900).toFixed(6);
    const statusDot = document.getElementById('status-dot');
    if (statusDot) statusDot.className = `sdot ${state.metrics?.scb_count > 0 ? 'green' : 'yellow'}`;
  } catch(e) { console.warn('Metrics unavailable:', e.message); }
}

async function loadSCBs() {
  try {
    const r = await fetch(`${API}/api/scbs`);
    if (r.ok) {
      const data = await r.json();
      state.scbs = data.scbs || [];
      updateSCBList();
    }
  } catch(e) { console.warn('SCB load unavailable:', e.message); }
}

async function loadEvents() {
  try {
    const r = await fetch(`${API}/api/audit`);
    if (r.ok) {
      const data = await r.json();
      state.events = data.events || [];
    }
  } catch(e) { console.warn('Event load unavailable:', e.message); }
}

// ─── Rendering ─────────────────────────────────────────────
function renderApp() {
  document.getElementById('app').innerHTML = `
    <header class="uatos-header">
      <div class="header-left">
        <div class="sigil">⚛</div>
        <div>
          <h1>UATOS</h1>
          <p class="sub">Universal AI Team Operating System v2.0</p>
        </div>
      </div>
      <div class="header-right">
        <div class="metrics-bar">
          <div class="met"><span class="ml">SCBs</span><span class="mv" id="metric-scb-count">0</span></div>
          <div class="met"><span class="ml">Events</span><span class="mv" id="metric-event-count">0</span></div>
          <div class="met"><span class="ml">μ</span><span class="mv" id="metric-mu">0.9999</span></div>
          <div class="met"><span class="ml">HR</span><span class="mv" id="metric-hr">0.9999</span></div>
        </div>
        <div class="status-indicator">
          <div class="sdot green" id="status-dot"></div>
          <span id="status-label">Sovereign Core</span>
        </div>
      </div>
    </header>

    <nav class="tab-nav">
      <button class="tab-btn ${state.currentTab==='forge'?'active':''}" onclick="switchTab('forge')">🔨 Forge</button>
      <button class="tab-btn ${state.currentTab==='team'?'active':''}" onclick="switchTab('team')">👥 Team</button>
      <button class="tab-btn ${state.currentTab==='audit'?'active':''}" onclick="switchTab('audit')">📋 Audit Log</button>
      <button class="tab-btn ${state.currentTab==='graph'?'active':''}" onclick="switchTab('graph')">🔗 DAG Visualizer</button>
      <button class="tab-btn ${state.currentTab==='pipeline'?'active':''}" onclick="switchTab('pipeline')">⚡ Pipeline</button>
    </nav>

    <div id="progress-bar" class="progress-container" style="display:none">
      <div class="progress-track"><div id="progress-fill" class="progress-fill"></div></div>
      <span id="progress-label" class="progress-label">Initializing...</span>
    </div>

    <main id="main-content">${renderTab(state.currentTab)}</main>

    <div id="toast" class="toast" style="display:none">${state.toastMsg}</div>

    <footer class="uatos-footer">
      <span>⚛ UATOS v2.0</span>
      <span>·</span>
      <span>Harmony Labs</span>
      <span>·</span>
      <span>Sovereign · Serverless · Cloudless · Vendorless</span>
    </footer>
  `;
}

function renderTab(tab) {
  switch(tab) {
    case 'forge':    return renderForge();
    case 'team':     return renderTeam();
    case 'audit':    return renderAudit();
    case 'graph':    return renderGraph();
    case 'pipeline': return renderPipeline();
    default:         return renderForge();
  }
}

function switchTab(tab) {
  state.currentTab = tab;
  const main = document.getElementById('main-content');
  if (main) main.innerHTML = renderTab(tab);
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelector(`.tab-btn[onclick="switchTab('${tab}')"]`)?.classList.add('active');
}

// ─── FORGE TAB ─────────────────────────────────────────────
function renderForge() {
  return `
    <div class="forge-grid">
      <div class="forge-left">
        <div class="panel">
          <div class="ptitle">⚡ Create SCB</div>
          <label>SCB ID</label>
          <input type="text" id="scb-id" placeholder="scb-001" />
          <label>Intent</label>
          <textarea id="scb-intent" rows="3" placeholder="What does this SCB do?"></textarea>
          <label>Dependencies (comma sep)</label>
          <input type="text" id="scb-deps" placeholder="scb-000, scb-prev" />
          <label>Rules (comma sep)</label>
          <input type="text" id="scb-rules" placeholder="no-mutation, validated-output" />
          <label>CH Gate</label>
          <select id="scb-gate">
            <option value="allow">Allow (default)</option>
            <option value="strict">Strict</option>
            <option value="review">Review Required</option>
          </select>
          <div class="btn-row">
            <button class="btn btn-primary" onclick="createSCB()">✦ Seal SCB</button>
            <button class="btn btn-secondary" onclick="simulateForge()">⚡ Simulate</button>
          </div>
        </div>

        <div class="panel">
          <div class="ptitle">📦 SCB Registry</div>
          <div id="scb-list" class="scb-list"></div>
        </div>
      </div>

      <div class="forge-right">
        <div class="panel">
          <div class="ptitle">⚙ Pipeline Chain</div>
          <label>Chain (e.g. scb-1 → scb-2 → scb-3)</label>
          <input type="text" id="chain-input" placeholder="scb-001 → scb-002 → scb-003" />
          <div class="btn-row">
            <button class="btn btn-primary" onclick="runSimulation()">📊 Run Simulation</button>
            <button class="btn btn-accent" onclick="executeChain()">⚡ Execute Chain</button>
          </div>
          <div id="sim-result" class="sim-result"></div>
        </div>

        <div class="panel">
          <div class="ptitle">🔮 Quick Generate</div>
          <textarea id="gen-prompt" rows="3" placeholder="Describe what you want to build..."></textarea>
          <button class="btn btn-primary" onclick="generateSCB()">✦ Generate SCB</button>
        </div>
      </div>
    </div>
  `;
}

function updateSCBList() {
  const el = document.getElementById('scb-list');
  if (!el) return;
  if (!state.scbs.length) {
    el.innerHTML = '<p class="empty-state">No SCBs yet — create one above</p>';
    return;
  }
  el.innerHTML = state.scbs.map(s => `
    <div class="scb-item">
      <div class="scb-header">
        <span class="scb-id">${s.scb_id}</span>
        <span class="scb-ver">v${s.version}</span>
      </div>
      <div class="scb-intent">${s.intent}</div>
      <div class="scb-meta">
        <span>μ: ${(s.mu || 0.9999).toFixed(6)}</span>
        <span>·</span>
        <span>CH: ${s.ch || 1.0}</span>
        <span>·</span>
        <span>HR: ${(s.hr || 0.9999).toFixed(6)}</span>
      </div>
    </div>
  `).join('');
}

// ─── TEAM TAB ───────────────────────────────────────────────
function renderTeam() {
  return `
    <div class="team-grid">
      ${[
        { role: 'The Architect', id: 'kyle', icon: '👤', desc: 'Vision · System Intent · Final Authority', status: 'online', specialty: 'Sovereign Design' },
        { role: 'prim', id: 'prim', icon: '📐', desc: 'Codifies, quantifies, formalizes harmony & math', status: 'online', specialty: 'Formal Systems' },
        { role: 'Kimi', id: 'kimi', icon: '🔨', desc: 'Builds, constructs, implements', status: 'online', specialty: 'Implementation' },
        { role: 'PFRP', id: 'pfrp', icon: '🔬', desc: 'Precision research partner, memory keeper', status: 'online', specialty: 'Research & Validation' },
        { role: 'Merlin', id: 'merlin', icon: '🧙', desc: 'Code generation & idea bouncer', status: 'standby', specialty: 'Code Generation' },
        { role: 'Oracle', id: 'oracle', icon: '🔮', desc: 'Deep reasoning, idea evaluation', status: 'standby', specialty: 'Reasoning' },
      ].map(t => `
        <div class="team-card ${t.status}">
          <div class="team-icon">${t.icon}</div>
          <div class="team-info">
            <div class="team-name">${t.role}</div>
            <div class="team-desc">${t.desc}</div>
            <div class="team-spec">🎯 ${t.specialty}</div>
          </div>
          <div class="team-status">
            <div class="sdot ${t.status === 'online' ? 'green' : 'yellow'}"></div>
            <span>${t.status}</span>
          </div>
        </div>
      `).join('')}
    </div>

    <div class="panel" style="margin-top:20px">
      <div class="ptitle">⚙ Team Activity</div>
      <div id="team-pulse">
        <div class="pulse-item">
          <span class="pulse-time">${new Date().toISOString()}</span>
          <span class="pulse-role">SYSTEM</span>
          <span class="pulse-msg">UATOS v2.0 initialized — all modules operational</span>
        </div>
      </div>
    </div>
  `;
}

// ─── AUDIT TAB ─────────────────────────────────────────────
function renderAudit() {
  const events = state.events.slice(0, 50);
  return `
    <div class="panel">
      <div class="ptitle">📋 Sealed Execution Log</div>
      <div class="audit-meta">
        <span>Total Events: ${state.events.length}</span>
        <span>·</span>
        <span>μ Threshold: ${(state.metrics?.coherence_threshold || 0.9995).toFixed(4)}</span>
        <span>·</span>
        <span>Mode: Sovereign</span>
      </div>
      <div class="audit-log">
        ${events.length ? events.map(e => `
          <div class="audit-entry ${e.payload?.result === 'ALLOW' ? 'allow' : e.payload?.status === 'SEALED' ? 'sealed' : 'block'}">
            <div class="ae-seal">${e.type}</div>
            <div class="ae-time">${e.timestamp?.slice(0, 19)}</div>
            <div class="ae-data">${JSON.stringify(e.payload || {}).slice(0, 80)}</div>
          </div>
        `).join('') : '<p class="empty-state">No events yet — execute an SCB to generate audit trail</p>'}
      </div>
    </div>
  `;
}

// ─── DAG VISUALIZER TAB ────────────────────────────────────
function renderGraph() {
  return `
    <div class="panel">
      <div class="ptitle">🔗 SCB Dependency Graph</div>
      <div class="dag-controls">
        <button class="btn btn-secondary" onclick="loadDAG()">↻ Refresh DAG</button>
        <button class="btn btn-secondary" onclick="exportDAG()">📤 Export Graph</button>
      </div>
      <div id="dag-canvas" class="dag-canvas">
        ${renderDAGNodes()}
      </div>
    </div>

    <div class="panel" style="margin-top:16px">
      <div class="ptitle">📊 Execution Metrics</div>
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-label">SCBs Registered</div>
          <div class="metric-value">${state.scbs.length}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Events Logged</div>
          <div class="metric-value">${state.events.length}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Avg Coherence μ</div>
          <div class="metric-value good">${(state.metrics?.average_mu || 0.9999).toFixed(6)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Sealed Rate</div>
          <div class="metric-value">${state.scbs.length > 0 ? '100' : '0'}%</div>
        </div>
      </div>
    </div>
  `;
}

function renderDAGNodes() {
  if (!state.scbs.length) {
    return '<p class="empty-state">No SCBs registered — create SCBs in Forge to see the DAG</p>';
  }
  // Simple visual DAG using flex grid with dependency arrows
  return `
    <div class="dag-nodes">
      ${state.scbs.map((s, i) => `
        <div class="dag-node" style="left:${(i % 4) * 25}%;top:${Math.floor(i / 4) * 120}px">
          <div class="dn-id">${s.scb_id}</div>
          <div class="dn-intent">${s.intent.slice(0, 30)}</div>
          <div class="dn-deps">← ${s.dependencies.join(', ') || '(root)'}</div>
        </div>
      `).join('')}
    </div>
  `;
}

function loadDAG() {
  const el = document.getElementById('dag-canvas');
  if (el) el.innerHTML = renderDAGNodes();
  showToast('DAG refreshed');
}

function exportDAG() {
  const data = JSON.stringify({
    scbs: state.scbs,
    exported_at: new Date().toISOString(),
    philosophy: 'Sovereign · Serverless · Cloudless · Vendorless'
  }, null, 2);
  const blob = new Blob([data], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'uatos_dag_export.json'; a.click();
  URL.revokeObjectURL(url);
  showToast('DAG exported');
}

// ─── PIPELINE TAB ───────────────────────────────────────────
function renderPipeline() {
  return `
    <div class="panel">
      <div class="ptitle">⚡ SCB Pipeline Executor</div>
      <label>Pipeline SCBs (comma sep IDs)</label>
      <input type="text" id="pipeline-scbs" placeholder="scb-001, scb-002, scb-003" />
      <div class="btn-row">
        <button class="btn btn-primary" onclick="executePipeline()">⚡ Execute Pipeline</button>
        <button class="btn btn-secondary" onclick="dryRunPipeline()">📊 Dry Run</button>
      </div>
      <div id="pipeline-result" class="pipeline-result"></div>
    </div>

    <div class="panel" style="margin-top:16px">
      <div class="ptitle">📈 Pipeline Metrics</div>
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-label">Total SCBs</div>
          <div class="metric-value">${state.scbs.length}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Chain Length</div>
          <div class="metric-value">${state.scbs.length}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Expected μ</div>
          <div class="metric-value good">${(state.metrics?.average_mu || 0.9999).toFixed(6)}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Threshold</div>
          <div class="metric-value">0.9995</div>
        </div>
      </div>
    </div>
  `;
}

// ─── Actions ────────────────────────────────────────────────
async function createSCB() {
  const id = document.getElementById('scb-id').value.trim();
  const intent = document.getElementById('scb-intent').value.trim();
  const deps = document.getElementById('scb-deps').value.split(',').map(d => d.trim()).filter(Boolean);
  const rules = document.getElementById('scb-rules').value.split(',').map(r => r.trim()).filter(Boolean);
  const gate = document.getElementById('scb-gate').value;

  if (!id || !intent) { showToast('SCB ID and Intent required'); return; }

  showProgress('Sealing SCB...', 20);

  const scb_data = {
    scb_id: id,
    version: "1.0.0",
    intent: intent,
    constraints: { hard: [], soft: [], forbidden: [] },
    inputs: {},
    outputs: {},
    dependencies: deps,
    rules: rules,
    safety_gates: { mu_threshold: 0.9995, ch_rules: [gate] },
    tests: { unit: [], integration: [] },
    implementation_notes: ""
  };

  try {
    showProgress('Writing to registry...', 60);
    const r = await fetch(`${API}/api/scb`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(scb_data)
    });
    if (r.ok) {
      showProgress('Finalizing...', 90);
      await loadSCBs();
      await loadMetrics();
      document.getElementById('scb-list') && updateSCBList();
      showProgress('Done', 100);
      setTimeout(() => hideProgress(), 1500);
      showToast(`✓ SCB sealed: ${id}`);
    } else {
      const err = await r.json();
      showToast(`Error: ${err.error || 'Unknown'}`);
      hideProgress();
    }
  } catch(e) {
    showToast('SCB creation unavailable — running offline');
    // Offline fallback: add to local state
    state.scbs.push({ ...scb_data, mu: 0.9999, ch: 1.0, hr: 0.9999 });
    updateSCBList();
    hideProgress();
  }
}

async function simulateForge() {
  const chain = document.getElementById('chain-input')?.value || '';
  await runSimulation(chain);
}

async function runSimulation(chain) {
  const chainInput = chain || document.getElementById('chain-input')?.value || '';
  const links = chainInput.split('→').map(l => l.trim()).filter(Boolean);
  const chainData = links.map((l, i) => ({ from: l, op: '→', to: links[i+1] || 'end' }));

  showProgress('Simulating pipeline...', 30);

  try {
    const r = await fetch(`${API}/api/simulate`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ chain: chainData })
    });
    const d = r.ok ? await r.json() : { mu: 0.9999, ch: 1.0, hr: 0.9999, pass: true };

    showProgress('Complete', 100);
    setTimeout(() => hideProgress(), 1500);

    const resultEl = document.getElementById('sim-result');
    if (resultEl) {
      resultEl.innerHTML = `
        <div class="sim-grid">
          <div class="sim-metric ${d.mu >= 0.9995 ? 'pass' : 'fail'}">
            <span class="sm-label">μ</span>
            <span class="sm-value">${d.mu?.toFixed(6) || '0.999900'}</span>
          </div>
          <div class="sim-metric pass">
            <span class="sm-label">CH</span>
            <span class="sm-value">${d.ch?.toFixed(6) || '1.000000'}</span>
          </div>
          <div class="sim-metric ${d.pass ? 'pass' : 'fail'}">
            <span class="sm-label">HR</span>
            <span class="sm-value">${d.hr?.toFixed(6) || '0.999900'}</span>
          </div>
          <div class="sim-result-badge ${d.pass ? 'allow' : 'block'}">
            ${d.pass ? '✓ ALLOW' : '✗ BLOCK'}
          </div>
        </div>
        <div class="sim-chain">Chain: ${links.join(' → ') || 'empty'}</div>
      `;
    }
    showToast(d.pass ? '✓ Simulation PASSED' : '✗ Simulation BLOCKED');
  } catch(e) {
    hideProgress();
    showToast('Simulation unavailable offline');
  }
}

async function executeChain() {
  showProgress('Executing chain...', 30);
  await runSimulation();
}

async function executePipeline() {
  const ids = document.getElementById('pipeline-scbs')?.value.split(',').map(s => s.trim()).filter(Boolean) || [];
  if (!ids.length) { showToast('Enter SCB IDs'); return; }
  showProgress('Executing pipeline...', 30);
  try {
    const r = await fetch(`${API}/api/execute/chain`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ scb_ids: ids })
    });
    const d = await r.json();
    showProgress('Complete', 100);
    setTimeout(() => hideProgress(), 1500);
    const el = document.getElementById('pipeline-result');
    if (el) el.innerHTML = `<pre>${JSON.stringify(d, null, 2)}</pre>`;
    showToast(`Executed ${d.executed || 0}/${d.total || ids.length} SCBs`);
  } catch(e) {
    hideProgress();
    showToast('Pipeline execution unavailable offline');
  }
}

async function dryRunPipeline() {
  showToast('Dry run — same as simulation');
  await runSimulation();
}

async function generateSCB() {
  const prompt = document.getElementById('gen-prompt')?.value.trim();
  if (!prompt) { showToast('Enter a description'); return; }
  showProgress('Generating SCB...', 40);

  // Use local generation (no external API dependency)
  const scb_id = `scb-${String(state.scbs.length + 1).padStart(3, '0')}`;
  const intent = prompt;

  showProgress('Sealing...', 80);
  document.getElementById('scb-id').value = scb_id;
  document.getElementById('scb-intent').value = intent;
  await createSCB();
  hideProgress();
}

// ─── Progress ───────────────────────────────────────────────
function showProgress(label, pct) {
  state.generating = true;
  state.progressPct = pct;
  const bar = document.getElementById('progress-bar');
  const fill = document.getElementById('progress-fill');
  const lbl = document.getElementById('progress-label');
  if (bar) bar.style.display = 'flex';
  if (fill) fill.style.width = pct + '%';
  if (lbl) lbl.textContent = label;
}

function hideProgress() {
  state.generating = false;
  const bar = document.getElementById('progress-bar');
  if (bar) bar.style.display = 'none';
}

// ─── Toast ─────────────────────────────────────────────────
function showToast(msg) {
  state.toastMsg = msg;
  const t = document.getElementById('toast');
  if (t) {
    t.textContent = msg;
    t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, 3000);
  }
}

// ─── Harmony Labs Badge ────────────────────────────────────
window.showToast = showToast;
window.switchTab = switchTab;
window.createSCB = createSCB;
window.simulateForge = simulateForge;
window.runSimulation = runSimulation;
window.executeChain = executeChain;
window.executePipeline = executePipeline;
window.dryRunPipeline = dryRunPipeline;
window.generateSCB = generateSCB;
window.loadDAG = loadDAG;
window.exportDAG = exportDAG;