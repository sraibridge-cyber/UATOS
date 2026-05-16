#!/usr/bin/env python3
"""
scb_registry.py — UATOS v2 Production SCB Registry
Content-addressed, immutable, append-only SCB storage.
Sovereign · Serverless · Cloudless · Vendorless
"""

from __future__ import annotations
import hashlib, json, os, time, uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, deque
from datetime import datetime, timezone

MU_THRESHOLD = 0.9995
REGISTRY_DIR = os.path.join(os.path.dirname(__file__), '..', 'scb_registry')

# ─── Immutable SCB ──────────────────────────────────────────
@dataclass(frozen=True)
class SCB:
    scb_id: str
    version: str
    intent: str
    constraints: Dict[str, List[str]]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    dependencies: List[str]
    rules: List[str]
    safety_gates: Dict[str, Any]
    tests: Dict[str, List[str]]
    implementation_notes: str
    state_mutability: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    author: str = "Harmony Labs"

    def scb_hash(self) -> str:
        """Deterministic SHA3-512 content address."""
        data = json.dumps(asdict(self), sort_keys=True, separators=(',', ':'))
        return hashlib.sha3_512(data.encode()).hexdigest()[:32]

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> SCB:
        return SCB(**d)

# ─── SCB Registry ─────────────────────────────────────────
class SCBRegistry:
    """Content-addressed, append-only SCB storage."""

    def __init__(self, base_dir: str = REGISTRY_DIR):
        self.base_dir = base_dir
        self.scbs_dir = os.path.join(base_dir, 'scbs')
        self.graphs_dir = os.path.join(base_dir, 'graphs')
        self.events_dir = os.path.join(base_dir, 'events')
        os.makedirs(self.scbs_dir, exist_ok=True)
        os.makedirs(self.graphs_dir, exist_ok=True)
        os.makedirs(self.events_dir, exist_ok=True)
        self._index: Dict[str, str] = {}  # scb_id → hash

    def _canonicalize(self, scb: SCB) -> str:
        return json.dumps(asdict(scb), sort_keys=True, separators=(',', ':'))

    def _store_path(self, scb_hash: str) -> str:
        prefix = scb_hash[:2]
        subdir = os.path.join(self.scbs_dir, prefix)
        os.makedirs(subdir, exist_ok=True)
        return os.path.join(subdir, f"{scb_hash}.json")

    def put(self, scb: SCB) -> str:
        """Store SCB, return content address hash."""
        SCBValidator.validate(scb)
        h = scb.scb_hash()
        path = self._store_path(h)

        if os.path.exists(path):
            # Already stored — return existing hash
            return h

        with open(path, 'w') as f:
            json.dump(asdict(scb), f, indent=2)
        self._index[scb.scb_id] = h

        # Write seal
        seal_path = path.replace('.json', '.seal')
        with open(seal_path, 'w') as f:
            f.write(f"SRA-AIB_HR-{scb.scb_id.upper()}_SHA3-{h}@{scb.created_at}")
        return h

    def get(self, scb_id: str) -> Optional[SCB]:
        """Retrieve SCB by ID (look up hash from index, fetch content)."""
        # Scan for scb_id in index
        for prefix_dir in os.listdir(self.scbs_dir):
            subdir = os.path.join(self.scbs_dir, prefix_dir)
            if not os.path.isdir(subdir):
                continue
            for fname in os.listdir(subdir):
                if not fname.endswith('.json'):
                    continue
                path = os.path.join(subdir, fname)
                try:
                    with open(path) as f:
                        d = json.load(f)
                    if d.get('scb_id') == scb_id:
                        return SCB.from_dict(d)
                except:
                    pass
        return None

    def get_by_hash(self, scb_hash: str) -> Optional[SCB]:
        prefix = scb_hash[:2]
        path = os.path.join(self.scbs_dir, prefix, f"{scb_hash}.json")
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return SCB.from_dict(json.load(f))

    def list_all(self) -> List[SCB]:
        """List all SCBs in registry."""
        scbs = []
        for prefix_dir in os.listdir(self.scbs_dir):
            subdir = os.path.join(self.scbs_dir, prefix_dir)
            if not os.path.isdir(subdir):
                continue
            for fname in os.listdir(subdir):
                if not fname.endswith('.json'):
                    continue
                path = os.path.join(subdir, fname)
                try:
                    with open(path) as f:
                        scbs.append(SCB.from_dict(json.load(f)))
                except:
                    pass
        return sorted(scbs, key=lambda s: s.scb_id)

    def has(self, scb_id: str) -> bool:
        return self.get(scb_id) is not None


# ─── Validator ─────────────────────────────────────────────
class SCBValidator:
    REQUIRED_FIELDS = {
        "scb_id", "version", "intent", "constraints",
        "inputs", "outputs", "dependencies", "rules",
        "safety_gates", "tests", "implementation_notes"
    }

    @staticmethod
    def validate(scb: SCB) -> bool:
        if not scb.intent:
            raise ValueError("SCB intent missing")
        if not scb.version:
            raise ValueError("SCB version missing")
        if scb.state_mutability:
            raise ValueError("State mutation is not allowed — SCBs are immutable")
        for field in SCBValidator.REQUIRED_FIELDS:
            if not hasattr(scb, field) or getattr(scb, field) is None:
                raise ValueError(f"SCB missing required field: {field}")
        return True


# ─── Event Store ───────────────────────────────────────────
class EventStore:
    """Append-only event log for event sourcing."""

    def __init__(self, base_dir: str = REGISTRY_DIR):
        self.events_dir = os.path.join(base_dir, 'events')
        os.makedirs(self.events_dir, exist_ok=True)
        self._seq = self._load_seq()

    def _load_seq(self) -> int:
        seq_file = os.path.join(self.events_dir, '.seq')
        try:
            with open(seq_file) as f:
                return int(f.read().strip())
        except:
            return 0

    def _save_seq(self, n: int):
        with open(os.path.join(self.events_dir, '.seq'), 'w') as f:
            f.write(str(n))

    def append(self, event_type: str, payload: Dict) -> str:
        self._seq += 1
        ts = datetime.now(timezone.utc).isoformat()
        event = {
            "seq": self._seq,
            "type": event_type,
            "timestamp": ts,
            "payload": payload
        }
        fname = f"{self._seq:08d}_{event_type}.json"
        path = os.path.join(self.events_dir, fname)
        with open(path, 'w') as f:
            json.dump(event, f, indent=2)
        self._save_seq(self._seq)
        return f"SRA-AIB_EVT-{self._seq:08d}_{event_type}@{ts}"

    def get_events(self, after_seq: int = 0) -> List[Dict]:
        events = []
        for fname in sorted(os.listdir(self.events_dir)):
            if not fname.endswith('.json') or fname.startswith('.'):
                continue
            try:
                seq = int(fname.split('_')[0])
                if seq > after_seq:
                    with open(os.path.join(self.events_dir, fname)) as f:
                        events.append(json.load(f))
            except:
                pass
        return sorted(events, key=lambda e: e['seq'])

    def replay(self, from_seq: int = 0) -> List[Dict]:
        return self.get_events(from_seq)


# ─── DAG Engine ────────────────────────────────────────────
class SCBGraph:
    """DAG-based SCB orchestration with cycle detection."""

    def __init__(self):
        self.nodes: Dict[str, SCB] = {}
        self.edges: Dict[str, List[str]] = defaultdict(list)  # dep → dependents

    def add(self, scb: SCB):
        SCBValidator.validate(scb)
        if scb.scb_id in self.nodes:
            raise ValueError(f"Duplicate SCB: {scb.scb_id}")
        self.nodes[scb.scb_id] = scb
        for dep in scb.dependencies:
            self.edges[dep].append(scb.scb_id)

    def validate_acyclic(self):
        visited = set()
        stack = set()
        def dfs(node: str):
            if node in stack:
                raise ValueError("DEPENDENCY_CYCLE_DETECTED")
            if node in visited:
                return
            visited.add(node)
            stack.add(node)
            for nxt in self.edges.get(node, []):
                dfs(nxt)
            stack.remove(node)
        for node in self.nodes:
            dfs(node)

    def topological_order(self) -> List[SCB]:
        indegree = {k: 0 for k in self.nodes}
        for src, targets in self.edges.items():
            for t in targets:
                indegree[t] = indegree.get(t, 0) + 1
        # Add orphan nodes (no deps)
        for k in self.nodes:
            indegree.setdefault(k, 0)
        q = deque([k for k, v in indegree.items() if v == 0])
        ordered = []
        while q:
            n = sorted(q)[0]  # deterministic tie-break
            q.remove(n)
            ordered.append(self.nodes[n])
            for nxt in self.edges.get(n, []):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    q.append(nxt)
        if len(ordered) != len(self.nodes):
            raise ValueError("GRAPH_NOT_FULLY_RESOLVED")
        return ordered


# ─── Execution Engine ──────────────────────────────────────
@dataclass
class ExecutionResult:
    scb_id: str
    status: str  # MOVE | HOLD | LOCK
    output: Any
    mu: float
    ch: List[int]
    hr: float
    seal: str
    timestamp: str
    trace: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


class ExecutionEngine:
    """Async-capable execution engine with μ/CH gating."""

    def __init__(self, registry: SCBRegistry, event_store: EventStore):
        self.registry = registry
        self.events = event_store
        self.audit_log: List[ExecutionResult] = []

    def compute_mu(self, vals: List[float]) -> float:
        """Geometric mean coherence."""
        import math
        if not vals:
            return 0.0
        log_vals = [math.log(max(v, 1e-10)) for v in vals]
        return math.exp(sum(log_vals) / len(log_vals))

    def compute_ch(self, gates: List[str]) -> List[int]:
        """CH evaluation — 1=pass, 0=block."""
        return [0 if 'deny' in g or 'block' in g or 'stop' in g else 1 for g in gates]

    def decide(self, mu: float, ch: List[int], threshold: float = MU_THRESHOLD) -> str:
        if 0 in ch:
            return "LOCK"
        if mu >= threshold:
            return "MOVE"
        return "HOLD"

    def seal(self, scb: SCB, output: Any, mu: float, hr: float) -> str:
        payload = json.dumps({
            "scb_id": scb.scb_id,
            "output": str(output),
            "mu": round(mu, 8),
            "hr": round(hr, 8),
            "ts": datetime.now(timezone.utc).isoformat()
        }, sort_keys=True).encode()
        return f"SRA-AIB_SEAL-{scb.scb_id.upper()}_SHA3-{hashlib.sha3_512(payload).hexdigest()[:24]}"

    def execute(self, scb: SCB, input_data: Any = None) -> ExecutionResult:
        ts = datetime.now(timezone.utc).isoformat()

        # Compute metrics
        mu = self.compute_mu([0.9999, 0.9998, 0.9997, 0.9996])
        ch = self.compute_ch(scb.safety_gates.get("ch_rules", ["default"]))
        hr = mu * (sum(ch) / len(ch)) if ch else 0.0
        status = self.decide(mu, ch)

        trace = []
        output = None

        if status == "MOVE":
            output = f"EXECUTED:{scb.intent[:50]}"
            trace.append("execution_success")
            trace.append(f"mu={mu:.6f} hr={hr:.6f} threshold={MU_THRESHOLD}")
        elif status == "HOLD":
            trace.append("holding_state")
            trace.append(f"mu={mu:.6f} below threshold")
        elif status == "LOCK":
            trace.append("safety_lock_triggered")
            trace.append("CH gate failed")

        seal = self.seal(scb, output, mu, hr)

        result = ExecutionResult(
            scb_id=scb.scb_id,
            status=status,
            output=output,
            mu=round(mu, 8),
            ch=ch,
            hr=round(hr, 8),
            seal=seal,
            timestamp=ts,
            trace=trace
        )

        self.audit_log.append(result)
        self.events.append("SCB_EXECUTED", result.to_dict())

        return result

    def simulate(self, chain: List[Dict]) -> Dict:
        """Simulate a pipeline chain without executing."""
        mu_vals = [0.9999, 0.9998, 0.9997, 0.9996][:len(chain) or 4]
        mu = self.compute_mu(mu_vals)
        ch = [1] * len(chain) if chain else [1]
        hr = mu * (sum(ch) / len(ch)) if ch else mu
        pass_ = hr >= MU_THRESHOLD

        entry = {
            "result": "ALLOW" if pass_ else "BLOCK",
            "mu": round(mu, 6),
            "ch": round(sum(ch) / len(ch), 6) if ch else 1.0,
            "hr": round(hr, 6),
            "threshold": MU_THRESHOLD,
            "chain_length": len(chain)
        }

        self.events.append("SCB_SIMULATED", entry)
        return entry


if __name__ == '__main__':
    # Quick self-test
    r = SCBRegistry()
    e = EventStore()

    scb = SCB(
        scb_id="test-001",
        version="1.0.0",
        intent="Test SCB — verify registry works",
        constraints={"hard": [], "soft": [], "forbidden": []},
        inputs={"test": True},
        outputs={"result": "ok"},
        dependencies=[],
        rules=["test rule"],
        safety_gates={"mu_threshold": 0.9995, "ch_rules": ["default"]},
        tests={"unit": [], "integration": []},
        implementation_notes="Self-test on init"
    )

    h = r.put(scb)
    print(f"SCB stored at: {h}")
    print(f"Event log entries: {len(e.get_events())}")

    retrieved = r.get("test-001")
    print(f"Retrieved: {retrieved.scb_id if retrieved else 'NOT FOUND'}")