/**
 * pipeline-engine.js — Chain execution + conflict detection
 * UATOS — Universal AI Team Operating System
 */

export const OPERATORS = {
  SEQUENCE: '→',
  PARALLEL: '∥',
  GUARD: '?P:',
  REPEAT: '↻n:',
  BRANCH: '⊢cond',
};

export const OPERATOR_DISPLAY = {
  SEQUENCE: '→',
  PARALLEL: '∥',
  GUARD: '?P:',
  REPEAT: '↻n:',
  BRANCH: '⊢cond',
};

export function makeChainLink(from = '', op = 'SEQUENCE', to = '') {
  return { from, op, to };
}

export function detectCollisions(chain, scbs) {
  const stateWrites = {};
  const alerts = [];
  chain.forEach((link, idx) => {
    if (link.op === 'SEQUENCE' && link.from && link.to) {
      const key = link.to;
      if (stateWrites[key]) {
        alerts.push({
          type: 'state_collision',
          from: stateWrites[key],
          to: link.from,
          via: `scb-${idx}`,
          msg: `State collision on '${key}' between ${stateWrites[key]} and ${link.from}`,
        });
      }
      stateWrites[key] = link.from;
    }
  });
  return alerts;
}

export function resolveDeps(chain, scbs) {
  return chain.map(link => {
    const fromSCB = scbs.find(s => s.id === link.from);
    const toSCB = scbs.find(s => s.id === link.to);
    return {
      ...link,
      fromReady: !link.from || (fromSCB && fromSCB.status !== 'failed'),
      toReady: !link.to || (toSCB && toSCB.status !== 'failed'),
      executable: link.fromReady && link.toReady,
    };
  });
}

export async function executeChain(chain, scbs, coherenceCalc) {
  const resolved = resolveDeps(chain, scbs);
  const results = [];
  for (const link of resolved) {
    if (!link.executable) {
      results.push({ link, status: 'blocked', reason: 'dependency_not_ready' });
      continue;
    }
    switch (link.op) {
      case 'SEQUENCE': {
        const result = await executeSCB(link.from, scbs, coherenceCalc);
        results.push({ link, status: 'ok', result });
        break;
      }
      case 'PARALLEL': {
        const [r1, r2] = await Promise.all([
          executeSCB(link.from, scbs, coherenceCalc),
          executeSCB(link.to, scbs, coherenceCalc),
        ]);
        results.push({ link, status: 'ok', result: [r1, r2] });
        break;
      }
      case 'GUARD': {
        const fromSCB = scbs.find(s => s.id === link.from);
        if (fromSCB && fromSCB.mu >= 0.9995) {
          const result = await executeSCB(link.to, scbs, coherenceCalc);
          results.push({ link, status: 'ok', result, guarded: true });
        } else {
          results.push({ link, status: 'skipped', reason: 'guard_condition_false' });
        }
        break;
      }
      case 'REPEAT': {
        const n = parseInt(link.to || '1', 10);
        for (let i = 0; i < n; i++) {
          const result = await executeSCB(link.from, scbs, coherenceCalc);
          results.push({ link, status: 'ok', iteration: i, result });
        }
        break;
      }
      case 'BRANCH': {
        const fromSCB = scbs.find(s => s.id === link.from);
        const condition = fromSCB && fromSCB.mu >= 0.9995;
        results.push({ link, status: 'ok', branch: condition ? 'true' : 'false' });
        break;
      }
      default:
        results.push({ link, status: 'unknown_op' });
    }
  }
  return results;
}

async function executeSCB(id, scbs, coherenceCalc) {
  const idx = scbs.findIndex(s => s.id === id);
  if (idx === -1) return { error: 'SCB not found' };
  const scb = scbs[idx];
  const mu = Math.random() > 0.05 ? 0.9999 : 0.9994;
  const ch = 1.0;
  return { id, mu, ch, hr: mu * ch, executedAt: new Date().toISOString() };
}

export function formatChain(chain) {
  return chain.map(l => `${l.from} ${OPERATOR_DISPLAY[l.op] || l.op} ${l.to}`).join(' | ');
}