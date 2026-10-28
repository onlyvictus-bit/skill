"""Pure SR3c coordinator guards; these tests never start a selected runtime."""
import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).absolute().parents[1] / 'scripts/shutdown_repair_verification.py'
spec = importlib.util.spec_from_file_location('sr3_verification_test', SCRIPT)
sr3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sr3)


class CoordinatorGuards(unittest.TestCase):
    def complete_row(self, code=0):
        return {'exit_code': code, 'execution': 'EXITED', 'failure': None,
                'containment': {'timed_out': False, 'capture_complete': True, 'tree_contained': True,
                                'capture_errors': [], 'output_limit_exceeded': False}}

    def test_budgets_are_exact_and_unchanged(self):
        sr3.validate_budgets(dict(sr3.BUDGETS))
        changed = dict(sr3.BUDGETS); changed['public'] = 91
        with self.assertRaisesRegex(ValueError, 'E_SR3_BUDGET'):
            sr3.validate_budgets(changed)

    def test_capture_setup_timeout_or_lost_tree_never_becomes_success(self):
        row = self.complete_row()
        sr3.validate_capture(SimpleNamespace(returncode=0), row)
        for key, value in (('timed_out', True), ('capture_complete', False), ('tree_contained', False)):
            broken = self.complete_row(); broken['containment'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'E_SR3_CAPTURE_INCOMPLETE'):
                sr3.validate_capture(SimpleNamespace(returncode=0), broken)
        with self.assertRaisesRegex(ValueError, 'E_SR3_CAPTURE_INCOMPLETE'):
            sr3.validate_capture(None, self.complete_row())

    def test_complete_nonzero_is_distinct_from_incomplete_capture(self):
        row = self.complete_row(1)
        sr3.validate_capture(SimpleNamespace(returncode=1), row, exits=(1,))
        with self.assertRaisesRegex(ValueError, 'E_SR3_CHILD_EXIT'):
            sr3.validate_capture(SimpleNamespace(returncode=1), row)

    def test_suite_requires_exact_discovery_results_and_no_skips(self):
        expected = ('test_a.test_one', 'test_a.test_two')
        receipt = {'discovered': 2, 'tests_run': 2, 'failures': [], 'errors': [], 'skipped': [],
                   'excluded': [], 'expected_failures': [], 'interrupted': False}
        sr3.validate_suite(receipt, expected)
        for key, value in (('skipped', [['test_a.test_two', 'POSIX']]), ('excluded', ['x'])):
            broken = dict(receipt); broken[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'E_SR3_SUITE_ACCOUNTING'):
                sr3.validate_suite(broken, expected)

    def test_stage_requires_every_group_and_preservation(self):
        groups = [{'label':name, 'passed': True, 'receipt': {'sha256': 'a'}, 'cases': {'sha256': 'b'}} for name,_,_ in sr3.GROUPS]
        self.assertTrue(sr3.validate_stage(groups, True, True))
        for candidate, preserved in (([], True), (groups, False), ([{'passed': False}], True)):
            with self.subTest(candidate=candidate, preserved=preserved), self.assertRaisesRegex(ValueError, 'E_SR3_STAGE'):
                sr3.validate_stage(candidate, preserved)

    def test_source_discovery_requires_unique_unittest_ids(self):
        self.assertEqual(sr3.validate_discovery(['test_x.X.test_one'], 'test_x.py'), ('test_x.X.test_one',))
        for value in ([], ['test_x.X.test_one', 'test_x.X.test_one'], ['not-a-test']):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'E_SR3_DISCOVERY_SOURCE'):
                sr3.validate_discovery(value, 'test_x.py')

    def test_ordered_accounting_requires_the_retained_all_pass_verdict(self):
        unit = {'discovered': 1, 'tests_run': 1, 'failures': [], 'errors': [], 'skipped': [],
                'excluded': [], 'expected_failures': [], 'interrupted': False}
        report = {'gate1_complete': False, 'observation_only': True}
        accepted = SimpleNamespace(TARGET='test_x.X.test_one',
                                   validate_ordered_result=lambda value: 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE')
        self.assertEqual(sr3.validate_ordered(report, unit, accepted), 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE')
        refused = SimpleNamespace(TARGET='test_x.X.test_one',
                                  validate_ordered_result=lambda value: 'ORDERED_FAILURE_REQUIRES_DETAIL_REVIEW')
        with self.assertRaisesRegex(ValueError, 'E_SR3_ORDERED_RESULT'):
            sr3.validate_ordered(report, unit, refused)

    def test_contract_flags_are_explicitly_fail_closed(self):
        self.assertIn('stage_complete', sr3.FLAGS)
        self.assertIn('gate1_complete', sr3.FLAGS)
        self.assertEqual(sr3.OUTPUT.name, 'sr3-normal')
        self.assertEqual(sr3.CONTROLLER, Path(r'C:\Python314\python.exe'))

    def test_saved_group_plan_round_trips_and_uses_selected_runtime(self):
        groups = sr3.group_plan()
        self.assertEqual(json.loads(json.dumps(groups)), groups)
        worker = Path('selected-312.exe')
        self.assertEqual(sr3.test_argv(worker, Path('runner.py'), Path('source'), 'test_x.py', Path('out'))[0], worker)
        self.assertTrue(all(group[2] == 60 for group in groups))
        self.assertIn('memory-integrity/tests_v2/test_knowledge_process_lifecycle.py', sr3.LIVE_DELTA)

    def test_stage_cannot_close_with_one_group_or_without_ordered_replay(self):
        groups = [{'label': name, 'passed': True, 'receipt': {'sha256':'a'}, 'cases': {'sha256':'b'}}
                  for name, _, _ in sr3.GROUPS]
        self.assertTrue(sr3.validate_stage(groups, True, True))
        for items, ordered in ((groups[:-1], True), (groups, False), (groups+groups[:1], True)):
            with self.subTest(items=items, ordered=ordered), self.assertRaisesRegex(ValueError, 'E_SR3_STAGE'):
                sr3.validate_stage(items, True, ordered)

    def test_runtime_source_hashes_are_sealed_not_observed_as_new_baseline(self):
        with patch.object(sr3, 'SEALED_SOURCES', {'a.py':'a'*64}):
            sr3.validate_source_seals({'a.py':{'sha256':'a'*64}})
            for changed in ({'a.py':{'sha256':'b'*64}}, {'a.py':{'sha256':'a'*64}, 'surprise.py':{'sha256':'c'*64}}):
                with self.assertRaisesRegex(ValueError, 'E_SR3_UNREVIEWED_SOURCE'):
                    sr3.validate_source_seals(changed)

    def test_preparation_failure_is_retained_and_cannot_be_retried(self):
        with tempfile.TemporaryDirectory(prefix='sr3-prepare-fault-') as name:
            root = Path(name)
            with patch.object(sr3, 'ROOT', root), patch.object(sr3, 'PREPARATION', root/'prepare'), \
                 patch.object(sr3, 'CONTRACT', root/'Inputs.json'), \
                 patch.object(sr3, 'load_module', return_value=SimpleNamespace(normal_account=lambda:None)), \
                 patch.object(sr3, 'build_contract', side_effect=OSError('CONTROL_PRIVATE_INPUT_DENIED')) as build:
                with self.assertRaisesRegex(OSError, 'CONTROL_PRIVATE_INPUT_DENIED'): sr3.prepare()
                failure = json.loads((root/'prepare/Failure.json').read_bytes())
                self.assertIn('CONTROL_PRIVATE_INPUT_DENIED', failure['failure'])
                self.assertFalse(failure['stage_complete'])
                self.assertFalse((root/'Inputs.json').exists())
                with self.assertRaisesRegex(ValueError, 'E_SR3_PREPARATION_CONSUMED'): sr3.prepare()
                self.assertEqual(build.call_count, 1)

    def test_protected_delta_cannot_delete_or_change_unapproved_input(self):
        old = {'keep':'a', 'approved':'old'}
        sr3.validate_protected_delta(old, {'keep':'a', 'approved':'new', 'new-file':'x'}, {'approved','new-file'})
        for current in ({'approved':'new'}, {'keep':'changed', 'approved':'new'}, {'keep':'a','approved':'old','surprise':'x'}):
            with self.subTest(current=current), self.assertRaisesRegex(ValueError, 'E_SR3_UNAPPROVED_PROTECTED_DELTA'):
                sr3.validate_protected_delta(old, current, {'approved','new-file'})

    def test_old_baselines_and_consumed_stack_are_fixed_required_inputs(self):
        self.assertEqual(sr3.OLD_SEALS[sr3.BEFORE.relative_to(sr3.REPO).as_posix()],
                         '4da04f0fdb6b80ee0c79e1cdc4802f0bd73c9dd7f2fdf7e0e9c10ac04c1e745f')
        self.assertEqual(sr3.OLD_SEALS[sr3.PARENT_INPUTS.relative_to(sr3.REPO).as_posix()],
                         '5bc5788cd7a21af47e3a305bd3352b27a4cead6ae46d22dbce9eb748aef6f1ed')
        self.assertIn('cleanup-lifetime-stack-20261024', {path.name for path in sr3.HISTORY_ROOTS})

    def test_actual_committed_source_copy_contains_only_exact_named_live_delta(self):
        path = sr3.REPO/'.github/scripts/gate1_current_preflight.py'
        c1 = sr3.load_module(path, {'sha256':sr3.C1_SHA, 'size':path.stat().st_size})
        basis, tree = sr3.source_basis(c1)
        value = {'tree':tree, 'live_delta':{name:sr3.record(sr3.REPO/name) for name in sr3.LIVE_DELTA}}
        with tempfile.TemporaryDirectory(prefix='sr3-real-source-copy-') as name:
            copied = Path(name)/'source'
            actual = sr3.copy_source(c1, value, copied)
            expected = dict(basis)
            expected.update({name:row['sha256'] for name,row in value['live_delta'].items()})
            self.assertEqual(actual, expected)
            c1.verify_source(copied, expected)
            for name in sr3.LIVE_DELTA:
                self.assertEqual((copied/name).read_bytes(), (sr3.REPO/name).read_bytes())

    def test_public_helpers_cannot_rebaseline_themselves_before_preparation(self):
        for name in ('.github/scripts/gate1_ordered_runner.py', '.github/scripts/gate1_ordered_diagnostic.py'):
            with self.subTest(name=name):
                records = {key:{'sha256':value} for key,value in sr3.SUPPORT_SEALS.items()}
                sr3.validate_support_seals(records)
                records[name]['sha256'] = '0'*64
                with self.assertRaisesRegex(ValueError, 'E_SR3_SUPPORT_SEAL'):
                    sr3.validate_support_seals(records)


if __name__ == '__main__':
    unittest.main()
