"""R4 shared-project claim protocol qualification pilot.

Runs only in a newly created throw-away project, but exercises the production
SharedNativeClaimAdapter and the real companion coordination guard. Success
qualifies the claim protocol, not any particular user's shared database and not
other native verbs.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from . import native
from . import native_observation as observation
from .native_pilot import (
    _canonical, _capture_record, _strict_setup_run, build_env, init_argv, issue_id,
)

ACTOR = "memory-integrity-shared-pilot"


def run_shared_claim_protocol_pilot(*, bd_path, expected_executable_sha256,
                                    workspace, receipt, ledger_module,
                                    coordination_module, artifacts_module,
                                    runner=None, observer=None):
    bd_path = Path(bd_path).resolve()
    workspace = Path(workspace).resolve()
    receipt = Path(receipt).resolve()
    if workspace.exists():
        raise native.NativeContractError("E_SHARED_PILOT_WORKSPACE_EXISTS")
    if receipt.exists() or receipt.is_symlink():
        raise native.NativeContractError("E_SHARED_PILOT_RECEIPT_EXISTS")
    if not receipt.parent.is_dir():
        raise native.NativeContractError("E_SHARED_PILOT_RECEIPT_PARENT")
    if not bd_path.is_file():
        raise native.NativeContractError("E_SHARED_PILOT_BD_PATH")
    actual_sha = hashlib.sha256(bd_path.read_bytes()).hexdigest()
    if actual_sha != str(expected_executable_sha256).lower():
        raise native.NativeContractError("E_SHARED_PILOT_BD_HASH")
    for module, method, code in (
        (ledger_module, "connect", "E_SHARED_PILOT_LEDGER"),
        (coordination_module, "register_task", "E_SHARED_PILOT_COORDINATION"),
        (artifacts_module, "store_bytes", "E_SHARED_PILOT_ARTIFACTS"),
    ):
        if module is None or not callable(getattr(module, method, None)):
            raise native.NativeContractError(code)

    if runner is None:
        def runner(argv, cwd, env):
            return observation._capture_process(
                argv, cwd=str(cwd), env=env,
                timeout=observation.TIMEOUT_SECONDS, shell=False)

    beads = workspace / ".beads"
    env = build_env(beads)
    transcript = []

    version_raw = _strict_setup_run(
        runner,
        [str(bd_path), "--sandbox", "--actor", ACTOR, "--json",
         "--readonly", "version"],
        workspace.parent, env, transcript)
    version = observation._strict_json(version_raw)
    if not isinstance(version, dict) or version.get("version") != "1.3.1" or             version.get("commit") != observation.COMMIT:
        raise native.NativeQualificationError("E_SHARED_PILOT_VERSION")

    launcher = workspace.with_name(workspace.name + "-launcher")
    if launcher.exists():
        raise native.NativeContractError("E_SHARED_PILOT_LAUNCHER_EXISTS")
    workspace.mkdir(parents=True, exist_ok=False)
    launcher.mkdir(parents=True, exist_ok=False)
    _strict_setup_run(
        runner, ["git", "init", "--quiet"], launcher, dict(os.environ), transcript)
    _strict_setup_run(
        runner, ["git", "config", "beads.role", "maintainer"],
        launcher, dict(os.environ), transcript)
    _strict_setup_run(runner, init_argv(bd_path), launcher, env, transcript)

    info_raw = _strict_setup_run(
        runner,
        [str(bd_path), "--sandbox", "--actor", ACTOR, "--json",
         "--readonly", "info"],
        launcher, env, transcript)
    info = observation._strict_json(info_raw)
    config = info.get("config") if isinstance(info, dict) else None
    prefix = config.get("issue_prefix") if isinstance(config, dict) else None
    if not isinstance(prefix, str) or not prefix.strip():
        raise native.NativeContractError("E_SHARED_PILOT_PREFIX")

    metadata = observation._strict_json((beads / "metadata.json").read_bytes())
    project_id = metadata.get("project_id") if isinstance(metadata, dict) else None
    database_name = metadata.get("dolt_database") if isinstance(metadata, dict) else None
    if not isinstance(project_id, str) or not project_id.strip() or             not isinstance(database_name, str) or not database_name.strip():
        raise native.NativeContractError("E_SHARED_PILOT_METADATA")

    created_raw = _strict_setup_run(
        runner,
        [str(bd_path), "--sandbox", "--actor", ACTOR, "--json",
         "create", "R4 shared claim protocol pilot", "-t", "task", "-p", "4"],
        launcher, env, transcript)
    task_id = issue_id(created_raw)

    selection = native.NativeSelection(
        str(bd_path), str(workspace), "1.3.1", actual_sha,
        expected_project_id=project_id,
        expected_database_name=database_name,
        expected_prefix=prefix,
    )
    observe_fn = observer or (lambda selected: native.NativeBeadsAdapter(selected).observe())
    observed = observe_fn(selection)
    if not isinstance(observed, dict) or observed.get("ok") is not True or             not isinstance(observed.get("snapshot"), dict):
        raise native.NativeQualificationError("E_SHARED_PILOT_OBSERVATION")
    native_snapshot = observed["snapshot"]
    native_snapshot_digest = native_snapshot.get("snapshot_digest")
    if not isinstance(native_snapshot_digest, str) or len(native_snapshot_digest) != 64:
        raise native.NativeQualificationError("E_SHARED_PILOT_OBSERVATION_DIGEST")

    evidence_ref = hashlib.sha256(_canonical(observed)).hexdigest()
    operation_id = "r4-shared-claim-" + hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:20]
    work_item_id = "r4-shared-pilot::" + task_id
    command = {"kind": "claim", "native_task_id": task_id, "actor": ACTOR}
    authorization = {
        "schema_version": 1,
        "approved": True,
        "scope": "SHARED_PROJECT_CLAIM",
        "selection_digest": native.selection_digest(selection),
        "operation_id": operation_id,
        "work_item_id": work_item_id,
        "native_task_id": task_id,
        "actor": ACTOR,
        "qualification_id": "r4-shared-" + evidence_ref[:16],
        "evidence_refs": [evidence_ref],
    }

    def captured_runner(argv, cwd, command_env):
        result = runner(argv, cwd, command_env)
        evidence = _capture_record(result)
        transcript.append({
            "arguments": list(argv),
            "exit_code": evidence["exit_code"],
            "stdout_sha256": evidence["stdout_sha256"],
            "stderr_sha256": evidence["stderr_sha256"],
            "stdout_bytes": evidence["stdout_bytes"],
            "stderr_bytes": evidence["stderr_bytes"],
        })
        return result

    adapter = native.SharedNativeClaimAdapter(
        selection, authorization, operation_id=operation_id,
        work_item_id=work_item_id, native_task_id=task_id, actor=ACTOR)
    # Override only the process runner while retaining production adapter logic.
    adapter._run = lambda args, readonly: _adapter_run_for_pilot(
        adapter, args, readonly, captured_runner)

    requirement_digest = hashlib.sha256(b"r4-shared-claim-protocol").hexdigest()
    task_digest = hashlib.sha256(_canonical(command)).hexdigest()
    source_id = "NATIVE-SHARED-" + evidence_ref[:16]
    source_digest = hashlib.sha256(task_id.encode("utf-8")).hexdigest()
    profile_digest = hashlib.sha256(b"native-shared-claim-v1").hexdigest()
    snapshot = {
        "schema_version": 1,
        "workspace_id": "r4-shared-pilot",
        "requirement_digest": requirement_digest,
        "revision": str(native_snapshot.get("head") or native_snapshot_digest),
        "native_observation": "NATIVE_SHARED_CLAIM_PROTOCOL",
        "nodes": [work_item_id],
        "edges": [],
        "complete": True,
        "page_complete": True,
    }
    policy = {
        "schema_version": 1,
        "coordination_required": True,
        "workspace_id": "r4-shared-pilot",
        "task_id": work_item_id,
        "run_id": "r4-shared-pilot",
        "source_id": source_id,
        "source_digest": source_digest,
        "profile_digest": profile_digest,
        "requirement_digest": requirement_digest,
        "fence": "shared-native-claim-v1",
    }

    cm_root = workspace / "cm"
    cas = cm_root / "artifacts"
    cas.mkdir(parents=True)
    db = ledger_module.connect(cm_root / "ledger.sqlite")
    try:
        ledger_module.create_work_item(db, work_item_id, task_digest, source_id)
        coordination_module.register_task(db, work_item_id, policy, snapshot, cas)
        context = coordination_module.context_envelope({
            work_item_id: coordination_module.observed_context(policy, snapshot)
        })
        journal = native.CMCoordinationJournal(db, ledger_module)
        first = native.coordinate_guarded_native_operation(
            coordination_module, db, journal, adapter, operation_id,
            work_item_id, str(cas), context, command)
        second = native.coordinate_guarded_native_operation(
            coordination_module, db, journal, adapter, operation_id,
            work_item_id, str(cas), context, command)
        history = ledger_module.verify_history(db)
        rows = db.execute(
            "SELECT kind, detail FROM events WHERE kind LIKE 'NATIVE_%' ORDER BY seq"
        ).fetchall()
        journal_events = [
            row["kind"] for row in rows
            if json.loads(row["detail"]).get("operation_id") == operation_id
        ]
    finally:
        db.close()

    claims = [
        row for row in transcript
        if "update" in row["arguments"] and "--claim" in row["arguments"]
    ]
    if first.get("status") != "NATIVE_APPLIED":
        raise native.NativeContractError("E_SHARED_PILOT_FIRST_RESULT")
    if second.get("status") != "IDEMPOTENT_NATIVE_APPLIED":
        raise native.NativeContractError("E_SHARED_PILOT_IDEMPOTENCY")
    if len(claims) != 1:
        raise native.NativeContractError("E_SHARED_PILOT_DUPLICATE_CLAIM")
    if journal_events != ["NATIVE_INTENT", "NATIVE_OUTCOME"]:
        raise native.NativeContractError("E_SHARED_PILOT_JOURNAL")
    if history.get("internal_chain") != "VERIFIED" or             history.get("projection_replay") != "VERIFIED":
        raise native.NativeContractError("E_SHARED_PILOT_HISTORY")

    out = {
        "schema_version": 1,
        "ok": True,
        "overall": "R4_SHARED_CLAIM_PROTOCOL_VERIFIED",
        "native_shared_claim_protocol_qualified": True,
        "native_beads_qualified": False,
        "native_merge_qualified": False,
        "generic_native_write_qualified": False,
        "shared_database_authorized": False,
        "qualification_scope": "SHARED_PROJECT_CLAIM",
        "selection_digest": native.selection_digest(selection),
        "qualification_id": authorization["qualification_id"],
        "qualification_evidence_ref": evidence_ref,
        "native_task_id": task_id,
        "operation_id": operation_id,
        "claim_invocations": len(claims),
        "journal_events": journal_events,
        "first": first,
        "second": second,
        "history_internal_chain": history["internal_chain"],
        "history_projection_replay": history["projection_replay"],
        "commands": transcript,
        "note": (
            "The production shared-claim protocol is qualified. Each real shared "
            "workspace still requires an exact current authorization record bound "
            "to its selection, CM work item, native task, actor and operation id."
        ),
    }
    with receipt.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(out, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
    return out


def _adapter_run_for_pilot(adapter, args, readonly, runner):
    """Inject the pilot recorder without changing production command semantics."""
    exe, root, beads, _db, _metadata = observation._selection(adapter.selection)
    argv = [str(exe), "--sandbox", "--actor", adapter.actor, "--json"]
    if readonly:
        argv.append("--readonly")
    argv.extend(args)
    result = runner(argv, root, build_env(beads))
    evidence = _capture_record(result)
    return result["stdout"].decode("utf-8", errors="strict"), evidence
