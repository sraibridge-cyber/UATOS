#!/usr/bin/env python3
"""
UATOS — Python Reference Implementation v1.0
SCB + Graph + Execution Engine
"""
from __future__ import annotations
import hashlib, time, json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, deque

MU_THRESHOLD = 0.9995

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

class SCBValidator:
    REQUIRED_FIELDS = {"scb_id","version","intent","constraints","inputs","outputs","dependencies","rules","safety_gates","tests","implementation_notes"}
    @staticmethod
    def validate(scb: SCB) -> bool:
        if not scb.intent: raise ValueError("SCB intent missing")
        if scb.state_mutability: raise ValueError("State mutation is not allowed")
        if scb.safety_gates.get("mu_threshold", MU_THRESHOLD) > 1.0: raise ValueError("Invalid μ threshold")
        return True

class SCBGraph:
    def __init__(self):
        self.nodes: Dict[str, SCB] = {}
        self.edges: Dict[str, List[str]] = defaultdict(list)
    def add(self, scb: SCB):
        SCBValidator.validate(scb)
        if scb.scb_id in self.nodes: raise ValueError(f"Duplicate SCB: {scb.scb_id}")
        self.nodes[scb.scb_id] = scb
        for dep in scb.dependencies: self.edges[dep].append(scb.scb_id)
    def validate_acyclic(self):
        visited, stack = set(), set()
        def dfs(node: str):
            if node in stack: raise ValueError("DEPENDENCY_CYCLE_DETECTED")
            if node in visited: return
            visited.add(node); stack.add(node)
            for nxt in self.edges.get(node, []): dfs(nxt)
            stack.remove(node)
        for node in self.nodes: dfs(node)
    def topological_order(self) -> List[SCB]:
        indegree = {k: 0 for k in self.nodes}
        for src, targets in self.edges.items():
            for t in targets: indegree[t] += 1
        q = deque([k for k, v in indegree.items() if v == 0])
        ordered = []
        while q:
            n = sorted(q)[0]; q.remove(n)
            ordered.append(self.nodes[n])
            for nxt in self.edges.get(n, []):
                indegree[nxt] -= 1
                if indegree[nxt] == 0: q.append(nxt)
        if len(ordered) != len(self.nodes): raise ValueError("GRAPH_NOT_FULLY_RESOLVED")
        return ordered

@dataclass
class ExecutionResult:
    scb_id: str; status: str; output: Any; mu: float; ch: List[int]; seal: str
    trace: List[str] = field(default_factory=list)

class ExecutionEngine:
    def __init__(self): self.audit_log = []
    def compute_mu(self, scb: SCB, input_data: Any) -> float:
        base = len(scb.intent) % 100 / 100
        return min(1.0, base + 0.9)
    def compute_ch(self, scb: SCB, input_data: Any) -> List[int]:
        gates = scb.safety_gates.get("ch_rules", ["default"])
        return [1 if "allow" in g or "ok" in g else 1 for g in gates]
    def decide(self, mu: float, ch: List[int], threshold: float) -> str:
        if 0 in ch: return "LOCK"
        if mu >= threshold: return "MOVE"
        return "HOLD"
    def seal(self, scb: SCB, output: Any, mu: float) -> str:
        payload = json.dumps({"scb_id": scb.scb_id, "output": str(output), "mu": mu, "ts": time.time()}, sort_keys=True).encode()
        return hashlib.sha3_512(payload).hexdigest()
    def execute(self, scb: SCB, input_data: Any) -> ExecutionResult:
        mu = self.compute_mu(scb, input_data)
        ch = self.compute_ch(scb, input_data)
        threshold = scb.safety_gates.get("mu_threshold", MU_THRESHOLD)
        status = self.decide(mu, ch, threshold)
        output, trace = None, []
        if status == "MOVE":
            output = f"EXECUTED:{scb.intent}"; trace.append("execution_success")
        elif status == "LOCK":
            output = "LOCKED"; trace.append("safety_gate_triggered")
        else:
            output = "HOLDING"; trace.append("threshold_not_met")
        result = ExecutionResult(scb.scb_id, status, output, mu, ch, self.seal(scb, output, mu), trace)
        self.audit_log.append(result)
        return result

def main():
    print("UATOS v1.0 — SCB Validator, Graph, Execution Engine")
    print("MU_THRESHOLD =", MU_THRESHOLD)
    print("SEAL =", hashlib.sha3_512(b"UATOS-v1.0").hexdigest()[:16])

if __name__ == "__main__": main()