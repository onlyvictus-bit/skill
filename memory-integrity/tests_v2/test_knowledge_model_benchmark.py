"""Real patch-outcome experiment contracts, including failed model outputs."""
import importlib
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
MODULE = ROOT / 'scripts' / 'knowledge_bridge' / 'model_benchmark.py'


class ModelBenchmarkContracts(unittest.TestCase):
    def module(self):
        self.assertTrue(MODULE.is_file(), 'real model coding benchmark is missing')
        return importlib.import_module('knowledge_bridge.model_benchmark')

    def test_three_independent_bug_baselines_fail_their_fixed_oracles(self):
        benchmark = self.module()
        cases = benchmark.fixtures()
        self.assertEqual(len(cases), 3)
        self.assertEqual(len({case['id'] for case in cases}), 3)
        for case in cases:
            self.assertNotIn('patch', case)
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                benchmark.write_files(root, case['files'])
                result = benchmark.run_regression(root, case['test_ids'])
                self.assertFalse(result['regression_passed'])
                self.assertEqual(result['tests_run'], 3)
                self.assertEqual(set(result['test_ids']), set(case['test_ids']))

    def test_generated_code_is_used_exactly_and_no_scripted_repair_is_injected(self):
        benchmark = self.module()
        emitted = 'def alive(expires_at, now):\n    return False\n'
        self.assertEqual(benchmark.extract_code(emitted), emitted)
        self.assertEqual(benchmark.extract_code('```python\n' + emitted + '```'), emitted)
        with self.assertRaisesRegex(ValueError, 'E_MODEL_PATCH_FORMAT'):
            benchmark.extract_code('Here is the code:\n```python\n' + emitted + '```')
        with self.assertRaises(ValueError):
            benchmark.extract_code('```python\ndef broken(')

    def test_generated_shell_file_and_network_access_are_refused(self):
        benchmark = self.module()
        for code in ('import os\ndef alive(a,b): return os.system("echo bad")\n',
                     'def alive(a,b): return open("secrets").read()\n',
                     'def alive(a,b): return a.__class__.__mro__\n',
                     'def alive(a,b): return eval(a)\n'):
            with self.assertRaisesRegex(ValueError, 'E_MODEL_PATCH_UNSAFE'):
                benchmark.validate_code(code)
        benchmark.validate_code('def alive(expires_at, now):\n    return expires_at is None or expires_at > now\n')

    def test_zero_or_failed_trials_do_not_claim_superiority(self):
        benchmark = self.module()
        empty = benchmark.summarize([])
        self.assertIsNone(empty['direct_graph_pass_delta'])
        self.assertEqual(empty['general_coding_benefit'], 'UNVERIFIED')
        rows = [{'variant': variant, 'regression_passed': False, 'elapsed_seconds': 0.1,
                 'input_token_count': 10, 'output_token_count': 4, 'patch_applied': False}
                for variant in benchmark.VARIANTS]
        measured = benchmark.summarize(rows)
        self.assertEqual(measured['direct_graph_pass_delta'], 0)
        self.assertFalse(measured['default_graph'])
        self.assertTrue(all(row['regression_passes'] == 0 for row in measured['summaries']))

    def test_actual_pinned_worker_is_required(self):
        benchmark = self.module()
        with self.assertRaisesRegex(ValueError, 'E_MODEL_BENCHMARK_WORKER'):
            benchmark.run('not-a-manifest', ROOT.parent / 'claude-mon', lambda p: {})

    def test_import_failure_is_a_retained_negative_attempt_of_the_fixed_oracle(self):
        benchmark = self.module()
        self.assertTrue(callable(getattr(benchmark, 'oracle_attempted', None)),
                        'negative-outcome oracle verification is missing')
        case = benchmark.fixtures()[0]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            benchmark.write_files(root, case['files'])
            (root / 'worker.py').write_text('def wrong_name(a, b):\n    return False\n')
            receipt = benchmark.run_regression(root, case['test_ids'])
        self.assertFalse(receipt['regression_passed'])
        self.assertTrue(receipt['errors'])
        self.assertTrue(benchmark.oracle_attempted(receipt, case['test_ids']))
        self.assertFalse(benchmark.oracle_attempted(receipt, ['invented.test']))
        altered = dict(receipt, transcript='invented success')
        self.assertFalse(benchmark.oracle_attempted(altered, case['test_ids']))

    def test_cli_help_and_existing_output_refusal_need_no_model_calls(self):
        self.module()
        help_result = subprocess.run([sys.executable, '-B', str(MODULE), '--help'], capture_output=True, text=True, timeout=15)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn('--manifest', help_result.stdout)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'existing.json'
            target.write_text('preserve existing receipt')
            result = subprocess.run([sys.executable, '-B', str(MODULE), '--manifest', str(target),
                '--claude-mon-root', str(ROOT.parent / 'claude-mon'), '--worker-python', sys.executable,
                '--output', str(target)], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 1)
            self.assertIn('E_MODEL_BENCHMARK_OUTPUT_EXISTS', result.stdout)
            self.assertEqual(target.read_text(), 'preserve existing receipt')

    @unittest.skipUnless(os.name == 'posix', 'direct per-model signal timeout is POSIX-only')
    def test_direct_model_budget_interrupts_overdue_work(self):
        benchmark = self.module()
        self.assertTrue(callable(getattr(benchmark, 'model_budget', None)), 'direct model timeout guard is missing')
        import time
        with self.assertRaisesRegex(ValueError, 'E_LOCAL_MODEL_TIMEOUT'):
            with benchmark.model_budget(0.02):
                time.sleep(0.1)


@unittest.skipUnless(os.environ.get('KNOWLEDGE_MODEL_MANIFEST') and os.environ.get('MODEL_PYTHON')
                     and os.environ.get('KNOWLEDGE_WORKER_PYTHON'), 'explicit actual model and worker runtimes not selected')
class RealModelBenchmark(unittest.TestCase):
    module = ModelBenchmarkContracts.module

    def test_one_actual_case_keeps_equal_oracles_and_complete_raw_receipts(self):
        from knowledge_bridge.worker_client import WorkerClient, ModelClient
        benchmark = self.module()
        worker = WorkerClient(os.environ['KNOWLEDGE_WORKER_PYTHON'], timeout=60,
            model_client=ModelClient(os.environ['MODEL_PYTHON'], os.environ['KNOWLEDGE_MODEL_MANIFEST'], timeout=120))
        case = benchmark.fixtures()[0]
        result = benchmark.run_case(case, os.environ['KNOWLEDGE_MODEL_MANIFEST'], ROOT.parent / 'claude-mon', worker)
        self.assertEqual(len(result['runs']), 4)
        self.assertFalse(result['baseline']['regression_passed'])
        for row in result['runs']:
            self.assertTrue(benchmark.oracle_attempted(row['regression'], case['test_ids']))
            if row['regression']['regression_passed']:
                self.assertEqual(set(row['regression']['test_ids']), set(case['test_ids']))
                self.assertEqual(row['regression']['tests_run'], 3)
            else:
                self.assertTrue(row['regression']['failures'] or row['regression']['errors']
                                or row['regression']['process_exit_code'] != 0)
            self.assertIn('prompt', row)
            self.assertIn('model_receipt', row)
            self.assertTrue(row['model_receipt']['output_token_count'] > 0)
            self.assertEqual(row['source_versions'], result['source_versions'])
            self.assertFalse(row['unnecessary_changes'])


if __name__ == '__main__':
    unittest.main()
