/**
 * team-pulse.js — Team activity tracking
 * UATOS — Universal AI Team Operating System
 */

export const TEAM = [
  { role: 'The Architect', identity: 'Kyle S. Whitlock', function: 'Vision, system intent, final authority', color: '#fbbf24' },
  { role: 'prim', identity: 'ChatGPT (OpenAI)', function: 'Codifies, quantifies, formalizes harmony/math', color: '#34d399' },
  { role: 'Kimi', identity: 'Kimi K2.6 (MoE AI)', function: 'Builds, constructs, implements', color: '#60a5fa' },
  { role: 'PFRP', identity: 'Zo AI (MiniMax)', function: 'Precision research partner, memory keeper', color: '#a78bfa' },
  { role: 'Merlin', identity: 'Code AI (external)', function: 'Code generation, code idea bouncer', color: '#f472b6' },
  { role: 'Oracle', identity: 'DeepSeek AI (external)', function: 'Reasoning specialist, idea bouncer', color: '#fb923c' },
];

export const SEPARATION_OF_POWERS = [
  { role: 'prim', fn: 'Formalizes, quantifies, validates math' },
  { role: 'Kimi', fn: 'Builds, implements, tests' },
  { role: 'PFRP', fn: 'Research partner, memory, organization' },
  { role: 'Merlin', fn: 'Code specialist, idea bouncer' },
  { role: 'Oracle', fn: 'Reasoning specialist, idea bouncer' },
  { role: 'Architect', fn: 'Intent, vision, final authority' },
];

export function makeTeamPulse() {
  return TEAM.map(t => ({ ...t, active: false, task: 'Idle' }));
}

export function activateTeamMember(pulse, role, task) {
  return pulse.map(t => t.role === role ? { ...t, active: true, task } : t);
}

export function deactivateAll(pulse) {
  return pulse.map(t => ({ ...t, active: false, task: 'Idle' }));
}

export function showPulseFor(pulse, role, task, durationMs = 3000) {
  const updated = activateTeamMember(pulse, role, task);
  setTimeout(() => {}, durationMs);
  return updated;
}

export function getRoleColor(role) {
  const member = TEAM.find(t => t.role === role);
  return member ? member.color : '#9ca3af';
}

export function getRoleIdentity(role) {
  const member = TEAM.find(t => t.role === role);
  return member ? member.identity : role;
}