"""Root-cause diagnostic guards; no selected runtime or old attempt is executed."""
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).absolute().parents[1]/'scripts/cleanup_lifetime_diagnostic.py'


class LifetimeDiagnostic(unittest.TestCase):
    def module(self):
        self.assertTrue(SCRIPT.is_file(), 'new bounded diagnostic helper missing')
        spec = importlib.util.spec_from_file_location('lifetime_diagnostic_tests', SCRIPT)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module

    @staticmethod
    def command(timed_out=True):
        return {'execution':'TIMEOUT' if timed_out else 'EXITED', 'exit_code':1 if timed_out else 0,
            'failure':None, 'containment':{'timed_out':timed_out, 'capture_complete':True,
            'capture_errors':[], 'output_limit_exceeded':False, 'tree_contained':True}}

    @staticmethod
    def stack():
        return b'Timeout (0:00:10)!\nThread 0x123 (most recent call first):\n  File "fixture.py", line 3 in wait\n'

    def test_argv_adds_only_existing_stack_option_without_skip_or_budget_override(self):
        module = self.module()
        worker, output = Path('worker.exe'), Path('new-output')
        self.assertEqual(module.arguments(worker, output), [worker, '-B',
            module.SOURCE/'.github/scripts/gate1_runner.py', '--package-root',
            module.SOURCE/'memory-integrity', '--pattern', 'test_knowledge_windows_shutdown.py',
            '--output-dir', output/'tests', '--stack-after', '10'])
        self.assertEqual(module.WATCHDOG, 60)

    def test_timeout_with_stack_is_diagnostic_evidence_never_fixed(self):
        module = self.module()
        self.assertEqual(module.classify_capture(None, self.command(), self.stack()),
                         'TIMEOUT_STACK_CAPTURED_NOT_FIXED')

    def test_timeout_without_stack_remains_inconclusive(self):
        module = self.module()
        for raw in (b'', b'not a Python stack'):
            self.assertEqual(module.classify_capture(None, self.command(), raw),
                             'TIMEOUT_NO_STACK_INCONCLUSIVE')

    def test_incomplete_uncontained_overflow_and_capture_error_refuse_any_verdict(self):
        module = self.module()
        for key, value in (('capture_complete',False), ('tree_contained',False),
                           ('output_limit_exceeded',True), ('capture_errors',['CONTROL_CAPTURE_ERROR'])):
            row = self.command(); row['containment'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'E_LD_CAPTURE'):
                module.classify_capture(None, row, self.stack())

    def test_missing_or_inconsistent_process_result_cannot_be_success(self):
        module = self.module()
        with self.assertRaisesRegex(ValueError, 'E_LD_CAPTURE'):
            module.classify_capture(None, self.command(False), b'')
        with self.assertRaisesRegex(ValueError, 'E_LD_CAPTURE'):
            module.classify_capture(SimpleNamespace(returncode=0), self.command(), self.stack())

    def test_exit_zero_still_requires_inner_unit_validation(self):
        module = self.module()
        self.assertEqual(module.classify_capture(SimpleNamespace(returncode=0), self.command(False), b''),
                         'LIFETIME_COMPLETED_PENDING_UNIT_VALIDATION')

    def test_nonzero_exit_is_failed_even_if_stack_was_captured(self):
        module = self.module(); row = self.command(False); row['exit_code'] = 1
        self.assertEqual(module.classify_capture(SimpleNamespace(returncode=1), row, self.stack()),
                         'LIFETIME_FAILED_NOT_FIXED')

    def test_case_ids_are_static_exact_twelve_and_never_execute_input(self):
        module = self.module()
        raw = 'raise AssertionError("MUST_NOT_EXECUTE")\nclass WindowsShutdown:\n'
        raw += ''.join(' def test_'+str(number).zfill(2)+'(self): pass\n' for number in range(12))
        ids = module.case_ids(raw.encode())
        self.assertEqual(len(ids), 12)
        self.assertEqual(ids, sorted(ids))
        with self.assertRaisesRegex(ValueError, 'E_LD_CASE_IDS'):
            module.case_ids(raw.replace('def test_11','def not_a_test_11').encode())

    def test_wrong_account_refuses_before_output_or_selected_child(self):
        module = self.module()
        with tempfile.TemporaryDirectory(prefix='ld-account-') as name:
            output = Path(name)/'not-created'
            c1 = SimpleNamespace(normal_account=Mock(side_effect=ValueError('CONTROL_WRONG_ACCOUNT')))
            with patch.object(module, 'context', return_value=(None,c1)), patch.object(module, 'OUTPUT', output):
                with self.assertRaisesRegex(ValueError, 'CONTROL_WRONG_ACCOUNT'):
                    module.run('unused')
            self.assertFalse(output.exists())

    def test_setup_failure_is_retained_and_does_not_consume_lifecycle_attempt(self):
        module = self.module()
        with tempfile.TemporaryDirectory(prefix='ld-setup-') as name:
            output = Path(name)/'diagnostic'
            def require(value, message):
                if not value: raise ValueError(message)
            def save(path, value):
                with path.open('x', encoding='utf-8') as stream: json.dump(value, stream)
            c1 = SimpleNamespace(normal_account=lambda:None, read_file=lambda _:b'{}',
                sha=lambda _:'seal', require=require, ordinary=lambda _:None, HEAD='head',
                record=lambda path:{'path':str(path)}, save=save,
                load_support=Mock(side_effect=OSError('CONTROL_SETUP')))
            with patch.object(module, 'context', return_value=(None,c1)), \
                 patch.object(module, 'verify_inputs'), patch.object(module, 'OUTPUT', output):
                self.assertEqual(module.run('seal'), 1)
            receipt = json.loads((output/'Receipt.json').read_text(encoding='utf-8'))
            self.assertEqual(receipt['status'], 'PARTIAL_OR_FAILED_NO_RETRY')
            self.assertIn('CONTROL_SETUP', receipt['failure'])
            self.assertFalse(receipt['diagnostic_attempt_consumed'])
            self.assertFalse(receipt['stage_complete'])
            self.assertEqual(receipt['commands'], [])
            self.assertFalse((output/'diagnostic-attempt').exists())

    def test_real_existing_runner_writes_a_usable_thread_stack_without_source_overlay(self):
        module = self.module()
        with tempfile.TemporaryDirectory(prefix='ld-stack-smoke-') as name:
            root = Path(name); package = root/'package'; tests = package/'tests_v2'
            tests.mkdir(parents=True)
            (tests/'test_wait.py').write_text('import threading,unittest\nclass Wait(unittest.TestCase):\n'
                ' def test_wait(self): threading.Event().wait(2)\n', encoding='utf-8')
            output = root/'output'
            proc = subprocess.run([sys.executable, '-B', str(SCRIPT.with_name('retained_unittest.py')),
                '--package-root', str(package), '--pattern', 'test_wait.py', '--output-dir', str(output),
                '--stack-after', '1'], capture_output=True, timeout=15)
            self.assertEqual(proc.returncode, 0, proc.stderr.decode('utf-8', errors='replace'))
            stack = (output/'Slow-Stack.log').read_bytes()
            self.assertIn(b'test_wait.py', stack)
            self.assertEqual(module.classify_capture(None, self.command(), stack),
                             'TIMEOUT_STACK_CAPTURED_NOT_FIXED')

    def test_timeout_stack_is_retained_in_real_coordinator_flow_without_success_claim(self):
        self.run_timeout_flow(False)

    def test_preservation_failure_overrides_even_a_captured_diagnostic(self):
        self.run_timeout_flow(True)

    def run_timeout_flow(self, fail_preservation):
        module = self.module()
        with tempfile.TemporaryDirectory(prefix='ld-flow-') as name:
            output = Path(name)/'diagnostic'
            def require(value, message):
                if not value: raise ValueError(message)
            def read(path):
                return b'{}' if path == module.CONTRACT else Path(path).read_bytes()
            def record(path):
                raw = read(path)
                return {'path':str(path), 'size':len(raw), 'sha256':hashlib.sha256(raw).hexdigest(), 'links':1}
            def save(path, value):
                with path.open('x', encoding='utf-8') as stream: json.dump(value, stream)
            calls = []
            def capture(argv, target, cwd, env, timeout):
                calls.append((argv, timeout))
                if '--stack-after' in argv:
                    (output/'tests').mkdir()
                    (output/'tests/Slow-Stack.log').write_bytes(self.stack())
                    return None, self.command()
                return SimpleNamespace(returncode=0, stdout=b'{}'), self.command(False)
            host = SimpleNamespace(capture_owned=capture)
            g = SimpleNamespace(WORKER=Path('selected-worker.exe'), runtime_probe=lambda:'identity')
            c1 = SimpleNamespace(normal_account=lambda:None, read_file=read,
                sha=lambda _: 'seal', ordinary=lambda _:None, HEAD='head', require=require,
                record=record, save=save, validate_runtime=Mock(), validate_dependencies=Mock(),
                dependency_versions=lambda:{'control':'1'},
                load_support=lambda role:host if role == 'offline_host_validation' else g)
            c2 = SimpleNamespace(environment=lambda _: {}, require_capture=Mock())
            cr = SimpleNamespace(load=lambda _: c2)
            checks = [None, None, ValueError('CONTROL_PRESERVATION')] if fail_preservation else None
            with patch.object(module, 'context', return_value=(cr,c1)), patch.object(module, 'OUTPUT', output), \
                 patch.object(module, 'verify_inputs', side_effect=checks):
                self.assertEqual(module.run('seal'), 1)
            value = json.loads((output/'Receipt.json').read_text(encoding='utf-8'))
            self.assertEqual(value['status'], 'PARTIAL_OR_FAILED_NO_RETRY' if fail_preservation else
                             'TIMEOUT_STACK_CAPTURED_NOT_FIXED')
            self.assertFalse(value['stage_complete'])
            self.assertFalse(value['fix_validated'])
            self.assertFalse(value['root_cause_confirmed'])
            self.assertTrue(value['diagnostic_attempt_consumed'])
            self.assertIn('Slow-Stack.log', value['internal_files'])
            self.assertEqual(calls[-1][1], 60)
            self.assertEqual(len(calls), 3)
            if fail_preservation:
                self.assertIn('CONTROL_PRESERVATION', value['preservation_failure'])
            else:
                self.assertTrue(value['pinned_preservation_verified'])


if __name__ == '__main__': unittest.main()
