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
                                 PracticalContractError, strict_canonical_json)
from .practical_sql import _text
from . import practical_lease_sql

DOLT_PIN = 'ca21a9d1dab233a694b99ad0be9e78590967a1cc2773eb202fa0dd2929239ba2'
APPROVED_ROOTS = (Path('C:/Users/sakth/memory-integrity-practical-fence-20261013'),
                  Path('C:/Users/sakth/memory-integrity-scratch-20261011/practical-fence-20261013'))
TIMEOUT_SECONDS = 15
MAX_CAPTURE_BYTES = 1024 * 1024


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
        request = LeaseGuardedTitleRequest.from_value(value)
        if request.lease_granted_node != self.selection.native_node_id:
            raise PracticalContractError('E_MI2_FOREIGN_LEASE_NODE')
        return dict(work_item_id=request.work_item_id, operation_id=request.operation_id,
                    selection_digest=self.selection.digest, store_incarnation=self.selection.incarnation,
                    database=self.selection.database, branch='main', native_task_id=request.task_id,
                    actor=request.actor, grant_id=request.grant_id, original_row_lock=request.expected_row_lock,
                    fixed_deadline=request.fixed_deadline_utc, command_digest=request.command_digest,
                    backend_operation_id=request.operation_id, lease_holder=request.lease_holder,
                    lease_granted_node=request.lease_granted_node,
                    lease_granted_at_utc=request.lease_granted_at_utc,
                    lease_expires_at_utc=request.lease_expires_at_utc,
                    lease_heartbeat_at_utc=request.lease_heartbeat_at_utc)

    def _invoke(self, sql):
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
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TIMEOUT_SECONDS,
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
        if set(receipt) != set(expected) or strict_canonical_json(receipt) != strict_canonical_json(expected) or \
                receipt.get('native_write_qualified') is not False or receipt.get('head_committed') is not False or \
                not _token(row['resulting_row_lock']) or row['resulting_row_lock'] == request.expected_row_lock:
            raise LeaseDeliveryUnknown('E_MI2_RECEIPT_BINDING')
        if not _utc(request.lease_granted_at_utc) <= _utc(row['authorization_time']) < _utc(request.fixed_deadline_utc):
            raise LeaseDeliveryUnknown('E_MI2_RECEIPT_AUTHORIZATION')
        return receipt

    def execute_guarded_title(self, value, *, cm_db, reservation):
        from complete_read_v2 import ledger
        if type(self) is not LeaseScratchBackend:
            raise PracticalContractError('E_MI2_BACKEND_TYPE')
        request = LeaseGuardedTitleRequest.from_value(value)
        binding = self.intent_binding(request)
        # Refuse bogus capability and unsafe path before consuming the attempt.
        ledger._practical_owner(reservation,cm_db,binding)
        _native_boundary(self.selection)
        claimed = ledger.consume_practical_native_dispatch(cm_db,binding,reservation)
        if not claimed['dispatch']:
            raise PracticalContractError('E_MI2_OPERATION_READBACK_ONLY')
        try:
            rows = LeaseScratchBackend._invoke(self,practical_lease_sql.guarded_title_sql(self.selection,request))
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

    def read_operation(self, value):
        request = LeaseGuardedTitleRequest.from_value(value)
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
