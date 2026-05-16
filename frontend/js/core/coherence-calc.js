/**
 * coherence-calc.js — μ, CH, HR calculations + threshold gate
 * UATOS — Universal AI Team Operating System
 */

export const CONSTITUTIONAL_THRESHOLD = 0.9995;

export function calcCoherence(vals) {
  if (!vals || !vals.length) return 0;
  const logVals = vals.map(v => Math.log(Math.max(v, 1e-10)));
  return Math.exp(logVals.reduce((s, v) => s + v, 0) / vals.length);
}

export function calcCH(vals) {
  if (!vals || !vals.length) return 0;
  return Math.pow(vals.reduce((a, v) => a * v, 1), 1 / vals.length);
}

export function calcHR(mu, ch) {
  return mu * ch;
}

export function checkThreshold(hr) {
  return hr >= CONSTITUTIONAL_THRESHOLD;
}

export function calcMuFromSamples(samples) {
  if (!samples || !samples.length) return 0;
  return calcCoherence(samples);
}

export function calcCHNorm(samples) {
  if (!samples || !samples.length) return 0;
  return calcCH(samples);
}

export function runGate(constraints) {
  return constraints.every(c => c.satisfied !== false);
}

export function mkMetrics(mu, ch, hr) {
  return {
    mu: parseFloat(mu.toFixed(6)),
    ch: parseFloat(ch.toFixed(6)),
    hr: parseFloat(hr.toFixed(6)),
    timestamp: new Date().toISOString(),
    pass: checkThreshold(hr),
  };
}

export function updateMetrics(muLog, chLog, newMu, newCH) {
  return {
    muLog: [...(muLog || []).slice(-9), newMu],
    chLog: [...(chLog || []).slice(-9), newCH],
  };
}

export function getDefaultMuLog() {
  return [0.9998, 0.9997, 0.9999];
}

export function getDefaultCHLog() {
  return [1.0, 1.0, 1.0];
}