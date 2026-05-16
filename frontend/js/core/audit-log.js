/**
 * audit-log.js — Sealed execution log management
 * UATOS — Universal AI Team Operating System
 */

import { checkThreshold } from './coherence-calc.js';

export function makeSeal(scb, ts = new Date()) {
  const data = JSON.stringify({ scb, ts: ts.toISOString() });
  let hash = 0;
  for (let i = 0; i < data.length; i++) {
    hash = ((hash << 5) - hash) + data.charCodeAt(i);
    hash = hash & hash;
  }
  const hex = Math.abs(hash).toString(16).padStart(8, '0');
  return `SR-AIB_HR-${scb.id.toUpperCase()}_SHA3-${hex}@${ts.toISOString()}`;
}

export function mkAuditEntry(scb, metrics, role, result) {
  return {
    seal: makeSeal(scb),
    event: result === 'SEALED' ? `Sealed: ${scb.intent}` : `Simulated: ${scb.intent}`,
    role,
    result,
    mu: metrics.mu,
    ch: metrics.ch,
    hr: metrics.hr,
    timestamp: new Date().toISOString(),
    blocked: result === 'BLOCK',
  };
}

export function listAuditLog() {
  try {
    return JSON.parse(localStorage.getItem('uatos_audit') || '[]');
  } catch { return []; }
}

export function appendAuditEntry(entry) {
  const log = listAuditLog();
  log.unshift(entry);
  localStorage.setItem('uatos_audit', JSON.stringify(log));
  return log;
}

export function getAuditStats(log) {
  const total = log.length;
  const sealed = log.filter(e => e.result === 'SEALED').length;
  const blocked = log.filter(e => e.result === 'BLOCK').length;
  const allow = log.filter(e => e.result === 'ALLOW').length;
  const avgMu = log.filter(e => e.mu).reduce((s, e, _, a) => s + parseFloat(e.mu) / a.length, 0);
  return { total, sealed, blocked, allow, avgMu };
}

export function formatSeal(seal) {
  const [prefix, ts] = seal.split('@');
  return { prefix, timestamp: ts || '', short: prefix.slice(0, 50) };
}

export function exportLog(log, format = 'json') {
  if (format === 'json') return JSON.stringify(log, null, 2);
  if (format === 'csv') {
    const headers = 'seal,event,role,result,mu,ch,hr,timestamp\n';
    const rows = log.map(e => `"${e.seal}","${e.event}","${e.role}","${e.result}","${e.mu || ''}","${e.ch || ''}","${e.hr || ''}","${e.timestamp}"`).join('\n');
    return headers + rows;
  }
  return '';
}