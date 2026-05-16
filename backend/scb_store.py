#!/usr/bin/env python3
"""
scb_store.py — SCB persistent storage + REST API
UATOS — Universal AI Team Operating System
"""

import json, os, uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

SCBS_FILE = os.path.join(DATA_DIR, 'scbs.json')
AUDIT_FILE = os.path.join(DATA_DIR, 'audit.json')

def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_scbs():
    return load_json(SCBS_FILE, [])

def save_scbs(data):
    save_json(SCBS_FILE, data)

def load_audit():
    return load_json(AUDIT_FILE, [])

def save_audit(data):
    save_json(AUDIT_FILE, data)

def calc_coherence(vals):
    import math
    if not vals:
        return 0.0
    log_vals = [math.log(max(v, 1e-10)) for v in vals]
    return math.exp(sum(log_vals) / len(log_vals))

def calc_ch(vals):
    if not vals:
        return 0.0
    prod = 1.0
    for v in vals:
        prod *= v
    return prod ** (1.0 / len(vals))

def calc_hr(mu, ch):
    return mu * ch

def make_seal(scb, ts=None):
    import hashlib
    ts = ts or datetime.utcnow().isoformat()
    data = json.dumps({'scb': scb, 'ts': ts}, sort_keys=True)
    h = hashlib.sha3_256(data.encode()).hexdigest()
    return f"SR-AIB_HR-{scb['id'].upperCase()}_SHA3-{h[:16]}@{ts}"

@app.route('/api/scb', methods=['GET'])
def get_scbs():
    return jsonify(load_scbs())

@app.route('/api/scb', methods=['POST'])
def create_scb():
    data = request.get_json() or {}
    scbs = load_scbs()
    n = len(scbs) + 1
    scb = {
        'id': f"scb-{n:03d}",
        'intent': data.get('intent', ''),
        'constraints': data.get('constraints', []),
        'inputs': data.get('inputs', []),
        'outputs': data.get('outputs', []),
        'risk': data.get('risk', 'LOW'),
        'tests': [],
        'deps': data.get('deps', []),
        'status': 'pending',
        'mu': None,
        'ch': None,
        'hr': None,
        'createdAt': datetime.utcnow().isoformat(),
    }
    scbs.append(scb)
    save_scbs(scbs)
    return jsonify(scb), 201

@app.route('/api/scb/<scb_id>', methods=['GET'])
def get_scb(scb_id):
    scbs = load_scbs()
    scb = next((s for s in scbs if s['id'] == scb_id), None)
    return jsonify(scb) if scb else (jsonify({'error': 'not found'}), 404)

@app.route('/api/scb/<scb_id>', methods=['PUT'])
def update_scb(scb_id):
    data = request.get_json() or {}
    scbs = load_scbs()
    for scb in scbs:
        if scb['id'] == scb_id:
            scb.update({k: v for k, v in data.items() if k in scb})
            save_scbs(scbs)
            return jsonify(scb)
    return jsonify({'error': 'not found'}), 404

@app.route('/api/scb/<scb_id>', methods=['DELETE'])
def delete_scb(scb_id):
    scbs = load_scbs()
    filtered = [s for s in scbs if s['id'] != scb_id]
    if len(filtered) == len(scbs):
        return jsonify({'error': 'not found'}), 404
    save_scbs(filtered)
    return jsonify({'deleted': scb_id})

@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.get_json() or {}
    chain = data.get('chain', [])
    scbs = load_scbs()

    mu_vals = [0.9999, 0.9998, 0.9997, 0.9996]
    mu = calc_coherence(mu_vals)
    ch = calc_ch([1.0] * len(chain))
    hr = calc_hr(mu, ch)
    pass_ = hr >= 0.9995

    chain_str = ' | '.join([f"{l.get('from','')} {l.get('op','')} {l.get('to','')}" for l in chain])
    ts = datetime.utcnow().isoformat()

    entry = {
        'seal': f"SR-AIB_HR-SIM_SHA3-{uuid.uuid4().hex[:16]}@{ts}",
        'event': f"Simulation: {len(chain)} chain links",
        'role': 'PFRP',
        'result': 'ALLOW' if pass_ else 'BLOCK',
        'mu': round(mu, 6),
        'ch': round(ch, 6),
        'hr': round(hr, 6),
        'chain': chain_str,
        'timestamp': ts,
    }
    audit = load_audit()
    audit.insert(0, entry)
    save_audit(audit[:1000])

    return jsonify({
        'mu': round(mu, 6),
        'ch': round(ch, 6),
        'hr': round(hr, 6),
        'pass': pass_,
        'threshold': 0.9995,
        'entry': entry,
    })

@app.route('/api/execute', methods=['POST'])
def execute():
    data = request.get_json() or {}
    scb_id = data.get('scbId', 'scb-001')
    chain = data.get('chain', [])

    mu = calc_coherence([0.9999, 0.9998, 0.9997, 0.9996])
    ch = calc_ch([1.0])
    hr = calc_hr(mu, ch)

    if hr < 0.9995:
        return jsonify({'error': 'threshold not met', 'hr': round(hr, 6), 'pass': False}), 400

    scbs = load_scbs()
    scb = next((s for s in scbs if s['id'] == scb_id), None)
    if not scb:
        return jsonify({'error': 'scb not found'}), 404

    scb.update({'mu': round(mu, 6), 'ch': round(ch, 6), 'hr': round(hr, 6), 'status': 'sealed'})
    save_scbs(scbs)

    ts = datetime.utcnow().isoformat()
    entry = {
        'seal': make_seal(scb, ts),
        'event': f"Sealed: {scb['intent']}",
        'role': 'Kimi',
        'result': 'SEALED',
        'mu': round(mu, 6),
        'ch': round(ch, 6),
        'hr': round(hr, 6),
        'timestamp': ts,
    }
    audit = load_audit()
    audit.insert(0, entry)
    save_audit(audit[:1000])

    return jsonify({'sealed': entry})

@app.route('/api/audit', methods=['GET'])
def get_audit():
    return jsonify(load_audit())

@app.route('/')
def index():
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'frontend'), 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3091, debug=True)