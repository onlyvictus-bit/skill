"""Generated SQL for the isolated ordinary-local practical fence.

There is deliberately no ``execute_sql`` API.  Each builder accepts a validated
contract object and emits one bounded Dolt SQL batch.  The public backend never
accepts a caller-provided SQL fragment.  The one experiment helper accepts a
typed, bounded pause object so the native race harness can pause *after* the
database timestamp has been sampled without making pauses a production request
feature.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable

from .practical_contract import (
    ExpiredReacquireRequest,
    GuardedTitleRequest,
    InitialClaimRequest,
    PracticalContractError,
    PracticalSelection,
    TransitionRequest,
)


_TABLE_PREFIX = "memory_integrity_practical_"
_LOCAL_TABLES = (
    _TABLE_PREFIX + "grants",
    _TABLE_PREFIX + "grant_history",
    _TABLE_PREFIX + "operations",
    _TABLE_PREFIX + "metadata",
    _TABLE_PREFIX + "token_history",
)


def _text(value: str) -> str:
    """A SQL UTF-8 literal with no quote or comment interpolation surface."""
    if not isinstance(value, str):
        raise PracticalContractError("E_PRACTICAL_SQL_TEXT")
    return "CONVERT(0x" + value.encode("utf-8").hex() + " USING utf8mb4)"


def _int(value: int) -> str:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PracticalContractError("E_PRACTICAL_SQL_INT")
    return str(value)


def _selection(selection: PracticalSelection) -> PracticalSelection:
    return PracticalSelection.from_value(selection)


def _ignore_statements() -> str:
    # Pinned Dolt stores ignore rules in this system table.  This precedes table
    # creation so these local controls cannot enter the Beads working set.
    return "\n".join(
        "INSERT INTO dolt_ignore(pattern, ignored) SELECT " + _text(name) + ", 1 "
        "WHERE NOT EXISTS (SELECT 1 FROM dolt_ignore WHERE pattern = " + _text(name) + ");"
        for name in _LOCAL_TABLES
    )


def initialize_local_tables_sql(selection: PracticalSelection) -> str:
    _selection(selection)
    return "\n".join((
        _ignore_statements(),
        "CREATE TABLE IF NOT EXISTS memory_integrity_practical_metadata ("
        "store_incarnation VARCHAR(192) NOT NULL, metadata_key VARCHAR(96) NOT NULL, "
        "metadata_value LONGTEXT NOT NULL, PRIMARY KEY(store_incarnation, metadata_key));",
        "CREATE TABLE IF NOT EXISTS memory_integrity_practical_grants ("
        "store_incarnation VARCHAR(192) NOT NULL, grant_id VARCHAR(192) NOT NULL, "
        "native_task_id VARCHAR(192) NOT NULL, actor VARCHAR(192) NOT NULL, "
        "status VARCHAR(64) NOT NULL, fixed_deadline_utc DATETIME(6) NOT NULL, "
        "issue_revision BIGINT NOT NULL, tombstoned TINYINT NOT NULL DEFAULT 0, "
        "PRIMARY KEY(store_incarnation, grant_id));",
        "CREATE TABLE IF NOT EXISTS memory_integrity_practical_grant_history ("
        "store_incarnation VARCHAR(192) NOT NULL, grant_id VARCHAR(192) NOT NULL, "
        "event_kind VARCHAR(64) NOT NULL, event_utc DATETIME(6) NOT NULL, "
        "details LONGTEXT NOT NULL, PRIMARY KEY(store_incarnation, grant_id, event_kind, event_utc));",
        "CREATE TABLE IF NOT EXISTS memory_integrity_practical_token_history ("
        "store_incarnation VARCHAR(192) NOT NULL, row_lock_token BIGINT NOT NULL, "
        "operation_id VARCHAR(192) NOT NULL, PRIMARY KEY(store_incarnation, row_lock_token), "
        "UNIQUE KEY practical_token_operation(store_incarnation, operation_id));",
        "CREATE TABLE IF NOT EXISTS memory_integrity_practical_operations ("
        "store_incarnation VARCHAR(192) NOT NULL, backend_operation_id VARCHAR(192) NOT NULL, "
        "command_digest CHAR(64) NOT NULL, binding_json LONGTEXT NOT NULL, receipt_json LONGTEXT NOT NULL, "
        "state VARCHAR(64) NOT NULL, resulting_row_lock BIGINT NOT NULL, "
        "PRIMARY KEY(store_incarnation, backend_operation_id), "
        "UNIQUE KEY practical_operation_digest(store_incarnation, backend_operation_id, command_digest));",
        "INSERT INTO memory_integrity_practical_metadata(store_incarnation, metadata_key, metadata_value) "
        "SELECT " + _text(selection.incarnation) + ", " + _text("selection_digest") + ", " + _text(selection.digest)
        + " WHERE NOT EXISTS (SELECT 1 FROM memory_integrity_practical_metadata WHERE metadata_key = "
        + _text("selection_digest") + " AND metadata_value <> " + _text(selection.digest) + ") "
        "AND NOT EXISTS (SELECT 1 FROM memory_integrity_practical_metadata WHERE store_incarnation = "
        + _text(selection.incarnation) + " AND metadata_key = " + _text("selection_digest") + ");",
    ))


def observe_sql(selection: PracticalSelection) -> str:
    selection = _selection(selection)
    return (
        "SELECT DATABASE() AS database_name, active_branch() AS branch_name, UTC_TIMESTAMP(6) AS observed_utc, "
        + _text(selection.incarnation) + " AS requested_incarnation, "
        + _text(selection.digest) + " AS selection_digest;"
    )


def read_task_sql(selection: PracticalSelection, task_id: str) -> str:
    selection = _selection(selection)
    return (
        "SELECT id, title, status, assignee, row_lock FROM issues WHERE id = " + _text(task_id)
        + " AND DATABASE() = " + _text(selection.database) + " AND active_branch() = " + _text(selection.main_branch) + ";"
    )


def read_grant_sql(selection: PracticalSelection, grant_id: str) -> str:
    selection = _selection(selection)
    return (
        "SELECT store_incarnation, grant_id, native_task_id, actor, status, fixed_deadline_utc, issue_revision, tombstoned "
        "FROM memory_integrity_practical_grants WHERE store_incarnation = " + _text(selection.incarnation)
        + " AND grant_id = " + _text(grant_id) + ";"
    )


def read_dependencies_sql(selection: PracticalSelection, task_id: str) -> str:
    selection = _selection(selection)
    return (
        "SELECT id, issue_id, depends_on_issue_id, depends_on_wisp_id, depends_on_external, type "
        "FROM dependencies WHERE issue_id = " + _text(task_id)
        + " AND DATABASE() = " + _text(selection.database)
        + " AND active_branch() = " + _text(selection.main_branch) + " ORDER BY id;"
    )


def read_operation_sql(selection: PracticalSelection, operation_id: str, command_digest: str) -> str:
    selection = _selection(selection)
    return (
        "SELECT store_incarnation, backend_operation_id, command_digest, binding_json, receipt_json, state, resulting_row_lock "
        "FROM memory_integrity_practical_operations WHERE store_incarnation = " + _text(selection.incarnation)
        + " AND backend_operation_id = " + _text(operation_id)
        + " AND command_digest = " + _text(command_digest) + ";"
    )


def _binding_json(selection: PracticalSelection, request: TransitionRequest) -> str:
    payload = request.as_dict()
    payload.update({
        "selection_digest": selection.digest,
        "store_incarnation": selection.incarnation,
        "database": selection.database,
        "branch": selection.main_branch,
        "native_task_id": request.task_id,
        "original_row_lock": request.expected_row_lock,
        "backend_operation_id": request.operation_id,
    })
    # Request values have already passed strict canonical validation.
    from .practical_contract import strict_canonical_json
    return strict_canonical_json(payload).decode("utf-8")


def _receipt_json(selection: PracticalSelection, request: TransitionRequest) -> str:
    # The generated SQL replaces the final row_lock token after its guarded
    # update.  This static projection pins all immutable identity fields.
    import json
    return json.dumps({
        "schema_version": 1,
        "status": "WORKING_SET_APPLIED",
        "evidence_class": "NATIVE_OBSERVED_UNQUALIFIED",
        "native_write_qualified": False,
        "head_committed": False,
        "backend_operation_id": request.operation_id,
        "operation_id": request.operation_id,
        "command_digest": request.command_digest,
        "work_item_id": request.work_item_id,
        "selection_digest": selection.digest,
        "store_incarnation": selection.incarnation,
        "database": selection.database,
        "branch": selection.main_branch,
        "native_task_id": request.task_id,
        "actor": request.actor,
        "grant_id": request.grant_id,
        "original_row_lock": request.expected_row_lock,
        "fixed_deadline_utc": request.fixed_deadline_utc,
        "resulting_row_lock": "DATABASE_GENERATED",
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _guarded_batch(selection: PracticalSelection, request: TransitionRequest, *, title: str | None,
                   after_auth_statement: str = "") -> str:
    selection = _selection(selection)
    request.validate()
    binding = _binding_json(selection, request)
    receipt = _receipt_json(selection, request)
    set_title = ""
    if title is not None:
        set_title = ", i.title = " + _text(title)
    else:
        # Ordinary protected transitions must not silently translate into a
        # title mutation.  Their visible issue change is ownership + row lock.
        set_title = ""
    common = (
        "i.id = " + _text(request.task_id)
        + " AND i.status = " + _text(request.expected_status)
        + " AND i.assignee = " + _text(request.actor)
        + " AND i.row_lock = " + _int(request.expected_row_lock)
        + " AND i.row_lock <> 0"
        + " AND g.store_incarnation = " + _text(selection.incarnation)
        + " AND g.grant_id = " + _text(request.grant_id)
        + " AND g.native_task_id = " + _text(request.task_id)
        + " AND g.actor = " + _text(request.actor)
        + " AND g.status = " + _text(request.expected_status)
        + " AND g.issue_revision = " + _int(request.expected_row_lock)
        + " AND g.tombstoned = 0"
        + " AND g.fixed_deadline_utc = " + _text(request.fixed_deadline_utc)
        + " AND @practical_auth_now < @practical_original_deadline"
        + " AND DATABASE() = " + _text(selection.database)
        + " AND active_branch() = " + _text(selection.main_branch)
        + " AND NOT EXISTS (SELECT 1 FROM dependencies AS d WHERE d.issue_id = " + _text(request.task_id) + ")"
        + " AND EXISTS (SELECT 1 FROM memory_integrity_practical_metadata AS m WHERE m.store_incarnation = "
        + _text(selection.incarnation) + " AND m.metadata_key = " + _text("selection_digest")
        + " AND m.metadata_value = " + _text(selection.digest) + ")"
    )
    return "\n".join((
        "START TRANSACTION;",
        "SET @practical_auth_now = UTC_TIMESTAMP(6);",
        "SET @practical_original_deadline = " + _text(request.fixed_deadline_utc) + ";",
        # This produces 60 positive random bits, safely inside signed BIGINT.
        "SET @practical_new_row_lock = CAST(CONV(SUBSTRING(SHA2(UUID(), 256), 1, 15), 16, 10) AS SIGNED);",
        "SET @practical_authorized = (SELECT COUNT(*) FROM issues AS i JOIN memory_integrity_practical_grants AS g ON g.native_task_id = i.id WHERE " + common + ");",
        after_auth_statement,
        "INSERT INTO memory_integrity_practical_token_history(store_incarnation, row_lock_token, operation_id) "
        "SELECT " + _text(selection.incarnation) + ", @practical_new_row_lock, " + _text(request.operation_id)
        + " FROM issues AS i JOIN memory_integrity_practical_grants AS g ON g.native_task_id = i.id WHERE " + common + " AND @practical_authorized = 1;",
        "UPDATE issues AS i JOIN memory_integrity_practical_grants AS g ON g.native_task_id = i.id "
        "SET i.assignee = " + _text(request.target_actor) + set_title
        + ", i.row_lock = @practical_new_row_lock, g.issue_revision = @practical_new_row_lock "
        "WHERE " + common + " AND @practical_authorized = 1"
        + " AND EXISTS (SELECT 1 FROM memory_integrity_practical_token_history AS h WHERE h.store_incarnation = "
        + _text(selection.incarnation) + " AND h.row_lock_token = @practical_new_row_lock AND h.operation_id = "
        + _text(request.operation_id) + ");",
        "INSERT INTO memory_integrity_practical_operations(store_incarnation, backend_operation_id, command_digest, binding_json, receipt_json, state, resulting_row_lock) "
        "SELECT " + _text(selection.incarnation) + ", " + _text(request.operation_id) + ", " + _text(request.command_digest)
        + ", " + _text(binding) + ", JSON_SET(CAST(" + _text(receipt) + " AS JSON), '$.authorization_time_utc', @practical_auth_now, '$.resulting_row_lock', @practical_new_row_lock), " + _text("WORKING_SET_APPLIED") + ", @practical_new_row_lock "
        "WHERE ROW_COUNT() = 1;",
        "INSERT INTO memory_integrity_practical_grant_history(store_incarnation, grant_id, event_kind, event_utc, details) "
        "SELECT " + _text(selection.incarnation) + ", " + _text(request.grant_id) + ", " + _text(request.action)
        + ", @practical_auth_now, " + _text(binding) + " WHERE ROW_COUNT() = 1;",
        "COMMIT;",
        "SELECT " + _text("WORKING_SET_APPLIED") + " AS state, @practical_new_row_lock AS resulting_row_lock, @practical_auth_now AS authorization_time_utc "
        "FROM memory_integrity_practical_operations WHERE store_incarnation = " + _text(selection.incarnation)
        + " AND backend_operation_id = " + _text(request.operation_id)
        + " AND command_digest = " + _text(request.command_digest) + ";",
    ))


def transition_sql(selection: PracticalSelection, request: TransitionRequest) -> str:
    return _guarded_batch(selection, request, title=None)


def guarded_title_sql(selection: PracticalSelection, request: GuardedTitleRequest) -> str:
    return _guarded_batch(selection, request, title=request.title)


def _initial_binding(selection: PracticalSelection, request: InitialClaimRequest) -> str:
    from .practical_contract import strict_canonical_json
    value = request.as_dict()
    value.update({
        "selection_digest": selection.digest, "store_incarnation": selection.incarnation,
        "database": selection.database, "branch": selection.main_branch,
        "native_task_id": request.task_id, "original_row_lock": request.expected_row_lock,
        "backend_operation_id": request.operation_id,
    })
    return strict_canonical_json(value).decode("utf-8")


def _dynamic_receipt_sql(selection: PracticalSelection, request, *, prior: bool = False) -> str:
    values = [
        "'schema_version', 1", "'status', 'WORKING_SET_APPLIED'",
        "'evidence_class', 'NATIVE_OBSERVED_UNQUALIFIED'", "'native_write_qualified', FALSE",
        "'head_committed', FALSE", "'backend_operation_id', " + _text(request.operation_id),
        "'operation_id', " + _text(request.operation_id), "'command_digest', " + _text(request.command_digest),
        "'work_item_id', " + _text(request.work_item_id), "'selection_digest', " + _text(selection.digest),
        "'store_incarnation', " + _text(selection.incarnation), "'database', " + _text(selection.database),
        "'branch', " + _text(selection.main_branch), "'native_task_id', " + _text(request.task_id),
        "'actor', " + _text(request.actor), "'original_row_lock', " + _int(request.expected_row_lock),
        "'resulting_row_lock', @practical_new_row_lock", "'authorization_time_utc', @practical_auth_now",
    ]
    if prior:
        values.extend(("'prior_grant_id', " + _text(request.prior_grant_id),
                       "'prior_deadline_utc', " + _text(request.prior_deadline_utc),
                       "'fresh_authorization_deadline_utc', " + _text(request.fresh_authorization_deadline_utc)))
    else:
        values.extend(("'new_grant_id', " + _text(request.new_grant_id),
                       "'fresh_authorization_deadline_utc', " + _text(request.fresh_authorization_deadline_utc)))
    return "JSON_OBJECT(" + ", ".join(values) + ")"


def initial_claim_sql(selection: PracticalSelection, request: InitialClaimRequest) -> str:
    """First grant from a real open/unassigned task; no raw grant seed exists."""
    selection = _selection(selection)
    request.validate()
    where = (
        "i.id = " + _text(request.task_id) + " AND i.status = " + _text(request.expected_status)
        + " AND i.assignee IS NULL AND i.row_lock = " + _int(request.expected_row_lock)
        + " AND i.row_lock <> 0 AND @practical_auth_now < @practical_fresh_authorization_deadline"
        + " AND DATABASE() = " + _text(selection.database)
        + " AND active_branch() = " + _text(selection.main_branch)
    )
    binding = _initial_binding(selection, request)
    receipt = _dynamic_receipt_sql(selection, request)
    return "\n".join((
        "START TRANSACTION;",
        "SET @practical_auth_now = UTC_TIMESTAMP(6);",
        "SET @practical_fresh_authorization_deadline = " + _text(request.fresh_authorization_deadline_utc) + ";",
        "SET @practical_new_row_lock = CAST(CONV(SUBSTRING(SHA2(UUID(), 256), 1, 15), 16, 10) AS SIGNED);",
        "INSERT INTO memory_integrity_practical_token_history(store_incarnation, row_lock_token, operation_id) "
        "SELECT " + _text(selection.incarnation) + ", @practical_new_row_lock, " + _text(request.operation_id)
        + " FROM issues AS i WHERE " + where + ";",
        "UPDATE issues AS i SET i.assignee = " + _text(request.actor)
        + ", i.status = " + _text("in_progress") + ", i.row_lock = @practical_new_row_lock WHERE " + where
        + " AND EXISTS (SELECT 1 FROM memory_integrity_practical_token_history AS h WHERE h.store_incarnation = "
        + _text(selection.incarnation) + " AND h.row_lock_token = @practical_new_row_lock AND h.operation_id = "
        + _text(request.operation_id) + ");",
        "INSERT INTO memory_integrity_practical_grants(store_incarnation, grant_id, native_task_id, actor, status, fixed_deadline_utc, issue_revision, tombstoned) "
        "SELECT " + _text(selection.incarnation) + ", " + _text(request.new_grant_id) + ", " + _text(request.task_id)
        + ", " + _text(request.actor) + ", " + _text("in_progress") + ", " + _text(request.new_deadline_utc)
        + ", @practical_new_row_lock, 0 WHERE ROW_COUNT() = 1;",
        "INSERT INTO memory_integrity_practical_operations(store_incarnation, backend_operation_id, command_digest, binding_json, receipt_json, state, resulting_row_lock) "
        "SELECT " + _text(selection.incarnation) + ", " + _text(request.operation_id) + ", " + _text(request.command_digest)
        + ", " + _text(binding) + ", " + receipt + ", " + _text("WORKING_SET_APPLIED") + ", @practical_new_row_lock "
        "WHERE EXISTS (SELECT 1 FROM memory_integrity_practical_grants AS g WHERE g.store_incarnation = "
        + _text(selection.incarnation) + " AND g.grant_id = " + _text(request.new_grant_id)
        + " AND g.issue_revision = @practical_new_row_lock AND g.tombstoned = 0);",
        "INSERT INTO memory_integrity_practical_grant_history(store_incarnation, grant_id, event_kind, event_utc, details) "
        "SELECT " + _text(selection.incarnation) + ", " + _text(request.new_grant_id) + ", " + _text("initial_claim")
        + ", @practical_auth_now, " + _text(binding) + " WHERE ROW_COUNT() = 1;",
        "COMMIT;",
        "SELECT " + _text("WORKING_SET_APPLIED") + " AS state, @practical_new_row_lock AS resulting_row_lock, "
        "@practical_auth_now AS authorization_time_utc FROM memory_integrity_practical_operations WHERE store_incarnation = "
        + _text(selection.incarnation) + " AND backend_operation_id = " + _text(request.operation_id)
        + " AND command_digest = " + _text(request.command_digest) + ";",
    ))


def expired_reacquire_sql(selection: PracticalSelection, request: ExpiredReacquireRequest) -> str:
    """New authorization after a prior grant expired; never renews the old op."""
    selection = _selection(selection)
    request.validate()
    from .practical_contract import strict_canonical_json
    binding_value = request.as_dict()
    binding_value.update({
        "selection_digest": selection.digest, "store_incarnation": selection.incarnation,
        "database": selection.database, "branch": selection.main_branch,
        "native_task_id": request.task_id, "original_row_lock": request.expected_row_lock,
        "backend_operation_id": request.operation_id,
    })
    binding = strict_canonical_json(binding_value).decode("utf-8")
    receipt = _dynamic_receipt_sql(selection, request, prior=True)
    prior_where = (
        "i.id = " + _text(request.task_id) + " AND i.status = " + _text(request.expected_status)
        + " AND i.row_lock = " + _int(request.expected_row_lock) + " AND i.row_lock <> 0"
        + " AND g.store_incarnation = " + _text(selection.incarnation)
        + " AND g.grant_id = " + _text(request.prior_grant_id)
        + " AND g.native_task_id = " + _text(request.task_id)
        + " AND g.actor = " + _text(request.actor)
        + " AND g.issue_revision = " + _int(request.expected_row_lock)
        + " AND g.fixed_deadline_utc = " + _text(request.prior_deadline_utc)
        + " AND g.tombstoned = 0"
        + " AND @practical_auth_now >= @practical_prior_deadline"
        + " AND @practical_auth_now < @practical_fresh_authorization_deadline"
        + " AND DATABASE() = " + _text(selection.database)
        + " AND active_branch() = " + _text(selection.main_branch)
    )
    return "\n".join((
        "START TRANSACTION;",
        "SET @practical_auth_now = UTC_TIMESTAMP(6);",
        "SET @practical_prior_deadline = " + _text(request.prior_deadline_utc) + ";",
        "SET @practical_fresh_authorization_deadline = " + _text(request.fresh_authorization_deadline_utc) + ";",
        "SET @practical_new_row_lock = CAST(CONV(SUBSTRING(SHA2(UUID(), 256), 1, 15), 16, 10) AS SIGNED);",
        "INSERT INTO memory_integrity_practical_token_history(store_incarnation, row_lock_token, operation_id) "
        "SELECT " + _text(selection.incarnation) + ", @practical_new_row_lock, " + _text(request.operation_id)
        + " FROM issues AS i JOIN memory_integrity_practical_grants AS g ON g.native_task_id = i.id WHERE " + prior_where + ";",
        "UPDATE issues AS i JOIN memory_integrity_practical_grants AS g ON g.native_task_id = i.id "
        "SET i.assignee = " + _text(request.target_actor) + ", i.status = " + _text("in_progress")
        + ", i.row_lock = @practical_new_row_lock, g.tombstoned = 1 WHERE " + prior_where
        + " AND EXISTS (SELECT 1 FROM memory_integrity_practical_token_history AS h WHERE h.store_incarnation = "
        + _text(selection.incarnation) + " AND h.row_lock_token = @practical_new_row_lock AND h.operation_id = "
        + _text(request.operation_id) + ");",
        "INSERT INTO memory_integrity_practical_grants(store_incarnation, grant_id, native_task_id, actor, status, fixed_deadline_utc, issue_revision, tombstoned) "
        "SELECT " + _text(selection.incarnation) + ", " + _text(request.new_grant_id) + ", " + _text(request.task_id)
        + ", " + _text(request.target_actor) + ", " + _text("in_progress") + ", " + _text(request.new_deadline_utc)
        + ", @practical_new_row_lock, 0 WHERE ROW_COUNT() = 1;",
        "INSERT INTO memory_integrity_practical_operations(store_incarnation, backend_operation_id, command_digest, binding_json, receipt_json, state, resulting_row_lock) "
        "SELECT " + _text(selection.incarnation) + ", " + _text(request.operation_id) + ", " + _text(request.command_digest)
        + ", " + _text(binding) + ", " + receipt + ", " + _text("WORKING_SET_APPLIED") + ", @practical_new_row_lock "
        "WHERE EXISTS (SELECT 1 FROM memory_integrity_practical_grants AS g WHERE g.store_incarnation = "
        + _text(selection.incarnation) + " AND g.grant_id = " + _text(request.new_grant_id)
        + " AND g.issue_revision = @practical_new_row_lock AND g.tombstoned = 0);",
        "INSERT INTO memory_integrity_practical_grant_history(store_incarnation, grant_id, event_kind, event_utc, details) "
        "SELECT " + _text(selection.incarnation) + ", " + _text(request.prior_grant_id) + ", " + _text("expired_reacquire")
        + ", @practical_auth_now, " + _text(binding) + " WHERE ROW_COUNT() = 1;",
        "COMMIT;",
        "SELECT " + _text("WORKING_SET_APPLIED") + " AS state, @practical_new_row_lock AS resulting_row_lock, "
        "@practical_auth_now AS authorization_time_utc FROM memory_integrity_practical_operations WHERE store_incarnation = "
        + _text(selection.incarnation) + " AND backend_operation_id = " + _text(request.operation_id)
        + " AND command_digest = " + _text(request.command_digest) + ";",
    ))


@dataclass(frozen=True)
class HarnessPauseBarrier:
    """Harness-only timing aid; absent from all public mutation request shapes."""
    seconds: Decimal

    @classmethod
    def from_seconds(cls, value: int | str | Decimal) -> "HarnessPauseBarrier":
        try:
            seconds = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise PracticalContractError("E_PRACTICAL_BARRIER") from exc
        if not Decimal("0") < seconds <= Decimal("30"):
            raise PracticalContractError("E_PRACTICAL_BARRIER")
        return cls(seconds)

    def sql(self) -> str:
        return "DO SLEEP(" + format(self.seconds, "f") + ");"


def experiment_guarded_title_sql(selection: PracticalSelection, request: GuardedTitleRequest,
                                 *, pause_barrier: HarnessPauseBarrier) -> str:
    """Build the same production transaction plus a typed test-only pause."""
    if not isinstance(pause_barrier, HarnessPauseBarrier):
        raise PracticalContractError("E_PRACTICAL_BARRIER")
    return _guarded_batch(selection, request, title=request.title,
                          after_auth_statement=pause_barrier.sql())


def metadata(selection: PracticalSelection) -> dict[str, str]:
    """Read-only SQL catalogue for the native pause experiment controller."""
    selection = _selection(selection)
    return {
        "initialize_local_tables": initialize_local_tables_sql(selection),
        "observe": observe_sql(selection),
        "read_task": read_task_sql(selection, "PRACTICAL_TASK_ID"),
        "read_grant": read_grant_sql(selection, "PRACTICAL_GRANT_ID"),
        "read_operation": read_operation_sql(selection, "PRACTICAL_OPERATION_ID", "0" * 64),
    }
