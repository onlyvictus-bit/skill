"""Unqualified lease-bound title transaction template; no dispatch entry point.

The predecessor adapter remains STOPPED. This builder still needs the matching
v2 scratch schema, protected lease-minting transitions, actual CLI error/rollback
proof, consumer integration, and the real synchronized race. String tests do
not establish Dolt grammar, atomicity, native eligibility, or durability.
"""
from .practical_contract import (
    LeaseGuardedTitleRequest, LeasePracticalSelection, PracticalContractError,
    strict_canonical_json,
)
from .practical_sql import _text


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
