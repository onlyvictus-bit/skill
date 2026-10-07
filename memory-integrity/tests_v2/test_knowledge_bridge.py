"""Knowledge bridge adversarial contracts and real optional runtime checks."""
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
sys.path.insert(0,str(ROOT/'scripts'))
CM = ROOT.parent/'claude-mon'

class Fixture(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('knowledge_bridge'), 'governed knowledge bridge is missing')
        from knowledge_bridge import contracts, indexing, retrieval, verification
        self.c, self.i, self.r, self.v = contracts,indexing,retrieval,verification
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.store=self.root/'index'
        for name,text in [('policy','Retry only if read-only; never retry writes.\n'),('client','Client depends on worker.\n'),('worker','Worker retry tests.\n'),('secret','Confidential constraint.\n')]:
            (self.root/(name+'.txt')).write_text(text,encoding='utf-8')
        self.sources={'schema_version':1,'workspace_id':'demo','repository':'fixture','sources':[{'id':n,'path':n+'.txt','authority':'AUTHORITATIVE'} for n in ('policy','client','worker','secret')]}
        def ref(n): return {'source_id':n,'unit_id':'U000001'}
        self.projection={'schema_version':1,'ontology':'project-1','embedding':{'model':'curated-test-vectors','dimension':2,'evidence_class':'TEST_ONLY'},'nodes':[{'id':n,'type':'Assertion' if n=='policy' else 'Component','text':n,'source_units':[ref(n)],'polarity':'positive','conditions':['read-only'] if n=='policy' else [],'derivation':None,'valid_from':None,'valid_until':None,'review_status':'unreviewed','vector':[1.0,0.0] if n=='policy' else [0.0,1.0]} for n in ('policy','client','worker','secret')],'edges':[{'id':'E1','subject':'policy','predicate':'IMPLEMENTS','object':'client','source_units':[ref('policy')],'conditions':[],'valid_from':None,'valid_until':None},{'id':'E2','subject':'client','predicate':'DEPENDS_ON','object':'worker','source_units':[ref('client')],'conditions':[],'valid_from':None,'valid_until':None},{'id':'ES','subject':'policy','predicate':'REFERENCES','object':'secret','source_units':[ref('secret')],'conditions':[],'valid_from':None,'valid_until':None}]}
        self.policy={'schema_version':1,'workspace_id':'demo','task_id':'T1','allowed_source_ids':['policy','client','worker']}
        self.task={'schema_version':1,'task_id':'T1','required_units':[ref('policy')],'require_graph':True,'max_bytes':100000,'execution_task_digest':None}
    def build(self): return self.i.build(self.root,self.sources,self.projection,self.store,CM)

class Bridge(Fixture):
    def test_duplicate_json_and_nonfinite_refused(self):
        for raw in ['{"x":1,"x":2}','{"x":NaN}']:
            with self.assertRaises(ValueError): self.c.loads(raw)
    def test_canonical_manifest_reopen_and_drift(self):
        built=self.build(); g=self.i.load(self.store,self.root,CM)
        self.assertEqual(g['generation'],built['generation'])
        self.assertEqual(g['sources']['policy']['manifest']['units'][0]['id'],'U000001')
        (self.root/'policy.txt').write_text('changed\n')
        with self.assertRaisesRegex(ValueError,'STALE'): self.i.load(self.store,self.root,CM)
    def test_bad_endpoint_missing_unit_duplicate_id_unknown_field_refused(self):
        for change in ['endpoint','unit','duplicate','field','condition','time','vector']:
            with self.subTest(change=change):
                p=copy.deepcopy(self.projection)
                if change=='endpoint': p['edges'][0]['object']='undefined'
                if change=='unit': p['nodes'][0]['source_units'][0]['unit_id']='MISSING'
                if change=='duplicate': p['nodes'].append(p['nodes'][0])
                if change=='field': p['nodes'][0]['READY']=True
                if change=='condition': p['nodes'][0]['conditions']='read-only'
                if change=='time': p['nodes'][0]['valid_until']='invalid'
                if change=='vector': p['nodes'][0]['vector']=[1,0,9]
                with self.assertRaises(ValueError): self.i.build(self.root,self.sources,p,self.store,CM)
    def test_source_escape_refused(self):
        self.sources['sources'][0]['path']='../outside'
        with self.assertRaises(ValueError): self.build()
    def test_interrupted_publication_preserves_current_and_writer_lock(self):
        a=self.build(); before=(self.store/'CURRENT').read_bytes()
        (self.store/'writer.lock').write_text('retained interrupted operation')
        with self.assertRaisesRegex(ValueError,'WRITER'): self.build()
        self.assertEqual((self.store/'CURRENT').read_bytes(),before)
        (self.store/'writer.lock').unlink()
        original=self.i.os.replace
        def fail(src,dst):
            if Path(dst).name=='CURRENT': raise OSError('injected prepublication interruption')
            return original(src,dst)
        self.i.os.replace=fail
        try:
            with self.assertRaises(OSError): self.build()
        finally: self.i.os.replace=original
        self.assertEqual(self.i.load(self.store,self.root,CM)['generation'],a['generation'])
    def test_permission_filter_before_worker_and_pack(self):
        self.build(); g=self.i.load(self.store,self.root,CM)
        seen={}
        def worker(payload):
            seen.update(payload)
            return {'ok':True,'backend':'TEST_ONLY','results':[{'id':'policy','score':1.0,'path':['policy'],'edge_ids':[]}],'limits_reached':[],'lineage':{}}
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,0],worker,max_hops=2)
        self.assertNotIn('secret',json.dumps(seen))
        self.assertNotIn('secret',json.dumps(pack))
        self.assertEqual(pack['units'][0]['text'],'Retry only if read-only; never retry writes.\n')
        self.assertEqual(pack['coverage'],'UNVERIFIED')
    def test_revoked_required_scope_budget_unknown_worker_result_blocks(self):
        self.build(); g=self.i.load(self.store,self.root,CM)
        for mode in ('revoked','budget','foreign'):
            with self.subTest(mode=mode):
                p=copy.deepcopy(self.policy); t=copy.deepcopy(self.task)
                if mode=='revoked': p['allowed_source_ids'].remove('policy')
                if mode=='budget': t['max_bytes']=10
                def worker(payload): return {'ok':True,'backend':'TEST_ONLY','results':[{'id':'secret' if mode=='foreign' else 'policy','score':1,'path':['policy'],'edge_ids':[]}],'limits_reached':[],'lineage':{}}
                with self.assertRaises(ValueError): self.r.retrieve(g,self.root,p,t,[1,0],worker)
    def test_missing_worker_and_bad_query_vector_block(self):
        self.build(); g=self.i.load(self.store,self.root,CM)
        for vec in ([1,0],[1],[0,0],[float('nan'),1]):
            with self.assertRaises(ValueError): self.r.retrieve(g,self.root,self.policy,self.task,vec,None)
    def test_unobserved_stage_is_unknown_not_zero(self):
        expected=[{'id':'C1','text':'retries permitted','polarity':'positive','conditions':['read-only'],'source_units':[{'source_id':'policy','unit_id':'U000001'}]}]
        out=self.v.audit(expected,{'source':None,'retrieval':[],'prompt':None,'answer':None})
        self.assertIsNone(out['metrics']['answer_coverage'])
        self.assertIsNone(out['metrics']['prompt_inclusion'])
        self.assertIn('prompt',out['limitations'])
    def test_id_overlap_reversed_condition_and_unsupported_claim(self):
        e={'id':'C1','text':'retries permitted','polarity':'positive','conditions':['read-only'],'source_units':[{'source_id':'policy','unit_id':'U000001'}]}
        a=dict(e,conditions=['write']); unknown=dict(e,id='C2')
        out=self.v.audit([e],{'source':[e],'retrieval':[e],'prompt':[e],'answer':[a,unknown]})
        self.assertEqual(out['metrics']['prompt_id_overlap'],0.5)
        self.assertEqual(out['metrics']['source_support'],0.0)
        self.assertTrue(any(f['kind']=='CONTRADICTION' for f in out['findings']))
        self.assertTrue(any(f['kind']=='UNSUPPORTED' for f in out['findings']))
    def test_retrieved_constraint_omitted_from_prompt(self):
        e={'id':'C1','text':'condition','polarity':'positive','conditions':[],'source_units':[{'source_id':'policy','unit_id':'U000001'}]}
        out=self.v.audit([e],{'source':[e],'retrieval':[e],'prompt':[],'answer':[]})
        self.assertTrue(any(f['kind']=='CONTEXT_GAP' for f in out['findings']))

class Runtime(Fixture):
    def setUp(self):
        if not os.environ.get('KNOWLEDGE_WORKER_PYTHON'): self.skipTest('explicit pinned Semantica runtime not selected')
        super().setUp()
        from knowledge_bridge.worker_client import WorkerClient
        self.worker=WorkerClient(os.environ['KNOWLEDGE_WORKER_PYTHON'],timeout=45)
    def test_real_semantica_two_hop_vectors_lineage_shacl(self):
        hello=self.worker({'op':'handshake'})
        self.assertEqual(hello['semantica_version'],'0.7.0')
        self.assertEqual(hello['revision'],'320761de5d040a54a3220acc563223b4a7ffdc51')
        self.build();g=self.i.load(self.store,self.root,CM)
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,0],self.worker,max_hops=2,seeds=1)
        self.assertEqual([n['id'] for n in pack['retrieval']['results']],['policy','client','worker'])
        self.assertEqual(pack['retrieval']['results'][-1]['path'],['policy','client','worker'])
        self.assertEqual(pack['retrieval']['results'][-1]['edge_ids'],['E1','E2'])
        self.assertEqual(pack['retrieval']['backend'],'SEMANTICA_OBSERVED')
        self.assertTrue(pack['retrieval']['lineage']['policy']['integrity_verified'])
        self.assertEqual(pack['retrieval']['shacl'],'CONFORMS')
    def test_expired_private_nodes_absent_before_runtime(self):
        self.projection['nodes'][1]['valid_until']='2000-01-01T00:00:00Z'
        self.build();g=self.i.load(self.store,self.root,CM)
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,0],self.worker,seeds=1)
        self.assertEqual([r['id'] for r in pack['retrieval']['results']],['policy'])
    def test_wrong_runtime_pin_refused(self):
        from knowledge_bridge.worker_client import WorkerClient
        with self.assertRaises(ValueError): WorkerClient(os.environ['KNOWLEDGE_WORKER_PYTHON'],expected_revision='0'*40)({'op':'handshake'})
    def test_runtime_visit_budget(self):
        self.build();g=self.i.load(self.store,self.root,CM)
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,0],self.worker,seeds=1,max_visits=2)
        self.assertEqual(len(pack['retrieval']['results']),2)
        self.assertIn('max_visits',pack['retrieval']['limits_reached'])
    def test_actual_lineage_contains_recursive_premise(self):
        self.projection['nodes'][0]['derivation']={'rule':'fixture premise','premises':['worker']}
        self.projection['edges']=[]
        self.build();g=self.i.load(self.store,self.root,CM)
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,0],self.worker,max_hops=0)
        self.assertIn('node:worker',pack['retrieval']['lineage']['policy']['lineage_entity_ids'])
        self.assertIn('source:worker:U000001',pack['retrieval']['lineage']['policy']['lineage_entity_ids'])
    def test_nonaxis_real_query_replay_and_worker_timeout(self):
        self.build();g=self.i.load(self.store,self.root,CM)
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,1],self.worker,max_hops=2)
        self.r.verify_pack(pack,g,self.root,self.policy,self.task,self.worker)
        from knowledge_bridge.worker_client import WorkerClient
        with self.assertRaisesRegex(ValueError,'TIMEOUT'):
            WorkerClient(os.environ['KNOWLEDGE_WORKER_PYTHON'],timeout=.001)({'op':'handshake'})

class AdditionalContracts(Fixture):
    def test_nonaxis_query_pack_verifies_without_rounding_drift(self):
        self.task['require_graph']=False
        self.build();g=self.i.load(self.store,self.root,CM)
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,1],None)
        self.r.verify_pack(pack,g,self.root,self.policy,self.task)
    def test_optional_pack_cannot_falsify_embedding_provenance(self):
        self.task['require_graph']=False;self.build();g=self.i.load(self.store,self.root,CM)
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,0],None)
        pack['embedding']=dict(pack['embedding'],evidence_class='HOST_OBSERVED')
        pack['pack_digest']=self.c.digest(self.c.canonical({k:v for k,v in pack.items() if k!='pack_digest'}))
        with self.assertRaisesRegex(ValueError,'EMBEDDING'): self.r.verify_pack(pack,g,self.root,self.policy,self.task)
    def test_unreviewed_derivation_cycle_refused(self):
        self.projection['nodes'][0]['derivation']={'rule':'fixture','premises':['client']}
        self.projection['nodes'][1]['derivation']={'rule':'fixture','premises':['policy']}
        with self.assertRaisesRegex(ValueError,'DERIVATION_CYCLE'): self.build()
    def test_rehashed_forged_assertion_pack_refused(self):
        self.build();g=self.i.load(self.store,self.root,CM)
        def worker(payload): return {'ok':True,'backend':'SEMANTICA_OBSERVED','results':[{'id':'policy','score':1,'path':['policy'],'edge_ids':[]}],'limits_reached':[],'lineage':{}}
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,0],worker)
        pack['assertions'][0]=dict(pack['assertions'][0],conditions=['writes'])
        pack['pack_digest']=self.c.digest(self.c.canonical({k:v for k,v in pack.items() if k!='pack_digest'}))
        with self.assertRaisesRegex(ValueError,'ASSERTION'): self.r.verify_pack(pack,g,self.root,self.policy,self.task)
    def test_different_query_embedding_model_refused(self):
        self.build();g=self.i.load(self.store,self.root,CM)
        with self.assertRaisesRegex(ValueError,'EMBEDDING_MODEL'):
            self.r.retrieve(g,self.root,self.policy,self.task,[1,0],None,query_model='different-model')
    def test_current_acl_loader_does_not_reopen_denied_sources(self):
        self.build();(self.root/'secret.txt').unlink()
        self.i.load(self.store,self.root,CM,allowed_sources=self.policy['allowed_source_ids'])
    def test_corrupted_generation_and_changed_branch_refused(self):
        self.build();pointer=(self.store/'CURRENT').read_text().strip();path=self.store/'generations'/pointer/'generation.json'
        path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'CORRUPT'): self.i.load(self.store,self.root,CM)
        subprocess.run(['git','init',str(self.root)],check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.root),'symbolic-ref','HEAD','refs/heads/fixture-A'],check=True)
        self.build()
        subprocess.run(['git','-C',str(self.root),'symbolic-ref','HEAD','refs/heads/fixture-B'],check=True)
        with self.assertRaisesRegex(ValueError,'REPOSITORY_SCOPE'): self.i.load(self.store,self.root,CM)

class AuditCompletion(Fixture):
    def test_observed_empty_is_blocked_for_nonempty_expectations(self):
        e={'id':'C1','text':'condition','polarity':'positive','conditions':[],'source_units':[{'source_id':'policy','unit_id':'U000001'}]}
        out=self.v.audit([e],dict(source=[],retrieval=[],prompt=[],answer=[]))
        self.assertFalse(out['ok']);self.assertEqual(out['metrics']['answer_coverage'],0)
    def test_source_disagreement_cannot_pass_with_matching_answer_id(self):
        e={'id':'C1','text':'condition','polarity':'positive','conditions':[],'source_units':[{'source_id':'policy','unit_id':'U000001'}]}
        out=self.v.audit([e],dict(source=[dict(e,text='different')],retrieval=[e],prompt=[e],answer=[e]))
        self.assertFalse(out['ok']);self.assertEqual(out['metrics']['source_support'],0)

class SavedPackSecurity(Fixture):
    def test_backend_label_cannot_qualify_graph_required_pack(self):
        self.build();g=self.i.load(self.store,self.root,CM)
        def worker(payload): return {'ok':True,'backend':'TEST_ONLY','results':[{'id':'policy','score':1,'path':['policy'],'edge_ids':[]}],'limits_reached':[],'lineage':{}}
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,0],worker)
        pack['retrieval']['backend']='SEMANTICA_OBSERVED'
        pack['pack_digest']=self.c.digest(self.c.canonical({k:v for k,v in pack.items() if k!='pack_digest'}))
        with self.assertRaises(ValueError): self.r.verify_pack(pack,g,self.root,self.policy,self.task)
    def test_rehashed_unauthorized_path_refused(self):
        self.build();g=self.i.load(self.store,self.root,CM)
        def worker(payload): return {'ok':True,'backend':'SEMANTICA_OBSERVED','results':[{'id':'policy','score':1,'path':['policy'],'edge_ids':[]}],'limits_reached':[],'lineage':{}}
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,0],worker)
        pack['retrieval']['results'][0].update(path=['secret','policy'],edge_ids=['ES'])
        pack['pack_digest']=self.c.digest(self.c.canonical({k:v for k,v in pack.items() if k!='pack_digest'}))
        with self.assertRaisesRegex(ValueError,'PATH'): self.r.verify_pack(pack,g,self.root,self.policy,self.task)
    def test_derivation_premise_units_reopened(self):
        self.projection['nodes'][0]['derivation']={'rule':'policy requires worker premise','premises':['worker']}
        self.projection['edges']=[];self.task['required_units']=[]
        self.build();g=self.i.load(self.store,self.root,CM)
        def worker(payload): return {'ok':True,'backend':'TEST_ONLY','results':[{'id':'policy','score':1,'path':['policy'],'edge_ids':[]}],'limits_reached':[],'lineage':{}}
        pack=self.r.retrieve(g,self.root,self.policy,self.task,[1,0],worker,max_hops=0)
        self.assertEqual({u['source_id'] for u in pack['units']},{'policy','worker'})

if __name__=='__main__': unittest.main()
