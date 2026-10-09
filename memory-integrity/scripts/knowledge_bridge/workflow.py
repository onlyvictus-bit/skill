"""One Memory Integrity front door for optional knowledge operations."""
from pathlib import Path
from . import contracts as c
from . import indexing,retrieval,trace_adapter,verification

def worker(args):
    if not args.worker_python: return None
    from .worker_client import WorkerClient
    return WorkerClient(args.worker_python,timeout=args.worker_timeout,model_client=model_worker(args))

def model_worker(args):
    python=getattr(args,'model_python',None);manifest=getattr(args,'model_manifest',None)
    if bool(python)!=bool(manifest):raise ValueError('E_LOCAL_MODEL_EXPLICIT_SELECTION')
    if not python:return None
    from .worker_client import ModelClient
    return ModelClient(python,manifest,timeout=getattr(args,'model_timeout',120))

def register(sub):
    for name in ('knowledge-status','knowledge-index','knowledge-project','knowledge-refresh','knowledge-impact','knowledge-retrieve','knowledge-test','knowledge-admit','knowledge-check-admission','knowledge-benchmark','knowledge-audit','knowledge-syntax','knowledge-process','knowledge-model-benchmark'):
        p=sub.add_parser(name)
        p.add_argument('--claude-mon-root',required=True)
        p.add_argument('--worker-python');p.add_argument('--worker-timeout',type=float,default=30)
        p.add_argument('--model-python');p.add_argument('--model-manifest');p.add_argument('--model-timeout',type=float,default=120)
        if name=='knowledge-status': continue
        if name in ('knowledge-benchmark','knowledge-model-benchmark'):
            p.add_argument('--output',required=True);continue
        for key in ('project-root','index-dir'): p.add_argument('--'+key,required=True)
        if name=='knowledge-index':
            p.add_argument('--source-map',required=True);p.add_argument('--projection-file',required=True)
        elif name in ('knowledge-project','knowledge-refresh'):
            p.add_argument('--source-map',required=True);p.add_argument('--test-receipt')
        else:
            for key in ('policy-file','task-file'): p.add_argument('--'+key,required=True)
            if name=='knowledge-retrieve':
                p.add_argument('--query-vector');p.add_argument('--query-text');p.add_argument('--evidence-pack',required=True)
                p.add_argument('--query-model');p.add_argument('--embedding-mode',choices=('lexical','lsa','hybrid','learned'),default='lexical')
                p.add_argument('--strategy',choices=('vector','community','global','drift'),default='vector')
                p.add_argument('--execution',choices=('single','distributed-local'),default='single')
                p.add_argument('--rerank',action='store_true')
                p.add_argument('--direction',choices=('outgoing','incoming','both'),default='outgoing')
                p.add_argument('--max-hops',type=int,default=2);p.add_argument('--seeds',type=int,default=1)
                p.add_argument('--max-visits',type=int,default=100);p.add_argument('--max-results',type=int,default=50)
            elif name=='knowledge-test':
                p.add_argument('--test-path',action='append',required=True);p.add_argument('--test-timeout',type=int,default=60);p.add_argument('--output',required=True)
            elif name in ('knowledge-syntax','knowledge-process'):
                p.add_argument('--output',required=True)
                if name=='knowledge-process':p.add_argument('--max-new-tokens',type=int,default=256)
            elif name!='knowledge-impact':
                p.add_argument('--run-map',required=True);p.add_argument('--expected-claims',required=True)
                p.add_argument('--source',required=True)
                if name in ('knowledge-admit','knowledge-check-admission'):
                    p.add_argument('--admission-spec',required=True);p.add_argument('--admission-file',required=True);p.add_argument('--test-receipt')

def dispatch(args):
    indexing.partition_engine(args.claude_mon_root)
    if args.command=='knowledge-status':
        w=worker(args)
        return w({'op':'handshake'}) if w else {'ok':True,'knowledge':'DEGRADED','graph_required_readiness':'BLOCKED','runtime':'UNAVAILABLE','answer_generation':False}
    if args.command=='knowledge-index':
        return indexing.build(args.project_root,c.read(args.source_map),c.read(args.projection_file),args.index_dir,args.claude_mon_root)
    if args.command=='knowledge-benchmark':
        from .benefit_benchmark import run
        result=run(args.claude_mon_root,worker(args));save(args.output,result);return result
    if args.command=='knowledge-model-benchmark':
        models=model_worker(args)
        if models is None or not args.worker_python:raise ValueError('E_MODEL_BENCHMARK_EXPLICIT_RUNTIMES')
        from .worker_client import _process
        return _process(models.python,Path(__file__).with_name('model_benchmark.py'),{},1800,models.executable_digest,
                        ('--manifest',models.manifest,'--claude-mon-root',args.claude_mon_root,'--worker-python',args.worker_python,
                         '--output',args.output,'--model-timeout',models.timeout))
    if args.command in ('knowledge-project','knowledge-refresh'):
        from . import impact
        return impact.build(args.project_root,c.read(args.source_map),args.index_dir,args.claude_mon_root,worker(args),c.read(args.test_receipt) if args.test_receipt else None,language_parser=model_worker(args))
    policy=c.read(args.policy_file);task=c.read(args.task_file)
    doc=indexing.load(args.index_dir,args.project_root,args.claude_mon_root,allowed_sources=policy['allowed_source_ids'])
    retrieval.validate_policy(policy,doc,task)
    if args.command=='knowledge-impact':
        allowed=set(policy['allowed_source_ids'])
        return {'ok':True,'generation':doc['generation'],'stale_sources':doc.get('stale_sources',[]),'invalidated_nodes':[n['id'] for n in doc['projection']['nodes'] if n['id'] in doc.get('invalidated_nodes',[]) and all(r['source_id'] in allowed for r in n['source_units'])],'scope':'declared source and dependency closure; incomplete static graph cannot prove no other dependency'}
    if args.command=='knowledge-test':
        from . import test_evidence
        if set(policy['allowed_source_ids'])!=set(doc['sources']):raise ValueError('E_TEST_SCOPE_ACCESS: explicit local test execution requires entire declared source scope')
        result=test_evidence.run(args.project_root,doc,args.test_path,args.test_timeout);save(args.output,result);return result
    if args.command=='knowledge-syntax':
        model=model_worker(args)
        if model is None:raise ValueError('E_LOCAL_PARSER_RUNTIME_REQUIRED')
        rows=[]
        for ident in sorted(policy['allowed_source_ids']):
            source=doc['sources'][ident]
            if Path(source['path']).suffix not in {'.js','.jsx','.ts','.tsx'}:continue
            raw=c.within(args.project_root,source['path']).read_bytes()
            if c.digest(raw)!=source['source_sha256']:raise ValueError('E_STALE_SOURCE')
            parsed=model.syntax(raw.decode('utf-8'),source['path'])
            for unit in source['manifest']['units']:indexing.reopen(doc,args.project_root,{'source_id':ident,'unit_id':unit['id']})
            rows.append({'source_id':ident,'source_sha256':source['source_sha256'],'syntax':parsed})
        result={'ok':bool(rows) and all(row['syntax']['status']=='OBSERVED' for row in rows),
                'generation':doc['generation'],'syntax':rows,'runtime_call_truth':'UNVERIFIED'}
        save(args.output,result);return result
    if args.command=='knowledge-process':
        from .semantic_proposals import process
        result=process(doc,args.project_root,policy,task,model_worker(args),args.max_new_tokens)
        save(args.output,result);return result
    if args.command=='knowledge-retrieve':
        if bool(args.query_vector)==bool(args.query_text):raise ValueError('E_QUERY_ONE_MODE_REQUIRED')
        if args.query_text:
            from . import retrieval_v2
            if args.strategy!='vector' or args.execution!='single' or args.embedding_mode=='learned' or args.rerank:
                pack=retrieval_v2.retrieve_advanced(doc,args.project_root,policy,task,args.query_text,worker(args),args.max_hops,args.seeds,args.max_visits,args.max_results,direction=args.direction,embedding_mode=args.embedding_mode,strategy=args.strategy,execution=args.execution,rerank=args.rerank)
            else:
                pack=retrieval_v2.retrieve(doc,args.project_root,policy,task,args.query_text,worker(args),args.max_hops,args.seeds,args.max_visits,args.max_results,direction=args.direction,embedding_mode=args.embedding_mode)
        else:
            if args.direction!='outgoing':raise ValueError('E_QUERY_DIRECTION_REQUIRES_PROJECT_2')
            if args.strategy!='vector' or args.execution!='single' or args.rerank or args.embedding_mode!='lexical':
                raise ValueError('E_VECTOR_QUERY_ADVANCED_FLAGS_UNSUPPORTED')
            pack=retrieval.retrieve(doc,args.project_root,policy,task,c.loads(args.query_vector),worker(args),args.max_hops,args.seeds,args.max_visits,args.max_results,query_model=args.query_model)
        if task['require_graph'] and pack['retrieval']['backend']!='SEMANTICA_OBSERVED': raise ValueError('E_GRAPH_REQUIRED')
        target=save(args.evidence_pack,pack)
        return {'ok':True,'overall':'SOURCE_REOPENED','generation':doc['generation'],'pack_digest':pack['pack_digest'],'units':len(pack['units']),'coverage':'UNVERIFIED','semantic_truth':'UNVERIFIED','evidence_pack':str(target),'retrieval_backend':pack['retrieval']['backend'],'limits_reached':pack['retrieval']['limits_reached']}
    checked,pack,expected,result=audit_run(args,doc,policy,task)
    if args.command in ('knowledge-admit','knowledge-check-admission'):
        from . import admission
        fresh=admission.produce(c.read(args.admission_spec),task,policy,pack,result,checked,c.read(args.test_receipt) if args.test_receipt else None,args.project_root,doc,expected)
        if args.command=='knowledge-admit':save(args.admission_file,fresh)
        else:return admission.verify(c.read(args.admission_file),fresh)
        return {'ok':True,'verdict':fresh['verdict'],'admission_digest':fresh['admission_digest'],'semantic_truth':'UNVERIFIED'}
    return result

def save(path,doc):
    target=c.ordinary(path)
    with target.open('xb') as handle:handle.write(c.canonical(doc))
    return target

def audit_run(args,doc,policy,task):
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
    return checked,pack,expected,result

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
    from .worker_client import ModelClient
    model_python=getattr(args,'knowledge_model_python',None);manifest=getattr(args,'knowledge_model_manifest',None)
    if bool(model_python)!=bool(manifest):raise ValueError('E_LOCAL_MODEL_EXPLICIT_SELECTION')
    models=ModelClient(model_python,manifest,timeout=getattr(args,'knowledge_model_timeout',120)) if model_python else None
    replay=WorkerClient(executable,timeout=getattr(args,'knowledge_worker_timeout',30),model_client=models) if executable else None
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
