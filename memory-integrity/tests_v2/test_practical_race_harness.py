"""Offline tests for the lease race controller, verifier and live driver.

Nothing here starts a server, runs Dolt, or proves native behavior. These
tests prove the harness: that the known integrated false passes are rejected
through the real ``run_race`` entrypoint, that the orchestration drives every
arm, that the live driver builds bounded correct transports, and that missing
or unverifiable evidence is never a pass.

The implementation, its mocks and these tests are correlated evidence. They
are not independent native proof.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT.parent / 'claude-mon/scripts'))

from hybrid_bridge import practical_race_controller as controller
from hybrid_bridge import practical_race_verify as verify
from hybrid_bridge.practical_lease_backend import LeaseDeliveryUnknown

COMMIT = '3ea23556fd336ba64a3ebcf6b4fc169e71051d11'
MANIFEST = 'a' * 64
CONTROLLER_SHA = 'b' * 64
VERIFIER_SHA = 'c' * 64
DOLT_SHA = 'd' * 64
NODE = 'practical-approved-scratch-only'
NAMESPACE = 'store-1'
TASK = 'mipx-1'
ALICE = 'alice'
BOB = 'bob'
GRANT_OLD = 'grant-1'
GRANT_NEW = 'grant-2'
OP_STALE = 'op-1'
OP_WIN = 'op-reassign-1'
OP_POSITIVE = 'op-positive'
GRANTED_AT = '2026-10-14 10:00:00.000000'
HEARTBEAT_BEFORE = '2026-10-14 10:00:00.000000'
EXPIRES = '2026-10-14 10:05:00.000000'
AUTH = '2026-10-14 10:00:01.500000'
HEARTBEAT_AFTER = '2026-10-14 10:00:01.000000'
BARRIER_AUTH = '2026-10-14 10:00:01.100000'
BARRIER_TRANSFER = '2026-10-14 10:00:02.100000'
BARRIER_RESUME = '2026-10-14 10:00:03.100000'
TOKEN_BEFORE = -7
TOKEN_AFTER = 812
TITLE_OLD = 'old title'
TITLE_WIN = 'bob takes the task'
TITLE_STALE = 'safe title'
RUN = 'race-0123456789abcdef'

TABLES = ('issues', 'leases', 'grants', 'grant_history', 'current_grants',
          'metadata', 'token_history', 'operations')


def metadata_row():
    return {'store_incarnation': NAMESPACE, 'namespace_key': 'identity',
            'selection_digest': 'e' * 64, 'native_node_id': NODE,
            'selected_database': 'mipx', 'selected_main_branch': 'main'}


def _state(*, owner, title, token, grant_id, live_grant, holder, heartbeat,
           prior_tombstoned, history=(), tokens=(), operations=()):
    grants = []
    if prior_tombstoned:
        grants.append({'store_incarnation': NAMESPACE, 'grant_id': GRANT_OLD, 'task_id': TASK,
                       'actor': ALICE, 'status': 'CURRENT', 'issue_revision': TOKEN_BEFORE,
                       'tombstoned': 1, 'fixed_deadline_utc': EXPIRES, 'lease_node': NODE, 'lease_granted_at': GRANTED_AT,
                       'lease_expiry': EXPIRES, 'lease_heartbeat': HEARTBEAT_BEFORE})
    grants.append({'store_incarnation': NAMESPACE, 'grant_id': grant_id, 'task_id': TASK,
                   'actor': owner, 'status': 'GRANTED', 'issue_revision': token,
                   'tombstoned': 0, 'fixed_deadline_utc': EXPIRES, 'lease_node': NODE, 'lease_granted_at': GRANTED_AT,
                   'lease_expiry': EXPIRES, 'lease_heartbeat': heartbeat})
    return {
        'issues': [{'id': TASK, 'assignee': owner, 'title': title, 'status': 'in_progress',
                    'row_lock': token, 'ephemeral': 0}],
        'leases': [{'issue_id': TASK, 'holder': holder, 'granted_node': NODE,
                    'granted_at': GRANTED_AT, 'lease_expires_at': EXPIRES,
                    'heartbeat_at': heartbeat}],
        'grants': grants,
        'grant_history': list(history),
        'current_grants': [{'store_incarnation': NAMESPACE, 'task_id': TASK,
                            'grant_id': grant_id, 'current_revision': token}],
        'metadata': [metadata_row()],
        'token_history': list(tokens),
        'operations': list(operations),
    }


def state_before():
    """S0: Alice holds the live lease under her own grant."""
    state = _state(owner=ALICE, title=TITLE_OLD, token=TOKEN_BEFORE, grant_id=GRANT_OLD,
                  live_grant=GRANT_OLD, holder=ALICE, heartbeat=HEARTBEAT_BEFORE,
                  prior_tombstoned=False)
    state['grants'][0]['status'] = 'CURRENT'  # Real initial-claim producer.
    return state


def state_after_transfer():
    """S1: the legitimate transfer is committed and observed."""
    state = _state(owner=BOB, title=TITLE_WIN, token=TOKEN_AFTER, grant_id=GRANT_NEW,
                  live_grant=GRANT_NEW, holder=BOB, heartbeat=HEARTBEAT_AFTER,
                  prior_tombstoned=True)
    # A committed transfer has already emitted these records at S1.
    state['grant_history'] = [
        {'store_incarnation': NAMESPACE, 'grant_id': GRANT_OLD, 'event_kind': 'TOMBSTONED', 'event_utc': AUTH},
        {'store_incarnation': NAMESPACE, 'grant_id': GRANT_NEW, 'event_kind': 'MINTED', 'event_utc': AUTH}]
    state['token_history'] = [{'store_incarnation': NAMESPACE, 'row_token': TOKEN_AFTER, 'operation_id': OP_WIN}]
    state['operations'] = [{'store_incarnation': NAMESPACE, 'operation_id': OP_WIN,
                            'command_digest': 'f' * 64, 'authorization_time': AUTH,
                            'resulting_row_lock': TOKEN_AFTER}]
    return state


def state_final():
    """S2: fresh readback after the stale operation finished with no effect."""
    final = state_after_transfer()
    final['grant_history'] = [
        {'store_incarnation': NAMESPACE, 'grant_id': GRANT_OLD, 'event_kind': 'TOMBSTONED',
         'event_utc': AUTH},
        {'store_incarnation': NAMESPACE, 'grant_id': GRANT_NEW, 'event_kind': 'MINTED',
         'event_utc': AUTH},
    ]
    final['token_history'] = [{'store_incarnation': NAMESPACE, 'row_token': TOKEN_AFTER,
                               'operation_id': OP_WIN}]
    final['operations'] = [{'store_incarnation': NAMESPACE, 'operation_id': OP_WIN,
                            'command_digest': 'f' * 64, 'authorization_time': AUTH,
                            'resulting_row_lock': TOKEN_AFTER}]
    return final


def clean_evidence():
    """A complete, internally consistent evidence set: zero reasons."""
    return {
        'schema_version': verify.EVIDENCE_SCHEMA_VERSION,
        'run_id': RUN,
        'source': {'commit': COMMIT, 'working_tree': 'DIRTY',
                   'source_manifest_sha256': MANIFEST,
                   'controller_sha256': CONTROLLER_SHA, 'verifier_sha256': VERIFIER_SHA},
        'runtime': {'engine': controller.ENGINE_SYNTHETIC,
                    'evidence_class': controller.EVIDENCE_CLASS_SYNTHETIC,
                    'dolt_sha256': DOLT_SHA, 'expected_dolt_sha256': DOLT_SHA},
        'store': {'observed': True, 'verification': 'QUERY_OBSERVED', 'database': 'mipx',
                  'branch': 'main', 'namespace': NAMESPACE, 'node': NODE,
                  'schema_tables': sorted(verify.REQUIRED_PHYSICAL_TABLES)},
        'identities': {'task_id': TASK, 'stale_actor': ALICE, 'winner': BOB,
                       'stale_grant_id': GRANT_OLD, 'winner_grant_id': GRANT_NEW,
                       'expected_title': TITLE_WIN,
                       'stale_operation_ids': [OP_STALE], 'winner_operation_ids': [OP_WIN]},
        'barrier': {'kind': controller.BARRIER_KIND, 'run_id': RUN, 'operation_id': OP_STALE,
                    'session_id': '4242', 'observed_by': controller.BARRIER_OBSERVED_BY,
                    'authorization_time': BARRIER_AUTH,
                    'transfer_committed_at': BARRIER_TRANSFER,
                    'resumed_at': BARRIER_RESUME, 'unsupported': False},
        'observations': {'before': state_before(), 'after_transfer': state_after_transfer(),
                         'final': state_final()},
        'operations': {OP_WIN: {'store_incarnation': NAMESPACE, 'command_digest': 'f' * 64,
                                'authorization_time': AUTH, 'resulting_row_lock': TOKEN_AFTER,
                                'result': verify.BACKEND_APPLIED}},
        'cm': {'history': {OP_STALE: [verify.CM_INTENT, verify.CM_DISPATCHED, verify.CM_UNKNOWN],
                           OP_WIN: [verify.CM_INTENT, verify.CM_DISPATCHED,
                                    verify.CM_UNKNOWN, verify.CM_APPLIED]},
               'dispatch_counts': {OP_STALE: 1, OP_WIN: 1}},
        'controls': {
            'positive': {'executed': True, 'applied': True, 'fence_refused': False},
            'disabled': {'executed': True, 'preserved_transfer': True,
                         'unrelated_conflict_absent': True, 'unsafe_effect_observed': True,
                         'disabled_components': list(controller.disabled_fence_components())},
        },
        'refusal': {'by': 'fence', 'code': 'LeaseDeliveryUnknown'},
    }


class ScriptedDriver:
    """Offline stand-in for the live driver.

    It implements the whole phase protocol the orchestrator drives and records
    the exact call order. Every phase result can be overridden so a specific
    defect can be injected at the seam the orchestrator actually uses.
    """

    PROTOCOL = ('preflight', 'start_server', 'apply_ddl', 'bootstrap_namespace',
                'register_selection', 'store_identity', 'seed', 'start_alice',
                'wait_barrier', 'run_transfer', 'observed_clock', 'observe_transfer',
                'resume_alice', 'fresh_readback', 'operation_records', 'cm_observations',
                'positive_control', 'disabled_comparison', 'stop_alice', 'stop_server')

    def __init__(self, **overrides):
        self.calls = []
        self.overrides = overrides
        self.evidence = clean_evidence()
        self.alice = {'process': None, 'session': '4242'}

    def _record(self, name, result):
        self.calls.append(name)
        if name in self.overrides:
            value = self.overrides[name]
            if isinstance(value, BaseException):
                raise value
            if callable(value):
                return value()
            return value
        return result

    def preflight(self):
        return self._record('preflight', {
            'run_id': RUN, 'structural_only': True, 'dolt_sha256': DOLT_SHA,
            'expected_dolt_sha256': DOLT_SHA, 'source_commit': COMMIT, 'working_tree': 'DIRTY'})

    def start_server(self):
        return self._record('start_server', {'pid': 4242, 'owned': True})

    def store_identity(self):
        return self._record('store_identity', dict(self.evidence['store']))

    def apply_ddl(self, statements):
        assert statements, 'setup DDL must not be empty'
        return self._record('apply_ddl', None)

    def bootstrap_namespace(self):
        return self._record('bootstrap_namespace', None)

    def register_selection(self):
        return self._record('register_selection', None)

    def seed(self, seed_spec):
        return self._record('seed', self.evidence['observations']['before'])

    def start_alice(self, batch_sql):
        assert 'DO SLEEP' in batch_sql, 'alice arm must hold an observed barrier'
        return self._record('start_alice', self.alice)

    def wait_barrier(self, handle, timeout):
        return self._record('wait_barrier', dict(self.evidence['barrier']))

    def run_transfer(self, batch_sql):
        assert 'UPDATE leases SET holder' in batch_sql
        return self._record('run_transfer', {'committed': True, 'operation_id': OP_WIN})

    def observed_clock(self):
        return self._record('observed_clock', BARRIER_TRANSFER)

    def observe_transfer(self, phase):
        return self._record('observe_transfer', self.evidence['observations']['after_transfer'])

    def resume_alice(self, handle):
        # Scripted verifier fixture only: the attributed refusal is supplied
        # as a test premise. The live driver cannot establish this cause from
        # UNKNOWN plus current staleness. This is not full-sequence evidence.
        return self._record('resume_alice', {'outcome': 'UNKNOWN',
                                             'code': 'E_MI2_PREDICATE_NO_LONGER_HOLDS',
                                             'authority_readable': True,
                                             'predicate_refused': True,
                                             'refusal': dict(self.evidence['refusal']),
                                             'resumed_at': BARRIER_RESUME})

    def fresh_readback(self, queries):
        assert queries, 'readback queries must not be empty'
        return self._record('fresh_readback', self.evidence['observations']['final'])

    def operation_records(self):
        return self._record('operation_records', dict(self.evidence['operations']))

    def cm_observations(self):
        return self._record('cm_observations', dict(self.evidence['cm']))

    def positive_control(self):
        return self._record('positive_control', dict(self.evidence['controls']['positive']))

    def disabled_comparison(self):
        return self._record('disabled_comparison', dict(self.evidence['controls']['disabled']))

    def stop_server(self):
        return self._record('stop_server', True)

    def stop_alice(self):
        return self._record('stop_alice', True)


def build_schedule(**kwargs):
    from tests_v2.test_practical_lease_contract import packet, reassign_packet
    return controller.build_race_schedule(
        engine=controller.ENGINE_SYNTHETIC,
        selection={'scratch_root': 'C:/scratch/x', 'dolt_executable': 'C:/scratch/x/dolt.exe',
                   'dolt_sha256': '0' * 64, 'host': '127.0.0.1', 'port': 50001,
                   'database': 'mipx', 'main_branch': 'main', 'incarnation': NAMESPACE,
                   'native_node_id': NODE,
                   'candidate_route': 'APPROVED_SCRATCH_PRACTICAL_CONTRACT'},
        alice_title_packet=packet(), bob_reassign_packet=reassign_packet(),
        port=50001, database='mipx', pause_seconds=20,
        source_commit=COMMIT, working_tree='DIRTY', **kwargs)


def codes(result):
    return {reason['code'] for reason in result['reasons']}


class ScheduleTests(unittest.TestCase):
    def test_build_schedule_contains_all_phases_and_barrier(self):
        schedule = build_schedule()
        for phase in ('setup', 'seed', 'alice_arm', 'bob_arm', 'readback', 'controls',
                      'disabled_arm'):
            self.assertIn(phase, schedule['phases'])
        self.assertIn('DO SLEEP(20)', schedule['phases']['alice_arm']['batch'])
        self.assertIn('UPDATE leases SET holder', schedule['phases']['bob_arm']['batch'])
        self.assertEqual(schedule['engine'], controller.ENGINE_SYNTHETIC)
        self.assertTrue(schedule['phases']['disabled_arm']['harness_only'])
        self.assertEqual(schedule['identities']['stale_grant_id'], GRANT_OLD)
        self.assertEqual(schedule['identities']['winner_grant_id'], GRANT_NEW)
        self.assertEqual(schedule['identities']['expected_title'], TITLE_WIN)

    def test_synthetic_fixture_covers_every_referenced_table(self):
        schedule = build_schedule()
        ddl = ' '.join(schedule['phases']['setup']['ddl'])
        # The generated authority predicates join a dependencies table; a
        # synthetic fixture without it cannot execute the real SQL at all.
        self.assertIn('FROM dependencies AS d', schedule['phases']['bob_arm']['batch'])
        for table in controller.REQUIRED_SYNTHETIC_TABLES:
            self.assertIn('CREATE TABLE IF NOT EXISTS ' + table, ddl)

    def test_disabled_comparison_names_components_and_preserves_the_transfer(self):
        schedule = build_schedule()
        arm = schedule['phases']['disabled_arm']
        self.assertTrue(arm['harness_only'])
        self.assertTrue(arm['preserves_transfer'])
        self.assertTrue(arm['disabled_components'])
        self.assertNotIn('E_MI2_AUTH', arm['batch'])
        # There must be no production switch that turns the fence off.
        source = Path(controller.__file__).read_text(encoding='utf-8')
        self.assertNotIn('disable_fence', source)
        self.assertNotIn('fence_enabled=False', source)

    def test_barrier_marker_is_attached_only_to_the_bounded_pause(self):
        schedule = build_schedule()
        marked = controller._mark_barrier(schedule['phases']['alice_arm']['batch'])
        self.assertIn(controller.BARRIER_COMMENT, marked)
        self.assertIn('DO SLEEP(20)', marked)
        self.assertEqual(marked.count(controller.BARRIER_COMMENT), 1)
        with self.assertRaises(LeaseDeliveryUnknown):
            controller._mark_barrier('SELECT 1;')


class VerifierBaselineTests(unittest.TestCase):
    def test_complete_consistent_evidence_is_the_only_pass(self):
        result = verify.judge_evidence(clean_evidence())
        self.assertEqual(result['verdict'], verify.PASSED, result['reasons'])
        self.assertEqual(result['reasons'], [])

    def test_single_canonical_verdict_path_is_the_only_scored_entry(self):
        # The controller must reach a verdict through judge_evidence alone. A
        # second, weaker scorer in the controller is exactly the defect that
        # let all five false passes through before.
        source = Path(controller.__file__).read_text(encoding='utf-8')
        self.assertEqual(source.count('race_verify.judge_evidence'), 1)
        self.assertNotIn('_judge_predicates', source)
        self.assertNotIn('verify_winner_predicates', source)
        exported = [name for name in dir(verify) if name.startswith('judge_')]
        self.assertEqual(exported, ['judge_evidence'])

    def test_reason_codes_carry_explicit_severity_not_english_prefixes(self):
        for name, severity in verify.REASON_SEVERITY.items():
            reason = verify._reason(name, 'detail')
            self.assertEqual(reason['severity'], severity)
            self.assertEqual(reason['code'], name)
        with self.assertRaises(KeyError):
            verify._reason('NOT_A_REGISTERED_CODE', 'detail')


class FalsePassCaseTests(unittest.TestCase):
    """The five integrated false passes, each through the real run_race()."""

    def _run(self, **overrides):
        return controller.run_race(build_schedule(), driver=ScriptedDriver(**overrides))

    def test_case_a_none_barrier_is_inconclusive_through_run_race(self):
        result = self._run(wait_barrier=None)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('BARRIER_INVALID', codes(result))
        self.assertTrue(result['stopped'])

    def test_case_b_stale_backend_success_record_with_unknown_journal_fails(self):
        driver = ScriptedDriver()
        driver.evidence['operations'][OP_STALE] = {
            'store_incarnation': NAMESPACE, 'command_digest': '2' * 64,
            'authorization_time': AUTH, 'resulting_row_lock': TOKEN_AFTER + 2,
            'result': verify.CM_APPLIED}
        result = controller.run_race(build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('STALE_BACKEND_SUCCESS_RECORD', codes(result))

    def test_case_c_extended_expiry_wrong_actor_and_grant_revision_disagreement_fails(self):
        driver = ScriptedDriver()

        def final_with_defects():
            final = state_final()
            final['leases'][0]['lease_expires_at'] = '2026-10-14 10:30:00.000000'
            final['grants'][1]['actor'] = 'mallory'
            final['grants'][1]['issue_revision'] = 999
            return final

        result = controller.run_race(build_schedule(),
                                     driver=ScriptedDriver(fresh_readback=final_with_defects))
        self.assertEqual(result['verdict'], verify.FAILED)
        found = codes(result)
        self.assertIn('EXPIRY_MOVED', found)
        self.assertIn('GRANT_ACTOR_MISMATCH', found)
        self.assertIn('GRANT_REVISION_MISMATCH', found)
        self.assertTrue(result['stopped'])

    def test_case_d_unverified_beads_marker_only_is_inconclusive(self):
        schedule = build_schedule()
        schedule['engine'] = controller.ENGINE_BEADS
        schedule['evidence_class'] = controller.EVIDENCE_CLASS_BEADS
        driver = ScriptedDriver()
        # A marker path and nothing observed from the store itself.
        driver.overrides['store_identity'] = {
            'observed': True, 'verification': 'UNVERIFIED_MARKER_ONLY', 'database': 'mipx',
            'branch': 'main', 'namespace': NAMESPACE, 'node': NODE,
            'schema_tables': list(verify.TABLE_KEYS),
            'beads': {'observed': False, 'version': None, 'schema_tables': []}}
        result = controller.run_race(schedule, driver=driver)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('IDENTITY_UNVERIFIED', codes(result))

    def test_case_e_controls_scheduled_but_not_executed_is_inconclusive(self):
        driver = ScriptedDriver()
        driver.overrides['positive_control'] = {'executed': False}
        driver.overrides['disabled_comparison'] = {'executed': False}
        result = controller.run_race(build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('CONTROL_NOT_EXECUTED', codes(result))
        # Both phases are scheduled, so their absence must be visible.
        self.assertIn('positive_control', driver.calls)
        self.assertIn('disabled_comparison', driver.calls)
        self.assertTrue(result['stopped'])


class RetainedNegativeTests(unittest.TestCase):
    """The negative cases retained from the earlier harness, still non-passing."""

    def _verdict(self, mutate=None, **overrides):
        evidence = clean_evidence()
        if mutate is not None:
            mutate(evidence)
        driver = ScriptedDriver(**overrides)
        driver.evidence = evidence
        return controller.run_race(build_schedule(), driver=driver)

    def test_empty_evidence_is_never_a_pass(self):
        result = verify.judge_evidence({})
        self.assertNotEqual(result['verdict'], verify.PASSED)
        self.assertIn('EVIDENCE_MISSING', codes(result))

    def test_absent_journal_observation_is_a_reason(self):
        result = self._verdict(lambda e: e['cm']['history'].pop(OP_STALE))
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('EVIDENCE_MISSING', codes(result))

    def test_absent_dispatch_observation_is_a_reason(self):
        def drop(evidence):
            evidence['cm']['dispatch_counts'].pop(OP_STALE)
        result = self._verdict(drop)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('DISPATCH_UNOBSERVED', codes(result))

    def test_title_only_stale_change_with_unchanged_ownership_fails(self):
        # Ownership fields are untouched; only the title is stale. Full-row
        # comparison against the winner's committed title is what catches it.
        def stale_title(evidence):
            final = state_final()
            final['issues'][0]['title'] = TITLE_STALE
            evidence['observations']['final'] = final
        result = self._verdict(stale_title)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('STALE_COMMITTED_EFFECT', codes(result))

    def test_missing_rows_or_tables_fail(self):
        def drop_table(evidence):
            evidence['observations']['final'].pop('token_history')
        result = self._verdict(drop_table)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('OBSERVATION_INCOMPLETE', codes(result))

        def drop_row(evidence):
            evidence['observations']['final']['leases'] = []
        result = self._verdict(drop_row)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)

    def test_disappeared_grant_row_fails(self):
        def remove_prior(evidence):
            final = state_final()
            final['grants'] = [row for row in final['grants'] if row['grant_id'] != GRANT_OLD]
            evidence['observations']['final'] = final
        result = self._verdict(remove_prior)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('PRIOR_GRANT_NOT_TOMBSTONED', codes(result))

    def test_duplicate_dispatch_fails(self):
        def twice(evidence):
            evidence['cm']['dispatch_counts'][OP_STALE] = 2
        result = self._verdict(twice)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('DUPLICATE_DISPATCH', codes(result))

    def test_unrelated_refusal_is_inconclusive_not_proof(self):
        result = self._verdict(resume_alice={'outcome': 'UNKNOWN', 'code': 'E_X',
                                             'authority_readable': True,
                                             'predicate_refused': False,
                                             'resumed_at': BARRIER_RESUME})
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('REFUSAL_UNRELATED', codes(result))

    def test_unknown_refusal_reason_never_falls_through_to_passed(self):
        result = self._verdict(resume_alice={'outcome': 'SOMETHING_NEW', 'code': 'E_Y',
                                             'authority_readable': True,
                                             'predicate_refused': False,
                                             'resumed_at': BARRIER_RESUME})
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('REFUSAL_UNKNOWN', codes(result))
        for refused in (True, False):
            mapped = controller.stale_refusal_attribution(
                outcome='UNKNOWN', predicate_refused=refused, authority_readable=True)
            self.assertEqual(mapped['by'], None if refused else 'other')
        applied = controller.stale_refusal_attribution(
            outcome='APPLIED', predicate_refused=False, authority_readable=True)
        self.assertEqual(applied['by'], None)
        unknown = controller.stale_refusal_attribution(
            outcome='SOMETHING_ELSE', predicate_refused=True, authority_readable=True)
        self.assertNotEqual(unknown['by'], 'fence')

    def test_observed_unsafe_effect_fails_even_when_evidence_is_incomplete(self):
        def both(evidence):
            evidence['observations']['final'].pop('token_history')
            final = state_final()
            final['issues'][0]['title'] = TITLE_STALE
            evidence['observations']['final']['issues'] = final['issues']
        result = self._verdict(both)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('STALE_COMMITTED_EFFECT', codes(result))


class EvidenceSchemaTests(unittest.TestCase):
    """Malformed, duplicated and contradictory evidence is rejected."""

    def test_wrong_schema_version_is_rejected(self):
        evidence = clean_evidence()
        evidence['schema_version'] = 99
        self.assertIn('EVIDENCE_SCHEMA_VERSION', codes(verify.judge_evidence(evidence)))

    def test_malformed_types_are_rejected(self):
        for mutate in (
            lambda e: e.__setitem__('run_id', 17),
            lambda e: e.__setitem__('source', 'not a mapping'),
            lambda e: e['identities'].__setitem__('stale_operation_ids', 'op-1'),
            lambda e: e.__setitem__('observations', []),
            lambda e: e['store'].__setitem__('observed', 'yes'),
            lambda e: e['barrier'].__setitem__('session_id', True),
        ):
            evidence = clean_evidence()
            mutate(evidence)
            self.assertNotEqual(verify.judge_evidence(evidence)['verdict'], verify.PASSED)

    def test_duplicate_row_identity_is_not_silently_overwritten(self):
        evidence = clean_evidence()
        final = state_final()
        # The same composite identity appears twice. Dictionary construction
        # must not collapse it, and the ambiguity must never be a pass.
        final['grants'].append(dict(final['grants'][1], actor=ALICE))
        evidence['observations']['final'] = final
        result = verify.judge_evidence(evidence)
        self.assertIn('DUPLICATE_ROW_IDENTITY', codes(result))
        self.assertNotEqual(result['verdict'], verify.PASSED)

    def test_a_second_live_grant_is_caught_by_the_active_grant_set(self):
        # A duplicate identity is ambiguous; a *distinct* extra live grant is a
        # real defect and must fail rather than hide behind the index.
        evidence = clean_evidence()
        final = state_final()
        final['grants'].append({'store_incarnation': NAMESPACE, 'grant_id': 'grant-rogue',
                                'task_id': TASK, 'actor': ALICE, 'status': 'CURRENT',
                                'issue_revision': TOKEN_BEFORE, 'tombstoned': 0,
                                'lease_node': NODE, 'lease_granted_at': GRANTED_AT,
                                'lease_expiry': EXPIRES, 'lease_heartbeat': HEARTBEAT_BEFORE})
        evidence['observations']['final'] = final
        result = verify.judge_evidence(evidence)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('ACTIVE_GRANT_SET_WRONG', codes(result))

    def test_per_table_identities_include_issue_id_and_composite_keys(self):
        self.assertEqual(verify.TABLE_KEYS['leases'], ('issue_id',))
        self.assertEqual(verify.TABLE_KEYS['grants'], ('store_incarnation', 'grant_id'))
        self.assertEqual(verify.TABLE_KEYS['token_history'], ('store_incarnation', 'row_token'))
        self.assertEqual(verify.TABLE_KEYS['grant_history'],
                         ('store_incarnation', 'grant_id', 'event_kind', 'event_utc'))

    def test_missing_required_section_is_rejected(self):
        evidence = clean_evidence()
        evidence.pop('controls')
        self.assertIn('EVIDENCE_MISSING', codes(verify.judge_evidence(evidence)))

    def test_journal_claiming_applied_without_backend_record_is_a_false_accept(self):
        evidence = clean_evidence()
        evidence['cm']['history'][OP_STALE] = [verify.CM_INTENT, verify.CM_DISPATCHED,
                                               verify.CM_APPLIED]
        result = verify.judge_evidence(evidence)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('STALE_SUCCESS_RECEIPT', codes(result))

    def test_stale_operation_never_dispatched_is_not_fencing_proof(self):
        evidence = clean_evidence()
        evidence['cm']['history'][OP_STALE] = [verify.CM_INTENT]
        evidence['cm']['dispatch_counts'][OP_STALE] = 0
        result = verify.judge_evidence(evidence)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('DISPATCH_UNOBSERVED', codes(result))

    def test_runtime_pin_mismatch_is_not_a_pass(self):
        evidence = clean_evidence()
        evidence['runtime']['dolt_sha256'] = '9' * 64
        self.assertIn('RUNTIME_PIN_MISMATCH', codes(verify.judge_evidence(evidence)))

    def test_synthetic_engine_cannot_claim_real_beads_evidence(self):
        evidence = clean_evidence()
        evidence['runtime']['evidence_class'] = controller.EVIDENCE_CLASS_BEADS
        result = verify.judge_evidence(evidence)
        self.assertIn('EVIDENCE_SCHEMA_INVALID', codes(result))

    def test_ineffective_disabled_control_is_inconclusive_not_a_weakened_fence(self):
        evidence = clean_evidence()
        evidence['controls']['disabled']['unsafe_effect_observed'] = False
        result = verify.judge_evidence(evidence)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('CONTROL_INEFFECTIVE', codes(result))

    def test_positive_control_that_was_refused_is_not_a_working_fence(self):
        evidence = clean_evidence()
        evidence['controls']['positive']['fence_refused'] = True
        result = verify.judge_evidence(evidence)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('CONTROL_INEFFECTIVE', codes(result))

    def test_token_freshness_and_binding_are_checked_not_predicted(self):
        evidence = clean_evidence()
        evidence['observations']['final']['token_history'][0]['operation_id'] = OP_STALE
        self.assertIn('TOKEN_NOT_BOUND', codes(verify.judge_evidence(evidence)))

    def test_authorization_may_finish_saving_after_the_original_deadline(self):
        # The adopted contract: authorization must precede the original
        # deadline, but the save may complete later. That must not be
        # re-tightened into an expiry-before-save rule.
        evidence = clean_evidence()
        late = '2026-10-14 10:04:59.900000'
        # Both observations of the operation must agree, or the run is
        # contradictory rather than merely late.
        evidence['operations'][OP_WIN]['authorization_time'] = late
        final = state_final()
        final['operations'][0]['authorization_time'] = late
        final['leases'][0]['heartbeat_at'] = '2026-10-14 10:04:59.000000'
        final['grants'][1]['lease_heartbeat'] = '2026-10-14 10:04:59.000000'
        for row in final['grant_history']:
            row['event_utc'] = late
        evidence['observations']['final'] = final
        # S1 is also a committed observation of this same transfer.
        import copy
        evidence['observations']['after_transfer'] = copy.deepcopy(final)
        self.assertEqual(verify.judge_evidence(evidence)['verdict'], verify.PASSED,
                         verify.judge_evidence(evidence)['reasons'])

    def test_authorization_at_or_after_the_original_deadline_fails(self):
        evidence = clean_evidence()
        evidence['observations']['final']['operations'][0]['authorization_time'] = EXPIRES
        evidence['operations'][OP_WIN]['authorization_time'] = EXPIRES
        self.assertEqual(verify.judge_evidence(evidence)['verdict'], verify.FAILED)


class OrchestrationTests(unittest.TestCase):
    def test_orchestration_executes_enabled_positive_and_disabled_arms_in_order(self):
        driver = ScriptedDriver()
        result = controller.run_race(build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.PASSED, result['reasons'])
        order = [name for name in driver.calls]
        for name in ScriptedDriver.PROTOCOL:
            self.assertIn(name, order, name)
        enabled = order.index('resume_alice')
        self.assertLess(order.index('wait_barrier'), enabled)
        self.assertLess(order.index('run_transfer'), enabled)
        self.assertGreater(order.index('positive_control'), enabled)
        self.assertGreater(order.index('disabled_comparison'), order.index('positive_control'))
        self.assertEqual(order[-1], 'stop_server')
        self.assertTrue(result['stopped'])

    def test_legitimate_transfer_is_required_before_alice_resumes(self):
        driver = ScriptedDriver(run_transfer={'committed': False})
        result = controller.run_race(build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertNotIn('resume_alice', driver.calls)
        self.assertEqual(driver.calls[-1], 'stop_server')

    def test_unobserved_transfer_state_stops_the_run(self):
        driver = ScriptedDriver(observe_transfer={'issues': []})
        result = controller.run_race(build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('OBSERVATION_INCOMPLETE', codes(result))

    def test_store_identity_must_be_observed_before_the_race_mutates_anything(self):
        driver = ScriptedDriver(store_identity={'observed': False})
        result = controller.run_race(build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        # Schema, bootstrap and registration may precede identity on a fresh
        # store, but no task may be seeded or claimed without it.
        self.assertNotIn('seed', driver.calls)
        self.assertNotIn('start_alice', driver.calls)

    def test_preflight_must_be_structurally_observed(self):
        driver = ScriptedDriver(preflight={'structural_only': False})
        result = controller.run_race(build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertNotIn('start_server', driver.calls)

    def test_harness_failure_before_the_server_starts_never_stops(self):
        driver = ScriptedDriver(preflight=RuntimeError('boom'))
        result = controller.run_race(build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertFalse(result['stopped'])
        self.assertNotIn('start_server', driver.calls)

    def test_failed_stop_blocks_success_label_and_stays_visible(self):
        driver = ScriptedDriver(stop_server=False)
        result = controller.run_race(build_schedule(), driver=driver)
        self.assertFalse(result['stopped'])
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('HARNESS_ERROR', codes(result))

    def test_failed_stop_does_not_hide_an_observed_unsafe_effect(self):
        def stale_title(evidence):
            final = state_final()
            final['issues'][0]['title'] = TITLE_STALE
            evidence['observations']['final'] = final
        driver = ScriptedDriver(stop_server=False)
        driver.evidence = clean_evidence()
        stale_title(driver.evidence)
        result = controller.run_race(build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertFalse(result['stopped'])

    def test_failure_after_every_phase_still_stops_the_owned_server(self):
        for phase in ('seed', 'start_alice', 'wait_barrier', 'run_transfer',
                      'observe_transfer', 'resume_alice', 'fresh_readback',
                      'cm_observations', 'positive_control', 'disabled_comparison'):
            with self.subTest(phase=phase):
                driver = ScriptedDriver(**{phase: RuntimeError('boom')})
                result = controller.run_race(build_schedule(), driver=driver)
                self.assertNotEqual(result['verdict'], verify.PASSED)
                self.assertEqual(driver.calls[-1], 'stop_server')
                self.assertTrue(result['stopped'])

    def test_winner_requests_built_from_resulting_facts_not_fixture_packets(self):
        driver = controller._LiveDriver(build_schedule())
        driver.run_id = RUN
        # At transfer time Alice still holds the live lease, so her own
        # unchanged authority is the legitimate transferor basis. Bob is not
        # stealing the lease through an unguarded mutation.
        at_transfer = {'issue_id': TASK, 'holder': ALICE, 'granted_node': NODE,
                       'granted_at': GRANTED_AT, 'lease_expires_at': EXPIRES,
                       'heartbeat_at': HEARTBEAT_BEFORE, 'grant_id': GRANT_OLD,
                       'issue_row_lock': TOKEN_BEFORE}
        driver._current_authority = lambda: at_transfer
        transfer = driver._transfer_request_from_observed()
        self.assertEqual(transfer.actor, ALICE)
        self.assertEqual(transfer.target_actor, BOB)
        self.assertEqual(transfer.grant_id, GRANT_OLD)
        self.assertNotEqual(transfer.new_grant_id, GRANT_OLD)
        self.assertEqual(transfer.expected_row_lock, TOKEN_BEFORE)
        # Nothing is taken from the fixture packet's stale facts.
        self.assertEqual(transfer.lease_granted_at_utc, GRANTED_AT)
        self.assertEqual(transfer.lease_expires_at_utc, EXPIRES)

        # The winner's own follow-up must use the resulting facts, never the
        # original fixture packets.
        after_transfer = {'issue_id': TASK, 'holder': BOB, 'granted_node': NODE,
                          'granted_at': GRANTED_AT, 'lease_expires_at': EXPIRES,
                          'heartbeat_at': HEARTBEAT_AFTER, 'grant_id': GRANT_NEW,
                          'issue_row_lock': TOKEN_AFTER}
        driver._current_authority = lambda: after_transfer
        positive = driver._positive_request_from_observed()
        self.assertEqual(positive.expected_row_lock, TOKEN_AFTER)
        self.assertNotEqual(positive.expected_row_lock, TOKEN_BEFORE)
        self.assertEqual(positive.grant_id, GRANT_NEW)
        self.assertNotEqual(positive.grant_id, GRANT_OLD)
        self.assertEqual(positive.lease_heartbeat_at_utc, HEARTBEAT_AFTER)
        self.assertNotEqual(positive.operation_id, OP_STALE)

    def test_build_race_schedule_rejects_an_out_of_range_pause(self):
        from tests_v2.test_practical_lease_contract import packet, reassign_packet
        with self.assertRaisesRegex(ValueError, 'E_HARNESS_PAUSE'):
            controller.build_race_schedule(
                engine=controller.ENGINE_SYNTHETIC,
                selection=build_schedule()['requests']['selection'],
                alice_title_packet=packet(), bob_reassign_packet=reassign_packet(),
                port=50001, database='mipx', pause_seconds=0)


class BarrierTests(unittest.TestCase):
    def _verdict(self, barrier):
        evidence = clean_evidence()
        evidence['barrier'] = barrier
        return verify.judge_evidence(evidence)

    def test_valid_barrier_is_required_for_a_pass(self):
        self.assertEqual(verify.judge_evidence(clean_evidence())['verdict'], verify.PASSED)

    def test_none_or_empty_barrier_is_never_a_pass(self):
        for barrier in (None, {}, [], 'observed', True):
            with self.subTest(barrier=barrier):
                evidence = clean_evidence()
                evidence['barrier'] = barrier
                self.assertNotEqual(verify.judge_evidence(evidence)['verdict'], verify.PASSED)

    def test_caller_supplied_boolean_is_not_barrier_evidence(self):
        evidence = clean_evidence()
        evidence['barrier']['session_id'] = True
        self.assertIn('BARRIER_INVALID', codes(verify.judge_evidence(evidence)))

    def test_sleep_string_is_not_barrier_evidence(self):
        evidence = clean_evidence()
        evidence['barrier']['authorization_time'] = 'slept for 20 seconds'
        self.assertIn('BARRIER_INVALID', codes(verify.judge_evidence(evidence)))

    def test_barrier_must_bind_the_exact_run_and_operation(self):
        for key, value in (('run_id', 'race-other'), ('operation_id', 'op-other')):
            evidence = clean_evidence()
            evidence['barrier'][key] = value
            self.assertIn('BARRIER_INVALID', codes(verify.judge_evidence(evidence)))

    def test_barrier_ordering_must_be_authorization_then_transfer_then_resume(self):
        evidence = clean_evidence()
        # The transfer cannot have committed before the snapshot was reached.
        evidence['barrier']['transfer_committed_at'] = BARRIER_RESUME
        evidence['barrier']['resumed_at'] = BARRIER_TRANSFER
        result = verify.judge_evidence(evidence)
        self.assertIn('BARRIER_ORDERING_UNPROVEN', codes(result))

    def test_unsupported_synchronization_is_inconclusive(self):
        evidence = clean_evidence()
        evidence['barrier']['unsupported'] = True
        evidence['barrier']['authorization_time'] = None
        result = verify.judge_evidence(evidence)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('BARRIER_UNSUPPORTED_SYNC', codes(result))

    def test_unsupported_marker_must_be_a_boolean(self):
        evidence = clean_evidence()
        evidence['barrier']['unsupported'] = 'no'
        self.assertIn('BARRIER_INVALID', codes(verify.judge_evidence(evidence)))


class DatetimeAssumptionTests(unittest.TestCase):
    """The conversion rule is runtime-dependent and must be labeled so."""

    def test_datetime_truncation_assumption_is_not_a_universal_mysql_claim(self):
        source = Path(controller.__file__).read_text(encoding='utf-8')
        verifier = Path(verify.__file__).read_text(encoding='utf-8')
        combined = source + verifier
        self.assertIn('runtime-dependent assumption', verifier)
        self.assertNotIn('MySQL always truncates', combined)
        self.assertNotIn('universally truncates', combined)

    def test_fractional_second_boundaries_and_rollover(self):
        # (granted, expires, authorization, heartbeat, expected verdict, reason)
        cases = (
            ('2026-10-14 10:00:00.000000', '2026-10-14 10:05:00.000000',
             '2026-10-14 10:00:01.000000', '2026-10-14 10:00:01.000000',
             verify.PASSED, None),
            ('2026-10-14 10:00:00.000000', '2026-10-14 10:05:00.000000',
             '2026-10-14 10:00:01.999999', '2026-10-14 10:00:01.000000',
             verify.PASSED, None),
            ('2026-10-14 10:00:00.000000', '2026-10-14 10:05:00.000000',
             '2026-10-14 10:00:01.000001', '2026-10-14 10:00:01.000000',
             verify.PASSED, None),
            # A rounding runtime would produce this instead. It must fail, and
            # the enabled fence must not be relaxed to accommodate it.
            ('2026-10-14 10:00:00.000000', '2026-10-14 10:05:00.000000',
             '2026-10-14 10:00:01.600000', '2026-10-14 10:00:02.000000',
             verify.FAILED, 'HEARTBEAT_NOT_DERIVED'),
            # Minute rollover inside the lease window.
            ('2026-10-14 10:00:00.000000', '2026-10-14 10:05:00.000000',
             '2026-10-14 10:04:59.999999', '2026-10-14 10:04:59.000000',
             verify.PASSED, None),
            # Hour, day and year rollover, each with a consistent lease window.
            ('2026-10-14 23:59:59.000000', '2026-10-15 00:05:00.000000',
             '2026-10-14 23:59:59.999999', '2026-10-14 23:59:59.000000',
             verify.PASSED, None),
            ('2026-12-31 23:59:00.000000', '2027-01-01 00:05:00.000000',
             '2026-12-31 23:59:59.500000', '2026-12-31 23:59:59.000000',
             verify.PASSED, None),
            # The resulting heartbeat may never precede the original grant.
            ('2026-10-14 10:00:00.000000', '2026-10-14 10:05:00.000000',
             '2026-09-14 09:59:59.999999', '2026-09-14 09:59:59.000000',
             verify.FAILED, 'HEARTBEAT_NOT_DERIVED'),
        )
        for granted, expires, authorization, heartbeat, expected, reason in cases:
            with self.subTest(authorization=authorization):
                evidence = clean_evidence()
                evidence['operations'][OP_WIN]['authorization_time'] = authorization
                final = state_final()
                for observation in (evidence['observations']['before'],
                                    evidence['observations']['after_transfer'], final):
                    observation['leases'][0]['granted_at'] = granted
                    observation['leases'][0]['lease_expires_at'] = expires
                    observation['leases'][0]['heartbeat_at'] = (
                        granted if observation is not final else heartbeat)
                    for grant in observation['grants']:
                        grant['lease_granted_at'] = granted
                        grant['lease_expiry'] = expires
                        grant['fixed_deadline_utc'] = expires
                        if grant['grant_id'] == GRANT_NEW:
                            grant['lease_heartbeat'] = heartbeat
                final['operations'][0]['authorization_time'] = authorization
                for row in final['grant_history']:
                    row['event_utc'] = authorization
                evidence['observations']['final'] = final
                # S1 and S2 describe the same transfer authorization and
                # resulting lease heartbeat; later save time is separate.
                import copy
                evidence['observations']['after_transfer'] = copy.deepcopy(final)
                result = verify.judge_evidence(evidence)
                if expected is verify.PASSED:
                    self.assertEqual(result['verdict'], verify.PASSED, result['reasons'])
                else:
                    self.assertEqual(result['verdict'], expected, result['reasons'])
                    self.assertIn(reason, codes(result))

    def test_unreadable_timestamps_are_never_a_pass(self):
        for value in ('2026-10-14', 'not-a-time', 17, None, ''):
            with self.subTest(value=value):
                evidence = clean_evidence()
                evidence['observations']['final']['leases'][0]['heartbeat_at'] = value
                self.assertNotEqual(verify.judge_evidence(evidence)['verdict'], verify.PASSED)

    def test_heartbeat_must_not_precede_the_original_grant(self):
        evidence = clean_evidence()
        evidence['observations']['final']['leases'][0]['heartbeat_at'] = \
            '2026-10-14 09:59:59.000000'
        self.assertIn('HEARTBEAT_NOT_DERIVED', codes(verify.judge_evidence(evidence)))


class ConfirmationRefusalTests(unittest.TestCase):
    def test_run_schedule_refuses_without_explicit_confirmation(self):
        for value in (False, None, 0, '', 'true', 1):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'confirm_native_execution'):
                    controller.run_schedule({'phases': {}}, confirm_native_execution=value)

    def test_confirmation_refusal_happens_before_any_native_side_effect(self):
        created = []

        class Trap(controller._LiveDriver):
            def __init__(self, schedule):
                created.append(schedule)
                super().__init__(schedule)

        original = controller._LiveDriver
        controller._LiveDriver = Trap
        try:
            with self.assertRaisesRegex(ValueError, 'confirm_native_execution'):
                controller.run_schedule({'phases': {}}, confirm_native_execution=False)
        finally:
            controller._LiveDriver = original
        # No driver may even be constructed, let alone start a process.
        self.assertEqual(created, [])


# -- live driver, at the process boundary --------------------------------

class FakePopen:
    """Process-boundary stand-in. Records argv and owns its own lifecycle."""

    instances = []

    def __init__(self, argv, **kwargs):
        self.argv = list(argv)
        self.kwargs = kwargs
        self.pid = 9000 + len(FakePopen.instances)
        self.terminated = False
        self.killed = False
        self._returncode = None
        FakePopen.instances.append(self)

    def poll(self):
        return self._returncode

    def wait(self, timeout=None):
        if self._returncode is None and self.killed:
            self._returncode = -9
        return self._returncode

    def terminate(self):
        self.terminated = True
        self._returncode = 0

    def kill(self):
        self.killed = True
        self._returncode = -9


class StubbornPopen(FakePopen):
    """Ignores terminate, so a stop genuinely fails and must stay visible."""

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True


class StubRun:
    def __init__(self, stdout=b'{"rows": []}', returncode=0, stderr=b''):
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr


@contextlib.contextmanager
def patched_subprocess(module, *, run=None):
    """Replace only the harness module's subprocess reference, then restore."""
    calls = []
    holder = type('SubprocessStub', (), {
        'run': staticmethod(lambda argv, **kwargs: (calls.append(('run', argv, kwargs)),
                                                     run(argv, **kwargs))[1]),
        'Popen': staticmethod(lambda argv, **kwargs: (calls.append(('popen', argv, kwargs)),
                                                      FakePopen(argv, **kwargs))[1]),
        'DEVNULL': subprocess.DEVNULL,
        'STDOUT': subprocess.STDOUT,
        'PIPE': subprocess.PIPE,
        'CREATE_NO_WINDOW': getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    })
    original = module.subprocess
    module.subprocess = holder
    try:
        yield calls
    finally:
        module.subprocess = original


def rows_packet(*rows):
    return json.dumps({'rows': list(rows)}).encode('utf-8')


def live_driver(tmp, *, spawn=None, engine=controller.ENGINE_SYNTHETIC):
    schedule = build_schedule()
    schedule['engine'] = engine
    schedule['requests']['selection'] = dict(schedule['requests']['selection'],
                                             scratch_root=str(tmp))
    # A short shutdown window keeps the failing-stop test fast; the driver
    # default is what a real run uses.
    driver = controller._LiveDriver(schedule, spawn=spawn or FakePopen,
                                    stop_grace_seconds=0.05)
    driver._current_authority = AuthorityObservation()
    driver.run_id = RUN
    driver.log_dir = tmp / '.practical-race' / RUN
    driver.log_dir.mkdir(parents=True, exist_ok=True)
    return driver


class LiveDriverTransportTests(unittest.TestCase):
    def setUp(self):
        FakePopen.instances = []
        self.temp = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_live_driver_has_no_placeholder_methods(self):
        import inspect
        source = Path(controller.__file__).read_text(encoding='utf-8')
        self.assertNotIn('E_HARNESS_UNVERIFIED_DRIVER', source)
        self.assertNotIn('live execution needs a working host', source)
        driver = live_driver(self.tmp)
        for name in ('preflight', 'start_server', 'store_identity', 'apply_ddl',
                     'bootstrap_namespace', 'register_selection', 'seed', 'start_alice',
                     'wait_barrier', 'run_transfer', 'observe_transfer', 'resume_alice',
                     'read_state', 'fresh_readback', 'operation_records', 'cm_observations',
                     'positive_control', 'disabled_comparison', 'stop_server'):
            with self.subTest(method=name):
                body = inspect.getsource(getattr(driver, name))
                self.assertNotIn('UNVERIFIED_DRIVER', body)
                self.assertNotIn('needs a working host', body)
                # A placeholder body raises immediately and does nothing else.
                self.assertNotRegex(body.strip().split('\n')[-1].strip(),
                                    r'^raise\s+\w*Error\(', name)

    def test_server_argv_is_fixed_and_never_shell_interpreted(self):
        driver = live_driver(self.tmp)
        handle = driver.start_server()
        # start_server goes through the driver's own spawn seam, so the real
        # method's argv and keywords are what the fake process received.
        owned = FakePopen.instances[0]
        argv = owned.argv
        self.assertEqual(handle['pid'], owned.pid)
        self.assertTrue(argv[0].endswith('dolt.exe'))
        self.assertEqual(argv[1:], ['sql-server', '--host', '127.0.0.1',
                                    '--port', '50001', '--no-tls'])
        self.assertIs(owned.kwargs['shell'], False)
        self.assertEqual(owned.kwargs['stdin'], subprocess.DEVNULL)

    def test_partial_start_failure_is_visible_and_never_claims_a_handle(self):
        class Exploding(FakePopen):
            def __init__(self, argv, **kwargs):
                raise OSError('cannot start')

        driver = live_driver(self.tmp, spawn=Exploding)
        with self.assertRaises(OSError):
            driver.start_server()
        self.assertIsNone(driver.server_process)
        self.assertIsNone(driver.server_pid)

    def test_stop_terminates_only_the_process_it_owns_and_verifies_exit(self):
        driver = live_driver(self.tmp)
        with patched_subprocess(controller):
            driver.start_server()
        owned = driver.server_process
        self.assertTrue(driver.stop_server())
        self.assertTrue(owned.terminated)
        self.assertFalse(owned.killed)
        self.assertIsNone(driver.server_process)

    def test_stop_of_the_owned_server_is_visible_when_it_fails(self):
        driver = live_driver(self.tmp, spawn=StubbornPopen)
        with patched_subprocess(controller):
            driver.start_server()
        self.assertFalse(driver.stop_server())
        self.assertTrue(FakePopen.instances[0].killed)

    def test_owned_handles_only_never_terminates_by_name_or_port(self):
        source = Path(controller.__file__).read_text(encoding='utf-8')
        for forbidden in ('taskkill', 'Stop-Process', 'killall', 'pkill',
                          'netstat', 'Get-NetTCPConnection', '--port=0'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        # Cleanup goes through the retained handle only.
        driver = live_driver(self.tmp)
        with patched_subprocess(controller):
            driver.start_server()
            owned = driver.server_process
            driver.stop_server()
        self.assertIs(owned, FakePopen.instances[0])

    def test_sql_outside_the_harness_allowlist_is_refused(self):
        driver = live_driver(self.tmp)
        for statement in ('DROP TABLE issues;', 'SELECT 1; DELETE FROM issues;',
                          'UPDATE issues SET assignee = "alice";', ''):
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(ValueError, 'E_HARNESS_SQL'):
                    driver._sql([statement])

    def test_shell_metacharacters_in_harness_sql_are_not_interpreted(self):
        driver = live_driver(self.tmp)
        with patched_subprocess(controller, run=lambda argv, **kwargs: StubRun(
                rows_packet())) as calls:
            driver._sql(['SELECT 1 AS a;'], readback=True)
        argv = calls[0][1]
        self.assertIs(calls[0][2]['shell'], False)
        self.assertEqual(argv[-1], 'SELECT 1 AS a;')

    def test_literal_rejects_unsafe_identifiers(self):
        for value in ('', None, 17, 'a\x00b', 'x' * 600):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'E_HARNESS_LITERAL'):
                    controller._literal(value)

    def test_literal_escapes_quotes_rather_than_terminating_the_string(self):
        # An identifier carrying SQL punctuation is neutralized, not executed.
        self.assertEqual(controller._literal("x'; DROP TABLE issues; --"),
                         "'x''; DROP TABLE issues; --'")

    def test_bounded_output_capture_is_enforced(self):
        driver = live_driver(self.tmp)
        oversized = b'{"rows": []}' + b' ' * (controller.DRIVER_CAPTURE_BYTES + 1)
        with patched_subprocess(controller, run=lambda argv, **kwargs: StubRun(oversized)):
            with self.assertRaisesRegex(ValueError, 'E_HARNESS_CAPTURE'):
                driver._sql(['SELECT 1 AS a;'], readback=True)

    def test_error_propagation_from_a_failing_statement(self):
        driver = live_driver(self.tmp)
        with patched_subprocess(controller, run=lambda argv, **kwargs: StubRun(
                b'', returncode=1, stderr=b'boom')):
            with self.assertRaisesRegex(ValueError, 'E_HARNESS_SQL_RESULT'):
                driver._sql(['SELECT 1 AS a;'], readback=True)

    def test_timeout_is_not_swallowed(self):
        driver = live_driver(self.tmp)

        def timeout(argv, **kwargs):
            raise subprocess.TimeoutExpired(argv, controller.DRIVER_TIMEOUT_SECONDS)
        with patched_subprocess(controller, run=timeout):
            with self.assertRaises(subprocess.TimeoutExpired):
                driver._sql(['SELECT 1 AS a;'], readback=True)

    def test_result_shape_is_validated_not_assumed(self):
        driver = live_driver(self.tmp)
        for payload in (b'{"columns": []}', b'{"rows": {}}', b'not json', b''):
            with self.subTest(payload=payload):
                with patched_subprocess(controller, run=lambda argv, **kwargs: StubRun(payload)):
                    with self.assertRaises((ValueError, IndexError)):
                        driver._sql(['SELECT 1 AS a;'], readback=True)

    def test_duplicate_result_keys_are_refused(self):
        driver = live_driver(self.tmp)
        with patched_subprocess(controller, run=lambda argv, **kwargs: StubRun(
                b'{"rows": [{"a": 1, "a": 2}]}')):
            with self.assertRaisesRegex(ValueError, 'duplicate key'):
                driver._sql(['SELECT 1 AS a;'], readback=True)

    def test_fresh_readback_uses_a_new_invocation_and_never_the_cache(self):
        driver = live_driver(self.tmp)
        with patched_subprocess(controller, run=lambda argv, **kwargs: StubRun(
                rows_packet({'store_incarnation': NAMESPACE, 'namespace_key': 'identity',
                             'selection_digest': 'e' * 64, 'native_node_id': NODE,
                             'selected_database': 'mipx', 'selected_main_branch': 'main'}))
                ) as calls:
            driver._namespace = NAMESPACE
            driver.fresh_readback(['SELECT 1 AS a;'])
            driver.fresh_readback(['SELECT 1 AS a;'])
        runs = [argv for kind, argv, _ in calls if kind == 'run']
        self.assertEqual(len(runs), 16)
        self.assertEqual(runs[0], runs[8])

    def test_store_identity_is_observed_not_asserted(self):
        driver = live_driver(self.tmp)
        with patched_subprocess(controller, run=lambda argv, **kwargs: StubRun(
                rows_packet({'store_incarnation': NAMESPACE}))):
            self.assertEqual(driver.store_identity(), {'observed': False})

    def test_beads_identity_requires_observed_schema(self):
        from hybrid_bridge.practical_contract import LeasePracticalSelection
        driver = live_driver(self.tmp, engine=controller.ENGINE_BEADS)
        digest = LeasePracticalSelection.from_value(driver.schedule['requests']['selection']).digest
        answers = [
            rows_packet({'observed_database': 'mipx', 'observed_branch': 'main',
                         'observed_utc': AUTH}),
            rows_packet({'store_incarnation': NAMESPACE, 'namespace_key': 'identity',
                         'selection_digest': digest, 'native_node_id': NODE,
                         'selected_database': 'mipx', 'selected_main_branch': 'main'}),
            rows_packet({'observed_table': 'issues'}),
        ]
        seen = []

        def run(argv, **kwargs):
            seen.append(argv)
            return StubRun(answers[min(len(seen) - 1, len(answers) - 1)])
        with patched_subprocess(controller, run=run):
            identity = driver.store_identity()
        self.assertFalse(identity['beads']['observed'])
        self.assertEqual(identity['beads']['schema_tables'], [])

    def test_preflight_refuses_a_wrong_pin_without_starting_anything(self):
        driver = live_driver(self.tmp)
        fake = self.tmp / 'dolt.exe'
        fake.write_bytes(b'not the pinned binary')
        driver.schedule['requests']['selection']['dolt_executable'] = str(fake)
        with self.assertRaisesRegex(ValueError, 'E_HARNESS_DOLT_PIN'):
            driver.preflight()
        self.assertEqual(FakePopen.instances, [])

    def test_preflight_refuses_a_missing_scratch_root(self):
        driver = live_driver(self.tmp)
        driver.schedule['requests']['selection']['scratch_root'] = str(self.tmp / 'nope')
        with self.assertRaisesRegex(ValueError, 'E_HARNESS_PATH'):
            driver.preflight()

    def test_alice_runs_in_its_own_bounded_client_process(self):
        driver = live_driver(self.tmp)
        schedule = build_schedule()
        with patched_subprocess(controller):
            handle = driver.start_alice(schedule['phases']['alice_arm']['batch'])
        argv = FakePopen.instances[0].argv
        self.assertEqual(argv[1:3], ['-m', 'hybrid_bridge.practical_race_alice'])
        self.assertIn(controller.BARRIER_COMMENT, handle['batch'])
        self.assertIsNotNone(handle['pid'])

    def test_unsupported_session_view_yields_explicit_unsupported_evidence(self):
        driver = live_driver(self.tmp)
        with patched_subprocess(controller, run=lambda argv, **kwargs: (_ for _ in ()).throw(
                ValueError('E_HARNESS_SQL_RESULT: no processlist'))):
            barrier = driver.wait_barrier({'process': None}, 1)
        self.assertTrue(barrier['unsupported'])
        self.assertIsNone(barrier['authorization_time'])
        result = verify.judge_evidence({**clean_evidence(), 'barrier': barrier})
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE)
        self.assertIn('BARRIER_UNSUPPORTED_SYNC', codes(result))

    def test_barrier_timeout_without_observation_returns_no_evidence(self):
        driver = live_driver(self.tmp)
        with patched_subprocess(controller, run=lambda argv, **kwargs: StubRun(
                rows_packet())):
            self.assertIsNone(driver.wait_barrier({'process': None}, 0.1))

    def test_disabled_comparison_reports_a_causal_inability_rather_than_a_pass(self):
        driver = live_driver(self.tmp)
        driver._namespace = NAMESPACE
        with patched_subprocess(controller, run=lambda argv, **kwargs: (_ for _ in ()).throw(
                ValueError('E_HARNESS_SQL_RESULT: unrelated conflict'))):
            outcome = driver.disabled_comparison()
        # An arm that cannot execute has not demonstrated anything, so it is not
        # labelled executed.
        self.assertFalse(outcome['executed'])
        self.assertFalse(outcome['unsafe_effect_observed'])
        self.assertIn('error', outcome)
        evidence = {**clean_evidence(), 'controls': {
            'positive': {'executed': True, 'applied': True, 'fence_refused': False},
            'disabled': outcome}}
        result = verify.judge_evidence(evidence)
        self.assertNotEqual(result['verdict'], verify.PASSED)
        self.assertIn('CONTROL_NOT_EXECUTED', codes(result))


class ReviewerVerifierCaseTests(unittest.TestCase):
    """Six further false passes found by independent review.

    Each mutates recorded evidence only and drives the real run_race().
    """

    def _verdict(self, mutate=None, refusal=None):
        evidence = clean_evidence()
        if mutate is not None:
            mutate(evidence)
        driver = ScriptedDriver()
        driver.evidence = evidence
        if refusal is not None:
            driver.overrides['resume_alice'] = refusal
        return controller.run_race(build_schedule(), driver=driver)

    def test_case1_empty_final_grant_history_is_not_a_pass(self):
        def empty_history(evidence):
            evidence['observations']['final']['grant_history'] = []
        result = self._verdict(empty_history)
        self.assertNotEqual(result['verdict'], verify.PASSED, result['reasons'])

    def test_case1b_partial_grant_history_is_not_a_pass(self):
        def only_tombstone(evidence):
            evidence['observations']['final']['grant_history'] = [
                row for row in evidence['observations']['final']['grant_history']
                if row['event_kind'] != 'MINTED']
        result = self._verdict(only_tombstone)
        self.assertNotEqual(result['verdict'], verify.PASSED, result['reasons'])
        self.assertIn('GRANT_HISTORY_INCOMPLETE', codes(result))

    def test_case2_stale_row_in_snapshot_with_absent_record_is_not_a_pass(self):
        # Two observations of the same backend state disagree: the final
        # operations snapshot carries the stale operation while the separate
        # operation-record mapping omits it.
        def disagree(evidence):
            evidence['observations']['final']['operations'].append(
                {'store_incarnation': NAMESPACE, 'operation_id': OP_STALE,
                 'command_digest': '9' * 64,
                 'authorization_time': '2026-10-14 10:00:01.500000',
                 'resulting_row_lock': TOKEN_AFTER})
        result = self._verdict(disagree)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('STALE_BACKEND_SUCCESS_RECORD', codes(result))

    def test_case2b_snapshot_and_record_mapping_must_agree_on_fields(self):
        def disagree(evidence):
            row = evidence['observations']['final']['operations'][0]
            row['resulting_row_lock'] = TOKEN_AFTER + 5
        result = self._verdict(disagree)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('OPERATION_RECORD_DISAGREEMENT', codes(result))

    def test_case3_unrelated_task_that_disappears_is_not_a_pass(self):
        # "Unaffected work survives" must hold inside the affected tables too,
        # not only in tables the verifier happens to classify as unaffected.
        def vanish(evidence):
            evidence['observations']['before']['issues'].append(
                {'id': 'mipx-unrelated', 'assignee': 'carol', 'title': 'unrelated work',
                 'status': 'in_progress', 'row_lock': 5, 'ephemeral': 0})
        result = self._verdict(vanish)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('ROW_LOST', codes(result))

    def test_case3b_unrelated_grant_that_disappears_is_not_a_pass(self):
        def vanish(evidence):
            for observation in ('before', 'after_transfer', 'final'):
                evidence['observations'][observation]['grants'].append(
                    {'store_incarnation': NAMESPACE, 'grant_id': 'grant-other',
                     'task_id': 'mipx-other', 'actor': 'dave', 'status': 'CURRENT',
                     'issue_revision': 3, 'tombstoned': 0, 'lease_node': NODE,
                     'lease_granted_at': GRANTED_AT, 'lease_expiry': EXPIRES,
                     'lease_heartbeat': HEARTBEAT_BEFORE})
            evidence['observations']['before']['issues'].append(
                {'id': 'mipx-other', 'assignee': 'dave', 'title': 'other',
                 'status': 'in_progress', 'row_lock': 3, 'ephemeral': 0})
        result = self._verdict(vanish)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('ROW_LOST', codes(result))

    def test_case4_successor_grant_lease_facts_must_match_the_lease(self):
        for field, value in (('lease_node', 'some-other-node'),
                             ('lease_expiry', '2026-10-14 11:00:00.000000'),
                             ('lease_heartbeat', '2026-10-14 09:00:00.000000'),
                             ('lease_granted_at', '2026-10-14 09:59:00.000000')):
            with self.subTest(field=field):
                def mismatch(evidence, field=field, value=value):
                    evidence['observations']['final']['grants'][1][field] = value
                result = self._verdict(mismatch)
                self.assertEqual(result['verdict'], verify.FAILED)
                self.assertIn('GRANT_LEASE_FACTS_MISMATCH', codes(result))

    def test_case5_pointer_in_a_foreign_namespace_is_not_a_pass(self):
        def foreign(evidence):
            evidence['observations']['final']['current_grants'][0]['store_incarnation'] = \
                'other-store'
        result = self._verdict(foreign)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('POINTER_MISMATCH', codes(result))

    def test_case6_no_attributable_refusal_is_never_a_pass(self):
        result = self._verdict(refusal={'outcome': None, 'code': None,
                                        'resumed_at': BARRIER_RESUME})
        self.assertNotEqual(result['verdict'], verify.PASSED, result['reasons'])
        self.assertIn('REFUSAL_UNKNOWN', codes(result))
        # An unrelated refusal stays inconclusive for its own reason.
        unrelated = self._verdict(refusal={'outcome': 'UNKNOWN', 'code': 'E_X',
                                           'authority_readable': True,
                                           'predicate_refused': False,
                                           'resumed_at': BARRIER_RESUME})
        self.assertIn('REFUSAL_UNRELATED', codes(unrelated))

    def test_observed_unsafe_effect_still_fails_with_incomplete_evidence(self):
        # The new checks must not let incompleteness mask a real defect.
        def both(evidence):
            evidence['observations']['final']['grant_history'] = []
            evidence['observations']['final']['grants'][1]['lease_node'] = 'foreign'
        result = self._verdict(both)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('GRANT_LEASE_FACTS_MISMATCH', codes(result))


# -- driver wiring, exercised on the real methods -------------------------

class AuthorityObservation:
    """Observed authority the driver builds its requests from."""

    def __init__(self, holder=ALICE, grant_id=GRANT_OLD, token=TOKEN_BEFORE,
                 heartbeat=HEARTBEAT_BEFORE):
        self.values = {'issue_id': TASK, 'holder': holder, 'granted_node': NODE,
                       'granted_at': GRANTED_AT, 'lease_expires_at': EXPIRES,
                       'heartbeat_at': heartbeat, 'grant_id': grant_id,
                       'issue_row_lock': token}

    def __call__(self):
        return dict(self.values)


class FakeConsumer:
    """Stands in for the sealed consumer at the process boundary only.

    It returns the real companion completion shape. A mock that invented an
    `observed_state` field is exactly what hid the return-contract bug, so
    this one deliberately does not have that field.
    """

    def __init__(self, kind=verify.CM_APPLIED, raises=None):
        self.kind = kind
        self.raises = raises
        self.calls = []
        self._db = object()

    def dispatch_reassign_title(self, request):
        self.calls.append(('reassign', request))
        if self.raises is not None:
            raise self.raises
        return {'inserted': True, 'kind': self.kind, 'binding': dict(request.as_dict())}

    def dispatch_lease_title(self, request):
        self.calls.append(('title', request))
        if self.raises is not None:
            raise self.raises
        return {'inserted': True, 'kind': self.kind, 'binding': dict(request.as_dict())}


def readback_packets():
    """One result packet per read_state query, with two grants and two history rows."""
    return [
        rows_packet({'id': TASK, 'assignee': BOB, 'title': TITLE_WIN,
                     'status': 'in_progress', 'row_lock': TOKEN_AFTER, 'ephemeral': 0}),
        rows_packet({'issue_id': TASK, 'holder': BOB, 'granted_node': NODE,
                     'granted_at': GRANTED_AT, 'lease_expires_at': EXPIRES,
                     'heartbeat_at': HEARTBEAT_AFTER}),
        rows_packet({'store_incarnation': NAMESPACE, 'grant_id': GRANT_OLD, 'task_id': TASK,
                     'actor': ALICE, 'status': 'CURRENT', 'issue_revision': TOKEN_BEFORE,
                     'tombstoned': 1, 'lease_node': NODE, 'lease_granted_at': GRANTED_AT,
                     'lease_expiry': EXPIRES, 'lease_heartbeat': HEARTBEAT_BEFORE},
                    {'store_incarnation': NAMESPACE, 'grant_id': GRANT_NEW, 'task_id': TASK,
                     'actor': BOB, 'status': 'GRANTED', 'issue_revision': TOKEN_AFTER,
                     'tombstoned': 0, 'lease_node': NODE, 'lease_granted_at': GRANTED_AT,
                     'lease_expiry': EXPIRES, 'lease_heartbeat': HEARTBEAT_AFTER}),
        rows_packet({'store_incarnation': NAMESPACE, 'grant_id': GRANT_OLD,
                     'event_kind': 'TOMBSTONED', 'event_utc': AUTH},
                    {'store_incarnation': NAMESPACE, 'grant_id': GRANT_NEW,
                     'event_kind': 'MINTED', 'event_utc': AUTH}),
        rows_packet({'store_incarnation': NAMESPACE, 'task_id': TASK,
                     'grant_id': GRANT_NEW, 'current_revision': TOKEN_AFTER}),
        rows_packet(dict(metadata_row())),
        rows_packet({'store_incarnation': NAMESPACE, 'row_token': TOKEN_AFTER,
                     'operation_id': OP_WIN}),
        rows_packet({'store_incarnation': NAMESPACE, 'operation_id': OP_WIN,
                     'command_digest': 'f' * 64, 'authorization_time': AUTH,
                     'resulting_row_lock': TOKEN_AFTER}),
    ]


class DriverWiringTests(unittest.TestCase):
    """Real _LiveDriver methods behind fake process and SQL boundaries."""

    def setUp(self):
        FakePopen.instances = []
        self.temp = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_generated_schema_batch_is_executable_through_the_driver(self):
        driver = live_driver(self.tmp)
        schedule = build_schedule()
        with patched_subprocess(controller, run=lambda a, **k: StubRun(rows_packet())) as calls:
            driver.apply_ddl(schedule['phases']['setup']['ddl'])
        runs = [argv for kind, argv, _ in calls if kind == 'run']
        self.assertEqual(len(runs), len(schedule['phases']['setup']['ddl']))
        # The stored procedure and its internal semicolons must survive intact
        # in a single invocation, never split across clients.
        schema = runs[0][-1]
        self.assertIn('CREATE PROCEDURE IF NOT EXISTS mi_practical_assert_v2', schema)
        self.assertIn("SIGNAL SQLSTATE '45000'", schema)
        self.assertIn('CREATE TABLE IF NOT EXISTS mi_practical_v2_grants', schema)
        for argv in runs:
            self.assertNotIn('-q ;', argv)

    def test_bootstrap_and_registration_batches_keep_their_transaction_boundary(self):
        driver = live_driver(self.tmp)
        minted = 'c0dec0de-2026-4017-8017-000000000017'
        replies = iter([rows_packet(), rows_packet(
            {'store_incarnation': minted, 'namespace_key': 'identity'}),
            rows_packet(dict(store_incarnation=minted, namespace_key='identity',
                             selection_digest=None, native_node_id=None,
                             selected_database=None, selected_main_branch=None)), rows_packet()])
        with patched_subprocess(controller, run=lambda a, **k: StubRun(next(replies))) as calls:
            driver.bootstrap_namespace()
            driver.register_selection()
        runs = [argv[-1] for kind, argv, _ in calls if kind == 'run'
                and argv[-1].startswith('START TRANSACTION;')]
        self.assertEqual(len(runs), 2)
        self.assertIn('START TRANSACTION;', runs[0])
        self.assertIn('COMMIT;', runs[0])
        self.assertIn('START TRANSACTION;', runs[1])
        self.assertIn('COMMIT;', runs[1])

    def test_foreign_batch_text_is_still_refused(self):
        driver = live_driver(self.tmp)
        with patched_subprocess(controller, run=lambda a, **k: StubRun(rows_packet())) as calls:
            with self.assertRaises(ValueError):
                driver.apply_ddl(['DROP TABLE issues;'])
        self.assertEqual([c for c in calls if c[0] == 'run'], [])

    def test_cm_observations_handles_several_winner_operations(self):
        from complete_read_v2 import ledger
        driver = live_driver(self.tmp)
        driver.schedule['identities']['winner_operation_ids'] = ['op-a', 'op-b']
        consumer = FakeConsumer()
        consumer._db = ledger.connect(':memory:')
        self.addCleanup(consumer._db.close)
        driver._consumer_for = lambda: consumer

        def events(db, operation_id=None):
            return [{'kind': kind, 'detail': json.dumps({'binding': {'operation_id': operation_id}})} for kind in
                    (verify.CM_INTENT, verify.CM_DISPATCHED)]

        import hybrid_bridge.practical_race_controller as module
        original = module.ledger_events
        module.ledger_events = events
        try:
            observed = driver.cm_observations()
        finally:
            module.ledger_events = original
        self.assertEqual(sorted(observed['history']), ['op-1', 'op-a', 'op-b'])
        self.assertEqual(observed['dispatch_counts']['op-a'], 1)

    def test_run_transfer_requires_proven_success_not_a_returned_value(self):
        driver = live_driver(self.tmp)
        driver._current_authority = AuthorityObservation()
        consumer = FakeConsumer(kind=verify.CM_UNKNOWN)
        driver._consumer_for = lambda: consumer
        outcome = driver.run_transfer('UPDATE leases SET holder = x;')
        self.assertFalse(outcome['committed'])
        self.assertEqual(outcome['outcome'], 'UNKNOWN')
        # A proven working-set application is accepted.
        driver._consumer_for = lambda: FakeConsumer()
        self.assertTrue(driver.run_transfer('x')['committed'])

    def test_run_transfer_accepts_a_dataclass_request(self):
        driver = live_driver(self.tmp)
        driver._current_authority = AuthorityObservation()
        consumer = FakeConsumer()
        driver._consumer_for = lambda: consumer
        outcome = driver.run_transfer('UPDATE leases SET holder = x;')
        request = consumer.calls[0][1]
        self.assertEqual(outcome['operation_id'], request.operation_id)

    def test_read_state_keeps_every_row_under_its_own_table(self):
        driver = live_driver(self.tmp)
        driver._namespace = NAMESPACE
        packets = readback_packets()
        seen = []

        def run(argv, **kwargs):
            seen.append(argv)
            return StubRun(packets[min(len(seen) - 1, len(packets) - 1)])

        with patched_subprocess(controller, run=run):
            state = driver.read_state()
        self.assertEqual(len(state['grants']), 2)
        self.assertEqual(len(state['grant_history']), 2)
        self.assertEqual(len(state['operations']), 1)
        for row in state['grant_history']:
            self.assertIn('event_kind', row)
        for row in state['current_grants']:
            self.assertNotIn('event_kind', row)
        self.assertEqual(state['issues'][0]['id'], TASK)
        self.assertEqual(sum(len(v) for v in state.values()), 10)

    def test_positive_control_requires_applied_evidence_and_readback(self):
        driver = live_driver(self.tmp)
        driver._current_authority = AuthorityObservation(
            holder=BOB, grant_id=GRANT_NEW, token=TOKEN_AFTER, heartbeat=HEARTBEAT_AFTER)
        driver._consumer_for = lambda: FakeConsumer(kind=verify.CM_UNKNOWN)
        outcome = driver.positive_control()
        self.assertFalse(outcome['applied'])
        self.assertEqual(outcome['outcome'], 'UNKNOWN')
        # An unknown outcome must never be reported as applied.
        driver._consumer_for = lambda: FakeConsumer(kind=None)
        self.assertFalse(driver.positive_control()['applied'])

    def test_positive_control_confirms_the_effect_by_fresh_readback(self):
        driver = live_driver(self.tmp)
        driver._namespace = NAMESPACE
        driver._current_authority = AuthorityObservation(
            holder=BOB, grant_id=GRANT_NEW, token=TOKEN_AFTER, heartbeat=HEARTBEAT_AFTER)
        driver._consumer_for = lambda: FakeConsumer()
        packets = readback_packets()
        packets[0] = rows_packet({'id': TASK, 'assignee': BOB, 'title': 'positive control title',
                                 'status': 'in_progress', 'row_lock': TOKEN_AFTER,
                                 'ephemeral': 0})
        seen = []

        def run(argv, **kwargs):
            seen.append(argv)
            return StubRun(packets[min(len(seen) - 1, len(packets) - 1)])

        with patched_subprocess(controller, run=run):
            outcome = driver.positive_control()
        self.assertTrue(outcome['applied'])
        # The confirmation is an independent readback, not the dispatch result.
        self.assertGreaterEqual(len(seen), 2)
        self.assertEqual(outcome['readback_title'], 'positive control title')

    def test_disabled_comparison_executes_and_observes_the_unsafe_baseline(self):
        driver = live_driver(self.tmp)
        driver._namespace = NAMESPACE
        stale = [rows_packet()] + readback_packets()
        stale[1] = rows_packet({'id': TASK, 'assignee': ALICE, 'title': TITLE_STALE,
                               'status': 'in_progress', 'row_lock': TOKEN_AFTER,
                               'ephemeral': 0})
        seen = []

        def run(argv, **kwargs):
            seen.append(argv)
            return StubRun(stale[min(len(seen) - 1, len(stale) - 1)])

        with patched_subprocess(controller, run=run):
            outcome = driver.disabled_comparison()
        updates = [argv for argv in seen
                  if 'UPDATE issues SET title' in argv[-1]]
        self.assertEqual(len(updates), 1, 'the disabled arm must really execute its update')
        self.assertTrue(outcome['executed'])
        self.assertTrue(outcome['unsafe_effect_observed'])
        self.assertNotIn('error', outcome)

    def test_alice_worker_spec_carries_no_sql_and_derives_the_paused_batch(self):
        driver = live_driver(self.tmp)
        with patched_subprocess(controller):
            handle = driver.start_alice(build_schedule()['phases']['alice_arm']['batch'])
        spec = json.loads(Path(handle['spec_path']).read_text(encoding='utf-8'))
        self.assertNotIn('batch', spec)
        self.assertNotIn('sql', spec)
        self.assertEqual(spec['pause_seconds'], 20)
        self.assertIn(controller.BARRIER_COMMENT, handle['batch'])

    def test_alice_worker_env_can_import_the_harness_and_the_companion(self):
        driver = live_driver(self.tmp)
        with patched_subprocess(controller):
            driver.start_alice(build_schedule()['phases']['alice_arm']['batch'])
        env = FakePopen.instances[0].kwargs['env']
        entries = env['PYTHONPATH'].split(os.pathsep)
        self.assertTrue(any(entry.endswith('hybrid_bridge') or
                            entry.endswith(('scripts', 'scripts_v2')) for entry in entries))
        self.assertTrue(any('complete_read_v2' in entry or
                            entry.endswith('scripts') for entry in entries))
        self.assertTrue(any(Path(entry, 'hybrid_bridge').is_dir() for entry in entries))
        self.assertTrue(any(Path(entry, 'complete_read_v2').is_dir() for entry in entries))

    def test_orchestration_bootstraps_before_it_observes_identity(self):
        driver = ScriptedDriver()
        controller.run_race(build_schedule(), driver=driver)
        order = driver.calls
        self.assertLess(order.index('apply_ddl'), order.index('store_identity'))
        self.assertLess(order.index('bootstrap_namespace'), order.index('store_identity'))
        self.assertLess(order.index('register_selection'), order.index('store_identity'))
        self.assertLess(order.index('store_identity'), order.index('seed'))

    def test_owned_client_is_stopped_after_a_failure(self):
        driver = ScriptedDriver(wait_barrier=None)
        alice = {'process': None}
        driver.overrides['start_alice'] = alice
        controller.run_race(build_schedule(), driver=driver)
        self.assertIn('stop_alice', driver.calls)
        self.assertEqual(driver.calls[-1], 'stop_server')

    def test_owned_client_is_stopped_after_a_successful_run(self):
        driver = ScriptedDriver()
        controller.run_race(build_schedule(), driver=driver)
        self.assertIn('stop_alice', driver.calls)
        self.assertLess(driver.calls.index('stop_alice'), driver.calls.index('stop_server'))

    def test_source_manifest_covers_the_worker_and_the_companion(self):
        manifest, digest = controller._source_manifest()
        self.assertIn('practical_race_alice.py', manifest)
        self.assertIn('complete_read_v2/ledger.py', manifest)
        self.assertEqual(digest, hashlib.sha256(json.dumps(
            manifest, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest())
        for name in manifest:
            self.assertEqual(len(manifest[name]), 64)

    def test_paused_dispatch_is_derived_not_supplied(self):
        # The sealed backend must build the paused batch itself from the
        # validated request, so no caller SQL can reach the store.
        from hybrid_bridge.practical_lease_backend import LeaseScratchBackend
        from hybrid_bridge import practical_lease_sql as lease_sql
        from tests_v2.test_practical_lease_contract import packet
        seen = {}

        def recording_builder(selection, request, *, pause_seconds):
            seen['selection'] = selection
            seen['request'] = request
            seen['pause_seconds'] = pause_seconds
            return lease_sql.experiment_guarded_title_sql(
                selection, request, pause_seconds=pause_seconds)

        original_builder = lease_sql.experiment_guarded_title_sql
        original_invoke = LeaseScratchBackend._invoke
        lease_sql.experiment_guarded_title_sql = recording_builder
        LeaseScratchBackend._invoke = lambda self, sql, *, timeout=0: []
        try:
            backend = _pinned_backend()
            with self.assertRaises(Exception):
                backend.execute_paused_guarded_title(
                    packet(), cm_db=object(), reservation=object(), pause_seconds=20)
        finally:
            lease_sql.experiment_guarded_title_sql = original_builder
            LeaseScratchBackend._invoke = original_invoke
        self.assertEqual(seen['pause_seconds'], 20)
        self.assertEqual(seen['request'].operation_id, 'op-1')
        self.assertEqual(seen['selection'].native_node_id,
                         'practical-approved-scratch-only')
        # The batch really carries the bounded pause, and the transport bound
        # grows by exactly that pause.
        built = lease_sql.experiment_guarded_title_sql(
            seen['selection'], seen['request'], pause_seconds=20)
        self.assertIn('DO SLEEP(20)', built)

    def test_paused_dispatch_bounds_the_pause(self):
        from hybrid_bridge.practical_lease_backend import LeaseScratchBackend
        from tests_v2.test_practical_lease_contract import packet
        backend = _pinned_backend()
        for value in (0, 31, -1, '20', 20.0, True):
            with self.subTest(pause=value):
                with self.assertRaises(Exception):
                    backend.execute_paused_guarded_title(
                        packet(), cm_db=object(), reservation=object(), pause_seconds=value)


def _pinned_backend():
    from hybrid_bridge.practical_lease_backend import LeaseScratchBackend
    from tests_v2.test_practical_lease_backend import selected
    return LeaseScratchBackend(selected())


class RealContractTests(unittest.TestCase):
    """Contracts taken from the real components, not from a mock's shape."""

    def test_completion_outcome_uses_the_real_companion_return_shape(self):
        # The real completion returns {'inserted','kind','binding'} and has no
        # observed_state field at all.
        import inspect
        from complete_read_v2 import ledger
        self.assertNotIn('observed_state', inspect.getsource(
            ledger.complete_practical_native_readback).split('return {')[1].split('}')[0])
        applied = {'inserted': True, 'kind': verify.CM_APPLIED, 'binding': {}}
        unknown = {'inserted': True, 'kind': verify.CM_UNKNOWN, 'binding': {}}
        self.assertEqual(controller.completion_outcome(applied), 'APPLIED')
        self.assertEqual(controller.completion_outcome(unknown), 'UNKNOWN')
        # A missing or unrecognized field is never success.
        for value in ({}, {'inserted': True}, {'observed_state': 'WORKING_SET_APPLIED'},
                      {'kind': 'SOMETHING_ELSE'}, None, 'APPLIED'):
            with self.subTest(value=value):
                self.assertNotEqual(controller.completion_outcome(value), 'APPLIED')

    def test_the_three_success_layers_stay_distinct(self):
        # Backend receipt state, companion terminal event and uncertainty are
        # three different things and must never be collapsed.
        self.assertNotEqual('WORKING_SET_APPLIED', verify.CM_APPLIED)
        self.assertNotEqual('WORKING_SET_APPLIED', verify.CM_UNKNOWN)
        self.assertNotEqual(verify.CM_APPLIED, verify.CM_UNKNOWN)
        self.assertEqual(controller.completion_outcome({'kind': verify.CM_UNKNOWN}), 'UNKNOWN')

    def test_unknown_is_never_promoted_to_a_fence_refusal(self):
        attributed = controller.stale_refusal_attribution(
            outcome='UNKNOWN', predicate_refused=False, authority_readable=True)
        self.assertNotEqual(attributed['by'], 'fence')
        unreadable = controller.stale_refusal_attribution(
            outcome='UNKNOWN', predicate_refused=True, authority_readable=False)
        self.assertEqual(unreadable['by'], 'other')
        refused = controller.stale_refusal_attribution(
            outcome='UNKNOWN', predicate_refused=True, authority_readable=True)
        self.assertIsNone(refused['by'])
        self.assertEqual(refused['code'], 'E_HARNESS_EXECUTION_CAUSE_UNPROVEN')
        absent = controller.stale_refusal_attribution(
            outcome=None, predicate_refused=True, authority_readable=True)
        self.assertNotEqual(absent['by'], 'fence')

    def test_transfer_and_positive_control_read_the_real_field(self):
        driver = live_driver(Path(tempfile.mkdtemp()))
        driver._current_authority = AuthorityObservation()
        driver._consumer_for = lambda: FakeConsumer(kind=verify.CM_APPLIED)
        self.assertTrue(driver.run_transfer('x')['committed'])
        driver._consumer_for = lambda: FakeConsumer(kind=verify.CM_UNKNOWN)
        self.assertFalse(driver.run_transfer('x')['committed'])
        driver._consumer_for = lambda: FakeConsumer(kind=None)
        self.assertFalse(driver.run_transfer('x')['committed'])

    def test_executed_paused_sql_carries_the_marker_the_watcher_searches(self):
        from hybrid_bridge.practical_lease_backend import LeaseScratchBackend
        from tests_v2.test_practical_lease_backend import selected
        from tests_v2.test_practical_lease_contract import packet
        captured = {}

        def fake_invoke(self, sql, *, timeout=0):
            captured['sql'] = sql
            captured['timeout'] = timeout
            return []

        original = LeaseScratchBackend._invoke
        original_owner = LeaseScratchBackend._execute_protected
        LeaseScratchBackend._invoke = fake_invoke

        def stop_before_dispatch(self, request, cm_db, reservation, *, sql, timeout):
            captured['sql'] = sql
            captured['timeout'] = timeout
            raise LeaseDeliveryUnknown('E_TEST_STOP_BEFORE_DISPATCH')

        LeaseScratchBackend._execute_protected = stop_before_dispatch
        try:
            backend = LeaseScratchBackend(selected())
            with self.assertRaises(LeaseDeliveryUnknown):
                backend.execute_paused_guarded_title(
                    packet(), cm_db=object(), reservation=object(), pause_seconds=20)
        finally:
            LeaseScratchBackend._invoke = original
            LeaseScratchBackend._execute_protected = original_owner
        self.assertIn('DO SLEEP(20)', captured['sql'])
        self.assertIn(controller.BARRIER_COMMENT, captured['sql'])

    def test_claim_request_uses_the_current_v2_contract(self):
        from hybrid_bridge.practical_lease_issuer import LeaseClaimRequest
        from hybrid_bridge import practical_lease_sql as lease_sql
        from hybrid_bridge.practical_contract import canonical_command_digest
        from tests_v2.test_practical_lease_backend import selected
        payload = {'schema_version': 2, 'work_item_id': 'work-1',
                   'operation_id': 'op-claim', 'action': 'initial_claim_lease',
                   'task_id': TASK, 'actor': ALICE, 'expected_status': 'open',
                   'expected_assignee': None, 'expected_row_lock': 0,
                   'new_grant_id': GRANT_OLD}
        payload['command_digest'] = canonical_command_digest(payload)
        request = LeaseClaimRequest.from_value(payload)
        # The real builder must accept the request the driver builds.
        batch = lease_sql.initial_claim_sql(selected(), request)
        self.assertIn('initial_claim', batch.lower())

    def test_seed_inserts_rather_than_updates(self):
        driver = live_driver(Path(tempfile.mkdtemp()))
        driver._namespace = NAMESPACE  # Bootstrap is this component test's prerequisite.
        driver._claim = lambda: None
        packets = ([rows_packet(), rows_packet({'store_incarnation': NAMESPACE})]
                   + readback_packets())
        seen = []

        def run(argv, **kwargs):
            seen.append(argv[-1])
            return StubRun(packets[min(len(seen) - 1, len(packets) - 1)])

        with patched_subprocess(controller, run=run):
            driver.seed({'issue': {'id': TASK, 'status': 'open'}})
        self.assertTrue(any(s.upper().startswith('INSERT INTO ISSUES') for s in seen))
        self.assertFalse(any(s.upper().startswith('UPDATE ISSUES') for s in seen))
        # Seed preserves the namespace already bound before registration.
        self.assertEqual(driver.schedule['requests']['selection']['incarnation'], NAMESPACE)


class SecondRoundVerifierCaseTests(unittest.TestCase):
    """Three further false passes found by the second review."""

    def _verdict(self, mutate):
        evidence = clean_evidence()
        mutate(evidence)
        driver = ScriptedDriver()
        driver.evidence = evidence
        return controller.run_race(build_schedule(), driver=driver)

    def test_successor_grant_missing_lease_snapshot_is_not_a_pass(self):
        def strip(evidence):
            grant = evidence['observations']['final']['grants'][1]
            for field in ('lease_node', 'lease_granted_at', 'lease_expiry', 'lease_heartbeat'):
                grant.pop(field, None)
        result = self._verdict(strip)
        self.assertNotEqual(result['verdict'], verify.PASSED, result['reasons'])
        self.assertIn('GRANT_LEASE_FACTS_INCOMPLETE', codes(result))

    def test_each_missing_grant_lease_field_is_caught(self):
        for field in ('lease_node', 'lease_granted_at', 'lease_expiry', 'lease_heartbeat'):
            with self.subTest(field=field):
                def strip_one(evidence, field=field):
                    evidence['observations']['final']['grants'][1].pop(field, None)
                result = self._verdict(strip_one)
                self.assertNotEqual(result['verdict'], verify.PASSED)

    def test_s1_lease_holder_inconsistent_with_the_transfer_is_not_a_pass(self):
        def wrong_holder(evidence):
            evidence['observations']['after_transfer']['leases'][0]['holder'] = 'mallory'
        result = self._verdict(wrong_holder)
        self.assertNotEqual(result['verdict'], verify.PASSED, result['reasons'])
        self.assertIn('TRANSFER_STATE_INCONSISTENT', codes(result))

    def test_s1_pointer_and_prior_grant_are_checked(self):
        def bad_pointer(evidence):
            evidence['observations']['after_transfer']['current_grants'][0]['grant_id'] = GRANT_OLD
        self.assertIn('POINTER_MISMATCH', codes(self._verdict(bad_pointer)))

        def prior_still_live(evidence):
            evidence['observations']['after_transfer']['grants'][0]['tombstoned'] = 0
        self.assertIn('PRIOR_GRANT_NOT_TOMBSTONED', codes(self._verdict(prior_still_live)))

    def test_stale_operation_in_s1_cannot_vanish_in_s2(self):
        # An observed unsafe effect stays observed even if a later snapshot
        # omits it.
        def stale_then_gone(evidence):
            evidence['observations']['after_transfer']['operations'].append(
                {'store_incarnation': NAMESPACE, 'operation_id': OP_STALE,
                 'command_digest': '7' * 64,
                 'authorization_time': '2026-10-14 10:00:01.500000',
                 'resulting_row_lock': TOKEN_AFTER})
        result = self._verdict(stale_then_gone)
        self.assertEqual(result['verdict'], verify.FAILED)
        self.assertIn('STALE_BACKEND_SUCCESS_RECORD', codes(result))


class RealComponentIntegrationTests(unittest.TestCase):
    """Component integration with scripted authority, clock and snapshots.

    These six tests cover individual component contracts. They do not drive
    fresh setup through claim, race, controls and verdict. The stateful test
    in test_practical_race_offline_sequence supplies that coverage.
    """

    def setUp(self):
        # Retained and uniquely named: this suite never deletes evidence, and
        # Windows keeps the sqlite handle open past close anyway.
        self.root = Path(tempfile.mkdtemp(prefix='practical-race-integration-'))
        FakePopen.instances = []
        from complete_read_v2 import ledger
        from hybrid_bridge.practical_lease_backend import LeaseScratchBackend
        from hybrid_bridge.practical_lease_consumer import LeaseNativeConsumer
        from tests_v2.test_practical_consumer import (
            authority_row, lease_selection, reassign_persisted_row)
        from tests_v2.test_practical_lease_backend import reassign_persisted_row as _rpr
        self.ledger = ledger
        self.authority_row = authority_row
        self.reassign_row = _rpr
        self.db = ledger.connect(self.root / 'cm.sqlite')
        selection = lease_selection()
        work_item = 'work-' + TASK
        ledger.create_work_item(self.db, work_item, 'task-' + work_item, 'SMOKE')
        ledger.coordination_put(self.db, work_item, {'registered': True})
        self.backend = LeaseScratchBackend(selection)
        self.consumer = LeaseNativeConsumer(self.db, self.backend)
        self.authority = authority_row(self.backend.selection.digest,
                                       issue_id=TASK, grant_id=GRANT_OLD,
                                       holder=ALICE, assignee=ALICE,
                                       issue_row_lock=TOKEN_BEFORE,
                                       grant_actor=ALICE,
                                       issue_revision=TOKEN_BEFORE,
                                       current_revision=TOKEN_BEFORE)
        schedule = build_schedule()
        schedule['requests']['selection'] = dict(selection)
        driver = controller._LiveDriver(schedule, spawn=FakePopen, stop_grace_seconds=0.05)
        driver.run_id = RUN
        driver.log_dir = self.root / '.practical-race' / RUN
        driver.log_dir.mkdir(parents=True, exist_ok=True)
        driver._namespace = self.backend.selection.incarnation
        driver._consumer_for = lambda: self.consumer
        driver._current_authority = lambda: dict(self.authority)
        driver._clock = lambda: '2026-10-14 10:00:01.500000'
        driver.read_state = lambda: state_final()
        self.driver = driver

    def tearDown(self):
        self.db.close()

    def _boundary(self, dispatch_rows, readback_rows):
        """Fake only the process boundary; argv and receipt parsing stay real."""
        import hybrid_bridge.practical_lease_backend as backend_module

        def run(argv, **kwargs):
            sql = argv[-1]
            if 'observed_utc' in sql:
                payload = {'rows': [self.authority]}
            elif sql.lstrip().upper().startswith('SELECT'):
                payload = {'rows': list(readback_rows)}
            else:
                payload = {'rows': list(dispatch_rows)}
            return StubRun(json.dumps(payload).encode())

        original_boundary = backend_module._native_boundary
        backend_module._native_boundary = lambda selection: None
        original_run = backend_module.subprocess.run
        backend_module.subprocess.run = run
        return backend_module, original_boundary, original_run

    def _restore(self, patched):
        module, boundary, run = patched
        module._native_boundary = boundary
        module.subprocess.run = run

    def test_real_transfer_dispatch_is_read_through_the_real_completion_shape(self):
        request = self.driver._transfer_request_from_observed()
        receipt = self.reassign_row(self.backend.selection, request)
        patched = self._boundary([receipt], [receipt])
        try:
            result = self.consumer.dispatch_reassign_title(request.as_dict())
            outcome = self.driver.run_transfer('x')
        finally:
            self._restore(patched)
        # The companion really returns inserted/kind/binding, and the driver
        # must read that, not an invented field.
        self.assertEqual(set(result), {'inserted', 'kind', 'binding'})
        self.assertEqual(result['kind'], verify.CM_APPLIED)
        self.assertTrue(outcome['committed'])
        self.assertEqual(outcome['outcome'], 'APPLIED')

    def test_real_uncertain_dispatch_is_not_read_as_success_or_a_refusal(self):
        request = self.driver._transfer_request_from_observed()
        # No stored operation row: the dispatch is uncertain, not successful.
        patched = self._boundary([], [])
        try:
            result = self.consumer.dispatch_reassign_title(request.as_dict())
            outcome = self.driver.run_transfer('x')
        finally:
            self._restore(patched)
        self.assertEqual(result['kind'], verify.CM_UNKNOWN)
        self.assertFalse(outcome['committed'])
        self.assertEqual(outcome['outcome'], 'UNKNOWN')
        # An unknown outcome alone never attributes a fence refusal.
        self.assertNotEqual(
            controller.stale_refusal_attribution(
                outcome='UNKNOWN', predicate_refused=False,
                authority_readable=True)['by'], 'fence')
        self.assertEqual(
            controller.stale_refusal_attribution(
                outcome='UNKNOWN', predicate_refused=True,
                authority_readable=True)['by'], None)

    def test_real_journal_records_the_dispatch_consumption(self):
        request = self.driver._transfer_request_from_observed()
        receipt = self.reassign_row(self.backend.selection, request)
        patched = self._boundary([receipt], [receipt])
        try:
            self.consumer.dispatch_reassign_title(request.as_dict())
        finally:
            self._restore(patched)
        kinds = [row[0] for row in self.db.execute(
            "SELECT kind FROM events WHERE kind LIKE 'PRACTICAL_NATIVE_%' ORDER BY seq")]
        self.assertEqual(kinds[0], verify.CM_INTENT)
        self.assertEqual(kinds.count(verify.CM_DISPATCHED), 1)
        self.assertEqual(kinds[-1], verify.CM_APPLIED)
        self.assertEqual(self.ledger.verify_history(self.db)['internal_chain'], 'VERIFIED')

    def test_real_paused_dispatch_sql_carries_the_marker(self):
        from hybrid_bridge.practical_lease_backend import LeaseScratchBackend
        from tests_v2.test_practical_lease_backend import selected
        from tests_v2.test_practical_lease_contract import packet
        captured = {}
        original_invoke = LeaseScratchBackend._invoke
        original_protected = LeaseScratchBackend._execute_protected
        LeaseScratchBackend._invoke = lambda self, sql, *, timeout=0: []

        def capture(self, request, cm_db, reservation, *, sql, timeout):
            captured['sql'] = sql
            raise LeaseDeliveryUnknown('E_TEST_STOP')

        LeaseScratchBackend._execute_protected = capture
        try:
            with self.assertRaises(LeaseDeliveryUnknown):
                LeaseScratchBackend(selected()).execute_paused_guarded_title(
                    packet(), cm_db=object(), reservation=object(), pause_seconds=20)
        finally:
            LeaseScratchBackend._invoke = original_invoke
            LeaseScratchBackend._execute_protected = original_protected
        self.assertIn('DO SLEEP(20)', captured['sql'])
        self.assertIn(controller.BARRIER_COMMENT, captured['sql'])

    def test_real_claim_request_is_accepted_by_the_real_builder(self):
        from hybrid_bridge.practical_lease_issuer import LeaseClaimRequest
        from hybrid_bridge import practical_lease_sql as lease_sql
        from hybrid_bridge.practical_contract import canonical_command_digest
        from tests_v2.test_practical_lease_backend import selected
        payload = {'schema_version': 2, 'work_item_id': 'work-1', 'operation_id': 'op-claim',
                   'action': 'initial_claim_lease', 'task_id': TASK, 'actor': ALICE,
                   'expected_status': 'open', 'expected_assignee': None,
                   'expected_row_lock': 0, 'new_grant_id': GRANT_OLD}
        payload['command_digest'] = canonical_command_digest(payload)
        request = LeaseClaimRequest.from_value(payload)
        batch = lease_sql.initial_claim_sql(selected(), request)
        lowered = batch.lower()
        self.assertIn('e_mi2_initial_claim_auth', lowered)
        self.assertIn('insert into leases', lowered)

    def test_observed_store_identity_shape_is_what_the_verifier_demands(self):
        identity = {'observed': True, 'verification': 'QUERY_OBSERVED', 'database': 'mipx',
                    'branch': 'main', 'namespace': self.backend.selection.incarnation,
                    'node': self.backend.selection.native_node_id,
                    'schema_tables': sorted(verify.REQUIRED_PHYSICAL_TABLES)}
        evidence = clean_evidence()
        evidence['store'] = identity
        result = verify.judge_evidence(evidence)
        self.assertNotIn('IDENTITY_UNVERIFIED', codes(result))
        self.assertEqual(result['verdict'], verify.PASSED, result['reasons'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
