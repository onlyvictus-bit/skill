#!/usr/bin/env python3
"""Run the R4 shared-project claim protocol qualification pilot."""
import argparse
import json

from hybrid_bridge import shared_native_pilot


def _modules(claude_mon_root):
    import memory_integrity_workflow
    modules = memory_integrity_workflow.companion(claude_mon_root)
    from complete_read_v2 import coordination
    return modules[0], modules[1], coordination


def main(argv=None, run_func=shared_native_pilot.run_shared_claim_protocol_pilot):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bd", required=True)
    parser.add_argument("--expected-executable-sha256", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--claude-mon-root", required=True)
    args = parser.parse_args(argv)
    try:
        artifacts, ledger, coordination = _modules(args.claude_mon_root)
        out = run_func(
            bd_path=args.bd,
            expected_executable_sha256=args.expected_executable_sha256,
            workspace=args.workspace,
            receipt=args.receipt,
            ledger_module=ledger,
            coordination_module=coordination,
            artifacts_module=artifacts,
        )
    except Exception as exc:
        out = {
            "ok": False,
            "overall": "BLOCKED",
            "qualification_scope": "SHARED_PROJECT_CLAIM",
            "native_shared_claim_protocol_qualified": False,
            "native_beads_qualified": False,
            "native_merge_qualified": False,
            "blockers": [type(exc).__name__ + ": " + str(exc)],
        }
    print(json.dumps(out, sort_keys=True, ensure_ascii=False))
    return 0 if out.get("ok") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
