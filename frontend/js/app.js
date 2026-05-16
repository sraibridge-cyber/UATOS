/**
 * app.js — UATOS v1 Main React Application
 * Universal AI Team Operating System
 *
 * Tabs: Forge | Team | Audit Log
 * Stores: localStorage (scbs, audit log, mu/ch history)
 */

import { RISK_LEVELS, RISK_COLORS, makeSCB, addSCB, updateSCB, listSCBs, saveSCBs } from './core/scb-manager.js';
import { OPERATOR_DISPLAY, makeChainLink, detectCollisions } from './core/pipeline-engine.js';
import { CONSTITUTIONAL_THRESHOLD, calcCoherence, calcCH, calcHR, checkThreshold, mkMetrics, getDefaultMuLog, getDefaultCHLog, updateMetrics } from './core/coherence-calc.js';
import { makeSeal, mkAuditEntry, listAuditLog, appendAuditEntry } from './core/audit-log.js';
import { TEAM, SEPARATION_OF_POWERS, makeTeamPulse, activateTeamMember, deactivateAll } from './core/team-pulse.js';

const TABS = [
  { id: 'forge', label: '⚒️ The Forge' },
  { id: 'team',  label: '👥 The Team' },
  { id: 'audit', label: '📜 Audit Log' },
];

// ── Coherence mini-chart bar ──────────────────────────────
function MiniBar({ value, color, label }) {
  const pct = Math.round(value * 100);
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value" style={{ color }}>{value.toFixed(6)}</div>
      <div className="metric-bar">
        {[...Array(10)].map((_, i) => (
          <div
            key={i}
            className="metric-bar-item"
            style={{
              height: `${pct}%`,
              background: i < Math.round(pct) ? color + '66' : 'rgba(255,255,255,0.05)',
            }}
          />
        ))}
      </div>
    </div>
  );
}

// ── SCB List Item ──────────────────────────────────────────
function SCBItem({ scb, active, onClick }) {
  return (
    <div className={`scb-item ${active ? 'active' : ''}`} onClick={onClick}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="scb-id">{scb.id}</span>
        <span className={`risk-badge risk-${scb.risk}`}>{scb.risk}</span>
      </div>
      <div className="scb-intent">{scb.intent}</div>
    </div>
  );
}

// ── SCB Editor ─────────────────────────────────────────────
function SCBEditor({ scb, onUpdate }) {
  return (
    <div className="card">
      <h3>SCB EDITOR — {scb.id.toUpperCase()}</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <label>INTENT
          <input
            value={scb.intent}
            onChange={e => onUpdate(scb.id, 'intent', e.target.value)}
            placeholder="What does this SCB do?"
          />
        </label>
        <label>RISK LEVEL
          <select
            value={scb.risk}
            onChange={e => onUpdate(scb.id, 'risk', e.target.value)}
            style={{ color: RISK_COLORS[scb.risk] }}
          >
            {RISK_LEVELS.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </label>
        <label>DEPENDENCIES (comma sep SCB IDs)
          <input
            value={scb.deps.join(', ')}
            onChange={e => onUpdate(scb.id, 'deps', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
            placeholder="e.g. scb-001, scb-002"
          />
        </label>
        {scb.mu && (
          <div style={{ fontSize: 11, fontFamily: 'monospace', color: '#6b7280', padding: '6px 10px', background: 'rgba(0,0,0,0.2)', borderRadius: 6 }}>
            μ={scb.mu} | CH={scb.ch || '—'} | HR={scb.hr || '—'} | {scb.status}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Chain Link Row ─────────────────────────────────────────
function ChainLinkRow({ link, scbs, onUpdate }) {
  return (
    <div className="chain-link">
      <select value={link.from} onChange={e => onUpdate(link, 'from', e.target.value)} style={{ flex: 1 }}>
        <option value="">— from —</option>
        {scbs.map(s => <option key={s.id} value={s.id}>{s.id} | {s.intent}</option>)}
      </select>
      <select className="op" value={link.op} onChange={e => onUpdate(link, 'op', e.target.value)}>
        {Object.keys(OPERATOR_DISPLAY).map(op => (
          <option key={op} value={op}>{OPERATOR_DISPLAY[op]}</option>
        ))}
      </select>
      <select value={link.to} onChange={e => onUpdate(link, 'to', e.target.value)} style={{ flex: 1 }}>
        <option value="">— to —</option>
        {scbs.map(s => <option key={s.id} value={s.id}>{s.id} | {s.intent}</option>)}
      </select>
    </div>
  );
}

// ── Simulate Button ────────────────────────────────────────
function SimOutput({ simOutput }) {
  if (!simOutput) return null;
  const pass = simOutput.includes('PASS');
  return (
    <div className={`sim-output ${pass ? 'pass' : 'fail'}`}>
      {simOutput}
    </div>
  );
}

// ── Audit Log Entry ────────────────────────────────────────
function AuditEntry({ entry }) {
  const isOk = entry.result === 'ALLOW' || entry.result === 'SEALED';
  return (
    <div className="log-entry">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="log-seal">{entry.seal.slice(0, 60)}</span>
        <span className={`log-result log-result-${entry.result.toLowerCase()}`}>{entry.result}</span>
      </div>
      <div className="log-event">{entry.event}</div>
      {entry.mu && <div className="log-metrics">μ={entry.mu} | CH={entry.ch} | HR={entry.hr}</div>}
      {entry.chain && <div className="log-metrics" style={{ fontFamily: 'monospace' }}>{entry.chain}</div>}
    </div>
  );
}

// ── Main App ────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState('forge');
  const [scbs, setScbs] = useState(() => { const s = listSCBs(); return s.length ? s : [makeSCB('scb-001', 'Parse Human Intent')]; });
  const [activeId, setActiveId] = useState('scb-001');
  const [chain, setChain] = useState([makeChainLink('scb-001', 'SEQUENCE', null)]);
  const [muLog, setMuLog] = useState(getDefaultMuLog());
  const [chLog, setChLog] = useState(getDefaultCHLog());
  const [auditLog, setAuditLog] = useState(() => listAuditLog());
  const [teamPulse, setTeamPulse] = useState(makeTeamPulse());
  const [simOutput, setSimOutput] = useState('');
  const [conflictAlerts, setConflictAlerts] = useState([]);

  const active = scbs.find(s => s.id === activeId) || scbs[0];

  // ── SCB Ops ────────────────────────────────────────────
  function handleAddSCB() {
    const id = `scb-${String(scbs.length + 1).padStart(3, '0')}`;
    const ns = addSCB(scbs, `SCB ${scbs.length + 1} goal`);
    saveSCBs(ns);
    setScbs(ns);
    setActiveId(id);
  }

  function handleUpdateSCB(id, field, val) {
    const ns = updateSCB(scbs, id, field, val);
    saveSCBs(ns);
    setScbs(ns);
  }

  function handleChainUpdate(link, field, val) {
    const nc = chain.map(l => l === link ? { ...link, [field]: val } : l);
    setChain(nc);
    setConflictAlerts(detectCollisions(nc, scbs));
  }

  // ── Simulation ─────────────────────────────────────────
  function handleSimulate() {
    const muVals = [0.9999, 0.9998, 0.9997, 0.9996];
    const chVals = [1.0, 1.0, 1.0, 1.0];
    const mu = calcCoherence(muVals);
    const ch = calcCH(chVals);
    const hr = calcHR(mu, ch);
    const pass = checkThreshold(hr);
    const metrics = mkMetrics(mu, ch, hr);
    const { muLog: newMuLog, chLog: newChLog } = updateMetrics(muLog, chLog, mu, ch);
    setMuLog(newMuLog);
    setChLog(newChLog);

    const chainStr = chain.map(l => `${l.from} ${OPERATOR_DISPLAY[l.op] || l.op} ${l.to || '?'}`).join(' | ');
    const output = `μ=${mu.toFixed(6)} | CH=${ch.toFixed(6)} | HR=${hr.toFixed(6)} | ${pass ? '✅ PASS — ALLOW' : '❌ FAIL — BLOCK'}`;
    setSimOutput(output);

    const entry = {
      seal: `SR-AIB_HR-${active.id.toUpperCase()}_SIM_SHA3-${Math.abs(Date.now()).toString(16).padStart(8, '0')}@${new Date().toISOString()}`,
      event: `Simulation: ${active.intent}`,
      role: 'PFRP',
      result: pass ? 'ALLOW' : 'BLOCK',
      mu: metrics.mu,
      ch: metrics.ch,
      hr: metrics.hr,
      chain: chainStr,
      timestamp: new Date().toISOString(),
    };
    const newLog = appendAuditEntry(entry);
    setAuditLog(newLog);
    setTeamPulse(activateTeamMember(teamPulse, 'PFRP', pass ? `Simulation passed (HR=${hr.toFixed(6)})` : 'Blocked — threshold not met'));
    setTimeout(() => setTeamPulse(deactivateAll(teamPulse)), 3000);
  }

  // ── Execute ─────────────────────────────────────────────
  function handleExecute() {
    const muVals = [0.9999, 0.9998, 0.9997, 0.9996];
    const mu = calcCoherence(muVals);
    const ch = calcCH([1.0]);
    const hr = calcHR(mu, ch);
    const pass = checkThreshold(hr);
    if (!pass) {
      setSimOutput(`μ=${mu.toFixed(6)} | CH=${ch.toFixed(6)} | HR=${hr.toFixed(6)} | ❌ FAIL — BLOCK (HR below threshold)`);
      return;
    }
    const metrics = mkMetrics(mu, ch, hr);
    const seal = makeSeal({ ...active, mu: metrics.mu, ch: metrics.ch, hr: metrics.hr });
    const entry = mkAuditEntry({ ...active, mu: metrics.mu, ch: metrics.ch, hr: metrics.hr }, metrics, 'Kimi', 'SEALED');
    const newLog = appendAuditEntry(entry);
    setAuditLog(newLog);
    setSimOutput(`μ=${metrics.mu} | CH=${metrics.ch} | HR=${metrics.hr} | 🔒 SEALS CREATED`);
    const ns = updateSCB(scbs, active.id, 'status', 'sealed');
    saveSCBs(ns);
    setScbs(ns);
    setTeamPulse(activateTeamMember(teamPulse, 'Kimi', `Sealed: ${seal.slice(0, 30)}...`));
    setTimeout(() => setTeamPulse(deactivateAll(teamPulse)), 4000);
  }

  // ── Render ──────────────────────────────────────────────
  return (
    <div style={{ fontFamily: 'Georgia, serif', minHeight: '100vh', background: '#0a0a0f', color: '#e8e6e3', padding: '0 0 80px' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 16px' }}>

        {/* Header */}
        <div className="uatos-header">
          <div className="eyebrow">HARMONY LABS — SOVEREIGN TECHNOLOGY</div>
          <h1>⚙️ UATOS</h1>
          <div className="meta">Universal AI Team Operating System — The Architect: Kyle S. Whitlock | v1.0 | Sealed 2026-05-01</div>
        </div>

        {/* Conflict Alerts */}
        {conflictAlerts.length > 0 && (
          <div className="conflict-alert">
            {conflictAlerts.map((a, i) => <div key={i}>⚠️ {a.msg}</div>)}
          </div>
        )}

        {/* Tab Nav */}
        <div className="tab-nav">
          {TABS.map(t => (
            <button key={t.id} className={`tab-btn ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </div>

        {/* FORGE TAB */}
        {tab === 'forge' && (
          <div className="forge-grid">

            {/* SCB List */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h3>SCB PIPELINE</h3>
                <button className="btn-add" onClick={handleAddSCB}>+ SCB</button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {scbs.map(s => <SCBItem key={s.id} scb={s} active={activeId === s.id} onClick={() => setActiveId(s.id)} />)}
              </div>
            </div>

            {/* SCB Editor */}
            <SCBEditor scb={active} onUpdate={handleUpdateSCB} />

            {/* Pipeline Chain */}
            <div className="card full">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h3>PIPELINE CHAIN</h3>
                <button className="btn-add" onClick={() => setChain([...chain, makeChainLink()])}>+ Link</button>
              </div>
              <div>
                {chain.map((link, i) => (
                  <ChainLinkRow key={i} link={link} scbs={scbs} onUpdate={handleChainUpdate} />
                ))}
                {chain.length === 0 && (
                  <div style={{ fontSize: 12, color: '#6b7280', padding: '8px 0' }}>No links yet. Add a chain link to build your pipeline.</div>
                )}
              </div>
            </div>

            {/* Simulation Output */}
            <div className="card">
              <h3>SIMULATION OUTPUT</h3>
              <SimOutput simOutput={simOutput} />
            </div>

            {/* Operators */}
            <div className="card">
              <h3>OPERATORS</h3>
              <div className="operator-grid">
                {[
                  { sym: '→', name: 'SEQUENCE', desc: 'Chain SCBs in order' },
                  { sym: '∥', name: 'PARALLEL', desc: 'Run SCBs concurrently' },
                  { sym: '?P:', name: 'GUARD', desc: 'Run if condition P true' },
                  { sym: '↻n:', name: 'REPEAT', desc: 'Loop n times' },
                  { sym: '⊢cond', name: 'BRANCH', desc: 'Fork on condition' },
                ].map(op => (
                  <div key={op.sym} className="operator-item">
                    <span className="operator-sym">{op.sym}</span>
                    <span className="operator-name">{op.name}</span>
                    <div className="operator-desc">{op.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Execute Buttons */}
            <div className="center">
              <button className="btn-primary" onClick={handleSimulate} style={{ marginRight: 12 }}>▶ Simulate Pipeline</button>
              <button className="btn-success" onClick={handleExecute}>⚡ Execute + Seal</button>
            </div>
          </div>
        )}

        {/* TEAM TAB */}
        {tab === 'team' && (
          <div>
            <div className="team-grid">
              {teamPulse.map(t => (
                <div key={t.role} className={`team-card ${t.active ? 'active' : ''}`} style={t.active ? { borderColor: t.color + '55' } : {}}>
                  <div className="team-dot-row">
                    <div className="team-dot" style={{ background: t.active ? t.color : '#374151', boxShadow: t.active ? `0 0 8px ${t.color}` : 'none' }} />
                    <span className="team-role">{t.role}</span>
                  </div>
                  <div className="team-identity" style={{ color: t.color }}>{t.identity}</div>
                  <div className="team-fn">{t.function}</div>
                  {t.active && <div className="team-task">⚡ {t.task}</div>}
                </div>
              ))}
            </div>
            <div className="card">
              <h3>SEPARATION OF POWERS</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                {SEPARATION_OF_POWERS.map(p => (
                  <div key={p.role} style={{ background: 'rgba(0,0,0,0.2)', padding: '8px 12px', borderRadius: 6 }}>
                    <div style={{ fontSize: 11, color: '#60a5fa', fontFamily: 'monospace' }}>{p.role}</div>
                    <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>{p.fn}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* AUDIT TAB */}
        {tab === 'audit' && (
          <div>
            <div className="metrics-grid">
              <MiniBar value={muLog.length ? muLog[muLog.length - 1] : 0} color="#60a5fa" label="μ Coherence" />
              <MiniBar value={chLog.length ? chLog[chLog.length - 1] : 0} color="#34d399" label="CH_norm" />
              <div className="metric-card">
                <div className="metric-label">THRESHOLD</div>
                <div className="metric-value" style={{ color: '#a78bfa' }}>0.9995</div>
                <div className="metric-threshold">Constitutional minimum</div>
              </div>
            </div>
            <div className="card">
              <h3>SEALED EXECUTION LOG</h3>
              <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                {auditLog.length === 0 && (
                  <div style={{ fontSize: 12, color: '#6b7280', padding: '16px 0' }}>No entries yet. Run a simulation to start the audit trail.</div>
                )}
                {auditLog.slice().map((entry, i) => <AuditEntry key={i} entry={entry} />)}
              </div>
            </div>
          </div>
        )}

      </div>

      {/* Footer */}
      <div className="footer">
        UATOS — Harmony Labs | Built on <a href="https://zo-computer.cello.so/z1sqilOByck" target="_blank" rel="noopener noreferrer">Zo</a>
      </div>
    </div>
  );
}