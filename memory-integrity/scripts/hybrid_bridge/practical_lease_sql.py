"""Lease-bound SQL builders; native grammar and atomicity remain unqualified.

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


_V2_LOCAL_TABLES = (
    'mi_practical_v2_grants',
    'mi_practical_v2_current_grants',
    'mi_practical_v2_grant_history',
    'mi_practical_v2_metadata',
    'mi_practical_v2_token_history',
    'mi_practical_v2_operations',
)

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


def _same_utc_moment(left, right, field):
    """Refuse a legacy seed whose caller deadline disagrees with its lease."""
    left = _utc(left, field)
    right = _utc(right, field)
    for form in _UTC_FORMATS:
        try:
            left_value = datetime.strptime(left, form)
            break
        except ValueError:
            continue
    for form in _UTC_FORMATS:
        try:
            right_value = datetime.strptime(right, form)
            break
        except ValueError:
            continue
    if left_value != right_value:
        raise PracticalContractError('E_MI2_LEGACY_DEADLINE_LEASE_MISMATCH')


def _binary_equals(column, encoded_value):
    return 'BINARY ' + column + ' = BINARY ' + encoded_value


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
        'lease_node VARCHAR(192) NOT NULL, lease_granted_at DATETIME NOT NULL, '
        'lease_expiry DATETIME NOT NULL, lease_heartbeat DATETIME NOT NULL, '
        'PRIMARY KEY(store_incarnation, grant_id));',
        'CREATE TABLE IF NOT EXISTS mi_practical_v2_current_grants ('
        'store_incarnation VARCHAR(192) NOT NULL, task_id VARCHAR(192) NOT NULL, '
        'grant_id VARCHAR(192) NOT NULL, current_revision BIGINT NOT NULL, '
        'PRIMARY KEY(store_incarnation, task_id), '
        'UNIQUE KEY mi2_current_grant(store_incarnation, grant_id));',
        'CREATE TABLE IF NOT EXISTS mi_practical_v2_grant_history ('
        'store_incarnation VARCHAR(192) NOT NULL, grant_id VARCHAR(192) NOT NULL, '
        'event_kind VARCHAR(64) NOT NULL, event_utc DATETIME(6) NOT NULL, '
        'details LONGTEXT NOT NULL, '
        'PRIMARY KEY(store_incarnation, grant_id, event_kind, event_utc));',
        'CREATE TABLE IF NOT EXISTS mi_practical_v2_metadata ('
        'singleton TINYINT NOT NULL DEFAULT 1, store_incarnation VARCHAR(192) NOT NULL, '
        "namespace_key VARCHAR(96) NOT NULL DEFAULT 'identity', "
        'selection_digest CHAR(64) NULL, native_node_id VARCHAR(192) NULL, '
        'selected_database VARCHAR(192) NULL, selected_main_branch VARCHAR(64) NULL, '
        'PRIMARY KEY(singleton), UNIQUE KEY mi2_metadata_incarnation(store_incarnation));',
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
        "BEGIN IF cond IS NULL OR cond <> TRUE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = err; END IF; END;",
    ])


def v2_dolt_ignore_registration_sql():
    """Register and read back actual local sidecar ignores.

    This generated builder is not evidence that a native server accepted the
    grammar, retained the settings, or left HEAD unchanged.
    """
    inserts = [
        'INSERT INTO dolt_ignore(pattern,ignored) SELECT ' + _text(name) + ',1 '
        'WHERE NOT EXISTS (SELECT 1 FROM dolt_ignore WHERE pattern = ' + _text(name) + ');'
        for name in _V2_LOCAL_TABLES
    ]
    readback = 'SELECT pattern,ignored FROM dolt_ignore WHERE pattern IN (' + ','.join(
        _text(name) for name in _V2_LOCAL_TABLES) + ') ORDER BY pattern;'
    return '\n'.join(inserts + [readback])


def v2_namespace_bootstrap_sql():
    """Mint/read one DB-owned incarnation; never accept a caller incarnation."""
    return '\n'.join([
        'START TRANSACTION;',
        'INSERT INTO mi_practical_v2_metadata(singleton,store_incarnation) '
        'SELECT 1,UUID() WHERE NOT EXISTS '
        '(SELECT 1 FROM mi_practical_v2_metadata WHERE singleton = 1);',
        "CALL mi_practical_assert_v2((SELECT COUNT(*) FROM mi_practical_v2_metadata WHERE singleton = 1) = 1, 'E_MI2_NAMESPACE_CARDINALITY');",
        'COMMIT;',
        'SELECT store_incarnation,namespace_key FROM mi_practical_v2_metadata WHERE singleton = 1;',
    ])


def v2_selection_registration_sql(selection):
    """Bind a selection only after bootstrap readback supplied its incarnation."""
    selection = LeasePracticalSelection.from_value(selection)
    namespace = _text(selection.incarnation)
    digest = _text(selection.digest)
    database = _text(selection.database)
    branch = _text(selection.main_branch)
    node = _text(selection.native_node_id)
    return '\n'.join([
        'START TRANSACTION;',
        'UPDATE mi_practical_v2_metadata SET selection_digest = ' + digest
        + ',native_node_id = ' + node + ',selected_database = ' + database
        + ',selected_main_branch = ' + branch + ' WHERE singleton = 1 AND store_incarnation = '
        + namespace + ' AND selection_digest IS NULL;',
        "CALL mi_practical_assert_v2((SELECT COUNT(*) FROM mi_practical_v2_metadata WHERE singleton = 1 AND store_incarnation = "
        + namespace + ' AND selection_digest = ' + digest + ' AND native_node_id = ' + node
        + ' AND selected_database = ' + database + ' AND selected_main_branch = ' + branch
        + ") = 1, 'E_MI2_SELECTION_IDENTITY');",
        'COMMIT;',
        'SELECT store_incarnation,namespace_key,selection_digest,native_node_id,selected_database,selected_main_branch '
        'FROM mi_practical_v2_metadata WHERE singleton = 1;',
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
    """UNQUALIFIED_LEGACY_GRANT_SEED retained for inspection only.

    It refuses when the grant id already exists anywhere
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
    _same_utc_moment(fixed_deadline_utc, lease_expiry_utc, 'fixed_deadline_utc')
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
    _same_utc_moment(fixed_deadline_utc, lease_expiry_utc, 'fixed_deadline_utc')
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


def initial_claim_sql(selection, request):
    """Build the minimum guarded native initial-claim transaction.

    The input has no caller deadline or lease authority.  The single backend
    UTC_TIMESTAMP(6) sample is converted to native DATETIME precision, then
    used for granted/heartbeat and the exactly-300-second expiry.  This output
    is deliberately only an offline candidate: native grammar, handler scope,
    rollback and all-or-nothing behavior require the retained real probes.
    """
    from .practical_lease_issuer import LeaseClaimRequest

    selection = LeasePracticalSelection.from_value(selection)
    request = LeaseClaimRequest.from_value(request)
    namespace = _text(selection.incarnation)
    selection_digest = _text(selection.digest)
    database = _text(selection.database)
    branch = _text(selection.main_branch)
    node = _text(selection.native_node_id)
    task = _text(request.task_id)
    actor = _text(request.actor)
    grant = _text(request.new_grant_id)
    operation = _text(request.operation_id)
    digest = _text(request.command_digest)

    binding = request.as_dict()
    binding.update(
        store_incarnation=selection.incarnation,
        selection_digest=selection.digest,
        database=selection.database,
        branch=selection.main_branch,
        native_node_id=selection.native_node_id,
        native_lease_ttl_seconds=300,
    )
    receipt = dict(
        binding,
        status='WORKING_SET_APPLIED',
        evidence_class='NATIVE_OBSERVED_UNQUALIFIED',
        native_write_qualified=False,
        head_committed=False,
        backend_operation_id=request.operation_id,
        native_task_id=request.task_id,
        original_row_lock=request.expected_row_lock,
    )
    binding_json = _text(strict_canonical_json(binding).decode('utf-8'))
    receipt_json = _text(strict_canonical_json(receipt).decode('utf-8'))
    # The equality predicate intentionally preserves an observed initial zero
    # row_lock from the pinned issue schema.  No caller seeds the replacement.
    authority = ' AND '.join([
        'i.id = ' + task,
        "i.status = 'open'",
        'i.assignee IS NULL',
        'i.row_lock = ' + str(request.expected_row_lock),
        'i.ephemeral = 0',
        'NOT EXISTS (SELECT 1 FROM dependencies AS d WHERE d.issue_id = i.id)',
        'NOT EXISTS (SELECT 1 FROM leases AS l WHERE l.issue_id = i.id)',
        'NOT EXISTS (SELECT 1 FROM mi_practical_v2_current_grants AS c '
        'WHERE c.store_incarnation = ' + namespace + ' AND c.task_id = i.id)',
        'NOT EXISTS (SELECT 1 FROM mi_practical_v2_grants AS g '
        'WHERE g.store_incarnation = ' + namespace + ' AND g.task_id = i.id AND g.tombstoned = 0)',
        'm.singleton = 1',
        'm.store_incarnation = ' + namespace,
        'm.namespace_key = ' + _text('identity'),
        'm.selection_digest = ' + selection_digest,
        'm.native_node_id = ' + node,
        'm.selected_database = ' + database,
        'm.selected_main_branch = ' + branch,
        'DATABASE() IN (' + database + ',CONCAT(' + database + ",'/main'))",
        'active_branch() = ' + branch,
    ])
    authority_query = ('SELECT COUNT(*) FROM issues AS i JOIN mi_practical_v2_metadata AS m '
                       'ON m.singleton = 1 WHERE ' + authority)
    return '\n'.join([
        'BEGIN NOT ATOMIC',
        'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
        'START TRANSACTION;',
        'SET @mi2_auth = UTC_TIMESTAMP(6);',
        'SET @mi2_lease_granted = CAST(@mi2_auth AS DATETIME);',
        'SET @mi2_lease_heartbeat = @mi2_lease_granted;',
        'SET @mi2_lease_expiry = DATE_ADD(@mi2_lease_granted, INTERVAL 300 SECOND);',
        'SET @mi2_initial_authorized = (' + authority_query + ');',
        "CALL mi_practical_assert_v2(@mi2_initial_authorized = 1, 'E_MI2_INITIAL_CLAIM_AUTH');",
        'SET @mi2_operation_exists = (SELECT COUNT(*) FROM mi_practical_v2_operations '
        'WHERE store_incarnation = ' + namespace + ' AND operation_id = ' + operation + ');',
        "CALL mi_practical_assert_v2(@mi2_operation_exists = 0, 'E_MI2_OPERATION_REPLAY');",
        'SET @mi2_current_exists = (SELECT COUNT(*) FROM mi_practical_v2_current_grants '
        'WHERE store_incarnation = ' + namespace + ' AND task_id = ' + task + ');',
        "CALL mi_practical_assert_v2(@mi2_current_exists = 0, 'E_MI2_CURRENT_GRANT_EXISTS');",
        'SET @mi2_token = NULLIF(CAST(CRC32(UUID()) AS SIGNED),0);',
        "CALL mi_practical_assert_v2(@mi2_token IS NOT NULL AND @mi2_token <> "
        + str(request.expected_row_lock) + ", 'E_MI2_TOKEN');",
        'UPDATE issues SET status = ' + _text('in_progress') + ', assignee = ' + actor
        + ', row_lock = @mi2_token WHERE id = ' + task + " AND status = 'open' AND assignee IS NULL"
        + ' AND row_lock = ' + str(request.expected_row_lock) + ' AND ephemeral = 0;',
        'SET @mi2_issue_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_issue_changed = 1, 'E_MI2_ISSUE_CARDINALITY');",
        'INSERT INTO leases(issue_id,holder,granted_node,granted_at,lease_expires_at,heartbeat_at) VALUES ('
        + task + ',' + actor + ',' + node + ',@mi2_lease_granted,@mi2_lease_expiry,@mi2_lease_heartbeat);',
        'SET @mi2_lease_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_lease_changed = 1, 'E_MI2_LEASE_CARDINALITY');",
        'INSERT INTO mi_practical_v2_grants(store_incarnation,grant_id,task_id,actor,status,'
        'fixed_deadline_utc,issue_revision,tombstoned,lease_node,lease_granted_at,lease_expiry,lease_heartbeat) VALUES ('
        + namespace + ',' + grant + ',' + task + ',' + actor + ",'CURRENT',@mi2_lease_expiry,@mi2_token,0,"
        + node + ',@mi2_lease_granted,@mi2_lease_expiry,@mi2_lease_heartbeat);',
        'SET @mi2_grant_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_grant_changed = 1, 'E_MI2_GRANT_CARDINALITY');",
        'INSERT INTO mi_practical_v2_current_grants(store_incarnation,task_id,grant_id,current_revision) VALUES ('
        + namespace + ',' + task + ',' + grant + ',@mi2_token);',
        'SET @mi2_current_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_current_changed = 1, 'E_MI2_CURRENT_GRANT_CARDINALITY');",
        'INSERT INTO mi_practical_v2_grant_history(store_incarnation,grant_id,event_kind,event_utc,details) VALUES ('
        + namespace + ',' + grant + ",'INITIAL_CLAIM',@mi2_auth,'db-minted-native-lease');",
        'SET @mi2_history_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_history_changed = 1, 'E_MI2_HISTORY_CARDINALITY');",
        'INSERT INTO mi_practical_v2_token_history(store_incarnation,row_token,operation_id) VALUES ('
        + namespace + ',@mi2_token,' + operation + ');',
        'SET @mi2_token_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_token_changed = 1, 'E_MI2_TOKEN_CARDINALITY');",
        'INSERT INTO mi_practical_v2_operations(store_incarnation,operation_id,command_digest,binding_json,receipt_json,'
        'authorization_time,resulting_row_lock) VALUES (' + namespace + ',' + operation + ',' + digest + ','
        + binding_json + ',JSON_SET(CAST(' + receipt_json + " AS JSON),'$.authorization_time_utc',"
        + "DATE_FORMAT(@mi2_auth,'%Y-%m-%d %H:%i:%s.%f'),'$.lease_granted_at_utc',"
        + "DATE_FORMAT(@mi2_lease_granted,'%Y-%m-%d %H:%i:%s.%f'),'$.lease_expires_at_utc',"
        + "DATE_FORMAT(@mi2_lease_expiry,'%Y-%m-%d %H:%i:%s.%f'),'$.lease_heartbeat_at_utc',"
        + "DATE_FORMAT(@mi2_lease_heartbeat,'%Y-%m-%d %H:%i:%s.%f'),'$.resulting_row_lock',@mi2_token),"
        + '@mi2_auth,@mi2_token);',
        'SET @mi2_receipt_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_receipt_changed = 1, 'E_MI2_RECEIPT_CARDINALITY');",
        'COMMIT;',
        'END;',
        'SELECT receipt_json,binding_json,command_digest,authorization_time,resulting_row_lock '
        'FROM mi_practical_v2_operations WHERE store_incarnation = ' + namespace
        + ' AND operation_id = ' + operation + ' AND command_digest = ' + digest + ';',
    ])


def _title_batch(selection, request, pause_seconds=None):
    selection = LeasePracticalSelection.from_value(selection)
    request = LeaseGuardedTitleRequest.from_value(request)
    if selection.native_node_id != request.lease_granted_node:
        raise PracticalContractError('E_MI2_FOREIGN_LEASE_NODE')
    predicate = ' AND '.join([
        _binary_equals('i.id', _text(request.task_id)),
        'i.status = ' + _text('in_progress'),
        _binary_equals('i.assignee', _text(request.actor)),
        'i.row_lock = ' + str(request.expected_row_lock),
        'i.ephemeral = 0',
        'l.issue_id = i.id',
        _binary_equals('l.holder', _text(request.lease_holder)),
        _binary_equals('l.granted_node', _text(request.lease_granted_node)),
        'l.granted_at = ' + _text(request.lease_granted_at_utc),
        'l.lease_expires_at = ' + _text(request.lease_expires_at_utc),
        'l.heartbeat_at = ' + _text(request.lease_heartbeat_at_utc),
        '@mi2_auth < l.lease_expires_at',
        _binary_equals('g.grant_id', _text(request.grant_id)),
        'g.task_id = i.id', 'BINARY g.actor = BINARY i.assignee', 'g.tombstoned = 0',
        'g.issue_revision = i.row_lock',
        'g.fixed_deadline_utc = l.lease_expires_at',
        'c.grant_id = g.grant_id', 'c.current_revision = i.row_lock',
        'BINARY g.lease_node = BINARY l.granted_node', 'g.lease_granted_at = l.granted_at',
        'g.lease_expiry = l.lease_expires_at', 'g.lease_heartbeat = l.heartbeat_at',
        'g.store_incarnation = m.store_incarnation',
        'm.namespace_key = ' + _text('identity'),
        'm.store_incarnation = ' + _text(selection.incarnation),
        'm.selection_digest = ' + _text(selection.digest),
        'm.native_node_id = l.granted_node',
        'm.selected_database = ' + _text(selection.database),
        'm.selected_main_branch = ' + _text(selection.main_branch),
        'DATABASE() IN (' + _text(selection.database) + ',CONCAT('
        + _text(selection.database) + ",'/main'))",
        'active_branch() = ' + _text('main'),
        'NOT EXISTS (SELECT 1 FROM dependencies AS d WHERE d.issue_id = i.id)',
    ])
    # The read starts the actual transaction snapshot before a native harness
    # pause. It is not a locking read, and not a client-side permission check.
    authority = ('SELECT COUNT(*) FROM issues AS i JOIN leases AS l ON l.issue_id = i.id '
                  'JOIN mi_practical_v2_grants AS g ON g.task_id = i.id '
                  'JOIN mi_practical_v2_current_grants AS c ON c.store_incarnation = g.store_incarnation '
                  'AND c.task_id = g.task_id '
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
        'BEGIN NOT ATOMIC',
        'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
        'START TRANSACTION;',
        'SET @mi2_auth = UTC_TIMESTAMP(6);',
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
        'WHERE ' + _binary_equals('id', task) + ' AND ' + _binary_equals('assignee', _text(request.actor))
        + ' AND status = ' + _text('in_progress') + ' AND row_lock = ' + str(request.expected_row_lock) + ';',
        'SET @mi2_issue_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_issue_changed = 1, 'E_MI2_ISSUE_CARDINALITY');",
        'UPDATE mi_practical_v2_grants SET issue_revision = @mi2_token WHERE '
        + _binary_equals('store_incarnation', namespace) + ' AND ' + _binary_equals('grant_id', grant)
        + ' AND ' + _binary_equals('task_id', task)
        + ' AND issue_revision = ' + str(request.expected_row_lock) + ' AND tombstoned = 0;',
        'SET @mi2_grant_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_grant_changed = 1, 'E_MI2_GRANT_CARDINALITY');",
        'UPDATE mi_practical_v2_current_grants SET current_revision = @mi2_token WHERE '
        + _binary_equals('store_incarnation', namespace) + ' AND ' + _binary_equals('task_id', task)
        + ' AND ' + _binary_equals('grant_id', grant)
        + ' AND current_revision = ' + str(request.expected_row_lock) + ';',
        'SET @mi2_current_changed = ROW_COUNT();',
        "CALL mi_practical_assert_v2(@mi2_current_changed = 1, 'E_MI2_CURRENT_GRANT_CARDINALITY');",
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
        'END;',
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
