#!/usr/bin/env python3
"""
uatos_cli.py — UATOS v2 Command Line Interface
Sovereign · Serverless · Cloudless · Vendorless
"""

import sys, os, json, argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'runtime'))
from scb_registry import SCB, SCBRegistry, SCBValidator, EventStore, SCBGraph, ExecutionEngine, MU_THRESHOLD

REGISTRY_DIR = os.environ.get('UATOS_REGISTRY_DIR', os.path.join(os.path.dirname(__file__), '..', 'scb_registry'))

registry = SCBRegistry(REGISTRY_DIR)
event_store = EventStore(REGISTRY_DIR)
engine = ExecutionEngine(registry, event_store)


def cmd_create(args):
    """Create a new SCB."""
    scb = SCB(
        scb_id=args.id,
        version=args.version or "1.0.0",
        intent=args.intent,
        constraints={"hard": [], "soft": [], "forbidden": []},
        inputs=args.inputs or {},
        outputs={},
        dependencies=args.deps or [],
        rules=args.rules or [],
        safety_gates={"mu_threshold": MU_THRESHOLD, "ch_rules": [args.gate] if args.gate else ["default"]},
        tests={"unit": [], "integration": []},
        implementation_notes=args.notes or ""
    )
    h = registry.put(scb)
    print(f"✓ SCB created: {args.id} @ {h[:16]}...")
    event_store.append("CLI_SCBCREATED", {"scb_id": args.id, "hash": h})


def cmd_list(args):
    """List all SCBs."""
    scbs = registry.list_all()
    print(f"\n{'SCB ID':<20} {'Version':<10} {'Intent':<40} {'Created'}")
    print("-" * 95)
    for s in scbs:
        print(f"{s.scb_id:<20} {s.version:<10} {s.intent[:38]:<40} {s.created_at[:19]}")
    print(f"\nTotal: {len(scbs)} SCBs")


def cmd_get(args):
    """Get SCB by ID."""
    scb = registry.get(args.id)
    if not scb:
        print(f"✗ SCB not found: {args.id}")
        return
    print(f"\n=== {scb.scb_id} ===")
    print(f"Version:     {scb.version}")
    print(f"Intent:      {scb.intent}")
    print(f"Dependencies:{', '.join(scb.dependencies) or '(none)'}")
    print(f"Rules:       {', '.join(scb.rules) or '(none)'}")
    print(f"State:       {'Mutable' if scb.state_mutability else 'Immutable'}")
    print(f"Created:     {scb.created_at}")
    print(f"Hash:        {scb.scb_hash()}")
    print(f"Safety gates: {scb.safety_gates}")
    print()


def cmd_simulate(args):
    """Simulate a chain."""
    chain = []
    if args.chain:
        for link in args.chain.split(','):
            parts = link.split('->')
            chain.append({"from": parts[0], "to": parts[1] if len(parts) > 1 else ""})

    result = engine.simulate(chain)
    status = "✓ PASS" if result['result'] == 'ALLOW' else "✗ BLOCK"
    print(f"\n{status} | μ={result['mu']:.6f} | CH={result['ch']:.6f} | HR={result['hr']:.6f}")
    print(f"Threshold:   {MU_THRESHOLD}")
    print(f"Chain links: {result['chain_length']}")


def cmd_execute(args):
    """Execute an SCB."""
    scb = registry.get(args.id)
    if not scb:
        print(f"✗ SCB not found: {args.id}")
        return

    result = engine.execute(scb)
    print(f"\n=== Execution Result ===")
    print(f"SCB:     {result.scb_id}")
    print(f"Status:  {result.status}")
    print(f"μ:       {result.mu:.6f}")
    print(f"CH:      {result.ch}")
    print(f"HR:      {result.hr:.6f}")
    print(f"Seal:    {result.seal}")
    print(f"Output:  {result.output or '(none)'}")
    print(f"Trace:   {' | '.join(result.trace)}")


def cmd_events(args):
    """Show event log."""
    events = event_store.get_events(args.after)
    print(f"\n{'Seq':<8} {'Type':<25} {'Timestamp'}")
    print("-" * 60)
    for e in events:
        print(f"{e['seq']:<8} {e['type']:<25} {e['timestamp'][:19]}")
    print(f"\nTotal: {len(events)} events")


def cmd_replay(args):
    """Replay events from sequence."""
    events = event_store.replay(args.from_seq)
    print(f"\nReplaying from seq {args.from_seq} — {len(events)} events")
    for e in events:
        print(f"[{e['seq']}] {e['type']}: {json.dumps(e['payload'])[:80]}")


def cmd_metrics(args):
    """Show system metrics."""
    scbs = registry.list_all()
    events = event_store.get_events()

    print(f"\n=== UATOS System Metrics ===")
    print(f"SCBs:        {len(scbs)}")
    print(f"Events:      {len(events)}")
    print(f"Executions:  {len(engine.audit_log)}")
    print(f"Threshold:   μ ≥ {MU_THRESHOLD}")
    print(f"Mode:        Sovereign · Serverless · Cloudless · Vendorless")
    print()


def cmd_graph(args):
    """Show DAG structure."""
    scbs = registry.list_all()
    graph = SCBGraph()
    for s in scbs:
        try:
            graph.add(s)
        except:
            pass

    print(f"\n=== DAG Structure ({len(graph.nodes)} nodes) ===")
    for node_id, scb in graph.nodes.items():
        deps = ', '.join(scb.dependencies) or '(root)'
        print(f"  {node_id} ← [{deps}]")
        print(f"    intent: {scb.intent[:50]}")


def cmd_help(args):
    print("""
UATOS v2 CLI — Sovereign AI Team Operating System

Usage: uatos_cli.py <command> [options]

Commands:
  create <id> <intent>     Create new SCB
  list                     List all SCBs
  get <id>                 Get SCB details
  simulate --chain A->B    Simulate pipeline chain
  execute <id>             Execute single SCB
  events [--after N]       Show event log
  replay --from N          Replay events from seq N
  metrics                  System metrics
  graph                    Show DAG structure
  help                     Show this help

Options:
  --version TEXT           SCB version (default: 1.0.0)
  --deps DEP1,DEP2         Comma-separated dependencies
  --rules RULE1,RULE2      Comma-separated rules
  --gate TEXT              CH gate (default: allow)
  --inputs JSON            JSON input dict
  --notes TEXT             Implementation notes
  --after N                Events after seq N
  --from N                 Replay from seq N
  --chain A->B,C->D        Chain links

Examples:
  python uatos_cli.py create scb-001 "Build user auth module"
  python uatos_cli.py list
  python uatos_cli.py simulate --chain auth->session->token
  python uatos_cli.py execute scb-001
  python uatos_cli.py events --after 0
  python uatos_cli.py metrics
""")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('command', nargs='?')
    args, unknown = parser.parse_known_args()

    if not args.command or args.command == 'help':
        cmd_help(args)
        return

    # Parse remaining args with sub-parsers
    sub = argparse.ArgumentParser()
    sub.add_argument('id', nargs='?')
    sub.add_argument('intent', nargs='?')
    sub.add_argument('--version')
    sub.add_argument('--deps')
    sub.add_argument('--rules')
    sub.add_argument('--gate')
    sub.add_argument('--inputs')
    sub.add_argument('--notes')
    sub.add_argument('--chain')
    sub.add_argument('--after', type=int, default=0)
    sub.add_argument('--from', dest='from_seq', type=int, default=0)

    parsed = sub.parse_args(unknown)

    if args.command == 'create':
        if not parsed.id or not parsed.intent:
            print("Error: create requires <id> and <intent>")
            return
        cmd_create(parsed)
    elif args.command == 'list':
        cmd_list(parsed)
    elif args.command == 'get':
        if not parsed.id:
            print("Error: get requires <id>")
            return
        cmd_get(parsed)
    elif args.command == 'simulate':
        cmd_simulate(parsed)
    elif args.command == 'execute':
        if not parsed.id:
            print("Error: execute requires <id>")
            return
        cmd_execute(parsed)
    elif args.command == 'events':
        cmd_events(parsed)
    elif args.command == 'replay':
        cmd_replay(parsed)
    elif args.command == 'metrics':
        cmd_metrics(parsed)
    elif args.command == 'graph':
        cmd_graph(parsed)
    else:
        print(f"Unknown command: {args.command}")
        cmd_help(args)


if __name__ == '__main__':
    main()