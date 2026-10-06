#!/usr/bin/env python3
"""Claude Mon read-basis gate that composes with, but never replaces, Fable."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from claude_mon_core import get_source, iter_receipts, load_registry, task_spec_sha256, verify_receipt


def check_required_sources(project_root: str | Path, task_spec: str, source_ids: list[str] | None = None) -> dict:
    root = Path(project_root).resolve()
    registry = load_registry(root)
    if source_ids:
        selected = [get_source(root, sid) for sid in source_ids]
    else:
        selected = [s for s in registry["sources"] if s.get("required")]
    wanted = task_spec_sha256(task_spec)
    blocked = []
    passed = []
    for source in selected:
        candidates = [r for r in iter_receipts(root, source["source_id"]) if r.get("task_spec_sha256") == wanted]
        complete = None
        for rec in reversed(candidates):
            check = verify_receipt(root, rec["receipt_id"], task_spec=task_spec)
            if check.get("status") == "COMPLETE":
                complete = check
                break
        if complete:
            passed.append({"source_id": source["source_id"], "receipt_id": complete["receipt_id"]})
        else:
            blocked.append({"source_id": source["source_id"], "reason": "NO_COMPLETE_RECEIPT"})
    return {"ok": not blocked, "task_spec_sha256": wanted, "passed": passed, "blocked": blocked}


def run_fable_guard(fable_guard: str, project_root: str | Path, gate: str) -> dict:
    proc = subprocess.run(
        [sys.executable, fable_guard, "check", "--project", str(Path(project_root).resolve()), "--gate", gate],
        text=True,
        capture_output=True,
        check=False,
    )
    return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def main() -> int:
    p = argparse.ArgumentParser(description="Compose Fable's existing guard with Claude Mon source-coverage receipts.")
    p.add_argument("--project", required=True)
    p.add_argument("--task-spec-file", required=True)
    p.add_argument("--source-id", action="append", dest="source_ids")
    p.add_argument("--fable-guard")
    p.add_argument("--fable-gate", choices=["plan", "execute", "resume", "complete"], default="execute")
    args = p.parse_args()
    task_spec = Path(args.task_spec_file).read_text(encoding="utf-8")
    result = {"fable": None, "claude_mon": None, "ok": False}
    if args.fable_guard:
        result["fable"] = run_fable_guard(args.fable_guard, args.project, args.fable_gate)
        if not result["fable"]["ok"]:
            print(json.dumps(result, sort_keys=True))
            return 2
    result["claude_mon"] = check_required_sources(args.project, task_spec, args.source_ids)
    result["ok"] = bool(result["claude_mon"]["ok"] and (result["fable"] is None or result["fable"]["ok"]))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
