"""Lease-v2 protected CM consumer for the isolated practical fence.

This is the successor to the stopped v1 predecessor (whose constructor
refusal stays locked by test). It accepts only the concrete sealed
``LeaseScratchBackend``, derives current-authority observations internally
from that backend, and coordinates exactly-once dispatch through the
single CM journal: reserve intent, winner-only dispatch with consumption
persisted before the mutating process, independent exact operation
readback, and durable APPLIED-or-UNKNOWN outcomes. Reconciliation reopens
the original intent and reads the original operation; it never claims,
heartbeats, refreshes authority, or resends an uncertain write.

A precheck never replaces the database transaction fence: the SQL batch
repeats every predicate atomically at authorization time.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from complete_read_v2 import ledger

from .practical_contract import LeaseGuardedTitleRequest, LeaseReassignRequest, PracticalContractError
from .practical_lease_backend import LeaseDeliveryUnknown, LeaseScratchBackend
from .practical_lease_sql import _same_utc_moment


class LeaseConsumerError(ValueError):
    """A local lease-consumer refusal; this is not a qualification state."""


_ROUTE = 'APPROVED_SCRATCH_PRACTICAL_CONTRACT'
_AUTHORITY_FIELDS = frozenset({
    'issue_id', 'issue_title', 'issue_status', 'assignee', 'issue_row_lock',
    'ephemeral', 'holder', 'granted_node', 'granted_at', 'lease_expires_at',
    'heartbeat_at', 'grant_id', 'grant_actor', 'grant_status',
    'fixed_deadline_utc', 'issue_revision', 'tombstoned', 'lease_node',
    'lease_granted_at', 'lease_expiry', 'lease_heartbeat', 'current_revision',
    'selection_digest', 'native_node_id', 'selected_database',
    'selected_main_branch', 'observed_utc',
})
_UTC_FORMATS = ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f')


def _int64_nonzero(value: Any) -> bool:
    return (not isinstance(value, bool) and isinstance(value, int)
            and value != 0 and -(2 ** 63) <= value <= 2 ** 63 - 1)


def _parse_utc(value: Any, code: str) -> datetime:
    if not isinstance(value, str):
        raise LeaseConsumerError(code)
    for form in _UTC_FORMATS:
        try:
            return datetime.strptime(value, form)
        except ValueError:
            continue
    raise LeaseConsumerError(code)


def _same_moment(left: Any, right: Any, field: str) -> None:
    try:
        _same_utc_moment(left, right, field)
    except PracticalContractError as exc:
        raise LeaseConsumerError(
            'E_PRACTICAL_CURRENT_AUTHORITY: %s disagrees with the request' % field) from exc


class LeaseNativeConsumer:
    """Winner-only CM reservation plus separately observed lease readback."""

    # No __dict__: instance-level replacement of the readback callback (or
    # any other attribute) is structurally impossible. Combined with the
    # exact-type construction gate below, neither a subclass override nor a
    # shadowed method can reach the ledger's protected reader registration.
    __slots__ = ('_db', '_backend', '_requests', '_reader_registration')

    def __init__(self, cm_db, backend: LeaseScratchBackend):
        # The v1 predecessor was stopped precisely because an injected runner
        # could register a fabricated proof path. This successor only accepts
        # the concrete sealed backend class: no subclass, no shadowed trust
        # path, no caller-provided runner or reader. The exact-type gate on
        # self closes the subclass vector: a subclass overriding the readback
        # callback must never obtain a reader registration.
        if type(self) is not LeaseNativeConsumer:
            raise LeaseConsumerError(
                'E_PRACTICAL_CONSUMER: exact LeaseNativeConsumer required, subclass refused')
        if type(backend) is not LeaseScratchBackend:
            raise LeaseConsumerError('E_PRACTICAL_BACKEND: concrete LeaseScratchBackend required')
        selection = backend.selection
        if backend.native_write_qualified is not False or \
                backend.evidence_class != 'NATIVE_OBSERVED_UNQUALIFIED' or \
                backend.candidate_route != _ROUTE or selection.candidate_route != _ROUTE or \
                selection.main_branch != 'main':
            raise LeaseConsumerError('E_PRACTICAL_BACKEND: unsupported backend route or qualification')
        self._db = cm_db
        self._backend = backend
        # Process-local validated requests by operation id. The ledger holds
        # the durable binding; this map only lets the readback callback
        # reopen the exact request the backend reader requires. It never
        # creates authority: completion compares against durable intent.
        self._requests: dict[str, LeaseGuardedTitleRequest] = {}
        # Deliberately private registration seam, as in the predecessor: the
        # returned capability is connection-bound and cannot be built from a
        # public success dictionary.
        self._reader_registration = ledger._register_practical_native_readback_consumer(cm_db, self)

    def _request(self, value) -> LeaseGuardedTitleRequest:
        try:
            return LeaseGuardedTitleRequest.from_value(value)
        except PracticalContractError as exc:
            raise LeaseConsumerError(
                'E_PRACTICAL_REQUEST: exact lease-guarded-title request required') from exc

    def _reassign_request(self, value) -> LeaseReassignRequest:
        try:
            return LeaseReassignRequest.from_value(value)
        except PracticalContractError as exc:
            raise LeaseConsumerError(
                'E_PRACTICAL_REQUEST: exact lease-reassign request required') from exc

    def _current_prerequisite(self, request: LeaseGuardedTitleRequest) -> None:
        """Fail closed before any intent is reserved; the SQL repeats this atomically."""
        try:
            authority = self._backend.read_current_authority(request)
        except LeaseDeliveryUnknown as exc:
            raise LeaseConsumerError(
                'E_PRACTICAL_CURRENT_AUTHORITY: backend authority unreadable') from exc
        if not isinstance(authority, dict) or set(authority) != _AUTHORITY_FIELDS:
            raise LeaseConsumerError('E_PRACTICAL_CURRENT_AUTHORITY: authority shape changed')
        selection = self._backend.selection
        if authority['issue_id'] != request.task_id \
                or authority['issue_status'] != request.expected_status \
                or authority['assignee'] != request.actor \
                or authority['issue_row_lock'] != request.expected_row_lock \
                or not _int64_nonzero(authority['issue_row_lock']) \
                or authority['ephemeral'] not in (0, False):
            raise LeaseConsumerError(
                'E_PRACTICAL_CURRENT_AUTHORITY: task ownership/revision is no longer current')
        if authority['holder'] != request.lease_holder \
                or authority['granted_node'] != request.lease_granted_node:
            raise LeaseConsumerError(
                'E_PRACTICAL_CURRENT_AUTHORITY: lease holder/node is no longer current')
        _same_moment(authority['granted_at'], request.lease_granted_at_utc, 'granted_at')
        _same_moment(authority['lease_expires_at'], request.lease_expires_at_utc, 'lease_expires_at')
        _same_moment(authority['heartbeat_at'], request.lease_heartbeat_at_utc, 'heartbeat_at')
        # Grant lifecycle status is distinct from task status: producers write
        # CURRENT on initial claim and GRANTED on reassign mint; a task status
        # such as in_progress, or any retired lifecycle value, is never a
        # live grant. The current-generation pointer plus tombstoned marker
        # remain the primary currency signals; this rejects anything else.
        if authority['grant_id'] != request.grant_id \
                or authority['grant_actor'] != request.actor \
                or authority['grant_status'] not in ('CURRENT', 'GRANTED') \
                or authority['issue_revision'] != request.expected_row_lock \
                or authority['tombstoned'] not in (0, False):
            raise LeaseConsumerError(
                'E_PRACTICAL_CURRENT_AUTHORITY: grant is changed, inactive, or foreign')
        _same_moment(authority['fixed_deadline_utc'], request.fixed_deadline_utc, 'fixed_deadline_utc')
        _same_moment(authority['lease_granted_at'], request.lease_granted_at_utc, 'grant lease granted_at')
        _same_moment(authority['lease_expiry'], request.lease_expires_at_utc, 'grant lease expiry')
        _same_moment(authority['lease_heartbeat'], request.lease_heartbeat_at_utc, 'grant lease heartbeat')
        if authority['current_revision'] != request.expected_row_lock:
            raise LeaseConsumerError(
                'E_PRACTICAL_CURRENT_AUTHORITY: current pointer moved past this grant')
        if authority['selection_digest'] != selection.digest \
                or authority['native_node_id'] != selection.native_node_id \
                or authority['selected_database'] != selection.database \
                or authority['selected_main_branch'] != selection.main_branch:
            raise LeaseConsumerError(
                'E_PRACTICAL_CURRENT_AUTHORITY: store identity is not the selected scratch store')
        observed = _parse_utc(authority['observed_utc'],
                              'E_PRACTICAL_CURRENT_AUTHORITY: database clock unreadable')
        expiry = _parse_utc(request.lease_expires_at_utc,
                            'E_PRACTICAL_CURRENT_AUTHORITY: fixed deadline unreadable')
        if not observed < expiry:
            raise LeaseConsumerError(
                'E_PRACTICAL_CURRENT_AUTHORITY: database UTC is at or after fixed deadline')

    def read_practical_native_operation(self, binding: Mapping[str, Any]) -> dict[str, Any] | None:
        """Private ledger callback: reopen the exact persisted operation receipt.

        A missing or erroring backend read is uncertain, never a reason to
        replay the write: return None so CM records UNKNOWN. Only an exact
        backend-validated receipt becomes WORKING_SET_APPLIED, so a foreign
        or compact receipt can never seal success.
        """
        try:
            if not isinstance(binding, Mapping):
                return None
            request = self._requests.get(binding.get('operation_id'))
            if request is None:
                return None
            # A missing backend record is uncertainty, not proof: return None
            # so CM records UNKNOWN. Only an exact returned receipt seals
            # WORKING_SET_APPLIED below; a raised mismatch also lands here.
            if self._backend.read_operation(request) is None:
                return None
        except Exception:
            return None
        observed = dict(binding)
        observed['observed_state'] = 'WORKING_SET_APPLIED'
        return observed

    def dispatch_lease_title(self, value) -> dict[str, Any]:
        """Dispatch at most once; a loser/retry can only read the stored operation."""
        return self._dispatch_title(value, pause_seconds=None)

    def dispatch_paused_lease_title(self, value, *, pause_seconds) -> dict[str, Any]:
        """Harness support: the same title dispatch with a bounded pause inside
        the transaction, so an authorization snapshot can be observed rather
        than assumed. The journal, consumption, readback and terminal states
        are identical to the ordinary dispatch.
        """
        if type(pause_seconds) is not int or not 1 <= pause_seconds <= 30:
            raise LeaseConsumerError('E_PRACTICAL_PAUSE_BOUNDS: pause must be 1..30 seconds')
        return self._dispatch_title(value, pause_seconds=pause_seconds)

    def _dispatch_title(self, value, *, pause_seconds) -> dict[str, Any]:
        from .release_profile import require_native_execution_enabled
        require_native_execution_enabled()
        request = self._request(value)
        self._current_prerequisite(request)
        try:
            binding = self._backend.intent_binding(request)
        except PracticalContractError as exc:
            raise LeaseConsumerError(
                'E_PRACTICAL_BINDING: lease facts do not bind this store') from exc
        reservation = ledger.reserve_practical_native_intent(self._db, binding)
        self._requests[request.operation_id] = request
        if not reservation['winner']:
            return ledger.complete_practical_native_readback(
                self._db, binding, self._reader_registration)
        try:
            # The backend persists dispatch consumption before the mutating
            # process; completion re-reads below and a returned receipt is
            # never treated as proof here.
            if pause_seconds is None:
                self._backend.execute_guarded_title(
                    request, cm_db=self._db, reservation=reservation['reservation'])
            else:
                self._backend.execute_paused_guarded_title(
                    request, cm_db=self._db, reservation=reservation['reservation'],
                    pause_seconds=pause_seconds)
        except Exception:
            return ledger.complete_practical_native_readback(
                self._db, binding, self._reader_registration, reservation['reservation'])
        return ledger.complete_practical_native_readback(
            self._db, binding, self._reader_registration, reservation['reservation'])
        return ledger.complete_practical_native_readback(
            self._db, binding, self._reader_registration, reservation['reservation'])

    def reconcile_lease_title(self, value) -> dict[str, Any]:
        """Read-only recovery: it cannot acquire a winner token or replay SQL."""
        from .release_profile import require_native_execution_enabled
        require_native_execution_enabled()
        if isinstance(value, LeaseReassignRequest) or (
                isinstance(value, Mapping) and value.get('action') == 'reassign_title_lease'):
            request = self._reassign_request(value)
        else:
            request = self._request(value)
        try:
            binding = self._backend.intent_binding(request)
        except PracticalContractError as exc:
            raise LeaseConsumerError(
                'E_PRACTICAL_BINDING: lease facts do not bind this store') from exc
        self._requests[request.operation_id] = request
        return ledger.complete_practical_native_readback(
            self._db, binding, self._reader_registration)

    def dispatch_reassign_title(self, value) -> dict[str, Any]:
        """Transfer dispatch at most once; a loser/retry can only read back."""
        from .release_profile import require_native_execution_enabled
        require_native_execution_enabled()
        request = self._reassign_request(value)
        # The transferor prerequisite is the same currency shape as a title:
        # assignee, holder, grant, pointer and store must all be current
        # before any intent is reserved.
        self._current_prerequisite(request)
        try:
            binding = self._backend.intent_binding(request)
        except PracticalContractError as exc:
            raise LeaseConsumerError(
                'E_PRACTICAL_BINDING: lease facts do not bind this store') from exc
        reservation = ledger.reserve_practical_native_intent(self._db, binding)
        self._requests[request.operation_id] = request
        if not reservation['winner']:
            return ledger.complete_practical_native_readback(
                self._db, binding, self._reader_registration)
        try:
            # As in title dispatch, the backend persists dispatch consumption
            # before the mutating process; completion re-reads below and a
            # returned receipt is never treated as proof here.
            self._backend.execute_reassign_title(
                request, cm_db=self._db, reservation=reservation['reservation'])
        except Exception as exc:
            return ledger.complete_practical_native_readback(
                self._db, binding, self._reader_registration, reservation['reservation'])
        return ledger.complete_practical_native_readback(
            self._db, binding, self._reader_registration, reservation['reservation'])
