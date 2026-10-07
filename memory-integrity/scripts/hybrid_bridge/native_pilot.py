"""Disposable M7 Beads pilot helpers.

This module is intentionally scoped to a throw-away pilot database. It does
not activate NativeBeadsAdapter or authorize shared/project database writes.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path

from . import native
from . import native_observation as observation

ACTOR = "memory-integrity-pilot"


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_env(beads_dir, inherited=None):
    inherited = dict(os.environ if inherited is None else inherited)
    env = {k:v for k,v in inherited.items()
           if not k.upper().startswith(("BEADS_", "BD_", "DOLT_"))}
    env.update(BEADS_DIR=str(beads_dir), BD_DISABLE_METRICS="1", BD_JSON_ENVELOPE="0")
    return env


def init_argv(bd):
    return [str(bd), "--sandbox", "--actor", ACTOR, "--json",
            "init", "--quiet", "--stealth"]


def _parse_issue(raw):
    try:
        value = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise native.NativeContractError("E_PILOT_JSON") from exc
    if isinstance(value, list):
        if len(value) != 1 or not isinstance(value[0], dict):
            raise native.NativeContractError("E_PILOT_ISSUE_COUNT")
        value = value[0]
    if not isinstance(value, dict):
        raise native.NativeContractError("E_PILOT_ISSUE")
    ident = value.get("id")
    if not isinstance(ident, str) or not ident.strip():
        raise native.NativeContractError("E_PILOT_ISSUE_ID")
    return value


def issue_id(raw):
    return _parse_issue(raw)["id"]


def _capture_record(result):
    if not isinstance(result, dict):
        raise native.NativeContractError("E_PILOT_CAPTURE")
    required = ("exit_code", "stdout", "stderr", "capture_complete", "timed_out",
                "output_limit_exceeded", "capture_errors")
    if any(key not in result for key in required):
        raise native.NativeContractError("E_PILOT_CAPTURE")
    if result["timed_out"] or result["output_limit_exceeded"] or             result["capture_complete"] is not True or result["capture_errors"]:
        raise native.NativeContractError("E_PILOT_CAPTURE_UNCERTAIN")
    stdout, stderr = result["stdout"], result["stderr"]
    if not isinstance(stdout, bytes) or not isinstance(stderr, bytes):
        raise native.NativeContractError("E_PILOT_CAPTURE_BYTES")
    try:
        stderr_text = stderr.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise native.NativeContractError("E_PILOT_STDERR_UTF8") from exc
    unexpected = [line for line in stderr_text.splitlines()
                  if line.strip() and line.strip() != observation.JSON_MIGRATION_NOTE]
    if unexpected:
        raise native.NativeContractError("E_PILOT_DIAGNOSTIC: " + " | ".join(unexpected))
    if type(result["exit_code"]) is not int or result["exit_code"] != 0:
        raise native.NativeContractError("E_PILOT_EXIT: %s" % (result["exit_code"],))
    return {
        "exit_code": result["exit_code"],
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
    }


class PilotNativeAdapter:
    """Real-command adapter constrained to a disposable M7 pilot.

    The qualification attributes satisfy the journal seam only inside the
    pilot. A successful pilot receipt is still environment-scoped evidence,
    not permission to mutate a shared/project Beads database.
    """

    native_write_qualified = True
    evidence_class = "NATIVE_VERIFIED"
    qualification_scope = "DISPOSABLE_PILOT"

    def __init__(self, selection, qualification_id, evidence_refs, runner=None,
                 command_cwd=None):
        selection.validate()
        if not isinstance(qualification_id, str) or not qualification_id.strip():
            raise native.NativeContractError("E_PILOT_QUALIFICATION_ID")
        if not isinstance(evidence_refs, (list, tuple)) or not evidence_refs:
            raise native.NativeContractError("E_PILOT_EVIDENCE")
        self.selection = selection
        self.qualification_id = qualification_id
        self.qualification_evidence_refs = tuple(evidence_refs)
        self.selection_digest = hashlib.sha256(_canonical(asdict(selection))).hexdigest()
        self.command_cwd = None if command_cwd is None else Path(command_cwd).resolve()
        self._runner = runner or self._default_runner

    def _default_runner(self, argv, cwd, env):
        return observation._capture_process(
            argv, cwd=str(cwd), env=env, timeout=observation.TIMEOUT_SECONDS, shell=False)

    def _run(self, args, readonly):
        exe, root, beads, _db, _metadata = observation._selection(self.selection)
        argv = [str(exe), "--sandbox", "--actor", ACTOR, "--json"]
        if readonly:
            argv.append("--readonly")
        argv.extend(args)
        result = self._runner(
            argv, self.command_cwd if self.command_cwd is not None else root,
            build_env(beads))
        evidence = _capture_record(result)
        return result["stdout"].decode("utf-8", errors="strict"), evidence

    def execute(self, operation_id, command):
        del operation_id
        if not isinstance(command, dict) or command.get("kind") != "claim":
            raise native.NativeContractError("E_PILOT_OPERATION: only claim is qualified")
        task_id = command.get("native_task_id")
        actor = command.get("actor")
        if not isinstance(task_id, str) or not task_id.strip() or actor != ACTOR:
            raise native.NativeContractError("E_PILOT_OPERATION_IDENTITY")
        _raw, evidence = self._run(["update", task_id, "--claim"], readonly=False)
        return evidence

    def readback(self, command):
        if not isinstance(command, dict) or command.get("kind") != "claim":
            raise native.NativeContractError("E_PILOT_OPERATION")
        task_id = command.get("native_task_id")
        raw, _evidence = self._run(["show", task_id], readonly=True)
        issue = _parse_issue(raw)
        applied = (issue.get("id") == task_id and
                   issue.get("status") in ("in_progress", "in-progress") and
                   issue.get("assignee") == ACTOR)
        return {
            "applied": applied,
            "native_task_id": task_id,
            "observed_state": {
                "id": issue.get("id"),
                "status": issue.get("status"),
                "assignee": issue.get("assignee"),
                "lease_expires_at": issue.get("lease_expires_at"),
            },
            "snapshot_digest": hashlib.sha256(_canonical(issue)).hexdigest(),
        }


def _strict_setup_run(runner, argv, cwd, env, transcript):
    result = runner(argv, cwd, env)
    evidence = _capture_record(result)
    transcript.append({
        "arguments": list(argv),
        "exit_code": evidence["exit_code"],
        "stdout_sha256": evidence["stdout_sha256"],
        "stderr_sha256": evidence["stderr_sha256"],
        "stdout_bytes": evidence["stdout_bytes"],
        "stderr_bytes": evidence["stderr_bytes"],
    })
    return result["stdout"].decode("utf-8", errors="strict")


def run_disposable_pilot(*, bd_path, expected_executable_sha256, workspace, receipt,
                         ledger_module, runner=None, observer=None):
    """Run the M7 claim/interruption/recovery proof in a new disposable DB.

    This proves only the selected disposable pilot boundary. It never promotes
    NativeBeadsAdapter, never authorizes shared/project writes, and never
    retries an uncertain claim.
    """
    bd_path = Path(bd_path).resolve()
    workspace = Path(workspace).resolve()
    receipt = Path(receipt).resolve()
    if workspace.exists():
        raise native.NativeContractError("E_PILOT_WORKSPACE_EXISTS")
    if receipt.exists() or receipt.is_symlink():
        raise native.NativeContractError("E_PILOT_RECEIPT_EXISTS")
    if not receipt.parent.is_dir():
        raise native.NativeContractError("E_PILOT_RECEIPT_PARENT")
    if not bd_path.is_file():
        raise native.NativeContractError("E_PILOT_BD_PATH")
    actual_sha = hashlib.sha256(bd_path.read_bytes()).hexdigest()
    if actual_sha != str(expected_executable_sha256).lower():
        raise native.NativeContractError("E_PILOT_BD_HASH")
    if ledger_module is None or not callable(getattr(ledger_module, "connect", None)):
        raise native.NativeContractError("E_PILOT_LEDGER")

    if runner is None:
        def runner(argv, cwd, env):
            return observation._capture_process(
                argv, cwd=str(cwd), env=env,
                timeout=observation.TIMEOUT_SECONDS, shell=False)

    beads = workspace / ".beads"
    env = build_env(beads)
    transcript = []

    version_argv = [str(bd_path), "--sandbox", "--actor", ACTOR, "--json",
                    "--readonly", "version"]
    version_raw = _strict_setup_run(
        runner, version_argv, workspace.parent, env, transcript)
    version = observation._strict_json(version_raw)
    if not isinstance(version, dict) or version.get("version") != "1.3.1" or \
            version.get("commit") != observation.COMMIT:
        raise native.NativeQualificationError("E_PILOT_VERSION")

    launcher = workspace.with_name(workspace.name + "-launcher")
    if launcher.exists():
        raise native.NativeContractError("E_PILOT_LAUNCHER_EXISTS")
    workspace.mkdir(parents=True, exist_ok=False)
    launcher.mkdir(parents=True, exist_ok=False)

    _strict_setup_run(
        runner, ["git", "init", "--quiet"], launcher, dict(os.environ), transcript)
    _strict_setup_run(
        runner, ["git", "config", "beads.role", "maintainer"],
        launcher, dict(os.environ), transcript)

    _strict_setup_run(runner, init_argv(bd_path), launcher, env, transcript)

    info_argv = [str(bd_path), "--sandbox", "--actor", ACTOR, "--json",
                 "--readonly", "info"]
    info_raw = _strict_setup_run(runner, info_argv, launcher, env, transcript)
    info = observation._strict_json(info_raw)
    config = info.get("config") if isinstance(info, dict) else None
    prefix = config.get("issue_prefix") if isinstance(config, dict) else None
    if not isinstance(prefix, str) or not prefix.strip():
        raise native.NativeContractError("E_PILOT_PREFIX")

    metadata_path = beads / "metadata.json"
    try:
        metadata = observation._strict_json(metadata_path.read_bytes())
    except OSError as exc:
        raise native.NativeContractError("E_PILOT_METADATA") from exc
    if not isinstance(metadata, dict):
        raise native.NativeContractError("E_PILOT_METADATA")
    project_id = metadata.get("project_id")
    database_name = metadata.get("dolt_database")
    if not isinstance(project_id, str) or not project_id.strip() or \
            not isinstance(database_name, str) or not database_name.strip():
        raise native.NativeContractError("E_PILOT_METADATA_IDENTITY")

    create_argv = [str(bd_path), "--sandbox", "--actor", ACTOR, "--json",
                   "create", "M7 exactly-once recovery pilot", "-t", "task", "-p", "4"]
    created_raw = _strict_setup_run(runner, create_argv, launcher, env, transcript)
    task_id = issue_id(created_raw)

    selection = native.NativeSelection(
        str(bd_path), str(workspace), "1.3.1", actual_sha,
        expected_project_id=project_id,
        expected_database_name=database_name,
        expected_prefix=prefix,
    )
    observe_fn = observer or (lambda selected: native.NativeBeadsAdapter(selected).observe())
    observed = observe_fn(selection)
    if not isinstance(observed, dict) or observed.get("ok") is not True or \
            not isinstance(observed.get("snapshot"), dict):
        raise native.NativeQualificationError("E_PILOT_OBSERVATION")
    snapshot = observed["snapshot"]
    snapshot_digest = snapshot.get("snapshot_digest")
    if not isinstance(snapshot_digest, str) or len(snapshot_digest) != 64:
        raise native.NativeQualificationError("E_PILOT_OBSERVATION_DIGEST")
    qualification_ref = hashlib.sha256(_canonical(observed)).hexdigest()
    qualification_id = "m7-disposable-" + qualification_ref[:16]

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

    adapter = PilotNativeAdapter(
        selection, qualification_id, [qualification_ref], runner=captured_runner,
        command_cwd=launcher)
    command = {"kind": "claim", "native_task_id": task_id, "actor": ACTOR}
    operation_id = "m7-claim-" + hashlib.sha256(_canonical(command)).hexdigest()[:20]
    work_item_id = "m7-pilot::" + task_id
    task_digest = hashlib.sha256(_canonical(command)).hexdigest()
    source_id = "NATIVE-PILOT-" + qualification_ref[:16]
    journal_path = workspace / "m7-cm-ledger.sqlite"

    db = ledger_module.connect(journal_path)
    try:
        ledger_module.create_work_item(db, work_item_id, task_digest, source_id)
        journal = native.CMCoordinationJournal(db, ledger_module)

        class InterruptAfterEffect:
            native_write_qualified = adapter.native_write_qualified
            evidence_class = adapter.evidence_class
            selection_digest = adapter.selection_digest
            qualification_id = adapter.qualification_id
            qualification_evidence_refs = adapter.qualification_evidence_refs

            def execute(self, op_id, payload):
                adapter.execute(op_id, payload)
                raise InterruptedError("M7 injected interruption after native effect")

            def readback(self, payload):
                return adapter.readback(payload)

        guard = {
            "ok": True, "coordinated": True, "phase": "dispatch",
            "blocked": [], "ready": [],
            "snapshot_digest": snapshot_digest,
            "revision": str(snapshot.get("head") or snapshot.get("branch") or "pilot"),
            "basis": {
                "pilot_scope": "DISPOSABLE_PILOT",
                "qualification_ref": qualification_ref,
                "task_id": task_id,
            },
        }
        interrupted = native.coordinate_native_operation(
            journal, InterruptAfterEffect(), operation_id, work_item_id, command, guard)
    finally:
        db.close()

    db = ledger_module.connect(journal_path)
    try:
        journal = native.CMCoordinationJournal(db, ledger_module)
        recovered = native.reconcile_native_operation(
            journal, adapter, operation_id, work_item_id, command)
        recovered_again = native.reconcile_native_operation(
            journal, adapter, operation_id, work_item_id, command)
        rows = db.execute(
            "SELECT kind, detail FROM events WHERE kind LIKE 'NATIVE_%' ORDER BY seq"
        ).fetchall()
        journal_events = []
        for row in rows:
            try:
                payload = json.loads(row["detail"])
            except (TypeError, ValueError):
                continue
            if payload.get("operation_id") == operation_id:
                journal_events.append(row["kind"])
        history = ledger_module.verify_history(db)
    finally:
        db.close()

    claim_invocations = [
        row for row in transcript
        if "update" in row["arguments"] and "--claim" in row["arguments"]
    ]
    if len(claim_invocations) != 1:
        raise native.NativeContractError("E_PILOT_DUPLICATE_CLAIM")
    if interrupted.get("status") != "UNKNOWN" or \
            recovered.get("status") != "RECONCILED_NATIVE_APPLIED" or \
            recovered_again.get("status") != "IDEMPOTENT_RECONCILED":
        raise native.NativeContractError("E_PILOT_RECOVERY")
    if journal_events != ["NATIVE_INTENT", "NATIVE_UNKNOWN", "NATIVE_RECONCILED"]:
        raise native.NativeContractError("E_PILOT_JOURNAL_SEQUENCE")
    if history.get("internal_chain") != "VERIFIED" or history.get("projection_replay") != "VERIFIED":
        raise native.NativeContractError("E_PILOT_HISTORY")

    out = {
        "schema_version": 1,
        "ok": True,
        "overall": "M7_DISPOSABLE_PILOT_VERIFIED",
        "qualification_scope": "DISPOSABLE_PILOT",
        "pilot_native_write_observed": True,
        "native_beads_qualified": False,
        "shared_database_authorized": False,
        "installed_promoted": False,
        "workspace": str(workspace),
        "launcher_cwd": str(launcher),
        "receipt_path": str(receipt),
        "bd_sha256": actual_sha,
        "selection_digest": adapter.selection_digest,
        "qualification_id": qualification_id,
        "qualification_evidence_ref": qualification_ref,
        "native_task_id": task_id,
        "operation_id": operation_id,
        "interrupted": interrupted,
        "recovered": recovered,
        "recovered_again": recovered_again,
        "journal_events": journal_events,
        "history_internal_chain": history["internal_chain"],
        "history_projection_replay": history["projection_replay"],
        "claim_invocations": len(claim_invocations),
        "commands": transcript,
        "note": (
            "Disposable pilot proof only. It does not authorize or qualify "
            "native writes to a shared/project database."
        ),
    }
    with receipt.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(out, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
    return out
