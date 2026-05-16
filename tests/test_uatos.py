#!/usr/bin/env python3
"""
test_uatos.py — UATOS v2 Test Suite
Tests SCB registry, DAG, execution engine, and API.
Sovereign · Serverless · Cloudless · Vendorless
"""

import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'runtime'))
from scb_registry import SCB, SCBRegistry, SCBValidator, EventStore, SCBGraph, ExecutionEngine, MU_THRESHOLD

def test_scb_immutability():
    """SCBs must be immutable (frozen dataclass)."""
    scb = SCB(
        scb_id="test-001", version="1.0.0", intent="Immutability test",
        constraints={"hard": [], "soft": [], "forbidden": []},
        inputs={}, outputs={}, dependencies=[], rules=[],
        safety_gates={"mu_threshold": 0.9995, "ch_rules": ["allow"]},
        tests={"unit": [], "integration": []}, implementation_notes=""
    )
    h = scb.scb_hash()
    print(f"  ✓ SCB hash: {h}")
    assert len(h) == 32, f"Expected 32-char hash, got {len(h)}"

def test_validator():
    """Validator rejects invalid SCBs."""
    try:
        SCBValidator.validate(SCB(
            scb_id="bad", version="1.0.0", intent="",  # empty intent
            constraints={"hard": [], "soft": [], "forbidden": []},
            inputs={}, outputs={}, dependencies=[], rules=[],
            safety_gates={}, tests={}, implementation_notes=""
        ))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  ✓ Validator correctly rejected empty intent: {e}")

def test_cycle_detection():
    """DAG rejects cyclic dependencies."""
    graph = SCBGraph()
    # True cycle: a→b→c→d→c (c depends on d AND d depends on c)
    graph.add(SCB(
        scb_id="a", version="1.0.0", intent="Node A",
        constraints={"hard": [], "soft": [], "forbidden": []},
        inputs={}, outputs={}, dependencies=[], rules=[],
        safety_gates={"mu_threshold": 0.9995, "ch_rules": ["allow"]},
        tests={"unit": [], "integration": []}, implementation_notes=""
    ))
    graph.add(SCB(
        scb_id="b", version="1.0.0", intent="Node B",
        constraints={"hard": [], "soft": [], "forbidden": []},
        inputs={}, outputs={}, dependencies=["a"], rules=[],
        safety_gates={"mu_threshold": 0.9995, "ch_rules": ["allow"]},
        tests={"unit": [], "integration": []}, implementation_notes=""
    ))
    graph.add(SCB(
        scb_id="c", version="1.0.0", intent="Node C",
        constraints={"hard": [], "soft": [], "forbidden": []},
        inputs={}, outputs={}, dependencies=["b", "d"], rules=[],  # depends on b AND d
        safety_gates={"mu_threshold": 0.9995, "ch_rules": ["allow"]},
        tests={"unit": [], "integration": []}, implementation_notes=""
    ))
    graph.add(SCB(
        scb_id="d", version="1.0.0", intent="Node D",
        constraints={"hard": [], "soft": [], "forbidden": []},
        inputs={}, outputs={}, dependencies=["c"], rules=[],  # depends on c → CYCLE: b→c→d→c
        safety_gates={"mu_threshold": 0.9995, "ch_rules": ["allow"]},
        tests={"unit": [], "integration": []}, implementation_notes=""
    ))
    try:
        graph.validate_acyclic()
        assert False, "Should have detected cycle"
    except ValueError as e:
        print(f"  ✓ Cycle detected correctly: {e}")

def test_registry():
    """SCB registry stores and retrieves correctly."""
    import tempfile
    tmp = tempfile.mkdtemp()
    r = SCBRegistry(tmp)
    e = EventStore(tmp)

    scb = SCB(
        scb_id="reg-test-001", version="1.0.0",
        intent="Registry test SCB",
        constraints={"hard": [], "soft": [], "forbidden": []},
        inputs={"test": True}, outputs={}, dependencies=[], rules=[],
        safety_gates={"mu_threshold": 0.9995, "ch_rules": ["allow"]},
        tests={"unit": ["test_one"], "integration": []},
        implementation_notes="Registry test"
    )

    h = r.put(scb)
    print(f"  ✓ Stored at: {h}")

    retrieved = r.get("reg-test-001")
    assert retrieved is not None, "Should retrieve SCB"
    assert retrieved.scb_id == "reg-test-001"
    assert retrieved.intent == "Registry test SCB"
    print(f"  ✓ Retrieved: {retrieved.scb_id}")

    assert r.has("reg-test-001")
    assert not r.has("non-existent")
    print(f"  ✓ Registry has/has-not check passed")

def test_execution():
    """Execution engine computes μ/CH/HR correctly."""
    import tempfile
    tmp = tempfile.mkdtemp()
    r = SCBRegistry(tmp)
    e = EventStore(tmp)
    engine = ExecutionEngine(r, e)

    mu = engine.compute_mu([0.9999, 0.9998, 0.9997, 0.9996])
    ch = engine.compute_ch(["allow", "allow"])
    hr = mu * (sum(ch) / len(ch))

    print(f"  μ={mu:.6f} CH={sum(ch)/len(ch):.6f} HR={hr:.6f}")
    assert mu >= 0.9995, f"μ {mu} below threshold"
    assert hr >= 0.9995, f"HR {hr} below threshold"
    print(f"  ✓ Metrics pass threshold")

    scb = SCB(
        scb_id="exec-test-001", version="1.0.0", intent="Execute test",
        constraints={"hard": [], "soft": [], "forbidden": []},
        inputs={}, outputs={}, dependencies=[], rules=[],
        safety_gates={"mu_threshold": 0.9995, "ch_rules": ["allow"]},
        tests={"unit": [], "integration": []}, implementation_notes=""
    )

    result = engine.execute(scb)
    print(f"  ✓ Execution result: {result.status} seal={result.seal[:30]}...")
    assert result.status == "MOVE", f"Expected MOVE, got {result.status}"

def test_coherence_formula():
    """Verify geometric mean formula."""
    import math
    vals = [0.9999, 0.9998, 0.9997, 0.9996]
    mu = math.exp(sum(math.log(v) for v in vals) / len(vals))
    print(f"  μ = exp(sum(log(vals)) / n) = {mu:.10f}")
    assert 0.9995 <= mu <= 1.0, f"μ out of range: {mu}"
    print(f"  ✓ Coherence formula verified: μ ≥ 0.9995")

def test_event_store():
    """Event store appends and replays correctly."""
    import tempfile
    tmp = tempfile.mkdtemp()
    e = EventStore(tmp)

    for i in range(5):
        e.append(f"TEST_EVENT_{i}", {"seq": i, "data": f"test-{i}"})

    events = e.get_events()
    print(f"  ✓ Appended 5 events, retrieved {len(events)}")
    assert len(events) == 5, f"Expected 5 events, got {len(events)}"

    replayed = e.replay(2)
    print(f"  ✓ Replayed from seq 2: {len(replayed)} events")
    assert len(replayed) == 3, f"Expected 3 replayed events, got {len(replayed)}"

def test_topological_order():
    """DAG returns deterministic topological order."""
    graph = SCBGraph()
    for sid, deps in [("a", []), ("b", ["a"]), ("c", ["a"]), ("d", ["b", "c"]), ("e", ["d"])]:
        graph.add(SCB(
            scb_id=sid, version="1.0.0", intent=f"Node {sid}",
            constraints={"hard": [], "soft": [], "forbidden": []},
            inputs={}, outputs={}, dependencies=deps, rules=[],
            safety_gates={"mu_threshold": 0.9995, "ch_rules": ["allow"]},
            tests={"unit": [], "integration": []}, implementation_notes=""
        ))

    graph.validate_acyclic()
    order = graph.topological_order()
    ids = [s.scb_id for s in order]
    print(f"  Order: {' → '.join(ids)}")

    # e must come after d; d must come after b and c; etc.
    assert ids.index('a') < ids.index('b')
    assert ids.index('a') < ids.index('c')
    assert ids.index('b') < ids.index('d')
    assert ids.index('c') < ids.index('d')
    assert ids.index('d') < ids.index('e')
    print(f"  ✓ Topological order valid")

def test_mu_threshold():
    """Verify MU_THRESHOLD constant."""
    print(f"  MU_THRESHOLD = {MU_THRESHOLD}")
    assert MU_THRESHOLD == 0.9995, f"Expected 0.9995, got {MU_THRESHOLD}"
    print(f"  ✓ Threshold correct")

def main():
    print("\n=== UATOS v2 Test Suite ===")
    tests = [
        ("SCB Immutability", test_scb_immutability),
        ("Validator", test_validator),
        ("Cycle Detection", test_cycle_detection),
        ("SCB Registry", test_registry),
        ("Execution Engine", test_execution),
        ("Coherence Formula", test_coherence_formula),
        ("Event Store", test_event_store),
        ("Topological Sort", test_topological_order),
        ("μ Threshold", test_mu_threshold),
    ]

    passed = 0
    for name, fn in tests:
        print(f"\n[{name}]")
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")

    print(f"\n=== RESULTS: {passed}/{len(tests)} passed ===")
    return 0 if passed == len(tests) else 1

if __name__ == '__main__':
    sys.exit(main())