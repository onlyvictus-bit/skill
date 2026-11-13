"""Contract tests for the portable offline CI suite runner."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / '.github' / 'scripts' / 'offline_ci_suite.py'


def load_runner():
    spec = importlib.util.spec_from_file_location('offline_ci_suite', RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OfflineCiSuite(unittest.TestCase):
    def setUp(self):
        root = os.environ.get('OFFLINE_CI_TEST_ROOT')
        self.base = Path(tempfile.mkdtemp(prefix='offline-ci-suite-', dir=root))
        self.runner = load_runner()

    def package(self, name='package', body=''):
        package = self.base / name
        tests = package / 'tests'
        tests.mkdir(parents=True)
        (tests / '__init__.py').write_text('', encoding='utf-8')
        (tests / 'test_cases.py').write_text(textwrap.dedent(body), encoding='utf-8')
        return package

    def invoke(self, package, output):
        proc = subprocess.run([sys.executable, '-B', str(RUNNER), '--package-root', str(package),
                               '--test-dir', 'tests', '--pattern', 'test_*.py', '--output-dir', str(output)],
                              capture_output=True, text=True, timeout=30)
        self.last_output = proc.stdout + proc.stderr
        return proc.returncode

    def test_complete_success_records_real_case_outcomes_and_scoped_temp(self):
        package = self.package(body='''
            import pathlib, tempfile, unittest
            class Cases(unittest.TestCase):
                def test_pass(self):
                    self.assertEqual(pathlib.Path(tempfile.gettempdir()).name, 'retained-temp')
                @unittest.skip('declared skip')
                def test_skip(self): pass
                @unittest.expectedFailure
                def test_xfail(self): self.assertEqual(1, 2)
        ''')
        output = self.base / 'result'
        self.assertEqual(self.invoke(package, output), 0)
        receipt = json.loads((output / 'Receipt.json').read_text(encoding='utf-8'))
        self.assertEqual((receipt['discovered'], receipt['tests_run']), (3, 3))
        self.assertFalse(receipt['failures']); self.assertFalse(receipt['errors'])
        self.assertEqual(len(receipt['skipped']), 1); self.assertEqual(len(receipt['expected_failures']), 1)
        events = [json.loads(line) for line in (output / 'Cases.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual([event['event'] for event in events].count('START'), 3)
        self.assertEqual([event['event'] for event in events].count('END'), 3)
        self.assertTrue(all(event['seconds'] >= 0 for event in events if event['event'] == 'END'))

    def test_failure_retains_case_cause_and_returns_nonzero(self):
        package = self.package(body='''
            import unittest
            class Broken(unittest.TestCase):
                def test_broken(self): self.assertEqual('actual', 'expected')
        ''')
        output = self.base / 'broken-result'
        self.assertEqual(self.invoke(package, output), 1)
        receipt = json.loads((output / 'Receipt.json').read_text(encoding='utf-8'))
        self.assertEqual(len(receipt['failures']), 1)
        events = [json.loads(line) for line in (output / 'Cases.jsonl').read_text(encoding='utf-8').splitlines()]
        end = [event for event in events if event['event'] == 'END'][0]
        self.assertEqual(end['outcome'], 'failure')
        self.assertIn('AssertionError', end['cause'])
        self.assertTrue((output / 'unittest.log').is_file())

    def test_existing_or_in_package_output_is_refused_before_discovery(self):
        package = self.package(body='''\n            import unittest\n            class Ok(unittest.TestCase):\n                def test_ok(self): pass\n        ''')
        self.assertNotEqual(self.invoke(package, package / 'bad'), 0)
        self.assertIn('OUTPUT_IN_PACKAGE', self.last_output)
        output = self.base / 'existing'; output.mkdir()
        self.assertNotEqual(self.invoke(package, output), 0)
        self.assertIn('OUTPUT_EXISTS', self.last_output)

    def test_zero_cases_and_unexpected_success_cannot_pass(self):
        package = self.package(body='import unittest\n')
        self.assertEqual(self.invoke(package, self.base/'empty-result'), 1)
        other = self.package('unexpected', '''
            import unittest
            class Unexpected(unittest.TestCase):
                @unittest.expectedFailure
                def test_now_passes(self): pass
        ''')
        self.assertEqual(self.invoke(other, self.base/'unexpected-result'), 1)
        value = json.loads((self.base/'unexpected-result/Receipt.json').read_bytes())
        self.assertEqual(len(value['unexpected_successes']), 1)

    def test_subtest_failure_retains_parent_error_and_original_cause(self):
        package = self.package(body='''
            import unittest
            class Subtest(unittest.TestCase):
                def test_parent(self):
                    with self.subTest(segment='write'): self.fail('original segment cause')
        ''')
        output = self.base/'subtest-result'
        self.assertEqual(self.invoke(package, output), 1)
        ends = [json.loads(line) for line in (output/'Cases.jsonl').read_text().splitlines()
                if json.loads(line)['event'] == 'END']
        self.assertEqual(ends[0]['outcome'], 'failure')
        self.assertIn('original segment cause', ends[0]['cause'])

    def test_discovery_exception_retains_full_failure_receipt(self):
        package = self.package(body='raise ValueError("import segment cause")\n')
        output = self.base/'import-result'
        self.assertEqual(self.invoke(package, output), 1)
        value = json.loads((output/'Receipt.json').read_bytes())
        self.assertTrue(value['errors'])
        self.assertIn('import segment cause', value['errors'][0]['cause'])

    def test_memory_integrity_default_ready_copy_root_is_scoped_without_overriding_explicit_root(self):
        package = self.base / 'memory-integrity'
        module = package / 'scripts' / 'knowledge_bridge'; module.mkdir(parents=True)
        (module / '__init__.py').write_text('', encoding='utf-8')
        (module / 'windows_ready_copy.py').write_text(textwrap.dedent('''
            default_root = object()
            class ReadyCopy:
                def __init__(self, source, token, *, root=None): self.root = root
        '''), encoding='utf-8')
        tests = package / 'tests'; tests.mkdir()
        (tests / '__init__.py').write_text('', encoding='utf-8')
        (tests / 'test_ready.py').write_text(textwrap.dedent('''
            from pathlib import Path
            import unittest
            from knowledge_bridge import windows_ready_copy as ready
            class Ready(unittest.TestCase):
                def test_default_is_scoped(self):
                    self.assertEqual(ready.ReadyCopy('s','t').root.parts[-2:], ('managed','ready-copies-v1'))
                def test_explicit_is_unchanged(self):
                    root = Path('chosen-root')
                    self.assertEqual(ready.ReadyCopy('s','t',root=root).root, root)
        '''), encoding='utf-8')
        self.assertEqual(self.invoke(package, self.base / 'ready-result'), 0)


if __name__ == '__main__':
    unittest.main()
