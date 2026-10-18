"""Offline repair regressions. TEST_ONLY; no native SQL execution is proved."""
import json
from pathlib import Path
import tempfile
import unittest

from tests_v2 import test_practical_race_harness as h

controller = h.controller
verify = h.verify


class RefusalCausationRegressionTests(unittest.TestCase):
    def test_actual_resume_unrelated_failure_after_transfer_is_not_fence_proof(self):
        root = Path(tempfile.mkdtemp(prefix='refusal-causation-retained-'))
        driver = h.live_driver(root)
        driver._clock = lambda: h.BARRIER_RESUME
        driver._current_authority = h.AuthorityObservation(
            holder=h.BOB, grant_id=h.GRANT_NEW, token=h.TOKEN_AFTER,
            heartbeat=h.HEARTBEAT_AFTER)
        driver.alice_outcome_path = root / 'unrelated-outcome.json'
        driver.alice_outcome_path.write_text(json.dumps({
            'operation_id': h.OP_STALE, 'outcome': 'UNKNOWN',
            'code': 'E_UNRELATED_TRANSPORT_FAILURE'}), encoding='utf-8')
        outcome = driver.resume_alice({'process': None})
        result = controller.run_race(
            h.build_schedule(), driver=h.ScriptedDriver(resume_alice=outcome))
        self.assertTrue(outcome['predicate_refused'])
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE, result)
        self.assertEqual(outcome['refusal'], {
            'by': None, 'code': 'E_HARNESS_EXECUTION_CAUSE_UNPROVEN'})
        self.assertIn('REFUSAL_UNKNOWN', h.codes(result))

    def test_unknown_and_current_staleness_alone_remain_unattributed(self):
        result = controller.stale_refusal_attribution(
            outcome='UNKNOWN', predicate_refused=True, authority_readable=True)
        self.assertEqual(result, {
            'by': None, 'code': 'E_HARNESS_EXECUTION_CAUSE_UNPROVEN'})

    def test_worker_cannot_supply_its_own_fence_cause(self):
        root = Path(tempfile.mkdtemp(prefix='forged-cause-retained-'))
        driver = h.live_driver(root)
        driver._clock = lambda: h.BARRIER_RESUME
        driver.alice_outcome_path = root / 'forged.json'
        driver.alice_outcome_path.write_text(json.dumps({
            'operation_id': h.OP_STALE, 'outcome': 'UNKNOWN',
            'refusal': {'by': 'fence', 'code': 'CALLER_CREATED_CAUSE'},
            'execution_cause': {'success': True, 'predicate': 'rejected'}}))
        self.assertNotEqual(driver.resume_alice({'process': None})['refusal']['by'], 'fence')


class NamespacePropagationRegressionTests(unittest.TestCase):
    minted = 'c0dec0de-2026-4017-8017-000000000017'

    def _exercise(self, bootstrap_rows=None, observed=None, existing=None):
        from hybrid_bridge.practical_lease_sql import v2_namespace_bootstrap_sql
        driver = h.live_driver(Path(tempfile.mkdtemp(prefix='namespace-retained-')))
        calls = []
        metadata = dict(store_incarnation=self.minted, namespace_key='identity',
                        selection_digest=None, native_node_id=None,
                        selected_database=None, selected_main_branch=None)
        if observed is not None:
            metadata.update(observed)
        bootstrapped = False

        def run(argv, **kwargs):
            nonlocal bootstrapped
            sql = argv[-1]
            calls.append(sql)
            if sql == v2_namespace_bootstrap_sql():
                bootstrapped = True
                rows = bootstrap_rows if bootstrap_rows is not None else [
                    {'store_incarnation': self.minted, 'namespace_key': 'identity'}]
            elif sql.startswith('SELECT') and 'mi_practical_v2_metadata' in sql:
                rows = [metadata] if bootstrapped else list(existing or [])
            else:
                rows = []
            return h.StubRun(json.dumps({'rows': rows}).encode())

        return driver, calls, h.patched_subprocess(controller, run=run)

    def test_minted_namespace_is_bound_before_registration(self):
        from hybrid_bridge.practical_contract import LeasePracticalSelection
        driver, calls, boundary = self._exercise()
        with boundary:
            driver.bootstrap_namespace()
            driver.register_selection()
        selected = LeasePracticalSelection.from_value(driver.schedule['requests']['selection'])
        self.assertEqual(selected.incarnation, self.minted)
        registration = next(sql for sql in calls if 'SET selection_digest' in sql)
        from hybrid_bridge.practical_sql import _text
        self.assertIn('store_incarnation = ' + _text(self.minted), registration)
        self.assertIn(_text(selected.digest), registration)
        self.assertEqual(driver._namespace, self.minted)

    def test_missing_malformed_or_mismatched_bootstrap_refuses_before_registration(self):
        cases = [([], None), ([{}], None),
                 ([{'store_incarnation': '', 'namespace_key': 'identity'}], None),
                 ([{'store_incarnation': 'not-a-db-uuid', 'namespace_key': 'identity'}],
                  {'store_incarnation': 'not-a-db-uuid'}),
                 ([{'store_incarnation': self.minted, 'namespace_key': 'foreign'}], None),
                 ([{'store_incarnation': self.minted, 'namespace_key': 'identity'}] * 2, None),
                 (None, {'store_incarnation': 'foreign-store'}),
                 (None, {'selection_digest': 'a' * 64})]
        for rows, observed in cases:
            with self.subTest(rows=rows, observed=observed):
                driver, calls, boundary = self._exercise(rows, observed)
                with boundary, self.assertRaisesRegex(ValueError, 'E_HARNESS_NAMESPACE'):
                    driver.bootstrap_namespace()
                self.assertFalse(any('SET selection_digest' in sql for sql in calls))
                self.assertEqual(driver.schedule['requests']['selection']['incarnation'], h.NAMESPACE)

    def test_existing_namespace_is_not_adopted_or_mutated(self):
        driver, calls, boundary = self._exercise(existing=[{'store_incarnation': 'foreign'}])
        with boundary, self.assertRaisesRegex(ValueError, 'E_HARNESS_NAMESPACE_EXISTING'):
            driver.bootstrap_namespace()
        self.assertTrue(all(sql.startswith('SELECT') for sql in calls))


class OperationPropagationRegressionTests(unittest.TestCase):
    def test_actual_alice_request_identity_reaches_schedule_and_barrier(self):
        driver = h.live_driver(Path(tempfile.mkdtemp(prefix='operation-retained-')))
        with h.patched_subprocess(controller):
            handle = driver.start_alice(driver.schedule['phases']['alice_arm']['batch'])
        actual = json.loads(handle['spec_path'].read_text())['request']['operation_id']
        self.assertEqual(driver.schedule['operation_ids']['alice'], actual)
        self.assertEqual(driver.schedule['identities']['stale_operation_ids'], [actual])
        self.assertEqual(driver.schedule['requests']['alice_title']['operation_id'], actual)
        driver._barrier_session = lambda: 'session-1'
        driver._clock = lambda: h.BARRIER_AUTH
        self.assertEqual(driver.wait_barrier(handle, 1)['operation_id'], actual)
        from hybrid_bridge.practical_sql import _text
        self.assertIn(_text(actual), handle['batch'])

    def test_wrong_or_missing_worker_operation_identity_is_not_consumed(self):
        for operation_id in ('wrong-operation', None):
            with self.subTest(operation_id=operation_id):
                root = Path(tempfile.mkdtemp(prefix='wrong-operation-retained-'))
                driver = h.live_driver(root)
                driver._clock = lambda: h.BARRIER_RESUME
                driver.alice_outcome_path = root / 'worker.json'
                driver.alice_outcome_path.write_text(json.dumps({
                    'operation_id': operation_id, 'outcome': 'APPLIED',
                    'refusal': {'by': 'fence', 'code': 'caller-made'}}))
                outcome = driver.resume_alice({'process': None})
                self.assertIsNone(outcome['outcome'])
                self.assertEqual(outcome['code'], 'E_HARNESS_ALICE_OPERATION_ID')
                self.assertNotEqual(controller._refusal_from_alice(outcome)['by'], 'fence')


class ObservationContractRegressionTests(unittest.TestCase):
    physical = ['issues', 'leases', 'dependencies', 'mi_practical_v2_grants',
                'mi_practical_v2_grant_history', 'mi_practical_v2_current_grants',
                'mi_practical_v2_metadata', 'mi_practical_v2_token_history',
                'mi_practical_v2_operations']

    def _identity(self, tables=None, beads=False):
        from hybrid_bridge.practical_contract import LeasePracticalSelection
        driver = h.live_driver(Path(tempfile.mkdtemp(prefix='identity-retained-')),
                               engine=controller.ENGINE_BEADS if beads else controller.ENGINE_SYNTHETIC)
        selected = LeasePracticalSelection.from_value(driver.schedule['requests']['selection'])
        metadata = dict(h.metadata_row(), selection_digest=selected.digest)

        def run(argv, **kwargs):
            sql = argv[-1]
            if 'information_schema.tables' in sql:
                if 'COUNT(*)' in sql:
                    return h.StubRun(h.rows_packet({'issues_present': 1} if 'issues_present' in sql
                                                   else {'leases_present': 1}))
                return h.StubRun(h.rows_packet(*[{'observed_table': name}
                                                 for name in (tables if tables is not None else self.physical)]))
            if 'VERSION()' in sql:
                return h.StubRun(h.rows_packet({'observed_version': 'TEST_ONLY_VERSION'}))
            if 'DATABASE() AS observed_database' in sql:
                return h.StubRun(h.rows_packet({'observed_database': 'mipx',
                                               'observed_branch': 'main', 'observed_utc': h.AUTH}))
            return h.StubRun(h.rows_packet(metadata))

        with h.patched_subprocess(controller, run=run):
            return driver.store_identity()

    def test_actual_store_identity_physical_names_satisfy_verifier(self):
        evidence = h.clean_evidence()
        evidence['store'] = self._identity()
        self.assertEqual(set(evidence['store']['schema_tables']), set(self.physical))
        self.assertNotIn('IDENTITY_UNVERIFIED', h.codes(verify.judge_evidence(evidence)))

    def test_actual_nested_beads_identity_shape_reaches_verifier(self):
        evidence = h.clean_evidence()
        evidence['runtime'].update(engine=controller.ENGINE_BEADS,
                                   evidence_class=controller.EVIDENCE_CLASS_BEADS)
        evidence['store'] = self._identity(beads=True)
        self.assertNotIn('IDENTITY_UNVERIFIED', h.codes(verify.judge_evidence(evidence)))

    def test_missing_physical_table_or_logical_aliases_cannot_pass(self):
        cases = [self.physical[:-1], list(verify.TABLE_KEYS), self.physical + ['issues'],
                 self.physical + [None]] + [
                    [name for name in self.physical if name != absent] for absent in self.physical]
        for tables in cases:
            with self.subTest(tables=tables):
                evidence = h.clean_evidence()
                evidence['store'] = self._identity(tables=tables)
                self.assertIn('IDENTITY_UNVERIFIED', h.codes(verify.judge_evidence(evidence)))

    def test_backend_receipt_state_is_distinct_from_companion_terminal(self):
        evidence = h.clean_evidence()
        evidence['operations'][h.OP_WIN]['result'] = 'WORKING_SET_APPLIED'
        self.assertNotIn('OBSERVATION_INCOMPLETE', h.codes(verify.judge_evidence(evidence)))

    def test_duplicate_operation_rows_are_not_collapsed(self):
        driver = h.live_driver(Path(tempfile.mkdtemp(prefix='duplicate-record-retained-')))
        row = dict(store_incarnation=h.NAMESPACE, operation_id=h.OP_WIN,
                   command_digest='f' * 64, authorization_time=h.AUTH,
                   resulting_row_lock=h.TOKEN_AFTER,
                   receipt_json=json.dumps({'status': 'WORKING_SET_APPLIED'}))
        with h.patched_subprocess(controller, run=lambda a, **k: h.StubRun(h.rows_packet(row, row))):
            with self.assertRaisesRegex(ValueError, 'E_HARNESS_OPERATION_IDENTITY'):
                driver.operation_records()


class SharedTransferInvariantRegressionTests(unittest.TestCase):
    def test_s1_missing_each_successor_lease_field_never_passes(self):
        for field in ('lease_node', 'lease_granted_at', 'lease_expiry', 'lease_heartbeat'):
            with self.subTest(field=field):
                driver = h.ScriptedDriver()
                driver.evidence['observations']['after_transfer']['grants'][1].pop(field)
                result = controller.run_race(h.build_schedule(), driver=driver)
                self.assertIn('GRANT_LEASE_FACTS_INCOMPLETE', h.codes(result))
                self.assertNotEqual(result['verdict'], verify.PASSED)


class FullSequenceOfflineTests(unittest.TestCase):
    """Actual connected orchestration, with only native boundaries modeled."""

    def _run(self, fault=None):
        import copy
        from unittest.mock import patch
        from hybrid_bridge.practical_lease_backend import DOLT_PIN
        from tests_v2.practical_race_transport_model import StatefulNativeTransport
        root = Path(tempfile.mkdtemp(prefix='full-sequence-retained-'))
        schedule = h.build_schedule()
        schedule['requests']['selection'].update(
            scratch_root=str(root), dolt_executable=str(root / 'dolt.exe'), dolt_sha256=DOLT_PIN)
        model = StatefulNativeTransport(root, schedule, fault)
        driver = controller._LiveDriver(schedule, spawn=model.spawn, stop_grace_seconds=0.01)
        self.addCleanup(lambda: driver._cm_db.close() if driver._cm_db is not None else None)
        with model, patch.object(verify, 'judge_evidence', wraps=verify.judge_evidence) as judge:
            result = controller.run_race(schedule, driver=driver)
            evidence = copy.deepcopy(judge.call_args.args[0]) if judge.called else None
            canonical_calls = judge.call_count
        errors = [handle.error for handle in model.handles if handle.error]
        trace = dict(TEST_ONLY=True, native_sql_execution_proved=False, fault=fault,
                     canonical_calls=canonical_calls, result=result, evidence=evidence,
                     selection=copy.deepcopy(schedule['requests']['selection']),
                     native_boundary_trace=model.trace, dispatched_operations=model.dispatches)
        (root / 'connected-trace.json').write_text(json.dumps(trace, indent=2), encoding='utf-8')
        self.assertEqual(errors, [], errors)
        return result, evidence, model, driver

    def test_complete_uncertain_sequence_reaches_only_execution_cause_uncertainty(self):
        result, evidence, model, driver = self._run('unrelated_transport_failure')
        self.assertIsNotNone(evidence, result)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE, result)
        self.assertEqual(h.codes(result), {'REFUSAL_UNKNOWN'}, result)
        self.assertEqual(evidence['refusal'], {
            'by': None, 'code': 'E_HARNESS_EXECUTION_CAUSE_UNPROVEN'})
        self.assertTrue(result['stopped'])
        namespace = evidence['store']['namespace']
        self.assertEqual(namespace, model.minted)
        self.assertEqual(driver._consumer._backend.selection.incarnation, namespace)
        self.assertEqual(evidence['store']['schema_tables'], sorted(model.tables))
        op = driver.alice_request.operation_id
        self.assertEqual(evidence['identities']['stale_operation_ids'], [op])
        self.assertEqual(evidence['barrier']['operation_id'], op)
        self.assertEqual(evidence['cm']['dispatch_counts'][op], 1)
        self.assertEqual(evidence['cm']['history'][op][-1], verify.CM_UNKNOWN)
        mutations = [row for row in model.trace if row['event'] == 'mutation']
        bindings = [row['binding'] for row in mutations] + [model.pending[0]]
        self.assertEqual({row['store_incarnation'] for row in bindings}, {namespace})
        self.assertEqual({row['selection_digest'] for row in bindings},
                         {driver._consumer._backend.selection.digest})
        self.assertEqual({row['task_id'] for row in bindings}, {h.TASK})
        self.assertEqual(len({row['operation_id'] for row in bindings}), 4)
        self.assertEqual(set(evidence['operations']),
                         {row['operation_id'] for row in evidence['observations']['final']['operations']})
        self.assertNotIn('op-positive-' + driver.run_id, evidence['operations'])

    def test_missing_execution_cause_remains_inconclusive_at_canonical_verifier(self):
        result, evidence, model, driver = self._run('missing_execution_cause')
        self.assertIsNotNone(evidence, result)
        self.assertEqual(result['verdict'], verify.INCONCLUSIVE, result)
        self.assertEqual(h.codes(result), {'REFUSAL_UNKNOWN'}, result)

    def test_full_sequence_faults_cannot_pass(self):
        cases = [
            ('foreign_namespace', {'IDENTITY_UNVERIFIED'}),
            ('wrong_worker_operation', {'REFUSAL_UNKNOWN'}),
            ('missing_physical_table', {'IDENTITY_UNVERIFIED'}),
            ('backend_companion_status_confusion', {'OBSERVATION_INCOMPLETE'}),
            ('invalid_s1', {'WINNER_STATE_LOST'}),
            ('invalid_s1_lease', {'GRANT_LEASE_FACTS_MISMATCH', 'GRANT_LEASE_FACTS_INCOMPLETE'}),
            ('stale_effect', {'STALE_COMMITTED_EFFECT', 'STALE_BACKEND_SUCCESS_RECORD'}),
            ('stale_success_record', {'STALE_BACKEND_SUCCESS_RECORD'}),
            ('missing_history', {'GRANT_HISTORY_INCOMPLETE'}),
            ('ineffective_positive_control', {'CONTROL_INEFFECTIVE'}),
            ('ineffective_disabled_control', {'CONTROL_NOT_EXECUTED'}),
            ('failed_cleanup', {'HARNESS_ERROR'}),
            ('missing_receipt', {'HARNESS_ERROR', 'OBSERVATION_INCOMPLETE'}),
            ('contradictory_receipt', {'HARNESS_ERROR', 'OBSERVATION_INCOMPLETE'}),
            ('duplicate_dispatch', {'DUPLICATE_DISPATCH'}),
            ('missing_s1_operation', {'OPERATION_RECORD_DISAGREEMENT', 'OBSERVATION_INCOMPLETE'}),
        ]
        for fault, expected in cases:
            with self.subTest(fault=fault):
                result, evidence, model, driver = self._run(fault)
                self.assertNotEqual(result['verdict'], verify.PASSED, result)
                self.assertTrue(h.codes(result) & expected, result)
                if fault in ('invalid_s1', 'stale_effect', 'stale_success_record'):
                    self.assertEqual(result['verdict'], verify.FAILED, result)

    def test_existing_backend_and_companion_bindings_reach_canonical_evidence(self):
        result, evidence, model, driver = self._run('missing_execution_cause')
        self.assertEqual(h.codes(result), {'REFUSAL_UNKNOWN'}, result)
        op = evidence['identities']['winner_operation_ids'][0]
        record = evidence['operations'][op]
        self.assertIn('receipt', record)
        self.assertEqual(record['receipt']['status'], verify.BACKEND_APPLIED)
        self.assertEqual(record['binding']['operation_id'], op)
        self.assertEqual(record['receipt']['backend_operation_id'], op)
        self.assertEqual(driver.schedule['requests']['bob_reassign']['command_digest'],
                         record['binding']['command_digest'])
        from hybrid_bridge.practical_sql import _text
        self.assertIn(_text(evidence['store']['namespace']),
                      driver.schedule['phases']['bob_arm']['batch'])
        for binding in evidence['cm']['bindings'][op]:
            self.assertEqual(binding['backend_operation_id'], op)
            self.assertEqual(binding['command_digest'], record['binding']['command_digest'])
            self.assertEqual(binding['selection_digest'], evidence['store']['selection_digest'])
        self.assertEqual(evidence['cm']['internal_chain'], 'VERIFIED')
        self.assertIn('alice', evidence)
        self.assertEqual(evidence['alice']['operation_id'], driver.alice_request.operation_id)
        self.assertEqual(evidence['alice']['outcome'], 'UNKNOWN')
        self.assertEqual([row['kind'] for row in evidence['cm']['events'][op]],
                         evidence['cm']['history'][op])

    def test_duplicate_alice_start_is_refused_without_repeating_uncertain_mutation(self):
        result, evidence, model, driver = self._run('missing_execution_cause')
        with self.assertRaisesRegex(ValueError, 'E_HARNESS_ALICE_ALREADY_STARTED'):
            driver.start_alice(driver.schedule['phases']['alice_arm']['batch'])
        self.assertEqual(model.dispatches.count(driver.alice_request.operation_id), 1)
        self.assertEqual(evidence['cm']['dispatch_counts'][driver.alice_request.operation_id], 1)

    def test_owned_companion_connection_is_closed_after_sequence(self):
        import sqlite3
        result, evidence, model, driver = self._run('missing_execution_cause')
        self.assertTrue(result['stopped'])
        with self.assertRaises(sqlite3.ProgrammingError):
            driver._cm_db.execute('SELECT 1')


class AdditionalScriptedTransferInvariantTests(unittest.TestCase):
    """Narrow invariant fixtures; these do not exercise the full sequence."""

    def test_s1_open_status_is_an_observed_unsafe_transfer(self):
        driver = h.ScriptedDriver()
        driver.evidence['observations']['after_transfer']['issues'][0]['status'] = 'open'
        result = controller.run_race(h.build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.FAILED, result)
        self.assertIn('WINNER_STATE_LOST', h.codes(result))

    def test_s1_pointer_revision_and_foreign_grant_are_checked(self):
        for table, field, value in [('current_grants', 'current_revision', 900),
                                     ('grants', 'task_id', 'another-task')]:
            with self.subTest(table=table):
                driver = h.ScriptedDriver()
                index = 1 if table == 'grants' else 0
                driver.evidence['observations']['after_transfer'][table][index][field] = value
                result = controller.run_race(h.build_schedule(), driver=driver)
                self.assertNotEqual(result['verdict'], verify.PASSED)


class CompleteTransferRelationshipTests(unittest.TestCase):
    def test_s1_winner_operation_must_match_the_same_boundary(self):
        for value in ([], [dict(h.state_final()['operations'][0], command_digest='a' * 64)]):
            with self.subTest(value=value):
                driver = h.ScriptedDriver()
                driver.evidence['observations']['after_transfer']['operations'] = value
                result = controller.run_race(h.build_schedule(), driver=driver)
                self.assertNotEqual(result['verdict'], verify.PASSED, result)

    def test_transfer_relationships_are_required_in_both_phases(self):
        cases = [('metadata', 0, 'store_incarnation', 'foreign-store'),
                 ('metadata', 0, 'selection_digest', 'a' * 64),
                 ('grants', 0, 'actor', 'changed-prior-actor'),
                 ('grants', 1, 'fixed_deadline_utc', '2026-10-14 10:06:00.000000'),
                 ('grants', 1, 'lease_node', None),
                 ('grant_history', 0, 'grant_id', 'foreign-grant'),
                 ('token_history', 0, 'operation_id', 'foreign-operation')]
        import copy
        for phase in ('after_transfer', 'final'):
            for table, index, field, value in cases:
                with self.subTest(phase=phase, table=table, field=field):
                    driver = h.ScriptedDriver()
                    # Both committed phases start with complete observations.
                    driver.evidence['observations']['after_transfer'] = copy.deepcopy(h.state_final())
                    state = driver.evidence['observations'][phase]
                    state[table][index][field] = value
                    result = controller.run_race(h.build_schedule(), driver=driver)
                    self.assertNotEqual(result['verdict'], verify.PASSED, result)

    def test_baseline_claim_history_cannot_disappear(self):
        driver = h.ScriptedDriver()
        baseline = dict(store_incarnation=h.NAMESPACE, grant_id=h.GRANT_OLD,
                        event_kind='INITIAL_CLAIM', event_utc=h.GRANTED_AT)
        driver.evidence['observations']['before']['grant_history'].append(baseline)
        result = controller.run_race(h.build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.FAILED, result)
        self.assertIn('ROW_LOST', h.codes(result))

    def test_unsafe_s1_survives_later_receipt_collection_error(self):
        driver = h.ScriptedDriver(operation_records=ValueError('E_TEST_READBACK_UNAVAILABLE'))
        driver.evidence['observations']['after_transfer']['issues'][0]['title'] = h.TITLE_STALE
        result = controller.run_race(h.build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.FAILED, result)
        self.assertIn('STALE_COMMITTED_EFFECT', h.codes(result))

    def test_duplicate_rows_cannot_hide_an_unsafe_second_observation(self):
        import copy
        driver = h.ScriptedDriver()
        row = copy.deepcopy(driver.evidence['observations']['after_transfer']['issues'][0])
        row['title'] = h.TITLE_STALE
        driver.evidence['observations']['after_transfer']['issues'].append(row)
        result = controller.run_race(h.build_schedule(), driver=driver)
        self.assertEqual(result['verdict'], verify.FAILED, result)
        self.assertIn('DUPLICATE_ROW_IDENTITY', h.codes(result))
