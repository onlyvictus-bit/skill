"""Beads observation adapter and inactive native mutation seam.

There is no native write executor in this module. A configured executable, archive
checksum, or approval never activates it.  M7 must verify the extracted binary
version/hash and perform the disposable database pilot before activation can be
considered.  ``FixtureBeadsAdapter`` is explicitly in-memory TEST_ONLY policy
evidence and cannot be substituted for an executable adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


class NativeQualificationError(RuntimeError):
    pass


class NativeContractError(ValueError):
    pass


@dataclass(frozen=True)
class NativeSelection:
    executable: str
    database: str
    expected_version: str
    executable_sha256: str
    release_ref: str = "beads-v1.3.1:c1c4b642ac1c08d8c828007a1c2f96e47e43ef7c"
    archive_sha256: str | None = None
    expected_project_id: str | None = None
    expected_database_name: str | None = None
    expected_prefix: str | None = None

    def validate(self):
        for key, value in (("executable", self.executable), ("database", self.database),
                           ("expected_version", self.expected_version)):
            if not isinstance(value, str) or not value.strip():
                raise NativeContractError("E_NATIVE_%s: non-empty text required" % key.upper())
        if not isinstance(self.executable_sha256, str) or len(self.executable_sha256) != 64:
            raise NativeContractError("E_NATIVE_EXE_SHA256: extracted executable SHA-256 required")
        try:
            int(self.executable_sha256,16)
        except ValueError as exc:
            raise NativeContractError("E_NATIVE_EXE_SHA256: hexadecimal digest required") from exc


def native_status(selection):
    """Return an honest inactive status without probing or running a binary."""
    selection.validate()
    return {
        "active": False,
        "qualification": "UNQUALIFIED_M7",
        "candidate": {
            "release_ref": selection.release_ref,
            "expected_version": selection.expected_version,
            "executable": selection.executable,
            "database": selection.database,
            "archive_sha256": selection.archive_sha256,
            "executable_sha256": selection.executable_sha256,
        },
        "missing": [
            "executable observed/version verified", "executable SHA-256 observed",
            "disposable database round trip", "native JSON/schema qualification",
            "M7 explicit authorization and retained receipt",
        ],
        "note": "archive metadata and candidate pins are not executable qualification",
    }


class NativeBeadsAdapter:
    """Real readonly observations; native mutation still requires M7 qualification.

    A clean read never sets active/qualified, grants a claim, or accepts evidence.
    Failures retain command outputs through observe(); read_snapshot refuses
    incomplete or unsafe observations rather than returning a fixture graph.
    """

    def __init__(self, selection):
        selection.validate()
        self.selection = selection

    def status(self):
        return native_status(self.selection)

    def observe(self):
        from .native_observation import observe
        return observe(self.selection)

    def read_snapshot(self):
        result = self.observe()
        if not result["ok"]:
            error = NativeQualificationError("; ".join(result["blockers"]))
            error.observation = result
            raise error
        return result["snapshot"]

    def execute(self, operation_id, command):
        del operation_id, command
        raise NativeQualificationError("E_NATIVE_UNQUALIFIED: native writes are disabled before M7")


class MemoryCoordinationJournal:
    """Minimal protocol-compatible central-journal stand-in for fixture tests.

    CM owns the real canonical chain.  This object merely makes the required
    intent/outcome/UNKNOWN sequencing observable before CM's M5 ledger is
    connected; it must never be treated as retained audit evidence.
    """

    def __init__(self):
        self.events = []
        self._ops = {}

    def append(self, kind, operation_id, payload):
        if not isinstance(operation_id,str) or not operation_id.strip():
            raise NativeContractError("E_NATIVE_OPERATION_ID: nonempty operation identity required")
        if kind not in ("NATIVE_INTENT", "NATIVE_OUTCOME", "NATIVE_UNKNOWN", "NATIVE_RECONCILED"):
            raise NativeContractError("E_NATIVE_EVENT_KIND: %s" % kind)
        record = {"kind": kind, "operation_id": operation_id, "payload": dict(payload)}
        self.events.append(record)
        self._ops[operation_id] = record
        return record

    def last(self, operation_id):
        return self._ops.get(operation_id)


class CMCoordinationJournal:
    """A narrow adapter to the supplied CM central ledger module.

    Callers must inject the already selected companion module and its open
    SQLite connection.  There is deliberately no module discovery or fallback
    ledger: the event append occurs in CM's serialised chain.  ``details`` are
    parsed from the durable event row on reopen, so unknown native operations
    are not forgotten merely because a Python process ended.
    """

    def __init__(self, db, ledger_module):
        if db is None or ledger_module is None or not callable(getattr(ledger_module, "coordination_record_event", None)):
            raise NativeContractError("E_CM_JOURNAL: explicit CM db and ledger module required")
        self.db = db
        self.ledger = ledger_module

    def _row(self, operation_id):
        for row in self.db.execute("SELECT kind, detail, actor, op_id, identity_json, evidence_refs_json FROM events WHERE kind LIKE 'NATIVE_%' ORDER BY seq DESC"):
            try:
                payload = json.loads(row["detail"])
                identity = json.loads(row["identity_json"])
                evidence = json.loads(row["evidence_refs_json"])
            except (TypeError, ValueError, KeyError) as exc:
                raise NativeContractError("E_CM_JOURNAL_PARSE: %s" % type(exc).__name__)
            if payload.get("operation_id") == operation_id:
                return {"kind": row["kind"], "operation_id": operation_id, "payload": payload,
                        "actor": row["actor"], "identity": identity, "evidence_refs": evidence}
        return None

    def append(self, kind, operation_id, payload):
        if not isinstance(operation_id,str) or not operation_id.strip():
            raise NativeContractError("E_NATIVE_OPERATION_ID: nonempty operation identity required")
        if kind not in ("NATIVE_INTENT", "NATIVE_OUTCOME", "NATIVE_UNKNOWN", "NATIVE_RECONCILED",
                        "NATIVE_MERGE_INTENT", "NATIVE_MERGE_OUTCOME"):
            raise NativeContractError("E_NATIVE_EVENT_KIND: %s" % kind)
        if not isinstance(payload, dict):
            raise NativeContractError("E_CM_JOURNAL_PAYLOAD")
        payload = dict(payload)
        payload["operation_id"] = operation_id
        previous = self._row(operation_id)
        allowed_predecessors = {
            "NATIVE_INTENT": (), "NATIVE_MERGE_INTENT": (),
            "NATIVE_OUTCOME": ("NATIVE_INTENT",), "NATIVE_MERGE_OUTCOME": ("NATIVE_MERGE_INTENT",),
            "NATIVE_UNKNOWN": ("NATIVE_INTENT",), "NATIVE_RECONCILED": ("NATIVE_INTENT", "NATIVE_UNKNOWN"),
        }
        if previous is not None:
            if previous["kind"] == kind and previous["payload"] == payload:
                return previous
            if previous["kind"] not in allowed_predecessors[kind]:
                raise NativeContractError("E_CM_JOURNAL_ORDER: %s after %s" % (kind, previous["kind"]))
        elif allowed_predecessors[kind]:
            raise NativeContractError("E_CM_JOURNAL_ORDER: %s requires an intent" % kind)
        work_item_id = payload.get("work_item_id")
        identity = {"operation_id": operation_id, "work_item_id": work_item_id,
                    "native_evidence_class": payload.get("evidence_class", "TEST_ONLY")}
        evidence = [item for item in payload.get("evidence_refs", []) if isinstance(item, str)]
        self.ledger.coordination_record_event(
            self.db, kind, work_item_id, json.dumps(payload, sort_keys=True, separators=(",", ":")),
            actor="unknown", op_id=operation_id + ":" + kind.lower(), object_version=1,
            identity=identity, evidence_refs=evidence,
        )
        return self._row(operation_id)

    def last(self, operation_id):
        return self._row(operation_id)


class FixtureBeadsAdapter:
    """In-memory TEST_ONLY adapter with visible write count and readback.

    This is a complete local fixture contract, not a mock of the CLI.  It
    models only the operation identity/reconciliation boundary that must hold
    regardless of the eventual native command serialization.
    """

    def __init__(self, state):
        if not isinstance(state, dict):
            raise NativeContractError("E_FIXTURE_STATE: object required")
        branch, head = state.get("branch"), state.get("head")
        if not isinstance(branch, str) or not branch or not isinstance(head, str) or not head:
            raise NativeContractError("E_FIXTURE_IDENTITY: branch and head required")
        self._state = dict(state)
        self._operations = {}
        self._interrupt = set()
        self.write_count = 0

    def interrupt_next(self, operation_id):
        self._interrupt.add(operation_id)

    def read_snapshot(self):
        payload = dict(self._state)
        payload.update({
            "database": payload.get("database", "fixture:beads"),
            "evidence_class": "TEST_ONLY",
            "native": False,
            "complete_read": True,
        })
        return payload

    def execute(self, operation_id, command):
        if operation_id in self._operations:
            return dict(self._operations[operation_id], duplicate_suppressed=True)
        self.write_count += 1
        record = {"operation_id": operation_id, "command": dict(command), "status": "APPLIED", "evidence_class": "TEST_ONLY"}
        self._operations[operation_id] = record
        if operation_id in self._interrupt:
            self._interrupt.remove(operation_id)
            raise InterruptedError("fixture interruption after one logical write")
        return dict(record, duplicate_suppressed=False)

    def readback(self, operation_id):
        return self._operations.get(operation_id)


def _command_digest(command):
    if not isinstance(command, dict) or not command:
        raise NativeContractError("E_NATIVE_COMMAND: non-empty object required")
    return hashlib.sha256(json.dumps(command, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()



def _hex_digest(value, code):
    if not isinstance(value, str) or len(value) != 64:
        raise NativeContractError(code)
    try:
        int(value, 16)
    except ValueError as exc:
        raise NativeContractError(code) from exc
    return value.lower()


def _qualified_native_adapter(adapter):
    """Validate immutable qualification identity for real native writes."""
    if getattr(adapter, "native_write_qualified", False) is not True:
        raise NativeQualificationError("E_NATIVE_UNQUALIFIED: native writes are disabled")
    if getattr(adapter, "evidence_class", None) != "NATIVE_VERIFIED":
        raise NativeQualificationError("E_NATIVE_QUALIFICATION_EVIDENCE")
    selection_digest = _hex_digest(
        getattr(adapter, "selection_digest", None), "E_NATIVE_SELECTION_DIGEST")
    qualification_id = getattr(adapter, "qualification_id", None)
    if not isinstance(qualification_id, str) or not qualification_id.strip():
        raise NativeQualificationError("E_NATIVE_QUALIFICATION_ID")
    refs = getattr(adapter, "qualification_evidence_refs", ())
    if not isinstance(refs, (tuple, list)) or not refs:
        raise NativeQualificationError("E_NATIVE_QUALIFICATION_REFS")
    refs = [_hex_digest(value, "E_NATIVE_QUALIFICATION_REF") for value in refs]
    if not callable(getattr(adapter, "execute", None)) or not callable(getattr(adapter, "readback", None)):
        raise NativeQualificationError("E_NATIVE_QUALIFICATION_ADAPTER")
    return {
        "selection_digest": selection_digest,
        "qualification_id": qualification_id,
        "evidence_refs": refs,
        "evidence_class": "NATIVE_VERIFIED",
    }


def _native_guard(guard):
    """Require a current companion dispatch guard before native mutation."""
    if not isinstance(guard, dict) or guard.get("ok") is not True or \
            guard.get("coordinated") is not True or guard.get("phase") != "dispatch" or \
            guard.get("blocked"):
        raise NativeContractError("E_NATIVE_GUARD: current coordinated dispatch guard required")
    snapshot = _hex_digest(guard.get("snapshot_digest"), "E_NATIVE_GUARD_SNAPSHOT")
    revision = guard.get("revision")
    basis = guard.get("basis")
    if not isinstance(revision, str) or not revision.strip() or not isinstance(basis, dict):
        raise NativeContractError("E_NATIVE_GUARD: revision and basis required")
    canonical = json.dumps(guard, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "snapshot_digest": snapshot,
        "revision": revision,
        "guard_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def _operation_binding(payload, operation_id, work_item_id, command_digest, qualification):
    if not isinstance(payload, dict) or payload.get("operation_id") != operation_id or \
            payload.get("work_item_id") != work_item_id or \
            payload.get("command_digest") != command_digest or \
            payload.get("selection_digest") != qualification["selection_digest"] or \
            payload.get("qualification_id") != qualification["qualification_id"]:
        raise NativeContractError("E_NATIVE_OPERATION_REBIND")


def coordinate_native_operation(journal, adapter, operation_id, work_item_id, command, guard):
    """Durable INTENT -> one native mutation -> readback -> terminal record.

    Once an INTENT exists without a proven terminal outcome, never issue the
    mutation again. Recovery must use reconcile_native_operation and backend
    readback only.
    """
    if not isinstance(journal, CMCoordinationJournal):
        raise NativeContractError("E_NATIVE_CM_JOURNAL_REQUIRED")
    if not isinstance(operation_id, str) or not operation_id.strip() or \
            not isinstance(work_item_id, str) or not work_item_id.strip():
        raise NativeContractError("E_NATIVE_OPERATION_ID")
    qualification = _qualified_native_adapter(adapter)
    guarded = _native_guard(guard)
    digest = _command_digest(command)
    previous = journal.last(operation_id)
    if previous is not None:
        _operation_binding(previous["payload"], operation_id, work_item_id, digest, qualification)
        if previous["kind"] == "NATIVE_OUTCOME":
            return {"operation_id": operation_id, "status": "IDEMPOTENT_NATIVE_APPLIED",
                    "result": previous["payload"].get("readback")}
        if previous["kind"] == "NATIVE_RECONCILED":
            return {"operation_id": operation_id, "status": "IDEMPOTENT_RECONCILED",
                    "result": previous["payload"].get("readback")}
        return {"operation_id": operation_id, "status": "UNKNOWN",
                "action": "reconcile backend readback; do not repeat native write"}

    intent = {
        "work_item_id": work_item_id,
        "command_digest": digest,
        "selection_digest": qualification["selection_digest"],
        "qualification_id": qualification["qualification_id"],
        "guard_digest": guarded["guard_digest"],
        "snapshot_digest": guarded["snapshot_digest"],
        "revision": guarded["revision"],
        "evidence_class": "NATIVE_VERIFIED",
        "evidence_refs": list(qualification["evidence_refs"]),
    }
    journal.append("NATIVE_INTENT", operation_id, intent)
    try:
        execution = adapter.execute(operation_id, command)
        readback = adapter.readback(command)
        if not isinstance(readback, dict) or readback.get("applied") is not True:
            raise NativeContractError("E_NATIVE_READBACK: applied effect not proven")
        if readback.get("native_task_id") != command.get("native_task_id"):
            raise NativeContractError("E_NATIVE_READBACK: task identity mismatch")
    except Exception as exc:
        journal.append("NATIVE_UNKNOWN", operation_id, dict(
            intent, reason=type(exc).__name__, error=str(exc)))
        return {"operation_id": operation_id, "status": "UNKNOWN",
                "action": "reconcile backend readback; do not repeat native write"}

    outcome = dict(intent, execute_evidence=execution, readback=readback)
    journal.append("NATIVE_OUTCOME", operation_id, outcome)
    return {"operation_id": operation_id, "status": "NATIVE_APPLIED", "result": readback}



def coordinate_guarded_native_operation(coordination_module, db, journal, adapter,
                                        operation_id, work_item_id, artifacts_dir,
                                        current_context, command):
    """Derive the dispatch guard from CM itself, then perform one native op.

    Callers provide observed context, not a pre-approved guard result. A
    blocked/invalid CM guard raises before the native intent is appended.
    """
    guard_fn = getattr(coordination_module, "guard", None)
    if not callable(guard_fn):
        raise NativeContractError("E_NATIVE_COORDINATION_MODULE")
    guard = guard_fn(db, work_item_id, artifacts_dir, current_context, "dispatch")
    return coordinate_native_operation(
        journal, adapter, operation_id, work_item_id, command, guard)


def reconcile_native_operation(journal, adapter, operation_id, work_item_id, command):
    """Resolve uncertain native delivery by readback only, never by retrying."""
    if not isinstance(journal, CMCoordinationJournal):
        raise NativeContractError("E_NATIVE_CM_JOURNAL_REQUIRED")
    qualification = _qualified_native_adapter(adapter)
    digest = _command_digest(command)
    previous = journal.last(operation_id)
    if previous is None or previous["kind"] not in (
            "NATIVE_INTENT", "NATIVE_UNKNOWN", "NATIVE_OUTCOME", "NATIVE_RECONCILED"):
        raise NativeContractError("E_NATIVE_RECONCILE_STATE")
    _operation_binding(previous["payload"], operation_id, work_item_id, digest, qualification)
    if previous["kind"] == "NATIVE_RECONCILED":
        return {"operation_id": operation_id, "status": "IDEMPOTENT_RECONCILED",
                "result": previous["payload"].get("readback")}
    if previous["kind"] == "NATIVE_OUTCOME":
        return {"operation_id": operation_id, "status": "IDEMPOTENT_NATIVE_APPLIED",
                "result": previous["payload"].get("readback")}

    readback = adapter.readback(command)
    if not isinstance(readback, dict) or readback.get("applied") is not True:
        return {"operation_id": operation_id, "status": "UNKNOWN",
                "action": "effect absent or unproven; do not retry without a new approved basis"}
    if readback.get("native_task_id") != command.get("native_task_id"):
        raise NativeContractError("E_NATIVE_RECONCILE_REBIND")
    payload = dict(previous["payload"], readback=readback,
                   recovery="authoritative backend readback; native write not reissued")
    journal.append("NATIVE_RECONCILED", operation_id, payload)
    return {"operation_id": operation_id, "status": "RECONCILED_NATIVE_APPLIED",
            "result": readback}


def _hex_digest(value, code):
    if not isinstance(value, str) or len(value) != 64:
        raise NativeContractError(code)
    try:
        int(value, 16)
    except ValueError as exc:
        raise NativeContractError(code) from exc
    return value.lower()


def _qualified_native_adapter(adapter):
    """Require explicit retained qualification before any native write."""
    if getattr(adapter, "native_write_qualified", False) is not True:
        raise NativeQualificationError("E_NATIVE_UNQUALIFIED: native writes are disabled")
    if getattr(adapter, "evidence_class", None) != "NATIVE_VERIFIED":
        raise NativeQualificationError("E_NATIVE_QUALIFICATION_EVIDENCE")
    selection_digest = _hex_digest(
        getattr(adapter, "selection_digest", None), "E_NATIVE_SELECTION_DIGEST")
    qualification_id = getattr(adapter, "qualification_id", None)
    if not isinstance(qualification_id, str) or not qualification_id.strip():
        raise NativeQualificationError("E_NATIVE_QUALIFICATION_ID")
    refs = getattr(adapter, "qualification_evidence_refs", ())
    if not isinstance(refs, (tuple, list)) or not refs:
        raise NativeQualificationError("E_NATIVE_QUALIFICATION_REFS")
    refs = [_hex_digest(value, "E_NATIVE_QUALIFICATION_REF") for value in refs]
    if not callable(getattr(adapter, "execute", None)) or not callable(getattr(adapter, "readback", None)):
        raise NativeQualificationError("E_NATIVE_QUALIFICATION_ADAPTER")
    return {
        "selection_digest": selection_digest,
        "qualification_id": qualification_id,
        "evidence_refs": refs,
        "evidence_class": "NATIVE_VERIFIED",
    }


def _native_guard(guard):
    """Require current companion dispatch eligibility before mutation."""
    if not isinstance(guard, dict) or guard.get("ok") is not True or \
            guard.get("coordinated") is not True or guard.get("phase") != "dispatch" or \
            guard.get("blocked"):
        raise NativeContractError("E_NATIVE_GUARD: current coordinated dispatch guard required")
    snapshot = _hex_digest(guard.get("snapshot_digest"), "E_NATIVE_GUARD_SNAPSHOT")
    revision = guard.get("revision")
    basis = guard.get("basis")
    if not isinstance(revision, str) or not revision.strip() or not isinstance(basis, dict):
        raise NativeContractError("E_NATIVE_GUARD: revision and basis required")
    canonical = json.dumps(guard, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "snapshot_digest": snapshot,
        "revision": revision,
        "guard_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def _operation_binding(payload, operation_id, work_item_id, command_digest, qualification):
    if not isinstance(payload, dict) or payload.get("operation_id") != operation_id or \
            payload.get("work_item_id") != work_item_id or \
            payload.get("command_digest") != command_digest or \
            payload.get("selection_digest") != qualification["selection_digest"] or \
            payload.get("qualification_id") != qualification["qualification_id"]:
        raise NativeContractError("E_NATIVE_OPERATION_REBIND")


def coordinate_native_operation(journal, adapter, operation_id, work_item_id, command, guard):
    """Persist intent before one mutation; uncertain delivery is never retried."""
    if not isinstance(journal, CMCoordinationJournal):
        raise NativeContractError("E_NATIVE_CM_JOURNAL_REQUIRED")
    if not isinstance(operation_id, str) or not operation_id.strip() or \
            not isinstance(work_item_id, str) or not work_item_id.strip():
        raise NativeContractError("E_NATIVE_OPERATION_ID")
    qualification = _qualified_native_adapter(adapter)
    guarded = _native_guard(guard)
    digest = _command_digest(command)
    previous = journal.last(operation_id)
    if previous is not None:
        _operation_binding(previous["payload"], operation_id, work_item_id, digest, qualification)
        if previous["kind"] == "NATIVE_OUTCOME":
            return {"operation_id": operation_id, "status": "IDEMPOTENT_NATIVE_APPLIED",
                    "result": previous["payload"].get("readback")}
        if previous["kind"] == "NATIVE_RECONCILED":
            return {"operation_id": operation_id, "status": "IDEMPOTENT_RECONCILED",
                    "result": previous["payload"].get("readback")}
        return {"operation_id": operation_id, "status": "UNKNOWN",
                "action": "reconcile backend readback; do not repeat native write"}

    intent = {
        "work_item_id": work_item_id,
        "command_digest": digest,
        "selection_digest": qualification["selection_digest"],
        "qualification_id": qualification["qualification_id"],
        "guard_digest": guarded["guard_digest"],
        "snapshot_digest": guarded["snapshot_digest"],
        "revision": guarded["revision"],
        "evidence_class": "NATIVE_VERIFIED",
        "evidence_refs": list(qualification["evidence_refs"]),
    }
    journal.append("NATIVE_INTENT", operation_id, intent)
    try:
        execution = adapter.execute(operation_id, command)
        readback = adapter.readback(command)
        if not isinstance(readback, dict) or readback.get("applied") is not True:
            raise NativeContractError("E_NATIVE_READBACK: applied effect not proven")
        if readback.get("native_task_id") != command.get("native_task_id"):
            raise NativeContractError("E_NATIVE_READBACK: task identity mismatch")
    except Exception as exc:
        journal.append("NATIVE_UNKNOWN", operation_id, dict(
            intent, reason=type(exc).__name__, error=str(exc)))
        return {"operation_id": operation_id, "status": "UNKNOWN",
                "action": "reconcile backend readback; do not repeat native write"}

    outcome = dict(intent, execute_evidence=execution, readback=readback)
    journal.append("NATIVE_OUTCOME", operation_id, outcome)
    return {"operation_id": operation_id, "status": "NATIVE_APPLIED", "result": readback}


def reconcile_native_operation(journal, adapter, operation_id, work_item_id, command):
    """Resolve uncertain delivery by readback only; never issue the write again."""
    if not isinstance(journal, CMCoordinationJournal):
        raise NativeContractError("E_NATIVE_CM_JOURNAL_REQUIRED")
    qualification = _qualified_native_adapter(adapter)
    digest = _command_digest(command)
    previous = journal.last(operation_id)
    if previous is None or previous["kind"] not in (
            "NATIVE_INTENT", "NATIVE_UNKNOWN", "NATIVE_OUTCOME", "NATIVE_RECONCILED"):
        raise NativeContractError("E_NATIVE_RECONCILE_STATE")
    _operation_binding(previous["payload"], operation_id, work_item_id, digest, qualification)
    if previous["kind"] == "NATIVE_RECONCILED":
        return {"operation_id": operation_id, "status": "IDEMPOTENT_RECONCILED",
                "result": previous["payload"].get("readback")}
    if previous["kind"] == "NATIVE_OUTCOME":
        return {"operation_id": operation_id, "status": "IDEMPOTENT_NATIVE_APPLIED",
                "result": previous["payload"].get("readback")}

    readback = adapter.readback(command)
    if not isinstance(readback, dict) or readback.get("applied") is not True:
        return {"operation_id": operation_id, "status": "UNKNOWN",
                "action": "effect absent or unproven; do not retry without a new approved basis"}
    if readback.get("native_task_id") != command.get("native_task_id"):
        raise NativeContractError("E_NATIVE_RECONCILE_REBIND")
    payload = dict(previous["payload"], readback=readback,
                   recovery="authoritative backend readback; native write not reissued")
    journal.append("NATIVE_RECONCILED", operation_id, payload)
    return {"operation_id": operation_id, "status": "RECONCILED_NATIVE_APPLIED",
            "result": readback}


def _fixture_journal(journal):
    if not isinstance(journal, (MemoryCoordinationJournal, CMCoordinationJournal)):
        raise NativeContractError("E_NATIVE_FIXTURE_ONLY: a fixture-compatible journal is required")
    return journal


def coordinate_fixture_operation(journal, adapter, operation_id, command):
    """Intent -> execute once -> readback -> outcome, or UNKNOWN/reconcile.

    The same operation id can never issue a second write after an interruption:
    it returns UNKNOWN until a later reconciliation has authoritative backend
    readback.  This is deliberately bounded to TEST_ONLY fixtures.
    """
    _fixture_journal(journal)
    if not isinstance(adapter, FixtureBeadsAdapter):
        raise NativeContractError("E_NATIVE_FIXTURE_ONLY: fixture adapter required")
    if not isinstance(operation_id, str) or not operation_id.strip():
        raise NativeContractError("E_NATIVE_OPERATION_ID")
    previous = journal.last(operation_id)
    if previous is not None:
        previous_digest = previous.get("payload", {}).get("command_digest")
        requested_digest = _command_digest(command)
        if previous_digest is not None and previous_digest != requested_digest:
            raise NativeContractError("E_NATIVE_OPERATION_REBIND: operation id has a different command")
        if previous["kind"] == "NATIVE_UNKNOWN":
            return {"operation_id": operation_id, "status": "UNKNOWN", "action": "reconcile backend; do not repeat write"}
        if previous["kind"] == "NATIVE_INTENT":
            return {"operation_id": operation_id, "status": "UNKNOWN", "action": "intent has no outcome; reconcile backend; do not repeat write"}
        return {"operation_id": operation_id, "status": "IDEMPOTENT", "action": "outcome already recorded"}
    intent = {"command_digest": _command_digest(command), "evidence_class": "TEST_ONLY"}
    journal.append("NATIVE_INTENT", operation_id, intent)
    try:
        result = adapter.execute(operation_id, command)
        readback = adapter.readback(operation_id)
        if readback != {k: v for k, v in result.items() if k != "duplicate_suppressed"}:
            raise NativeContractError("E_NATIVE_READBACK: fixture readback mismatch")
    except (InterruptedError, NativeContractError) as exc:
        journal.append("NATIVE_UNKNOWN", operation_id, {"reason": type(exc).__name__, "command_digest":intent["command_digest"], "evidence_class": "TEST_ONLY"})
        return {"operation_id": operation_id, "status": "UNKNOWN", "action": "reconcile backend; do not repeat write"}
    journal.append("NATIVE_OUTCOME", operation_id, {"readback": readback, "command_digest":intent["command_digest"], "evidence_class": "TEST_ONLY"})
    return {"operation_id": operation_id, "status": "TEST_ONLY_APPLIED", "result": readback}


def reconcile_fixture_operation(journal, adapter, operation_id):
    """Resolve an UNKNOWN fixture intent by readback only, never by retrying.

    A returned ``ABSENT`` remains UNKNOWN because a real backend may need a
    stronger replica/read barrier before concluding that the interrupted write
    did not commit.  That conservative boundary avoids manufacturing a second
    write during recovery.
    """
    _fixture_journal(journal)
    if not isinstance(adapter, FixtureBeadsAdapter):
        raise NativeContractError("E_NATIVE_FIXTURE_ONLY: fixture adapter required")
    previous = journal.last(operation_id)
    if previous is None or previous["kind"] not in ("NATIVE_INTENT", "NATIVE_UNKNOWN", "NATIVE_RECONCILED"):
        raise NativeContractError("E_NATIVE_RECONCILE_STATE: UNKNOWN operation required")
    if previous["kind"] == "NATIVE_RECONCILED":
        return {"operation_id": operation_id, "status": "IDEMPOTENT_RECONCILED", "action": "readback already sealed"}
    readback = adapter.readback(operation_id)
    if readback is None:
        return {"operation_id": operation_id, "status": "UNKNOWN", "action": "absent readback needs stronger backend reconciliation; do not retry"}
    digest = previous["payload"].get("command_digest")
    if not isinstance(readback,dict) or readback.get("operation_id")!=operation_id or _command_digest(readback.get("command"))!=digest:
        raise NativeContractError("E_NATIVE_RECONCILE_REBIND")
    journal.append("NATIVE_RECONCILED", operation_id, {"readback": readback, "command_digest":digest,"evidence_class": "TEST_ONLY"})
    return {"operation_id": operation_id, "status": "RECONCILED_APPLIED", "result": readback}


@dataclass(frozen=True)
class JournalCursor:
    replica: str
    branch: str
    sequence: int


def observe_journal(cursor, events, observation=None):
    """Observe a bounded clone-local Beads journal without making it evidence.

    A missing sequence, merge/sync/restore gap requires explicit re-baselining;
    journal data is never a replacement for the CM central history chain.
    """
    if not isinstance(cursor, JournalCursor) or cursor.sequence < 0:
        raise NativeContractError("E_JOURNAL_CURSOR")
    if not isinstance(events, list):
        raise NativeContractError("E_JOURNAL_EVENTS")
    if observation is not None and (not isinstance(observation,dict) or observation.get("replica")!=cursor.replica or observation.get("branch")!=cursor.branch):
        return {"status":"GAP_REBASELINE_REQUIRED","reason":"replica/branch identity changed","authoritative":False}
    expected = cursor.sequence + 1
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("seq"), int):
            raise NativeContractError("E_JOURNAL_EVENT")
        if event.get("op") in ("merge","sync","restore"):
            return {"status":"GAP_REBASELINE_REQUIRED","reason":"native head operation requires full snapshot rebaseline","authoritative":False}
        if event["seq"] != expected:
            return {
                "status": "GAP_REBASELINE_REQUIRED", "replica": cursor.replica,
                "branch": cursor.branch, "expected_next_seq": expected,
                "observed_seq": event["seq"], "authoritative": False,
            }
        expected += 1
    return {
        "status": "OBSERVED_NONAUTHORITATIVE", "replica": cursor.replica,
        "branch": cursor.branch, "next_cursor": expected - 1,
        "authoritative": False,
    }
