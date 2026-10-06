#!/usr/bin/env python3
"""memory-integrity v2 thin CLI entrypoint. JSON envelopes, stable exit codes.

`capabilities --claude-mon-root <dir>` performs the versioned handshake
against an explicit engine copy. Pinned digest lives in PINNED_ENGINE_DIGEST
and is updated only by deliberate contract review, never automatically.
Exit 0 on success, 1 on handshake failure, 2 on broken invocation.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrity_v2 import ENGINE_VERSION  # noqa: E402
from integrity_v2 import engine_client  # noqa: E402
from integrity_v2 import extraction, report, source_audit, watchdog  # noqa: E402

# Pinned by deliberate review of claude-mon complete_read_v2/contracts.py.
# M0 value recorded at build time; any contract change requires re-pinning.
PINNED_ENGINE_DIGEST = "bf3c6314a1b0e8503230f483ef0be19cbf2ace1d4cab96eb4d7a2599b0270c9f"


def cmd_capabilities(args):
    ok, payload = engine_client.handshake(
        args.claude_mon_root,
        expect_schema_version=2,
        expect_digest=None if PINNED_ENGINE_DIGEST.startswith("REPLACE_") else PINNED_ENGINE_DIGEST,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if ok else 1


class TestBackend:
    """In-process controlled store for the watchdog command. TEST_ONLY."""

    def __init__(self):
        self.store = {}
        self.next_id = 0

    def remember(self, text):
        self.next_id += 1
        rec = {"id": "canon-%d" % self.next_id, "text": text}
        self.store[rec["id"]] = dict(rec)
        return rec

    def search(self, query):
        return {"hits": [dict(r) for r in self.store.values() if query in r["text"]]}

    def fetch(self, record_id):
        rec = self.store.get(record_id)
        return dict(rec) if rec else None

    def delete(self, record_id):
        if record_id not in self.store:
            return {"deleted": False}
        del self.store[record_id]
        return {"deleted": True}


def cmd_audit(args):
    scope = json.loads(Path(args.scope_file).read_text(encoding="utf-8"))
    current = {}
    for rel in [s["path"] for s in scope.get("sources", [])]:
        target = Path(args.source_dir) / rel
        if target.is_file():
            current[rel] = target.read_bytes()
    manifests = {}
    manifest_dir = Path(args.manifest_dir)
    if manifest_dir.is_dir():
        for path in sorted(manifest_dir.glob("*.json")):
            try:
                manifests[path.stem] = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                pass
    verdict, findings = source_audit.audit_scope(scope, current, manifests,
                                                 engine_root=args.claude_mon_root,
                                                 expected_schema_digest=PINNED_ENGINE_DIGEST)
    print(json.dumps({"ok": verdict == "READY", "verdict": verdict,
                      "findings": findings}, indent=2))
    return 0 if verdict == "READY" else 1


def cmd_report(args):
    layers = json.loads(Path(args.layers_file).read_text(encoding="utf-8"))
    reasons = json.loads(Path(args.reasons_file).read_text(encoding="utf-8")) \
        if args.reasons_file else {}
    if args.evidence_file:
        evidence = json.loads(Path(args.evidence_file).read_text(encoding="utf-8"))
        try:
            out = report.compose_verified(layers, reasons, evidence,
                                          empty_set_authorized=args.empty_set,
                                          evidence_root=args.evidence_root)
        except report.ReportError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
            return 1
    else:
        try:
            out = report.compose(layers, reasons)
        except report.ReportError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
            return 1
        out["warning"] = ("formatter-only composition is not authoritative; use the "
                          "offline workflow verify command for bound proof")
    # No JSON file of caller-provided READY strings is a successful report gate.
    ready = False
    print(json.dumps({"ok": ready, **out}, indent=2, sort_keys=True))
    return 1


def cmd_watchdog(args):
    out = watchdog.strict_roundtrip(TestBackend(), args.scope or "cli-probe", args.canary)
    ok = out["verdict"] == "HEALTHY"
    print(json.dumps({"ok": ok, "evidence_class": "TEST_ONLY", **out},
                     indent=2, sort_keys=True))
    return 0 if ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="memory_integrity_v2",
                                     description="memory-integrity v2 entrypoint")
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="command")
    cap = sub.add_parser("capabilities", help="handshake an explicit engine copy")
    cap.add_argument("--claude-mon-root", required=True)

    audit = sub.add_parser("audit", help="scope/binding audit over real files")
    audit.add_argument("--claude-mon-root", required=True)
    audit.add_argument("--scope-file", required=True)
    audit.add_argument("--source-dir", required=True)
    audit.add_argument("--manifest-dir", required=True)

    rep = sub.add_parser("report", help="compose layer verdicts")
    rep.add_argument("--layers-file", required=True)
    rep.add_argument("--reasons-file", default=None)
    rep.add_argument("--evidence-file", default=None)
    rep.add_argument("--evidence-root", default=None)
    rep.add_argument("--empty-set", action="store_true")

    watch = sub.add_parser("watchdog", help="strict round-trip on a TEST_ONLY backend")
    watch.add_argument("--scope", default="cli-probe")
    watch.add_argument("--canary", required=True)
    args = parser.parse_args(argv)
    if args.version:
        print(ENGINE_VERSION)
        return 0
    if args.command == "capabilities":
        return cmd_capabilities(args)
    if args.command == "audit":
        return cmd_audit(args)
    if args.command == "report":
        return cmd_report(args)
    if args.command == "watchdog":
        return cmd_watchdog(args)
    parser.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
