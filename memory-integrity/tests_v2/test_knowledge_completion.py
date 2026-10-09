"""Source impact, actual local test evidence and non-circular admission gates."""
import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));CM=ROOT.parent/'claude-mon'
from knowledge_bridge import contracts as c,indexing
class RemainingPublicContract(unittest.TestCase):
 def test_explicit_local_model_client_exists(self):
  from knowledge_bridge import worker_client
  self.assertTrue(hasattr(worker_client,'ModelClient'),'bounded explicit local model client is missing')
 def test_advanced_retrieval_receipt_has_separate_validator(self):
  from knowledge_bridge import retrieval_v2
  self.assertTrue(hasattr(retrieval_v2,'validate_advanced_receipt'),'versioned advanced retrieval binding is missing')
 def test_model_client_rejects_wrong_input_hash_and_token_counts(self):
  from knowledge_bridge.worker_client import ModelClient
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   manifest=Path(d)/'models.json';manifest.write_text('{}');client=ModelClient(Path(sys.executable).absolute(),manifest)
   bad={'ok':True,'operation':'embedding','model':{'manifest_digest':client.manifest_digest},
        'vectors':[[1,0]],'input_sha256':['0'*64],'input_token_counts':[1],'input_token_ids':[[1]]}
   with patch('knowledge_bridge.worker_client._process',return_value=bad):
    with self.assertRaisesRegex(ValueError,'E_MODEL_INPUT_BINDING'):client({'op':'embed','texts':['correct source']})
 @unittest.skipUnless(os.name=='posix' and Path('/proc').exists(),'POSIX process-group observation required')
 def test_timeout_terminates_worker_descendants(self):
  from knowledge_bridge.worker_client import _process
  import time
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);pidfile=root/'child.pid';script=root/'worker.py';heartbeat=root/'heartbeat'
   child='from pathlib import Path\nimport time\np=Path('+repr(str(heartbeat))+')\nfor n in range(3000):\n p.write_text(str(n))\n time.sleep(.02)\n'
   script.write_text('import subprocess,sys,time\nfrom pathlib import Path\nchild=subprocess.Popen([sys.executable,"-c",'+repr(child)+'])\nPath('+repr(str(pidfile))+').write_text(str(child.pid))\ntime.sleep(60)\n')
   with self.assertRaisesRegex(ValueError,'E_WORKER_TIMEOUT'):
    _process(sys.executable,script,{},.5,c.digest(Path(sys.executable).read_bytes()))
   pid=int(pidfile.read_text());before=heartbeat.read_text();time.sleep(.15)
   alive=heartbeat.read_text()!=before
   if alive:
    try:os.kill(pid,9)
    except ProcessLookupError:pass
   self.assertFalse(alive,'worker child survived outer timeout')
 @unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON'),'explicit pinned runtime required')
 def test_public_advanced_modes_source_closure_and_replay(self):
  from knowledge_bridge import impact,retrieval
  from knowledge_bridge.worker_client import WorkerClient
  fixture=Completion();fixture.setUp();self.addCleanup(fixture.doCleanups)
  impact.build(fixture.root,fixture.map,fixture.store,CM)
  policy={'schema_version':1,'workspace_id':'w','task_id':'t','allowed_source_ids':['client','worker','test']}
  task={'schema_version':1,'task_id':'t','required_units':[{'source_id':'worker','unit_id':'U000001'}],'require_graph':True,'max_bytes':200000,'execution_task_digest':c.digest(c.canonical({'schema_version':3,'instructions':'inspect work'}))}
  for name,value in [('policy',policy),('task',task)]: (fixture.root/(name+'.json')).write_bytes(c.canonical(value))
  for strategy,execution in [('community','single'),('global','single'),('drift','single'),('vector','distributed-local')]:
   with self.subTest(strategy=strategy,execution=execution):
    path=fixture.root/(strategy+'-'+execution+'.json')
    cmd=[sys.executable,'-B',str(ROOT/'scripts/memory_integrity_workflow.py'),'knowledge-retrieve','--claude-mon-root',str(CM),'--project-root',str(fixture.root),'--index-dir',str(fixture.store),'--policy-file',str(fixture.root/'policy.json'),'--task-file',str(fixture.root/'task.json'),'--query-text','work','--evidence-pack',str(path),'--worker-python',os.environ['KNOWLEDGE_WORKER_PYTHON'],'--strategy',strategy,'--execution',execution]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=90);self.assertEqual(p.returncode,0,p.stdout+p.stderr)
    pack=c.read(path);self.assertEqual(pack['retrieval']['schema_version'],3)
    self.assertIn(('worker','U000001'),{(u['source_id'],u['unit_id']) for u in pack['units']})
    doc=indexing.load(fixture.store,fixture.root,CM)
    replay=WorkerClient(os.environ['KNOWLEDGE_WORKER_PYTHON'])
    retrieval.verify_pack(pack,doc,fixture.root,policy,task,replay)
    changed=copy.deepcopy(pack);changed['retrieval']['engine']['generation_lease']='0'*64
    changed['pack_digest']=c.digest(c.canonical({k:v for k,v in changed.items() if k!='pack_digest'}))
    with self.assertRaisesRegex(ValueError,'LEASE'):retrieval.verify_pack(changed,doc,fixture.root,policy,task,replay)
class Completion(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.store=self.root/'index'
  self.map={'schema_version':1,'workspace_id':'w','repository':'example','sources':[{'id':'client','path':'client.py','authority':'AUTHORITATIVE'},{'id':'worker','path':'worker.py','authority':'AUTHORITATIVE'},{'id':'test','path':'test_sample.py','authority':'SUPPORTING'}]}
  (self.root/'client.py').write_text('from worker import work\ndef call():\n    return work()\n')
  (self.root/'worker.py').write_text('def work():\n    return 2\n')
  (self.root/'test_sample.py').write_text('import unittest\nfrom worker import work\nclass Check(unittest.TestCase):\n    def test_work(self):\n        self.assertEqual(work(), 2)\n')
 def modules(self):
  from knowledge_bridge import impact,test_evidence,admission
  return impact,test_evidence,admission
 def build(self):
  impact,_,_=self.modules();return impact.build(self.root,self.map,self.store,CM)
 def test_same_branch_unrelated_commit_and_incremental_reuse(self):
  impact,_,_=self.modules()
  for args in [('init',),('config','user.email','fixture@example.invalid'),('config','user.name','Fixture'),('add','.'),('commit','-m','initial')]:subprocess.run(['git','-C',str(self.root),*args],check=True,capture_output=True)
  self.build();doc=indexing.load(self.store,self.root,CM)
  (self.root/'unrelated.txt').write_text('unrelated')
  for args in [('add','unrelated.txt'),('commit','-m','unrelated')]:subprocess.run(['git','-C',str(self.root),*args],check=True,capture_output=True)
  current=indexing.load(self.store,self.root,CM);self.assertEqual(doc['generation'],current['generation'])
  (self.root/'worker.py').write_text('def work():\n    return 3\n')
  stale=indexing.load(self.store,self.root,CM);self.assertEqual(stale['stale_sources'],['worker']);self.assertTrue(stale['invalidated_nodes'])
  self.assertTrue(any(n['id'] in stale['invalidated_nodes'] for n in stale['projection']['nodes'] if n['source_units'][0]['source_id']=='client'))
  refreshed=impact.build(self.root,self.map,self.store,CM);self.assertNotEqual(refreshed['generation'],doc['generation']);self.assertEqual(refreshed['reused_sources'],2)
 def test_source_edit_between_extraction_and_publication_is_refused(self):
  from unittest.mock import patch
  impact,_,_=self.modules();original=indexing.build
  def race(*args,**kwargs):
   (self.root/'worker.py').write_text('def changed():\n    return 3\n')
   return original(*args,**kwargs)
  with patch.object(indexing,'build',race):
   with self.assertRaisesRegex(ValueError,'STALE'):self.build()
  self.assertFalse((self.store/'CURRENT').exists())
 def test_branch_change_blocks_current_use(self):
  self.modules()
  for args in [('init',),('config','user.email','fixture@example.invalid'),('config','user.name','Fixture'),('add','.'),('commit','-m','initial')]:subprocess.run(['git','-C',str(self.root),*args],check=True,capture_output=True)
  self.build();subprocess.run(['git','-C',str(self.root),'checkout','-b','other'],check=True,capture_output=True)
  with self.assertRaisesRegex(ValueError,'BRANCH'):indexing.load(self.store,self.root,CM)
 def test_real_tests_fail_and_stale_pass_never_admits(self):
  _,te,_=self.modules();doc=self.build();frozen=indexing.load(self.store,self.root,CM)
  result=te.run(self.root,frozen,['test_sample.py'],timeout=20);self.assertTrue(result['ok']);self.assertEqual(result['cases'][0]['status'],'pass')
  self.assertTrue(result['cases'][0]['source_units']);te.verify(result,self.root,frozen)
  (self.root/'worker.py').write_text('def work():\n    return 3\n')
  with self.assertRaisesRegex(ValueError,'STALE'):te.verify(result,self.root,frozen)
  self.build();failure=te.run(self.root,indexing.load(self.store,self.root,CM),['test_sample.py'],timeout=20);self.assertFalse(failure['ok']);self.assertEqual(failure['cases'][0]['status'],'fail')
 def test_empty_skipped_and_forged_test_receipt_cannot_pass(self):
  _,te,_=self.modules();(self.root/'test_sample.py').write_text('import unittest\nclass Check(unittest.TestCase):\n    @unittest.skip("fixture")\n    def test_work(self): pass\n')
  self.build();doc=indexing.load(self.store,self.root,CM);result=te.run(self.root,doc,['test_sample.py'],timeout=20);self.assertFalse(result['ok']);self.assertEqual(result['cases'][0]['status'],'skipped')
  forged=copy.deepcopy(result);forged['ok']=True;forged['cases'][0]['status']='pass';forged['receipt_digest']=c.digest(c.canonical({k:v for k,v in forged.items() if k!='receipt_digest'}))
  with self.assertRaisesRegex(ValueError,'REPLAY|MISMATCH'):te.verify(forged,self.root,doc)
  (self.root/'test_sample.py').write_text('import unittest\n');self.build();empty=te.run(self.root,indexing.load(self.store,self.root,CM),['test_sample.py'],timeout=20);self.assertFalse(empty['ok']);self.assertEqual(empty['cases'],[])
 def test_admission_rejects_unknown_assurance_classes(self):
  _,_,ad=self.modules()
  spec={'schema_version':1,'task_id':'t','purpose':'modify retry','criteria':{'REQ-X-1':['test_sample.Check.test_work']},'required_checks':['semantic_truth'],'oracle_review':{'reviewer':'fixture','oracle_digest':'0'*64}}
  with self.assertRaisesRegex(ValueError,'ASSURANCE'):ad.validate_spec(spec)
 def test_requested_extraction_checks_reject_failed_required_parser(self):
  _,_,ad=self.modules();self.build();doc=indexing.load(self.store,self.root,CM)
  doc['construction']['extraction']['sources']['worker']['status']='FAILED'
  with self.assertRaisesRegex(ValueError,'EXTRACTION'):
   ad.check_extraction(['python_syntax_extraction'],doc,self.root,[{'source_id':'worker','unit_id':'U000001'}])
if __name__=='__main__':unittest.main()

class ProtectedAdmission(unittest.TestCase):
 def setUp(self):
  if not os.environ.get('KNOWLEDGE_WORKER_PYTHON'):self.skipTest('explicit pinned runtime not selected')
  self.fixture=Completion('test_admission_rejects_unknown_assurance_classes');self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);self.root=self.fixture.root;self.entry=ROOT/'scripts/memory_integrity_workflow.py'
  (self.root/'policy.md').write_bytes(b'Client depends on Worker.\r\n');self.fixture.map['sources'].append({'id':'policy','path':'policy.md','authority':'AUTHORITATIVE'})
  self.instructions='Verify worker returns 2'
  self.task={'schema_version':1,'task_id':'coding','required_units':[{'source_id':'policy','unit_id':'U000001'}],'require_graph':True,'max_bytes':200000,'execution_task_digest':c.digest(c.canonical({'schema_version':3,'instructions':self.instructions}))}
  self.policy={'schema_version':1,'workspace_id':'w','task_id':'coding','allowed_source_ids':['client','worker','test','policy']}
  self.expected=[{'id':'prose:'+c.digest(b'policy\x00Worker')[:32],'text':'Worker Client depends on Worker.','polarity':'positive','conditions':[],'source_units':[{'source_id':'policy','unit_id':'U000001'}]}]
  for name,value in [('sources',self.fixture.map),('policy',self.policy),('task',self.task),('oracle',self.expected),('responses',{'U000001':{'interpretation':json.dumps({'claims':self.expected}),'findings':[],'disposition':'resolved','reviewer':'independent-fixture','unresolved':[]}})]:self.save(name,value)
 def save(self,name,value): (self.root/(name+'.json')).write_bytes(c.canonical(value));return self.root/(name+'.json')
 def cli(self,cmd,*extra):
  p=subprocess.run([sys.executable,'-B',str(self.entry),cmd,'--claude-mon-root',str(CM),*map(str,extra)],capture_output=True,text=True,timeout=90)
  self.assertTrue(p.stdout,p.stderr);return p.returncode,json.loads(p.stdout)
 def basis(self):return ['--project-root',self.root,'--index-dir',self.fixture.store,'--policy-file',self.root/'policy.json','--task-file',self.root/'task.json','--worker-python',os.environ['KNOWLEDGE_WORKER_PYTHON']]
 def prepare(self):
  code,out=self.cli('knowledge-project','--project-root',self.root,'--index-dir',self.fixture.store,'--source-map',self.root/'sources.json','--worker-python',os.environ['KNOWLEDGE_WORKER_PYTHON']);self.assertEqual(code,0,out)
  code,out=self.cli('knowledge-retrieve',*self.basis(),'--query-text','Worker','--direction','incoming','--evidence-pack',self.root/'pack.json');self.assertEqual(code,0,out)
  code,out=self.cli('knowledge-test',*self.basis(),'--test-path','test_sample.py','--output',self.root/'tests.json');self.assertEqual(code,0,out);self.assertTrue(out['ok'])
  self.receipt=out
  code,out=self.cli('offline-run','--source',self.root/'policy.md','--task',self.instructions,'--responses-file',self.root/'responses.json','--run-dir',self.root/'run','--knowledge-pack',self.root/'pack.json','--knowledge-index',self.fixture.store,'--knowledge-root',self.root,'--knowledge-policy',self.root/'policy.json','--knowledge-task',self.root/'task.json','--knowledge-worker-python',os.environ['KNOWLEDGE_WORKER_PYTHON']);self.assertEqual(code,0,out)
  spec={'schema_version':1,'task_id':'coding','purpose':'verify declared coding criterion','criteria':{'REQ-CODE-1':['test_sample.Check.test_work']},'required_checks':['source_identity','protected_request','structured_oracle','local_tests'],'oracle_review':{'reviewer':'independent-fixture','oracle_digest':c.digest(c.canonical(self.expected))}};self.save('spec',spec)
 def admit_args(self):return [*self.basis(),'--source',self.root/'policy.md','--run-map',self.root/'run/run-map.json','--expected-claims',self.root/'oracle.json','--admission-spec',self.root/'spec.json','--admission-file',self.root/'admission.json','--test-receipt',self.root/'tests.json']
 def test_public_task_relative_admission_and_stale_rejection(self):
  self.prepare();code,out=self.cli('knowledge-admit',*self.admit_args());self.assertEqual(code,0,out);self.assertEqual(out['verdict'],'ADMITTED_FOR_DECLARED_OFFLINE_CHECKS')
  code,out=self.cli('knowledge-check-admission',*self.admit_args());self.assertEqual(code,0,out)
  # Exercise the existing external governor's actual automated-test consumer.
  import importlib.util
  guard_path=Path.home()/'.codex/skills/remote-skills/skill-6ab2a17ee0888191a75c7b5a1171fbbc/scripts/fable_guard.py'
  if guard_path.is_file():
   spec=importlib.util.spec_from_file_location('completion_fable_guard',guard_path);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
   argv=[sys.executable,'-B',str(self.entry),'knowledge-check-admission','--claude-mon-root',str(CM),*map(str,self.admit_args())]
   observation=guard.automated_observation(self.root,'REQ-CODE',['REQ-CODE-1'],'TEST-ADMISSION',{'id':'TEST-ADMISSION','kind':'automated','argv':argv,'expect':'exit=0'},['admission.json','worker.py'],{'requirements_digest':'0'*64,'plan_digest':'0'*64,'tests_digest':'0'*64},90)
   self.assertEqual(observation['result'],'pass',observation)
  from knowledge_bridge import impact,indexing
  fresh=impact.build(self.root,self.fixture.map,self.root/'with-tests',CM,test_receipt=self.receipt);doc=indexing.load(self.root/'with-tests',self.root,CM)
  self.assertTrue(any(n['type']=='TestRun' for n in doc['projection']['nodes']));self.assertTrue(any(e['predicate']=='DERIVED_FROM' for e in doc['projection']['edges']))
  (self.root/'worker.py').write_text('def work():\n    return 3\n')
  code,out=self.cli('knowledge-check-admission',*self.admit_args());self.assertNotEqual(code,0,out)
 def test_criterion_missing_test_and_forged_admission_are_refused(self):
  self.prepare();spec=c.read(self.root/'spec.json');spec['criteria']['REQ-CODE-1']=['test_sample.Check.absent'];self.save('spec',spec)
  code,out=self.cli('knowledge-admit',*self.admit_args());self.assertNotEqual(code,0,out);self.assertFalse((self.root/'admission.json').exists())
  spec['criteria']['REQ-CODE-1']=['test_sample.Check.test_work'];self.save('spec',spec);code,out=self.cli('knowledge-admit',*self.admit_args());self.assertEqual(code,0,out)
  stored=c.read(self.root/'admission.json');stored['purpose']='different purpose';stored['admission_digest']=c.digest(c.canonical({k:v for k,v in stored.items() if k!='admission_digest'}));self.save('admission',stored)
  code,out=self.cli('knowledge-check-admission',*self.admit_args());self.assertNotEqual(code,0,out)
