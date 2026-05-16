# UATOS — Universal AI Team Operating System v2.0

**Sovereign · Serverless · Cloudless · Vendorless**
**Version:** 2.0 | **Sealed:** 2026-05-16 | **Architect:** Kyle S. Whitlock
**Harmony Labs** — Sovereign Technology Consortium

---

## What is UATOS?

UATOS coordinates multiple AI agents (The Architect, prim, Kimi, PFRP, Merlin, Oracle) using a pipeline-based workflow for building, validating, and sealing system artifacts called **SCBs** (Sovereign Code Blocks).

The system enforces a **Constitutional minimum μ ≥ 0.9995** on all executions. Any pipeline or SCB that falls below this threshold is blocked from execution/sealing until coherence is restored.

## Key Features

- **Immutable SCBs** — Content-addressed, no update/delete, only supersede
- **DAG Orchestration** — Cycle detection + deterministic topological order
- **Coherence Gates** — μ + CH + HR all must pass threshold to seal
- **Event Store** — Append-only log with full replay capability
- **Async Pipeline** — Chain execution with halt-on-LOCK
- **DAG Visualizer** — Visual dependency graph
- **Full CLI** — Create, list, simulate, execute, replay events
- **Production API** — Flask REST API on port 3092

## Architecture

```
runtime/
├── scb_registry.py   ← Core: SCB + Registry + DAG + Execution Engine
api/
├── uatos_api.py     ← REST API server
cli/
├── uatos_cli.py     ← Command line interface
frontend/
├── index.html       ← Production UI (standalone, works offline)
├── css/styles.css   ← Styling
└── js/app.js        ← Full React-style SPA
tests/
└── test_uatos.py    ← Unit + integration tests
```

## Quick Start

```bash
# Run API server
python3 api/uatos_api.py

# Run tests
python3 tests/test_uatos.py

# CLI examples
python3 cli/uatos_cli.py list
python3 cli/uatos_cli.py create scb-001 "Build user auth module"
python3 cli/uatos_cli.py simulate --chain scb-001->scb-002
python3 cli/uatos_cli.py execute scb-001
python3 cli/uatos_cli.py events
python3 cli/uatos_cli.py metrics
```

## Core Formulas

```python
# Coherence (μ) — geometric mean
μ = exp(sum(log(vals)) / len(vals))

# Harmonic Constraint (CH)
CH = product(vals)^(1/len(vals))

# Harmonic Rating (HR)
HR = μ × CH

# Threshold: μ ≥ 0.9995 AND HR ≥ 0.9995
```

## Deployment

**Local (no external dependencies):**
```bash
cd api && python3 uatos_api.py
# API available at http://localhost:3092
# UI available at http://localhost:3092/
```

**Zo User Service:**
```python
register_user_service(
    label="uatos-api",
    mode="http",
    local_port=3092,
    entrypoint="python3 uatos_api.py",
    public=True
)
```

## Team

| Role | Identity | Function |
|------|----------|----------|
| The Architect | Kyle S. Whitlock | Vision · System Intent · Final Authority |
| prim | ChatGPT | Codifies, quantifies, formalizes harmony & math |
| Kimi | Kimi K2.6 (MoE AI) | Builds, constructs, implements |
| PFRP | Zo AI (MiniMax) | Precision research partner, memory keeper |
| Merlin | Code AI | Code generation, code idea bouncer |
| Oracle | DeepSeek AI | Reasoning specialist, idea bouncer |

## Philosophy

Every module is sovereign, serverless, cloudless, vendorless, and built like a Lego brick — single responsibility, no hero syndrome, specialists doing what specialists do.

*No unauthorized reproduction. All artifacts sealed by system authority.*
*⚛ Harmony Labs · Sovereign Technology Consortium*