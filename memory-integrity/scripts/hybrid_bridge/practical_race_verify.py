"""The single authoritative, fail-closed verdict path for the lease race.

There is exactly one way to turn observations into a verdict:
``judge_evidence``. The controller calls it and nothing else. No narrower
predicate helper can produce a verdict, because a strict helper that the
orchestrator does not use cannot protect the experiment: the previous
arrangement let ``run_race`` score a weaker checker while a correct one sat
unused beside it.

Design rules that the earlier implementation broke:

* Missing or unverifiable evidence is never PASSED. An empty snapshot, an
  absent journal entry, a missing dispatch count, an unobserved barrier, an
  unobserved store identity and an unexecuted control are all reasons.
* Observed unsafe effects fail even when other evidence is incomplete.
* An unrelated refusal is not fencing proof and an unknown refusal reason
  never falls through to a pass.
* Reasons carry explicit codes and severities. No English-prefix matching.
* Row identity is per table, including issue_id and composite keys. No
  generic id/operation_id/grant_id heuristic, and no dictionary
  construction that silently collapses duplicate rows.
* Database-generated conflict tokens are not required to be known before
  the run. Their type, freshness, uniqueness and cross-record agreement are
  checked instead.

These functions decide recorded observations only. They never touch a
database and prove no native behavior.
"""
from __future__ import annotations

from datetime import datetime

EVIDENCE_SCHEMA_VERSION = 1

UNSAFE = 'UNSAFE'
UNPROVEN = 'UNPROVEN'

PASSED = 'PASSED'
FAILED = 'FAILED'
INCONCLUSIVE = 'INCONCLUSIVE'

# Reason codes. UNSAFE codes mean an observed bad effect and force FAILED.
# UNPROVEN codes mean the evidence cannot support any verdict and force
# INCONCLUSIVE. Both are non-empty outcomes; only zero reasons is PASSED.
REASON_SEVERITY = {
    # Observed unsafe effects.
    'STALE_COMMITTED_EFFECT': UNSAFE,
    'STALE_SUCCESS_RECEIPT': UNSAFE,
    'STALE_BACKEND_SUCCESS_RECORD': UNSAFE,
    'CM_FALSE_ACCEPT': UNSAFE,
    'DUPLICATE_DISPATCH': UNSAFE,
    'ROW_LOST': UNSAFE,
    'UNEXPLAINED_CHANGE': UNSAFE,
    'EXPIRY_MOVED': UNSAFE,
    'GRANT_ACTOR_MISMATCH': UNSAFE,
    'GRANT_REVISION_MISMATCH': UNSAFE,
    'HEARTBEAT_NOT_DERIVED': UNSAFE,
    'TOKEN_NOT_ROTATED': UNSAFE,
    'TOKEN_NOT_BOUND': UNSAFE,
    'POINTER_MISMATCH': UNSAFE,
    'ACTIVE_GRANT_SET_WRONG': UNSAFE,
    'PRIOR_GRANT_NOT_TOMBSTONED': UNSAFE,
    'GRANT_HISTORY_FOREIGN': UNSAFE,
    'GRANT_LEASE_FACTS_MISMATCH': UNSAFE,
    'OPERATION_RECORD_DISAGREEMENT': UNSAFE,
    'WINNER_STATE_LOST': UNSAFE,
    'STALE_OPERATION_PRESENT': UNSAFE,
    # Evidence that cannot support a verdict.
    'EVIDENCE_MISSING': UNPROVEN,
    'GRANT_HISTORY_INCOMPLETE': UNPROVEN,
    'GRANT_LEASE_FACTS_INCOMPLETE': UNPROVEN,
    'TRANSFER_STATE_INCONSISTENT': UNPROVEN,
    'EVIDENCE_SCHEMA_INVALID': UNPROVEN,
    'EVIDENCE_SCHEMA_VERSION': UNPROVEN,
    'DUPLICATE_ROW_IDENTITY': UNPROVEN,
    'OBSERVATION_INCOMPLETE': UNPROVEN,
    'BARRIER_INVALID': UNPROVEN,
    'BARRIER_ORDERING_UNPROVEN': UNPROVEN,
    'BARRIER_UNSUPPORTED_SYNC': UNPROVEN,
    'IDENTITY_UNVERIFIED': UNPROVEN,
    'RUNTIME_PIN_MISMATCH': UNPROVEN,
    'CONTROL_NOT_EXECUTED': UNPROVEN,
    'CONTROL_INEFFECTIVE': UNPROVEN,
    'CONTROL_CAUSALITY_UNPROVEN': UNPROVEN,
    'JOURNAL_HISTORY_INVALID': UNPROVEN,
    'DISPATCH_UNOBSERVED': UNPROVEN,
    'REFUSAL_UNRELATED': UNPROVEN,
    'REFUSAL_UNKNOWN': UNPROVEN,
    'HARNESS_ERROR': UNPROVEN,
}

# CM journal vocabulary, from the companion ledger's practical namespace.
CM_INTENT = 'PRACTICAL_NATIVE_INTENT'
CM_DISPATCHED = 'PRACTICAL_NATIVE_DISPATCHED'
CM_APPLIED = 'PRACTICAL_NATIVE_APPLIED'
CM_UNKNOWN = 'PRACTICAL_NATIVE_UNKNOWN'
CM_KINDS = (CM_INTENT, CM_DISPATCHED, CM_APPLIED, CM_UNKNOWN)
BACKEND_APPLIED = 'WORKING_SET_APPLIED'

# Per-table row identity. These are the real primary keys of the generated
# schema; a single generic id heuristic cannot express them.
TABLE_KEYS = {
    'issues': ('id',),
    'leases': ('issue_id',),
    'grants': ('store_incarnation', 'grant_id'),
    'grant_history': ('store_incarnation', 'grant_id', 'event_kind', 'event_utc'),
    'current_grants': ('store_incarnation', 'task_id'),
    'metadata': ('store_incarnation',),
    'token_history': ('store_incarnation', 'row_token'),
    'operations': ('store_incarnation', 'operation_id'),
}
REQUIRED_TABLES = frozenset(TABLE_KEYS)

# A schema observation contains physical names. Logical snapshot keys are an
# explicit mapping, never aliases inserted to fill holes in observed schema.
PHYSICAL_EVIDENCE_TABLES = {
    'issues': 'issues', 'leases': 'leases',
    'mi_practical_v2_grants': 'grants',
    'mi_practical_v2_grant_history': 'grant_history',
    'mi_practical_v2_current_grants': 'current_grants',
    'mi_practical_v2_metadata': 'metadata',
    'mi_practical_v2_token_history': 'token_history',
    'mi_practical_v2_operations': 'operations',
}
REQUIRED_PHYSICAL_TABLES = frozenset(PHYSICAL_EVIDENCE_TABLES) | {'dependencies'}

# The lease snapshot a successor grant must carry, and the lease column each
# field must equal.
_GRANT_LEASE_FIELDS = (
    ('lease_node', 'granted_node'),
    ('lease_granted_at', 'granted_at'),
    ('lease_expiry', 'lease_expires_at'),
    ('lease_heartbeat', 'heartbeat_at'),
)

# Tables whose rows are legitimately rewritten by a successful transfer.
AFFECTED_TABLES = frozenset({'issues', 'leases', 'grants', 'current_grants',
                             'token_history', 'operations', 'grant_history'})

BARRIER_KINDS = ('AUTHORIZATION_SNAPSHOT_HELD',)
BARRIER_KEYS = frozenset({'kind', 'run_id', 'operation_id', 'session_id',
                          'observed_by', 'authorization_time',
                          'transfer_committed_at', 'resumed_at', 'unsupported'})

# Fixed refusal-source vocabulary. The controller maps a structured driver
# outcome onto FENCE or OTHER with this closed set; it never guesses from a
# free-form error string, and any value outside the set stays unattributed
# instead of falling through to a pass.
REFUSAL_FROM_PROTECTED = ('PROTECTED_ASSERT', 'PROTECTED_AUTHORIZATION')
REFUSAL_FROM_ELSEWHERE = ('TRANSPORT', 'HARNESS', 'SERVER', 'TIMEOUT')

ENGINE_SYNTHETIC = 'synthetic-dolt-engine'
ENGINE_BEADS = 'real-beads-backed'
EVIDENCE_CLASS_SYNTHETIC = 'SYNTHETIC_ENGINE_MECHANISM_ONLY'
EVIDENCE_CLASS_BEADS = 'REAL_BEADS_OBSERVED_UNQUALIFIED'

_LIVE_GRANT_STATUS = ('CURRENT', 'GRANTED')
_HEX40 = frozenset('0123456789abcdef')
_HEX64 = frozenset('0123456789abcdef')


def _reason(code, detail='', **fields):
    """Build one structured reason. Unknown codes are a programming error."""
    if code not in REASON_SEVERITY:
        raise KeyError('unregistered reason code: ' + str(code))
    reason = {'code': code, 'severity': REASON_SEVERITY[code], 'detail': str(detail)}
    for key, value in fields.items():
        if value is not None:
            reason[key] = value
    return reason


def _is_hex(value, length):
    return (isinstance(value, str) and len(value) == length
            and set(value.lower()) <= _HEX64 and value.lower() == value)


def _utc(value):
    """Parse a native UTC timestamp as DATETIME or DATETIME(6)."""
    if not isinstance(value, str):
        return None
    for form in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(value, form)
        except ValueError:
            continue
    return None


def _int(value):
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _text(value):
    return value if isinstance(value, str) and value.strip() else None


def _identity(table, row):
    keys = TABLE_KEYS[table]
    parts = []
    for key in keys:
        value = row.get(key)
        if value is None or isinstance(value, (list, dict, set, tuple)):
            return None
        parts.append(value)
    return tuple(parts)


def _index(rows, table, reasons, where):
    """Map identity to row without ever collapsing a duplicate silently."""
    if not isinstance(rows, list):
        reasons.append(_reason('OBSERVATION_INCOMPLETE',
                               '%s %s is not a row list' % (where, table), table=table))
        return {}
    index = {}
    for position, row in enumerate(rows):
        if not isinstance(row, dict):
            reasons.append(_reason('EVIDENCE_SCHEMA_INVALID',
                                   '%s %s row %d is not a mapping' % (where, table, position),
                                   table=table))
            continue
        identity = _identity(table, row)
        if identity is None:
            reasons.append(_reason('OBSERVATION_INCOMPLETE',
                                   '%s %s row %d lacks a complete identity' % (where, table, position),
                                   table=table))
            continue
        if identity in index:
            reasons.append(_reason('DUPLICATE_ROW_IDENTITY',
                                   '%s %s repeats identity %r' % (where, table, identity),
                                   table=table, row=repr(identity)))
            if row != index[identity]:
                reasons.append(_reason('OPERATION_RECORD_DISAGREEMENT',
                                       '%s %s has contradictory rows for %r'
                                       % (where, table, identity), table=table))
            # Keep the first row but keep validating: the duplicate is still
            # compared semantically so a hidden stale row cannot pass quietly.
            continue
        index[identity] = row
    return index


def _state(observations, phase, reasons):
    """Validate one observation snapshot and return its per-table indexes.

    Every required table is always present in the result, empty when the
    observation omitted it, so a missing table produces reasons instead of a
    crash somewhere downstream.
    """
    if not isinstance(observations, dict):
        reasons.append(_reason('OBSERVATION_INCOMPLETE', '%s observation is not a mapping' % phase))
        return {table: {} for table in REQUIRED_TABLES}
    missing = sorted(REQUIRED_TABLES - set(observations))
    if missing:
        reasons.append(_reason('OBSERVATION_INCOMPLETE',
                               '%s observation is missing tables %r' % (phase, missing)))
    unexpected = sorted(set(observations) - REQUIRED_TABLES)
    if unexpected:
        reasons.append(_reason('OBSERVATION_INCOMPLETE',
                               '%s observation has unexpected tables %r' % (phase, unexpected)))
    return {table: _index(observations.get(table, []), table, reasons, phase)
            for table in sorted(REQUIRED_TABLES)}


def _single(index, table, field, value, reasons, where, code='OBSERVATION_INCOMPLETE'):
    """The one row of `table` whose `field` equals `value`, or a reason."""
    rows = [row for row in index.values() if row.get(field) == value]
    if len(rows) != 1:
        reasons.append(_reason(code, '%s expects exactly one %s row for %s=%r, found %d'
                               % (where, table, field, value, len(rows)), table=table))
        return None
    return rows[0]


def _validate_identity(evidence, reasons):
    source = evidence['source']
    for key in ('commit', 'source_manifest_sha256', 'controller_sha256', 'verifier_sha256'):
        length = 40 if key == 'commit' else 64
        value = source.get(key)
        if not _is_hex(value, length):
            reasons.append(_reason('IDENTITY_UNVERIFIED',
                                   'source.%s is not a lowercase %d-hex digest' % (key, length)))
    if source.get('working_tree') not in ('CLEAN', 'DIRTY'):
        reasons.append(_reason('IDENTITY_UNVERIFIED',
                               'source.working_tree must record CLEAN or DIRTY, got %r'
                               % (source.get('working_tree'),)))
    runtime = evidence['runtime']
    for key in ('dolt_sha256', 'expected_dolt_sha256'):
        if not _is_hex(runtime.get(key), 64):
            reasons.append(_reason('IDENTITY_UNVERIFIED', 'runtime.%s is not a 64-hex digest' % key))
    if runtime.get('dolt_sha256') and runtime['dolt_sha256'] != runtime.get('expected_dolt_sha256'):
        reasons.append(_reason('RUNTIME_PIN_MISMATCH',
                               'observed dolt digest differs from the contract pin'))
    store = evidence['store']
    if store.get('observed') is not True:
        reasons.append(_reason('IDENTITY_UNVERIFIED', 'store identity was not observed from the database'))
    if store.get('verification') != 'QUERY_OBSERVED':
        reasons.append(_reason('IDENTITY_UNVERIFIED',
                               'store.verification must be QUERY_OBSERVED, got %r'
                               % (store.get('verification'),)))
    for key in ('database', 'branch', 'namespace', 'node'):
        if _text(store.get(key)) is None:
            reasons.append(_reason('IDENTITY_UNVERIFIED', 'store.%s is unreadable' % key))
    tables = store.get('schema_tables')
    if not isinstance(tables, list) or any(_text(name) is None for name in tables) \
            or len(tables) != len(set(tables)) \
            or not REQUIRED_PHYSICAL_TABLES <= set(tables):
        reasons.append(_reason('IDENTITY_UNVERIFIED',
                               'store.schema_tables does not cover the tables this verifier reads'))
    engine = runtime.get('engine')
    evidence_class = runtime.get('evidence_class')
    if engine == ENGINE_SYNTHETIC:
        if evidence_class != EVIDENCE_CLASS_SYNTHETIC:
            reasons.append(_reason('EVIDENCE_SCHEMA_INVALID',
                                   'a synthetic engine run cannot claim %r' % (evidence_class,)))
    elif engine == ENGINE_BEADS:
        if evidence_class != EVIDENCE_CLASS_BEADS:
            reasons.append(_reason('EVIDENCE_SCHEMA_INVALID',
                                   'a real-Beads run must claim %r' % (EVIDENCE_CLASS_BEADS,)))
        beads = store.get('beads')
        # A .beads directory and a caller-supplied hash are not observed
        # Beads identity. Schema tables and version must come from a query.
        if not isinstance(beads, dict) or beads.get('observed') is not True \
                or _text(beads.get('version')) is None \
                or not isinstance(beads.get('schema_tables'), list) \
                or not {'issues', 'leases'} <= set(beads['schema_tables']):
            reasons.append(_reason('IDENTITY_UNVERIFIED',
                                   'real-Beads identity was not observed from the store itself'))
    else:
        reasons.append(_reason('IDENTITY_UNVERIFIED', 'unknown engine %r' % (engine,)))


def _validate_barrier(evidence, identities, reasons):
    barrier = evidence.get('barrier')
    stale = identities['stale_operation_ids']
    if not isinstance(stale, list) or len(stale) != 1:
        reasons.append(_reason('EVIDENCE_SCHEMA_INVALID',
                               'exactly one stale operation id is required for this proof'))
        return
    stale_operation = stale[0]
    # None, an empty mapping, or a bare boolean is never barrier evidence.
    if barrier is None:
        reasons.append(_reason('BARRIER_INVALID', 'wait_barrier returned no evidence'))
        return
    if not isinstance(barrier, dict):
        reasons.append(_reason('BARRIER_INVALID',
                               'barrier evidence is a %s, not a mapping' % type(barrier).__name__))
        return
    if not barrier:
        reasons.append(_reason('BARRIER_INVALID', 'barrier evidence is an empty mapping'))
        return
    if set(barrier) != BARRIER_KEYS:
        reasons.append(_reason('BARRIER_INVALID',
                               'barrier evidence keys differ: %r' % (sorted(set(barrier) ^ BARRIER_KEYS),)))
        return
    if not isinstance(barrier['unsupported'], bool):
        reasons.append(_reason('BARRIER_INVALID', 'barrier unsupported marker is not a boolean'))
        return
    if barrier['unsupported']:
        # The runtime exposed no session view. Unsupported synchronization is
        # INCONCLUSIVE; it is never quietly treated as an observed barrier.
        reasons.append(_reason('BARRIER_UNSUPPORTED_SYNC',
                               'this runtime exposes no observable authorization barrier'))
        return
    if barrier['kind'] not in BARRIER_KINDS:
        reasons.append(_reason('BARRIER_UNSUPPORTED_SYNC',
                               'unsupported synchronization kind %r' % (barrier['kind'],)))
        return
    if barrier['observed_by'] != 'DATABASE_SESSION_MARKER':
        reasons.append(_reason('BARRIER_INVALID',
                               'barrier must be observed by a database session marker, got %r'
                               % (barrier['observed_by'],)))
        return
    if _text(barrier['session_id']) is None:
        reasons.append(_reason('BARRIER_INVALID',
                               'barrier session identity is not an observed identifier'))
        return
    if barrier['run_id'] != evidence['run_id']:
        reasons.append(_reason('BARRIER_INVALID', 'barrier is bound to a different run'))
        return
    if barrier['operation_id'] != stale_operation:
        reasons.append(_reason('BARRIER_INVALID', 'barrier is bound to a different operation'))
        return
    authorization = _utc(barrier['authorization_time'])
    committed = _utc(barrier['transfer_committed_at'])
    resumed = _utc(barrier['resumed_at'])
    if authorization is None or committed is None or resumed is None:
        reasons.append(_reason('BARRIER_INVALID', 'barrier ordering timestamps are unreadable'))
        return
    # The authorization snapshot must be reached before the transfer commits,
    # and the transfer must commit before Alice's effect may resume. Without
    # this the run proves nothing about interleaving.
    if not authorization <= committed <= resumed:
        reasons.append(_reason('BARRIER_ORDERING_UNPROVEN',
                               'barrier ordering is not authorization <= transfer <= resume'))
        return


def _validate_operations(evidence, identities, phase, reasons, baseline=None):
    """Backend operation records: exact binding, receipt and token agreement."""
    records = evidence['operations']
    namespace = evidence['store'].get('namespace')
    stale = set(identities['stale_operation_ids'])
    winners = list(identities['winner_operation_ids'])
    if not isinstance(records, dict):
        reasons.append(_reason('EVIDENCE_MISSING', '%s backend operation records are not a mapping' % phase))
        return {}
    preserved = {row.get('operation_id') for row in (baseline or {}).values()}
    expected = set(winners) | preserved
    if set(records) != expected:
        # The stale operation must leave no backend record at all; its absence
        # is the expected shape, so only a present or foreign key is a defect.
        reasons.append(_reason('OBSERVATION_INCOMPLETE',
                               '%s operation records cover %r, expected exactly %r'
                               % (phase, sorted(records), sorted(expected))))
    for operation_id in sorted(stale & set(records)):
        record = records[operation_id]
        # Case B: a committed backend record for the stale operation is an
        # observed stale effect, even when the CM journal still says UNKNOWN.
        reasons.append(_reason('STALE_BACKEND_SUCCESS_RECORD',
                               'stale operation %s has a backend record in %s readback'
                               % (operation_id, phase), operation_id=operation_id))
        if not isinstance(record, dict):
            continue
        if _text(record.get('result')) == CM_APPLIED:
            reasons.append(_reason('STALE_SUCCESS_RECEIPT',
                                   'stale operation %s recorded %s' % (operation_id, CM_APPLIED),
                                   operation_id=operation_id))
    resolved = {}
    for operation_id in winners:
        record = records.get(operation_id)
        if not isinstance(record, dict):
            reasons.append(_reason('OBSERVATION_INCOMPLETE',
                                   '%s operation %s record is missing' % (phase, operation_id),
                                   operation_id=operation_id))
            continue
        if record.get('store_incarnation') != namespace:
            reasons.append(_reason('EVIDENCE_SCHEMA_INVALID',
                                   '%s operation %s is bound to another namespace'
                                   % (phase, operation_id), operation_id=operation_id))
        if not _is_hex(record.get('command_digest'), 64):
            reasons.append(_reason('OBSERVATION_INCOMPLETE',
                                   '%s operation %s has no command digest' % (phase, operation_id),
                                   operation_id=operation_id))
        authorization = _utc(record.get('authorization_time'))
        if authorization is None:
            reasons.append(_reason('OBSERVATION_INCOMPLETE',
                                   '%s operation %s authorization time is unreadable'
                                   % (phase, operation_id), operation_id=operation_id))
            continue
        resolved[operation_id] = record
    return resolved


def _validate_operation_snapshot_agreement(final, identities, records, reasons, observations=None,
                                          compare_records=True):
    """Two observations of the same backend state must not disagree.

    The final operations table snapshot and the separate operation-record
    mapping describe the same rows. A row present in one and absent from the
    other is either a hidden stale effect or a fabricated success, and either
    way it can never be a pass.
    """
    stale = set(identities['stale_operation_ids'])
    snapshot = final['operations']
    for identity, row in snapshot.items():
        operation_id = row.get('operation_id')
        if operation_id in stale:
            reasons.append(_reason('STALE_BACKEND_SUCCESS_RECORD',
                                   'the final operations snapshot still carries a row for the '
                                   'stale operation %r' % (operation_id,),
                                   operation_id=operation_id))
    # An observed effect does not stop being observed because a later snapshot
    # omits it. Every phase is scanned, so evidence cannot disappear backwards.
    if isinstance(observations, dict):
        for phase, state in observations.items():
            if phase == 'final' or not isinstance(state, dict):
                continue
            for row in state.get('operations', {}).values():
                operation_id = row.get('operation_id')
                if operation_id in stale:
                    reasons.append(_reason('STALE_BACKEND_SUCCESS_RECORD',
                                           'the %s snapshot carries a backend row for the stale '
                                           'operation %r' % (phase, operation_id),
                                           operation_id=operation_id))
    if not compare_records:
        return  # Collection failure is uncertainty; stale rows above still fail.
    snapshot_ids = {row.get('operation_id') for row in snapshot.values()}
    for operation_id in sorted(snapshot_ids - set(records)):
        reasons.append(_reason('OPERATION_RECORD_DISAGREEMENT',
                               'the final snapshot carries operation %r that the operation-record '
                               'mapping omits' % (operation_id,), operation_id=operation_id))
    for operation_id in sorted(set(records) - snapshot_ids):
        reasons.append(_reason('OPERATION_RECORD_DISAGREEMENT',
                               'operation %r is reported by the mapping but absent from the final '
                               'snapshot' % (operation_id,), operation_id=operation_id))
    for identity, row in snapshot.items():
        operation_id = row.get('operation_id')
        record = records.get(operation_id)
        if not isinstance(record, dict):
            continue
        for field in ('command_digest', 'authorization_time', 'resulting_row_lock'):
            if field in row and row.get(field) != record.get(field):
                reasons.append(_reason('OPERATION_RECORD_DISAGREEMENT',
                                       'operation %r %s is %r in the snapshot and %r in the mapping'
                                       % (operation_id, field, row.get(field), record.get(field)),
                                       operation_id=operation_id))


def _validate_final_state(evidence, identities, before, after_transfer, final, reasons):
    """Every affected-state relationship the adopted protocol requires."""
    task = identities['task_id']
    namespace = evidence['store'].get('namespace')
    winner = identities['winner']
    stale_actor = identities['stale_actor']
    stale_grant = identities['stale_grant_id']
    winner_grant = identities['winner_grant_id']

    # S0: the pre-race state must really be an Alice-owned in-progress task.
    origin = _single(before['issues'], 'issues', 'id', task, reasons, 'S0')
    origin_lease = _single(before['leases'], 'leases', 'issue_id', task, reasons, 'S0')
    if origin is not None:
        if origin.get('assignee') != stale_actor:
            reasons.append(_reason('OBSERVATION_INCOMPLETE',
                                   'S0 issue is not owned by the stale actor'))
        if origin.get('status') != 'in_progress':
            reasons.append(_reason('OBSERVATION_INCOMPLETE',
                                   'S0 issue status is not in_progress'))
    if origin_lease is not None and origin_lease.get('holder') != stale_actor:
        reasons.append(_reason('OBSERVATION_INCOMPLETE', 'S0 lease holder is not the stale actor'))

    # The winner operation must be bound to the transfer that happened.
    operations = _validate_operations(evidence, identities, 'S2', reasons, before['operations'])
    winner_operations = list(identities['winner_operation_ids'])
    if len(winner_operations) != 1:
        reasons.append(_reason('EVIDENCE_SCHEMA_INVALID',
                               'exactly one winner operation id is required for this proof'))
        return
    winner_operation = winner_operations[0]
    record = operations.get(winner_operation)
    if record is None:
        # Incomplete receipts cannot erase an already observed unsafe state.
        record = {}

    # S1: the transfer must have been independently observed as committed.
    if not isinstance(after_transfer, dict):
        reasons.append(_reason('OBSERVATION_INCOMPLETE',
                               'S1 transfer observation is missing; the transfer was not observed'))
        return
    # S1 already claims a committed transfer; it must satisfy the same
    # transfer invariants as S2. Only the observation boundary differs.
    for phase, snapshot in (('S1', after_transfer), ('S2', final)):
        if not any(snapshot.values()):
            reasons.append(_reason('OBSERVATION_INCOMPLETE', phase + ' has no observed rows'))
            continue
        start = len(reasons)
        _validate_transfer_state(evidence, identities, before, snapshot, record, reasons, phase)
        errors = evidence.get('harness_errors', [])
        readable = not isinstance(errors, list) or not any(
            str(error).startswith('operation_records:') for error in errors)
        _validate_operation_snapshot_agreement(
            snapshot, identities, evidence['operations'], reasons, compare_records=readable)
        _validate_token_history(evidence, identities, snapshot, reasons)
        _validate_grant_history(snapshot, identities, reasons, namespace,
                                record.get('authorization_time'), before['grant_history'])
        _validate_unaffected(before, snapshot, identities, reasons)
        for table in ('grant_history', 'token_history', 'operations'):
            for identity, row in before[table].items():
                current = snapshot[table].get(identity)
                if current != row:
                    reasons.append(_reason('ROW_LOST' if current is None else 'UNEXPLAINED_CHANGE',
                                           'baseline %s row %r was not preserved' % (table, identity)))
        for reason in reasons[start:]:
            reason['phase'] = phase
            reason['detail'] = phase + ': ' + reason['detail']


def _validate_transfer_state(evidence, identities, before, final, record, reasons, phase):
    """Shared committed-transfer invariants; no phase can use a weaker copy."""
    task = identities['task_id']
    namespace = evidence['store'].get('namespace')
    winner = identities['winner']
    stale_grant = identities['stale_grant_id']
    winner_grant = identities['winner_grant_id']
    origin = before['issues'].get((task,))
    origin_lease = before['leases'].get((task,))
    metadata = list(final['metadata'].values())
    origin_metadata = list(before['metadata'].values())
    if len(metadata) != 1 or len(origin_metadata) != 1 or metadata != origin_metadata:
        reasons.append(_reason('IDENTITY_UNVERIFIED', 'committed snapshot metadata is missing or changed'))
    elif any(metadata[0].get(field) != value for field, value in (
            ('store_incarnation', namespace), ('namespace_key', 'identity'),
            ('native_node_id', evidence['store'].get('node')),
            ('selected_database', (_text(evidence['store'].get('database')) or '').removesuffix('/main')),
            ('selected_main_branch', evidence['store'].get('branch')))):
        reasons.append(_reason('IDENTITY_UNVERIFIED', 'snapshot metadata disagrees with observed store'))
    issue = _single(final['issues'], 'issues', 'id', task, reasons, phase)
    lease = _single(final['leases'], 'leases', 'issue_id', task, reasons, phase)
    if issue is None or lease is None:
        return

    # Expected issue owner, title and status.
    if issue.get('assignee') != winner:
        reasons.append(_reason('WINNER_STATE_LOST',
                               'final issue owner is %r, not the successor %r'
                               % (issue.get('assignee'), winner)))
    if issue.get('status') != 'in_progress':
        reasons.append(_reason('WINNER_STATE_LOST',
                               'final issue status is %r' % (issue.get('status'),)))
    expected_title = identities.get('expected_title')
    if expected_title is not None and issue.get('title') != expected_title:
        reasons.append(_reason('STALE_COMMITTED_EFFECT',
                               'final issue title is %r, not the winner title %r'
                               % (issue.get('title'), expected_title)))

    # Lease: successor holds it; granted time, granting node and original
    # expiry never move; the resulting heartbeat is recorded separately and
    # correctly derived from the transfer authorization moment.
    if lease.get('holder') != winner:
        reasons.append(_reason('WINNER_STATE_LOST', 'final lease holder is %r, not %r'
                               % (lease.get('holder'), winner)))
        if phase == 'S1':
            reasons.append(_reason('TRANSFER_STATE_INCONSISTENT',
                                   'S1 lease does not describe the committed transfer'))
    if lease.get('granted_node') != evidence['store'].get('node'):
        reasons.append(_reason('GRANT_LEASE_FACTS_MISMATCH', 'lease was granted on another node'))
    for field in ('granted_at', 'granted_node', 'lease_expires_at'):
        if origin_lease is not None and lease.get(field) != origin_lease.get(field):
            reasons.append(_reason('EXPIRY_MOVED' if field == 'lease_expires_at' else 'STALE_COMMITTED_EFFECT',
                                   'final lease %s moved from %r to %r'
                                   % (field, origin_lease.get(field), lease.get(field))))
    authorization = _utc(record.get('authorization_time'))
    granted = _utc(lease.get('granted_at'))
    expiry = _utc(lease.get('lease_expires_at'))
    heartbeat = _utc(lease.get('heartbeat_at'))
    if authorization is None or granted is None or expiry is None or heartbeat is None:
        reasons.append(_reason('OBSERVATION_INCOMPLETE',
                               'lease or transfer authorization timestamps are unreadable'))
    else:
        # The builder writes CAST(authorization AS DATETIME). MySQL truncates
        # rather than rounds; that remains a runtime-dependent assumption until
        # a live server is observed, so this is the expected relationship and
        # not a claim about the pinned runtime.
        if heartbeat != authorization.replace(microsecond=0):
            reasons.append(_reason('HEARTBEAT_NOT_DERIVED',
                                   'resulting heartbeat %r is not the transfer authorization moment %r'
                                   % (lease.get('heartbeat_at'), record.get('authorization_time'))))
        if not granted <= heartbeat < expiry:
            reasons.append(_reason('HEARTBEAT_NOT_DERIVED',
                                   'resulting heartbeat falls outside granted <= heartbeat < expiry'))
        # Authorization must be at or after the original grant and strictly
        # before the original deadline. An operation authorized before the
        # original deadline may still finish saving later; that is the adopted
        # contract and must not be re-tightened here.
        if not granted <= authorization < expiry:
            reasons.append(_reason('EXPIRY_MOVED',
                                   'transfer authorization is outside the original lease window'))

    # Grants: prior tombstoned, successor live, exactly one active grant.
    live = [row for row in final['grants'].values()
            if row.get('task_id') == task and row.get('tombstoned') in (0, False)]
    if {row.get('grant_id') for row in live} != {winner_grant}:
        reasons.append(_reason('ACTIVE_GRANT_SET_WRONG',
                               'live grant set is %r, expected exactly {%r}'
                               % (sorted(row.get('grant_id') for row in live), winner_grant)))
    successor = final['grants'].get((namespace, winner_grant))
    if successor is None:
        reasons.append(_reason('OBSERVATION_INCOMPLETE',
                               'successor grant row is absent from the final readback'))
    else:
        if successor.get('task_id') != task or successor.get('store_incarnation') != namespace:
            reasons.append(_reason('GRANT_ACTOR_MISMATCH',
                                   'successor grant belongs to another task or store'))
        if successor.get('tombstoned') not in (0, False):
            reasons.append(_reason('WINNER_STATE_LOST', 'successor grant is tombstoned'))
        deadline = _utc(successor.get('fixed_deadline_utc'))
        if deadline is None:
            reasons.append(_reason('GRANT_LEASE_FACTS_INCOMPLETE', 'successor grant has no fixed deadline'))
        elif deadline != _utc(lease.get('lease_expires_at')):
            reasons.append(_reason('GRANT_LEASE_FACTS_MISMATCH', 'successor grant deadline differs from original expiry'))
        if successor.get('actor') != winner:
            reasons.append(_reason('GRANT_ACTOR_MISMATCH',
                                   'successor grant actor is %r, not %r'
                                   % (successor.get('actor'), winner)))
        if successor.get('status') not in _LIVE_GRANT_STATUS:
            reasons.append(_reason('GRANT_ACTOR_MISMATCH',
                                   'successor grant status %r is not a live lifecycle value'
                                   % (successor.get('status'),)))
        # The successor grant carries the lease snapshot. The fields are
        # mandatory, not optional: a grant that omits them describes no lease
        # at all, so absence is a reason rather than a skipped comparison.
        for grant_field, lease_field in _GRANT_LEASE_FIELDS:
            if grant_field not in successor:
                reasons.append(_reason('GRANT_LEASE_FACTS_INCOMPLETE',
                                       'successor grant omits its %s snapshot field' % grant_field))
            elif lease.get(lease_field) is not None \
                    and successor.get(grant_field) != lease.get(lease_field):
                reasons.append(_reason('GRANT_LEASE_FACTS_MISMATCH',
                                       'successor grant %s is %r but the lease %s is %r'
                                       % (grant_field, successor.get(grant_field),
                                          lease_field, lease.get(lease_field))))
    prior = final['grants'].get((namespace, stale_grant))
    if prior is None:
        reasons.append(_reason('PRIOR_GRANT_NOT_TOMBSTONED',
                               'prior grant row was removed; the no-deletion rule forbids it'))
    elif prior.get('tombstoned') not in (1, True):
        reasons.append(_reason('PRIOR_GRANT_NOT_TOMBSTONED',
                               'prior grant %r is still live' % (stale_grant,)))
    if prior is not None:
        original = before['grants'].get((namespace, stale_grant))
        if original is None or any(prior.get(field) != value
                                   for field, value in original.items() if field != 'tombstoned'):
            reasons.append(_reason('UNEXPLAINED_CHANGE', 'prior grant facts changed during transfer'))

    # Issue token, grant revision, current pointer and operation result agree.
    token = _int(issue.get('row_lock'))
    before_token = _int(origin.get('row_lock')) if origin is not None else None
    if token is None:
        reasons.append(_reason('TOKEN_NOT_ROTATED', 'final conflict token is not an integer'))
    else:
        if token == 0 or token == before_token:
            reasons.append(_reason('TOKEN_NOT_ROTATED',
                                   'final conflict token %r was not rotated from %r'
                                   % (token, before_token)))
        if successor is not None and _int(successor.get('issue_revision')) != token:
            reasons.append(_reason('GRANT_REVISION_MISMATCH',
                                   'successor grant revision %r differs from the issue token %r'
                                   % (successor.get('issue_revision'), token)))
        if record and _int(record.get('resulting_row_lock')) != token:
            reasons.append(_reason('GRANT_REVISION_MISMATCH',
                                   'operation receipt token %r differs from the issue token %r'
                                   % (record.get('resulting_row_lock'), token)))
    pointer = _single(final['current_grants'], 'current_grants', 'task_id', task, reasons, phase)
    if pointer is not None:
        if pointer.get('store_incarnation') != namespace:
            # The pointer is a (store_incarnation, task_id) row; a foreign
            # namespace means it does not describe the selected store at all.
            reasons.append(_reason('POINTER_MISMATCH',
                                   'current grant pointer names namespace %r, not %r'
                                   % (pointer.get('store_incarnation'), namespace)))
        if pointer.get('grant_id') != winner_grant:
            reasons.append(_reason('POINTER_MISMATCH',
                                   'current grant pointer names %r' % (pointer.get('grant_id'),)))
        if token is not None and _int(pointer.get('current_revision')) != token:
            reasons.append(_reason('POINTER_MISMATCH',
                                   'current grant pointer revision %r differs from the issue token %r'
                                   % (pointer.get('current_revision'), token)))
    # A winner operation must show the working-set effect it claims. Its exact
    # rejection/effect mechanism (ROW_COUNT, assertion, receipt shape) is not
    # pinned here; only the recorded result matters.
    if record.get('result') != BACKEND_APPLIED:
        reasons.append(_reason('OBSERVATION_INCOMPLETE',
                               'winner operation recorded %r instead of a working-set application'
                               % (record.get('result'),)))


def _validate_token_history(evidence, identities, final, reasons):
    namespace = evidence['store'].get('namespace')
    task = identities['task_id']
    issue = final['issues'].get((task,))
    if issue is None:
        return
    token = _int(issue.get('row_lock'))
    if token is None:
        return
    rows = [row for row in final['token_history'].values() if _int(row.get('row_token')) == token]
    if len(rows) != 1:
        # No token history at all is missing evidence, not an observed defect.
        # An ambiguous count is likewise unverifiable. Neither may pass.
        reasons.append(_reason('OBSERVATION_INCOMPLETE',
                               'conflict token %r has %d token-history rows' % (token, len(rows))))
        return
    if rows[0].get('store_incarnation') != namespace:
        reasons.append(_reason('TOKEN_NOT_BOUND', 'token history is bound to another namespace'))
    if rows[0].get('operation_id') != identities['winner_operation_ids'][0]:
        reasons.append(_reason('TOKEN_NOT_BOUND',
                               'conflict token is bound to operation %r, not the winner'
                               % (rows[0].get('operation_id'),)))


def _validate_journal(evidence, identities, reasons):
    cm = evidence['cm']
    if not isinstance(cm, dict):
        reasons.append(_reason('EVIDENCE_MISSING', 'companion journal observations are missing'))
        return
    history = cm.get('history')
    counts = cm.get('dispatch_counts')
    if not isinstance(history, dict) or not isinstance(counts, dict):
        reasons.append(_reason('EVIDENCE_MISSING',
                               'companion journal history and dispatch counts are required'))
        return
    stale = list(identities['stale_operation_ids'])
    winners = list(identities['winner_operation_ids'])
    for operation_id in stale + winners:
        if operation_id not in history:
            reasons.append(_reason('EVIDENCE_MISSING',
                                   'no journal observation for %s' % operation_id,
                                   operation_id=operation_id))
    for operation_id in stale:
        kinds = history.get(operation_id)
        if kinds is None:
            continue
        if not _valid_journal(kinds):
            reasons.append(_reason('JOURNAL_HISTORY_INVALID',
                                   'journal history for %s is not a valid chain: %r'
                                   % (operation_id, kinds), operation_id=operation_id))
            continue
        if CM_APPLIED in kinds:
            # CM must not falsely accept the stale operation.
            reasons.append(_reason('STALE_SUCCESS_RECEIPT',
                                   'companion journal records %s for the stale operation'
                                   % CM_APPLIED, operation_id=operation_id))
        elif CM_UNKNOWN not in kinds:
            # An operation with no terminal at all is unproven, not a false
            # accept: the protected route may simply not have closed yet.
            reasons.append(_reason('JOURNAL_HISTORY_INVALID',
                                   'stale operation %s reached no uncertain terminal'
                                   % operation_id, operation_id=operation_id))
        elif CM_DISPATCHED not in kinds:
            # Without a dispatch consumption the protected route was never
            # exercised, so a clean final state proves nothing about the fence.
            reasons.append(_reason('DISPATCH_UNOBSERVED',
                                   'stale operation %s was never dispatched through the protected '
                                   'route, so the fence was not tested' % operation_id,
                                   operation_id=operation_id))
    for operation_id in winners:
        kinds = history.get(operation_id)
        if kinds is None:
            continue
        if not _valid_journal(kinds):
            reasons.append(_reason('JOURNAL_HISTORY_INVALID',
                                   'journal history for %s is not a valid chain: %r'
                                   % (operation_id, kinds), operation_id=operation_id))
            continue
        if CM_APPLIED not in kinds:
            reasons.append(_reason('OBSERVATION_INCOMPLETE',
                                   'winner operation %s has no applied receipt' % operation_id,
                                   operation_id=operation_id))
    for operation_id in stale + winners:
        count = counts.get(operation_id)
        if count is None:
            reasons.append(_reason('DISPATCH_UNOBSERVED',
                                   'no dispatch observation for %s' % operation_id,
                                   operation_id=operation_id))
        elif not isinstance(count, int) or isinstance(count, bool):
            reasons.append(_reason('EVIDENCE_SCHEMA_INVALID',
                                   'dispatch count for %s is not an integer' % operation_id,
                                   operation_id=operation_id))
        elif count == 0:
            reasons.append(_reason('DISPATCH_UNOBSERVED',
                                   'operation %s was never dispatched' % operation_id,
                                   operation_id=operation_id))
        elif count > 1:
            reasons.append(_reason('DUPLICATE_DISPATCH',
                                   'operation %s was dispatched %d times' % (operation_id, count),
                                   operation_id=operation_id))
    # The live driver retains the actual immutable intent in every journal
    # event, as well as its observed chain/replay checks. Component-only
    # fixtures may supply the smaller history grammar above.
    if 'bindings' in cm:
        bindings = cm['bindings']
        if not isinstance(bindings, dict):
            reasons.append(_reason('EVIDENCE_SCHEMA_INVALID', 'CM bindings are not a mapping'))
            return
        for operation_id in stale + winners:
            values = bindings.get(operation_id)
            kinds = history.get(operation_id, [])
            if not isinstance(values, list) or len(values) != len(kinds) or not values \
                    or any(not isinstance(value, dict) for value in values):
                reasons.append(_reason('JOURNAL_HISTORY_INVALID', 'complete per-event intent bindings required'))
                continue
            first = values[0]
            expected_actor = identities['stale_actor']
            expected_grant = identities['stale_grant_id']
            expected = dict(operation_id=operation_id, backend_operation_id=operation_id,
                            native_task_id=identities['task_id'], actor=expected_actor,
                            grant_id=expected_grant, store_incarnation=evidence['store'].get('namespace'),
                            selection_digest=evidence['store'].get('selection_digest'))
            if any(value != first for value in values) or any(first.get(k) != v for k, v in expected.items()):
                reasons.append(_reason('JOURNAL_HISTORY_INVALID', 'journal intent identity changed or is foreign'))
            record = evidence['operations'].get(operation_id)
            if isinstance(record, dict) and record.get('intent_binding') != first:
                reasons.append(_reason('OPERATION_RECORD_DISAGREEMENT', 'backend and companion intents disagree'))
        if cm.get('internal_chain') != 'VERIFIED' or cm.get('projection_replay') != 'VERIFIED':
            reasons.append(_reason('JOURNAL_HISTORY_INVALID', 'companion chain or projection replay is not verified'))


def _valid_journal(kinds):
    """Mirror the companion ledger's practical history grammar."""
    if not isinstance(kinds, list) or not kinds:
        return False
    if any(kind not in CM_KINDS for kind in kinds):
        return False
    if kinds[0] != CM_INTENT:
        return False
    if CM_DISPATCHED in kinds:
        if len(kinds) < 2 or kinds[1] != CM_DISPATCHED or kinds.count(CM_DISPATCHED) != 1:
            return False
        terminals = kinds[2:]
    else:
        terminals = kinds[1:]
    if any(kind not in (CM_APPLIED, CM_UNKNOWN) for kind in terminals):
        return False
    if len(terminals) > 2:
        return False
    if len(terminals) == 2 and terminals != [CM_UNKNOWN, CM_APPLIED]:
        return False
    return True


def _changed_scope(identities):
    """Exactly which rows a legitimate transfer may rewrite.

    Rows outside this scope must survive untouched even inside the tables the
    transfer is allowed to change. Classifying a whole table as 'affected' and
    then ignoring it would let unrelated work vanish unnoticed.
    """
    task = identities['task_id']
    return {
        'issues': {task},
        'leases': {task},
        'grants': None,          # resolved per row by task_id
        'grant_history': {identities['stale_grant_id'], identities['winner_grant_id']},
        'current_grants': {task},
        'token_history': None,    # resolved per row by operation id
        'operations': set(identities['winner_operation_ids']),
        'metadata': None,         # the whole table is read-only here
    }


def _in_scope(table, row, identities):
    scope = _changed_scope(identities)
    if table == 'grants':
        return row.get('task_id') == identities['task_id']
    if table == 'token_history':
        return row.get('operation_id') == identities['winner_operation_ids'][0]
    if table == 'metadata':
        return False
    allowed = scope.get(table)
    return allowed is not None and any(row.get(field) in allowed for field in TABLE_KEYS[table])


def _validate_unaffected(before, final, identities, reasons):
    """Every row outside the transfer's scope must survive unchanged."""
    for table, rows in before.items():
        for identity, row in rows.items():
            if _in_scope(table, row, identities):
                continue
            current = final.get(table, {}).get(identity)
            if current is None:
                reasons.append(_reason('ROW_LOST',
                                       'out-of-scope %s row %r disappeared' % (table, identity),
                                       table=table))
            elif current != row:
                reasons.append(_reason('UNEXPLAINED_CHANGE',
                                       'out-of-scope %s row %r changed' % (table, identity),
                                       table=table))
    for table, rows in final.items():
        for identity, row in rows.items():
            if _in_scope(table, row, identities):
                continue
            if identity not in before.get(table, {}):
                reasons.append(_reason('UNEXPLAINED_CHANGE',
                                       'unexpected %s row %r appeared' % (table, identity),
                                       table=table))


def _validate_grant_history(final, identities, reasons, namespace=None, authorization=None, baseline=None):
    """The append-only transfer record must actually exist.

    The adopted protocol tombstones the prior grant and mints the successor in
    the same transaction, and history is never removed. A final readback with
    no such rows cannot be a pass.
    """
    rows = final['grant_history']
    expected = {identities['stale_grant_id']: 'TOMBSTONED',
                identities['winner_grant_id']: 'MINTED'}
    seen = {}
    for identity, row in rows.items():
        if (baseline or {}).get(identity) == row:
            continue
        grant_id = row.get('grant_id')
        kind = row.get('event_kind')
        if grant_id in expected and kind == expected[grant_id]:
            seen.setdefault(grant_id, []).append(row)
            if namespace is not None and row.get('store_incarnation') != namespace:
                reasons.append(_reason('GRANT_HISTORY_FOREIGN', 'transfer history belongs to another namespace'))
            if _utc(authorization) is not None and _utc(row.get('event_utc')) != _utc(authorization):
                reasons.append(_reason('GRANT_HISTORY_INCOMPLETE', 'history time differs from transfer authorization'))
        elif kind in ('TOMBSTONED', 'MINTED') and grant_id not in expected:
            reasons.append(_reason('GRANT_HISTORY_FOREIGN',
                                   'grant history records %s for unrelated grant %r'
                                   % (kind, grant_id)))
    for grant_id, kind in expected.items():
        if len(seen.get(grant_id, [])) != 1:
            reasons.append(_reason('GRANT_HISTORY_INCOMPLETE',
                                   'grant history requires one %s row for grant %r' % (kind, grant_id)))


def _validate_controls(evidence, identities, reasons):
    controls = evidence.get('controls')
    if not isinstance(controls, dict):
        reasons.append(_reason('CONTROL_NOT_EXECUTED', 'control results are missing'))
        return
    for name in ('positive', 'disabled'):
        if name not in controls:
            reasons.append(_reason('CONTROL_NOT_EXECUTED', '%s control was not executed' % name))
            continue
        control = controls[name]
        if not isinstance(control, dict) or control.get('executed') is not True:
            reasons.append(_reason('CONTROL_NOT_EXECUTED',
                                   '%s control did not actually execute' % name))
            continue
        if name == 'positive':
            if control.get('applied') is not True:
                reasons.append(_reason('CONTROL_INEFFECTIVE',
                                       'the current-owner positive control did not succeed, so the '
                                       'harness cannot show the fenced path still works'))
            if control.get('fence_refused') is not False:
                reasons.append(_reason('CONTROL_INEFFECTIVE',
                                       'the positive control was refused, so it proves nothing about '
                                       'a working fence'))
        else:
            disabled = control.get('disabled_components')
            if not isinstance(disabled, list) or not disabled:
                reasons.append(_reason('CONTROL_CAUSALITY_UNPROVEN',
                                       'the disabled comparison must name the fence components it '
                                       'disables'))
            if control.get('preserved_transfer') is not True:
                reasons.append(_reason('CONTROL_CAUSALITY_UNPROVEN',
                                       'the disabled comparison must preserve the legitimate transfer'))
            if control.get('unrelated_conflict_absent') is not True:
                reasons.append(_reason('CONTROL_CAUSALITY_UNPROVEN',
                                       'an unrelated database conflict cannot protect both arms'))
            if control.get('unsafe_effect_observed') is not True:
                # The disabled arm failed to expose the unsafe baseline. That
                # is INCONCLUSIVE, never a reason to weaken the enabled fence.
                reasons.append(_reason('CONTROL_INEFFECTIVE',
                                       'the fence-disabled comparison did not demonstrate the unsafe '
                                       'baseline, so the negative control is ineffective'))


def _validate_refusal(evidence, reasons):
    """A pass must establish that the protected mechanism refused the write.

    A clean final state is not enough on its own: if nothing shows the fence
    rejected the stale operation, the run has not demonstrated the fence at
    all. An unattributed or absent refusal is therefore never a pass.
    """
    refusal = evidence.get('refusal')
    if not isinstance(refusal, dict) or set(refusal) != {'by', 'code'}:
        reasons.append(_reason('REFUSAL_UNKNOWN',
                               'no attributable refusal evidence for the stale operation'))
        return
    by = refusal['by']
    if by == 'fence':
        return
    if by is None:
        reasons.append(_reason('REFUSAL_UNKNOWN',
                               'the stale operation was refused with no attributable source, so the '
                               'protected fence was never shown to reject it'))
        return
    if by == 'other':
        reasons.append(_reason('REFUSAL_UNRELATED',
                               'refusal came from %r, not from the fence'
                               % (refusal.get('code'),)))
        return
    # Any other reason code, including ones this build does not know, is
    # unattributed. It must never fall through to PASSED.
    reasons.append(_reason('REFUSAL_UNKNOWN',
                           'unattributed refusal reason %r' % (by,)))


def _validate_evidence_shape(evidence, reasons):
    if not isinstance(evidence, dict):
        reasons.append(_reason('EVIDENCE_SCHEMA_INVALID', 'evidence is not a mapping'))
        return False
    required = ('schema_version', 'run_id', 'source', 'runtime', 'store', 'identities',
                'observations', 'operations', 'cm', 'controls')
    missing = sorted(set(required) - set(evidence))
    if missing:
        reasons.append(_reason('EVIDENCE_MISSING', 'evidence is missing sections %r' % (missing,)))
        return False
    if evidence['schema_version'] != EVIDENCE_SCHEMA_VERSION:
        reasons.append(_reason('EVIDENCE_SCHEMA_VERSION',
                               'evidence schema version %r is not %d'
                               % (evidence['schema_version'], EVIDENCE_SCHEMA_VERSION)))
    if _text(evidence['run_id']) is None:
        reasons.append(_reason('EVIDENCE_SCHEMA_INVALID', 'run_id is unreadable'))
    identities = evidence['identities']
    if not isinstance(identities, dict):
        reasons.append(_reason('EVIDENCE_SCHEMA_INVALID', 'identities section is not a mapping'))
        return False
    for key in ('task_id', 'stale_actor', 'winner', 'stale_grant_id',
                'winner_grant_id', 'expected_title'):
        if _text(identities.get(key)) is None:
            reasons.append(_reason('EVIDENCE_SCHEMA_INVALID', 'identities.%s is unreadable' % key))
    for key in ('stale_operation_ids', 'winner_operation_ids'):
        value = identities.get(key)
        if not isinstance(value, list) or not value or \
                any(_text(item) is None for item in value):
            reasons.append(_reason('EVIDENCE_SCHEMA_INVALID',
                                   'identities.%s must be a non-empty list of identifiers' % key))
    for key in ('source', 'runtime', 'store'):
        if not isinstance(evidence[key], dict):
            reasons.append(_reason('EVIDENCE_SCHEMA_INVALID', '%s section is not a mapping' % key))
    observations = evidence['observations']
    if not isinstance(observations, dict):
        reasons.append(_reason('OBSERVATION_INCOMPLETE', 'observations section is not a mapping'))
    if not isinstance(evidence['operations'], dict):
        reasons.append(_reason('EVIDENCE_MISSING', 'operations section is not a mapping'))
    if not isinstance(evidence['cm'], dict):
        reasons.append(_reason('EVIDENCE_MISSING', 'cm section is not a mapping'))
    if not isinstance(evidence['controls'], dict):
        reasons.append(_reason('CONTROL_NOT_EXECUTED', 'controls section is not a mapping'))
    # Deep validation runs only when every container has the expected type, so
    # malformed evidence becomes a reason instead of an exception.
    containers_ok = (all(isinstance(evidence[key], dict)
                         for key in ('source', 'runtime', 'store', 'identities', 'operations',
                                     'cm', 'controls', 'observations'))
                     and all(isinstance(identities.get(key), list)
                             for key in ('stale_operation_ids', 'winner_operation_ids')))
    return containers_ok


def validate_evidence(evidence):
    """Every reason this evidence carries, in code order. Empty means nothing
    was found against it. This is the only place verdicts are decided."""
    reasons = []
    if not _validate_evidence_shape(evidence, reasons):
        return reasons
    identities = evidence['identities']
    _validate_identity(evidence, reasons)
    _validate_barrier(evidence, identities, reasons)
    observations = evidence['observations']
    before = _state(observations.get('before'), 'S0', reasons)
    after_transfer = _state(observations.get('after_transfer'), 'S1', reasons)
    final = _state(observations.get('final'), 'S2', reasons)
    if before is not None and after_transfer is not None and final is not None:
        _validate_final_state(evidence, identities, before, after_transfer, final, reasons)
    _validate_operation_snapshot_agreement(
        final, identities, evidence['operations'], reasons,
        {'before': before, 'after_transfer': after_transfer},
        compare_records=not isinstance(evidence.get('harness_errors', []), list) or not any(
            str(error).startswith('operation_records:') for error in evidence.get('harness_errors', [])))
    _validate_journal(evidence, identities, reasons)
    _validate_controls(evidence, identities, reasons)
    _validate_refusal(evidence, reasons)
    errors = evidence.get('harness_errors', [])
    if not isinstance(errors, list) or any(_text(error) is None for error in errors):
        reasons.append(_reason('EVIDENCE_SCHEMA_INVALID', 'harness_errors is not an observed error list'))
    else:
        for error in errors:
            reasons.append(_reason('HARNESS_ERROR', error))
    reasons.sort(key=lambda item: (item['severity'] != UNSAFE, item['code'], item['detail']))
    return reasons


def judge_evidence(evidence):
    """The one canonical verdict function.

    PASSED requires zero reasons: every mandatory observation, identity and
    both controls. An observed unsafe effect fails even when other evidence
    is incomplete. Anything unverifiable is INCONCLUSIVE, never PASSED.
    """
    reasons = validate_evidence(evidence)
    if any(reason['severity'] == UNSAFE for reason in reasons):
        verdict = FAILED
    elif reasons:
        verdict = INCONCLUSIVE
    else:
        verdict = PASSED
    return {
        'verdict': verdict,
        'reasons': reasons,
        'unsafe': [reason['code'] for reason in reasons if reason['severity'] == UNSAFE],
        'unproven': [reason['code'] for reason in reasons if reason['severity'] == UNPROVEN],
    }


def inconclusive(reason_code, detail):
    """A single, explicit inconclusive result for harness-level refusals."""
    return {
        'verdict': INCONCLUSIVE,
        'reasons': [_reason(reason_code, detail)],
        'unsafe': [],
        'unproven': [reason_code],
    }
