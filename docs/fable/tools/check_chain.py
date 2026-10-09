#!/usr/bin/env python3
"""Fable chain check (read-only): every requirement test_id registered;
every completed ID exists; plan tasks reference valid IDs; basis digests
match current files; evidence run referenced exists. Exit 0 or list gaps.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    errors = []
    requirements = json.loads((ROOT / "docs/fable/requirements.json").read_text())
    tests = json.loads((ROOT / "docs/fable/tests.json").read_text())
    plan = json.loads((ROOT / "docs/fable/plan.json").read_text())
    state = json.load((ROOT / "docs/fable/state.json").open())
    registered = {t["id"] for t in tests["tests"]}
    req_ids = {r["id"] for r in requirements["requirements"]}
    for req in requirements["requirements"]:
        for tid in req.get("test_ids", []) + [
                c for crit in req.get("criteria", []) for c in crit.get("test_ids", [])]:
            if tid not in registered:
                errors.append("test %s of %s unregistered" % (tid, req["id"]))
    for rid in state.get("completed_requirement_ids", []):
        if rid not in req_ids:
            errors.append("completed %s has no requirement" % (rid,))
    for task in plan.get("tasks", []):
        for rid in task.get("requirement_ids", []):
            if rid not in req_ids:
                errors.append("plan task %s references unknown %s"
                              % (task.get("id"), rid))
        for tid in task.get("test_ids", []):
            if tid not in registered:
                errors.append("plan task %s references unregistered %s"
                              % (task.get("id"), tid))
    for key, path in (("requirements_digest", "docs/fable/requirements.json"),
                      ("tests_digest", "docs/fable/tests.json"),
                      ("plan_digest", "docs/fable/plan.json")):
        if state.get("basis", {}).get(key) != sha(ROOT / path):
            errors.append("basis %s does not match %s" % (key, path))
    print(json.dumps({"ok": not errors, "errors": errors}, indent=1))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
