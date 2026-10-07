"""Held-out synthetic mechanism comparison. No model/task-success qualification."""
import argparse
import json
from pathlib import Path
import statistics
import tempfile
import time
from . import contracts as c,indexing,retrieval,verification
from .worker_client import WorkerClient

def run(companion,python,repeats=3):
    c.integer(repeats,1,20,'benchmark repeats')
    rows=[];build_times=[];storage=[]
    for case in ('read-only-retry','schema-migration','cache-invalidation'):
        with tempfile.TemporaryDirectory(prefix='knowledge-bench-') as temp:
            root=Path(temp);store=root/'index';names=('requirement','component','test')
            for n in names: (root/(n+'.txt')).write_bytes((case+': '+n+'\n').encode('utf-8'))
            ref=lambda n:{'source_id':n,'unit_id':'U000001'}
            sources={'schema_version':1,'workspace_id':case,'repository':'synthetic-held-out','sources':[{'id':n,'path':n+'.txt','authority':'AUTHORITATIVE'} for n in names]}
            nodes=[{'id':n,'type':typ,'text':case+': '+n,'source_units':[ref(n)],'polarity':'positive','conditions':[],'derivation':None,'valid_from':None,'valid_until':None,'review_status':'unreviewed','vector':[1,0] if i==0 else [0,1]} for i,(n,typ) in enumerate(zip(names,('Requirement','Component','TestCase')))]
            edges=[{'id':'E'+str(i),'subject':names[i],'predicate':predicate,'object':names[i+1],'source_units':[ref(names[i])],'conditions':[],'valid_from':None,'valid_until':None} for i,predicate in enumerate(('IMPLEMENTS','TESTS'))]
            projection={'schema_version':1,'ontology':'project-1','embedding':{'model':'fixture-vectors','dimension':2,'evidence_class':'TEST_ONLY'},'nodes':nodes,'edges':edges}
            policy={'schema_version':1,'workspace_id':case,'task_id':'T','allowed_source_ids':list(names)}
            task={'schema_version':1,'task_id':'T','required_units':[ref('requirement')],'require_graph':True,'max_bytes':100000,'execution_task_digest':None}
            start=time.perf_counter();indexing.build(root,sources,projection,store,companion);build_times.append(time.perf_counter()-start)
            doc=indexing.load(store,root,companion);storage.append(sum(p.stat().st_size for p in store.rglob('*') if p.is_file()))
            worker=WorkerClient(python,timeout=60)
            # Oracle is independently defined from the source fixture, before retrieval.
            expected=[{'id':n,'text':case+': '+n,'polarity':'positive','conditions':[],'source_units':[ref(n)]} for n in names]
            # Fixed omission injected for every variant, not a generated answer.
            answer=expected[:-1]
            for variant in ('direct-inspection','vector-only','graph','graph-and-audit'):
                for repeat in range(repeats):
                    start=time.perf_counter();audit=None
                    if variant=='direct-inspection':
                        units=[indexing.reopen(doc,root,ref(n)) for n in names];retained=set(names)
                    else:
                        pack=retrieval.retrieve(doc,root,policy,task,[1,0],worker,max_hops=0 if variant=='vector-only' else 2,query_model='fixture-vectors')
                        units=pack['units'];retained={n['id'] for n in pack['assertions']}
                        if variant=='graph-and-audit':
                            stage=[e for e in expected if e['id'] in retained]
                            audit=verification.audit(expected,{'source':expected,'retrieval':stage,'prompt':stage,'answer':answer})
                    rows.append({'case':case,'variant':variant,'repeat':repeat,'elapsed_seconds':time.perf_counter()-start,'source_unit_recall':len(retained&set(names))/len(names),'retained_source_bytes':sum(len(u['text'].encode('utf-8')) for u in units),'audit_omission_detected':None if audit is None else any(f.get('kind') in ('OBSERVED_LOSS','REQUIRED_CLAIM_MISSING') for f in audit['findings'])})
    summaries=[]
    for variant in ('direct-inspection','vector-only','graph','graph-and-audit'):
        selected=[r for r in rows if r['variant']==variant]
        summaries.append({'variant':variant,'runs':len(selected),'median_seconds':statistics.median(r['elapsed_seconds'] for r in selected),'mean_source_unit_recall':statistics.mean(r['source_unit_recall'] for r in selected),'mean_retained_source_bytes':statistics.mean(r['retained_source_bytes'] for r in selected),'omission_detection_rate':None if variant!='graph-and-audit' else statistics.mean(r['audit_omission_detected'] for r in selected)})
    return {'schema_version':1,'evidence_class':'TEST_ONLY','scope':'3 held-out synthetic cases; supplied vectors; fixed structured omission; no model calls','case_count':3,'repeats':repeats,'initial_index_seconds':build_times,'index_storage_bytes':storage,'summaries':summaries,'runs':rows,'model_usage':0,'task_success':None,'coding_benefit':'UNVERIFIED','default_graph':False,'limitations':['No independent embedding quality assessment','No generated coding result or regression assessment','Whole generation rebuild; no incremental invalidation optimization','Worker process startup included; no token/provider cost measured','Readiness test, not representative-workload superiority']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--claude-mon-root',required=True);p.add_argument('--worker-python',required=True);p.add_argument('--repeats',type=int,default=3)
    args=p.parse_args();print(json.dumps(run(args.claude_mon_root,args.worker_python,args.repeats),indent=2))
