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

    def __init__(self, selection, qualification_id, evidence_refs, runner=None):
        selection.validate()
        if not isinstance(qualification_id, str) or not qualification_id.strip():
            raise native.NativeContractError("E_PILOT_QUALIFICATION_ID")
        if not isinstance(evidence_refs, (list, tuple)) or not evidence_refs:
            raise native.NativeContractError("E_PILOT_EVIDENCE")
        self.selection = selection
        self.qualification_id = qualification_id
        self.qualification_evidence_refs = tuple(evidence_refs)
        self.selection_digest = hashlib.sha256(_canonical(asdict(selection))).hexdigest()
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
        result = self._runner(argv, root, build_env(beads))
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
