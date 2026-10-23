"""Real scratch inventories; no selected-runtime or original-data mutation."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]


class CleanupPreservation(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            'cleanup_preservation_subject', ROOT/'.github/scripts/gate1_cleanup_diagnostic.py')
        self.s = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.s)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        s = self.s
        s.g.REPO = self.root/'repo'; s.g.REPO.mkdir()
        s.g.WORKSPACE = self.root/'workspace'; s.g.WORKSPACE.mkdir()
        s.OUTPUT = s.g.WORKSPACE/'diagnostic'
        s.i.OUTPUT = s.g.WORKSPACE/'old-image'; s.i.OUTPUT.mkdir()
        self.keep = s.i.OUTPUT/'retained.log'; self.keep.write_bytes(b'old retained evidence')
        self.cache = s.i.OUTPUT/'cache.db'; self.cache.write_bytes(b'old retained cache')
        s.IMAGE_CONTRACT = self.root/'old-contract.json'
        s.g.save(s.IMAGE_CONTRACT, {})
        s.IMAGE_CONTRACT_SHA = s.g.file_record(s.IMAGE_CONTRACT)['sha256']
        source = s.g.WORKSPACE/'source'; source.mkdir()
        (source/'keep.py').write_bytes(b'original sealed source')
        s.HERE = self.root/'diagnostic-helper.py'
        s.HERE.write_bytes(b'sealed test-owned helper')
        self.doc = {'source': str(source), 'repo': str(s.g.REPO)}
        self.value = {
            'image_bound_records': {str(self.keep): s.g.file_record(self.keep)},
            'image_history_coverage': 'BOUND_RECORDS_ONLY_NOT_FULL_TEMP_TREE',
            'diagnostic_source_manifest': {'keep.py': s.g.sha(b'original sealed source')},
            'helper': s.g.file_record(s.HERE),
        }
        self.contract = self.root/'diagnostic-contract.json'
        s.g.save(self.contract, self.value)
        self.record = s.g.file_record(self.contract)
        self.digest = self.record['sha256']
        # These two existing validators bind the user's real runtime and567-file
        # original source. They are outside this authored two-file guard model.
        # NEW inventory, seal, no-repeat and failure-accounting checks stay real.
        validator = patch.object(s, 'validate_contract', return_value=self.doc)
        old_preservation = patch.object(s.i, 'check_preserved')
        self.addCleanup(validator.stop)
        self.addCleanup(old_preservation.stop)
        validator.start()
        old_preservation.start()

    def test_valid_inventory_is_measured_before_creating_output(self):
        value, doc, before, record = self.s.preflight(self.contract, self.digest)
        self.assertEqual(before, {
            'cache.db': self.s.g.sha(b'old retained cache'),
            'retained.log': self.s.g.sha(b'old retained evidence'),
        })
        self.assertEqual(record, self.record)
        self.assertFalse(self.s.OUTPUT.exists())
        self.assertEqual(self.keep.read_bytes(), b'old retained evidence')

    def test_unreadable_old_file_stops_before_output_and_retains_data(self):
        original = Path.read_bytes
        def read(path):
            if path == self.cache:
                raise PermissionError('synthetic boundary denial: '+str(path))
            return original(path)
        with patch.object(Path, 'read_bytes', read):
            with self.assertRaisesRegex(PermissionError, 'synthetic boundary denial'):
                self.s.preflight(self.contract, self.digest)
        self.assertFalse(self.s.OUTPUT.exists())
        self.assertEqual(self.cache.read_bytes(), b'old retained cache')

    def test_linked_old_evidence_stops_before_output_without_unlinking(self):
        alias = self.s.i.OUTPUT/'cache-alias.db'
        os.link(self.cache, alias)  # New test-owned hardlink, not user evidence.
        with self.assertRaisesRegex(ValueError, 'E_G1_EVIDENCE_LINK'):
            self.s.preflight(self.contract, self.digest)
        self.assertFalse(self.s.OUTPUT.exists())
        self.assertEqual(alias.read_bytes(), b'old retained cache')

    def test_existing_output_is_not_reused_or_removed(self):
        self.s.OUTPUT.mkdir()
        keep = self.s.OUTPUT/'keep'; keep.write_bytes(b'keep previous new attempt')
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_EXISTING_ATTEMPT_PRESERVED'):
            self.s.preflight(self.contract, self.digest)
        self.assertEqual(keep.read_bytes(), b'keep previous new attempt')

    def test_unbound_old_cache_change_is_detected_by_full_start_inventory(self):
        value, doc, before, record = self.s.preflight(self.contract, self.digest)
        self.cache.write_bytes(b'synthetic changed old cache')
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_IMAGE_ATTEMPT_CHANGED'):
            self.s.check_preserved(value, doc, before, record)
        self.assertEqual(self.cache.read_bytes(), b'synthetic changed old cache')

    def test_added_old_file_is_not_hidden_by_only_checking_bound_records(self):
        value, doc, before, record = self.s.preflight(self.contract, self.digest)
        extra = self.s.i.OUTPUT/'unexpected'; extra.write_bytes(b'new old-tree file')
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_IMAGE_ATTEMPT_CHANGED'):
            self.s.check_preserved(value, doc, before, record)
        self.assertEqual(extra.read_bytes(), b'new old-tree file')

    def test_external_contract_drift_is_detected_without_rebaselining(self):
        value, doc, before, record = self.s.preflight(self.contract, self.digest)
        self.contract.write_bytes(b'{"changed":true}')
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_CONTRACT_CHANGED'):
            self.s.check_preserved(value, doc, before, record)
        self.assertEqual(record['sha256'], self.digest)

    def test_helper_drift_after_preflight_cannot_report_preservation(self):
        value, doc, before, record = self.s.preflight(self.contract, self.digest)
        self.s.HERE.write_bytes(b'changed test-owned helper')
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_HELPER_CHANGED'):
            self.s.check_preserved(value, doc, before, record)
        self.assertEqual(self.keep.read_bytes(), b'old retained evidence')

    def test_postcreate_copy_failure_retains_failed_receipt_and_old_bytes(self):
        with patch.dict(os.environ, USERPROFILE=r'C:\Users\sakth'), \
                patch.object(self.s, '_copy_source', side_effect=RuntimeError('synthetic copy failure')):
            code = self.s.run(self.contract, self.digest)
        self.assertNotEqual(code, 0)
        receipt = json.loads((self.s.OUTPUT/'Receipt.json').read_text(encoding='utf-8'))
        self.assertIn('synthetic copy failure', receipt['failure'])
        self.assertFalse(receipt['gate1_complete'])
        self.assertFalse(receipt['fix_validated'])
        self.assertFalse(receipt['retry_authorized'])
        self.assertTrue(receipt['preservation'])
        self.assertEqual(self.keep.read_bytes(), b'old retained evidence')
        self.assertEqual(self.cache.read_bytes(), b'old retained cache')

    def test_original_formatter_negative_control_fails_public_detail_assertion(self):
        # Counterfactual: removing the diagnostic overlay must break the ACTUAL
        # positive public error roundtrip, not merely a source-text assertion.
        spec = importlib.util.spec_from_file_location(
            'cleanup_roundtrip_control', ROOT/'.github/tests/test_gate1_cleanup_diagnostic.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        probe = module.CleanupDiagnosticWorkerContract(
            'test_actual_public_workflow_blocker_retains_the_worker_diagnostic')
        probe.setUp()
        self.addCleanup(probe.doCleanups)
        with patch.object(probe.subject, 'diagnostic_worker_bytes', side_effect=lambda raw: raw):
            with self.assertRaisesRegex(AssertionError, 'GATE1_CLEANUP_DIAGNOSTIC'):
                probe.test_actual_public_workflow_blocker_retains_the_worker_diagnostic()

    def test_changed_start_snapshot_cannot_be_reported_preserved(self):
        def disturb(doc, value, output):
            (output/'Before-Image-Attempt.json').write_bytes(b'changed snapshot')
            raise RuntimeError('synthetic stop after snapshot change')
        with patch.dict(os.environ, USERPROFILE=r'C:\Users\sakth'), \
                patch.object(self.s, '_copy_source', side_effect=disturb):
            self.assertNotEqual(self.s.run(self.contract, self.digest), 0)
        receipt = json.loads((self.s.OUTPUT/'Receipt.json').read_text(encoding='utf-8'))
        self.assertFalse(receipt['preservation'])
        self.assertIn('E_CLEANUP_START_MAP_CHANGED', receipt['preservation_failure'])
        self.assertFalse(receipt['gate1_complete'])

    def preparation_paths(self):
        private = self.s.g.REPO/'.github/run-artifacts/offline-first-20261020'
        private.mkdir(parents=True)
        return private/'Gate1-Cleanup-Diagnostic-Contract-20261021.json', private/'Gate1-Cleanup-Preparation-20261021.json'

    def test_preparation_denied_history_creates_no_inputs_or_attempt(self):
        contract, receipt = self.preparation_paths()
        with patch.object(self.s, 'build_contract', side_effect=PermissionError('historical read denied')):
            with self.assertRaisesRegex(PermissionError, 'historical read denied'):
                self.s.prepare_contract()
        self.assertFalse(contract.exists())
        self.assertFalse(receipt.exists())
        self.assertFalse(self.s.OUTPUT.exists())

    def test_preparation_saves_inputs_only_then_refuses_repetition(self):
        contract, receipt = self.preparation_paths()
        with patch.object(self.s, 'build_contract', return_value=self.value):
            self.assertEqual(self.s.prepare_contract(), 0)
            old_contract, old_receipt = contract.read_bytes(), receipt.read_bytes()
            with self.assertRaisesRegex(ValueError, 'E_CLEANUP_PREPARATION_EXISTS'):
                self.s.prepare_contract()
        report = json.loads(old_receipt)
        self.assertEqual(report['status'], 'INPUT_ONLY_CONTRACT_PREPARED_DIAGNOSTIC_UNRUN')
        self.assertFalse(report['worker_started'])
        self.assertFalse(report['diagnostic_attempt_created'])
        self.assertFalse(self.s.OUTPUT.exists())
        self.assertEqual(contract.read_bytes(), old_contract)
        self.assertEqual(receipt.read_bytes(), old_receipt)

    def test_preparation_input_drift_keeps_failed_receipt_without_retry(self):
        contract, receipt = self.preparation_paths()
        with patch.object(self.s, 'build_contract', side_effect=[self.value, {'changed':True}]):
            self.assertEqual(self.s.prepare_contract(), 1)
        report = json.loads(receipt.read_bytes())
        self.assertEqual(report['status'], 'INPUT_ONLY_PREPARATION_FAILED_NO_RETRY')
        self.assertIn('E_CLEANUP_PREPARATION_INPUT_CHANGED', report['failure'])
        self.assertFalse(report['worker_started'])
        self.assertFalse(self.s.OUTPUT.exists())
        self.assertEqual(json.loads(contract.read_bytes()), self.value)

    def test_preparation_existing_diagnostic_output_creates_no_inputs(self):
        contract, receipt = self.preparation_paths()
        self.s.OUTPUT.mkdir()
        marker = self.s.OUTPUT/'keep'; marker.write_bytes(b'old diagnostic output')
        with patch.object(self.s, 'build_contract', return_value=self.value):
            with self.assertRaisesRegex(ValueError, 'E_CLEANUP_EXISTING_ATTEMPT_PRESERVED'):
                self.s.prepare_contract()
        self.assertFalse(contract.exists()); self.assertFalse(receipt.exists())
        self.assertEqual(marker.read_bytes(), b'old diagnostic output')

    def test_preparation_saved_contract_byte_drift_is_not_a_success(self):
        contract, receipt = self.preparation_paths()
        calls = []
        def build():
            calls.append(True)
            if len(calls) == 2:
                contract.write_bytes(b'{"drifted":true}')
            return self.value
        with patch.object(self.s, 'build_contract', side_effect=build):
            self.assertEqual(self.s.prepare_contract(), 1)
        report = json.loads(receipt.read_bytes())
        self.assertEqual(report['status'], 'INPUT_ONLY_PREPARATION_FAILED_NO_RETRY')
        self.assertIn('E_CLEANUP_PREPARATION_SAVED_CHANGED', report['failure'])
        self.assertEqual(contract.read_bytes(), b'{"drifted":true}')
        self.assertFalse(self.s.OUTPUT.exists())

    def test_preparation_output_appearing_during_validation_is_not_a_success(self):
        contract, receipt = self.preparation_paths()
        calls = []
        def build():
            calls.append(True)
            if len(calls) == 2: self.s.OUTPUT.mkdir()
            return self.value
        with patch.object(self.s, 'build_contract', side_effect=build):
            self.assertEqual(self.s.prepare_contract(), 1)
        report = json.loads(receipt.read_bytes())
        self.assertEqual(report['status'], 'INPUT_ONLY_PREPARATION_FAILED_NO_RETRY')
        self.assertIn('E_CLEANUP_EXISTING_ATTEMPT_PRESERVED', report['failure'])
        self.assertTrue(self.s.OUTPUT.exists())

    def controlled_run(self, mutate_build=False):
        # Run the real orchestrator with controlled captures, not the installed
        # runtime. Clone/fixture/preservation and the terminal classifier are real.
        self.value['fixture'] = self.s._fixture_values(self.s.OUTPUT)[0]
        self.contract.write_bytes(json.dumps(self.value).encode('utf-8'))
        self.record = self.s.g.file_record(self.contract); self.digest = self.record['sha256']
        captures = []
        def copy_source(doc, value, output):
            clone = output/'source'; clone.mkdir()
            (clone/'keep.py').write_bytes(b'original sealed source')
            return clone
        def capture(argv, target, output, env, timeout):
            captures.append((target.name, timeout))
            if target.name == 'build-index':
                (output/'task/index').mkdir()
                if mutate_build: (output/'task/worker.py').write_bytes(b'changed during synthetic build')
            stdout = target/'stdout.log'; stderr = target/'stderr.log'
            stdout.write_bytes(b'{"ok":true}' if target.name == 'public-vector-distributed' else b'{}')
            stderr.write_bytes(b'')
            return SimpleNamespace(returncode=0), {
                'stdout':self.s.g.file_record(stdout),'stderr':self.s.g.file_record(stderr)}
        with patch.dict(os.environ, USERPROFILE=r'C:\Users\sakth'), \
                patch.object(self.s, '_copy_source', side_effect=copy_source), \
                patch.object(self.s.g, 'sibling_module', return_value=SimpleNamespace(capture_owned=capture)), \
                patch.object(self.s.i, 'validate_runtime_observation'):
            self.assertEqual(self.s.run(self.contract, self.digest), 1)
        receipt = json.loads((self.s.OUTPUT/'Receipt.json').read_bytes())
        return receipt, captures

    def test_actual_run_rejects_malformed_public_success_and_keeps_no_false_inference_claim(self):
        receipt, captures = self.controlled_run()
        self.assertEqual(receipt['status'], 'HARNESS_OR_CAPTURE_FAILED')
        self.assertIn('E_CLEANUP_PUBLIC_CONTRACT', receipt['failure'])
        self.assertIsNone(receipt['inference_sent'])
        self.assertTrue(receipt['preservation'])
        self.assertIn(('public-vector-distributed',90), captures)
        self.assertEqual((self.s.OUTPUT/'public-vector-distributed/stdout.log').read_bytes(), b'{"ok":true}')

    def test_actual_run_stops_fixture_drift_after_build_before_public_capture(self):
        receipt, captures = self.controlled_run(mutate_build=True)
        self.assertEqual(receipt['status'], 'HARNESS_OR_CAPTURE_FAILED')
        self.assertIn('E_CLEANUP_FIXTURE_CHANGED', receipt['failure'])
        self.assertFalse(any(label == 'public-vector-distributed' for label, timeout in captures))
        self.assertFalse(receipt['fixture_preservation'])
        self.assertFalse(receipt['gate1_complete'])
        self.assertIsNone(receipt['inference_sent'])


if __name__ == '__main__':
    unittest.main()
