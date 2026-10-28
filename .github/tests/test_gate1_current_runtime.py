"""Failure-first controls for the next C2 phase; no selected runtime executes."""
import copy
import contextlib
import io
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[2]
SCRIPT = ROOT/'.github/scripts/gate1_current_runtime.py'


def subject():
    if not SCRIPT.exists(): raise AssertionError('C2 coordinator is not implemented')
    spec = importlib.util.spec_from_file_location('c2_test_subject', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class CurrentRuntime(unittest.TestCase):
    def setUp(self): self.g = subject()

    def suite(self):
        ids = ['sample.Case.test_a', 'sample.Case.test_b']
        report = {'expected_ids': ids, 'outcomes': {'started': ids,
            'finished': [{'id': i, 'outcome': 'PASS', 'reason': ''} for i in ids]}}
        row = {'tests_run': 2, 'discovered': 2, 'failures': [], 'errors': [], 'skipped': [],
            'excluded': [], 'expected_failures': [], 'interrupted': False}
        return ids, report, row

    def test_complete_suite_requires_both_case_and_aggregate_agreement(self):
        ids, report, row = self.suite()
        self.g.validate_suite(row, report, ids, {})
        for field, value in [('failures', [ids[0]]), ('errors', [ids[0]]), ('excluded', [ids[0]]),
                             ('tests_run', 1), ('interrupted', True), ('expected_failures', [ids[0]])]:
            bad = copy.deepcopy(row); bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.g.validate_suite(bad, report, ids, {})

    def test_missing_reordered_duplicate_and_incomplete_cases_are_rejected(self):
        ids, report, row = self.suite()
        for field, value in [('expected_ids', list(reversed(ids))), ('expected_ids', [ids[0], ids[0]])]:
            bad = copy.deepcopy(report); bad[field] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.g.validate_suite(row, bad, ids, {})
        bad = copy.deepcopy(report); bad['outcomes']['finished'].pop()
        with self.assertRaises(ValueError): self.g.validate_suite(row, bad, ids, {})
        bad = copy.deepcopy(report); bad['outcomes']['finished'][0]['outcome'] = 'INCOMPLETE'
        with self.assertRaises(ValueError): self.g.validate_suite(row, bad, ids, {})

    def test_skip_identity_reason_and_aggregate_must_all_match(self):
        ids, report, row = self.suite()
        report['outcomes']['finished'][1].update(outcome='SKIP', reason='optional model absent')
        row['skipped'] = [[ids[1], 'optional model absent']]
        self.g.validate_suite(row, report, ids, {ids[1]: 'model absent'})
        with self.assertRaises(ValueError): self.g.validate_suite(row, report, ids, {})
        bad = copy.deepcopy(row); bad['skipped'] = []
        with self.assertRaises(ValueError): self.g.validate_suite(bad, report, ids, {ids[1]: 'model absent'})

    def test_parent_success_and_exact_prepared_record_are_required(self):
        prepared = {'path': 'fixed', 'size': 123, 'sha256': 'a'*64, 'links': 1}
        row = {'status': 'STEP1_SOURCE_AND_ENVIRONMENT_VERIFIED_NOT_GATE1', 'failure': None,
            'head': self.g.HEAD, 'prepared': prepared, 'protected_unchanged': True,
            'gate1_complete': False, 'installed': False, 'release_ready': False,
            'retrieval_executed': False, 'producer_authentication': False}
        self.g.validate_parent(row, prepared)
        for field, value in [('status', 'PARTIAL_OR_FAILED_NO_RETRY'), ('failure', 'bad'),
                             ('protected_unchanged', False), ('gate1_complete', True), ('head', 'old')]:
            bad = copy.deepcopy(row); bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): self.g.validate_parent(bad, prepared)
        with self.assertRaises(ValueError): self.g.validate_parent(row, dict(prepared, sha256='b'*64))

    def test_adapted_replay_constructs_real_worker_with_default120(self):
        c1 = self.g.c1
        original = c1.read_file(self.g.SOURCE/'.github/scripts/offline_release_acceptance.py')
        raw = self.g.adapt_acceptance(original, self.g.SOURCE/'.github/fixtures/offline-first')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); script = root/'acceptance.py'; script.write_bytes(raw)
            spec = importlib.util.spec_from_file_location('adapted_acceptance_test', script)
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            for name, value in [('basis', {'policy': str(root/'policy'), 'task': str(root/'task'),
                     'pack': str(root/'pack'), 'index': str(root/'index'), 'project': str(root)}),
                    ('policy', {'allowed_source_ids': []}), ('task', {}), ('pack', {'pack_digest': 'a'*64})]:
                (root/name).write_text(json.dumps(value), encoding='utf-8')
            sys.path.insert(0, str(self.g.SOURCE/'memory-integrity/scripts'))
            from knowledge_bridge import indexing, retrieval
            def observe(pack, doc, project, policy, task, worker): self.assertEqual(worker.timeout, 120)
            args = SimpleNamespace(replay_input=root/'basis', package_root=self.g.SOURCE/'memory-integrity',
                claude_mon_root=self.g.SOURCE/'claude-mon', worker_python=str(Path(sys.executable).absolute()))
            with patch.object(indexing, 'load', return_value={}), patch.object(retrieval, 'verify_pack', side_effect=observe), \
                    contextlib.redirect_stdout(io.StringIO()):
                module.replay(args)

    def test_adaptation_refuses_changed_basis_instead_of_guessing(self):
        with self.assertRaises(ValueError): self.g.adapt_acceptance(b'not the pinned helper', Path('fixture'))

    def test_initial_and_replay_adaptation_preserves_other_ast(self):
        import ast
        original = self.g.c1.read_file(self.g.SOURCE/'.github/scripts/offline_release_acceptance.py')
        raw = self.g.adapt_acceptance(original, self.g.SOURCE/'.github/fixtures/offline-first')
        module = ast.parse(raw.decode()); execute = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'execute')
        assign = next(n for n in ast.walk(execute) if isinstance(n, ast.Assign) and
            any(isinstance(t, ast.Name) and t.id == 'worker_flags' for t in n.targets))
        value = eval(compile(ast.Expression(assign.value), '<worker flags>', 'eval'),
                     {'args': SimpleNamespace(worker_python='selected-python')})
        self.assertEqual(value, ['--worker-python', 'selected-python'])
        self.assertEqual(self.g.restore_acceptance(raw, self.g.SOURCE/'.github/fixtures/offline-first'), original)

    def test_failed_capture_keeps_command_record_before_refusal(self):
        import subprocess
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            host = SimpleNamespace(capture_owned=lambda *args: (
                subprocess.CompletedProcess(['child'], 7, b'', b'actual child reason'),
                {'exit_code': 7, 'execution': 'EXITED', 'failure': None}))
            try:
                proc, row = self.g.capture(host, 'bad-child', ['child'], root, {}, 10)
            except ValueError as error:
                self.fail('capture discarded the failed command before its caller could retain it: '+str(error))
            self.assertEqual(row['exit_code'], 7)
            self.assertEqual(proc.stderr, b'actual child reason')
            validator = getattr(self.g, 'require_capture', None)
            self.assertTrue(callable(validator), 'missing retained-command validation boundary')
            with self.assertRaisesRegex(ValueError, 'E_C2_CHILD_FAILED'):
                validator(proc, row)

    def test_setup_error_is_retained_without_workload_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'attempt'
            with patch.object(self.g, 'OUTPUT', output), patch.object(self.g, 'STOP', Path(folder)/'stop.json'), \
                    patch.object(self.g.c1, 'normal_account'), patch.object(self.g, 'inputs', return_value={}), \
                    patch.object(self.g, 'environment', side_effect=ValueError('deliberate setup refusal')), \
                    patch.object(self.g, 'preserved'), patch.object(self.g.c1, 'sha', return_value='sealed'), \
                    contextlib.redirect_stdout(io.StringIO()):
                try:
                    result = self.g.run(Path(__file__), 'sealed')
                except ValueError as error:
                    self.fail('setup escaped retained-receipt boundary: '+str(error))
            self.assertEqual(result, 1)
            receipt = json.loads((output/'Receipt.json').read_text(encoding='utf-8'))
            self.assertIn('deliberate setup refusal', receipt['failure'])
            self.assertEqual(receipt['status'], 'PARTIAL_OR_FAILED_NO_RETRY')
            self.assertFalse((output/'workload-claim.json').exists())
            self.assertFalse(receipt['gate1_complete'])

    def test_wrong_account_and_existing_attempt_do_not_touch_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'attempt'
            with patch.object(self.g, 'OUTPUT', output), \
                    patch.object(self.g.c1, 'normal_account', side_effect=ValueError('wrong account')):
                with self.assertRaisesRegex(ValueError, 'wrong account'):
                    self.g.run(Path(__file__), 'a'*64)
            self.assertFalse(output.exists())
            output.mkdir(); (output/'marker').write_bytes(b'keep me')
            with patch.object(self.g, 'OUTPUT', output), patch.object(self.g.c1, 'normal_account'):
                with self.assertRaisesRegex(ValueError, 'E_C2_EXISTING_ATTEMPT'):
                    self.g.run(Path(__file__), 'a'*64)
            self.assertEqual(list(output.iterdir()), [output/'marker'])
            self.assertEqual((output/'marker').read_bytes(), b'keep me')

    def test_acceptance_rejects_partial_duplicate_or_unreplayed_arms(self):
        module = self.g.load_module(self.g.SOURCE/'.github/scripts/offline_release_acceptance.py',
                                   'c2_test_acceptance_oracle')
        rows = [{'case': case, 'mode': mode, 'mandatory': mandatory,
                 'mandatory_missing': [], 'replay_verified': True}
                for case in ('freshness', 'unicode', 'approval', 'resume')
                for mode in ('literal', 'lexical', 'lsa') for mandatory in (False, True)]
        base = {'scope': 'RANKED_RUNTIME', 'checks': [{'name': name, 'passed': True}
                for name in module.CHECKS], 'measurements': rows}
        for bad_rows in (rows[:-1], rows[:-1]+[rows[0]],
                         [dict(row, replay_verified=False) if n == 0 else row for n, row in enumerate(rows)]):
            with self.subTest(arms=len(bad_rows)), self.assertRaisesRegex(ValueError, 'E_ACCEPTANCE_INCOMPLETE'):
                module.validate_receipt(dict(base, measurements=bad_rows))


if __name__ == '__main__': unittest.main()
