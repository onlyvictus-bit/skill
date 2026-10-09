#!/usr/bin/env python3
"""Single public skill workflow: offline audits and explicit native observation.

Supplied reviews are TEST_ONLY observations. They do not prove understanding.
The explicit companion owns the ledger; this facade never copies its engine.
Native observation reads the selected Beads project and never grants execution
qualification, native mutation, or evidence acceptance.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import sqlite3
import sys
import uuid

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from integrity_v2 import engine_client, report
from hybrid_bridge import cards, beads_bridge

SCHEMA_DIGEST = "bf3c6314a1b0e8503230f483ef0be19cbf2ace1d4cab96eb4d7a2599b0270c9f"
PROFILE = {"schema_version":2, "provider":"fake", "model":"offline-fixture-1",
           "encoding":"test-char", "encoding_version":"1", "counting_method":"test",
           "context_limit":1000000, "output_limit":100000,
           "endpoint":"offline://fixture", "purpose":"offline-audit", "max_spend":0}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def companion(root):
    ok, env = engine_client.handshake(root, expect_digest=SCHEMA_DIGEST)
    if not ok:
        raise ValueError("E_COMPANION: " + json.dumps(env))
    explicit = (Path(root) / "scripts").resolve()
    sys.path.insert(0, str(explicit))
    from complete_read_v2 import artifacts, ledger, partition, providers, results, runner
    if Path(partition.__file__).resolve().parent.parent != explicit:
        raise ValueError("E_COMPANION_IMPORT: module imported from another root")
    return artifacts, ledger, partition, providers, results, runner


def source_basis(path, partition):
    raw = Path(path).read_bytes()
    if not raw:
        raise ValueError("E_SOURCE_EMPTY: explicit nonempty UTF-8 text required")
    raw.decode("utf-8")
    sha = digest(raw)
    ident = "SRC-" + sha[:16]
    manifest = partition.build_manifest(ident, raw, max_unit_bytes=4096,
                                         max_primary_bytes=16384, context_units=1)
    errors = partition.validate_manifest(raw, manifest)
    if errors:
        raise ValueError(errors[0])
    return raw, ident, manifest


def write_json(path, value):
    Path(path).write_bytes(canonical(value))


def checked_reviews(fixture, ids):
    if not isinstance(fixture, dict) or set(fixture) != set(ids):
        raise ValueError("E_REVIEW_SCOPE: reviews must cover exact primary IDs")
    allowed = {"interpretation","findings","disposition","reviewer","unresolved"}
    for ident in ids:
        row = fixture[ident]
        if not isinstance(row, dict) or set(row) != allowed:
            raise ValueError("E_REVIEW_SHAPE: " + ident)
        for key in ("interpretation","reviewer"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise ValueError("E_REVIEW_EMPTY: " + ident + "/" + key)
        if row["disposition"] not in ("resolved","unresolved"):
            raise ValueError("E_REVIEW_DISPOSITION: " + ident)
        for key in ("findings","unresolved"):
            if not isinstance(row[key], list):
                raise ValueError("E_REVIEW_LIST: " + ident + "/" + key)
        if row["unresolved"] or row["disposition"] != "resolved":
            raise ValueError("E_REVIEW_UNRESOLVED: retain unresolved work; cannot accept complete offline run")
    return fixture


def presentation(out, rm_path):
    rm = json.loads(Path(rm_path).read_text(encoding="utf-8"))
    gap = {"id":"LIVE-UNVERIFIED","kind":"follow-up",
           "need":"Qualify live-provider and native memory behavior only with separate approval",
           "basis":{"requirement_ref":"R2-offline-scope","source_digest":next(iter(rm["source_digests"].values())),
                    "manifest_digest":rm["artifact_digests"]["manifest.json"],
                    "worktree_id":rm["generation"],"check_digest":digest(Path(rm_path).read_bytes())},
           "state":{"approval":"NOT_APPROVED","execution":"OFFLINE_ONLY","evidence":"TEST_ONLY",
                    "acceptance":out["overall"],"projection_freshness":"CURRENT" if out["ok"] else "BLOCKED"},
           "proof_ref":str(Path(rm_path).resolve()),"gap":"No live AI/backend/native Beads proof",
           "next":"Review isolated candidate before authorizing installation or one live call",
           "recheck":["provider consent","live dispatch qualification","fresh service boundary"],"blocking":True}
    out["cards"] = cards.derive_cards([gap], {"generation":rm["generation"],"run_map_digest":digest(Path(rm_path).read_bytes())})
    out["shadow"] = beads_bridge.project_shadow(out["cards"], str(Path(rm["run_dir"]).resolve()),
                                                 digest(Path(rm_path).read_bytes()))
    return out


def offline_run(args):
    from knowledge_bridge import workflow as knowledge, contracts as kc, trace_adapter
    knowledge_pack = knowledge.preflight(args)
    artifacts, ledger, partition, providers, results, runner = companion(args.claude_mon_root)
    raw, source_id, manifest = source_basis(args.source, partition)
    ids = [u["id"] for u in manifest["units"]]
    fixture_raw = Path(args.responses_file).read_bytes()
    fixture = checked_reviews(json.loads(fixture_raw), ids)
    task = {"schema_version":3,"instructions":args.task}
    if not args.task.strip():
        raise ValueError("E_TASK_EMPTY")
    task_digest, profile_digest = digest(canonical(task)), digest(canonical(PROFILE))
    run = Path(args.run_dir).resolve()
    rm_path = run / "run-map.json"
    if run.exists():
        if not rm_path.is_file():
            raise ValueError("E_RECOVERY: incomplete run retained; inspect and use new isolated run-dir, never blind resend")
        rm = json.loads(rm_path.read_text(encoding="utf-8"))
        if rm.get("task_digest") != task_digest or rm.get("profile_digest") != profile_digest \
                or rm.get("fixture_digest") != digest(fixture_raw):
            raise ValueError("E_RESUME_BASIS: task/profile/reviews changed; historical run preserved")
        expected_pack = None if knowledge_pack is None else digest(kc.canonical(knowledge_pack))
        if rm.get("knowledge_pack_sha256") != expected_pack:
            raise ValueError("E_KNOWLEDGE_RESUME_BASIS: pack changed or omitted")
        out = report.verify_run(rm_path, {source_id:digest(raw)}, args.claude_mon_root)
        if out["ok"]:
            observed = knowledge.verify_run(args,run)
            if observed is not None:
                out["knowledge"] = observed
        out["resumed"] = True
        return presentation(out, rm_path) if out["ok"] else out
    run.mkdir(parents=True, exist_ok=False)
    (run / "source.bin").write_bytes(raw)
    (run / "fixture.json").write_bytes(fixture_raw)
    if knowledge_pack is not None:
        (run / "knowledge-evidence.json").write_bytes(kc.canonical(knowledge_pack))
    write_json(run / "manifest.json", manifest)
    write_json(run / "task.json", task)
    write_json(run / "profile.json", PROFILE)
    generation = uuid.uuid4().hex
    binding = {"schema_version":3, "source_id":source_id, "source_digest":digest(raw),
               "task_digest":task_digest, "generation":generation}
    write_json(run / "scope.json", dict(binding, required_unit_ids=ids))
    write_json(run / "extraction.json", dict(binding, expected={"units":len(ids)},produced={"units":len(ids)},
                                            diagnostics=[],evidence_class="TEST_ONLY",format="utf8-text"))
    write_json(run / "semantic.json", dict(binding, reviews=[dict(unit_id=i,reviewer=fixture[i]["reviewer"],
                findings=fixture[i]["findings"],unresolved=fixture[i]["unresolved"],
                source_digest=digest(raw),task_digest=task_digest) for i in ids]))
    cas = run / "artifacts"
    cas.mkdir()
    db = ledger.connect(run / "ledger.sqlite")
    table = {u["id"]:u for u in manifest["units"]}
    def text(ident):
        start,end = table[ident]["range"]
        return raw[start:end].decode("utf-8")
    try:
        for chunk in manifest["chunks"]:
            wid = chunk["id"]
            ledger.create_work_item(db,wid,task_digest,source_id)
            primary = {i:text(i) for i in chunk["primary"]}
            context = {i:text(i) for i in chunk["context_before"] + chunk["context_after"]}
            if knowledge_pack is not None:
                context["knowledge_evidence_pack"] = kc.canonical(knowledge_pack).decode("utf-8")
            attempt, req_digest = runner.prepare(db,cas,wid,task_digest,primary,args.task,
                {"type":"rich-unit-results","schema_version":2},context,task_digest,PROFILE,
                counter=lambda value: value, manifest=manifest, source_bytes=raw)
            rich = {i:results.make_result(raw,manifest,i,task_digest,attempt,
                      fixture[i]["interpretation"],fixture[i]["findings"],fixture[i]["disposition"])
                    for i in chunk["primary"]}
            approval = ledger.issue_approval(db,attempt,req_digest,PROFILE["provider"],PROFILE["model"],
                PROFILE["endpoint"],PROFILE["purpose"],PROFILE["output_limit"],limits={"max_calls":1,"max_spend":0})
            runner.approve(db,attempt,approval)
            runner.dispatch_via_adapter(db,cas,providers.TestOnlyAdapter([("ok",rich)]),attempt,approval)
            runner.accept(db,cas,attempt,task_digest,manifest,raw,
                {"provider":PROFILE["provider"],"model":PROFILE["model"],"endpoint":PROFILE["endpoint"],
                 "purpose":PROFILE["purpose"],"max_output_tokens":PROFILE["output_limit"]})
    finally:
        db.close()
    if knowledge_pack is not None:
        trace_adapter.write(run,knowledge_pack)
    files = {p.relative_to(run).as_posix():digest(p.read_bytes()) for p in sorted(run.rglob("*")) if p.is_file()}
    rm = {"schema_version":3,"run_dir":str(run),"generation":generation,
          "source_id":source_id,"source_digests":{source_id:digest(raw)},"task_digest":task_digest,
          "profile_digest":profile_digest,"fixture_digest":digest(fixture_raw),"artifact_digests":files}
    if knowledge_pack is not None:
        rm["knowledge_pack_sha256"] = digest(kc.canonical(knowledge_pack))
    write_json(rm_path,rm)
    out = report.verify_run(rm_path,{source_id:digest(raw)},args.claude_mon_root)
    if out["ok"] and knowledge_pack is not None:
        out["knowledge"] = knowledge.verify_run(args,run)
    out["resumed"] = False
    return presentation(out,rm_path) if out["ok"] else out


def verify(args):
    rm_path = Path(args.run_map)
    rm = json.loads(rm_path.read_text(encoding="utf-8"))
    now = {rm["source_id"]:digest(Path(args.source).read_bytes())}
    out = report.verify_run(rm_path,now,args.claude_mon_root)
    if out["ok"]:
        from knowledge_bridge import workflow as knowledge
        observed = knowledge.verify_run(args,Path(rm['run_dir']).resolve())
        if observed is not None:
            out["knowledge"] = observed
    if out["ok"] and args.query:
        run = Path(rm["run_dir"])
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        records = {}
        db = sqlite3.connect((run / "ledger.sqlite").as_uri() + "?mode=ro",uri=True)
        try:
            rows = db.execute("SELECT a.response_digest FROM attempts a JOIN accepted b ON b.attempt_id=a.id WHERE b.revoked=0").fetchall()
            for row in rows:
                response = json.loads((run / "artifacts" / row[0]).read_text(encoding="utf-8"))
                records.update(response["results"])
        finally:
            db.close()
        ids = [u["id"] for u in manifest["units"]]
        # A simple locator may filter display, but never silently turn a
        # universal query into a top-k retrieval claim.
        universal = bool(re.search(r"\b(all|every|total|totals|absence)\b", args.query.lower()))
        chosen = ids if universal else [i for i in ids if args.query in records[i]["original_excerpt"]]
        out["recall"] = {"records":[records[i] for i in chosen],"mode":"exhaustive" if universal else "locator",
                         "coverage_basis":{"units":len(ids),"source_digest":now[rm["source_id"]]},
                         "semantic_answer_generated":False}
    return presentation(out,rm_path) if out["ok"] else out


def native_observe(args):
    from dataclasses import fields
    from hybrid_bridge import native, native_observation
    receipt = Path(args.receipt)
    if not receipt.is_absolute():
        raise ValueError("E_NATIVE_RECEIPT_PATH: absolute receipt path required")
    native_observation._ordinary(receipt.parent,directory=True)
    if receipt.exists() or receipt.is_symlink():
        raise ValueError("E_NATIVE_RECEIPT_EXISTS: preserve prior observation; choose a new receipt")
    # Keep the single-skill explicit companion contract even for diagnostics.
    companion(args.claude_mon_root)
    config = native_observation._strict_json(Path(args.selection_file).read_bytes())
    required = {field.name for field in fields(native.NativeSelection)}
    if not isinstance(config,dict) or set(config)!=required:
        raise ValueError("E_NATIVE_SELECTION_SCHEMA: exact explicit selection fields required")
    selection = native.NativeSelection(**config)
    out = native.NativeBeadsAdapter(selection).observe()
    out["receipt_path"] = str(receipt)
    # Exclusive creation prevents a second invocation from destroying evidence.
    with receipt.open("x",encoding="utf-8",newline="\n") as handle:
        handle.write(json.dumps(out,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command",required=True)
    run = sub.add_parser("offline-run")
    for key in ("claude-mon-root","source","task","responses-file","run-dir"):
        run.add_argument("--"+key,required=True)
    check = sub.add_parser("verify")
    for key in ("claude-mon-root","run-map","source"):
        check.add_argument("--"+key,required=True)
    check.add_argument("--query")
    for command in (run,check):
        for key in ("knowledge-index","knowledge-root","knowledge-policy","knowledge-task"):
            command.add_argument("--"+key)
        command.add_argument("--knowledge-worker-python")
        command.add_argument("--knowledge-worker-timeout",type=float,default=30)
        command.add_argument("--knowledge-model-python")
        command.add_argument("--knowledge-model-manifest")
        command.add_argument("--knowledge-model-timeout",type=float,default=120)
    run.add_argument("--knowledge-pack")
    check.add_argument("--require-knowledge",action="store_true")
    from knowledge_bridge import workflow as knowledge
    knowledge.register(sub)
    observe = sub.add_parser("native-observe")
    for key in ("claude-mon-root","selection-file","receipt"):
        observe.add_argument("--"+key,required=True)
    for name in ("coordinate-init","coordinate-run","coordinate-resume","coordinate-ready","coordinate-verify","coordinate-revoke","history-seal","branch-preview","branch-merge-fixture","branch-reconcile-fixture"):
        command = sub.add_parser(name)
        command.add_argument("--claude-mon-root",required=True)
        command.add_argument("--workspace-dir",required=True)
        command.add_argument("--checkpoint-file")
        if name == "coordinate-init":
            command.add_argument("--plan-file",required=True)
        if name in ("coordinate-run","coordinate-resume","coordinate-revoke"):
            command.add_argument("--task-id",required=True)
        if name == "coordinate-revoke":
            command.add_argument("--reason",required=True)
        if name == "coordinate-verify":
            command.add_argument("--query")
        if name == "history-seal":
            command.add_argument("--owner",required=True)
            command.add_argument("--seal-path",required=True)
        if name in ("branch-preview","branch-merge-fixture"):
            command.add_argument("--fixture-file",required=True)
        if name in ("branch-merge-fixture","branch-reconcile-fixture"):
            command.add_argument("--operation-id",required=True)
    args = parser.parse_args()
    try:
        if args.command.startswith("knowledge-"):
            out = knowledge.dispatch(args)
        elif args.command == "native-observe":
            out = native_observe(args)
        elif args.command.startswith(("coordinate-","branch-")) or args.command == "history-seal":
            import coordination_workflow
            out = coordination_workflow.dispatch(args)
        else:
            out = offline_run(args) if args.command == "offline-run" else verify(args)
    except Exception as exc:
        out = {"ok":False,"overall":"BLOCKED","evidence_class":"NATIVE_OBSERVED_UNQUALIFIED" if args.command=="native-observe" else "TEST_ONLY",
               "blockers":[type(exc).__name__ + ": " + str(exc)],
               "adapter_calls":0,"approvals_consumed":0}
        if args.command=="native-observe":
            out.update(active=False,native_beads_qualified=False,database_write_performed=False,inference_sent=False)
    print(json.dumps(out,sort_keys=True,ensure_ascii=False))
    return 0 if out.get("ok") is True else 2

if __name__ == "__main__":
    raise SystemExit(main())
