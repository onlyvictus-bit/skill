"""R3 public, explicit TEST_ONLY coordinated task workflow.

CM owns all execution/history. Native Beads remains unqualified. The approved
fixture plan declares all tasks and source paths; every consumption rereads
those current sources and the complete frozen graph, never a done flag.
"""
import json
from pathlib import Path
import re
import sqlite3

import memory_integrity_workflow as core


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _engines(root):
    modules = core.companion(root)
    from complete_read_v2 import coordination
    return (*modules, coordination)


def _blocked(reason, calls=0, consumed=0, **extra):
    return dict(ok=False, overall="BLOCKED", evidence_class="TEST_ONLY",
                native_beads_qualified=False, blockers=[str(reason)],
                adapter_calls=calls, approvals_consumed=consumed, **extra)


def _validate_plan(plan, partition):
    if not isinstance(plan,dict) or set(plan)!={"schema_version","workspace_id","run_id","requirement_digest","tasks"} or plan["schema_version"]!=1:
        raise ValueError("E_COORD_PLAN_SCHEMA")
    for key in ("workspace_id","run_id"):
        if not isinstance(plan[key],str) or not re.fullmatch(r"[A-Za-z0-9_.-]+",plan[key]):
            raise ValueError("E_COORD_PLAN_ID: "+key)
    if not isinstance(plan["tasks"],list) or not plan["tasks"]:
        raise ValueError("E_COORD_PLAN_TASKS")
    entries = {}
    for row in plan["tasks"]:
        if not isinstance(row,dict) or set(row)!={"id","source","task","responses_file","requires"} or not isinstance(row["id"],str) or not re.fullmatch(r"[A-Za-z0-9_.-]+",row["id"]) or row["id"] in entries:
            raise ValueError("E_COORD_PLAN_TASK_SCHEMA")
        if not isinstance(row["task"],str) or not row["task"].strip() or not isinstance(row["requires"],list) or any(not isinstance(p,str) for p in row["requires"]):
            raise ValueError("E_COORD_PLAN_TASK_VALUE")
        source_path = Path(row["source"]).resolve()
        review_path = Path(row["responses_file"]).resolve()
        raw, sid, manifest = core.source_basis(source_path,partition)
        reviews_raw = review_path.read_bytes()
        core.checked_reviews(json.loads(reviews_raw),[u["id"] for u in manifest["units"]])
        task = {"schema_version":3,"instructions":row["task"]}
        wid = plan["workspace_id"]+"::"+plan["run_id"]+"::"+row["id"]
        entries[row["id"]] = {"id":row["id"],"work_item_id":wid,"source_path":str(source_path),
            "reviews_path":str(review_path),"source_id":sid,"source_digest":core.digest(raw),
            "reviews_digest":core.digest(reviews_raw),"task":task,"task_digest":core.digest(core.canonical(task)),
            "manifest":manifest,"requires":list(row["requires"])}
    return entries


def initialize(args):
    artifacts,ledger,partition,providers,results,runner,coord = _engines(args.claude_mon_root)
    plan = _read(args.plan_file)
    entries = _validate_plan(plan,partition)
    snapshot = {"schema_version":1,"workspace_id":plan["workspace_id"],"requirement_digest":plan["requirement_digest"],
        "revision":core.digest(core.canonical(plan)),"native_observation":"FIXTURE_NATIVE_UNQUALIFIED",
        "nodes":[e["work_item_id"] for e in entries.values()],
        "edges":[{"from":entries[p]["work_item_id"],"to":e["work_item_id"],"kind":"hard"}
                 for e in entries.values() for p in e["requires"]],"complete":True,"page_complete":True}
    coord.validate_snapshot(snapshot)
    profile_digest = core.digest(core.canonical(core.PROFILE))
    policies = {ident:{"schema_version":1,"coordination_required":True,"workspace_id":plan["workspace_id"],
        "task_id":e["work_item_id"],"run_id":plan["run_id"],"source_id":e["source_id"],
        "source_digest":e["source_digest"],"profile_digest":profile_digest,
        "requirement_digest":plan["requirement_digest"],"fence":"fixture-single-writer-v1"}
        for ident,e in entries.items()}
    for ident,p in policies.items():
        coord.validate_policy(p,entries[ident]["work_item_id"])
    root = Path(args.workspace_dir).resolve()
    if root.exists():
        raise ValueError("E_COORD_WORKSPACE_EXISTS: preserve existing workspace; use verify/run, not overwrite")
    root.mkdir(parents=True,exist_ok=False)
    cas = root/"artifacts"
    cas.mkdir()
    state = {"schema_version":1,"plan":plan,"entries":entries,"policies":policies,"snapshot":snapshot,
             "profile":core.PROFILE,"profile_digest":profile_digest}
    state_raw = core.canonical(state)
    state_digest = artifacts.store_bytes(cas,state_raw)
    core.write_json(root/"coordination-map.json",{"state_digest":state_digest})
    db = ledger.connect(root/"ledger.sqlite")
    try:
        ledger.event(db,"COORDINATED_WORKSPACE_FROZEN",detail=json.dumps({"state_digest":state_digest}),evidence_refs=[state_digest])
        for ident,e in entries.items():
            ledger.create_work_item(db,e["work_item_id"],e["task_digest"],e["source_id"])
        for ident,e in entries.items():
            coord.register_task(db,e["work_item_id"],policies[ident],snapshot,cas)
    finally:
        db.close()
    out = status(args)
    out["initialized"] = True
    return out


def open_workspace(args):
    artifacts,ledger,partition,providers,results,runner,coord = _engines(args.claude_mon_root)
    root = Path(args.workspace_dir).resolve()
    db = sqlite3.connect((root/"ledger.sqlite").as_uri()+"?mode=ro",uri=True,isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        history = ledger.verify_history(db,_read(args.checkpoint_file) if getattr(args,"checkpoint_file",None) else None)
        if history["internal_chain"]!="VERIFIED" or history["projection_replay"]!="VERIFIED" or history["anchored_completeness"]=="FAILED":
            raise ValueError("E_COORD_HISTORY: "+str(history))
        anchors = db.execute("SELECT detail FROM events WHERE kind='COORDINATED_WORKSPACE_FROZEN' ORDER BY seq").fetchall()
        if len(anchors)!=1:
            raise ValueError("E_COORD_WORKSPACE_ANCHOR")
        expected = json.loads(anchors[0]["detail"])["state_digest"]
        if _read(root/"coordination-map.json")!={"state_digest":expected}:
            raise ValueError("E_COORD_MAP: mutable map differs from canonical history")
        state = json.loads(artifacts.open_verified(root/"artifacts",expected))
        context = observe_current(db,state,root/"artifacts",artifacts,coord)
        return root,db,state,context,history,(artifacts,ledger,partition,providers,results,runner,coord)
    except Exception:
        db.close()
        raise


def observe_current(db,state,cas,artifacts,coord):
    """Adapter-owned fresh offline observation at each protected boundary.

    Source bytes are reread from the declared paths, not from prior caller
    observations. Fixture policy/fence is a frozen single-writer contract, not
    a claim of live native lease or branch observation.
    """
    current_snapshot = dict(state["snapshot"])
    from hybrid_bridge import branch
    for merge in db.execute("SELECT detail FROM events WHERE kind='NATIVE_MERGE_OUTCOME' ORDER BY seq"):
        payload = json.loads(merge["detail"])
        branch.verify_retained_merge(payload,artifacts,cas)
        if payload.get("source_origin",{}).get("database")=="fixture:"+state["plan"]["workspace_id"]:
            current_snapshot["revision"] = payload["merged_graph_digest"]
    contexts = {}
    for ident,e in state["entries"].items():
        policy = dict(state["policies"][ident])
        try:
            policy["source_digest"] = core.digest(Path(e["source_path"]).read_bytes())
        except OSError:
            policy["source_digest"] = "0"*64
        contexts[e["work_item_id"]] = coord.observed_context(policy,current_snapshot)
    return coord.context_envelope(contexts)


def _view(db,state,ctx,cas,coord,ledger):
    ready,blocked,current,historical = [],{},[],[]
    for ident,e in state["entries"].items():
        fresh=observe_current(db,state,cas,coord.artifacts,coord)
        decision = coord.evaluate(db,e["work_item_id"],cas,fresh,"report")
        accepted = ledger.accepted_attempt(db,e["work_item_id"])
        if accepted:
            historical.append(ident)
        if not decision["ok"]:
            blocked[ident] = decision.get("blocked") or [decision.get("reason")]
        elif accepted:
            current.append(ident)
        else:
            ready.append(ident)
    return {"ready":sorted(ready),"blocked":blocked,"current_accepted":sorted(current),"historical_accepted":sorted(historical)}


def status(args):
    root,db,state,ctx,history,engines = open_workspace(args)
    *_,coord = engines
    ledger = engines[1]
    try:
        view = _view(db,state,ctx,root/"artifacts",coord,ledger)
    finally:
        db.close()
    return dict(ok=True,overall="COORDINATION_STATUS_OFFLINE",evidence_class="TEST_ONLY",
                native_beads_qualified=False,history=history,**view)


def run_task(args):
    root,ro,state,ctx,history,engines = open_workspace(args)
    artifacts,ledger,partition,providers,results,runner,coord = engines
    ident = args.task_id
    try:
        if ident not in state["entries"]:
            return _blocked("E_COORD_TASK_UNKNOWN: "+ident)
        e = state["entries"][ident]
        coord.guard(ro,e["work_item_id"],root/"artifacts",ctx,"resume")
        accepted = ledger.accepted_attempt(ro,e["work_item_id"])
        if accepted:
            return dict(ok=True,overall="VERIFIED_COORDINATED_TASK_OFFLINE",evidence_class="TEST_ONLY",
                        native_beads_qualified=False,task_id=ident,resumed=True,adapter_calls=0,approvals_consumed=0)
        raw,sid,manifest = core.source_basis(e["source_path"],partition)
        reviews_raw = Path(e["reviews_path"]).read_bytes()
        if core.digest(reviews_raw)!=e["reviews_digest"] or manifest!=e["manifest"]:
            return _blocked("E_COORD_REVIEW_SOURCE_BASIS: frozen inputs changed")
        reviews = core.checked_reviews(json.loads(reviews_raw),[u["id"] for u in manifest["units"]])
    except Exception as exc:
        return _blocked(exc)
    finally:
        ro.close()
    # Resume the same attempt from retained proof. Unknown delivery never
    # resends, and no SQLite/native atomicity is claimed.
    db = ledger.connect(root/"ledger.sqlite")
    cas = root/"artifacts"
    calls = 0
    consumed_before = db.execute("SELECT COUNT(*) FROM approvals WHERE consumed=1").fetchone()[0]
    class ObservedFixture(providers.TestOnlyAdapter):
        def dispatch(self,request):
            nonlocal calls
            calls += 1
            return super().dispatch(request)
    try:
        units = {u["id"]:raw[u["range"][0]:u["range"][1]].decode("utf-8") for u in manifest["units"]}
        ctx = observe_current(db,state,cas,artifacts,coord)
        latest=ledger._latest_attempt(db,e["work_item_id"])
        resumed=latest is not None and latest["state"] in ("QUEUED","PREPARED","AWAITING_APPROVAL","DISPATCHING","RESPONSE_SAVED","VALIDATED","DELIVERY_UNKNOWN")
        if latest is not None and latest["state"] in ("DISPATCHING","DELIVERY_UNKNOWN"):
            ledger.reconcile_uncertain_attempt(db,latest["id"])
            return _blocked("E_RECOVERY_UNKNOWN: retained uncertain delivery; no automatic resend",0,0,attempt_id=latest["id"],resumed=True)
        if latest is not None and latest["state"]=="AWAITING_APPROVAL" and latest["approval_id"]:
            ledger.reconcile_uncertain_attempt(db,latest["id"])
            return _blocked("E_RECOVERY_UNKNOWN: interrupted spent approval; no automatic resend",0,0,attempt_id=latest["id"],resumed=True)
        if latest is not None and latest["state"]=="QUEUED":
            # A queued attempt has no bound request and has not dispatched.
            # Keep its cancellation in history before a fresh preparation.
            ledger.transition(db,latest["id"],"CANCELLED",error="recovered incomplete preparation; no bound request")
            latest=None
        if latest is not None and latest["state"] in ("PREPARED","AWAITING_APPROVAL","RESPONSE_SAVED","VALIDATED"):
            attempt,digest=latest["id"],latest["request_digest"]
            decision=coord.guard(db,e["work_item_id"],cas,ctx,"resume",attempt)
            request_raw=artifacts.open_verified(cas,digest)
            request=json.loads(request_raw)
            proof=request["source_proof"]
            if artifacts.open_verified(cas,proof["source_artifact_digest"])!=raw or json.loads(artifacts.open_verified(cas,proof["manifest_artifact_digest"]))!=manifest:
                raise ValueError("E_RECOVERY_SOURCE_BASIS")
            expected_raw,expected_digest,_=providers.build_complete_request(e["work_item_id"],e["task_digest"],units,e["task"]["instructions"],
                {"type":"rich-unit-results","schema_version":2},{"coordination_basis":core.canonical(decision["basis"]).decode("utf-8")},e["task_digest"],state["profile"],lambda value:value,source_proof=proof)
            if request_raw!=expected_raw or digest!=expected_digest:
                raise ValueError("E_RECOVERY_REQUEST_BASIS: frozen public request differs")
            if latest["state"]=="PREPARED" and not ledger.request_measurement_binding(db,attempt,digest):
                measurement=providers.final_payload_measurement(request_raw,state["profile"],lambda value:value)
                ref=artifacts.store_bytes(cas,core.canonical(measurement))
                ledger.bind_request_measurement(db,attempt,digest,ref)
        else:
            attempt,digest = runner.prepare(db,cas,e["work_item_id"],e["task_digest"],units,e["task"]["instructions"],
                {"type":"rich-unit-results","schema_version":2},{},e["task_digest"],state["profile"],
                counter=lambda value:value,manifest=manifest,source_bytes=raw,coordination_context=ctx)
        rich = {i:results.make_result(raw,manifest,i,e["task_digest"],attempt,reviews[i]["interpretation"],
                                    reviews[i]["findings"],reviews[i]["disposition"]) for i in units}
        p = state["profile"]
        current=ledger._latest_attempt(db,e["work_item_id"])
        if current["state"] in ("PREPARED","AWAITING_APPROVAL"):
            ctx = observe_current(db,state,cas,artifacts,coord)
            coord.guard(db,e["work_item_id"],cas,ctx,"dispatch",attempt)
            approvals=db.execute("SELECT * FROM approvals WHERE attempt_id=? AND request_digest=? AND consumed=0 ORDER BY id",(attempt,digest)).fetchall()
            if len(approvals)>1: raise ValueError("E_RECOVERY_APPROVAL_AMBIGUOUS")
            approval=approvals[0]["id"] if approvals else ledger.issue_approval(db,attempt,digest,p["provider"],p["model"],p["endpoint"],p["purpose"],p["output_limit"],{"max_calls":1,"max_spend":0})
            if current["state"]=="PREPARED": runner.approve(db,attempt,approval)
            runner.dispatch_via_adapter(db,cas,ObservedFixture([("ok",rich)]),attempt,approval,
                coordination_context=observe_current(db,state,cas,artifacts,coord))
        elif current["state"]=="RESPONSE_SAVED":
            coord.guard(db,e["work_item_id"],cas,observe_current(db,state,cas,artifacts,coord),"resume",attempt)
            runner.validate(db,cas,attempt,lambda payload:providers.validate_response(json.loads(payload),sorted(units),current["response_digest"]))
        runner.accept(db,cas,attempt,e["task_digest"],manifest,raw,{"provider":p["provider"],"model":p["model"],"endpoint":p["endpoint"],"purpose":p["purpose"],"max_output_tokens":p["output_limit"]},
            coordination_context=observe_current(db,state,cas,artifacts,coord))
        return dict(ok=True,overall="VERIFIED_COORDINATED_TASK_OFFLINE",evidence_class="TEST_ONLY",
                    native_beads_qualified=False,task_id=ident,resumed=resumed,adapter_calls=calls,
                    approvals_consumed=db.execute("SELECT COUNT(*) FROM approvals WHERE consumed=1").fetchone()[0]-consumed_before)
    except Exception as exc:
        consumed = db.execute("SELECT COUNT(*) FROM approvals WHERE consumed=1").fetchone()[0]-consumed_before
        return _blocked(exc,calls,consumed)
    finally:
        db.close()


def verify(args):
    root,db,state,ctx,history,engines = open_workspace(args)
    artifacts,ledger,partition,providers,results,runner,coord = engines
    try:
        view = _view(db,state,ctx,root/"artifacts",coord,ledger)
        if len(view["current_accepted"])!=len(state["entries"]):
            return _blocked("E_COORD_CURRENT_APPLICABILITY: not all approved tasks have current verified evidence",history=history,**view)
        out = dict(ok=True,overall="VERIFIED_COORDINATED_OFFLINE",evidence_class="TEST_ONLY",
                   native_beads_qualified=False,history=history,**view)
        if getattr(args,"query",None):
            records = []
            for ident,e in state["entries"].items():
                accepted = ledger.accepted_attempt(db,e["work_item_id"])
                coord.guard(db,e["work_item_id"],root/"artifacts",
                    observe_current(db,state,root/"artifacts",artifacts,coord),"recall",accepted)
                row = db.execute("SELECT response_digest FROM attempts WHERE id=?",(accepted,)).fetchone()
                response = json.loads(artifacts.open_verified(root/"artifacts",row["response_digest"]))
                records.extend(dict(r,coordinated_task_id=ident) for r in response["results"].values())
            universal = bool(re.search(r"\b(all|every|total|totals|absence)\b",args.query.lower()))
            selected = records if universal else [r for r in records if args.query in r["original_excerpt"]]
            out["recall"] = {"mode":"exhaustive" if universal else "locator","records":selected,
                             "semantic_answer_generated":False,"required_tasks":len(state["entries"])}
        final_view=_view(db,state,ctx,root/"artifacts",coord,ledger)
        if len(final_view["current_accepted"])!=len(state["entries"]):
            return _blocked("E_COORD_CURRENT_APPLICABILITY: basis changed during consumption",history=history,**final_view)
        out.update(final_view)
        return out
    finally:
        db.close()


def revoke(args):
    root,ro,state,ctx,history,engines = open_workspace(args)
    ro.close()
    if args.task_id not in state["entries"]:
        return _blocked("E_COORD_TASK_UNKNOWN")
    ledger = engines[1]
    db = ledger.connect(root/"ledger.sqlite")
    try:
        ledger.revoke(db,state["entries"][args.task_id]["work_item_id"],args.reason)
    finally:
        db.close()
    return status(args)


def seal(args):
    root,db,state,ctx,history,engines = open_workspace(args)
    try:
        checkpoint = engines[1].make_checkpoint(db,args.owner)
    finally:
        db.close()
    target = Path(args.seal_path).resolve()
    if target.is_relative_to(root):
        raise ValueError("E_CHECKPOINT_LOCATION: separately retain outside checked workspace")
    with target.open("xb") as handle:
        handle.write(core.canonical(checkpoint))
    return dict(ok=True,checkpoint=checkpoint,checkpoint_path=str(target),
                trust_limit="caller-retained reference; no protected storage service assumed")


def branch_fixture(args):
    from hybrid_bridge import branch,native
    root,ro,state,ctx,history,engines = open_workspace(args)
    ro.close()
    artifacts,ledger,*_ = engines
    if args.command=="branch-reconcile-fixture":
        db=ledger.connect(root/"ledger.sqlite")
        try:
            out=branch.reconcile_central_fixture_merge(native.CMCoordinationJournal(db,ledger),artifacts,root/"artifacts",args.operation_id)
            out.update(ok=True,overall="TEST_ONLY_MERGE_REPLAN_REQUIRED",evidence_class="TEST_ONLY",native_beads_qualified=False)
            return out
        finally:
            db.close()
    doc = _read(args.fixture_file)
    if not isinstance(doc,dict) or set(doc)!={"base","source","target","common_ancestor"}:
        return _blocked("E_BRANCH_FIXTURE_SCHEMA")
    expected_tasks = set(state["entries"])
    for name in ("base","source","target"):
        origin = doc[name]
        if origin.get("database")!="fixture:"+state["plan"]["workspace_id"] or set(origin.get("tasks",{}))!=expected_tasks:
            return _blocked("E_BRANCH_SCOPE: fixture is foreign to selected coordinated workspace")
        doc[name] = branch.freeze_origin(origin,artifacts,root/"artifacts")
    preview = branch.preview_merge(doc["base"],doc["source"],doc["target"],doc["common_ancestor"])
    if args.command == "branch-preview":
        return dict(ok=preview["mergeable"],overall="TEST_ONLY_MERGE_PREVIEW",preview=preview,
                    evidence_class="TEST_ONLY",native_beads_qualified=False)
    db = ledger.connect(root/"ledger.sqlite")
    try:
        out = branch.apply_central_fixture_merge(doc["base"],doc["source"],doc["target"],doc["common_ancestor"],
            doc["source"]["head"],doc["target"]["head"],native.CMCoordinationJournal(db,ledger),artifacts,root/"artifacts",args.operation_id)
        out.update(ok=out["status"]!="UNKNOWN",overall="TEST_ONLY_MERGE_REPLAN_REQUIRED",
                   evidence_class="TEST_ONLY",native_beads_qualified=False)
        return out
    finally:
        db.close()


def dispatch(args):
    if args.command in ("branch-preview","branch-merge-fixture","branch-reconcile-fixture"):
        return branch_fixture(args)
    if args.command == "coordinate-verify":
        from integrity_v2 import recall,report
        return recall.recall_coordinated_workspace(args) if args.query else report.verify_coordinated_workspace(args)
    routes = {"coordinate-init":initialize,"coordinate-run":run_task,"coordinate-resume":run_task,"coordinate-ready":status,
              "coordinate-verify":verify,"coordinate-revoke":revoke,"history-seal":seal}
    return routes[args.command](args)
