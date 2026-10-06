#!/usr/bin/env python3
"""M8: composed Fable + integrity readiness gate. No auto-installs, no guessing.

Order: selected Fable guard first (explicit path only), then the integrity
layer predicate. Either side can block; neither side can pass for the other.
Unknown Fable schemas are never patched: a guard that errors blocks with its
own stderr tail attached. Exit 0 READY_FOR_DECLARED_TASK, 1 otherwise,
2 broken invocation.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

LAYERS = ("scope", "extraction", "coverage", "execution", "results",
          "semantic", "persistence")
READY = "READY"
TERMINAL_ORDER = ("FAILED", "BLOCKED", "STALE", "PARTIAL")


def run_fable_guard(guard_path, project_root, gate, timeout=120):
    """Run an explicit guard script. Returns (passed_bool, tail)."""
    try:
        proc = subprocess.run(
            [sys.executable, str(guard_path), "check", "--project", str(project_root),
             "--gate", gate],
            text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, "guard spawn failed: %s" % (exc,)
    tail = ((proc.stdout or "") + (proc.stderr or ""))[-800:]
    return proc.returncode == 0, tail.strip()


def compose_overall(layers, reasons=None):
    """Same predicate as memory-integrity report.compose, dependency-free.

    Conformance-tested to agree with it on a shared matrix. Duplication is
    deliberate: the bridge must not import the package it supervises.
    """
    reasons = reasons or {}
    unknown = sorted(set(layers) - set(LAYERS))
    if unknown:
        return {"overall": "FAILED", "errors": ["E_LAYER_UNKNOWN: %s" % (",".join(unknown))]}
    missing = sorted(set(LAYERS) - set(layers))
    if missing:
        return {"overall": "FAILED", "errors": ["E_LAYER_MISSING: %s" % (",".join(missing))]}
    for name, verdict in layers.items():
        if verdict not in (READY, "PARTIAL", "BLOCKED", "STALE", "FAILED", "NOT_REQUIRED"):
            return {"overall": "FAILED", "errors": ["E_LAYER_VALUE: %s" % (name,)]}
        if verdict == "NOT_REQUIRED" and not (reasons.get(name) or "").strip():
            return {"overall": "FAILED", "errors": ["E_LAYER_REASON: %s" % (name,)]}
    required = {n: v for n, v in layers.items() if v != "NOT_REQUIRED"}
    for state in TERMINAL_ORDER:
        if state in required.values():
            return {"overall": state, "layers": dict(layers)}
    return {"overall": "READY_FOR_DECLARED_TASK", "layers": dict(layers)}


def check(project_root, layers=None, reasons=None, fable_guard=None, fable_gate="execute"):
    """Fable guard first, then integrity predicate. Returns (overall, detail)."""
    if fable_guard is not None:
        passed, tail = run_fable_guard(fable_guard, project_root, fable_gate)
        if not passed:
            return "BLOCKED", {"fable_guard": "failed", "tail": tail}
    if layers is None:
        return "BLOCKED", {"integrity": "no layers supplied"}
    result = compose_overall(layers, reasons)
    return result["overall"], result


def main(argv=None):
    parser = argparse.ArgumentParser(prog="fable_bridge_v2")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--fable-guard", default=None)
    parser.add_argument("--fable-gate", default="execute",
                        choices=["plan", "execute", "resume", "complete"])
    parser.add_argument("--layers-file", default=None)
    parser.add_argument("--reasons-file", default=None)
    args = parser.parse_args(argv)
    layers = reasons = None
    if args.layers_file:
        try:
            layers = json.loads(Path(args.layers_file).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(json.dumps({"overall": "FAILED", "errors": ["E_INPUT_LAYERS: %s" % (exc,)]}))
            return 2
    if args.reasons_file:
        try:
            reasons = json.loads(Path(args.reasons_file).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(json.dumps({"overall": "FAILED", "errors": ["E_INPUT_REASONS: %s" % (exc,)]}))
            return 2
    overall, detail = check(args.project_root, layers, reasons,
                            args.fable_guard, args.fable_gate)
    print(json.dumps({"overall": overall, "detail": detail}, indent=2, sort_keys=True))
    return 0 if overall == "READY_FOR_DECLARED_TASK" else 1


if __name__ == "__main__":
    sys.exit(main())
