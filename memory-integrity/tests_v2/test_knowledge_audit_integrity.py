"""Independent-oracle integrity across real stage bytes and public preflight."""
import copy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from knowledge_bridge import contracts as c, trace_adapter, verification
from test_knowledge_bridge import Fixture, CM


class StageIntegrity(unittest.TestCase):
    def setUp(self):
        self.claim = {'id': 'C1', 'text': 'retries permitted', 'polarity': 'positive',
                      'conditions': ['read-only'],
                      'source_units': [{'source_id': 'policy', 'unit_id': 'U000001'}]}

    def test_retrieval_content_disagreement_blocks_despite_matching_ids(self):
        e = self.claim
        out = verification.audit([e], dict(source=[e], retrieval=[dict(e, conditions=['write'])],
                                          prompt=[e], answer=[e]))
        self.assertFalse(out['ok'])
        self.assertTrue(any(f['kind'] == 'PROPOSITION_MISMATCH' and f['stage'] == 'retrieval'
                            for f in out['findings']))

    def test_partial_stage_omissions_are_unknown_not_observed_losses(self):
        e = self.claim
        for stage in ('retrieval', 'prompt', 'answer'):
            with self.subTest(stage=stage):
                stages = {name: [e] for name in ('source', 'retrieval', 'prompt', 'answer')}
                stages[stage] = {'state': 'PARTIAL', 'claims': []}
                out = verification.audit([e], stages)
                self.assertIn(stage, out['limitations'])
                self.assertFalse(out['ok'])
                self.assertFalse(any(f['stage'] == stage for f in out['findings']))

    def test_partial_stage_observed_contradiction_still_blocks(self):
        e = self.claim
        out = verification.audit([e], dict(source=[e], retrieval=[e], prompt=[e],
                                          answer={'state': 'PARTIAL',
                                                  'claims': [dict(e, polarity='negative')]}))
        self.assertTrue(any(f['kind'] == 'CONTRADICTION' for f in out['findings']))
        self.assertIsNone(out['metrics']['answer_coverage'])

    def trace(self, assertions, interpretation=None, premises=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        run = Path(temp.name)
        (run / 'artifacts').mkdir()
        pack = {'units': self.claim['source_units'], 'assertions': assertions,
                'premises': premises or []}
        req = {'materials': {'context_knowledge_evidence_pack': c.canonical(pack).decode('utf-8')}}
        response = {'results': {'U000001': {'interpretation': interpretation or
                                           json.dumps({'claims': [self.claim]})}}}
        hashes = []
        for value in (req, response):
            raw = c.canonical(value)
            hashes.append(c.digest(raw))
            (run / 'artifacts' / hashes[-1]).write_bytes(raw)
        with closing(sqlite3.connect(run / 'ledger.sqlite')) as db, db:
            db.execute('CREATE TABLE attempts (id INTEGER PRIMARY KEY, request_digest TEXT, response_digest TEXT)')
            db.execute('CREATE TABLE accepted (attempt_id INTEGER, revoked INTEGER)')
            db.execute('INSERT INTO attempts VALUES (1,?,?)', hashes)
            db.execute('INSERT INTO accepted VALUES (1,0)')
        return run, pack

    def test_trace_uses_actual_retrieval_and_prompt_propositions(self):
        changed = dict(self.claim, conditions=['write'])
        run, pack = self.trace([changed])
        stages = trace_adapter.observed_stages(run, pack, [self.claim],
                                              source_units=self.claim['source_units'])
        self.assertEqual(stages['retrieval'], [changed])
        self.assertEqual(stages['prompt'], [changed])
        out = verification.audit([self.claim], stages)
        self.assertFalse(out['ok'])

    def test_current_source_is_not_lost_when_retrieval_omits_it(self):
        run, pack = self.trace([])
        pack['units'] = []
        stages = trace_adapter.observed_stages(run, pack, [self.claim],
                                              source_units=self.claim['source_units'])
        out = verification.audit([self.claim], stages)
        self.assertEqual(stages['source'], [self.claim])
        self.assertEqual(stages['retrieval'], [])
        self.assertFalse(any(f['stage'] == 'source' for f in out['findings']))
        self.assertTrue(any(f['stage'] == 'retrieval' and f['kind'] == 'OBSERVED_LOSS'
                            for f in out['findings']))

    def test_uninstrumented_source_basis_is_unknown(self):
        run, pack = self.trace([self.claim])
        stages = trace_adapter.observed_stages(run, pack, [self.claim])
        self.assertIsNone(stages['source'])
        self.assertIn('source', verification.audit([self.claim], stages)['limitations'])

    def test_reopened_prompt_unit_is_distinct_from_injected_assertion(self):
        run, pack = self.trace([])
        stages = trace_adapter.observed_stages(run, pack, [self.claim],
                                              source_units=self.claim['source_units'])
        # The curated proposition may be found via its source bytes even without
        # an extracted assertion. Transport does not fabricate an extraction.
        self.assertEqual(stages['prompt'], [self.claim])
        self.assertEqual(stages['retrieval'], [])

    def test_retrieved_recursive_premise_is_not_reported_as_lost(self):
        run, pack = self.trace([], premises=[self.claim])
        stages = trace_adapter.observed_stages(run, pack, [self.claim],
                                              source_units=self.claim['source_units'])
        self.assertEqual(stages['retrieval'], [self.claim])
        self.assertTrue(verification.audit([self.claim], stages)['ok'])


class OptionalReceiptIntegrity(Fixture):
    def setUp(self):
        super().setUp()
        self.task['require_graph'] = False
        self.task['execution_task_digest'] = self.c.digest(self.c.canonical(
            {'schema_version': 3, 'instructions': 'Review retry constraint'}))
        self.build()
        self.doc = self.i.load(self.store, self.root, CM)
        self.pack = self.r.retrieve(self.doc, self.root, self.policy, self.task, [1, 0], None)

    def rehash(self, pack):
        pack['pack_digest'] = c.digest(c.canonical({k: v for k, v in pack.items() if k != 'pack_digest'}))
        return pack

    def test_unknown_nested_receipt_keys_are_refused(self):
        pack = copy.deepcopy(self.pack)
        pack['retrieval']['READY'] = True
        self.rehash(pack)
        with self.assertRaises(ValueError):
            self.r.verify_pack(pack, self.doc, self.root, self.policy, self.task)

    def test_foreign_backend_cannot_qualify_optional_pack(self):
        pack = copy.deepcopy(self.pack)
        pack['retrieval']['backend'] = 'FORGED_BACKEND'
        self.rehash(pack)
        with self.assertRaises(ValueError):
            self.r.verify_pack(pack, self.doc, self.root, self.policy, self.task)

    def test_degraded_pack_cannot_claim_shacl_or_lineage(self):
        for key, value in [('shacl', 'CONFORMS'),
                           ('lineage', {'secret': {'integrity_verified': True}})]:
            with self.subTest(key=key):
                pack = copy.deepcopy(self.pack)
                pack['retrieval'][key] = value
                self.rehash(pack)
                with self.assertRaises(ValueError):
                    self.r.verify_pack(pack, self.doc, self.root, self.policy, self.task)

    def public_run(self, pack, name):
        for filename, doc in [('pack.json', pack), ('policy.json', self.policy),
                              ('task.json', self.task)]:
            (self.root / filename).write_bytes(c.canonical(doc))
        (self.root / 'responses.json').write_bytes(c.canonical({'U000001': {
            'interpretation': 'Retry only if read-only; never retry writes.', 'findings': [],
            'disposition': 'resolved', 'reviewer': 'offline-fixture', 'unresolved': []}}))
        run = self.root / name
        args = [sys.executable, '-B', str(ROOT / 'scripts/memory_integrity_workflow.py'),
                'offline-run', '--claude-mon-root', str(CM), '--source', str(self.root / 'policy.txt'),
                '--task', 'Review retry constraint', '--responses-file', str(self.root / 'responses.json'),
                '--run-dir', str(run), '--knowledge-pack', str(self.root / 'pack.json'),
                '--knowledge-index', str(self.store), '--knowledge-root', str(self.root),
                '--knowledge-policy', str(self.root / 'policy.json'),
                '--knowledge-task', str(self.root / 'task.json')]
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        return result.returncode, json.loads(result.stdout), run

    def test_public_preflight_rejects_forged_pack_before_run_state(self):
        pack = copy.deepcopy(self.pack)
        pack['retrieval']['shacl'] = 'CONFORMS'
        code, out, run = self.public_run(self.rehash(pack), 'forged-run')
        self.assertNotEqual(code, 0, out)
        self.assertEqual(out['overall'], 'BLOCKED')
        self.assertFalse(run.exists())

    def test_valid_direct_fallback_preserves_protected_workflow(self):
        code, out, run = self.public_run(self.pack, 'valid-run')
        self.assertEqual(code, 0, out)
        self.assertEqual(out['knowledge']['verdict'], 'BOUND_OFFLINE')
        self.assertTrue((run / 'knowledge-execution.json').is_file())


if __name__ == '__main__':
    unittest.main()
