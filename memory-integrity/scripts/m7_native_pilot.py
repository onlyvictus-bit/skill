#!/usr/bin/env python3
"""Run the isolated M7 native claim/interruption/recovery qualification pilot."""
import argparse
import json
import sys

from hybrid_bridge import native_pilot


def _ledger_module(claude_mon_root):
    import memory_integrity_workflow
    return memory_integrity_workflow.companion(claude_mon_root)[1]


def main(argv=None, run_func=native_pilot.run_disposable_pilot):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bd", required=True)
    parser.add_argument("--expected-executable-sha256", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--claude-mon-root", required=True)
    args = parser.parse_args(argv)
    try:
        ledger = _ledger_module(args.claude_mon_root)
        out = run_func(
            bd_path=args.bd,
            expected_executable_sha256=args.expected_executable_sha256,
            workspace=args.workspace,
            receipt=args.receipt,
            ledger_module=ledger,
        )
    except Exception as exc:
        out = {
            "ok": False,
            "overall": "BLOCKED",
            "qualification_scope": "DISPOSABLE_PILOT",
            "native_beads_qualified": False,
            "shared_database_authorized": False,
            "blockers": [type(exc).__name__ + ": " + str(exc)],
        }
    print(json.dumps(out, sort_keys=True, ensure_ascii=False))
    return 0 if out.get("ok") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
