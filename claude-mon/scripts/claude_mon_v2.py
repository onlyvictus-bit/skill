#!/usr/bin/env python3
"""claude-mon v2 CLI. JSON envelopes, stable exit codes.

Exit 0: ok / check passed. Exit 1: check blocked/failed (reason in envelope).
Exit 2: broken invocation or internal error. Emits no source content except
through explicit content-emitting commands (payload, open-unit, export).
No network calls. Counting defaults to the profile's method via tiktoken;
--counter-words selects an explicitly synthetic word-split counter whose
output can never qualify a live gate (see qualify_for_live).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from complete_read_v2 import ENGINE_VERSION  # noqa: E402
from complete_read_v2 import (artifacts, budget, contracts, inventory, ledger,  # noqa: E402
                              partition, providers, runner)

COMMANDS = ("capabilities", "freeze", "prepare", "preflight", "run", "accept",
            "resume", "status", "verify", "export", "open-unit", "query")

WORDS = lambda text: text.split()  # noqa: E731


def emit(payload, code=0):
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


def fail(reason, code=1):
    return emit({"ok": False, "error": reason}, code)


def load_json(path, what):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(emit({"ok": False, "error": "E_INPUT_%s: %s" % (what, exc)}, 2))


def run_paths(run_dir):
    root = Path(run_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root, str(root / "ledger.db"), str(root / "artifacts")


def counter_for(args):
    return WORDS if args.counter_words else None


def cmd_capabilities(_args):
    return emit(contracts.capabilities_envelope(COMMANDS))


def cmd_freeze(args):
    _, _, _ = run_paths(args.run_dir)
    try:
        scope = inventory.freeze_scope(args.run_dir, args.sources)
    except Exception as exc:
        return fail("%s: %s" % (type(exc).__name__, exc))
    out = Path(args.run_dir).resolve() / "scope.json"
    out.write_text(json.dumps(scope, indent=2, sort_keys=True), encoding="utf-8")
    return emit({"ok": True, "scope_digest": scope["scope_digest"],
                 "sources": len(scope["sources"]), "scope_file": str(out)})


def cmd_prepare(args):
    root, db_path, art = run_paths(args.run_dir)
    units = load_json(args.units_file, "UNITS")
    profile = load_json(args.profile_file, "PROFILE")
    schema = load_json(args.schema_file, "SCHEMA")
    context = load_json(args.context_file, "CONTEXT") if args.context_file else {}
    instructions = Path(args.instructions_file).read_text(encoding="utf-8")
    manifest = load_json(args.manifest_file, "MANIFEST") if args.manifest_file else None
    source = Path(args.source_file).read_bytes() if args.source_file else None
    db = ledger.connect(db_path)
    try:
        if db.execute("SELECT id FROM work_items WHERE id=?",
                      (args.work_item,)).fetchone() is None:
            ledger.create_work_item(db, args.work_item, args.task_digest,
                                    args.source_id or "UNSPECIFIED")
        attempt_id, digest = runner.prepare(
            db, art, args.work_item, args.task_digest, units, instructions, schema,
            context, args.task_spec_digest, profile, counter=counter_for(args),
            manifest=manifest, source_bytes=source)
    except (ledger.LedgerError, providers.AdapterError, artifacts.ArtifactError) as exc:
        return fail("%s: %s" % (type(exc).__name__, exc))
    finally:
        db.close()
    return emit({"ok": True, "attempt_id": attempt_id, "request_digest": digest})


def cmd_preflight(args):
    _, db_path, _ = run_paths(args.run_dir)
    manifest = load_json(args.manifest_file, "MANIFEST")
    source = Path(args.source_file).read_bytes()
    profile = load_json(args.profile_file, "PROFILE")
    db = ledger.connect(db_path)
    try:
        ok, notes = runner.preflight(
            db, args.work_item, manifest, source, profile, args.per_unit_output,
            expect_task_digest=getattr(args, "expect_task_digest", None), counter=counter_for(args),
            reasoning_reserve=args.reasoning_reserve, safety_reserve=args.safety_reserve)
    except (ledger.LedgerError, budget.BudgetError) as exc:
        return fail("%s: %s" % (type(exc).__name__, exc))
    finally:
        db.close()
    return emit({"ok": ok, "notes": notes}, 0 if ok else 1)


def cmd_run(args):
    _, db_path, art = run_paths(args.run_dir)
    script = load_json(args.script_file, "SCRIPT")
    behaviors = [(kind, payload) for kind, payload in script]
    db = ledger.connect(db_path)
    try:
        row = db.execute("SELECT work_item_id FROM attempts WHERE id=?",(args.attempt_id,)).fetchone()
        if row is not None and ledger.coordination_get(db,row["work_item_id"]) is not None:
            return fail("E_COORD_CLI: coordinated tasks require the Memory Integrity public workflow with fresh context")
        runner.approve(db, args.attempt_id, args.approval_ref)
        row = db.execute("SELECT request_digest FROM attempts WHERE id=?",
                         (args.attempt_id,)).fetchone()
        request = json.loads(artifacts.open_verified(art, row["request_digest"]).decode("utf-8"))
        profile = request.get("model", {})
        approval = ledger.issue_approval(
            db, args.attempt_id, row["request_digest"], args.provider, args.model,
            profile.get("endpoint", ""), args.purpose, args.max_output,
            {"max_spend": profile.get("max_spend", 0)})
        adapter = providers.TestOnlyAdapter(behaviors)
        runner.dispatch_via_adapter(db, art, adapter, args.attempt_id, approval)
        state = db.execute("SELECT state FROM attempts WHERE id=?",
                           (args.attempt_id,)).fetchone()["state"]
        if args.accept:
            if state != "VALIDATED":
                return fail("E_RUN_ACCEPT: attempt is %s, not VALIDATED" % (state,))
            if not args.manifest_file or not args.source_file or not args.expect_task_digest:
                return fail("E_RUN_ACCEPT: --accept needs --manifest-file, --source-file and "
                            "--expect-task-digest", 2)
            manifest_full = load_json(args.manifest_file, "MANIFEST")
            source_full = Path(args.source_file).read_bytes()
            try:
                runner.accept(db, art, args.attempt_id, args.expect_task_digest,
                              manifest_full, source_full, {
                                  "provider": args.provider, "model": args.model,
                                  "endpoint": "test-only-transport", "purpose": args.purpose,
                                  "max_output_tokens": args.max_output})
            except ledger.LedgerError as exc:
                return fail("E_RUN_ACCEPT: %s" % (exc,))
            state = "ACCEPTED"
    except (ledger.LedgerError, providers.AdapterError, artifacts.ArtifactError) as exc:
        return fail("%s: %s" % (type(exc).__name__, exc))
    finally:
        db.close()
    return emit({"ok": True, "attempt_id": args.attempt_id, "state": state})


def cmd_accept(args):
    _, db_path, art = run_paths(args.run_dir)
    manifest = load_json(args.manifest_file, "MANIFEST")
    source = Path(args.source_file).read_bytes()
    db = ledger.connect(db_path)
    try:
        runner.accept(db, art, args.attempt_id, args.expect_task_digest,
                      manifest, source, {
                          "provider": args.provider, "model": args.model,
                          "endpoint": args.endpoint, "purpose": args.purpose,
                          "max_output_tokens": args.max_output})
    except ledger.LedgerError as exc:
        return fail(str(exc))
    finally:
        db.close()
    return emit({"ok": True, "attempt_id": args.attempt_id, "state": "ACCEPTED"})


def cmd_resume(args):
    _, db_path, _ = run_paths(args.run_dir)
    db = ledger.connect(db_path)
    try:
        if db.execute("SELECT key FROM meta WHERE key LIKE 'coordination:%' LIMIT 1").fetchone():
            return fail("E_COORD_CLI: coordinated resume requires fresh public-workflow applicability checks")
        moved = ledger.reconcile_on_open(db)
        pending = ledger.pending_work(db)
    finally:
        db.close()
    return emit({"ok": True, "reconciled": moved, "pending": pending})


def cmd_status(args):
    _, db_path, _ = run_paths(args.run_dir)
    db = ledger.connect(db_path)
    try:
        items = [dict(r) for r in db.execute(
            "SELECT id, task_digest, source_id, status FROM work_items ORDER BY id").fetchall()]
        attempts = [dict(r) for r in db.execute(
            "SELECT id, work_item_id, attempt_no, state FROM attempts"
            " ORDER BY work_item_id, attempt_no").fetchall()]
    finally:
        db.close()
    if args.work_item:
        items = [i for i in items if i["id"] == args.work_item]
        attempts = [a for a in attempts if a["work_item_id"] == args.work_item]
    return emit({"ok": True, "work_items": items, "attempts": attempts})


def cmd_verify(args):
    manifest = load_json(args.manifest_file, "MANIFEST")
    source = Path(args.source_file).read_bytes()
    errors = partition.validate_manifest(source, manifest)
    if errors:
        return emit({"ok": False, "errors": errors}, 1)
    return emit({"ok": True, "units": len(manifest["units"]),
                 "chunks": len(manifest["chunks"])})


def cmd_export(args):
    _, db_path, art = run_paths(args.run_dir)
    db = ledger.connect(db_path)
    try:
        report = {
            "work_items": [dict(r) for r in db.execute("SELECT * FROM work_items").fetchall()],
            "attempts": [dict(r) for r in db.execute("SELECT * FROM attempts").fetchall()],
            "accepted": [dict(r) for r in db.execute("SELECT * FROM accepted").fetchall()],
            "events": db.execute("SELECT COUNT(*) c FROM events").fetchone()["c"],
            "artifacts": sorted(p.name for p in Path(art).iterdir()) if Path(art).is_dir() else [],
        }
    finally:
        db.close()
    out = Path(args.out)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return emit({"ok": True, "report_file": str(out),
                 "work_items": len(report["work_items"])})


def cmd_open_unit(args):
    import hashlib
    manifest = load_json(args.manifest_file, "MANIFEST")
    source = Path(args.source_file).read_bytes()
    if hashlib.sha256(source).hexdigest() != manifest.get("source_digest"):
        return fail("E_UNIT_STALE: source changed since manifest; re-freeze before reading")
    table = {u["id"]: u for u in manifest.get("units", [])}
    unit = table.get(args.unit_id)
    if unit is None:
        return fail("E_UNIT_UNKNOWN: %s" % (args.unit_id,))
    start, end = unit["range"]
    try:
        text = source[start:end].decode("utf-8")
    except UnicodeDecodeError as exc:
        return fail("E_UNIT_ENCODING: %s" % (exc,))
    if hashlib.sha256(source[start:end]).hexdigest() != unit.get("sha256"):
        return fail("E_UNIT_STALE: unit bytes differ from manifest; re-freeze before reading")
    return emit({"ok": True, "id": args.unit_id, "range": [start, end],
                 "sha256": unit.get("sha256"), "text": text})


def cmd_query(args):
    manifest = load_json(args.manifest_file, "MANIFEST")
    source = Path(args.source_file).read_bytes()
    errors = partition.validate_manifest(source, manifest)
    if errors:
        return fail("E_QUERY_STALE_OR_INVALID: %s" % (errors[0],))
    needle = args.text
    if not needle:
        return fail("E_QUERY_EMPTY")
    try:
        needle_bytes = needle.encode("utf-8")
    except (UnicodeEncodeError, AttributeError) as exc:
        return fail("E_QUERY_TEXT: %s" % (exc,))
    hits = []
    for unit in manifest.get("units", []):
        start, end = unit["range"]
        blob = source[start:end]
        if needle_bytes in blob:
            try:
                blob.decode("utf-8")
            except UnicodeDecodeError:
                return fail("E_QUERY_ENCODING: unit %s is not strict UTF-8" % (unit["id"],))
            hits.append({"id": unit["id"], "range": [start, end]})
        if len(hits) >= args.max_hits:
            break
    return emit({"ok": True, "mode": "locator-not-semantic-search",
                 "hits": hits, "truncated": len(hits) == args.max_hits})


def build_parser():
    parser = argparse.ArgumentParser(prog="claude_mon_v2",
                                     description="claude-mon v2 entrypoint")
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("capabilities")

    freeze = sub.add_parser("freeze")
    freeze.add_argument("--run-dir", required=True)
    freeze.add_argument("--sources", nargs="+", required=True)

    prep = sub.add_parser("prepare")
    prep.add_argument("--run-dir", required=True)
    prep.add_argument("--work-item", required=True)
    prep.add_argument("--task-digest", required=True)
    prep.add_argument("--task-spec-digest", required=True)
    prep.add_argument("--units-file", required=True)
    prep.add_argument("--instructions-file", required=True)
    prep.add_argument("--schema-file", required=True)
    prep.add_argument("--context-file", default=None)
    prep.add_argument("--profile-file", required=True)
    prep.add_argument("--source-id", default=None)
    prep.add_argument("--manifest-file", default=None)
    prep.add_argument("--source-file", default=None)
    prep.add_argument("--counter-words", action="store_true")

    pre = sub.add_parser("preflight")
    pre.add_argument("--run-dir", required=True)
    pre.add_argument("--work-item", required=True)
    pre.add_argument("--manifest-file", required=True)
    pre.add_argument("--source-file", required=True)
    pre.add_argument("--profile-file", required=True)
    pre.add_argument("--per-unit-output", type=int, required=True)
    pre.add_argument("--task-spec-digest", default=None)
    pre.add_argument("--expect-task-digest", default=None)
    pre.add_argument("--reasoning-reserve", type=int, default=0)
    pre.add_argument("--safety-reserve", type=int, default=0)
    pre.add_argument("--counter-words", action="store_true")

    run = sub.add_parser("run")
    run.add_argument("--run-dir", required=True)
    run.add_argument("--attempt-id", required=True)
    run.add_argument("--approval-ref", required=True)
    run.add_argument("--provider", required=True)
    run.add_argument("--model", required=True)
    run.add_argument("--purpose", required=True)
    run.add_argument("--max-output", type=int, required=True)
    run.add_argument("--script-file", required=True)
    run.add_argument("--accept", action="store_true")
    run.add_argument("--manifest-file", default=None)
    run.add_argument("--source-file", default=None)
    run.add_argument("--expect-task-digest", default=None)

    accept = sub.add_parser("accept")
    accept.add_argument("--run-dir", required=True)
    accept.add_argument("--attempt-id", required=True)
    accept.add_argument("--expect-task-digest", required=True)
    accept.add_argument("--manifest-file", required=True)
    accept.add_argument("--source-file", required=True)
    accept.add_argument("--provider", required=True)
    accept.add_argument("--model", required=True)
    accept.add_argument("--endpoint", required=True)
    accept.add_argument("--purpose", required=True)
    accept.add_argument("--max-output", type=int, required=True)

    resume = sub.add_parser("resume")
    resume.add_argument("--run-dir", required=True)

    status = sub.add_parser("status")
    status.add_argument("--run-dir", required=True)
    status.add_argument("--work-item", default=None)

    verify = sub.add_parser("verify")
    verify.add_argument("--manifest-file", required=True)
    verify.add_argument("--source-file", required=True)

    export = sub.add_parser("export")
    export.add_argument("--run-dir", required=True)
    export.add_argument("--out", required=True)

    open_unit = sub.add_parser("open-unit")
    open_unit.add_argument("--manifest-file", required=True)
    open_unit.add_argument("--source-file", required=True)
    open_unit.add_argument("--unit-id", required=True)

    query = sub.add_parser("query")
    query.add_argument("--manifest-file", required=True)
    query.add_argument("--source-file", required=True)
    query.add_argument("--text", required=True)
    query.add_argument("--max-hits", type=int, default=20)
    return parser


HANDLERS = {"capabilities": cmd_capabilities, "freeze": cmd_freeze,
            "prepare": cmd_prepare, "preflight": cmd_preflight, "run": cmd_run,
            "accept": cmd_accept, "resume": cmd_resume, "status": cmd_status,
            "verify": cmd_verify, "export": cmd_export, "open-unit": cmd_open_unit,
            "query": cmd_query}


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        from complete_read_v2 import ENGINE_VERSION
        print(ENGINE_VERSION)
        return 0
    handler = HANDLERS.get(args.command)
    if handler is None:
        parser.print_usage(sys.stderr)
        return 2
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
