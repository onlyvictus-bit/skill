"""Read consumed MP1 evidence only; never launch, repair, or promote an old run."""
import argparse
import hashlib
import json
from pathlib import Path
import stat

REPO = Path(__file__).absolute().parents[2]
ATTEMPT = REPO/'.github/run-artifacts/cleanup-membership-20261025/normal-membership'
RECEIPT_SHA = '0a61222897b210c2500a5c461b7bacc5f00e296b4d2f5678a51f82b256c488d7'
ROLES = ('root', 'relay', 'launcher', 'child')
FALSE_FLAGS = ('stage_complete', 'gate1_complete', 'release_ready', 'installed',
               'root_cause_confirmed', 'fix_validated', 'producer_authentication')


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_bytes(path, *, limit=1048576):
    """Bounded ordinary-file read, including identity checks around the read."""
    path = Path(path).absolute()
    for part in (path, *path.parents):
        info = part.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not
                (getattr(info, 'st_file_attributes', 0) & 0x400), 'E_SR_REDIRECTED_INPUT')
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'E_SR_LINKED_INPUT')
    require(before.st_size <= limit, 'E_SR_INPUT_SIZE')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    after = path.stat()
    require(len(raw) <= limit, 'E_SR_INPUT_SIZE')
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and
            len(raw) == after.st_size, 'E_SR_INPUT_CHANGED')
    return raw


def parse_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'E_SR_DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def bad_constant(value):
        raise ValueError('E_SR_NONFINITE_JSON: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad_constant)


def require_false_flags(value):
    require(isinstance(value, dict) and all(value.get(key) is False for key in FALSE_FLAGS),
            'E_SR_FALSE_FLAGS')


def capture_status(command):
    require(isinstance(command, dict), 'E_SR_CAPTURE_INCOMPLETE')
    flags = command.get('containment')
    require(isinstance(flags, dict) and command.get('execution') == 'EXITED' and
            command.get('failure') is None and flags.get('capture_complete') is True and
            flags.get('timed_out') is False and flags.get('capture_errors') == [] and
            flags.get('output_limit_exceeded') is False and flags.get('tree_contained') is True,
            'E_SR_CAPTURE_INCOMPLETE')
    code = command.get('exit_code')
    require(type(code) is int and type(flags.get('exit_code')) is int and
            code == flags['exit_code'], 'E_SR_CAPTURE_EXIT')
    # A nonzero child exit and a complete capture can both be true.
    return 'COMPLETE_NONZERO_EXIT' if code else 'COMPLETE_ZERO_EXIT'


def verify_stream(record, expected_path):
    require(isinstance(record, dict) and record.get('path') == str(expected_path), 'E_SR_STREAM_PATH')
    raw = read_bytes(expected_path)
    require(type(record.get('size')) is int and len(raw) == record['size'] and
            digest(raw) == record.get('sha256'), 'E_SR_STREAM_CHANGED')
    return raw


def validate_snapshot(row, *, phase):
    require(phase in ('before-write', 'before-terminate', 'after-terminate'), 'E_SR_PHASE')
    require(isinstance(row, dict) and isinstance(row.get('membership'), dict) and
            isinstance(row.get('roles'), dict) and set(row['roles']) == set(ROLES), 'E_SR_SNAPSHOT')
    membership = row['membership']; members = membership.get('members')
    require(isinstance(members, list) and all(type(pid) is int and pid > 0 for pid in members) and
            len(set(members)) == len(members) and
            all(type(membership.get(k)) is int and membership[k] >= 0
                for k in ('assigned', 'listed', 'active', 'total')) and
            membership['listed'] == len(members) and membership['assigned'] >= len(members) and
            membership['total'] >= membership['active'], 'E_SR_SNAPSHOT')
    require(all(isinstance(item, dict) and set(item) == {'in_job', 'signalled'} and
                type(item['in_job']) is bool and type(item['signalled']) is bool
                for item in row['roles'].values()), 'E_SR_ROLE_STATE')
    if phase == 'before-write':
        require(row.get('stage') == 'before-write' and
                membership['assigned'] == membership['listed'] == membership['active'] and
                not any(item['signalled'] for item in row['roles'].values()), 'E_SR_STABLE_MEMBERSHIP')
    # Before a SECOND terminate call, or after termination, association, live PID
    # list and signalling are sequential observations, not an atomic equality.
    # Never turn that relaxation into process-exit proof: classification below
    # uses the separately pinned handles' actual after-stop signalled values.
    return row


def interpret_events(rows):
    require(isinstance(rows, list) and rows and all(isinstance(row, dict) for row in rows), 'E_SR_EVENTS')
    required = ('fixture-created', 'session-created', 'roles-pinned', 'before-write',
                'request-ended', 'writer-pinned', 'after-stop', 'emergency-finished', 'handle-cleanup')
    stages = [row.get('stage') for row in rows]
    require(all(stages.count(stage) == 1 for stage in required), 'E_SR_EVENTS')
    positions = [stages.index(stage) for stage in required]
    require(positions == sorted(positions), 'E_SR_EVENTS_ORDER')
    after = rows[stages.index('after-stop')]
    # This reader is bound to ONE consumed witness, not a permissive future-run
    # parser. Its fallback had a second terminate-returned/after-terminate pair
    # but no second before-terminate row: the old observer rejected that snapshot.
    # Preserve that known absence, and refuse deletion of any retained phase.
    expected_stages = [*required[:6], 'before-terminate', 'terminate-returned',
                       'after-terminate', 'terminate-returned', 'after-terminate']
    if after.get('stop_error'):
        expected_stages.append('stop-failed')
    expected_stages.extend(required[6:])
    require(stages == expected_stages, 'E_SR_EVENTS_TRANSITIONS')
    for row in rows:
        if row['stage'] == 'terminate-returned':
            require(type(row.get('value')) is bool and type(row.get('last_error')) is int and
                    row['last_error'] >= 0 and (not row['value'] or row['last_error'] == 0),
                    'E_SR_EVENTS_TERMINATE_RESULT')
        if row['stage'] == 'stop-failed':
            require(isinstance(row.get('error'), list) and row['error'] and
                    all(isinstance(item, str) for item in row['error']) and
                    row['error'] == after['stop_error'], 'E_SR_EVENTS_STOP_ERROR')
    require(all(type(row.get('utc_ns')) is int for row in rows) and
            all(a['utc_ns'] <= b['utc_ns'] for a, b in zip(rows, rows[1:])), 'E_SR_EVENTS_TIME')
    pinned = rows[stages.index('roles-pinned')].get('pids')
    require(isinstance(pinned, dict) and set(pinned) == set(ROLES) and
            all(type(pid) is int and pid > 0 for pid in pinned.values()) and
            len(set(pinned.values())) == len(ROLES), 'E_SR_EVENTS_IDENTITY')
    before = rows[stages.index('before-write')]
    validate_snapshot(before, phase='before-write')
    require(all(item['in_job'] == (pinned[role] in before['membership']['members'])
                for role, item in before['roles'].items()), 'E_SR_STABLE_MEMBERSHIP')
    for row in rows:
        if row.get('stage') in ('before-terminate', 'after-terminate'):
            validate_snapshot(row, phase=row['stage'])
    signalled = after.get('signalled')
    require(isinstance(signalled, dict) and set(signalled) == set(ROLES) and
            all(type(value) is bool for value in signalled.values()) and
            type(after.get('writer_alive')) is bool, 'E_SR_EVENTS_EXIT')
    outside = [role for role in ROLES if not before['roles'][role]['in_job'] and not signalled[role]]
    inside = [role for role in ROLES if before['roles'][role]['in_job'] and not signalled[role]]
    if outside:
        classification = 'MEMBERSHIP_GAP_OBSERVED_NOT_FIXED'
    elif inside:
        classification = 'MEMBERSHIP_CONTRADICTION_REQUIRES_REDESIGN'
    elif after['writer_alive']:
        classification = 'PIPE_CANCELLATION_GAP_NOT_FIXED'
    elif after.get('stop_error'):
        classification = 'STOP_FAILURE_WITH_ALL_HANDLES_EXITED_NOT_FIXED'
    else:
        classification = 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE'
    return {'derived_classification':classification, 'outside_survivors':outside,
            'outside_survivor_pids':[pinned[role] for role in outside],
            'unknown_job_member_pids':sorted(set(before['membership']['members']) - set(pinned.values())),
            'writer_alive_after_stop':after['writer_alive'], 'stop_error':after.get('stop_error'),
            'role_pids':pinned, 'raw_events':rows}


def review_saved_attempt(*, expected_receipt_sha=RECEIPT_SHA):
    """Derived evidence only: the old rejected probe remains rejected."""
    observed = {}
    def read(path):
        raw = read_bytes(path)
        observed[str(path)] = {'path':str(path), 'size':len(raw), 'sha256':digest(raw)}
        return raw
    receipt_raw = read(ATTEMPT/'Receipt.json')
    require(digest(receipt_raw) == expected_receipt_sha == RECEIPT_SHA, 'E_SR_RECEIPT_SEAL')
    receipt = parse_json(receipt_raw); require_false_flags(receipt)
    require(receipt.get('attempt_consumed') is True and receipt.get('pinned_preservation_verified') is True and
            receipt.get('status') == 'PARTIAL_OR_FAILED_NO_RETRY', 'E_SR_RECEIPT_STATE')
    commands = receipt.get('commands')
    require(isinstance(commands, list) and [row.get('label') for row in commands] ==
            ['preclaim-identity', 'preclaim-dependencies', 'membership'], 'E_SR_COMMANDS')
    streams, capture = [], []
    for command in commands:
        status = capture_status(command)
        capture.append({'label':command['label'], 'capture':status, 'exit_code':command['exit_code']})
        require(command['exit_code'] == (1 if command['label'] == 'membership' else 0), 'E_SR_COMMAND_EXIT')
        for role in ('stdout', 'stderr'):
            path = ATTEMPT/command['label']/(role+'.log')
            raw = verify_stream(command.get(role), path)
            observed[str(path)] = {'path':str(path), 'size':len(raw), 'sha256':digest(raw)}
            streams.append(observed[str(path)])
    rows = [parse_json(line) for line in read(ATTEMPT/'probe/Incremental.jsonl').splitlines()]
    result = interpret_events(rows)
    identities = {}
    for number, role in enumerate(ROLES):
        marker = parse_json(read(ATTEMPT/'probe/fixture'/(role+'.json')))
        require(isinstance(marker, dict) and set(marker) == {'pid','creation','ppid','parent_creation'} and
                type(marker['pid']) is int and marker['pid'] == result['role_pids'][role] and
                type(marker['ppid']) is int and marker['ppid'] >= 0 and
                isinstance(marker['creation'], str) and marker['creation'].isdigit() and
                isinstance(marker['parent_creation'], str) and marker['parent_creation'].isdigit(), 'E_SR_ROLE_IDENTITY')
        if number:
            parent = identities[ROLES[number-1]]
            require(marker['ppid'] == parent['pid'] and marker['parent_creation'] == parent['creation'] and
                    int(marker['creation']) >= int(parent['creation']), 'E_SR_ROLE_PARENT')
        identities[role] = marker
    error = parse_json(read(ATTEMPT/'probe/Probe-error.json')); require_false_flags(error)
    require(error.get('scope') == 'MP1_MEMBERSHIP_ONLY_NOT_FIX' and
            isinstance(error.get('error'), list), 'E_SR_PROBE_ERROR')
    require(error.get('emergency_cleanup') ==
            next(row for row in rows if row['stage'] == 'emergency-finished').get('emergency') and
            error.get('handle_cleanup') ==
            next(row for row in rows if row['stage'] == 'handle-cleanup').get('handle_cleanup'),
            'E_SR_EVENT_RECEIPT_MISMATCH')
    emergency = error.get('emergency_cleanup') or {}
    cleanup = error.get('handle_cleanup') or {}
    combined = (emergency.get('completed') is True and emergency.get('errors') == [] and
                all(emergency.get(key) is True for key in ('writer_joined','root_reaped','streams_closed','job_closed')) and
                emergency.get('roles_signalled') == dict.fromkeys(ROLES, True) and
                cleanup.get('completed') is True and cleanup.get('errors') == [])
    # Compare the same data again before returning; no files are created or changed.
    for path, record in observed.items():
        require(digest(read_bytes(path)) == record['sha256'], 'E_SR_INPUT_CHANGED')
    return {'scope':'SR1_DERIVED_SAVED_MP1_EVIDENCE_ONLY', **result, **dict.fromkeys(FALSE_FLAGS,False),
            'old_probe_accepted':False, 'cancellation_alone_proven':False,
            'emergency_combined_cleanup_completed':combined, 'raw_probe_error':error,
            'role_identity_records':identities, 'commands':capture, 'verified_streams':streams,
            'input_records':list(observed.values()),
            'limitations':['OBSERVATION_ERRORS_NOT_RETAINED_BY_OLD_PROBE',
                           'SECOND_PRE_TERMINATE_SNAPSHOT_NOT_RETAINED_BY_OLD_PROBE',
                           'RAW_PROBE_EVENTS_NOT_HASH_BOUND_BY_OLD_RECEIPT',
                           'CONTAINMENT_METHOD_LABEL_NOT_DESCENDANT_EXIT_PROOF',
                           'EXACT_PIPE_HOLDER_AND_ESCAPE_MECHANISM_UNPROVEN']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-saved', action='store_true', required=True)
    parser.parse_args()
    print(json.dumps(review_saved_attempt(), sort_keys=True))
