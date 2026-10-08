"""Held-out deterministic coding outcomes, with an honest direct baseline."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
CM = ROOT.parent / 'claude-mon'


class BenefitContract(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('knowledge_bridge.benefit_benchmark'),
                             'held-out outcome benchmark is missing')
        from knowledge_bridge import benefit_benchmark
        return benefit_benchmark

    def test_worker_is_an_actual_selected_runtime(self):
        benchmark = self.module()
        with self.assertRaisesRegex(ValueError, 'BENEFIT_WORKER'):
            benchmark.run(CM, lambda payload: {'ok': True})

    def test_direct_graph_tie_is_not_promoted_to_coding_superiority(self):
        benchmark = self.module()
        rows = [{'case': 'separate-task', 'variant': variant, 'repeat': repeat,
                 'regression_passed': variant != 'lexical',
                 'missing_required_sources': [], 'unnecessary_changes': [],
                 'read_bytes': 100, 'elapsed_seconds': 0.1,
                 'changed_paths': ['worker.py'], 'patch_digest': 'a' * 64}
                for variant in benchmark.VARIANTS for repeat in range(2)]
        result = benchmark.summarize(rows)
        self.assertEqual(result['direct_graph_pass_delta'], 0)
        self.assertEqual(result['coding_benefit'], 'UNVERIFIED')
        self.assertFalse(result['default_graph'])
        self.assertTrue(result['deterministic_outcomes_stable'])

    def test_three_separate_case_oracles_do_not_come_from_retrieval(self):
        benchmark = self.module()
        cases = benchmark.fixtures()
        self.assertEqual(len(cases), 3)
        self.assertEqual(len({case['id'] for case in cases}), 3)
        for case in cases:
            self.assertEqual(set(case['required_sources']), {'api', 'client', 'worker', 'policy', 'regression'})
            self.assertEqual(case['required_test_ids'], ['regression.Check.test_primary',
                                                       'regression.Check.test_boundary',
                                                       'regression.Check.test_distractor'])
            self.assertIn(case['patch']['path'], case['files'])
            self.assertIn(case['patch']['old'], case['files'][case['patch']['path']])
            self.assertNotIn(case['patch']['new'] + '\n', case['files'][case['patch']['path']])

    def test_empty_measurements_do_not_report_a_stable_tie(self):
        result = self.module().summarize([])
        self.assertFalse(result['deterministic_outcomes_stable'])
        self.assertIsNone(result['direct_graph_pass_delta'])


@unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON'), 'explicit pinned runtime not selected')
class RealBenefit(unittest.TestCase):
    module = BenefitContract.module
    def test_real_case_runs_regressions_and_preserves_fair_direct_baseline(self):
        benchmark = self.module()
        from knowledge_bridge.worker_client import WorkerClient
        result = benchmark.run_case(benchmark.fixtures()[0], CM,
                                    WorkerClient(os.environ['KNOWLEDGE_WORKER_PYTHON'], timeout=60))
        self.assertFalse(result['baseline']['regression_passed'])
        self.assertEqual(len(result['runs']), 8)
        for variant in ('direct', 'graph', 'graph+audit'):
            rows = [row for row in result['runs'] if row['variant'] == variant]
            self.assertTrue(all(row['regression_passed'] for row in rows), rows)
            self.assertTrue(all(not row['missing_required_sources'] for row in rows), rows)
            self.assertTrue(all(not row['unnecessary_changes'] for row in rows), rows)
            for row in rows:
                self.assertIn('used_source_versions', row)
                self.assertEqual(row['used_source_versions'],
                                 {ident: result['source_versions'][ident] for ident in row['observed_sources']})
                self.assertEqual(row['stale_source_uses'], 0)
        direct = next(row for row in result['runs'] if row['variant'] == 'direct')
        self.assertEqual(set(direct['observed_sources']), set(result['source_versions']))
        self.assertLessEqual(direct['read_bytes'], direct['source_byte_budget'])
        audited = [row for row in result['runs'] if row['variant'] == 'graph+audit']
        self.assertTrue(all(row['audit']['evidence_class'] == 'STRUCTURED_AUDIT' for row in audited))
        self.assertTrue(all(row['audit']['omission_detected'] and row['audit']['flip_detected']
                            for row in audited))
        self.assertTrue(result['faults']['missing_source_blocked'])
        self.assertTrue(result['faults']['stale_source_blocked'])
        self.assertTrue(result['faults']['revoked_source_blocked'])
        self.assertTrue(result['faults']['repair_current'])


if __name__ == '__main__':
    unittest.main()
