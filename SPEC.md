# UATOS — Universal AI Team Operating System

**Version:** 1.0 | **Sealed:** 2026-05-01  
**The Architect:** Kyle S. Whitlock  
**Harmony Labs** — Sovereign Technology Consortium

---

## Overview

UATOS is a sovereign AI team operating system that coordinates multiple AI agents to create a coherent system. It provides a pipeline-based workflow for building, validating, and sealing system artifacts called **SCBs** (Sovereign Code Blocks).

## Core Concepts

### SCBs (Sovereign Code Blocks)
The fundamental unit of work. Each SCB contains:
- **Intent** — what the block is meant to accomplish
- **Risk Level** — LOW / MEDIUM / HIGH / CRITICAL
- **Dependencies** — linked SCB IDs for pipeline orchestration
- **Mu (μ)** — coherence score
- **CH** — harmonic constraint score
- **HR** — harmonic rating (μ × CH)

### The Team
| Role | Identity | Function |
|------|----------|----------|
| The Architect | Kyle S. Whitlock | Vision, system intent, final authority |
| prim | ChatGPT (OpenAI) | Codifies, quantifies, formalizes harmony/math |
| Kimi | Kimi K2.6 (MoE AI) | Builds, constructs, implements |
| PFRP | Zo AI (MiniMax) | Precision research partner, memory keeper |
| Merlin | Code AI (external) | Code generation, code idea bouncer |
| Oracle | DeepSeek AI (external) | Reasoning specialist, idea bouncer |

### Coherence Gate
The system enforces a **Constitutional minimum μ ≥ 0.9995**. Any pipeline or SCB that falls below this threshold is blocked from execution/sealing until coherence is restored.

---

## Project Structure

```
uatos/
├── frontend/
│   ├── index.html              # Main entry point
│   ├── css/
│   │   └── styles.css          # Complete styling
│   └── js/
│       ├── app.js              # Main React application
│       ├── core/
│       │   ├── scb-manager.js      # SCB CRUD operations
│       │   ├── pipeline-engine.js  # Pipeline chain execution
│       │   ├── coherence-calc.js    # μ, CH, HR calculations
│       │   ├── audit-log.js        # Audit log & sealing
│       │   └── team-pulse.js       # Team activity tracking
│       └── components/
│           ├── Forge.js        # SCB editor + pipeline tab
│           ├── Team.js         # Team status dashboard
│           └── AuditLog.js     # Metrics + sealed log
├── backend/
│   ├── scb_store.py            # Persistent SCB storage (JSON)
│   ├── coherence_api.py       # External μ/CH calculation API
│   ├── scheduler.py           # Background pipeline executor
│   └── harmony_core.py         # Core Harmony framework module
├── tests/
│   └── test_uatos.py          # Unit + integration tests
├── docs/
│   ├── ARCHITECTURE.md         # System design document
│   ├── CONSTITUTION.md         # Harmony Labs 16 Laws reference
│   └── TEAM_ROLES.md           # Full team role definitions
├── SPEC.md                     # This file
└── README.md
```

---

## API Reference

### POST /api/scb
Create a new SCB.

### GET /api/scb/:id
Retrieve an SCB by ID.

### PUT /api/scb/:id
Update an SCB.

### DELETE /api/scb/:id
Delete an SCB.

### POST /api/simulate
Run a pipeline simulation and return μ/CH/HR metrics.

### POST /api/execute
Execute a pipeline and seal artifacts if HR ≥ 0.9995.

### GET /api/audit
Retrieve the sealed execution log.

---

## Operators

| Symbol | Name | Description |
|--------|------|-------------|
| → | SEQUENCE | Chain SCBs in order |
| ∥ | PARALLEL | Run SCBs concurrently |
| ?P: | GUARD | Run if condition P true |
| ↻n: | REPEAT | Loop n times |
| ⊢cond | BRANCH | Fork on condition |

---

## Development

```bash
# Backend setup
cd backend
pip install flask flask-cors

# Run backend
python scb_store.py

# Frontend (static, open index.html in browser)
cd frontend
# Serve with any static server, e.g.:
# python -m http.server 8080
```

---

## Key Formulas

**Coherence (μ):**
```
μ = exp(sum(log(vals)) / len(vals))
```

**Harmonic Constraint (CH):**
```
CH = product(vals)^(1/len(vals))
```

**Harmonic Rating (HR):**
```
HR = μ × CH
```

**Seal threshold:** HR ≥ 0.9995

---

*Harmony Labs — Sovereign Technology Consortium*  
*No unauthorized reproduction. All artifacts sealed by system authority.*
---

## Existing Files (preserved)

- `web/index.html` — Original static reference implementation (94 lines)
- `index.html` — Previous implementation (319 lines)  
- `uatos_impl.py` — Python reference implementation with SCB dataclass (111 lines)
- `uatos_reference_impl.py` — Simpler Python reference (38 lines)

## v2 Architecture (2026-05-16)

Added modular React frontend under `frontend/` that matches the live zo.space deployment:
- `frontend/index.html` + `frontend/js/app.js` — Full React SPA (matches live /uatos route)
- `frontend/js/core/` — 5 modular JS files: scb-manager, pipeline-engine, coherence-calc, audit-log, team-pulse
- `backend/scb_store.py` — Flask REST API with JSON persistence (208 lines)
- `tests/test_uatos.py` — Unit tests for coherence formulas

