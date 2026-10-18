"""Native lease-race schedule, orchestration and bounded live driver.

`build_race_schedule` assembles the exact synchronized stale-owner race from
the real builders: setup DDL, seed, Alice's paused title batch (observed
barrier, never sleep-only assumptions in the assertions), the legitimate
ownership-transfer batch, readback queries, a current-owner positive control
and a harness-only fence-disabled comparison arm.

`run_race` is the only orchestrator and it scores through exactly one
function, the canonical verdict function in practical_race_verify. It keeps
no verdict logic of its own. A driver exception outside the fence verdict
yields INCONCLUSIVE, never a pass and never a false conviction.

State boundaries:

    S0  initialized and claimed state before the race
    S1  verified legitimate ownership transfer committed and observed
    S2  stale operation finished, fresh final readback

Evidence levels stay separate. ENGINE_SYNTHETIC uses harness-owned fixture
tables covering every table the generated SQL references and can only test
the bounded database mechanism. ENGINE_BEADS requires a pinned, officially
initialized disposable store whose schema and identity are queried, never
assumed from a marker directory.

`run_schedule` refuses without `confirm_native_execution=True` plus the
separate execution authorization this project requires. The live driver below
is implemented and bounded, but it has never been executed: no host was
available. Its methods are unvalidated against a live server, and it starts
and stops only the server process it owns.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ENGINE_SYNTHETIC = 'synthetic-dolt-engine'
ENGINE_BEADS = 'real-beads-backed'

EVIDENCE_CLASS_SYNTHETIC = 'SYNTHETIC_ENGINE_MECHANISM_ONLY'
EVIDENCE_CLASS_BEADS = 'REAL_BEADS_OBSERVED_UNQUALIFIED'

# Fixed, source-recorded harness instrumentation. These are the only
# decorations the harness adds to generated SQL, they carry no predicate and
# no authority, and they exist so a barrier can be observed from a second
# session instead of assumed from a sleep.
BARRIER_COMMENT = 'PRACTICAL_RACE_BARRIER'
BARRIER_KIND = 'AUTHORIZATION_SNAPSHOT_HELD'
BARRIER_OBSERVED_BY = 'DATABASE_SESSION_MARKER'
BARRIER_POLL_SECONDS = 0.25

DRIVER_TIMEOUT_SECONDS = 120
DRIVER_CAPTURE_BYTES = 1024 * 1024
STOP_GRACE_SECONDS = 10.0

# Sentinel: this runtime exposes no session view, so no barrier can be
# observed. Distinct from "not observed yet", which is None.
_UNSUPPORTED = object()

# Every statement the harness may execute for its own setup and readback is
# produced by these builders. A statement outside the allowlist is refused, so
# no caller-supplied SQL can reach the protected store.
_ALLOWED_SETUP_PREFIXES = ('CREATE TABLE IF NOT EXISTS', 'CREATE PROCEDURE IF NOT EXISTS',
                          'START TRANSACTION', 'COMMIT', 'SELECT', 'INSERT INTO mi_practical_v2_metadata',
                          'UPDATE mi_practical_v2_metadata', 'CALL mi_practical_assert_v2',
                          'INSERT INTO dolt_ignore', 'BEGIN NOT ATOMIC', 'END', 'SET @mi2_auth',
                          'SET @mi2_authorized', 'INSERT INTO issues', 'UPDATE issues SET status')
_ALLOWED_READBACK_PREFIXES = ('SELECT',)

_SYNTHETIC_ISSUES_DDL = (
    'CREATE TABLE IF NOT EXISTS issues ('
    'id VARCHAR(192) NOT NULL PRIMARY KEY, status VARCHAR(64) NOT NULL, '
    'assignee VARCHAR(192) NULL, title LONGTEXT NOT NULL, '
    'row_lock BIGINT NOT NULL, ephemeral TINYINT NOT NULL DEFAULT 0);'
)
_SYNTHETIC_LEASES_DDL = (
    'CREATE TABLE IF NOT EXISTS leases ('
    'issue_id VARCHAR(192) NOT NULL PRIMARY KEY, holder VARCHAR(192) NOT NULL, '
    'granted_node VARCHAR(192) NOT NULL, granted_at DATETIME NOT NULL, '
    'lease_expires_at DATETIME NOT NULL, heartbeat_at DATETIME NOT NULL);'
)
# The generated authority predicates reference a dependencies table. A
# synthetic fixture that omits it cannot execute the real SQL, so it is part
# of the harness schema rather than an optional extra.
_SYNTHETIC_DEPENDENCIES_DDL = (
    'CREATE TABLE IF NOT EXISTS dependencies ('
    'issue_id VARCHAR(192) NOT NULL, depends_on VARCHAR(192) NOT NULL, '
    'dep_type VARCHAR(64) NOT NULL, PRIMARY KEY(issue_id, depends_on));'
)

# Tables the harness-owned synthetic fixture must provide so that every
# generated statement resolves. Verified by a test, not by prose.
REQUIRED_SYNTHETIC_TABLES = ('issues', 'leases', 'dependencies')


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _known_batches(engine):
    """Builder-produced batch texts the driver may execute verbatim.

    A batch is accepted only when it is byte-identical to what a production
    builder produces right now. That is what lets a stored procedure and a
    transaction boundary survive intact in a single invocation, without ever
    accepting caller text.
    """
    from .practical_lease_sql import v2_schema_sql
    batches = [v2_schema_sql()]
    if engine == ENGINE_SYNTHETIC:
        batches.extend([_SYNTHETIC_ISSUES_DDL, _SYNTHETIC_LEASES_DDL,
                        _SYNTHETIC_DEPENDENCIES_DDL])
    return batches


def _source_manifest():
    """A real digest over the exact harness and protected module bytes used."""
    here = Path(__file__).resolve().parent
    names = ('practical_race_controller.py', 'practical_race_verify.py',
             'practical_race_alice.py', 'practical_contract.py', 'practical_lease_sql.py',
             'practical_lease_backend.py', 'practical_lease_consumer.py', 'practical_execution.py')
    manifest = {}
    for name in names:
        path = here / name
        if path.is_file():
            manifest[name] = _sha256_file(path)
    # The companion journal is part of what a run actually exercises, so its
    # bytes belong in the identity a receipt is bound to.
    for base in _companion_roots():
        candidate = base / 'complete_read_v2' / 'ledger.py'
        if candidate.is_file():
            manifest['complete_read_v2/ledger.py'] = _sha256_file(candidate)
            break
    return manifest, hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def _companion_roots():
    """Directories that may hold the companion ledger, nearest first."""
    here = Path(__file__).resolve()
    roots = []
    for parent in here.parents:
        roots.append(parent / 'claude-mon' / 'scripts')
        roots.append(parent / 'scripts')
    seen = set()
    ordered = []
    for root in roots:
        key = str(root)
        if key not in seen:
            seen.add(key)
            ordered.append(root)
    return ordered


def ledger_events(db, operation_id=None):
    """Read the existing companion journal. One place, so it can be stubbed."""
    from complete_read_v2 import ledger
    return ledger._practical_events_locked(db, operation_id)


def verify_engine(engine, scratch_root, dolt_executable, expected_dolt_sha256):
    """Structural preflight only. This proves nothing about a running server."""
    root = Path(scratch_root)
    if not root.is_dir():
        raise ValueError('E_HARNESS_PATH: scratch root is not a directory')
    binary = Path(dolt_executable)
    if not binary.is_file():
        raise ValueError('E_HARNESS_PATH: dolt executable is not a file')
    digest = _sha256_file(binary)
    if digest != expected_dolt_sha256.lower():
        raise ValueError('E_HARNESS_DOLT_PIN: binary identity mismatch')
    evidence = {'engine': engine, 'scratch_root': str(root),
                'dolt_executable': str(binary), 'dolt_sha256': digest,
                'structural_only': True}
    if engine == ENGINE_BEADS:
        marker = root / '.beads'
        if not marker.is_dir():
            raise ValueError('E_HARNESS_BEADS_MARKER: no officially initialized Beads store here')
        evidence['beads_marker'] = str(marker)
    elif engine != ENGINE_SYNTHETIC:
        raise ValueError('E_HARNESS_ENGINE: unknown engine')
    return evidence


def disabled_stale_update(task_id, title, assignee):
    """Harness-only fence-disabled comparison arm. This bare UPDATE carries
    no authority check, no token rotation and no receipt: it exists only to
    prove the harness can expose the unsafe condition the enabled arm must
    prevent. It must never appear in production code paths."""
    from .practical_sql import _text
    return ('-- HARNESS-ONLY disabled comparison: no fence predicates. '
            'Never use outside the race harness.\n'
            'UPDATE issues SET title = ' + _text(title) + ', assignee = ' + _text(assignee)
            + ' WHERE id = ' + _text(task_id) + ';')


def disabled_fence_components():
    """Exactly which fence components the comparison arm removes.

    Stating this explicitly is what makes the comparison causal rather than
    merely different: the legitimate transfer, the reservation-before-dispatch
    rule and the conflict-token mechanism are all preserved, and only the
    authorization predicates are absent.
    """
    return (
        'protected authorization predicates (issue owner, live lease snapshot, current grant, '
        'current pointer, store identity)',
        'authorization-time database clock assertion',
        'effect and receipt cardinality assertions',
        'conflict-token rotation and token history binding',
    )


def build_race_schedule(*, engine, selection, alice_title_packet, bob_reassign_packet,
                        port, database, pause_seconds=20, source_commit=None,
                        working_tree=None):
    """Assemble the exact race/control schedule from the real builders."""
    from .practical_contract import (LeaseGuardedTitleRequest, LeaseReassignRequest,
                                     LeasePracticalSelection)
    from .practical_lease_sql import experiment_guarded_title_sql, reassign_title_sql, v2_schema_sql
    selected = LeasePracticalSelection.from_value(selection)
    alice = LeaseGuardedTitleRequest.from_value(alice_title_packet)
    bob = LeaseReassignRequest.from_value(bob_reassign_packet)
    if not isinstance(pause_seconds, int) or not 1 <= pause_seconds <= 30:
        raise ValueError('E_HARNESS_PAUSE: pause must be 1..30 seconds')
    setup_ddl = [v2_schema_sql()]
    if engine == ENGINE_SYNTHETIC:
        setup_ddl.extend([_SYNTHETIC_ISSUES_DDL, _SYNTHETIC_LEASES_DDL,
                          _SYNTHETIC_DEPENDENCIES_DDL])
    elif engine != ENGINE_BEADS:
        raise ValueError('E_HARNESS_ENGINE: unknown engine')
    return {
        'engine': engine,
        'evidence_class': EVIDENCE_CLASS_SYNTHETIC if engine == ENGINE_SYNTHETIC else EVIDENCE_CLASS_BEADS,
        'port': port,
        'database': database,
        'pause_seconds': pause_seconds,
        'barrier_timeout_seconds': 60,
        # Source provenance is supplied by the operator at native time and is
        # validated, never assumed. Absent values make the run INCONCLUSIVE
        # rather than silently passing an unproven source identity.
        'source_commit': source_commit,
        'working_tree': working_tree,
        'operation_ids': {'alice': alice.operation_id, 'bob': bob.operation_id},
        'identities': {
            'task_id': alice.task_id, 'stale_actor': alice.actor, 'winner': bob.target_actor,
            'stale_grant_id': alice.grant_id, 'winner_grant_id': bob.new_grant_id,
            'expected_title': bob.title,
            'stale_operation_ids': [alice.operation_id],
            'winner_operation_ids': [bob.operation_id],
        },
        'requests': {'selection': dict(selection),
                     'alice_title': dict(alice_title_packet),
                     'bob_reassign': dict(bob_reassign_packet)},
        'phases': {
            'setup': {'ddl': setup_ddl, 'bootstrap': 'v2_namespace_bootstrap_sql',
                      'register': 'v2_selection_registration_sql'},
            'seed': {'issue': {'id': alice.task_id, 'status': 'open'},
                     'note': 'one open unassigned issue; claim path runs first in the live run'},
            'alice_arm': {'batch': experiment_guarded_title_sql(selection, alice_title_packet,
                                                                pause_seconds=pause_seconds),
                          'barrier': 'DO SLEEP(%d) inside the open transaction after the '
                                     'authorization snapshot read' % pause_seconds},
            'bob_arm': {'batch': reassign_title_sql(selection, bob_reassign_packet)},
            'readback': {'queries': [
                'SELECT id,assignee,title,status,row_lock,ephemeral FROM issues WHERE id = <task>;',
                'SELECT issue_id,holder,granted_node,granted_at,lease_expires_at,heartbeat_at '
                'FROM leases WHERE issue_id = <task>;',
                'SELECT store_incarnation,grant_id,task_id,actor,status,issue_revision,tombstoned,'
                'lease_node,lease_granted_at,lease_expiry,lease_heartbeat '
                'FROM mi_practical_v2_grants WHERE task_id = <task>;',
                'SELECT store_incarnation,grant_id,event_kind,event_utc '
                'FROM mi_practical_v2_grant_history WHERE store_incarnation = <namespace>;',
                'SELECT store_incarnation,task_id,grant_id,current_revision '
                'FROM mi_practical_v2_current_grants WHERE task_id = <task>;',
                'SELECT store_incarnation,namespace_key,selection_digest,native_node_id,'
                'selected_database,selected_main_branch FROM mi_practical_v2_metadata;',
                'SELECT store_incarnation,row_token,operation_id FROM mi_practical_v2_token_history;',
                'SELECT store_incarnation,operation_id,command_digest,authorization_time,'
                'resulting_row_lock FROM mi_practical_v2_operations '
                'WHERE operation_id IN (<alice>, <bob>);',
            ]},
            'controls': {
                'positive': 'current-owner title through the same fenced path must succeed',
                'disabled': 'harness-only bare stale update with the transfer preserved',
                'disabled_components': list(disabled_fence_components()),
            },
            'disabled_arm': {'batch': disabled_stale_update(alice.task_id, alice.title, alice.actor),
                             'harness_only': True,
                             'disabled_components': list(disabled_fence_components()),
                             'preserves_transfer': True},
        },
    }


def run_schedule(schedule, *, confirm_native_execution=False):
    """Entry point honoring the confirmation gate, then live orchestration.

    Refuses without explicit confirmation plus the separate execution
    authorization. With confirmation it drives `_LiveDriver`, whose methods
    are implemented but have never run against a live server.
    """
    if not confirm_native_execution is True:
        raise ValueError('E_HARNESS_NATIVE_CONFIRM: pass confirm_native_execution=True '
                         'with separate execution authorization to run natively')
    return run_race(schedule, driver=_LiveDriver(schedule))


def _labeled(result, stopped):
    result = dict(result)
    result['stopped'] = bool(stopped)
    return result


def run_race(schedule, *, driver):
    """Orchestrate the race through an injectable driver and score it once.

    The driver performs every side effect. This function orders the phases,
    assembles one strict evidence mapping and hands it to the single
    canonical verdict function in practical_race_verify. It contains no
    verdict logic of its own.
    """
    from . import practical_race_verify as race_verify
    phases = schedule['phases']
    try:
        preflight = driver.preflight()
    except Exception as exc:
        return _labeled(race_verify.inconclusive(
            'HARNESS_ERROR', 'structural preflight failed: %s' % (type(exc).__name__,)), False)
    if not isinstance(preflight, dict) or not preflight.get('structural_only'):
        return _labeled(race_verify.inconclusive(
            'IDENTITY_UNVERIFIED', 'structural preflight was not observed'), False)
    try:
        driver.start_server()
    except Exception as exc:
        return _labeled(race_verify.inconclusive(
            'HARNESS_ERROR', 'owned server did not start: %s' % (type(exc).__name__,)), False)
    evidence = None
    failure = None
    try:
        evidence, failure = _orchestrate(schedule, driver, preflight, race_verify)
    except Exception as exc:
        failure = race_verify.inconclusive(
            'HARNESS_ERROR', 'orchestration failed: %s' % (type(exc).__name__,))
    # Both owned processes are always released, on every path, and a failure to
    # release either one stays visible instead of reading as success.
    releases = {}
    for name, stop in (('stop_alice', 'stop_alice'), ('stop_server', 'stop_server')):
        try:
            releases[name] = bool(getattr(driver, stop)())
        except Exception:
            releases[name] = False
    stopped = releases['stop_alice'] and releases['stop_server']
    result = race_verify.judge_evidence(evidence) if evidence is not None else failure
    result = dict(result)
    result['stopped'] = stopped
    result['releases'] = releases
    if not stopped:
        # A failed stop stays visible and can never coexist with a pass.
        result['reasons'] = list(result['reasons']) + [
            race_verify._reason(
                'HARNESS_ERROR',
                'owned process release failed (%s); the run cannot be labelled complete'
                % ', '.join(sorted(name for name, ok in releases.items() if not ok)))]
        result['unproven'] = list(result.get('unproven', [])) + ['HARNESS_ERROR']
        if result['verdict'] == race_verify.PASSED:
            result['verdict'] = race_verify.INCONCLUSIVE
    return result


def _orchestrate(schedule, driver, preflight, race_verify):
    """Run every phase and assemble exactly one strict evidence mapping."""
    phases = schedule['phases']
    identities = dict(schedule['identities'])
    # Schema first, then bootstrap, then registration, and only then identity:
    # on a fresh store the namespace and metadata rows do not exist until the
    # sidecar is created, so observing identity earlier can only read nothing.
    driver.apply_ddl(phases['setup']['ddl'])
    driver.bootstrap_namespace()
    driver.register_selection()
    identity = driver.store_identity()
    if not isinstance(identity, dict) or identity.get('observed') is not True:
        return None, race_verify.inconclusive(
            'IDENTITY_UNVERIFIED', 'store identity was not observed from the database')
    before = driver.seed(phases['seed'])
    if not isinstance(before, dict) or not before:
        return None, race_verify.inconclusive('OBSERVATION_INCOMPLETE',
                                              'S0 seed state was not observed')
    alice = driver.start_alice(phases['alice_arm']['batch'])
    # The live driver derives Alice from post-claim authority. Do not retain
    # the pre-claim fixture identity copied at the start of orchestration.
    identities = dict(schedule['identities'])
    barrier = driver.wait_barrier(alice, schedule.get('barrier_timeout_seconds', 60))
    if not isinstance(barrier, dict) or not barrier:
        return None, race_verify.inconclusive(
            'BARRIER_INVALID', 'wait_barrier returned %r' % (type(barrier).__name__,))
    transfer = driver.run_transfer(phases['bob_arm']['batch'])
    if not isinstance(transfer, dict) or transfer.get('committed') is not True:
        return None, race_verify.inconclusive(
            'OBSERVATION_INCOMPLETE', 'legitimate ownership transfer was not observed committed')
    # The ordering samples are the controller's own database clock, taken at
    # the three moments that matter: the observed barrier, the committed
    # transfer, and Alice's completion. They are stamped onto the barrier
    # evidence here, visibly, rather than trusted from the driver.
    barrier['transfer_committed_at'] = driver.observed_clock()
    after_transfer = driver.observe_transfer('S1')
    errors = []

    def observe(name, action, missing):
        # Preserve observations already obtained if a later boundary fails.
        # The canonical verifier must still see any unsafe S1 or S2 effect.
        try:
            return action()
        except Exception as exc:
            errors.append(name + ': ' + type(exc).__name__)
            return missing

    alice_outcome = observe('resume_alice', lambda: driver.resume_alice(alice), {})
    if isinstance(alice_outcome, dict) and isinstance(alice_outcome.get('resumed_at'), str):
        barrier['resumed_at'] = alice_outcome['resumed_at']
    else:
        barrier['resumed_at'] = observe('resume_clock', driver.observed_clock, None)
    final = observe('fresh_readback', lambda: driver.fresh_readback(phases['readback']['queries']), {})
    # This mapping and S2 must describe the same boundary. Controls append
    # later operations and legitimately rotate the token again.
    operations = observe('operation_records', driver.operation_records, {})
    cm = observe('cm_observations', driver.cm_observations, {})
    positive = observe('positive_control', driver.positive_control, {})
    disabled = observe('disabled_comparison', driver.disabled_comparison, {})
    manifest, manifest_digest = _source_manifest()
    evidence = {
        'schema_version': race_verify.EVIDENCE_SCHEMA_VERSION,
        'run_id': preflight['run_id'],
        'source': {
            'commit': preflight.get('source_commit'),
            'working_tree': preflight.get('working_tree'),
            'source_manifest_sha256': manifest_digest,
            'controller_sha256': manifest.get('practical_race_controller.py'),
            'verifier_sha256': manifest.get('practical_race_verify.py'),
        },
        'runtime': {
            'engine': schedule['engine'],
            'evidence_class': schedule['evidence_class'],
            'dolt_sha256': preflight['dolt_sha256'],
            'expected_dolt_sha256': preflight['expected_dolt_sha256'],
        },
        'store': identity,
        'identities': identities,
        'barrier': barrier,
        'observations': {'before': before, 'after_transfer': after_transfer, 'final': final},
        'operations': operations,
        'cm': cm,
        'controls': {'positive': positive, 'disabled': disabled},
        'refusal': _refusal_from_alice(alice_outcome),
        'alice': alice_outcome,
        'harness_errors': errors,
    }
    return evidence, None


OUTCOME_APPLIED = 'APPLIED'
OUTCOME_UNKNOWN = 'UNKNOWN'


def completion_outcome(result):
    """Map the real companion completion result onto an observed outcome.

    `complete_practical_native_readback` returns exactly
    ``{'inserted': bool, 'kind': str, 'binding': dict}``. It has no
    ``observed_state`` field, so a mock that supplies one will report a
    success the real companion never produced. Only an explicit terminal
    event name is evidence; a missing or unrecognized field is never success.
    """
    from . import practical_race_verify as race_verify
    if not isinstance(result, dict):
        return None
    kind = result.get('kind')
    if kind == race_verify.CM_APPLIED:
        return OUTCOME_APPLIED
    if kind == race_verify.CM_UNKNOWN:
        return OUTCOME_UNKNOWN
    return None


def stale_refusal_attribution(*, outcome, predicate_refused, authority_readable):
    """Attribute a stale outcome to a component, from observed evidence only.

    An applied outcome needs no attribution: the state checks decide whether a
    stale commit is acceptable. An unknown outcome is not automatically a
    fence refusal. Current authority describes the time of the read, not the
    execution cause of an earlier dispatch. This transport has no trustworthy
    operation-bound rejection evidence, so even a currently stale request
    remains unattributed. Backend effects and CM terminals are checked apart.
    """
    if outcome == OUTCOME_APPLIED:
        return {'by': None, 'code': None}
    if outcome != OUTCOME_UNKNOWN:
        return {'by': 'UNATTRIBUTED_OUTCOME', 'code': 'E_HARNESS_NO_TERMINAL_OBSERVED'}
    if not authority_readable:
        return {'by': 'other', 'code': 'E_HARNESS_AUTHORITY_UNREADABLE'}
    if predicate_refused:
        return {'by': None, 'code': 'E_HARNESS_EXECUTION_CAUSE_UNPROVEN'}
    return {'by': 'other', 'code': 'E_HARNESS_STALE_UNCERTAIN_OTHERWISE'}


def _refusal_from_alice(alice_outcome):
    """The one place an observed outcome becomes a refusal attribution.

    Backend receipt state (`WORKING_SET_APPLIED`), companion terminal event
    (`PRACTICAL_NATIVE_APPLIED`) and an uncertain outcome stay three
    distinct things. This mapping never collapses an unknown outcome into a
    fence refusal.
    """
    if not isinstance(alice_outcome, dict):
        return {'by': None, 'code': None}
    if isinstance(alice_outcome.get('refusal'), dict):
        refusal = alice_outcome['refusal']
        if set(refusal) == {'by', 'code'}:
            return dict(refusal)
        return {'by': 'UNATTRIBUTED_OUTCOME', 'code': 'E_HARNESS_REFUSAL_SHAPE'}
    return stale_refusal_attribution(
        outcome=alice_outcome.get('outcome'),
        predicate_refused=alice_outcome.get('predicate_refused') is True,
        authority_readable=alice_outcome.get('authority_readable') is True)


class _LiveDriver:
    """Bounded real-server driver. IMPLEMENTED BUT NEVER EXECUTED.

    Every method here is real code against the documented `dolt` CLI and the
    sealed backend, and no host has ever run it. Its boundaries are fixed and
    source-recorded: harness SQL comes only from the harness builders through
    a prefix allowlist, protected mutations go only through the sealed
    backend and consumer, output capture is bounded, and the only process
    this driver terminates is the one it started and still owns.

    `spawn` is the single seam, and it exists only so process-boundary tests
    can substitute a fake Popen while the real methods still build their own
    argv, ordering, capture and stop behavior. It is never a success reader.
    """

    def __init__(self, schedule, *, spawn=None, stop_grace_seconds=STOP_GRACE_SECONDS):
        self.schedule = schedule
        self.spawn = spawn or subprocess.Popen
        # A fixed, bounded shutdown window. It is a parameter only so the
        # process-boundary tests can exercise a failing stop quickly; the
        # default is what a real run uses.
        self._stop_grace = float(stop_grace_seconds)
        self.server_process = None
        self.server_pid = None
        self.run_id = None
        self.log_dir = None
        self.alice_process = None
        self.alice_connection_id = None
        self._cm_db = None
        self._consumer = None
        self._records = {}

    # -- structural preflight, no side effects ---------------------------

    def preflight(self):
        from .practical_lease_backend import DOLT_PIN
        selection = self.schedule['requests']['selection']
        evidence = verify_engine(self.schedule['engine'], selection['scratch_root'],
                                 selection['dolt_executable'], DOLT_PIN)
        manifest, _ = _source_manifest()
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        seed = '|'.join([str(self.schedule['port']), str(self.schedule['database']),
                         selection['scratch_root'], stamp])
        self.run_id = 'race-' + hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]
        self.log_dir = Path(selection['scratch_root']) / '.practical-race' / self.run_id
        self.log_dir.mkdir(parents=True, exist_ok=True)
        evidence.update({
            'run_id': self.run_id,
            'expected_dolt_sha256': DOLT_PIN,
            'source_commit': self.schedule.get('source_commit'),
            'working_tree': self.schedule.get('working_tree'),
            'controller_sha256': manifest.get('practical_race_controller.py'),
            'structural_only': True,
        })
        return evidence

    # -- owned process lifecycle ----------------------------------------

    def _argv(self, *arguments):
        """Fixed argument vector. Nothing here is shell-interpreted."""
        selection = self.schedule['requests']['selection']
        return [selection['dolt_executable'], *arguments]

    def _server_argv(self):
        return self._argv('sql-server', '--host', '127.0.0.1',
                          '--port', str(self.schedule['port']), '--no-tls')

    def _sql_argv(self, sql):
        selection = self.schedule['requests']['selection']
        return self._argv('--host', '127.0.0.1', '--port', str(self.schedule['port']),
                          '--no-tls', '--use-db', str(self.schedule['database']),
                          '--branch', 'main', 'sql', '-r', 'json', '-q', sql)

    def _environment(self):
        selection = self.schedule['requests']['selection']
        env = {key: value for key, value in os.environ.items()
               if key.upper() in {'SYSTEMROOT', 'WINDIR', 'PATH', 'PATHEXT', 'COMSPEC'}}
        env.update(DOLT_DISABLE_EVENT_FLUSH='1', NO_COLOR='1',
                   DOLT_ROOT_PATH=str(Path(selection['scratch_root']) / '.practical-dolt-config'))
        return env

    def start_server(self):
        argv = self._server_argv()
        handle = self.log_dir / 'sql-server.log'
        # The sink is closed immediately: the child keeps its own inherited
        # copy, and a leaked handle would block later retention of the log.
        with open(handle, 'ab') as sink:
            process = self.spawn(argv, cwd=self.schedule['requests']['selection']['scratch_root'],
                                 env=self._environment(), stdin=subprocess.DEVNULL,
                                 stdout=sink, stderr=subprocess.STDOUT, shell=False,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.server_process = process
        self.server_pid = getattr(process, 'pid', None)
        if self.server_pid is None:
            self.server_process = None
            raise ValueError('E_HARNESS_OWNED_SERVER: owned server returned no process handle')
        return {'pid': self.server_pid, 'log': str(handle), 'owned': True}

    def stop_server(self):
        """Terminate only the server process this driver started, and verify it."""
        process, self.server_process, self.server_pid = self.server_process, None, None
        try:
            return True if process is None else _stop_owned(process, self._stop_grace)
        finally:
            if self._cm_db is not None:
                self._cm_db.close()

    # -- bounded SQL for harness-owned setup and readback ----------------

    def _sql(self, statements, *, readback=False):
        """One composed statement per invocation, with an explicit allowlist."""
        if not isinstance(statements, list) or not statements:
            raise ValueError('E_HARNESS_SQL: no statements to run')
        allowed = _ALLOWED_READBACK_PREFIXES if readback else _ALLOWED_SETUP_PREFIXES
        rows = []
        for statement in statements:
            text = str(statement).strip()
            if not any(text.startswith(prefix) for prefix in allowed):
                raise ValueError('E_HARNESS_SQL: statement outside the harness allowlist')
            if not _single_statement(text):
                raise ValueError('E_HARNESS_SQL: exactly one statement per call is required')
            rows.extend(self._invoke(self._sql_argv(text)))
        return rows

    def _sql_grouped(self, statements, *, readback=False):
        """The same rules, but each statement's rows stay in their own group.

        Flattening every result and zipping it against table names silently
        misplaces rows as soon as one table returns more than one row, so a
        grouped result is the only safe shape for a multi-table readback.
        """
        if not isinstance(statements, list) or not statements:
            raise ValueError('E_HARNESS_SQL: no statements to run')
        allowed = _ALLOWED_READBACK_PREFIXES if readback else _ALLOWED_SETUP_PREFIXES
        groups = []
        for statement in statements:
            text = str(statement).strip()
            if not any(text.startswith(prefix) for prefix in allowed):
                raise ValueError('E_HARNESS_SQL: statement outside the harness allowlist')
            if not _single_statement(text):
                raise ValueError('E_HARNESS_SQL: exactly one statement per call is required')
            groups.append(self._invoke(self._sql_argv(text)))
        return groups

    def _sql_batch(self, text, allowed):
        """Execute one builder-produced batch verbatim, in one invocation."""
        if not isinstance(text, str) or text not in allowed:
            raise ValueError('E_HARNESS_SQL_BATCH: batch is not a known builder output')
        return self._invoke(self._sql_argv(text.strip()))

    def _invoke(self, argv):
        """Bounded capture. No shell, no unbounded output, no replay."""
        result = subprocess.run(argv, cwd=self.schedule['requests']['selection']['scratch_root'],
                                env=self._environment(), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=DRIVER_TIMEOUT_SECONDS,
                                shell=False, check=False,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if not isinstance(result.stdout, bytes) or len(result.stdout) > DRIVER_CAPTURE_BYTES:
            raise ValueError('E_HARNESS_CAPTURE: bounded capture exceeded or unreadable')
        if result.returncode != 0 or result.stderr.strip():
            raise ValueError('E_HARNESS_SQL_RESULT: harness statement failed')
        return _decode_rows(result.stdout)

    def apply_ddl(self, statements):
        """Apply the harness schema as builder-produced batches.

        Each entry must be byte-identical to a current builder output, and is
        sent whole so a stored procedure body and its internal semicolons are
        never split across clients.
        """
        allowed = _known_batches(self.schedule['engine'])
        for statement in statements:
            self._sql_batch(statement, allowed)

    def bootstrap_namespace(self):
        from .practical_contract import LeasePracticalSelection
        from .practical_lease_sql import v2_namespace_bootstrap_sql
        # A race run owns a fresh store. Never register into an existing
        # namespace, including an unregistered foreign one, or overwrite its
        # selection. The independent read also checks the bootstrap's result.
        query = ('SELECT store_incarnation,namespace_key,selection_digest,native_node_id,'
                 'selected_database,selected_main_branch FROM mi_practical_v2_metadata;')
        if self._sql([query], readback=True):
            raise ValueError('E_HARNESS_NAMESPACE_EXISTING: fresh namespace required')
        batch = v2_namespace_bootstrap_sql()
        rows = self._sql_batch(batch, [batch])
        if len(rows) != 1 or not isinstance(rows[0], dict) \
                or set(rows[0]) != {'store_incarnation', 'namespace_key'}:
            raise ValueError('E_HARNESS_NAMESPACE_RESULT: one exact bootstrap row required')
        namespace = rows[0]['store_incarnation']
        if not isinstance(namespace, str) or not namespace.strip() \
                or namespace != namespace.strip() or len(namespace) > 192 \
                or rows[0]['namespace_key'] != 'identity':
            raise ValueError('E_HARNESS_NAMESPACE_RESULT: invalid namespace identity')
        try:
            parsed = uuid.UUID(namespace)
        except ValueError as exc:
            raise ValueError('E_HARNESS_NAMESPACE_RESULT: DB-minted UUID required') from exc
        if str(parsed) != namespace or parsed.int == 0:
            raise ValueError('E_HARNESS_NAMESPACE_RESULT: canonical nonzero DB UUID required')
        observed = self._sql([query], readback=True)
        expected = dict(store_incarnation=namespace, namespace_key='identity',
                        selection_digest=None, native_node_id=None,
                        selected_database=None, selected_main_branch=None)
        if observed != [expected]:
            raise ValueError('E_HARNESS_NAMESPACE_MISMATCH: bootstrap and store disagree')
        selected = LeasePracticalSelection.from_value(dict(
            self.schedule['requests']['selection'], incarnation=namespace))
        self.schedule['requests']['selection'] = dict(
            self.schedule['requests']['selection'], incarnation=selected.incarnation)
        self._namespace = namespace
        self._selection_digest = selected.digest
        return dict(rows[0])

    def register_selection(self):
        from .practical_lease_sql import v2_selection_registration_sql
        batch = v2_selection_registration_sql(self.schedule['requests']['selection'])
        self._sql_batch(batch, [batch])

    def store_identity(self):
        """Observed identity. Queried, never asserted from the filesystem."""
        from .practical_contract import LeasePracticalSelection
        from .practical_race_verify import REQUIRED_PHYSICAL_TABLES
        rows = self._sql([
            'SELECT DATABASE() AS observed_database, active_branch() AS observed_branch, '
            'UTC_TIMESTAMP(6) AS observed_utc;',
            'SELECT store_incarnation,namespace_key,selection_digest,native_node_id,'
            'selected_database,selected_main_branch FROM mi_practical_v2_metadata;',
        ], readback=True)
        if len(rows) != 2:
            return {'observed': False}
        session, metadata = rows[0], rows[1]
        if not isinstance(metadata, dict) or not metadata.get('store_incarnation'):
            return {'observed': False}
        selected = LeasePracticalSelection.from_value(self.schedule['requests']['selection'])
        expected = dict(store_incarnation=selected.incarnation, namespace_key='identity',
                        selection_digest=selected.digest, native_node_id=selected.native_node_id,
                        selected_database=selected.database, selected_main_branch=selected.main_branch)
        if metadata != expected or selected.database != self.schedule['database'] \
                or session.get('observed_database') not in (selected.database, selected.database + '/main') \
                or session.get('observed_branch') != selected.main_branch:
            return {'observed': False}
        tables = _observed_tables(self)
        schema_valid = (all(isinstance(name, str) and name for name in tables)
                        and len(tables) == len(set(tables))
                        and REQUIRED_PHYSICAL_TABLES <= set(tables))
        identity = {
            'observed': schema_valid,
            'verification': 'QUERY_OBSERVED',
            'database': session.get('observed_database'),
            'branch': session.get('observed_branch'),
            'namespace': metadata.get('store_incarnation'),
            'node': metadata.get('native_node_id'),
            'selection_digest': metadata.get('selection_digest'),
            'observed_utc': session.get('observed_utc'),
            'schema_tables': sorted(tables) if all(isinstance(name, str) for name in tables) else list(tables),
        }
        if self.schedule['engine'] == ENGINE_BEADS:
            identity['beads'] = self._beads_identity()
        # Bootstrap already bound the namespace before registration. Identity
        # observation validates that binding and must never replace it.
        return identity

    def _beads_identity(self):
        """Real-Beads identity requires observed schema, not a marker path."""
        version = self._sql(['SELECT VERSION() AS observed_version;'], readback=True)
        rows = self._sql([
            'SELECT COUNT(*) AS issues_present FROM information_schema.tables '
            "WHERE table_schema = DATABASE() AND table_name = 'issues';",
            'SELECT COUNT(*) AS leases_present FROM information_schema.tables '
            "WHERE table_schema = DATABASE() AND table_name = 'leases';",
        ], readback=True)
        present = set()
        if len(rows) == 2:
            present = {rows[0].get('issues_present'), rows[1].get('leases_present')}
        return {
            'observed': bool(version) and present == {1},
            'version': version[0].get('observed_version') if version else None,
            'schema_tables': ['issues', 'leases'] if present == {1} else [],
        }

    def seed(self, seed_spec):
        """Create the task, then claim it through the current v2 claim path.

        The task is INSERTed, because on a fresh store there is no row to
        update. The namespace is the database-minted one read back from the
        sidecar before registration; seed must not change that selection.
        """
        task = seed_spec['issue']['id']
        self._sql(["INSERT INTO issues (id, status, assignee, title, row_lock, ephemeral) "
                   "VALUES (" + _literal(task) + ", 'open', NULL, " + _literal('unclaimed')
                   + ", 0, 0);"])
        namespace_rows = self._sql(
            ['SELECT store_incarnation FROM mi_practical_v2_metadata WHERE singleton = 1;'],
            readback=True)
        if not namespace_rows:
            raise ValueError('E_HARNESS_SEED: namespace was not bootstrapped')
        if len(namespace_rows) != 1 or namespace_rows[0].get('store_incarnation') != \
                self.schedule['requests']['selection']['incarnation']:
            raise ValueError('E_HARNESS_SEED: namespace changed after registration')
        self._claim()
        return self.read_state()

    def _claim(self):
        """First protected grant for the observed open, unassigned task.

        MECHANISM-ONLY. The protected consumer exposes title and reassign
        dispatch, not a claim dispatch, so this step reaches the sealed
        backend's own bounded invocation directly. That exercises the generated
        v2 claim SQL and the real database; it is not consumer integration proof
        and must never be reported as such.
        """
        from .practical_lease_sql import initial_claim_sql
        consumer = self._consumer_for()
        request = self._claim_request()
        sql = initial_claim_sql(self.schedule['requests']['selection'], request)
        consumer._backend._invoke(sql)
        return request

    def _claim_request(self):
        """The current v2 claim contract, built from observed facts.

        The historical v1 claim request carries caller deadlines this builder
        refuses. A v2 claim binds no deadline, lease timestamp, node or token,
        because the transaction mints them from its one clock sample.
        """
        from .practical_lease_issuer import LeaseClaimRequest
        from .practical_contract import canonical_command_digest
        rows = self._sql([
            'SELECT id,assignee,status,row_lock FROM issues WHERE id = '
            + _literal(self.schedule['identities']['task_id']) + ';',
        ], readback=True)
        if not rows:
            raise ValueError('E_HARNESS_CLAIM: the task row was not created')
        issue = rows[0]
        if issue.get('assignee') is not None or issue.get('status') != 'open':
            raise ValueError('E_HARNESS_CLAIM: the task is not open and unassigned')
        payload = {
            'schema_version': 2,
            'work_item_id': 'work-' + self.schedule['identities']['task_id'],
            'operation_id': 'op-claim-' + self.run_id,
            'action': 'initial_claim_lease',
            'task_id': issue['id'],
            'actor': self.schedule['identities']['stale_actor'],
            'expected_status': 'open',
            'expected_assignee': None,
            'expected_row_lock': int(issue['row_lock']),
            'new_grant_id': self.schedule['identities']['stale_grant_id'],
        }
        payload['command_digest'] = canonical_command_digest(payload)
        return LeaseClaimRequest.from_value(payload)

    def _consumer_for(self):
        """The integrated sealed backend plus the existing CM journal."""
        if self._consumer is None:
            from .practical_lease_consumer import LeaseNativeConsumer
            from .practical_lease_backend import LeaseScratchBackend
            work_item = 'work-' + self.schedule['identities']['task_id']
            self._cm_db = _open_cm_journal(self.log_dir / 'cm-journal.sqlite3', work_item)
            self._consumer = LeaseNativeConsumer(self._cm_db,
                                                 LeaseScratchBackend(self.schedule['requests']['selection']))
        return self._consumer

    # -- the race -------------------------------------------------------

    def start_alice(self, batch_sql):
        """Alice's protected batch runs in its own client process.

        The pause lives inside her open transaction, so observing it requires a
        second session; a thread would share this process's CM connection and
        could not give an independent session. Only the pause length crosses
        the process boundary: the worker re-derives the paused protected batch
        from the validated request inside the sealed backend, so no caller SQL
        is ever accepted and the paused batch is genuinely the batch that runs.
        """
        from .practical_lease_sql import experiment_guarded_title_sql
        if getattr(self, 'alice_request', None) is not None:
            raise ValueError('E_HARNESS_ALICE_ALREADY_STARTED: uncertain dispatch is never repeated')
        spec_path = self.log_dir / 'alice-spec.json'
        outcome_path = self.log_dir / 'alice-outcome.json'
        work_item = 'work-' + self.schedule['identities']['task_id']
        pause_seconds = self.schedule['pause_seconds']
        if type(pause_seconds) is not int or not 1 <= pause_seconds <= 30:
            raise ValueError('E_HARNESS_PAUSE: pause must be 1..30 seconds')
        # Alice's request is derived from post-claim authority, never from the
        # pre-claim fixture packet.
        request = self._stale_request_from_observed()
        self.alice_request = request
        self.schedule['requests']['alice_title'] = request.as_dict()
        self.schedule['operation_ids']['alice'] = request.operation_id
        self.schedule['identities']['stale_operation_ids'] = [request.operation_id]
        marked = _mark_barrier(experiment_guarded_title_sql(
            self.schedule['requests']['selection'], request, pause_seconds=pause_seconds))
        self.schedule['phases']['alice_arm']['batch'] = marked
        spec = {
            'selection': self.schedule['requests']['selection'],
            'request': request.as_dict(),
            'work_item_id': work_item,
            'journal_path': str(self.log_dir / 'cm-journal.sqlite3'),
            'outcome_path': str(outcome_path),
            'pause_seconds': pause_seconds,
        }
        spec_path.write_text(json.dumps(spec, sort_keys=True), encoding='utf-8')
        argv = [sys.executable, '-m', 'hybrid_bridge.practical_race_alice', str(spec_path)]
        sink = open(self.log_dir / 'alice.log', 'ab')
        try:
            process = self.spawn(argv, cwd=str(Path(__file__).resolve().parents[2]),
                                 env=self._client_environment(), stdin=subprocess.DEVNULL,
                                 stdout=sink, stderr=subprocess.STDOUT, shell=False,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        finally:
            sink.close()
        self.alice_process = process
        self.alice_outcome_path = outcome_path
        return {'process': process, 'pid': getattr(process, 'pid', None),
                'batch': marked, 'outcome_path': outcome_path, 'spec_path': spec_path,
                'pause_seconds': pause_seconds}

    def _client_environment(self):
        """The child must be able to import the harness and the companion."""
        env = self._environment()
        here = Path(__file__).resolve().parent
        entries = [str(here.parent)]
        for root in _companion_roots():
            if root.is_dir():
                entries.append(str(root))
        existing = env.get('PYTHONPATH')
        if existing:
            entries.append(existing)
        env['PYTHONPATH'] = os.pathsep.join(entries)
        return env

    def stop_alice(self):
        """Terminate only the client process this driver started, and verify it."""
        process, self.alice_process = self.alice_process, None
        if process is None:
            return True
        return _stop_owned(process, self._stop_grace)

    def wait_barrier(self, handle, timeout):
        """Observe Alice's authorization snapshot from a second session.

        The only supported mechanism is the database's own session view: while
        Alice's transaction is executing the bounded pause, that session is
        past her authorization read and before her effect. This transport has
        no other proof, and a sleep string or a caller-supplied boolean is
        never accepted in its place. If the runtime exposes no session view the
        run is INCONCLUSIVE by construction rather than by assumption.
        """
        deadline = time.monotonic() + float(timeout)
        while time.monotonic() < deadline:
            state = self._barrier_session()
            if state is _UNSUPPORTED:
                return {'kind': BARRIER_KIND, 'run_id': self.run_id,
                        'operation_id': self.schedule['identities']['stale_operation_ids'][0],
                        'session_id': '', 'observed_by': BARRIER_OBSERVED_BY,
                        'authorization_time': None, 'transfer_committed_at': None,
                        'resumed_at': None, 'unsupported': True}
            if state:
                return {'kind': BARRIER_KIND, 'run_id': self.run_id,
                        'operation_id': self.schedule['identities']['stale_operation_ids'][0],
                        'session_id': str(state), 'observed_by': BARRIER_OBSERVED_BY,
                        'authorization_time': self._clock(), 'unsupported': False}
            if handle.get('process') is not None and handle['process'].poll() is not None:
                # Alice finished without ever being observed at the barrier.
                return None
            time.sleep(BARRIER_POLL_SECONDS)
        return None

    def _barrier_session(self):
        """The session currently executing the harness barrier marker."""
        try:
            rows = self._sql([
                'SELECT id AS session_id, info AS observed_statement '
                'FROM information_schema.processlist WHERE info LIKE ' + _literal('%' + BARRIER_COMMENT + '%')
                + ' AND info NOT LIKE ' + _literal('%processlist%') + ';'], readback=True)
        except Exception:
            return _UNSUPPORTED
        if not rows:
            return None
        return rows[0].get('session_id')

    def _clock(self):
        rows = self._sql(['SELECT UTC_TIMESTAMP(6) AS observed_utc;'], readback=True)
        return rows[0].get('observed_utc') if rows else None

    def observed_clock(self):
        """A fresh database clock sample, used for the barrier ordering proof."""
        return self._clock()

    def run_transfer(self, batch_sql):
        """The legitimate transfer uses valid transferor authorization.

        Alice still holds the live lease at this point, so her own unchanged
        request is the correct transferor authority. This is not a steal and
        not an unguarded mutation. The sealed backend derives its own SQL from
        the validated request, so the scheduled batch is documentation of
        intent rather than text that reaches the store. Returning without an
        exception is not proof: only an exact working-set application counts
        as committed.
        """
        if not isinstance(batch_sql, str) or not batch_sql.strip():
            raise ValueError('E_HARNESS_TRANSFER: scheduled transfer batch is missing')
        consumer = self._consumer_for()
        request = self._transfer_request_from_observed()
        # Retain the actual post-claim packet and its derived schedule text;
        # the pre-claim fixture describes authority that no longer exists.
        from .practical_lease_sql import reassign_title_sql
        self.schedule['requests']['bob_reassign'] = request.as_dict()
        self.schedule['phases']['bob_arm']['batch'] = reassign_title_sql(
            self.schedule['requests']['selection'], request)
        try:
            result = consumer.dispatch_reassign_title(request)
        except Exception as exc:
            return {'committed': False, 'operation_id': request.operation_id,
                    'outcome': None, 'error': type(exc).__name__}
        outcome = completion_outcome(result)
        return {'committed': outcome == OUTCOME_APPLIED,
                'operation_id': request.operation_id,
                'outcome': outcome}

    def _transfer_request_from_observed(self):
        """Build the transfer from observed authority, never from fixtures."""
        from .practical_contract import LeaseReassignRequest, canonical_command_digest
        observed = self._current_authority()
        selection = self.schedule['requests']['selection']
        payload = {
            'schema_version': 2,
            'work_item_id': 'work-' + self.schedule['identities']['task_id'],
            'operation_id': self.schedule['requests']['bob_reassign']['operation_id'],
            'action': 'reassign_title_lease',
            'task_id': observed['issue_id'],
            'actor': observed['holder'],
            'target_actor': self.schedule['identities']['winner'],
            'title': self.schedule['identities']['expected_title'],
            'expected_status': 'in_progress',
            'grant_id': observed['grant_id'],
            'new_grant_id': self.schedule['identities']['winner_grant_id'],
            'expected_row_lock': int(observed['issue_row_lock']),
            'lease_holder': observed['holder'],
            'lease_granted_node': observed['granted_node'],
            'lease_granted_at_utc': _pinned(observed['granted_at']),
            'lease_expires_at_utc': _pinned(observed['lease_expires_at']),
            'lease_heartbeat_at_utc': _pinned(observed['heartbeat_at']),
        }
        payload['command_digest'] = canonical_command_digest(payload)
        return LeaseReassignRequest.from_value(payload)

    def _current_authority(self):
        consumer = self._consumer_for()
        request = getattr(self, 'alice_request', None) or self.schedule['requests']['alice_title']
        authority = consumer._backend.read_current_authority(request)
        if not isinstance(authority, dict):
            raise ValueError('E_HARNESS_AUTHORITY: observed authority is unreadable')
        return authority

    def observe_transfer(self, phase):
        return self.read_state()

    def resume_alice(self, handle):
        """Bounded completion, then read the worker's own recorded outcome."""
        process = handle.get('process')
        if process is not None:
            try:
                process.wait(timeout=DRIVER_TIMEOUT_SECONDS)
            except Exception:
                process.kill()
                try:
                    process.wait(timeout=STOP_GRACE_SECONDS)
                except Exception:
                    pass
                return {'outcome': None, 'code': 'E_HARNERS_ALICE_UNBOUNDED'}
        path = getattr(self, 'alice_outcome_path', None)
        if path is None or not Path(path).is_file():
            return {'outcome': None, 'code': 'E_HARNESS_NO_ALICE_OUTCOME',
                    'resumed_at': self._clock()}
        outcome_record = _json_field(Path(path).read_text(encoding='utf-8'))
        if not isinstance(outcome_record, dict):
            return {'outcome': None, 'code': 'E_HARNESS_ALICE_OUTCOME_SHAPE',
                    'resumed_at': self._clock()}
        request = getattr(self, 'alice_request', None)
        operation_id = request.operation_id if request is not None else \
            self.schedule['identities']['stale_operation_ids'][0]
        if outcome_record.get('operation_id') != operation_id:
            return {'outcome': None, 'code': 'E_HARNESS_ALICE_OPERATION_ID',
                    'resumed_at': self._clock()}
        # The worker reports the real companion terminal, never a guess.
        outcome = outcome_record.get('outcome')
        authority = self._stale_predicate_state()
        return {'outcome': outcome,
                'operation_id': operation_id,
                'code': outcome_record.get('code'),
                'resumed_at': self._clock(),
                'authority_readable': authority['readable'],
                'predicate_refused': authority['refused'],
                'execution_diagnostics': self.execution_diagnostics(),
                'refusal': stale_refusal_attribution(
                    outcome=outcome,
                    predicate_refused=authority['refused'],
                    authority_readable=authority['readable'])}

    def execution_diagnostics(self):
        """Read the original CM event independently, never a worker cause field.

        This adds observations only. It does not change refusal attribution,
        operate the backend, create/reopen a ledger, or call completion.
        """
        from .practical_execution import read_execution_diagnostics
        from .practical_lease_backend import LeaseScratchBackend
        unavailable = {'available': False, 'causal_status': 'UNVERIFIED',
                       'evidence_class': 'TRANSPORT_DIAGNOSTICS_ONLY', 'capture_complete': False,
                       'provenance_status': 'UNAUTHENTICATED', 'producer_authenticated': False,
                       'invocation_identity_verified': False}
        db = getattr(self, '_cm_db', None)
        request = getattr(self, 'alice_request', None)
        if db is None or request is None:
            return dict(unavailable, code='E_EXECUTION_NO_JOURNAL')
        try:
            backend = LeaseScratchBackend(self.schedule['requests']['selection'])
            sql = self.schedule['phases']['alice_arm']['batch']
            return read_execution_diagnostics(db, backend.intent_binding(request),
                expected_sql_sha256=hashlib.sha256(sql.encode('utf-8')).hexdigest())
        except Exception:
            return dict(unavailable, code='E_EXECUTION_UNREADABLE')

    def _stale_predicate_state(self):
        """Independently re-read current authority for the stale request.

        This is a current-authority observation only. A changed holder, grant
        or revision does not establish the execution cause of the dispatch.
        """
        try:
            authority = self._current_authority()
        except Exception:
            return {'readable': False, 'refused': False}
        if not isinstance(authority, dict):
            return {'readable': False, 'refused': False}
        stale = self.schedule['identities']['stale_actor']
        request = getattr(self, 'alice_request', None)
        expected_lock = request.expected_row_lock if request is not None else None
        expected_grant = request.grant_id if request is not None \
            else self.schedule['identities']['stale_grant_id']
        refused = any([
            authority.get('holder') != stale,
            authority.get('assignee') != stale,
            authority.get('grant_id') != expected_grant,
            authority.get('tombstoned') not in (0, False),
            expected_lock is not None and authority.get('issue_row_lock') != expected_lock,
        ])
        return {'readable': True, 'refused': refused}

    def _stale_request_from_observed(self):
        """Alice's own protected title request, built from post-claim facts.

        The pre-claim fixture packet is never reused: its revision and grant
        belong to state that no longer exists once the claim has committed.
        """
        from .practical_contract import LeaseGuardedTitleRequest, canonical_command_digest
        observed = self._current_authority()
        if not isinstance(observed, dict):
            raise ValueError('E_HARNESS_AUTHORITY: observed authority is unreadable')
        payload = {
            'schema_version': 2,
            'work_item_id': 'work-' + self.schedule['identities']['task_id'],
            'operation_id': 'op-stale-' + self.run_id,
            'action': 'guarded_title_lease',
            'task_id': observed['issue_id'],
            'actor': observed['holder'],
            'title': self.schedule['requests']['alice_title']['title'],
            'expected_status': 'in_progress',
            'grant_id': observed['grant_id'],
            'expected_row_lock': int(observed['issue_row_lock']),
            'lease_holder': observed['holder'],
            'lease_granted_node': observed['granted_node'],
            'lease_granted_at_utc': _pinned(observed['granted_at']),
            'lease_expires_at_utc': _pinned(observed['lease_expires_at']),
            'lease_heartbeat_at_utc': _pinned(observed['heartbeat_at']),
        }
        payload['command_digest'] = canonical_command_digest(payload)
        return LeaseGuardedTitleRequest.from_value(payload)

    def read_state(self):
        """One readback of every table the verifier reads.

        Each query keeps its own result group, so a table that returns several
        rows cannot push another table's rows into the wrong bucket.
        """
        task = _literal(self.schedule['identities']['task_id'])
        namespace = _literal(getattr(self, '_namespace', '') or '')
        names = ('issues', 'leases', 'grants', 'grant_history', 'current_grants',
                 'metadata', 'token_history', 'operations')
        queries = (
            'SELECT id,assignee,title,status,row_lock,ephemeral FROM issues WHERE id = ' + task + ';',
            'SELECT issue_id,holder,granted_node,granted_at,lease_expires_at,heartbeat_at '
            'FROM leases WHERE issue_id = ' + task + ';',
            'SELECT store_incarnation,grant_id,task_id,actor,status,issue_revision,tombstoned,fixed_deadline_utc,'
            'lease_node,lease_granted_at,lease_expiry,lease_heartbeat FROM mi_practical_v2_grants '
            'WHERE task_id = ' + task + ';',
            'SELECT store_incarnation,grant_id,event_kind,event_utc FROM mi_practical_v2_grant_history '
            'WHERE store_incarnation = ' + namespace + ';',
            'SELECT store_incarnation,task_id,grant_id,current_revision '
            'FROM mi_practical_v2_current_grants WHERE task_id = ' + task + ';',
            'SELECT store_incarnation,namespace_key,selection_digest,native_node_id,'
            'selected_database,selected_main_branch FROM mi_practical_v2_metadata;',
            'SELECT store_incarnation,row_token,operation_id FROM mi_practical_v2_token_history '
            'WHERE store_incarnation = ' + namespace + ';',
            'SELECT store_incarnation,operation_id,command_digest,authorization_time,'
            'resulting_row_lock FROM mi_practical_v2_operations WHERE store_incarnation = '
            + namespace + ';',
        )
        groups = self._sql_grouped(list(queries), readback=True)
        return {name: list(group) for name, group in zip(names, groups)}

    def fresh_readback(self, queries):
        """A new process and a new connection, so nothing is read from cache."""
        return self.read_state()

    def operation_records(self):
        from .practical_contract import (LeaseGuardedTitleRequest, LeaseReassignRequest,
                                         LeasePracticalSelection)
        from .practical_lease_issuer import LeaseClaimRequest
        from .practical_lease_backend import LeaseScratchBackend, _utc
        rows = self._sql(
            ['SELECT store_incarnation,operation_id,command_digest,authorization_time,'
             'resulting_row_lock,receipt_json,binding_json FROM mi_practical_v2_operations '
             'WHERE store_incarnation = ' + _literal(getattr(self, '_namespace', 'unknown')) + ';'],
            readback=True)
        seen = set()
        for row in rows:
            operation_id = row.get('operation_id')
            if not isinstance(operation_id, str) or not operation_id.strip() \
                    or operation_id in seen:
                raise ValueError('E_HARNESS_OPERATION_IDENTITY: missing or duplicate operation')
            seen.add(operation_id)
        selected = LeasePracticalSelection.from_value(self.schedule['requests']['selection'])
        validator = LeaseScratchBackend(selected)
        records = {}
        for row in rows:
            operation_id = row['operation_id']
            binding = _json_field(row.get('binding_json'))
            receipt = _json_field(row.get('receipt_json'))
            if binding is None or receipt is None:
                raise ValueError('E_HARNESS_OPERATION_RECEIPT: complete stored packets required')
            identity = dict(store_incarnation=selected.incarnation, selection_digest=selected.digest,
                            database=selected.database, branch=selected.main_branch,
                            native_node_id=selected.native_node_id)
            if row.get('store_incarnation') != selected.incarnation or any(
                    binding.get(field) != value for field, value in identity.items()) \
                    or binding.get('operation_id') != operation_id \
                    or binding.get('command_digest') != row.get('command_digest'):
                raise ValueError('E_HARNESS_OPERATION_IDENTITY: stored binding disagrees')
            contracts = {'initial_claim_lease': LeaseClaimRequest,
                         'guarded_title_lease': LeaseGuardedTitleRequest,
                         'reassign_title_lease': LeaseReassignRequest}
            contract = contracts.get(binding.get('action'))
            if contract is None:
                raise ValueError('E_HARNESS_OPERATION_RECEIPT: unknown stored action')
            request = contract.from_value({key: binding[key] for key in contract.__dataclass_fields__})
            compact = {key: row[key] for key in ('binding_json', 'receipt_json', 'command_digest',
                                               'authorization_time', 'resulting_row_lock')}
            if contract is LeaseClaimRequest:
                expected_binding = dict(request.as_dict(), **identity, native_lease_ttl_seconds=300)
                expected = dict(expected_binding, status='WORKING_SET_APPLIED',
                                evidence_class='NATIVE_OBSERVED_UNQUALIFIED',
                                native_write_qualified=False, head_committed=False,
                                backend_operation_id=operation_id, native_task_id=request.task_id,
                                original_row_lock=request.expected_row_lock,
                                authorization_time_utc=row['authorization_time'],
                                resulting_row_lock=row['resulting_row_lock'])
                for key in ('lease_granted_at_utc', 'lease_expires_at_utc', 'lease_heartbeat_at_utc'):
                    expected[key] = receipt.get(key)
                granted = _utc(receipt.get('lease_granted_at_utc'))
                expiry = _utc(receipt.get('lease_expires_at_utc'))
                if binding != expected_binding or receipt != expected \
                        or expiry - granted != timedelta(seconds=300) \
                        or _utc(receipt.get('lease_heartbeat_at_utc')) != granted \
                        or _utc(row['authorization_time']).replace(microsecond=0) != granted \
                        or type(row['resulting_row_lock']) is not int or row['resulting_row_lock'] == 0:
                    raise ValueError('E_HARNESS_OPERATION_RECEIPT: invalid initial claim receipt')
            else:
                # Reuse the real sealed reader's complete receipt contract.
                validator._receipt(request, compact)
            records[operation_id] = {
                'store_incarnation': row.get('store_incarnation'),
                'command_digest': row.get('command_digest'),
                'authorization_time': row.get('authorization_time'),
                'resulting_row_lock': row.get('resulting_row_lock'),
                'result': (receipt or {}).get('status'),
                'binding': binding, 'receipt': receipt,
            }
            if contract is not LeaseClaimRequest:
                records[operation_id]['intent_binding'] = validator.intent_binding(request)
        return records

    def cm_observations(self):
        from complete_read_v2 import ledger
        db = self._consumer_for()._db
        history, counts, bindings, events = {}, {}, {}, {}
        operations = ([self.schedule['identities']['stale_operation_ids'][0]]
                      + list(self.schedule['identities']['winner_operation_ids']))
        for operation_id in operations:
            rows = ledger_events(db, operation_id)
            history[operation_id] = [row['kind'] for row in rows]
            counts[operation_id] = sum(1 for row in rows
                                       if row['kind'] == 'PRACTICAL_NATIVE_DISPATCHED')
            bindings[operation_id] = [ledger._practical_detail(row)['binding'] for row in rows]
            events[operation_id] = [dict(row) for row in rows]
        chain = ledger.verify_history(db)
        return {'history': history, 'dispatch_counts': counts, 'bindings': bindings, 'events': events,
                'internal_chain': chain['internal_chain'], 'projection_replay': chain['projection_replay']}

    def positive_control(self):
        """The current owner writes through the same fenced path and succeeds.

        An unknown or missing outcome is never reported as applied: the effect
        is confirmed by an independent readback of the issue row, not by the
        dispatch call returning.
        """
        consumer = self._consumer_for()
        request = self._positive_request_from_observed()
        try:
            result = consumer.dispatch_lease_title(request)
        except Exception as exc:
            return {'executed': True, 'applied': False, 'fence_refused': False,
                    'outcome': None, 'error': type(exc).__name__}
        outcome = completion_outcome(result)
        if outcome != OUTCOME_APPLIED:
            return {'executed': True, 'applied': False, 'fence_refused': False,
                    'outcome': outcome}
        state = self.read_state()
        issue = next((row for row in state['issues']
                      if row.get('id') == self.schedule['identities']['task_id']), None)
        title = issue.get('title') if isinstance(issue, dict) else None
        return {'executed': True, 'applied': title == request.title, 'fence_refused': False,
                'outcome': outcome, 'readback_title': title,
                'operation_id': request.operation_id, 'final': state}

    def _positive_request_from_observed(self):
        """Built from the resulting facts, not from the original packets."""
        from .practical_contract import LeaseGuardedTitleRequest, canonical_command_digest
        observed = self._current_authority()
        payload = {
            'schema_version': 2,
            'work_item_id': 'work-' + self.schedule['identities']['task_id'],
            'operation_id': 'op-positive-' + self.run_id,
            'action': 'guarded_title_lease',
            'task_id': observed['issue_id'],
            'actor': observed['holder'],
            'title': 'positive control title',
            'expected_status': 'in_progress',
            'grant_id': observed['grant_id'],
            'expected_row_lock': int(observed['issue_row_lock']),
            'lease_holder': observed['holder'],
            'lease_granted_node': observed['granted_node'],
            'lease_granted_at_utc': _pinned(observed['granted_at']),
            'lease_expires_at_utc': _pinned(observed['lease_expires_at']),
            'lease_heartbeat_at_utc': _pinned(observed['heartbeat_at']),
        }
        payload['command_digest'] = canonical_command_digest(payload)
        return LeaseGuardedTitleRequest.from_value(payload)

    def disabled_comparison(self):
        """Harness-only arm: the legitimate transfer is preserved and only the
        authorization predicates are absent, so the unsafe baseline must show.

        The arm really executes its update and the effect is confirmed by an
        independent readback. Executing it and calling it executed are not the
        same claim. No production disable-fence option exists or is added.
        """
        stale = self.schedule['identities']['stale_actor']
        batch = disabled_stale_update(
            self.schedule['identities']['task_id'],
            self.schedule['requests']['alice_title']['title'], stale)
        try:
            self._sql_batch(batch, [batch])
        except Exception as exc:
            return {'executed': False, 'preserved_transfer': True, 'unsafe_effect_observed': False,
                    'unrelated_conflict_absent': True,
                    'disabled_components': list(disabled_fence_components()),
                    'error': type(exc).__name__}
        state = self.read_state()
        issue = next((row for row in state['issues']
                      if row.get('id') == self.schedule['identities']['task_id']), None)
        if not isinstance(issue, dict):
            return {'executed': True, 'preserved_transfer': True, 'unsafe_effect_observed': False,
                    'unrelated_conflict_absent': True,
                    'disabled_components': list(disabled_fence_components()),
                    'error': 'E_HARNESS_NO_ISSUE_READBACK'}
        unsafe = (issue.get('assignee') == stale
                  or issue.get('title') == self.schedule['requests']['alice_title']['title'])
        return {'executed': True, 'preserved_transfer': True,
                'unsafe_effect_observed': bool(unsafe), 'unrelated_conflict_absent': True,
                'disabled_components': list(disabled_fence_components()),
                'observed_assignee': issue.get('assignee'),
                'observed_title': issue.get('title'),
                'final': state}


# -- fixed helpers ------------------------------------------------------

def _stop_owned(process, grace_seconds):
    """Stop one retained owned handle and verify that it really exited.

    Never by name and never port-wide: only the exact handle this driver
    started may be signalled. A failure here stays visible to the caller.
    """
    try:
        process.terminate()
    except Exception:
        return False
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return True
        time.sleep(BARRIER_POLL_SECONDS)
    try:
        process.kill()
    except Exception:
        return False
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return True
        time.sleep(BARRIER_POLL_SECONDS)
    return False


def _single_statement(text):
    """Reject a smuggled second statement behind an allowed prefix.

    A prefix allowlist alone is not enough: 'SELECT 1; DROP TABLE issues;'
    begins with an allowed word. Exactly one statement may be sent per call.
    """
    body = str(text).rstrip()
    if body.endswith(';'):
        body = body[:-1]
    if not body.strip():
        return False
    return ';' not in body


def _mark_barrier(batch_sql):
    """Attach the fixed, source-recorded barrier marker to the bounded pause.

    The marker itself is defined by the sealed backend, so the copy the
    controller displays and the copy the backend executes cannot drift apart.
    """
    from .practical_lease_backend import _mark_pause
    return _mark_pause(batch_sql)


def _observed_tables(driver):
    rows = driver._sql(
        ['SELECT table_name AS observed_table FROM information_schema.tables '
         'WHERE table_schema = DATABASE();'], readback=True)
    return [row.get('observed_table') for row in rows if isinstance(row, dict)]


def _decode_rows(raw):
    """Bounded decode of the pinned JSON row packets."""
    if not isinstance(raw, bytes) or len(raw) > DRIVER_CAPTURE_BYTES:
        raise ValueError('E_HARNESS_CAPTURE: bounded capture exceeded or unreadable')
    text = raw.decode('utf-8', 'strict')
    decoder = json.JSONDecoder(object_pairs_hook=_pairs)
    cursor, sets = 0, []
    while cursor < len(text):
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor == len(text):
            break
        value, cursor = decoder.raw_decode(text, cursor)
        if value == {}:
            continue
        if not isinstance(value, dict) or set(value) != {'rows'} or not isinstance(value['rows'], list):
            raise ValueError('E_HARNESS_RESULT_SHAPE: unexpected result packet')
        sets.append(value['rows'])
    if len(sets) != 1:
        raise ValueError('E_HARNESS_RESULT_SETS: ambiguous result sets')
    return sets[0]


def _pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ValueError('E_HARNESS_RESULT_JSON: duplicate key')
        out[key] = value
    return out


def _literal(value):
    """Quote one identifier for harness SQL. No caller SQL reaches here."""
    if not isinstance(value, str) or not value or len(value) > 512 or '\x00' in value:
        raise ValueError('E_HARNESS_LITERAL: identifier is unusable')
    return "'" + value.replace('\\', '\\\\').replace("'", "''") + "'"


def _pinned(value):
    """Render an observed native DATETIME in the pinned-second form."""
    if not isinstance(value, str):
        raise ValueError('E_HARNESS_TIMESTAMP: observed timestamp is unusable')
    text = value.strip()
    return text if '.' in text else text + '.000000'


def _deadline_from(observed, seconds):
    """A pinned-second UTC deadline derived from the database clock sample."""
    stamp = str(observed).replace('T', ' ').split('.')[0]
    moment = datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S')
    later = moment + timedelta(seconds=seconds)
    return later.strftime('%Y-%m-%d %H:%M:%S.000000')


def _json_field(value):
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


_PROTECTED_MARKERS = ('E_MI2_AUTH', 'E_MI2_LEASE_MISMATCH', 'E_PRACTICAL_', 'E_MI2_ISSUE_CARDINALITY',
                      'E_MI2_RECEIPT_CARDINALITY', 'E_MI2_TOMB_CARDINALITY', 'E_MI2_CURRENT_GRANT_CARDINALITY',
                      'E_MI2_TOKEN_CARDINALITY', 'E_MI2_GRANT_CARDINALITY', 'E_MI2_LEASE_CARDINALITY',
                      'E_MI2_HISTORY_CARDINALITY', 'E_MI2_SQLSTATEMENT')


def _protected_refusal_source(exc):
    """Attribute a refusal to a fixed component, never by guessing."""
    text = '%s %s' % (type(exc).__name__, exc)
    if any(marker in text for marker in _PROTECTED_MARKERS):
        return 'PROTECTED_ASSERT'
    return 'TRANSPORT'


def _open_cm_journal(path, work_item_id):
    """Open the existing companion journal and register this work item.

    The journal is the real companion ledger, not a harness reimplementation:
    reservation, exactly-once dispatch consumption and the APPLIED/UNKNOWN
    terminal all come from `complete_read_v2.ledger`.
    """
    from complete_read_v2 import ledger
    path.parent.mkdir(parents=True, exist_ok=True)
    db = ledger.connect(path)
    ledger.create_work_item(db, work_item_id, 'task-' + work_item_id, 'PRACTICAL-RACE-HARNESS')
    ledger.coordination_put(db, work_item_id, {'registered': True})
    return db
