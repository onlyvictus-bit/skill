"""Advanced discovery stays source-bound and never returns an authoritative answer."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


def fixture():
    ids = ['alpha', 'beta', 'gamma', 'unrelated']
    nodes = [{'id': ident, 'type': 'Component', 'text': text,
              'source_units': [{'source_id': ident, 'unit_id': 'U000001'}],
              'polarity': 'positive', 'conditions': [], 'derivation': None,
              'valid_from': None, 'valid_until': None, 'review_status': 'unreviewed',
              'vector': [1.0, 0.0]}
             for ident, text in zip(ids, ['alpha validation policy', 'beta validation caller',
                                          'gamma validation worker', 'unrelated billing'])]
    edges = [{'id': ident, 'subject': left, 'object': right, 'predicate': 'DEPENDS_ON',
              'source_units': [{'source_id': left, 'unit_id': 'U000001'}],
              'conditions': [], 'valid_from': None, 'valid_until': None}
             for ident, left, right in [('ab', 'alpha', 'beta'), ('bc', 'beta', 'gamma')]]
    return nodes, edges


class AdvancedRetrieval(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('knowledge_bridge.advanced_retrieval'),
                             'advanced retrieval module missing')
        from knowledge_bridge import advanced_retrieval
        self.a = advanced_retrieval
        self.nodes, self.edges = fixture()

    def test_unknown_strategy_fails_before_optional_import(self):
        with self.assertRaisesRegex(ValueError, 'E_ADVANCED_STRATEGY'):
            self.a.retrieve(self.nodes, self.edges, 'alpha', strategy='unknown')

    def test_prepared_vector_dimension_is_checked_before_runtime_imports(self):
        with self.assertRaisesRegex(ValueError, 'E_ADVANCED_VECTOR_BASIS'):
            self.a.retrieve(self.nodes, self.edges, 'alpha', vectors=[[1]] * 4,
                            query_vector=[1, 0], embedding_metadata={'dimension': 2})

    @unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON'), 'pinned runtime required')
    def test_all_three_real_adapters_return_only_authored_paths(self):
        # Run in the selected pinned runtime, preserving optional dependency isolation.
        import json
        import subprocess
        code = "import sys,json,socket;sys.path.insert(0,sys.argv[1]);from knowledge_bridge.worker import runtime_identity;runtime_identity();from knowledge_bridge.advanced_retrieval import retrieve;n,e=json.loads(sys.argv[2]);results=[retrieve(n,e,'alpha validation',strategy=s,max_hops=2) for s in ('community','global','drift')];assert results==[retrieve(n,e,'alpha validation',strategy=s,max_hops=2) for s in ('community','global','drift')];print(json.dumps(results))"
        run = subprocess.run([os.environ['KNOWLEDGE_WORKER_PYTHON'], '-B', '-c', code,
                              str(Path(__file__).resolve().parents[1] / 'scripts'),
                              json.dumps([self.nodes, self.edges])], capture_output=True,
                             text=True, encoding='utf-8', timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        for mode, result in zip(('community', 'global', 'drift'), json.loads(run.stdout)):
            self.assertTrue(result['results'], mode)
            self.assertNotIn('answer', result)
            self.assertNotIn('response', result)
            self.assertEqual(result['diagnostics']['strategy'], mode)
            self.assertEqual(result['diagnostics']['semantic_truth'], 'UNVERIFIED')
            for candidate in result['results']:
                for index, edge_id in enumerate(candidate['edge_ids']):
                    edge = next(e for e in self.edges if e['id'] == edge_id)
                    self.assertEqual((candidate['path'][index], candidate['path'][index + 1]),
                                     (edge['subject'], edge['object']))

    @unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON'), 'pinned runtime required')
    def test_global_report_findings_bind_exact_source_node_text(self):
        import json
        import subprocess
        code = "import sys,json;sys.path.insert(0,sys.argv[1]);from knowledge_bridge.worker import runtime_identity;runtime_identity();from knowledge_bridge.advanced_retrieval import retrieve;n,e=json.loads(sys.argv[2]);r=retrieve(n,e,'alpha validation',strategy='global');print(json.dumps(r))"
        run = subprocess.run([os.environ['KNOWLEDGE_WORKER_PYTHON'], '-B', '-c', code,
                              str(Path(__file__).resolve().parents[1] / 'scripts'),
                              json.dumps([self.nodes, self.edges])], capture_output=True,
                             text=True, encoding='utf-8', timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        diag = json.loads(run.stdout)['diagnostics']
        self.assertEqual(diag['report_kind'], 'SOURCE_BOUND_EXTRACTIVE')
        self.assertEqual(diag['provider_calls'], 0)
        self.assertEqual(len(diag['reports_digest']), 64)

