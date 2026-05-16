/**
 * scb-manager.js — SCB CRUD + state machine
 * UATOS — Universal AI Team Operating System
 */

export const RISK_LEVELS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
export const RISK_COLORS = { LOW: '#22c55e', MEDIUM: '#eab308', HIGH: '#f97316', CRITICAL: '#ef4444' };

export function makeSCB(id, intent, opts = {}) {
  return {
    id: id || `scb-${Date.now()}`,
    intent: intent || '',
    constraints: opts.constraints || [],
    inputs: opts.inputs || [],
    outputs: opts.outputs || [],
    risk: opts.risk || 'LOW',
    tests: opts.tests || [],
    deps: opts.deps || [],
    status: 'pending',
    mu: null,
    ch: null,
    hr: null,
    createdAt: new Date().toISOString(),
    ...opts,
  };
}

export function validateSCB(scb) {
  const errors = [];
  if (!scb.id) errors.push('SCB must have an ID');
  if (!scb.intent) errors.push('SCB must have an intent');
  if (!RISK_LEVELS.includes(scb.risk)) errors.push('Invalid risk level');
  return errors;
}

export function serializeSCB(scb) {
  return btoa(JSON.stringify(scb));
}

export function deserializeSCB(data) {
  try {
    return JSON.parse(atob(data));
  } catch {
    return null;
  }
}

export function listSCBs() {
  const stored = localStorage.getItem('uatos_scbs');
  return stored ? JSON.parse(stored) : [];
}

export function saveSCBs(scbs) {
  localStorage.setItem('uatos_scbs', JSON.stringify(scbs));
}

export function addSCB(scbs, intent) {
  const id = `scb-${String(scbs.length + 1).padStart(3, '0')}`;
  const newSCB = makeSCB(id, intent);
  return [...scbs, newSCB];
}

export function updateSCB(scbs, id, field, value) {
  return scbs.map(s => s.id === id ? { ...s, [field]: value } : s);
}

export function removeSCB(scbs, id) {
  return scbs.filter(s => s.id !== id);
}

export function findSCB(scbs, id) {
  return scbs.find(s => s.id === id);
}