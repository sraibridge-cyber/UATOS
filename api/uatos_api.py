#!/usr/bin/env python3
"""
uatos_api.py — UATOS v2 Production REST API
Sovereign · Serverless · Cloudless · Vendorless
Runs as a Zo user service on port 3092
"""

from __future__ import annotations
import os, sys, json
from datetime import datetime, timezone

# Add runtime to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'runtime'))

from scb_registry import (
    SCB, SCBRegistry, SCBValidator,
    EventStore, SCBGraph, ExecutionEngine,
    MU_THRESHOLD
)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

REGISTRY_DIR = os.environ.get('UATOS_REGISTRY_DIR', os.path.join(os.path.dirname(__file__), '..', 'scb_registry'))
DATA_DIR = os.environ.get('UATOS_DATA_DIR', os.path.join(os.path.dirname(__file__), '..', 'data'))

os.makedirs(DATA_DIR, exist_ok=True)

registry = SCBRegistry(REGISTRY_DIR)
event_store = EventStore(REGISTRY_DIR)
engine = ExecutionEngine(registry, event_store)

def api_response(data, status=200):
    return jsonify(data), status

def error_response(msg, status=400):
    return jsonify({"error": msg, "timestamp": datetime.now(timezone.utc).isoformat()}), status

# ─── SCB CRUD ───────────────────────────────────────────────
@app.route('/api/scbs', methods=['GET'])
def list_scbs():
    scbs = registry.list_all()
    return api_response({
        "scbs": [s.to_dict() for s in scbs],
        "count": len(scbs)
    })

@app.route('/api/scb', methods=['POST'])
def create_scb():
    data = request.get_json() or {}
    try:
        required = ['scb_id', 'version', 'intent', 'constraints', 'inputs',
                    'outputs', 'dependencies', 'rules', 'safety_gates', 'tests',
                    'implementation_notes']
        for field in required:
            if field not in data:
                return error_response(f"Missing required field: {field}")

        scb = SCB(**data)
        scb_hash = registry.put(scb)

        event_store.append("SCB_CREATED", {
            "scb_id": scb.scb_id,
            "hash": scb_hash,
            "version": scb.version
        })

        return api_response({
            "scb": scb.to_dict(),
            "hash": scb_hash,
            "timestamp": scb.created_at
        }, 201)
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(f"Internal error: {e}", 500)

@app.route('/api/scb/<scb_id>', methods=['GET'])
def get_scb(scb_id):
    scb = registry.get(scb_id)
    if not scb:
        return error_response(f"SCB not found: {scb_id}", 404)
    return api_response({"scb": scb.to_dict()})

@app.route('/api/scb/<scb_id>', methods=['PUT'])
def update_scb(scb_id):
    return error_response("SCBs are immutable — cannot update, only version", 400)

@app.route('/api/scb/<scb_id>', methods=['DELETE'])
def delete_scb(scb_id):
    return error_response("SCBs are append-only — no deletion permitted", 400)

@app.route('/api/scb/<scb_id>/exists', methods=['GET'])
def check_scb(scb_id):
    return api_response({"scb_id": scb_id, "exists": registry.has(scb_id)})

# ─── Simulation & Execution ────────────────────────────────
@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.get_json() or {}
    chain = data.get('chain', [])

    result = engine.simulate(chain)

    event_store.append("SIMULATION_RUN", {
        "chain_length": len(chain),
        "result": result
    })

    return api_response({
        "mu": result["mu"],
        "ch": result["ch"],
        "hr": result["hr"],
        "threshold": MU_THRESHOLD,
        "pass": result["result"] == "ALLOW",
        "chain_length": len(chain)
    })

@app.route('/api/execute/<scb_id>', methods=['POST'])
def execute_scb(scb_id):
    scb = registry.get(scb_id)
    if not scb:
        return error_response(f"SCB not found: {scb_id}", 404)

    input_data = request.get_json() or {}

    result = engine.execute(scb, input_data)

    return api_response({
        "result": result.to_dict(),
        "threshold": MU_THRESHOLD
    })

@app.route('/api/execute/chain', methods=['POST'])
def execute_chain():
    """Execute a chain of SCBs in topological order."""
    data = request.get_json() or {}
    scb_ids = data.get('scb_ids', [])

    graph = SCBGraph()
    for sid in scb_ids:
        scb = registry.get(sid)
        if not scb:
            return error_response(f"SCB not found: {sid}", 404)
        try:
            graph.add(scb)
        except ValueError as e:
            return error_response(str(e))

    try:
        graph.validate_acyclic()
    except ValueError as e:
        return error_response(f"Graph invalid: {e}")

    ordered = graph.topological_order()
    results = []

    for scb in ordered:
        result = engine.execute(scb)
        results.append(result.to_dict())
        if result.status == "LOCK":
            event_store.append("CHAIN_HALTED", {"last_scb": scb.scb_id, "status": "LOCK"})
            break

    event_store.append("CHAIN_EXECUTED", {"chain": scb_ids, "results_count": len(results)})

    return api_response({
        "executed": len(results),
        "total": len(scb_ids),
        "results": results
    })

# ─── Audit & Events ────────────────────────────────────────
@app.route('/api/audit', methods=['GET'])
def get_audit():
    after_seq = int(request.args.get('after', 0))
    events = event_store.get_events(after_seq)
    return api_response({
        "events": events,
        "count": len(events),
        "latest_seq": events[-1]['seq'] if events else after_seq
    })

@app.route('/api/audit/replay', methods=['GET'])
def replay_events():
    from_seq = int(request.args.get('from', 0))
    events = event_store.replay(from_seq)
    return api_response({
        "events": events,
        "count": len(events),
        "replayed_from": from_seq
    })

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """System metrics — how many SCBs, events, seal status."""
    scbs = registry.list_all()
    events = event_store.get_events()
    audit = engine.audit_log

    mu_vals = [r.mu for r in audit if hasattr(r, 'mu')]
    ch_vals = [sum(r.ch)/len(r.ch) if r.ch else 1.0 for r in audit if hasattr(r, 'ch')]

    return api_response({
        "scb_count": len(scbs),
        "event_count": len(events),
        "execution_count": len(audit),
        "average_mu": round(sum(mu_vals)/len(mu_vals), 6) if mu_vals else 0,
        "average_hr": round(sum(mu_vals)/len(mu_vals), 6) if mu_vals else 0,
        "sealed_count": len([r for r in audit if r.status == "MOVE"]),
        "blocked_count": len([r for r in audit if r.status == "LOCK"]),
        "coherence_threshold": MU_THRESHOLD,
        "system": "UATOS v2.0 — Sovereign · Serverless · Cloudless · Vendorless"
    })

@app.route('/api/health', methods=['GET'])
def health():
    return api_response({
        "status": "OPERATIONAL",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modules": ["SCBRegistry", "EventStore", "ExecutionEngine", "DAGEngine"]
    })

@app.route('/')
def index():
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'frontend'), 'index.html')

@app.route('/api/docs', methods=['GET'])
def docs():
    return jsonify({
        "name": "UATOS v2 API",
        "version": "2.0.0",
        "description": "Sovereign AI Team Operating System — Production API",
        "base_url": "/api",
        "endpoints": [
            {"method": "GET", "path": "/api/scbs", "description": "List all SCBs"},
            {"method": "POST", "path": "/api/scb", "description": "Create new SCB"},
            {"method": "GET", "path": "/api/scb/:id", "description": "Get SCB by ID"},
            {"method": "GET", "path": "/api/scb/:id/exists", "description": "Check SCB exists"},
            {"method": "POST", "path": "/api/simulate", "description": "Simulate pipeline chain"},
            {"method": "POST", "path": "/api/execute/:id", "description": "Execute single SCB"},
            {"method": "POST", "path": "/api/execute/chain", "description": "Execute SCB chain"},
            {"method": "GET", "path": "/api/audit", "description": "Get event log"},
            {"method": "GET", "path": "/api/audit/replay", "description": "Replay events from seq"},
            {"method": "GET", "path": "/api/metrics", "description": "System metrics"},
            {"method": "GET", "path": "/api/health", "description": "Health check"}
        ],
        "philosophy": "Sovereign · Serverless · Cloudless · Vendorless · Module-like"
    })

if __name__ == '__main__':
    port = int(os.environ.get('UATOS_PORT', 3092))
    app.run(host='0.0.0.0', port=port, debug=False)