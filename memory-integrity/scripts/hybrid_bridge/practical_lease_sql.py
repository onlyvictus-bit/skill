"""Unqualified lease-bound title transaction template; no dispatch entry point.

The predecessor adapter remains STOPPED. This builder still needs the matching
v2 scratch schema, protected lease-minting transitions, actual CLI error/rollback
proof, consumer integration, and the real synchronized race. String tests do
not establish Dolt grammar, atomicity, native eligibility, or durability.
"""
from datetime import datetime
import re

from .practical_contract import (
    LeaseGuardedTitleRequest, LeasePracticalSelection, PracticalContractError,
    strict_canonical_json,
)
from .practical_sql import _text

_UTC_FORMATS = ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f')


def _utc(value, field):
    """Pinned second-precision UTC text. Anything else refuses before SQL."""
    if not isinstance(value, str):
        raise PracticalContractError('E_MI2_TIME: %s must be UTC text' % (field,))
    for form in _UTC_FORMATS:
        try:
            datetime.strptime(value, form)
            return value
        except ValueError:
            continue
    raise PracticalContractError('E_MI2_TIME: %s is not pinned UTC YYYY-MM-DD HH:MM:SS[.ffffff]'
                                 % (field,))


def _name(value, field):
    if not isinstance(value, str) or not value.strip():
        raise PracticalContractError('E_MI2_NAME: %s required' % (field,))
    if len(value) > 192:
        raise PracticalContractError('E_MI2_NAME: %s over length' % (field,))
    return value


def v2_schema_sql():
    """Matching v2 scratch schema: grants, append-only history, metadata,
    token history, operations and the assert procedure. No DELETE, DROP,
    DOLT_ADD or DOLT_COMMIT anywhere: history is tombstoned, never removed."""
    return '\n'.join([
        'CREATE TABLE IF NOT EXISTS mi_practical_v2_grants ('
        'store_incarnation VARCHAR(192) NOT NULL, grant_id VARCHAR(192) NOT NULL, '
        'task_id VARCHAR(192) NOT NULL, actor VARCHAR(192) NOT NULL, '
        'status VARCHAR(64) NOT NULL, fixed_deadline_utc DATETIME(6) NOT NULL, '
        'issue_revision BIGINT NOT NULL, tombstoned TINYINT NOT NULL DEFAULT 0, '
        'lease_node VARCHAR(192) NOT NULL, lease_granted_at DATETIME(6) NOT NULL, '
        'lease_expiry DATETIME(6) NOT NULL, lease_heartbeat DATETIME(6) NOT NULL, '
        'PRIMARY KEY(store_incarnation, grant_id));',
        'CREATE TABLE IF NOT EXISTS mi_practical_v2_grant_history ('
        'store_incarnation VARCHAR(192) NOT NULL, grant_id VARCHAR(192) NOT NULL, '
        'event_kind VARCHAR(64) NOT NULL, event_utc DATETIME(6) NOT NULL, '
        'details LONGTEXT NOT NULL, '
        'PRIMARY KEY(store_incarnation, grant_id, event_kind, event_utc));',
        'CREATE TABLE IF NOT EXISTS mi_practical_v2_metadata ('
        'store_incarnation VARCHAR(192) NOT NULL, namespace_key VARCHAR(96) NOT NULL, '
        'selection_digest CHAR(64) NOT NULL, native_node_id VARCHAR(192) NOT NULL, '
        'PRIMARY KEY(store_incarnation, namespace_key));',
        'CREATE TABLE IF NOT EXISTS mi_practical_v2_token_history ('
        'store_incarnation VARCHAR(192) NOT NULL, row_token BIGINT NOT NULL, '
        'operation_id VARCHAR(192) NOT NULL, PRIMARY KEY(store_incarnation, row_token), '
        'UNIQUE KEY mi2_token_operation(store_incarnation, operation_id));',
        'CREATE TABLE IF NOT EXISTS mi_practical_v2_operations ('
        'store_incarnation VARCHAR(192) NOT NULL, operation_id VARCHAR(192) NOT NULL, '
        'command_digest CHAR(64) NOT NULL, binding_json LONGTEXT NOT NULL, '
        'receipt_json LONGTEXT NOT NULL, authorization_time DATETIME(6) NOT NULL, '
        'resulting_row_lock BIGINT NOT NULL, '
        'PRIMARY KEY(store_incarnation, operation_id), '
        'UNIQUE KEY mi2_operation_digest(store_incarnation, operation_id, command_digest));',
        'CREATE PROCEDURE IF NOT EXISTS mi_practical_assert_v2(cond BOOL, err VARCHAR(192)) '
        "BEGIN IF NOT cond THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = err; END IF; END;",
    ])


def _transition_prologue():
    return ['START TRANSACTION;',
            'SET @mi2_auth = UTC_TIMESTAMP();']


def _lease_live_assert(task, holder, node, granted, expiry, heartbeat):
    """The supplied lease snapshot must equal a live native lease row at DB
    authorization time. Liveness is DB-clock compared; no caller now value."""
    return [
        "CALL mi_practical_assert_v2((SELECT COUNT(*) FROM leases AS l "
        'WHERE l.issue_id = ' + task + ' AND l.holder = ' + holder
        + ' AND l.granted_node = ' + node + ' AND l.granted_at = ' + granted
        + ' AND l.lease_expires_at = ' + expiry + ' AND l.heartbeat_at = ' + heartbeat
        + ' AND l.lease_expires_at > @mi2_auth'
        + ") = 1, 'E_MI2_LEASE_MISMATCH');",
    ]


def _transition_epilogue():
    return ['COMMIT;']


def _digest64(value, field):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value or ''):
        raise PracticalContractError('E_MI2_DIGEST: %s must be 64 hex' % (field,))
    return value


def _lease_snapshot(lease_node, granted_at_utc, expiry_utc, heartbeat_utc):
    node = _text(_name(lease_node, 'lease_node'))
    granted = _text(_utc(granted_at_utc, 'lease_granted_at_utc'))
    expiry = _text(_utc(expiry_utc, 'lease_expiry_utc'))
    heartbeat = _text(_utc(heartbeat_utc, 'lease_heartbeat_utc'))
    return node, granted, expiry, heartbeat


def initial_claim_grant_sql(store_incarnation, task_id, actor, new_grant_id,
                            fixed_deadline_utc, lease_node, lease_granted_at_utc,
                            lease_expiry_utc, lease_heartbeat_utc,
                            selection_digest, native_node_id):
    """First protected grant: refuses when the grant id already exists anywhere
    in this store incarnation. Caller proposes, PRIMARY KEY disposes. The
    observed lease snapshot is stored on the grant row; the namespace identity
    row is minted here if absent, never overwritten."""
    incarnation = _text(_name(store_incarnation, 'store_incarnation'))
    task = _text(_name(task_id, 'task_id'))
    who = _text(_name(actor, 'actor'))
    grant = _text(_name(new_grant_id, 'new_grant_id'))
    _utc(fixed_deadline_utc, 'fixed_deadline_utc')
    deadline = _text(fixed_deadline_utc)
    node, granted, expiry, heartbeat = _lease_snapshot(
        lease_node, lease_granted_at_utc, lease_expiry_utc, lease_heartbeat_utc)
    digest = _text(_digest64(selection_digest, 'selection_digest'))
    native = _text(_name(native_node_id, 'native_node_id'))
    statements = _transition_prologue()
    statements.extend([
        "CALL mi_practical_assert_v2((SELECT COUNT(*) FROM mi_practical_v2_grants "
        'WHERE store_incarnation = ' + incarnation + ' AND grant_id = ' + grant
        + ") = 0, 'E_MI2_GRANT_REUSE');",
    ])
    statements.extend(_lease_live_assert(task, who, node, granted, expiry, heartbeat))
    statements.extend([
        'INSERT INTO mi_practical_v2_grants(store_incarnation,grant_id,task_id,actor,'
        'status,fixed_deadline_utc,issue_revision,tombstoned,'
        'lease_node,lease_granted_at,lease_expiry,lease_heartbeat) VALUES ('
        + incarnation + ',' + grant + ',' + task + ',' + who
        + ",'GRANTED'," + deadline + ',0,0,'
        + node + ',' + granted + ',' + expiry + ',' + heartbeat + ');',
        'SET @mi2_grant_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_grant_changed = 1, 'E_MI2_GRANT_CARDINALITY');",
        'INSERT INTO mi_practical_v2_grant_history(store_incarnation,grant_id,event_kind,'
        'event_utc,details) VALUES (' + incarnation + ',' + grant
        + ",'MINTED',@mi2_auth,'initial-claim');",
        'SET @mi2_history_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_history_changed = 1, 'E_MI2_HISTORY_CARDINALITY');",
        # Namespace identity is DB-created once per incarnation, then only read
        # back. A real statement error aborts the batch; zero affected rows
        # simply means this incarnation was already minted by an earlier claim.
        'INSERT INTO mi_practical_v2_metadata(store_incarnation,namespace_key,'
        'selection_digest,native_node_id) SELECT ' + incarnation + ",'identity',"
        + digest + ',' + native
        + ' WHERE NOT EXISTS (SELECT 1 FROM mi_practical_v2_metadata '
        'WHERE store_incarnation = ' + incarnation + " AND namespace_key = 'identity');",
    ])
    statements.extend(_transition_epilogue())
    return '\n'.join(statements)


def reassign_grant_sql(store_incarnation, task_id, prior_grant_id, new_grant_id,
                       actor, fixed_deadline_utc, lease_node, lease_granted_at_utc,
                       lease_expiry_utc, lease_heartbeat_utc):
    """Ownership transfer: tombstones the prior grant row, mints a fresh one,
    appends both history rows. The prior row is never deleted. The fresh row
    carries the newly observed lease snapshot."""
    incarnation = _text(_name(store_incarnation, 'store_incarnation'))
    task = _text(_name(task_id, 'task_id'))
    prior = _text(_name(prior_grant_id, 'prior_grant_id'))
    grant = _text(_name(new_grant_id, 'new_grant_id'))
    if prior_grant_id == new_grant_id:
        raise PracticalContractError('E_MI2_GRANT_REUSE: new grant must differ from prior')
    who = _text(_name(actor, 'actor'))
    _utc(fixed_deadline_utc, 'fixed_deadline_utc')
    deadline = _text(fixed_deadline_utc)
    node, granted, expiry, heartbeat = _lease_snapshot(
        lease_node, lease_granted_at_utc, lease_expiry_utc, lease_heartbeat_utc)
    statements = _transition_prologue()
    statements.extend([
        "CALL mi_practical_assert_v2((SELECT COUNT(*) FROM mi_practical_v2_grants "
        'WHERE store_incarnation = ' + incarnation + ' AND grant_id = ' + prior
        + ' AND task_id = ' + task + ' AND tombstoned = 0'
        + ") = 1, 'E_MI2_PRIOR_GRANT');",
        "CALL mi_practical_assert_v2((SELECT COUNT(*) FROM mi_practical_v2_grants "
        'WHERE store_incarnation = ' + incarnation + ' AND grant_id = ' + grant
        + ") = 0, 'E_MI2_GRANT_REUSE');",
    ])
    statements.extend(_lease_live_assert(task, who, node, granted, expiry, heartbeat))
    statements.extend([
        'UPDATE mi_practical_v2_grants SET tombstoned = 1 WHERE store_incarnation = '
        + incarnation + ' AND grant_id = ' + prior + ' AND task_id = ' + task
        + ' AND tombstoned = 0;',
        'SET @mi2_tomb_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_tomb_changed = 1, 'E_MI2_TOMB_CARDINALITY');",
        'INSERT INTO mi_practical_v2_grants(store_incarnation,grant_id,task_id,actor,'
        'status,fixed_deadline_utc,issue_revision,tombstoned,'
        'lease_node,lease_granted_at,lease_expiry,lease_heartbeat) VALUES ('
        + incarnation + ',' + grant + ',' + task + ',' + who
        + ",'GRANTED'," + deadline + ',0,0,'
        + node + ',' + granted + ',' + expiry + ',' + heartbeat + ');',
        'SET @mi2_grant_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_grant_changed = 1, 'E_MI2_GRANT_CARDINALITY');",
        'INSERT INTO mi_practical_v2_grant_history(store_incarnation,grant_id,event_kind,'
        'event_utc,details) VALUES (' + incarnation + ',' + prior
        + ",'TOMBSTONED',@mi2_auth,'reassign');",
        'INSERT INTO mi_practical_v2_grant_history(store_incarnation,grant_id,event_kind,'
        'event_utc,details) VALUES (' + incarnation + ',' + grant
        + ",'MINTED',@mi2_auth,'reassign');",
    ])
    statements.extend(_transition_epilogue())
    return '\n'.join(statements)


def _retire_grant_sql(kind, store_incarnation, task_id, grant_id, at_utc):
    incarnation = _text(_name(store_incarnation, 'store_incarnation'))
    task = _text(_name(task_id, 'task_id'))
    grant = _text(_name(grant_id, 'grant_id'))
    _utc(at_utc, 'at_utc')
    check = ('SELECT COUNT(*) FROM mi_practical_v2_grants WHERE store_incarnation = '
             + incarnation + ' AND grant_id = ' + grant
             + ' AND task_id = ' + task + ' AND tombstoned = 0')
    update = ('UPDATE mi_practical_v2_grants SET tombstoned = 1 WHERE store_incarnation = '
              + incarnation + ' AND grant_id = ' + grant + ' AND task_id = ' + task
              + ' AND tombstoned = 0')
    history = ('INSERT INTO mi_practical_v2_grant_history'
               '(store_incarnation,grant_id,event_kind,event_utc,details) VALUES ('
               + incarnation + ',' + grant + ',' + _text(kind)
               + ',@mi2_auth,' + _text(kind.lower()) + ')')
    statements = _transition_prologue()
    statements.append("CALL mi_practical_assert_v2((" + check + ") = 1, 'E_MI2_PRIOR_GRANT');")
    statements.append(update + ';')
    statements.append('SET @mi2_tomb_changed = ROW_COUNT();')
    statements.append("CALL mi_practical_assert_v2(@mi2_tomb_changed = 1, 'E_MI2_TOMB_CARDINALITY');")
    statements.append(history + ';')
    statements.extend(_transition_epilogue())
    return '\n'.join(statements)


def release_grant_sql(store_incarnation, task_id, grant_id, at_utc):
    """Voluntary release: tombstone plus history. Bytes retained, never deleted."""
    return _retire_grant_sql('RELEASED', store_incarnation, task_id, grant_id, at_utc)


def reclaim_grant_sql(store_incarnation, task_id, grant_id, at_utc):
    """Expiry reclaim: tombstone plus history. Bytes retained, never deleted."""
    return _retire_grant_sql('RECLAIMED', store_incarnation, task_id, grant_id, at_utc)


def verify_heartbeat_sql(store_incarnation, task_id, holder, node):
    """Heartbeat liveness verification only: asserts exactly one live native
    lease row for this holder on this node at DB authorization time. Emits no
    INSERT, UPDATE or DELETE and never re-arms anything: a missing, expired,
    foreign or mismatched lease refuses here instead of falling back."""
    _name(store_incarnation, 'store_incarnation')
    task = _text(_name(task_id, 'task_id'))
    who = _text(_name(holder, 'holder'))
    where = _text(_name(node, 'node'))
    statements = _transition_prologue()
    statements.append(
        "CALL mi_practical_assert_v2((SELECT COUNT(*) FROM leases AS l "
        'WHERE l.issue_id = ' + task + ' AND l.holder = ' + who
        + ' AND l.granted_node = ' + where + ' AND l.lease_expires_at > @mi2_auth'
        + ") = 1, 'E_MI2_HEARTBEAT');")
    statements.append(
        'SELECT l.issue_id,l.holder,l.granted_node,l.lease_expires_at FROM leases AS l '
        'WHERE l.issue_id = ' + task + ' AND l.holder = ' + who
        + ' AND l.granted_node = ' + where + ' AND l.lease_expires_at > @mi2_auth;')
    statements.extend(_transition_epilogue())
    return '\n'.join(statements)


def _title_batch(selection, request, pause_seconds=None):
    selection = LeasePracticalSelection.from_value(selection)
    request = LeaseGuardedTitleRequest.from_value(request)
    if selection.native_node_id != request.lease_granted_node:
        raise PracticalContractError('E_MI2_FOREIGN_LEASE_NODE')
    predicate = ' AND '.join([
        'i.id = ' + _text(request.task_id),
        'i.status = ' + _text('in_progress'),
        'i.assignee = ' + _text(request.actor),
        'i.row_lock = ' + str(request.expected_row_lock),
        'i.ephemeral = 0',
        'l.issue_id = i.id',
        'l.holder = ' + _text(request.lease_holder),
        'l.granted_node = ' + _text(request.lease_granted_node),
        'l.granted_at = ' + _text(request.lease_granted_at_utc),
        'l.lease_expires_at = ' + _text(request.lease_expires_at_utc),
        'l.heartbeat_at = ' + _text(request.lease_heartbeat_at_utc),
        '@mi2_auth < l.lease_expires_at',
        'g.grant_id = ' + _text(request.grant_id),
        'g.task_id = i.id', 'g.actor = i.assignee', 'g.tombstoned = 0',
        'g.issue_revision = i.row_lock',
        'g.lease_node = l.granted_node', 'g.lease_granted_at = l.granted_at',
        'g.lease_expiry = l.lease_expires_at', 'g.lease_heartbeat = l.heartbeat_at',
        'g.store_incarnation = m.store_incarnation',
        'm.namespace_key = ' + _text('identity'),
        'm.store_incarnation = ' + _text(selection.incarnation),
        'm.selection_digest = ' + _text(selection.digest),
        'm.native_node_id = l.granted_node',
        'DATABASE() = ' + _text(selection.database),
        'active_branch() = ' + _text('main'),
        'NOT EXISTS (SELECT 1 FROM dependencies AS d WHERE d.issue_id = i.id)',
    ])
    # The read starts the actual transaction snapshot before a native harness
    # pause. It is not a locking read, and not a client-side permission check.
    authority = ('SELECT COUNT(*) FROM issues AS i JOIN leases AS l ON l.issue_id = i.id '
                 'JOIN mi_practical_v2_grants AS g ON g.task_id = i.id '
                 'JOIN mi_practical_v2_metadata AS m ON m.store_incarnation = g.store_incarnation '
                 'WHERE ' + predicate)
    binding = request.as_dict()
    binding.update(selection_digest=selection.digest, store_incarnation=selection.incarnation,
                   database=selection.database, branch='main', native_node_id=selection.native_node_id)
    receipt = dict(binding, status='WORKING_SET_APPLIED', evidence_class='NATIVE_OBSERVED_UNQUALIFIED',
                   native_write_qualified=False, head_committed=False,
                   backend_operation_id=request.operation_id, native_task_id=request.task_id,
                   original_row_lock=request.expected_row_lock, fixed_deadline_utc=request.fixed_deadline_utc)
    binding_json = _text(strict_canonical_json(binding).decode('utf-8'))
    receipt_json = _text(strict_canonical_json(receipt).decode('utf-8'))
    namespace = _text(selection.incarnation)
    op = _text(request.operation_id)
    task = _text(request.task_id)
    grant = _text(request.grant_id)
    digest = _text(request.command_digest)
    statements = [
        'START TRANSACTION;',
        'SET @mi2_auth = UTC_TIMESTAMP();',
        'SET @mi2_authorized = (' + authority + ');',
        "CALL mi_practical_assert_v2(@mi2_authorized = 1, 'E_MI2_AUTH');",
        'SET @mi2_operation_exists = (SELECT COUNT(*) FROM mi_practical_v2_operations '
        'WHERE store_incarnation = ' + namespace + ' AND operation_id = ' + op + ');',
        "CALL mi_practical_assert_v2(@mi2_operation_exists = 0, 'E_MI2_OPERATION_REPLAY');",
    ]
    if pause_seconds is not None:
        if type(pause_seconds) is not int or not 1 <= pause_seconds <= 30:
            raise ValueError('E_MI2_HARNESS_PAUSE')
        statements.append('DO SLEEP(%d);' % pause_seconds)
    statements.extend([
        'SET @mi2_token = CAST(CONV(SUBSTRING(SHA2(UUID(), 256), 1, 15), 16, 10) AS SIGNED);',
        "CALL mi_practical_assert_v2(@mi2_token > 0 AND @mi2_token <> "
        + str(request.expected_row_lock) + ", 'E_MI2_TOKEN');",
        # One issue UPDATE, never a multi-table update or hidden reassignment.
        'UPDATE issues SET title = ' + _text(request.title) + ', row_lock = @mi2_token '
        'WHERE id = ' + task + ' AND assignee = ' + _text(request.actor)
        + ' AND status = ' + _text('in_progress') + ' AND row_lock = ' + str(request.expected_row_lock) + ';',
        'SET @mi2_issue_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_issue_changed = 1, 'E_MI2_ISSUE_CARDINALITY');",
        'UPDATE mi_practical_v2_grants SET issue_revision = @mi2_token WHERE store_incarnation = '
        + namespace + ' AND grant_id = ' + grant + ' AND task_id = ' + task
        + ' AND issue_revision = ' + str(request.expected_row_lock) + ' AND tombstoned = 0;',
        'SET @mi2_grant_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_grant_changed = 1, 'E_MI2_GRANT_CARDINALITY');",
        # UNIQUE(store_incarnation,row_token) must be in the v2 schema.
        # Collision or any failed assertion must abort the SQL batch; this
        # remains a required real native negative control, not assumed proof.
        'INSERT INTO mi_practical_v2_token_history(store_incarnation,row_token,operation_id) '
        'VALUES (' + namespace + ',@mi2_token,' + op + ');',
        'SET @mi2_token_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_token_changed = 1, 'E_MI2_TOKEN_CARDINALITY');",
        'INSERT INTO mi_practical_v2_operations(store_incarnation,operation_id,command_digest,'
        'binding_json,receipt_json,authorization_time,resulting_row_lock) VALUES ('
        + namespace + ',' + op + ',' + digest + ',' + binding_json
        + ',JSON_SET(CAST(' + receipt_json + " AS JSON),'$.authorization_time_utc',"
        "DATE_FORMAT(@mi2_auth,'%Y-%m-%d %H:%i:%s.%f'),'$.resulting_row_lock',@mi2_token),"
        '@mi2_auth,@mi2_token);',
        'SET @mi2_receipt_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_receipt_changed = 1, 'E_MI2_RECEIPT_CARDINALITY');",
        'COMMIT;',
        'SELECT receipt_json,binding_json,command_digest,authorization_time,resulting_row_lock '
        'FROM mi_practical_v2_operations WHERE store_incarnation = ' + namespace
        + ' AND operation_id = ' + op + ' AND command_digest = ' + digest + ';',
    ])
    return '\n'.join(statements)


def guarded_title_sql(selection, request):
    """Production-shaped SQL; no arbitrary caller barrier/fragment parameter."""
    return _title_batch(selection, request)


def experiment_guarded_title_sql(selection, request, *, pause_seconds):
    """Harness-only bounded pause after actual authorization/snapshot read."""
    return _title_batch(selection, request, pause_seconds)
