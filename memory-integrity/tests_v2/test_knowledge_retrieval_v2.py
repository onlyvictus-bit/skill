"""Text retrieval receipts preserve authored direction and current access scope."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
CM = ROOT.parent / 'claude-mon'


class RetrievalV2(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('knowledge_bridge.retrieval_v2'),
                             'text retrieval implementation is missing')
        from knowledge_bridge import contracts, indexing, retrieval_v2
        self.c, self.i, self.r = contracts, indexing, retrieval_v2
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, text in [('policy', 'Retry only read operations.\n'),
                           ('client', 'Client depends on Worker.\n'),
                           ('worker', 'Worker receives client requests.\n'),
                           ('secret', 'Confidential constraint.\n')]:
            (self.root / (name + '.txt')).write_text(text, encoding='utf-8')
        source_map = {'schema_version': 1, 'workspace_id': 'demo', 'repository': 'fixture',
                      'sources': [{'id': n, 'path': n + '.txt', 'authority': 'AUTHORITATIVE'}
                                  for n in ('policy', 'client', 'worker', 'secret')]}
        sources = self.i.freeze(self.root, source_map, CM)
        self.ref = lambda n: {'source_id': n, 'unit_id': 'U000001'}
        nodes = [{'id': n, 'type': 'Assertion' if n == 'policy' else 'Component',
                  'text': {'policy': 'read operation retry policy', 'client': 'client caller',
                           'worker': 'worker receives requests', 'secret': 'Private premise'}[n],
                  'source_units': [self.ref(n)], 'polarity': 'positive', 'conditions': [],
                  'derivation': None, 'valid_from': None, 'valid_until': None,
                  'review_status': 'unreviewed', 'vector': [1, 0]}
                 for n in ('policy', 'client', 'worker', 'secret')]
        edges = [{'id': 'CALLS', 'subject': 'client', 'predicate': 'DEPENDS_ON',
                  'object': 'worker', 'source_units': [self.ref('client')],
                  'conditions': [], 'valid_from': None, 'valid_until': None}]
        self.doc = {'schema_version': 1, 'workspace_id': 'demo', 'repository': 'fixture',
                    'sources': sources, 'source_basis_digest': self.c.digest(self.c.canonical(sources)),
                    'generation': 'a' * 64, 'stale_sources': [], 'invalidated_nodes': [],
                    'projection': {'schema_version': 1, 'ontology': 'project-2',
                                   'embedding': {'model': 'local-text-v1', 'dimension': 256,
                                                 'evidence_class': 'HOST_OBSERVED'},
                                   'nodes': nodes, 'edges': edges}}
        self.policy = {'schema_version': 1, 'workspace_id': 'demo', 'task_id': 'T',
                       'allowed_source_ids': ['policy', 'client', 'worker']}
        self.task = {'schema_version': 1, 'task_id': 'T', 'required_units': [self.ref('policy')],
                     'require_graph': False, 'max_bytes': 100000, 'execution_task_digest': None}
        self.seen = None

    def worker(self, results):
        def invoke(payload):
            self.seen = copy.deepcopy(payload)
            return {'schema_version': 2, 'ok': True, 'backend': 'TEST_ONLY',
                    'results': copy.deepcopy(results), 'limits_reached': [], 'lineage': {},
                    'shacl': 'UNVERIFIED', 'direction': payload['direction'],
                    'embedding_metadata': {'model': 'test-fit', 'dimension': 2,
                        'evidence_class': 'TEST_ONLY', 'mode': payload['embedding_mode'],
                        'algorithm': 'fixture lexical', 'semantic_quality': 'UNVERIFIED',
                        'fit_scope_digest': self.c.digest(self.c.canonical(sorted(
                            [{'id': n['id'], 'text': n['text']} for n in payload['nodes']],
                            key=lambda n: n['id']))), 'sklearn_version': 'fixture',
                        'feature_count': 2, 'document_count': len(payload['nodes']),
                        'lsa_components': 0, 'feature_limit': 2048,
                        'lexical_weight': 1.0, 'query_nonzero_features': 1}}
        return invoke

    def rehash(self, pack):
        pack['pack_digest'] = self.c.digest(self.c.canonical(
            {k: v for k, v in pack.items() if k != 'pack_digest'}))

    def test_incoming_path_retains_authored_edge_and_source_closure(self):
        results = [{'id': 'worker', 'score': 1, 'path': ['worker'], 'edge_ids': []},
                   {'id': 'client', 'score': 0.9, 'path': ['worker', 'client'], 'edge_ids': ['CALLS']}]
        pack = self.r.retrieve(self.doc, self.root, self.policy, self.task, 'worker',
                               self.worker(results), direction='incoming')
        self.assertEqual(pack['retrieval']['results'][1]['edge_ids'], ['CALLS'])
        self.assertEqual(self.seen['edges'][0]['subject'], 'client')
        self.assertEqual(self.seen['op'], 'retrieve_text')
        self.assertEqual({u['source_id'] for u in pack['units']}, {'policy', 'worker', 'client'})
        self.assertEqual(pack['retrieval']['schema_version'], 2)
        self.assertEqual(pack['retrieval']['query_binding']['query_text'], 'worker')

    def test_incoming_edge_cannot_be_relabelled_outgoing(self):
        results = [{'id': 'client', 'score': 0.9, 'path': ['worker', 'client'], 'edge_ids': ['CALLS']}]
        with self.assertRaisesRegex(ValueError, 'E_PATH_EDGE'):
            self.r.retrieve(self.doc, self.root, self.policy, self.task, 'worker',
                            self.worker(results), direction='outgoing')

    def test_both_direction_accepts_authored_reverse_step(self):
        results = [{'id': 'client', 'score': 0.9, 'path': ['worker', 'client'], 'edge_ids': ['CALLS']}]
        pack = self.r.retrieve(self.doc, self.root, self.policy, self.task, 'worker',
                               self.worker(results), direction='both')
        self.assertEqual(pack['retrieval']['direction'], 'both')

    def test_denied_premise_ids_and_text_never_reach_worker_or_pack(self):
        derived = copy.deepcopy(self.doc['projection']['nodes'][0])
        derived.update(id='derived', text='derived visible claim',
                       derivation={'rule': 'private premise rule', 'premises': ['secret']})
        self.doc['projection']['nodes'].append(derived)
        pack = self.r.retrieve(self.doc, self.root, self.policy, self.task, 'worker',
                               self.worker([]))
        self.assertNotIn('secret', json.dumps(self.seen))
        self.assertNotIn('secret', json.dumps(pack))
        self.assertNotIn('Confidential', json.dumps(pack))
        self.assertEqual(pack['retrieval']['exclusions']['outside_current_access'], 1)
        reasons = {e['id']: e['reason'] for e in pack['retrieval']['exclusions']['candidates']}
        self.assertEqual(reasons['derived'], 'premise_unavailable')

    def test_expiry_future_and_staleness_have_authorized_candidate_reasons(self):
        self.doc['projection']['nodes'][1]['valid_until'] = '2000-01-01T00:00:00Z'
        self.doc['projection']['nodes'][2]['valid_from'] = '2100-01-01T00:00:00Z'
        self.doc['invalidated_nodes'] = ['policy']
        self.task['required_units'] = []
        pack = self.r.retrieve(self.doc, self.root, self.policy, self.task, 'policy', None)
        reasons = {e['id']: e['reason'] for e in pack['retrieval']['exclusions']['candidates']}
        self.assertEqual(reasons, {'policy': 'stale', 'client': 'expired', 'worker': 'notyetvalid'})

    def test_stale_mandatory_source_blocks_before_worker(self):
        self.doc['stale_sources'] = ['policy']
        with self.assertRaisesRegex(ValueError, 'E_REQUIRED_STALE'):
            self.r.retrieve(self.doc, self.root, self.policy, self.task, 'worker', self.worker([]))
        self.assertIsNone(self.seen)

    def test_changed_dependency_invalidates_unchanged_mandatory_unit(self):
        self.task['required_units'] = [self.ref('client')]
        self.doc['stale_sources'] = ['worker']
        self.doc['invalidated_nodes'] = ['client', 'worker']
        with self.assertRaisesRegex(ValueError, 'E_REQUIRED_STALE'):
            self.r.retrieve(self.doc, self.root, self.policy, self.task, 'client', self.worker([]))
        self.assertIsNone(self.seen)

    def test_result_unit_order_is_stable_across_python_hash_seeds(self):
        code = "import sys;sys.path[:0]=" + repr([str(ROOT / 'scripts'), str(ROOT / 'tests_v2')]) + "\n"
        code += "from test_knowledge_retrieval_v2 import RetrievalV2\n"
        code += "f=RetrievalV2('test_incoming_path_retains_authored_edge_and_source_closure');f.setUp()\n"
        code += "results=[{'id':'worker','score':1,'path':['worker'],'edge_ids':[]},{'id':'client','score':0.9,'path':['client'],'edge_ids':[]}]\n"
        code += "p=f.r.retrieve(f.doc,f.root,f.policy,f.task,'worker',f.worker(results),seeds=2,direction='incoming')\n"
        code += "print(f.c.canonical(p).decode('utf-8'));f.doCleanups()\n"
        observed = []
        for seed in ('1', '2', '3'):
            result = subprocess.run([sys.executable, '-B', '-c', code], capture_output=True,
                                    text=True, timeout=15, env=dict(os.environ, PYTHONHASHSEED=seed))
            self.assertEqual(result.returncode, 0, result.stderr)
            observed.append(json.loads(result.stdout))
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(observed[0], observed[2])

    def test_receipt_rejects_unknown_nested_candidate_keys(self):
        results = [{'id': 'worker', 'score': 1, 'path': ['worker'], 'edge_ids': []}]
        pack = self.r.retrieve(self.doc, self.root, self.policy, self.task, 'worker', self.worker(results))
        pack['retrieval']['results'][0]['invented_evidence'] = True
        with self.assertRaises(ValueError):
            self.r.validate_receipt(pack['retrieval'])

    def test_optional_stale_source_is_excluded_and_unrelated_required_unit_survives(self):
        self.doc['stale_sources'] = ['worker']
        self.doc['invalidated_nodes'] = ['worker']
        pack = self.r.retrieve(self.doc, self.root, self.policy, self.task, 'policy', None)
        self.r.verify_pack(pack, self.doc, self.root, self.policy, self.task)
        self.assertEqual([u['source_id'] for u in pack['units']], ['policy'])
        self.assertIn({'id': 'worker', 'reason': 'stale'}, pack['retrieval']['exclusions']['candidates'])

    def test_unqualified_direct_receipt_has_no_embedding_or_shacl_claim(self):
        pack = self.r.retrieve(self.doc, self.root, self.policy, self.task, 'read retry', None)
        self.assertIsNone(pack['retrieval']['embedding_metadata'])
        self.assertEqual(pack['retrieval']['shacl'], 'UNVERIFIED')
        self.r.verify_pack(pack, self.doc, self.root, self.policy, self.task)
        forged = copy.deepcopy(pack)
        forged['retrieval']['shacl'] = 'CONFORMS'
        self.rehash(forged)
        with self.assertRaises(ValueError):
            self.r.verify_pack(forged, self.doc, self.root, self.policy, self.task)

    def test_unknown_reason_direction_and_binding_keys_are_rejected(self):
        pack = self.r.retrieve(self.doc, self.root, self.policy, self.task, 'worker', None)
        for field in ('reason', 'direction', 'binding'):
            with self.subTest(field=field):
                forged = copy.deepcopy(pack)
                if field == 'reason': forged['retrieval']['exclusions']['candidates'][0]['reason'] = 'AUTHORIZED_BY_CALLER'
                if field == 'direction': forged['retrieval']['direction'] = 'sideways'
                if field == 'binding': forged['retrieval']['query_binding']['extra'] = True
                self.rehash(forged)
                with self.assertRaises(ValueError):
                    self.r.verify_pack(forged, self.doc, self.root, self.policy, self.task)

    def test_changed_authorized_projection_and_omitted_reasons_do_not_verify(self):
        pack = self.r.retrieve(self.doc, self.root, self.policy, self.task, 'worker', None)
        for field in ('scope', 'reason'):
            with self.subTest(field=field):
                forged = copy.deepcopy(pack)
                if field == 'scope': forged['retrieval']['query_binding']['authorized_projection_digest'] = 'c' * 64
                else: forged['retrieval']['exclusions']['candidates'] = []
                self.rehash(forged)
                with self.assertRaises(ValueError):
                    self.r.verify_pack(forged, self.doc, self.root, self.policy, self.task)

    def test_required_graph_and_mandatory_budget_fail_closed(self):
        self.task['require_graph'] = True
        with self.assertRaisesRegex(ValueError, 'E_GRAPH_RUNTIME_UNAVAILABLE'):
            self.r.retrieve(self.doc, self.root, self.policy, self.task, 'worker', None)
        self.task['require_graph'] = False
        self.task['max_bytes'] = 10
        with self.assertRaisesRegex(ValueError, 'E_PACK_BUDGET'):
            self.r.retrieve(self.doc, self.root, self.policy, self.task, 'worker', None)

    @unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON'),
                         'explicit pinned Semantica runtime not selected')
    def test_actual_text_worker_incoming_replay_is_current_and_exact(self):
        from knowledge_bridge.worker_client import WorkerClient
        worker = WorkerClient(os.environ['KNOWLEDGE_WORKER_PYTHON'], timeout=45)
        self.task['require_graph'] = True
        pack = self.r.retrieve(self.doc, self.root, self.policy, self.task, 'worker receives requests',
                               worker, direction='incoming')
        self.assertEqual([r['id'] for r in pack['retrieval']['results']][:2], ['worker', 'client'])
        self.assertEqual(pack['retrieval']['results'][1]['edge_ids'], ['CALLS'])
        self.assertEqual(pack['retrieval']['embedding_metadata']['evidence_class'], 'HOST_OBSERVED')
        self.r.verify_pack(pack, self.doc, self.root, self.policy, self.task, worker)
        forged = copy.deepcopy(pack)
        forged['retrieval']['embedding_metadata']['model'] = 'invented-model'
        self.rehash(forged)
        with self.assertRaises(ValueError):
            self.r.verify_pack(forged, self.doc, self.root, self.policy, self.task, worker)


if __name__ == '__main__':
    unittest.main()
