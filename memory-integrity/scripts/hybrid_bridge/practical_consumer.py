"""CM-facing protected consumer for the isolated practical fence.

This module is deliberately a small adapter, not a generic native-write API.
It only accepts a concrete, still-unqualified ``PracticalBackend`` and passes
no caller-created success label or receipt into CM.  CM terminal history is
sealed only after this consumer performs a fresh exact backend operation
readback.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from complete_read_v2 import ledger

from .practical_backend import PracticalBackend
from .practical_contract import GuardedTitleRequest, PracticalContractError


class PracticalConsumerError(ValueError):
    """A local practical-consumer refusal; this is not a qualification state."""


_ROUTE = "APPROVED_SCRATCH_PRACTICAL_CONTRACT"
_OBSERVE_FIELDS = {"database_name", "branch_name", "observed_utc", "requested_incarnation", "selection_digest"}
_TASK_FIELDS = {"id", "title", "status", "assignee", "row_lock"}
_GRANT_FIELDS = {"store_incarnation", "grant_id", "native_task_id", "actor", "status", "fixed_deadline_utc", "issue_revision", "tombstoned"}
_BACKEND_RECEIPT_FIELDS = {
    "schema_version", "status", "evidence_class", "native_write_qualified", "head_committed",
    "backend_operation_id", "operation_id", "command_digest", "work_item_id", "selection_digest",
    "store_incarnation", "database", "branch", "native_task_id", "actor", "grant_id",
    "original_row_lock", "fixed_deadline_utc", "resulting_row_lock", "authorization_time_utc",
}


def _int64_nonzero(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value != 0 and -(2 ** 63) <= value <= 2 ** 63 - 1


def _database_utc(value: Any, code: str) -> datetime:
    if not isinstance(value, str):
        raise PracticalConsumerError(code)
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError as exc:
        raise PracticalConsumerError(code) from exc


class PracticalNativeConsumer:
    """Winner-only CM reservation plus separately observed practical readback."""

    def __init__(self, cm_db, backend: PracticalBackend):
        # The real-lease replacement is still being integrated. Do not let an
        # injected predecessor runner register a fabricated native proof path.
        # Preserve the earlier implementation below as review evidence, not
        # as an executable consumer or a qualified capability.
        raise PracticalConsumerError("E_PRACTICAL_REVISION_STOPPED: real lease v2 required")
        if type(backend) is not PracticalBackend:
            raise PracticalConsumerError("E_PRACTICAL_BACKEND: concrete PracticalBackend required")
        selection = backend.selection
        if backend.native_write_qualified is not False or \
                backend.evidence_class != "NATIVE_OBSERVED_UNQUALIFIED" or \
                backend.candidate_route != _ROUTE or selection.candidate_route != _ROUTE or \
                selection.main_branch != "main":
            raise PracticalConsumerError("E_PRACTICAL_BACKEND: unsupported backend route or qualification")
        self._db = cm_db
        self._backend = backend
        # This is a deliberately private registration seam.  The returned
        # opaque capability is connection-bound and cannot be constructed from
        # a public success/guard dictionary.
        self._reader_registration = ledger._register_practical_native_readback_consumer(cm_db, self)

    def _request(self, value: GuardedTitleRequest | Mapping[str, Any]) -> GuardedTitleRequest:
        try:
            return GuardedTitleRequest.from_value(value)
        except PracticalContractError as exc:
            raise PracticalConsumerError("E_PRACTICAL_REQUEST: exact guarded-title request required") from exc

    def _binding(self, request: GuardedTitleRequest) -> dict[str, Any]:
        selection = self._backend.selection
        return {
            "work_item_id": request.work_item_id,
            "operation_id": request.operation_id,
            "selection_digest": selection.digest,
            "store_incarnation": selection.incarnation,
            "database": selection.database,
            "branch": selection.main_branch,
            "native_task_id": request.task_id,
            "actor": request.actor,
            "grant_id": request.grant_id,
            "original_row_lock": request.expected_row_lock,
            # Preserve the database-UTC string used inside the backend SQL
            # transaction.  It is a binding byte, not a client-time rewrite.
            "fixed_deadline": request.fixed_deadline_utc,
            "command_digest": request.command_digest,
            "backend_operation_id": request.operation_id,
        }

    def _current_prerequisite(self, request: GuardedTitleRequest) -> None:
        """Fail closed before dispatch; backend SQL repeats these predicates atomically."""
        selection = self._backend.selection
        observed = self._backend.observe()
        if not isinstance(observed, dict) or set(observed) != _OBSERVE_FIELDS or \
                observed["database_name"] != selection.database or \
                observed["branch_name"] != selection.main_branch or \
                observed["requested_incarnation"] != selection.incarnation or \
                observed["selection_digest"] != selection.digest:
            raise PracticalConsumerError("E_PRACTICAL_CURRENT_SELECTION: selected local backend is not current")
        observed_utc = _database_utc(observed["observed_utc"], "E_PRACTICAL_CURRENT_SELECTION")
        deadline = _database_utc(request.fixed_deadline_utc, "E_PRACTICAL_CURRENT_GRANT")
        if observed_utc >= deadline:
            raise PracticalConsumerError("E_PRACTICAL_CURRENT_GRANT: database UTC is at or after fixed deadline")
        task = self._backend.read_task(request.task_id)
        if not isinstance(task, dict) or set(task) != _TASK_FIELDS or \
                task["id"] != request.task_id or task["status"] != request.expected_status or \
                task["assignee"] != request.actor or task["row_lock"] != request.expected_row_lock or \
                not _int64_nonzero(task["row_lock"]):
            raise PracticalConsumerError("E_PRACTICAL_CURRENT_TASK: task ownership/revision is no longer current")
        grant = self._backend.read_grant(request.grant_id)
        if not isinstance(grant, dict) or set(grant) != _GRANT_FIELDS or \
                grant["store_incarnation"] != selection.incarnation or grant["grant_id"] != request.grant_id or \
                grant["native_task_id"] != request.task_id or grant["actor"] != request.actor or \
                grant["status"] != request.expected_status or grant["fixed_deadline_utc"] != request.fixed_deadline_utc or \
                grant["issue_revision"] != request.expected_row_lock or grant["tombstoned"] not in (0, False) or \
                not _int64_nonzero(grant["issue_revision"]):
            raise PracticalConsumerError("E_PRACTICAL_CURRENT_GRANT: grant is changed, inactive, or foreign")

    def read_practical_native_operation(self, binding: Mapping[str, Any]) -> dict[str, Any] | None:
        """Private ledger callback: reopen the exact persisted operation receipt."""
        if not isinstance(binding, Mapping):
            raise PracticalConsumerError("E_PRACTICAL_READBACK: binding missing")
        try:
            raw = self._backend.read_operation(binding["backend_operation_id"], binding["command_digest"])
        except Exception:
            # A missing/erroring local backend read is uncertain, not a reason
            # to replay the write.  Return None so CM records UNKNOWN.
            return None
        if isinstance(raw, dict) and raw.get("status") in ("MISSING", "UNKNOWN"):
            return None
        if not isinstance(raw, dict) or set(raw) != _BACKEND_RECEIPT_FIELDS or \
                raw["schema_version"] != 1 or raw["status"] != "WORKING_SET_APPLIED" or \
                raw["evidence_class"] != "NATIVE_OBSERVED_UNQUALIFIED" or \
                raw["native_write_qualified"] is not False or raw["head_committed"] is not False or \
                not _int64_nonzero(raw["resulting_row_lock"]):
            raise PracticalConsumerError("E_PRACTICAL_READBACK: exact persisted working-set receipt required")
        actual = {
            "work_item_id": raw["work_item_id"], "operation_id": raw["operation_id"],
            "selection_digest": raw["selection_digest"], "store_incarnation": raw["store_incarnation"],
            "database": raw["database"], "branch": raw["branch"],
            "native_task_id": raw["native_task_id"], "actor": raw["actor"],
            "grant_id": raw["grant_id"], "original_row_lock": raw["original_row_lock"],
            "fixed_deadline": raw["fixed_deadline_utc"], "command_digest": raw["command_digest"],
            "backend_operation_id": raw["backend_operation_id"],
        }
        if dict(binding) != actual:
            raise PracticalConsumerError("E_PRACTICAL_READBACK: persisted receipt does not match durable CM intent")
        if _database_utc(raw["authorization_time_utc"], "E_PRACTICAL_READBACK") >= \
                _database_utc(raw["fixed_deadline_utc"], "E_PRACTICAL_READBACK"):
            raise PracticalConsumerError("E_PRACTICAL_READBACK: receipt authorization was not before fixed deadline")
        return dict(actual, observed_state="WORKING_SET_APPLIED")

    def dispatch_guarded_title(self, value: GuardedTitleRequest | Mapping[str, Any]) -> dict[str, Any]:
        """Dispatch at most once; a loser/retry can only read the stored operation."""
        request = self._request(value)
        self._current_prerequisite(request)
        binding = self._binding(request)
        reservation = ledger.reserve_practical_native_intent(self._db, binding)
        if not reservation["winner"]:
            return ledger.complete_practical_native_readback(self._db, binding, self._reader_registration)
        try:
            # Do not interpret this caller-visible response as proof.  CM will
            # invoke read_practical_native_operation below against the durable
            # backend operation record.
            self._backend.guarded_title(request)
        except Exception as exc:
            return ledger.mark_practical_native_unknown(
                self._db, reservation["reservation"], "dispatch interrupted: " + type(exc).__name__)
        return ledger.complete_practical_native_readback(
            self._db, binding, self._reader_registration, reservation["reservation"])

    def reconcile_guarded_title(self, value: GuardedTitleRequest | Mapping[str, Any]) -> dict[str, Any]:
        """Read-only recovery: it cannot acquire a winner token or replay SQL."""
        request = self._request(value)
        return ledger.complete_practical_native_readback(
            self._db, self._binding(request), self._reader_registration)
