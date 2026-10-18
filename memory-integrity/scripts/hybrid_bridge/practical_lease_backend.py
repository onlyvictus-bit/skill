"""Sealed, experimental lease-bound Dolt transport for the approved scratch pilot.

This is not an activated native writer or the stopped predecessor's fallback.
One durable CM dispatch consumption is required before a title mutation. A
receipt stays unqualified; only a separately integrated protected consumer can
complete CM history. Native transaction/rollback/crash behavior is UNVERIFIED.
Python introspection, module monkeypatching and DB administration are outside
the ordinary-public-API boundary, as in the companion's capability contract.
"""
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import ClassVar

from .practical_contract import (LeasePracticalSelection, LeaseGuardedTitleRequest,
                                 LeaseReassignRequest,
                                 PracticalContractError, strict_canonical_json)
from .practical_sql import _text
from . import practical_lease_sql

DOLT_PIN = 'ca21a9d1dab233a694b99ad0be9e78590967a1cc2773eb202fa0dd2929239ba2'
# Fixed, source-recorded observation marker. It is attached only to the bounded
# pause of the paused-title capability, carries no predicate and no authority,
# and exists so a second session can observe which session is holding the
# transaction open. It must be in the SQL that actually executes: a marker on a
# separate copy would let the watcher search for something that never ran.
PAUSE_BARRIER_MARKER = 'PRACTICAL_RACE_BARRIER'
APPROVED_ROOTS = (Path('C:/Users/sakth/memory-integrity-practical-fence-20261013'),
                  Path('C:/Users/sakth/memory-integrity-scratch-20261011/practical-fence-20261013'))
TIMEOUT_SECONDS = 15
MAX_CAPTURE_BYTES = 1024 * 1024


def _mark_pause(sql):
    """Attach the fixed observation marker to the bounded pause.

    Bounded and idempotent: it only touches the parentheses of the pause
    statement, adds no clause, and never runs twice.
    """
    if PAUSE_BARRIER_MARKER in sql:
        return sql
    for statement in ('DO SLEEP(', 'SLEEP('):
        index = sql.find(statement)
        if index < 0:
            continue
        end = sql.find(')', index)
        if end < 0:
            break
        return sql[:end + 1] + ' /* ' + PAUSE_BARRIER_MARKER + ' */' + sql[end + 1:]
    raise LeaseDeliveryUnknown('E_MI2_PAUSE_MARKER: no bounded pause to mark')


class LeaseDeliveryUnknown(RuntimeError):
    """Uncertain transport/readback; never grants permission to retry mutation."""


def _native_boundary(selection):
    from .native_observation import _ordinary
    if os.name != 'nt':
        raise PracticalContractError('E_MI2_WINDOWS_HOST')
    try:
        root = _ordinary(Path(selection.scratch_root), directory=True)
        executable = _ordinary(Path(selection.dolt_executable))
        allowed = any(root != candidate.resolve() and root.is_relative_to(candidate.resolve())
                      for candidate in APPROVED_ROOTS)
        if not allowed:
            raise PracticalContractError('E_MI2_SCRATCH_ROOT')
        # Retain the initialized physical Beads gate, not a guessed workspace.
        _ordinary(root / '.beads.gate.lock')
        _ordinary(root / '.beads', directory=True)
        if executable.name.lower() != 'dolt.exe' or hashlib.sha256(executable.read_bytes()).hexdigest() != DOLT_PIN:
            raise PracticalContractError('E_MI2_DOLT_PIN')
    except (OSError, RuntimeError) as exc:
        raise PracticalContractError('E_MI2_NATIVE_BOUNDARY') from exc


def _pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise LeaseDeliveryUnknown('E_MI2_DUPLICATE_JSON_KEY')
        out[key] = value
    return out


def _object(text):
    try:
        value = json.loads(text, object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        strict_canonical_json(value)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise LeaseDeliveryUnknown('E_MI2_JSON') from exc
    if not isinstance(value, dict):
        raise LeaseDeliveryUnknown('E_MI2_JSON_OBJECT')
    return value


def _rows(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_CAPTURE_BYTES:
        raise LeaseDeliveryUnknown('E_MI2_CAPTURE')
    try:
        text = raw.decode('utf-8', 'strict')
        decoder = json.JSONDecoder(object_pairs_hook=_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        cursor, sets = 0, []
        while cursor < len(text):
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            if cursor == len(text):
                break
            value, cursor = decoder.raw_decode(text, cursor)
            if value == {}:
                continue  # Pinned SQL CLI empty non-query result packet.
            if not isinstance(value, dict) or set(value) != {'rows'} or not isinstance(value['rows'], list):
                raise LeaseDeliveryUnknown('E_MI2_RESULT_SHAPE')
            if not all(isinstance(row, dict) for row in value['rows']):
                raise LeaseDeliveryUnknown('E_MI2_RESULT_SHAPE')
            sets.append(value['rows'])
        if len(sets) != 1:
            raise LeaseDeliveryUnknown('E_MI2_RESULT_SETS')
        return sets[0]
    except (UnicodeError, ValueError) as exc:
        raise LeaseDeliveryUnknown('E_MI2_RESULT_JSON') from exc


def _utc(value):
    if not isinstance(value, str):
        raise LeaseDeliveryUnknown('E_MI2_RESULT_TIME')
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError as exc:
        raise LeaseDeliveryUnknown('E_MI2_RESULT_TIME') from exc


def _token(value):
    return type(value) is int and value != 0 and -(2**63) <= value < 2**63


def _parse_request(value):
    """Accept exactly the two lease-bound request contracts, nothing else."""
    if isinstance(value, LeaseReassignRequest) or (
            not isinstance(value, LeaseGuardedTitleRequest)
            and isinstance(value, dict) and value.get('action') == 'reassign_title_lease'):
        return LeaseReassignRequest.from_value(value)
    return LeaseGuardedTitleRequest.from_value(value)


@dataclass(frozen=True, slots=True, init=False)
class LeaseScratchBackend:
    """Pinned low-level candidate; no injectable runner, mutable reader or activation."""
    _selection: LeasePracticalSelection
    native_write_qualified: ClassVar[bool] = False
    evidence_class: ClassVar[str] = 'NATIVE_OBSERVED_UNQUALIFIED'
    candidate_route: ClassVar[str] = 'APPROVED_SCRATCH_PRACTICAL_CONTRACT'

    def __init__(self, selection):
        selected = LeasePracticalSelection.from_value(selection)
        if Path(selected.dolt_executable).name.lower() != 'dolt.exe':
            raise PracticalContractError('E_MI2_DOLT_EXECUTABLE')
        if selected.dolt_sha256.lower() != DOLT_PIN:
            raise PracticalContractError('E_MI2_DOLT_PIN')
        object.__setattr__(self, '_selection', selected)

    @property
    def selection(self):
        return self._selection

    def activate(self, **_flags):
        return False

    def intent_binding(self, value):
        request = _parse_request(value)
        if request.lease_granted_node != self.selection.native_node_id:
            raise PracticalContractError('E_MI2_FOREIGN_LEASE_NODE')
        binding = dict(work_item_id=request.work_item_id, operation_id=request.operation_id,
                    selection_digest=self.selection.digest, store_incarnation=self.selection.incarnation,
                    database=self.selection.database, branch='main', native_task_id=request.task_id,
                    actor=request.actor, grant_id=request.grant_id, original_row_lock=request.expected_row_lock,
                    fixed_deadline=request.fixed_deadline_utc, command_digest=request.command_digest,
                    backend_operation_id=request.operation_id, lease_holder=request.lease_holder,
                    lease_granted_node=request.lease_granted_node,
                    lease_granted_at_utc=request.lease_granted_at_utc,
                    lease_expires_at_utc=request.lease_expires_at_utc,
                    lease_heartbeat_at_utc=request.lease_heartbeat_at_utc)
        if isinstance(request, LeaseReassignRequest):
            binding.update(target_actor=request.target_actor, new_grant_id=request.new_grant_id)
        return binding

    def _invoke(self, sql, *, timeout=TIMEOUT_SECONDS):
        if type(self) is not LeaseScratchBackend:
            raise PracticalContractError('E_MI2_BACKEND_TYPE')
        _native_boundary(self.selection)
        argv = [self.selection.dolt_executable, '--host', '127.0.0.1', '--port', str(self.selection.port),
                '--no-tls', '--use-db', self.selection.database, '--branch', 'main',
                'sql', '-r', 'json', '-q', sql]
        env = {key:value for key,value in os.environ.items()
               if key.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','COMSPEC'}}
        env.update(DOLT_DISABLE_EVENT_FLUSH='1', NO_COLOR='1',
                   DOLT_ROOT_PATH=str(Path(self.selection.scratch_root)/'.practical-dolt-config'))
        try:
            result = subprocess.run(argv, cwd=self.selection.scratch_root, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
                shell=False, check=False, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        except Exception as exc:
            raise LeaseDeliveryUnknown('E_MI2_PROCESS') from exc
        if result.returncode != 0 or not isinstance(result.stderr,bytes) or result.stderr.strip():
            raise LeaseDeliveryUnknown('E_MI2_PROCESS_RESULT')
        return _rows(result.stdout)

    def _receipt(self, request, row):
        fields = {'binding_json','receipt_json','command_digest','authorization_time','resulting_row_lock'}
        if not isinstance(row,dict) or set(row) != fields or row['command_digest'] != request.command_digest:
            raise LeaseDeliveryUnknown('E_MI2_RECEIPT_ROW')
        binding = request.as_dict()
        binding.update(selection_digest=self.selection.digest, store_incarnation=self.selection.incarnation,
                       database=self.selection.database, branch='main', native_node_id=self.selection.native_node_id)
        if strict_canonical_json(_object(row['binding_json'])) != strict_canonical_json(binding):
            raise LeaseDeliveryUnknown('E_MI2_RECEIPT_BINDING')
        receipt = _object(row['receipt_json'])
        expected = dict(binding,status='WORKING_SET_APPLIED',evidence_class=self.evidence_class,
                        native_write_qualified=False,head_committed=False,
                        backend_operation_id=request.operation_id,native_task_id=request.task_id,
                        original_row_lock=request.expected_row_lock,fixed_deadline_utc=request.fixed_deadline_utc,
                        authorization_time_utc=row['authorization_time'],resulting_row_lock=row['resulting_row_lock'])
        if isinstance(request, LeaseReassignRequest):
            # Original digest-bound facts stay verbatim in the binding above;
            # the transfer outcome lives under separately named resulting
            # fields. The heartbeat value itself comes from the stored row,
            # so the check below pins its exact transfer-time relationship
            # instead of trusting an echo of the receipt field.
            heartbeat_text = receipt.get('resulting_lease_heartbeat_at_utc')
            try:
                transferred = datetime.strptime(heartbeat_text, '%Y-%m-%d %H:%M:%S.%f')
            except (TypeError, ValueError) as exc:
                raise LeaseDeliveryUnknown('E_MI2_RECEIPT_HEARTBEAT') from exc
            if transferred.microsecond != 0:
                raise LeaseDeliveryUnknown('E_MI2_RECEIPT_HEARTBEAT')
            # The builder renders CAST(auth AS DATETIME): MySQL truncates the
            # fractional part, it never rounds. Runtime truncation behavior
            # stays unverified until observed against a live server.
            if transferred != _utc(row['authorization_time']).replace(microsecond=0):
                raise LeaseDeliveryUnknown('E_MI2_RECEIPT_HEARTBEAT')
            expected.update(prior_grant_id=request.grant_id, new_grant_id=request.new_grant_id,
                            target_actor=request.target_actor,
                            resulting_lease_heartbeat_at_utc=receipt.get('resulting_lease_heartbeat_at_utc'))
            if not _utc(request.lease_granted_at_utc) <= transferred:
                raise LeaseDeliveryUnknown('E_MI2_RECEIPT_TRANSFER')
        if set(receipt) != set(expected) or strict_canonical_json(receipt) != strict_canonical_json(expected) or \
                receipt.get('native_write_qualified') is not False or receipt.get('head_committed') is not False or \
                not _token(row['resulting_row_lock']) or row['resulting_row_lock'] == request.expected_row_lock:
            raise LeaseDeliveryUnknown('E_MI2_RECEIPT_BINDING')
        if not _utc(request.lease_granted_at_utc) <= _utc(row['authorization_time']) < _utc(request.fixed_deadline_utc):
            raise LeaseDeliveryUnknown('E_MI2_RECEIPT_AUTHORIZATION')
        return receipt

    def _execute_protected(self, request, cm_db, reservation, *, sql, timeout):
        """The one protected dispatch path: reserve, consume, run, read back.

        Reservation-before-dispatch, winner-only consumption, exact receipt
        validation and the APPLIED-or-UNKNOWN outcome are identical for every
        protected action, so the title, paused-title and transfer dispatches
        share this body rather than three drifting copies.
        """
        from complete_read_v2 import ledger
        binding = self.intent_binding(request)
        # Refuse bogus capability and unsafe path before consuming the attempt.
        ledger._practical_owner(reservation,cm_db,binding)
        _native_boundary(self.selection)
        claimed = ledger.consume_practical_native_dispatch(cm_db,binding,reservation)
        if not claimed['dispatch']:
            raise PracticalContractError('E_MI2_OPERATION_READBACK_ONLY')
        try:
            rows = LeaseScratchBackend._invoke(self,sql,timeout=timeout)
            if len(rows) != 1:
                raise LeaseDeliveryUnknown('E_MI2_RECEIPT_ABSENT')
            receipt = LeaseScratchBackend._receipt(self,request,rows[0])
        except Exception as exc:
            ledger.mark_practical_native_unknown(cm_db,reservation,'lease dispatch uncertain: '+type(exc).__name__)
            if isinstance(exc,LeaseDeliveryUnknown):
                raise
            raise LeaseDeliveryUnknown('E_MI2_DELIVERY_UNKNOWN') from exc
        # This low-level transport does not register a caller-provided reader or
        # fabricate CM APPLIED. Integrated consumer readback remains a P3 gate.
        ledger.mark_practical_native_unknown(cm_db,reservation,
            'working-set receipt observed; integrated protected readback still required')
        return receipt

    def execute_guarded_title(self, value, *, cm_db, reservation):
        if type(self) is not LeaseScratchBackend:
            raise PracticalContractError('E_MI2_BACKEND_TYPE')
        request = LeaseGuardedTitleRequest.from_value(value)
        return self._execute_protected(
            request, cm_db, reservation,
            sql=practical_lease_sql.guarded_title_sql(self.selection, request),
            timeout=TIMEOUT_SECONDS)

    def execute_paused_guarded_title(self, value, *, cm_db, reservation, pause_seconds):
        """Harness support: the same protected title dispatch with a bounded
        observation pause inside the open transaction.

        This exists so the race harness can watch a real authorization
        snapshot rather than assume one. It is deliberately not a SQL
        injection point: the batch is derived here from the validated request
        and a bounded pause, no caller text reaches the store, and the
        reservation, consumption, receipt and UNKNOWN handling are the same
        protected path as every other dispatch.
        """
        if type(self) is not LeaseScratchBackend:
            raise PracticalContractError('E_MI2_BACKEND_TYPE')
        if type(pause_seconds) is not int or not 1 <= pause_seconds <= 30:
            raise PracticalContractError('E_MI2_PAUSE_BOUNDS')
        request = LeaseGuardedTitleRequest.from_value(value)
        sql = practical_lease_sql.experiment_guarded_title_sql(
            self.selection, request, pause_seconds=pause_seconds)
        # The marker must be inside the statement that executes, otherwise the
        # watcher's session search can never match the real session.
        sql = _mark_pause(sql)
        # The pause legitimately outlives the ordinary transport budget, so the
        # bound is the pause plus the ordinary margin and nothing more.
        return self._execute_protected(
            request, cm_db, reservation, sql=sql, timeout=TIMEOUT_SECONDS + pause_seconds)

    def execute_reassign_title(self, value, *, cm_db, reservation):
        """Ownership-transfer dispatch: same winner/consumption/readback shape
        as title dispatch, but through the reassign batch and receipt."""
        from complete_read_v2 import ledger
        if type(self) is not LeaseScratchBackend:
            raise PracticalContractError('E_MI2_BACKEND_TYPE')
        request = LeaseReassignRequest.from_value(value)
        binding = self.intent_binding(request)
        # Refuse bogus capability and unsafe path before consuming the attempt.
        ledger._practical_owner(reservation,cm_db,binding)
        _native_boundary(self.selection)
        claimed = ledger.consume_practical_native_dispatch(cm_db,binding,reservation)
        if not claimed['dispatch']:
            raise PracticalContractError('E_MI2_OPERATION_READBACK_ONLY')
        try:
            rows = LeaseScratchBackend._invoke(self,practical_lease_sql.reassign_title_sql(self.selection,request))
            if len(rows) != 1:
                raise LeaseDeliveryUnknown('E_MI2_RECEIPT_ABSENT')
            receipt = LeaseScratchBackend._receipt(self,request,rows[0])
        except Exception as exc:
            ledger.mark_practical_native_unknown(cm_db,reservation,'lease dispatch uncertain: '+type(exc).__name__)
            if isinstance(exc,LeaseDeliveryUnknown):
                raise
            raise LeaseDeliveryUnknown('E_MI2_DELIVERY_UNKNOWN') from exc
        # This low-level transport does not register a caller-provided reader or
        # fabricate CM APPLIED. Integrated consumer readback remains a P3 gate.
        ledger.mark_practical_native_unknown(cm_db,reservation,
            'working-set receipt observed; integrated protected readback still required')
        return receipt

    def read_current_authority(self, value):
        """SELECT-only snapshot of the current issue/lease/grant/pointer state.

        A precheck never replaces the database transaction fence; it only lets
        a consumer refuse before reserving execution authority. Exactly one
        row must exist: zero means stale or missing, several means ambiguous.
        """
        request = _parse_request(value)
        if type(self) is not LeaseScratchBackend:
            raise PracticalContractError('E_MI2_BACKEND_TYPE')
        selected = self.selection
        namespace = _text(selected.incarnation)
        task = _text(request.task_id)
        database = _text(selected.database)
        sql = ('SELECT i.id AS issue_id,i.title AS issue_title,i.status AS issue_status,'
               'i.assignee AS assignee,i.row_lock AS issue_row_lock,i.ephemeral AS ephemeral,'
               'l.holder AS holder,l.granted_node AS granted_node,'
               'l.granted_at AS granted_at,l.lease_expires_at AS lease_expires_at,'
               'l.heartbeat_at AS heartbeat_at,'
               'g.grant_id AS grant_id,g.actor AS grant_actor,g.status AS grant_status,'
               'g.fixed_deadline_utc AS fixed_deadline_utc,g.issue_revision AS issue_revision,'
               'g.tombstoned AS tombstoned,g.lease_node AS lease_node,'
               'g.lease_granted_at AS lease_granted_at,g.lease_expiry AS lease_expiry,'
               'g.lease_heartbeat AS lease_heartbeat,'
               'c.current_revision AS current_revision,'
               'm.selection_digest AS selection_digest,m.native_node_id AS native_node_id,'
               'm.selected_database AS selected_database,m.selected_main_branch AS selected_main_branch,'
               'UTC_TIMESTAMP(6) AS observed_utc '
               'FROM issues AS i JOIN leases AS l ON l.issue_id=i.id '
               'JOIN mi_practical_v2_current_grants AS c ON c.store_incarnation=' + namespace
               + ' AND c.task_id=i.id '
               'JOIN mi_practical_v2_grants AS g ON g.store_incarnation=c.store_incarnation '
               'AND g.grant_id=c.grant_id AND g.task_id=c.task_id '
               'JOIN mi_practical_v2_metadata AS m ON m.store_incarnation=c.store_incarnation '
               "AND m.namespace_key='identity' WHERE BINARY i.id=BINARY " + task
               + ' AND DATABASE() IN (' + database + ",CONCAT(" + database + ",'/main'))"
               + " AND active_branch()='main';")
        rows = LeaseScratchBackend._invoke(self, sql)
        if not rows:
            raise LeaseDeliveryUnknown('E_MI2_AUTHORITY_ABSENT')
        if len(rows) != 1:
            raise LeaseDeliveryUnknown('E_MI2_AUTHORITY_CARDINALITY')
        return rows[0]

    def read_operation(self, value):
        request = _parse_request(value)
        self.intent_binding(request)
        selected = self.selection
        sql = ('SELECT o.receipt_json,o.binding_json,o.command_digest,o.authorization_time,o.resulting_row_lock '
               'FROM mi_practical_v2_operations AS o JOIN mi_practical_v2_metadata AS m '
               'ON m.store_incarnation=o.store_incarnation WHERE '
               'BINARY o.store_incarnation=BINARY '+_text(selected.incarnation)
               +' AND BINARY o.operation_id=BINARY '+_text(request.operation_id)
               +' AND BINARY o.command_digest=BINARY '+_text(request.command_digest)
               +" AND m.namespace_key='identity' AND BINARY m.selection_digest=BINARY "+_text(selected.digest)
               +' AND BINARY m.native_node_id=BINARY '+_text(selected.native_node_id)
               +' AND DATABASE() IN ('+_text(selected.database)+','+_text(selected.database+'/main')+')'
               +" AND active_branch()='main';")
        rows = LeaseScratchBackend._invoke(self,sql)
        if not rows:
            return None
        if len(rows) != 1:
            raise LeaseDeliveryUnknown('E_MI2_RECEIPT_CARDINALITY')
        return LeaseScratchBackend._receipt(self,request,rows[0])
