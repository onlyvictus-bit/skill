import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import specialist_gate as gate
from specialist_tools import NAMES, release_check, triangulate


class NumericTests(unittest.TestCase):
    def setUp(self):
        self.data = {'target': 'fixture', 'unit': 'seconds', 'max_tight_width': 4,
                     'lenses': [{'id': 'a', 'origins': ['raw-a'], 'range': [10, 12]},
                                {'id': 'b', 'origins': ['raw-b'], 'range': [11, 13]}]}

    def test_independent_overlap(self):
        value = triangulate(self.data)
        self.assertEqual(value['overlap'], 'TIGHT')
        self.assertEqual(value['common_region'], [11, 12])

    def test_copied_evidence_counts_once(self):
        self.data['lenses'][1]['origins'] = ['raw-a']
        self.assertEqual(triangulate(self.data)['overlap'], 'INSUFFICIENT')

    def test_transitive_correlation(self):
        self.data['lenses'].append({'id': 'c', 'origins': ['raw-a', 'raw-b'], 'range': [12, 14]})
        self.assertEqual(triangulate(self.data)['independent_family_count'], 1)

    def test_disjoint(self):
        self.data['lenses'][1]['range'] = [20, 22]
        self.assertEqual(triangulate(self.data)['overlap'], 'NONE')

    def test_broad_uncertainty_not_tight(self):
        self.data['lenses'][0]['range'] = [0, 1000]
        self.assertEqual(triangulate(self.data)['overlap'], 'PARTIAL')

    def test_missing_origin_rejected(self):
        self.data['lenses'][0]['origins'] = []
        with self.assertRaises(ValueError):
            triangulate(self.data)

    def test_nonfinite_rejected(self):
        self.data['lenses'][0]['range'][0] = float('nan')
        with self.assertRaises(ValueError):
            triangulate(self.data)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.data = {'expected_environment': 'scratch', 'observed_environment': 'scratch',
                     'expected_digest': 'a' * 64, 'observed_digest': 'a' * 64,
                     'exit_code': 0, 'healthy': True, 'authorized': True,
                     'observation_source': 'explicit synthetic fixture, no deployment'}

    def test_matching_observation(self):
        self.assertTrue(release_check(self.data)['consistent'])

    def test_failures_cannot_be_hidden_by_shipped(self):
        for key, bad in [('exit_code', 1), ('observed_digest', 'b' * 64),
                         ('observed_environment', 'production'), ('healthy', False),
                         ('authorized', False), ('observation_source', '')]:
            with self.subTest(key=key):
                data = {**self.data, key: bad, 'stdout': 'Shipped.'}
                self.assertFalse(release_check(data)['consistent'])

    def test_boolean_exit_is_not_zero(self):
        self.data['exit_code'] = False
        self.assertFalse(release_check(self.data)['consistent'])


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='six-specialist-test-')
        self.project = Path(self.temp.name)
        self.docs = self.project / 'docs/fable'
        self.docs.mkdir(parents=True)
        self.requirements = {'schema': 2, 'requirements': [{'id': 'R1', 'text': 'Fixture',
            'priority': 'required', 'criteria': [{'id': 'C1', 'text': 'Complete fixture', 'test_ids': ['T1']}], 'test_ids': ['T1']}]}
        self.plan = {'schema': 2, 'plan_id': 'test-v1', 'milestone': 'M1', 'tasks': [
            {'id': 'TASK1', 'requirement_ids': ['R1'], 'criterion_ids': ['C1'], 'test_ids': ['T1'],
             'artifacts': ['docs/fable/specialists.json', 'result.md'], 'action': 'Review fixture'}]}
        self.tests = {'schema': 2, 'tests': [{'id': 'T1', 'kind': 'manual', 'instructions': 'Inspect actual fixture'}]}
        (self.project / 'result.md').write_text('Observed fixture output\n', encoding='utf-8')
        self.record = {'schema': 1, 'skills': []}
        for name in NAMES:
            selected = name == 'cortex'
            self.record['skills'].append({'name': name, 'disposition': 'selected' if selected else 'not_applicable',
                'reason': 'Cortex routes this fixture' if selected else 'No relevant work in this bounded fixture',
                'requirement_ids': ['R1'] if selected else [], 'test_ids': ['T1'] if selected else [],
                'outputs': [{'path': 'result.md', 'sha256': hashlib.sha256((self.project / 'result.md').read_bytes()).hexdigest()}] if selected else [],
                'status': 'observed' if selected else 'pending'})
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        for name, value in [('requirements', self.requirements), ('plan', self.plan), ('tests', self.tests), ('specialists', self.record)]:
            (self.docs / (name + '.json')).write_text(json.dumps(value), encoding='utf-8')

    def test_combined_plan(self):
        self.assertEqual(gate.check(self.project, 'plan'), [])

    def test_original_missing_criterion_still_blocks(self):
        self.plan['tasks'][0]['criterion_ids'] = []
        self.save()
        self.assertTrue(any('E_CRITERIA_COVERAGE' in x for x in gate.check(self.project, 'plan')))

    def test_original_shell_rule_still_blocks(self):
        self.tests['tests'][0] = {'id': 'T1', 'kind': 'automated', 'shell_command': 'echo unsafe', 'expect': 'exit=0'}
        self.save()
        self.assertTrue(any('E_SHELL_AUTH' in x for x in gate.check(self.project, 'plan')))

    def test_execute_without_approval_blocks(self):
        (self.docs / 'approvals.json').write_text('{"schema":2,"approvals":[]}', encoding='utf-8')
        self.assertTrue(any('E_APPROVAL_MISSING' in x for x in gate.check(self.project, 'execute')))

    def test_omitted_skill_blocks(self):
        self.record['skills'].pop()
        self.save()
        self.assertTrue(gate.check(self.project, 'plan'))

    def test_duplicate_skill_blocks(self):
        self.record['skills'][1]['name'] = 'cortex'
        self.save()
        self.assertTrue(gate.check(self.project, 'plan'))

    def test_fresh_specialist_outputs(self):
        self.assertEqual(gate.check_specialists(self.project, 'complete'), [])

    def test_stale_output_blocks(self):
        (self.project / 'result.md').write_text('Changed', encoding='utf-8')
        self.assertTrue(any('E_SPECIALIST_STALE' in x for x in gate.check_specialists(self.project, 'complete')))

    def test_unavailable_selected_helper_blocks(self):
        next(r for r in self.record['skills'] if r['name'] == 'cortex')['status'] = 'unavailable'
        self.save()
        self.assertTrue(any('E_SPECIALIST_UNVERIFIED' in x for x in gate.check_specialists(self.project, 'complete')))

    def test_unplanned_output_blocks(self):
        next(r for r in self.record['skills'] if r['name'] == 'cortex')['outputs'][0]['path'] = 'unknown.md'
        self.save()
        self.assertTrue(any('E_SPECIALIST_SCOPE' in x for x in gate.check(self.project, 'plan')))

    def test_path_escape_blocks(self):
        next(r for r in self.record['skills'] if r['name'] == 'cortex')['outputs'][0]['path'] = '../outside.md'
        self.save()
        self.assertTrue(any('E_PATH_ESCAPE' in x for x in gate.check(self.project, 'plan')))

    def test_original_complete_gate_not_bypassed(self):
        (self.docs / 'approvals.json').write_text('{"schema":2,"approvals":[]}', encoding='utf-8')
        with self.assertRaises(ValueError):
            gate.check(self.project, 'complete')  # Missing canonical state; output hashes alone cannot pass.


@unittest.skipUnless(shutil.which('node'), 'Node required for native Unlazy runtime')
class NativeUnlazyTests(unittest.TestCase):
    def test_real_gate_runs_and_stale_result_demotes(self):
        with tempfile.TemporaryDirectory(prefix='native-unlazy-') as temp:
            outer = Path(temp)
            project = outer / 'project'
            project.mkdir()
            approval = outer / 'approvals'
            fixture = project / 'fixture.json'
            fixture.write_text('{"value":7}', encoding='utf-8')
            script = project / 'verify.mjs'
            script.write_text("import fs from 'node:fs';\nimport assert from 'node:assert/strict';\nconst data=JSON.parse(fs.readFileSync('fixture.json','utf8'));\nassert.equal(data.value,7);\nfs.writeFileSync('observed.txt','observed');\nconsole.log('FIXTURE_VERIFIED');\n", encoding='utf-8')
            ledger = project / 'GATES.md'
            original = '# Gates\n\n- [ ] G1: fixture contains expected value\n  CHECK: node verify.mjs\n  EXPECT: FIXTURE_VERIFIED\n  EVIDENCE: pending\n'
            ledger.write_text(original, encoding='utf-8')
            runner = ROOT / 'references/specialists/unlazy/scripts/gate-check.mjs'
            env = {**os.environ, 'UNLAZY_APPROVAL_DIR': str(approval)}
            def run(*args):
                return subprocess.run([shutil.which('node'), str(runner), '--root', str(project), *args, str(ledger)],
                    cwd=project, env=env, text=True, capture_output=True, timeout=30)
            pending = run('--status')
            self.assertEqual(pending.returncode, 1, pending.stdout + pending.stderr)
            self.assertEqual(ledger.read_text(encoding='utf-8'), original)
            self.assertFalse((project / 'observed.txt').exists())
            passed = run('--approve')
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            self.assertTrue((project / 'observed.txt').is_file())
            self.assertIn('- [x] G1', ledger.read_text(encoding='utf-8'))
            fixture.write_text('{"value":8}', encoding='utf-8')
            failed = run('--reverify')
            self.assertEqual(failed.returncode, 1, failed.stdout + failed.stderr)
            self.assertIn('- [ ] G1', ledger.read_text(encoding='utf-8'))
            fixture.write_text('{"value":7}', encoding='utf-8')
            with ledger.open('a', encoding='utf-8') as stream:
                stream.write('\n- [ ] PARENT: integration independently observed\n  EVIDENCE: pending\n')
            parent = run('--reverify')
            self.assertEqual(parent.returncode, 1, parent.stdout + parent.stderr)
            self.assertIn('- [x] G1', ledger.read_text(encoding='utf-8'))
            self.assertIn('PARENT', parent.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
