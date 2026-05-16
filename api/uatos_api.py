#!/usr/bin/env python3
"""
UATOS v2.0 — Backend API
Aegis-Dial: SR-AIBRIDGE | The Architect: Kyle S. Whitlock | Constituted: 2026-05-16
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from collections import deque
import math, hashlib, json, datetime

app = Flask(__name__)
CORS(app)

HISTORY_LIMIT = 100
audit_log = deque(maxlen=HISTORY_LIMIT)
events = deque(maxlen=500)
scbs = {}
scb_id_counter = 0
const mu_min = 0.9995

class SCB:
    def __init__(self, scb_id, intent, constraints=None, inputs=None, outputs=None, risk="LOW"):
        self.id = scb_id
        self.intent = intent
        self.constraints = constraints or []
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.risk = risk
        self.tests = []
        self.deps = []
        self.status = "pending"
        self.mu = None; self.ch = None; self.hr = None
        self.seal = None

    def to_dict(self):
        return {"id": self.id, "intent": self.intent, "constraints": self.constraints,
                "inputs": self.inputs, "outputs": self.outputs, "risk": self.risk,
                "status": self.status, "mu": self.mu, "ch": self.ch, "hr": self.hr, "seal": self.seal}

def calc_mu(vals):
    if not vals: return 0
    return math.exp(sum(math.log(max(v, 1e-10)) for v in vals) / len(vals))

def calc_ch(vals):
    return sum(vals) / len(vals) if vals else 0

def calc_hr(mu, ch):
    return mu * ch

def check_cycles(scb_id, deps):
    """True if adding scb_id with deps would create a dependency cycle."""
    visited = set()
    stack = [scb_id]
    while stack:
        cur = stack.pop()
        if cur == scb_id and visited:
            return True
        if cur not in visited:
            visited.add(cur)
            if cur in scbs:
                stack.extend(scbs[cur].deps)
    return False

def seal(scb):
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    data = json.dumps({"scb": scb.to_dict(), "ts": ts}, sort_keys=True).encode()
    h = hashlib.sha3_256(data).hexdigest()[:16]
    return f"SR-AIB_HR-{scb.id.upper()}_SHA3-{h}@{ts}"

def log_event(event_type, detail, role="System", result="OK", metrics=None):
    entry = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "type": event_type,
             "detail": detail, "role": role, "result": result}
    if metrics:
        entry.update(metrics)
    events.append(entry)
    audit_log.append(entry)
    return entry

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "OPERATIONAL", "version": "2.0.0",
                     "modules": ["SCBRegistry", "EventStore", "ExecutionEngine", "DAGEngine"],
                     "timestamp": datetime.datetime.utcnow().isoformat() + "Z"})

@app.route("/api/scb/create", methods=["POST"])
def create_scb():
    global scb_id_counter
    body = request.get_json() or {}
    intent = body.get("intent", f"SCB-{scb_id_counter + 1}")
    deps = body.get("deps", [])
    scb_id = f"scb-{scb_id_counter + 1:03d}"
    scb_id_counter += 1

    scb = SCB(scb_id, intent, risk=body.get("risk", "LOW"))
    scb.deps = deps
    scbs[scb_id] = scb

    log_event("SCB_CREATED", f"Created {scb_id}: {intent}", role="Kimi")
    return jsonify({"id": scb_id, "scb": scb.to_dict()}), 201

@app.route("/api/scb/list", methods=["GET"])
def list_scbs():
    return jsonify({"scbs": [s.to_dict() for s in scbs.values()], "count": len(scbs)})

@app.route("/api/scb/<scb_id>", methods=["GET"])
def get_scb(scb_id):
    scb = scbs.get(scb_id)
    if not scb:
        return jsonify({"error": f"SCB {scb_id} not found"}), 404
    return jsonify(scb.to_dict())

@app.route("/api/scb/simulate", methods=["POST"])
def simulate():
    body = request.get_json() or {}
    scb_id = body.get("scb_id", "scb-001")
    mu_vals = body.get("mu_vals", [0.9999, 0.9998, 0.9997, 0.9996])
    ch_vals = body.get("ch_vals", [1.0, 1.0, 1.0, 1.0])

    mu = calc_mu(mu_vals)
    ch = calc_ch(ch_vals)
    hr = calc_hr(mu, ch)
    passed = hr >= 0.9995

    entry = log_event("SIMULATION", f"Simulating {scb_id}", role="PFRP",
                      result="ALLOW" if passed else "BLOCK",
                      metrics={"mu": round(mu, 6), "ch": round(ch, 6), "hr": round(hr, 6)})

    if scb_id in scbs:
        scbs[scb_id].mu = mu; scbs[scb_id].ch = ch; scbs[scb_id].hr = hr
        scbs[scb_id].status = "simulated"

    return jsonify({"passed": passed, "mu": round(mu, 6), "ch": round(ch, 6),
                     "hr": round(hr, 6), "threshold": mu_min, "event": entry})

@app.route("/api/scb/execute", methods=["POST"])
def execute():
    body = request.get_json() or {}
    scb_id = body.get("scb_id", "scb-001")

    if scb_id not in scbs:
        return jsonify({"error": f"SCB {scb_id} not found"}), 404

    scb = scbs[scb_id]
    mu_vals = body.get("mu_vals", [0.9999, 0.9998, 0.9997])
    ch_vals = body.get("ch_vals", [1.0, 1.0, 1.0])

    mu = calc_mu(mu_vals)
    ch = calc_ch(ch_vals)
    hr = calc_hr(mu, ch)
    passed = hr >= 0.9995

    if not passed:
        entry = log_event("EXECUTION_BLOCKED", f"Blocked: HR={hr:.6f} < {mu_min}", role="PFRP", result="BLOCK")
        return jsonify({"passed": False, "mu": round(mu, 6), "ch": round(ch, 6), "hr": round(hr, 6), "event": entry}), 200

    scb.mu = mu; scb.ch = ch; scb.hr = hr
    scb.status = "executed"
    seal_id = seal(scb)
    scb.seal = seal_id

    entry = log_event("SCB_EXECUTED", f"Sealed {scb_id}", role="Kimi", result="SEALED",
                       metrics={"mu": round(mu, 6), "ch": round(ch, 6), "hr": round(hr, 6), "seal": seal_id})

    return jsonify({"passed": True, "seal": seal_id, "mu": round(mu, 6),
                    "ch": round(ch, 6), "hr": round(hr, 6), "event": entry})

@app.route("/api/events", methods=["GET"])
def get_events():
    limit = int(request.args.get("limit", 50))
    return jsonify({"events": list(events)[-limit:], "count": len(events)})

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    mu_vals = [s.mu for s in scbs.values() if s.mu]
    ch_vals = [s.ch for s in scbs.values() if s.ch]
    hr_vals = [s.hr for s in scbs.values() if s.hr]

    return jsonify({
        "scb_count": len(scbs),
        "event_count": len(events),
        "mu_avg": round(calc_mu(mu_vals), 6) if mu_vals else 0,
        "ch_avg": round(calc_ch(ch_vals), 6) if ch_vals else 0,
        "hr_avg": round(sum(hr_vals) / len(hr_vals), 6) if hr_vals else 0,
        "pass_count": sum(1 for s in scbs.values() if s.status == "executed"),
        "pending_count": sum(1 for s in scbs.values() if s.status == "pending"),
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 3092))
    app.run(host="0.0.0.0", port=port, debug=False)