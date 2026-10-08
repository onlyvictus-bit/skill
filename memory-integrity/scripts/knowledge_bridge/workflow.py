"""One Memory Integrity front door for optional knowledge operations."""
from pathlib import Path
from . import contracts as c
from . import indexing,retrieval,trace_adapter,verification

def worker(args):
    if not args.worker_python: return None
    from .worker_client import WorkerClient
    return WorkerClient(args.worker_python,timeout=args.worker_timeout)

def register(sub):
    for name in ('knowledge-status','knowledge-index','knowledge-retrieve','knowledge-audit'):
        p=sub.add_parser(name)
        p.add_argument('--claude-mon-root',required=True)
        p.add_argument('--worker-python');p.add_argument('--worker-timeout',type=float,default=30)
        if name=='knowledge-status': continue
        for key in ('project-root','index-dir'): p.add_argument('--'+key,required=True)
        if name=='knowledge-index':
            p.add_argument('--source-map',required=True);p.add_argument('--projection-file',required=True)
        else:
            for key in ('policy-file','task-file'): p.add_argument('--'+key,required=True)
            if name=='knowledge-retrieve':
                p.add_argument('--query-vector',required=True);p.add_argument('--evidence-pack',required=True)
                p.add_argument('--query-model',required=True)
                p.add_argument('--max-hops',type=int,default=2);p.add_argument('--seeds',type=int,default=1)
                p.add_argument('--max-visits',type=int,default=100);p.add_argument('--max-results',type=int,default=50)
            else:
                p.add_argument('--run-map',required=True);p.add_argument('--expected-claims',required=True)
                p.add_argument('--source',required=True)

def dispatch(args):
    indexing.partition_engine(args.claude_mon_root)
    if args.command=='knowledge-status':
        w=worker(args)
        return w({'op':'handshake'}) if w else {'ok':True,'knowledge':'DEGRADED','graph_required_readiness':'BLOCKED','runtime':'UNAVAILABLE','answer_generation':False}
    if args.command=='knowledge-index':
        return indexing.build(args.project_root,c.read(args.source_map),c.read(args.projection_file),args.index_dir,args.claude_mon_root)
    policy=c.read(args.policy_file);task=c.read(args.task_file)
    doc=indexing.load(args.index_dir,args.project_root,args.claude_mon_root,allowed_sources=policy['allowed_source_ids'])
    if args.command=='knowledge-retrieve':
        pack=retrieval.retrieve(doc,args.project_root,policy,task,c.loads(args.query_vector),worker(args),args.max_hops,args.seeds,args.max_visits,args.max_results,query_model=args.query_model)
        if task['require_graph'] and pack['retrieval']['backend']!='SEMANTICA_OBSERVED': raise ValueError('E_GRAPH_REQUIRED')
        target=c.ordinary(args.evidence_pack)
        with target.open('xb') as handle: handle.write(c.canonical(pack))
        return {'ok':True,'overall':'SOURCE_REOPENED','generation':doc['generation'],'pack_digest':pack['pack_digest'],'units':len(pack['units']),'coverage':'UNVERIFIED','semantic_truth':'UNVERIFIED','evidence_pack':str(target),'retrieval_backend':pack['retrieval']['backend'],'limits_reached':pack['retrieval']['limits_reached']}
    from integrity_v2 import report
    rm=c.read(args.run_map)
    checked=report.verify_run(args.run_map,{rm['source_id']:c.digest(Path(args.source).read_bytes())},args.claude_mon_root)
    if not checked.get('ok'): raise ValueError('E_KNOWLEDGE_PROTECTED_RUN: '+str(checked))
    run=Path(rm['run_dir']).resolve();pack=c.read(run/'knowledge-evidence.json')
    bind_execution_task(task,c.read(run/'task.json'))
    retrieval.verify_pack(pack,doc,args.project_root,policy,task,worker(args));trace_adapter.verify(run,pack)
    expected=c.read(args.expected_claims)
    if not isinstance(expected,list): raise ValueError('E_EXPECTED_CLAIMS')
    verification.claims(expected)
    source_units=[]
    for claim in expected:
        c.refs(claim['source_units'],doc['sources'])
        if any(r['source_id'] not in policy['allowed_source_ids'] for r in claim['source_units']): raise ValueError('E_EXPECTED_ACCESS')
        for ref in claim['source_units']:
            source_units.append(indexing.reopen(doc,args.project_root,ref))
    result=verification.audit(expected,trace_adapter.observed_stages(run,pack,expected,source_units=source_units))
    result['evidence_class']='TEST_ONLY';result['source_qualification']='source identity observed; proposition oracle supplied separately and requires review'
    return result

def bind_execution_task(task,actual_task):
    if task['execution_task_digest']!=c.digest(c.canonical(actual_task)): raise ValueError('E_KNOWLEDGE_EXECUTION_TASK: exact task instructions must be bound')

def preflight(args,run=None):
    names=('knowledge_index','knowledge_root','knowledge_policy','knowledge_task')
    values=[getattr(args,n,None) for n in names]
    if any(values) and not all(values): raise ValueError('E_KNOWLEDGE_EXPLICIT_BASIS')
    if not all(values):
        if getattr(args,'knowledge_pack',None) or getattr(args,'require_knowledge',False): raise ValueError('E_KNOWLEDGE_REQUIRED_BASIS')
        return None
    policy=c.read(args.knowledge_policy);task=c.read(args.knowledge_task)
    actual_task=c.read(Path(run)/'task.json') if run else {'schema_version':3,'instructions':args.task}
    bind_execution_task(task,actual_task)
    doc=indexing.load(args.knowledge_index,args.knowledge_root,args.claude_mon_root,allowed_sources=policy['allowed_source_ids'])
    path=getattr(args,'knowledge_pack',None) or (Path(run)/'knowledge-evidence.json' if run else None)
    if path is None: raise ValueError('E_KNOWLEDGE_PACK_REQUIRED')
    from .worker_client import WorkerClient
    executable=getattr(args,'knowledge_worker_python',None)
    replay=WorkerClient(executable,timeout=getattr(args,'knowledge_worker_timeout',30)) if executable else None
    pack=c.read(path);retrieval.verify_pack(pack,doc,args.knowledge_root,policy,task,replay)
    return pack

def verify_run(args,run):
    # Supplying an explicit knowledge contract itself requires checking it.
    basis=any(getattr(args,n,None) for n in ('knowledge_index','knowledge_root','knowledge_policy','knowledge_task'))
    required=getattr(args,'require_knowledge',False) or basis or trace_adapter.has_knowledge(run)
    if not required: return None
    pack=preflight(args,run)
    if pack is None: raise ValueError('E_KNOWLEDGE_REQUIRED_BASIS')
    return trace_adapter.verify(run,pack)
