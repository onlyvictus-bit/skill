"""One-session Dolt CLI adapter for the unqualified practical fence.

It is intentionally not a Beads/native adapter and has no path to activation.
The only mutation entry points accept the strict ordinary-local contract and
invoke one bounded ``dolt sql`` process.  A missing/ambiguous CLI result is
remembered as uncertain so this object will not replay the same write.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import hashlib
from typing import Any, Callable, Mapping

from . import practical_sql
from .practical_contract import (
    ExpiredReacquireRequest,
    GuardedTitleRequest,
    InitialClaimRequest,
    PracticalContractError,
    PracticalSelection,
    TransitionRequest,
    strict_canonical_json,
    validate_digest,
    validate_operation_id,
)


SQL_TIMEOUT_SECONDS = 15
APPROVED_SCRATCH_ROOTS = (Path("C:/Users/sakth/memory-integrity-practical-fence-20261013"),)


class PracticalUncertainDelivery(RuntimeError):
    """The one CLI attempt did not prove a backend result; never retry it."""


def _strict_json_rows(raw: bytes) -> list[dict[str, Any]]:
    if not isinstance(raw, bytes):
        raise PracticalUncertainDelivery("E_PRACTICAL_CAPTURE")
    lines = [line for line in raw.splitlines() if line.strip()]
    if len(lines) != 1:
        raise PracticalUncertainDelivery("E_PRACTICAL_RESULT_SHAPE")

    def pairs(items):
        output: dict[str, Any] = {}
        for key, value in items:
            if key in output:
                raise PracticalUncertainDelivery("E_PRACTICAL_RESULT_DUPLICATE_KEY")
            output[key] = value
        return output

    try:
        value = json.loads(lines[0].decode("utf-8", errors="strict"), object_pairs_hook=pairs,
                           parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()))
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise PracticalUncertainDelivery("E_PRACTICAL_RESULT_JSON") from exc
    if not isinstance(value, dict) or set(value) != {"rows"} or not isinstance(value["rows"], list):
        raise PracticalUncertainDelivery("E_PRACTICAL_RESULT_SHAPE")
    if not all(isinstance(row, dict) for row in value["rows"]):
        raise PracticalUncertainDelivery("E_PRACTICAL_RESULT_SHAPE")
    return value["rows"]


def _strict_json_object(raw: bytes) -> dict[str, Any]:
    rows = _strict_json_rows(raw)
    if len(rows) != 1:
        raise PracticalUncertainDelivery("E_PRACTICAL_RESULT_SHAPE")
    return rows[0]


class PracticalBackend:
    """Strict scratch candidate; neither a generic write capability nor proof."""

    native_write_qualified = False
    evidence_class = "NATIVE_OBSERVED_UNQUALIFIED"
    candidate_route = "APPROVED_SCRATCH_PRACTICAL_CONTRACT"
    mutation_revision_state = "STOPPED_PENDING_REAL_LEASE_V2"

    def __init__(self, selection: PracticalSelection | Mapping[str, Any], *, runner: Callable | None = None):
        self.selection = PracticalSelection.from_value(selection)
        self._runner = runner or self._run_cli
        self._operations: dict[str, dict[str, Any]] = {}

    def activate(self, **_flags: Any) -> bool:
        """Flags cannot promote this candidate into a generic native writer."""
        return False

    def _run_cli(self, argv: list[str], input_bytes: bytes, timeout: int, cwd: str) -> dict[str, Any]:
        from .release_profile import require_native_execution_enabled
        require_native_execution_enabled()
        self._validate_native_boundary()
        completed = subprocess.run(
            argv, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=cwd, timeout=timeout, shell=False, check=False,
        )
        return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}

    def _validate_native_boundary(self) -> None:
        """Check the physical scratch fence immediately before native process use."""
        try:
            root = Path(self.selection.scratch_root).resolve(strict=True)
            executable = Path(self.selection.dolt_executable).resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise PracticalContractError("E_PRACTICAL_NATIVE_PATH") from exc
        if not root.is_dir() or not executable.is_file() or not executable.is_absolute():
            raise PracticalContractError("E_PRACTICAL_NATIVE_PATH")
        approved = False
        for candidate in APPROVED_SCRATCH_ROOTS:
            try:
                root.relative_to(candidate.resolve(strict=True))
                approved = True
                break
            except (ValueError, OSError, RuntimeError):
                continue
        if not approved:
            raise PracticalContractError("E_PRACTICAL_SCRATCH_ROOT")
        digest = hashlib.sha256(executable.read_bytes()).hexdigest()
        if digest != self.selection.dolt_sha256.lower():
            raise PracticalContractError("E_PRACTICAL_DOLT_HASH")

    def _invoke_rows(self, sql: str) -> list[dict[str, Any]]:
        from .release_profile import require_native_execution_enabled
        require_native_execution_enabled()
        if not isinstance(sql, str) or not sql:
            raise PracticalContractError("E_PRACTICAL_SQL")
        argv = [
            self.selection.dolt_executable,
            "--host", "127.0.0.1",
            "--port", str(self.selection.port),
            "--no-tls",
            "--use-db", self.selection.database,
            "--branch", self.selection.main_branch,
            "sql", "-r", "json", "-q", sql,
        ]
        try:
            result = self._runner(argv, b"", SQL_TIMEOUT_SECONDS, self.selection.scratch_root)
        except Exception as exc:
            raise PracticalUncertainDelivery("E_PRACTICAL_PROCESS") from exc
        if not isinstance(result, Mapping) or set(result) != {"returncode", "stdout", "stderr"}:
            raise PracticalUncertainDelivery("E_PRACTICAL_PROCESS_RESULT")
        if result["returncode"] != 0:
            raise PracticalUncertainDelivery("E_PRACTICAL_PROCESS_EXIT")
        return _strict_json_rows(result["stdout"])

    def _invoke(self, sql: str) -> dict[str, Any]:
        rows = self._invoke_rows(sql)
        if len(rows) != 1:
            raise PracticalUncertainDelivery("E_PRACTICAL_RESULT_SHAPE")
        return rows[0]

    def initialize_local_tables(self) -> dict[str, Any]:
        return self._invoke(practical_sql.initialize_local_tables_sql(self.selection))

    def observe(self) -> dict[str, Any]:
        return self._invoke(practical_sql.observe_sql(self.selection))

    def read_task(self, task_id: str) -> dict[str, Any]:
        # Deliberately reuse strict id validation instead of accepting SQL-ish ids.
        return self._invoke(practical_sql.read_task_sql(self.selection, validate_operation_id(task_id)))

    def read_grant(self, grant_id: str) -> dict[str, Any]:
        return self._invoke(practical_sql.read_grant_sql(self.selection, validate_operation_id(grant_id)))

    def read_dependencies(self, task_id: str) -> list[dict[str, Any]]:
        task_id = validate_operation_id(task_id)
        rows = self._invoke_rows(practical_sql.read_dependencies_sql(self.selection, task_id))
        expected = {"id", "issue_id", "depends_on_issue_id", "depends_on_wisp_id", "depends_on_external", "type"}
        for row in rows:
            targets = (row.get("depends_on_issue_id"), row.get("depends_on_wisp_id"), row.get("depends_on_external"))
            if set(row) != expected or row.get("issue_id") != task_id or not isinstance(row.get("id"), str) \
                    or not isinstance(row.get("type"), str) or sum(target is not None for target in targets) != 1:
                raise PracticalUncertainDelivery("E_PRACTICAL_DEPENDENCY_READBACK")
        return [dict(row) for row in rows]

    def _remember_or_refuse(self, operation_id: str, digest: str) -> dict[str, Any] | None:
        previous = self._operations.get(operation_id)
        if previous is None:
            self._operations[operation_id] = {"command_digest": digest, "state": "UNKNOWN"}
            return None
        if previous["command_digest"] != digest:
            raise PracticalContractError("E_PRACTICAL_OPERATION_REBIND")
        if previous["state"] == "UNKNOWN":
            raise PracticalUncertainDelivery("E_PRACTICAL_OPERATION_UNKNOWN_NO_RETRY")
        return dict(previous["receipt"])

    def _receipt(self, request, resulting_row_lock: int, authorization_time_utc: str) -> dict[str, Any]:
        if isinstance(resulting_row_lock, bool) or not isinstance(resulting_row_lock, int) or resulting_row_lock == 0:
            raise PracticalUncertainDelivery("E_PRACTICAL_RESULTING_ROW_LOCK")
        if not isinstance(authorization_time_utc, str) or not authorization_time_utc:
            raise PracticalUncertainDelivery("E_PRACTICAL_AUTHORIZATION_TIME")
        receipt = {
            "schema_version": 1,
            "status": "WORKING_SET_APPLIED",
            "evidence_class": self.evidence_class,
            "native_write_qualified": False,
            "head_committed": False,
            "backend_operation_id": request.operation_id,
            "operation_id": request.operation_id,
            "command_digest": request.command_digest,
            "work_item_id": request.work_item_id,
            "selection_digest": self.selection.digest,
            "store_incarnation": self.selection.incarnation,
            "database": self.selection.database,
            "branch": self.selection.main_branch,
            "native_task_id": request.task_id,
            "actor": request.actor,
            "original_row_lock": request.expected_row_lock,
            "resulting_row_lock": resulting_row_lock,
            "authorization_time_utc": authorization_time_utc,
        }
        if isinstance(request, InitialClaimRequest):
            receipt["new_grant_id"] = request.new_grant_id
            receipt["fresh_authorization_deadline_utc"] = request.fresh_authorization_deadline_utc
        elif isinstance(request, ExpiredReacquireRequest):
            receipt["prior_grant_id"] = request.prior_grant_id
            receipt["prior_deadline_utc"] = request.prior_deadline_utc
            receipt["new_grant_id"] = request.new_grant_id
            receipt["fresh_authorization_deadline_utc"] = request.fresh_authorization_deadline_utc
        else:
            receipt["grant_id"] = request.grant_id
            receipt["fixed_deadline_utc"] = request.fixed_deadline_utc
        return receipt

    def _dispatch(self, request, sql: str) -> dict[str, Any]:
        cached = self._remember_or_refuse(request.operation_id, request.command_digest)
        if cached is not None:
            return cached
        try:
            result = self._invoke(sql)
            if set(result) != {"state", "resulting_row_lock", "authorization_time_utc"} or result["state"] != "WORKING_SET_APPLIED":
                raise PracticalUncertainDelivery("E_PRACTICAL_APPLY_RESULT")
            receipt = self._receipt(request, result["resulting_row_lock"], result["authorization_time_utc"])
        except Exception:
            # The operation identity remains sealed UNKNOWN even for a malformed
            # success-shaped result, because its database effect is not proven.
            self._operations[request.operation_id]["state"] = "UNKNOWN"
            raise
        self._operations[request.operation_id] = {
            "command_digest": request.command_digest,
            "state": "APPLIED",
            "receipt": receipt,
        }
        return dict(receipt)

    def transition(self, value: TransitionRequest | Mapping[str, Any]) -> dict[str, Any]:
        raise PracticalContractError("E_PRACTICAL_LEASE_REVISION_REQUIRED")
        request = TransitionRequest.from_value(value)
        return self._dispatch(request, practical_sql.transition_sql(self.selection, request))

    def guarded_title(self, value: GuardedTitleRequest | Mapping[str, Any]) -> dict[str, Any]:
        raise PracticalContractError("E_PRACTICAL_LEASE_REVISION_REQUIRED")
        request = GuardedTitleRequest.from_value(value)
        return self._dispatch(request, practical_sql.guarded_title_sql(self.selection, request))

    def initial_claim(self, value: InitialClaimRequest | Mapping[str, Any]) -> dict[str, Any]:
        raise PracticalContractError("E_PRACTICAL_LEASE_REVISION_REQUIRED")
        request = InitialClaimRequest.from_value(value)
        return self._dispatch(request, practical_sql.initial_claim_sql(self.selection, request))

    def expired_reacquire(self, value: ExpiredReacquireRequest | Mapping[str, Any]) -> dict[str, Any]:
        raise PracticalContractError("E_PRACTICAL_LEASE_REVISION_REQUIRED")
        request = ExpiredReacquireRequest.from_value(value)
        return self._dispatch(request, practical_sql.expired_reacquire_sql(self.selection, request))

    def read_operation(self, operation_id: str, command_digest: str) -> dict[str, Any]:
        operation_id = validate_operation_id(operation_id)
        command_digest = validate_digest(command_digest)
        row = self._invoke(practical_sql.read_operation_sql(self.selection, operation_id, command_digest))
        # Runtime observation is intentionally strict: callers do not infer an
        # operation from matching title/status or from a reused operation id.
        required = {
            "store_incarnation", "backend_operation_id", "command_digest", "binding_json",
            "receipt_json", "state", "resulting_row_lock",
        }
        if set(row) != required or row["store_incarnation"] != self.selection.incarnation \
                or row["backend_operation_id"] != operation_id or row["command_digest"] != command_digest \
                or row["state"] != "WORKING_SET_APPLIED":
            raise PracticalContractError("E_PRACTICAL_OPERATION_READBACK")
        try:
            binding = json.loads(row["binding_json"])
            receipt = json.loads(row["receipt_json"])
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise PracticalContractError("E_PRACTICAL_OPERATION_READBACK") from exc
        required_binding = {
            "operation_id": operation_id, "backend_operation_id": operation_id,
            "command_digest": command_digest, "selection_digest": self.selection.digest,
            "store_incarnation": self.selection.incarnation, "database": self.selection.database,
            "branch": self.selection.main_branch,
        }
        if not isinstance(binding, dict) or any(binding.get(key) != value for key, value in required_binding.items()):
            raise PracticalContractError("E_PRACTICAL_OPERATION_REBIND")
        if not isinstance(receipt, dict) or receipt.get("operation_id") != operation_id \
                or receipt.get("backend_operation_id") != operation_id \
                or receipt.get("command_digest") != command_digest:
            raise PracticalContractError("E_PRACTICAL_OPERATION_REBIND")
        # Parsing then canonicalizing detects values outside the finite JSON form
        # that the local operation writer is allowed to retain.
        strict_canonical_json(binding)
        strict_canonical_json(receipt)
        return receipt

    def metadata(self) -> dict[str, str]:
        return practical_sql.metadata(self.selection)
