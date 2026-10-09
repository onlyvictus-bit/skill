"""Two actual pinned workers must merge comparable scores and fail closed."""
import copy
import importlib.util
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from test_knowledge_advanced import fixture


class DistributedRetrieval(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('knowledge_bridge.distributed_retrieval'),
                             'distributed coordinator missing')
        from knowledge_bridge import distributed_retrieval as d
        self.d = d
        nodes, edges = fixture()
        self.payload = {'nodes': nodes, 'edges': edges, 'query_text': 'alpha validation',
                        'embedding_mode': 'lexical', 'direction': 'outgoing', 'seeds': 1,
                        'max_hops': 2, 'max_visits': 100, 'max_results': 50,
                        'generation_lease': 'a' * 64}

    def test_distribution_requires_selected_absolute_runtime(self):
        with self.assertRaisesRegex(ValueError, 'E_WORKER_PATH'):
            self.d.DistributedClient('python')

    @unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON'), 'pinned runtime required')
    def test_real_two_worker_result_equals_single_worker(self):
        from knowledge_bridge.worker_client import WorkerClient
        single_payload = {k: v for k, v in self.payload.items() if k != 'generation_lease'}
        single_payload.update(op='retrieve_text', ontology='project-2')
        single = WorkerClient(os.environ['KNOWLEDGE_WORKER_PYTHON'], timeout=45)(single_payload)
        client = self.d.DistributedClient(os.environ['KNOWLEDGE_WORKER_PYTHON'], timeout=45)
        result = client(self.payload)
        self.assertEqual(result['results'], single['results'])
        self.assertEqual(result['embedding_metadata'], single['embedding_metadata'])
        self.assertEqual(result['limits_reached'], single['limits_reached'])
        self.assertEqual(len(set(client.execution_proof['worker_pids'])), 2)
        self.assertNotIn('worker_pids', result['diagnostics'])
        self.assertEqual(result['diagnostics']['qualification_scope'], 'LOCAL_TWO_PROCESS_SHARDED')
        self.assertEqual(client(self.payload), result)

    @unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON'), 'pinned runtime required')
    def test_killed_owner_blocks_without_partial_pack(self):
        client = self.d.DistributedClient(os.environ['KNOWLEDGE_WORKER_PYTHON'], timeout=15)
        original = client._seed_phase
        def kill(sessions, payload, vectors, query):
            sessions[1].process.kill()
            sessions[1].process.wait(timeout=5)
            return original(sessions, payload, vectors, query)
        client._seed_phase = kill
        with self.assertRaisesRegex(ValueError, 'E_DISTRIBUTED_WORKER'):
            client(self.payload)
        self.assertTrue(all(not item['alive'] for item in client.execution_proof['workers_after_close']))

    def test_reply_binding_rejects_stale_lease_recomputed_digest(self):
        from knowledge_bridge import contracts as c
        reply = {'schema_version': 1, 'lane': 0, 'sequence': 3, 'lease': 'b' * 64,
                 'request_digest': 'd' * 64, 'ok': True, 'result': {}}
        with self.assertRaisesRegex(ValueError, 'E_DISTRIBUTED_REPLY_BINDING'):
            self.d.validate_reply(reply, 0, 3, 'a' * 64, 'd' * 64)

    def test_seed_response_cannot_invent_score_or_duplicate_owner(self):
        # Replies already crossed a real process boundary; validate their content
        # against the independently frozen vector basis as well as the envelope.
        class Session:
            def __init__(self, result): self.result = result
            def request(self, *args): return self.result
        client = self.d.DistributedClient(sys.executable)
        nodes = self.payload['nodes']
        vector = [[1.0, 0.0] for _ in nodes]
        malicious = [{'id': 'alpha', 'score': .2}, {'id': 'alpha', 'score': .2}]
        with self.assertRaisesRegex(ValueError, 'E_DISTRIBUTED_SEED'):
            client._seed_phase([Session({'seeds': malicious}), Session({'seeds': []})],
                               self.payload, vector, [1.0, 0.0])

    @unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON'), 'pinned runtime required')
    def test_real_cross_partition_paths_reverse_and_global_limits(self):
        client = self.d.DistributedClient(os.environ['KNOWLEDGE_WORKER_PYTHON'], timeout=45)
        self.assertNotEqual(self.d.owner('alpha'), self.d.owner('beta'))
        result = client(self.payload)
        self.assertEqual(result['results'][-1]['path'], ['alpha', 'beta', 'gamma'])
        self.assertEqual(result['results'][-1]['edge_ids'], ['ab', 'bc'])
        reverse = dict(self.payload, query_text='gamma validation worker', direction='incoming')
        result = client(reverse)
        self.assertEqual(result['results'][-1]['path'], ['gamma', 'beta', 'alpha'])
        self.assertEqual(result['results'][-1]['edge_ids'], ['bc', 'ab'])
        limited = client(dict(self.payload, max_visits=2))
        self.assertEqual(len(limited['results']), 2)
        self.assertEqual(limited['limits_reached'], ['max_visits'])

    @unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON') and os.name == 'posix', 'POSIX pinned runtime required')
    def test_suspended_worker_expires_shared_deadline_and_is_reaped(self):
        import signal
        import time
        client = self.d.DistributedClient(os.environ['KNOWLEDGE_WORKER_PYTHON'], timeout=15)
        original = client._seed_phase
        def suspend(sessions, payload, vectors, query):
            os.kill(sessions[1].process.pid, signal.SIGSTOP)
            for session in sessions: session.deadline = time.monotonic() + .15
            return original(sessions, payload, vectors, query)
        client._seed_phase = suspend
        with self.assertRaisesRegex(ValueError, 'E_DISTRIBUTED_WORKER_TIMEOUT'):
            client(self.payload)
        self.assertTrue(all(not item['alive'] for item in client.execution_proof['workers_after_close']))

    @unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON'), 'pinned runtime required')
    def test_exact_score_ties_choose_canonical_global_seed(self):
        payload = copy.deepcopy(self.payload)
        for node in payload['nodes']: node['text'] = 'same validation text'
        payload.update(query_text='same validation text', max_hops=0)
        result = self.d.DistributedClient(os.environ['KNOWLEDGE_WORKER_PYTHON'], timeout=45)(payload)
        self.assertEqual([r['id'] for r in result['results']], ['alpha'])

    @unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON'), 'pinned runtime required')
    def test_prepared_shared_vectors_are_used_by_both_actual_shards(self):
        payload = copy.deepcopy(self.payload)
        payload['vector_override'] = {'vectors': [[0, 1], [1, 0], [0, 1], [0, 1]],
                                     'query': [1, 0], 'metadata': {'model': 'fixture-learned',
                                     'fit_scope_digest': 'c' * 64, 'dimension': 2}}
        payload['max_hops'] = 0
        result = self.d.DistributedClient(os.environ['KNOWLEDGE_WORKER_PYTHON'], timeout=45)(payload)
        self.assertEqual([r['id'] for r in result['results']], ['beta'])
        self.assertEqual(result['embedding_metadata'], payload['vector_override']['metadata'])

