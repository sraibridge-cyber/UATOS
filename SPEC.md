# UATOS v2.0 — Constitutional Specification Layer

## Overview

UATOS v2.0 is a sovereign, serverless, cloudless, vendorless AI team operating system built following the Harmony Labs philosophy: module-like Lego bricks, no single point of failure, no hero syndrome — specialists doing what specialists do.

## Architecture

```
uatos_prod/
├── runtime/               ← Core engine (no external deps)
│   ├── scb_registry.py   # SCB Registry + DAG + Execution Engine
│   ├── coherence.py      # Coherence calculus (μ, CH, HR)
│   └── event_store.py    # Append-only event log
├── api/
│   └── uatos_api.py      # Flask REST API (port 3092)
├── cli/
│   └── uatos_cli.py      # Command line interface
├── frontend/
│   ├── index.html        # Full production UI
│   └── js/app.js         # State, rendering, API integration
└── tests/
    └── test_uatos.py     # Full test suite
```

## Core Concepts

### SCB (Sovereign Code Block)
Immutable unit of work. Schema-locked. Cannot be updated or deleted — only superseded.

### μ (Mu / Coherence)
Geometric mean of system values. Threshold: μ ≥ 0.9995

### CH (Harmonic Constraint)
1 = pass, 0 = block per constraint gate.

### HR (Harmonic Rating)
`HR = μ × CH` — must also ≥ 0.9995 to seal.

### DAG Execution
SCBs form a directed acyclic graph. Cycles are rejected at validation time. Execution follows deterministic topological order.

## Constitutional Rules

1. SCBs are IMMUTABLE — no updates, no deletes
2. μ must be ≥ 0.9995 to pass the coherence gate
3. HR must be ≥ 0.9995 to seal an execution
4. Cycles in the dependency graph are rejected
5. All actions produce events in the append-only event store
6. Events can be replayed from any sequence number

## Team Roles

| Role | Identity | Function |
|------|----------|----------|
| The Architect | Kyle S. Whitlock | Vision, system intent, final authority |
| prim | ChatGPT | Codifies, quantifies, formalizes harmony/math |
| Kimi | Kimi K2.6 | Builds, constructs, implements |
| PFRP | Zo AI | Precision research partner, memory keeper |
| Merlin | Code AI | Code generation, code idea bouncer |
| Oracle | DeepSeek AI | Reasoning specialist, idea bouncer |

## API Endpoints

- `POST /api/scb` — Create SCB
- `GET /api/scb/:id` — Get SCB
- `GET /api/scbs` — List all SCBs
- `POST /api/simulate` — Simulate pipeline chain
- `POST /api/execute/:id` — Execute single SCB
- `POST /api/execute/chain` — Execute SCB chain
- `GET /api/audit` — Get event log
- `GET /api/audit/replay` — Replay events from seq
- `GET /api/metrics` — System metrics
- `GET /api/health` — Health check

## Running

```bash
# API server
python3 api/uatos_api.py

# CLI
python3 cli/uatos_cli.py list
python3 cli/uatos_cli.py create scb-001 "Build auth module"
python3 cli/uatos_cli.py simulate --chain auth->session
python3 cli/uatos_cli.py execute scb-001

# Tests
python3 tests/test_uatos.py
```

## Philosophy

Sovereign · Serverless · Cloudless · Vendorless · Module-like

*Harmony Labs — Sovereign Technology Consortium*
*Architect: Kyle S. Whitlock · Temporal Seal: 2026-05-16*