"""SR4 ownership-only handoff controls; no selected runtime or old phase runs."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).absolute().parents[1] / 'scripts/shutdown_startup_successor.py'


class StartupHandoffGuards(unittest.TestCase):
    def helper(self):
        self.assertTrue(SCRIPT.exists(), 'SR4 bounded startup successor is not implemented')
        spec = importlib.util.spec_from_file_location('sr4_handoff_test', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def unit(self):
        return {'discovered': 2, 'tests_run': 2, 'failures': [], 'errors': [],
                'skipped': [], 'excluded': [], 'expected_failures': [], 'interrupted': False}

    def roles(self):
        return {'image': r'C:\Store\python3.12.exe', 'sys_executable': r'C:\venv\Scripts\python.exe',
                'prefix': r'C:\venv', 'base_prefix': r'C:\Store',
                'base_executable': r'C:\WindowsApps\python.exe', 'launcher': None}

    def observation(self):
        expected = {**self.roles(), 'token': 'a' * 64}
        observed = {**expected, 'pid': 99, 'in_any_job': True}
        return {'expected': expected, 'observed': observed,
                'termination': {'mode': 'graceful', 'native_exit_proved': True,
                                'records': 1, 'accounting_total': 1, 'operations': [],
                                'failures': []}, 'released': True}

    def case_files(self, m, root, *, failed=False):
        log = root / 'unittest.log'; log.write_text('CONTROL_ACTUAL_TRACE\n', encoding='utf-8')
        unit = self.unit()
        unit.update(log=str(log), log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
        if failed:
            unit['errors'] = ['test_a.A.test_one']
        m.save(root / 'Receipt.json', unit)
        scratch = root / 'retained-temp'; scratch.mkdir()
        m.save(scratch / 'SR4-Actual-Startup.json', self.observation())
        return unit

    def test_discovery_must_match_all_reviewed_ids_exactly(self):
        m = self.helper(); expected = ['test_a.A.test_one', 'test_b.B.test_two']
        self.assertEqual(m.validate_cases(expected, expected), expected)
        for value in ([], expected[:1], expected + expected[:1], expected[::-1],
                      expected + ['test_x.X.test_extra']):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'E_SR4_CASES'):
                m.validate_cases(value, expected)

    def test_skips_exclusions_errors_incomplete_or_boolean_counts_are_refused(self):
        m = self.helper(); ids = ['test_a.A.test_one', 'test_b.B.test_two']
        m.validate_unit(self.unit(), ids)
        for key, value in (('skipped', [['x', 'skip']]), ('excluded', ['x']), ('errors', ['x']),
                           ('failures', ['x']), ('expected_failures', ['x']),
                           ('interrupted', True), ('tests_run', 1), ('discovered', True)):
            row = self.unit(); row[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'E_SR4_UNIT'):
                m.validate_unit(row, ids)

    def test_distinct_base_and_loaded_image_roles_are_preserved(self):
        m = self.helper()
        m.validate_actual_startup(self.observation(), self.roles())
        self.assertNotEqual(self.observation()['observed']['base_executable'], self.roles()['image'])

    def test_forged_child_role_token_job_and_pid_are_refused(self):
        m = self.helper()
        for field, value in (('base_executable', self.roles()['image']), ('image', r'C:\other\python.exe'),
                             ('token', 'b' * 64), ('in_any_job', False), ('pid', True)):
            row = self.observation(); row['observed'][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'E_SR4_STARTUP'):
                m.validate_actual_startup(row, self.roles())

    def test_native_exit_and_release_must_both_be_proved(self):
        m = self.helper()
        for field in ('native_exit_proved', 'released'):
            row = self.observation()
            if field == 'released': row[field] = False
            else: row['termination'][field] = False
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'E_SR4_STARTUP'):
                m.validate_actual_startup(row, self.roles())

    def test_startup_frame_rejects_missing_or_unexpected_identity_and_cleanup_fields(self):
        m = self.helper()
        for section, field in (('observed', 'prefix'), ('expected', 'token'),
                               ('termination', 'native_exit_proved')):
            row = self.observation(); del row[section][field]
            with self.subTest(section=section, field=field), self.assertRaisesRegex(ValueError, 'E_SR4_STARTUP'):
                m.validate_actual_startup(row, self.roles())
        row = self.observation(); row['termination']['unbounded'] = True
        with self.assertRaisesRegex(ValueError, 'E_SR4_STARTUP'):
            m.validate_actual_startup(row, self.roles())

    def test_ownership_success_never_claims_stage_gate1_or_preservation(self):
        m = self.helper(); ids = ['test_a.A.test_one', 'test_b.B.test_two']
        row = m.ownership_result(self.unit(), ids, self.observation(), self.roles())
        self.assertEqual(row['status'], 'SR4_OWNERSHIP_OBSERVED_NOT_STAGE_COMPLETE')
        self.assertTrue(row['ownership_observed'])
        for key in ('stage_complete', 'gate1_complete', 'release_ready', 'installed',
                    'producer_authentication', 'preservation'):
            self.assertIs(row[key], False)

    def test_result_refuses_startup_proof_when_case_accounting_is_not_exact(self):
        m = self.helper(); ids = ['test_a.A.test_one', 'test_b.B.test_two']
        row = self.unit(); row['tests_run'] = 1
        with self.assertRaisesRegex(ValueError, 'E_SR4_UNIT'):
            m.ownership_result(row, ids, self.observation(), self.roles())

    def test_existing_output_cannot_be_reused_even_after_failure(self):
        m = self.helper()
        with tempfile.TemporaryDirectory(prefix='sr4-existing-') as name:
            path = Path(name) / 'already-used'; path.mkdir()
            (path / 'Failure.json').write_text('{"failed":true}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'E_SR4_EXISTING'):
                m.require_absent(path)
            self.assertEqual(json.loads((path / 'Failure.json').read_text()), {'failed': True})

    def test_bad_source_seal_prevents_module_execution(self):
        m = self.helper()
        with tempfile.TemporaryDirectory(prefix='sr4-module-') as name:
            path = Path(name) / 'not-trusted.py'
            path.write_text('raise RuntimeError("MUST_NOT_EXECUTE")', encoding='utf-8')
            with self.assertRaises(ValueError):
                m.load_checked(path, '0' * 64)

    def test_prepare_wrong_account_refuses_before_creating_output(self):
        m = self.helper()
        with tempfile.TemporaryDirectory(prefix='sr4-account-') as name:
            root = Path(name) / 'absent'
            with patch.object(m, 'ROOT', root), patch.object(m, 'normal', side_effect=ValueError('CONTROL_ACCOUNT')):
                with self.assertRaisesRegex(ValueError, 'CONTROL_ACCOUNT'):
                    m.prepare('a' * 64)
            self.assertFalse(root.exists())

    def test_source_authority_failure_precedes_output_and_claim(self):
        m = self.helper()
        with tempfile.TemporaryDirectory(prefix='sr4-authority-') as name:
            root = Path(name) / 'absent'
            with patch.object(m, 'ROOT', root), patch.object(m, 'normal'), \
                 patch.object(m, 'build_contract', side_effect=ValueError('CONTROL_SOURCE_CHANGED')):
                with self.assertRaisesRegex(ValueError, 'CONTROL_SOURCE_CHANGED'):
                    m.prepare('a' * 64)
            self.assertFalse(root.exists())

    def test_prepare_requires_external_contract_seal_before_any_output(self):
        m = self.helper()
        with tempfile.TemporaryDirectory(prefix='sr4-contract-') as name:
            root = Path(name) / 'absent'
            with patch.object(m, 'ROOT', root), patch.object(m, 'normal'), \
                 patch.object(m, 'build_contract', return_value={'fixture': 'not-a-runtime'}):
                with self.assertRaisesRegex(ValueError, 'E_SR4_EXTERNAL_INPUT'):
                    m.prepare('0' * 64)
            self.assertFalse(root.exists())

    def test_wrong_prepared_input_hash_refuses_before_run_claim(self):
        m = self.helper()
        with tempfile.TemporaryDirectory(prefix='sr4-input-') as name:
            root = Path(name); (root / 'Inputs.json').write_text('{}\n', encoding='utf-8')
            with patch.object(m, 'ROOT', root), patch.object(m, 'normal'):
                with self.assertRaisesRegex(ValueError, 'E_SR4_EXTERNAL_INPUT'):
                    m.run('0' * 64)
            self.assertFalse((root / 'Run-Claim.json').exists())

    def test_old_control_hash_cannot_be_replaced_by_fresh_observation(self):
        m = self.helper()
        with tempfile.TemporaryDirectory(prefix='sr4-old-') as name:
            path = Path(name) / 'old.json'; path.write_text('{"changed":true}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'E_SR4_OLD_CONTROL'):
                m.old_record(path, '0' * 64)

    def test_unfrozen_sources_refuse_before_building_inputs(self):
        m = self.helper()
        with patch.object(m, 'SR4_SOURCES', {}):
            with self.assertRaisesRegex(ValueError, 'E_SR4_UNFROZEN'):
                m.build_contract()

    def test_existing_preflight_support_pin_is_exact_and_importable(self):
        m = self.helper()
        self.assertEqual(m.C1_SHA, hashlib.sha256(SCRIPT.with_name('gate1_current_preflight.py').read_bytes()).hexdigest())
        self.assertTrue(callable(m.c1_module().normal_account))

    def test_unit_collection_retains_full_failure_evidence_before_refusing_exit(self):
        m = self.helper()
        self.assertTrue(callable(getattr(m, 'collect_unit', None)), 'unit evidence collector missing')
        with tempfile.TemporaryDirectory(prefix='sr4-failed-unit-') as name:
            root = Path(name); unit = self.case_files(m, root, failed=True); receipt = {}
            with self.assertRaisesRegex(ValueError, 'E_SR4_UNIT'):
                m.collect_unit(root, ['test_a.A.test_one', 'test_b.B.test_two'], self.roles(), receipt, 1)
            self.assertEqual(receipt['unit'], unit)
            self.assertEqual(receipt['unit_log']['sha256'], unit['log_sha256'])
            self.assertEqual(receipt['unit_log_text'], 'CONTROL_ACTUAL_TRACE\n')
            self.assertEqual(receipt['startup'], self.observation())

    def test_unit_collection_preserves_native_proof_and_rejects_duplicate_artifacts(self):
        m = self.helper()
        self.assertTrue(callable(getattr(m, 'collect_unit', None)), 'unit evidence collector missing')
        with tempfile.TemporaryDirectory(prefix='sr4-positive-unit-') as name:
            root = Path(name); self.case_files(m, root); receipt = {}
            m.collect_unit(root, ['test_a.A.test_one', 'test_b.B.test_two'], self.roles(), receipt, 0)
            self.assertEqual(receipt['startup']['termination']['accounting_total'], 1)
            other = root / 'retained-temp' / 'other'; other.mkdir()
            m.save(other / 'SR4-Actual-Startup.json', self.observation())
            with self.assertRaisesRegex(ValueError, 'E_SR4_STARTUP_ARTIFACT'):
                m.collect_unit(root, ['test_a.A.test_one', 'test_b.B.test_two'], self.roles(), {}, 0)

    def test_live_source_guard_rejects_unapproved_source_change(self):
        m = self.helper()
        self.assertTrue(callable(getattr(m, 'verify_live_source', None)), 'live source guard missing')
        with tempfile.TemporaryDirectory(prefix='sr4-source-check-') as name:
            root = Path(name); package = root / 'memory-integrity'; package.mkdir()
            path = package / 'unchanged.py'; path.write_bytes(b'original')
            manifest = {'memory-integrity/unchanged.py': hashlib.sha256(b'original').hexdigest()}
            with patch.object(m, 'REPO', root):
                m.verify_live_source(manifest, {})
                path.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'E_SR4_LIVE_SOURCE'):
                    m.verify_live_source(manifest, {})

    def test_history_critical_records_bind_consumed_failure_not_new_observations(self):
        m = self.helper()
        self.assertTrue(callable(getattr(m, 'history', None)), 'critical old-history guard missing')
        value = m.history(m.c1_module())
        self.assertEqual(value['receipt']['sha256'], 'beab04ef2dde95a01cc25ed21eedf6ff79c3e50c2aceacaf2cd2f74dc4fc76d2')
        self.assertEqual(len(value['commands']), 4)
        self.assertEqual(sum(len(row['streams']) for row in value['commands']), 8)

    def test_claimed_run_failure_is_retained_and_cannot_be_retried(self):
        m = self.helper()
        self.assertTrue(callable(getattr(m, 'execute', None)), 'runtime observation coordinator missing')
        with tempfile.TemporaryDirectory(prefix='sr4-one-shot-') as name:
            root = Path(name); m.save(root / 'Inputs.json', {'fixture': 'guard-only'})
            digest = m.record(root / 'Inputs.json')['sha256']
            with patch.object(m, 'ROOT', root), patch.object(m, 'normal'), \
                    patch.object(m, 'validate_contract'), \
                    patch.object(m, 'execute', side_effect=ValueError('CONTROL_OBSERVATION_FAILURE')):
                result = m.run(digest)
                self.assertFalse(result['ownership_observed'])
                self.assertFalse(result['stage_complete'])
                self.assertIn('CONTROL_OBSERVATION_FAILURE', m.read(root / 'run/Receipt.json')['failure'])
                self.assertTrue((root / 'Run-Claim.json').exists())
                self.assertTrue((root / 'Run-Failure.json').exists())
                with self.assertRaisesRegex(ValueError, 'E_SR4_EXISTING'):
                    m.run(digest)


if __name__ == '__main__':
    unittest.main()
