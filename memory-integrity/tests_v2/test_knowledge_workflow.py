"""Public entrypoint, exact CAS binding and fail-closed graph expectations."""
import copy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1];ENTRY=ROOT/'scripts/memory_integrity_workflow.py';CM=ROOT.parent/'claude-mon'
sys.path.insert(0,str(ROOT/'scripts'))

class PublicSurface(unittest.TestCase):
    def test_public_front_door_routes_knowledge(self):
        p=subprocess.run([sys.executable,'-B',str(ENTRY),'--help'],capture_output=True,text=True,timeout=20)
        self.assertIn('knowledge-index',p.stdout)
        self.assertIn('knowledge-retrieve',p.stdout)
        self.assertIn('knowledge-audit',p.stdout)
    def test_absolute_worker_executable_required(self):
        from knowledge_bridge.worker_client import WorkerClient
        with self.assertRaisesRegex(ValueError,'WORKER_PATH'): WorkerClient('python')

class RuntimeWorkflow(unittest.TestCase):
    def setUp(self):
        if not os.environ.get('KNOWLEDGE_WORKER_PYTHON'): self.skipTest('explicit pinned runtime not selected')
        from test_knowledge_bridge import Bridge
        self.fixture=Bridge(methodName='test_duplicate_json_and_nonfinite_refused');self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.f=self.fixture;self.base=self.f.root;self.pack_path=self.base/'pack.json';self.run=self.base/'run'
        self.f.task['execution_task_digest']=self.f.c.digest(self.f.c.canonical({'schema_version':3,'instructions':'Review retry constraint'}))
        self.f.build()
        from knowledge_bridge import indexing,retrieval
        from knowledge_bridge.worker_client import WorkerClient
        self.g=indexing.load(self.f.store,self.base,CM)
        self.pack=retrieval.retrieve(self.g,self.base,self.f.policy,self.f.task,[1,0],WorkerClient(os.environ['KNOWLEDGE_WORKER_PYTHON'],timeout=45))
        for name,doc in [('pack',self.pack),('policy',self.f.policy),('obligations',self.f.task)]:
            (self.base/(name+'.json')).write_text(json.dumps(doc),encoding='utf-8')
        self.responses=self.base/'responses.json';self.responses.write_text(json.dumps({'U000001':{'interpretation':'Retry only if read-only; never retry writes.','findings':[],'disposition':'resolved','reviewer':'offline-fixture','unresolved':[]}}),encoding='utf-8')
    def call(self,command,*args):
        p=subprocess.run([sys.executable,'-B',str(ENTRY),command,'--claude-mon-root',str(CM),*map(str,args)],capture_output=True,text=True,timeout=60)
        self.assertTrue(p.stdout,p.stderr)
        return p.returncode,json.loads(p.stdout)
    def extra(self):
        return ['--knowledge-worker-python',os.environ['KNOWLEDGE_WORKER_PYTHON'],'--knowledge-pack',self.pack_path,'--knowledge-index',self.f.store,'--knowledge-root',self.base,'--knowledge-policy',self.base/'policy.json','--knowledge-task',self.base/'obligations.json']
    def run_ok(self):
        code,out=self.call('offline-run','--source',self.base/'policy.txt','--task','Review retry constraint','--responses-file',self.responses,'--run-dir',self.run,*self.extra())
        self.assertEqual(code,0,out);return out
    def verify(self,*args):
        return self.call('verify','--source',self.base/'policy.txt','--run-map',self.run/'run-map.json','--require-knowledge','--knowledge-worker-python',os.environ['KNOWLEDGE_WORKER_PYTHON'],'--knowledge-index',self.f.store,'--knowledge-root',self.base,'--knowledge-policy',self.base/'policy.json','--knowledge-task',self.base/'obligations.json',*args)
    def test_pack_reaches_actual_serialized_request_and_sidecar(self):
        self.run_ok();db=sqlite3.connect(self.run/'ledger.sqlite');db.row_factory=sqlite3.Row
        row=db.execute('SELECT * FROM attempts').fetchone();db.close()
        request=json.loads((self.run/'artifacts'/row['request_digest']).read_text())
        packed=json.loads(request['materials']['context_knowledge_evidence_pack'])
        self.assertEqual(packed,self.pack)
        receipt=json.loads((self.run/'knowledge-execution.json').read_text())
        self.assertEqual(receipt['attempts'][0]['response_digest'],row['response_digest'])
        code,out=self.verify();self.assertEqual(code,0,out)
        self.assertEqual(out['knowledge']['verdict'],'BOUND_OFFLINE')
    def test_resume_without_pack_is_a_downgrade(self):
        self.run_ok()
        code,out=self.call('offline-run','--source',self.base/'policy.txt','--task','Review retry constraint','--responses-file',self.responses,'--run-dir',self.run)
        self.assertNotEqual(code,0,out)
    def test_current_acl_revoke_staleness_and_missing_receipt_block(self):
        self.run_ok()
        (self.base/'policy.json').write_text(json.dumps(dict(self.f.policy,allowed_source_ids=['client','worker'])))
        code,out=self.verify();self.assertNotEqual(code,0,out)
        (self.base/'policy.json').write_text(json.dumps(self.f.policy))
        (self.base/'client.txt').write_text('changed dependency\n')
        code,out=self.verify();self.assertNotEqual(code,0,out)
        (self.run/'knowledge-execution.json').unlink()
        code,out=self.verify();self.assertNotEqual(code,0,out)
    def test_changed_pack_refused_before_new_run_state(self):
        p=copy.deepcopy(self.pack);p['required_units']=[]
        self.pack_path.write_text(json.dumps(p))
        code,out=self.call('offline-run','--source',self.base/'policy.txt','--task','Review retry constraint','--responses-file',self.responses,'--run-dir',self.run,*self.extra())
        self.assertNotEqual(code,0,out);self.assertFalse(self.run.exists())
    def test_unrelated_plain_run_cannot_satisfy_graph_required_verifier(self):
        code,out=self.call('offline-run','--source',self.base/'policy.txt','--task','Review retry constraint','--responses-file',self.responses,'--run-dir',self.run)
        self.assertEqual(code,0,out)
        code,out=self.verify();self.assertNotEqual(code,0,out)
    def test_unrelated_execution_task_blocks_before_state(self):
        code,out=self.call('offline-run','--source',self.base/'policy.txt','--task','Unrelated instruction','--responses-file',self.responses,'--run-dir',self.run,*self.extra())
        self.assertNotEqual(code,0,out);self.assertFalse(self.run.exists())
    def test_audit_requires_protected_run_map(self):
        self.run_ok()
        oracle=self.base/'oracle.json';oracle.write_text('[]')
        code,out=self.call('knowledge-audit','--project-root',self.base,'--index-dir',self.f.store,'--policy-file',self.base/'policy.json','--task-file',self.base/'obligations.json','--worker-python',os.environ['KNOWLEDGE_WORKER_PYTHON'],'--source',self.base/'policy.txt','--run-map',self.run/'missing-map.json','--expected-claims',oracle)
        self.assertNotEqual(code,0,out)
    def test_copied_map_uses_verified_original_run_directory(self):
        self.run_ok();copied=self.base/'copied-map.json';copied.write_bytes((self.run/'run-map.json').read_bytes())
        code,out=self.verify('--run-map',copied);self.assertEqual(code,0,out)

if __name__=='__main__': unittest.main()
