"""Current permission-filtered GraphRAG, source reopening and fresh worker replay."""
from datetime import datetime,timezone
import math
from . import contracts as c
from . import indexing

def validate_receipt(receipt,execution=False):
    common={'ok','backend','results','limits_reached','lineage','shacl','query_binding','exclusions'}
    runtime={'score_scale','bridge_version','semantica_version','revision','network_policy','answer_generation'}
    if not isinstance(receipt,dict) or not common<=set(receipt) or set(receipt)-common-runtime: raise ValueError('E_RETRIEVAL_RECEIPT_SCHEMA')
    backend=receipt['backend']
    if receipt['ok'] is not True or backend not in ('DIRECT_INSPECTION_DEGRADED','SEMANTICA_OBSERVED','TEST_ONLY'): raise ValueError('E_RETRIEVAL_BACKEND')
    c.strings(receipt['limits_reached'],'retrieval limits')
    if not set(receipt['limits_reached'])<={'max_visits','max_results'}: raise ValueError('E_RETRIEVAL_LIMIT_KIND')
    if not isinstance(receipt['results'],list) or not isinstance(receipt['lineage'],dict): raise ValueError('E_RETRIEVAL_RECEIPT_TYPE')
    excluded=c.keys(receipt['exclusions'],{'outside_current_access_or_validity','optional_budget'},'retrieval exclusions')
    c.integer(excluded['outside_current_access_or_validity'],0,10000,'excluded nodes')
    if excluded['optional_budget']!=[]: raise ValueError('E_RETRIEVAL_EXCLUSIONS')
    if backend!='SEMANTICA_OBSERVED':
        c.keys(receipt,common,'unqualified retrieval receipt')
        if receipt['shacl']!='UNVERIFIED' or receipt['lineage']: raise ValueError('E_RETRIEVAL_FALSE_QUALIFICATION')
        if backend=='DIRECT_INSPECTION_DEGRADED' and (receipt['results'] or receipt['limits_reached']): raise ValueError('E_DEGRADED_RETRIEVAL_RESULTS')
        if execution and backend=='TEST_ONLY': raise ValueError('E_RETRIEVAL_UNQUALIFIED')
    else:
        if receipt['shacl'] not in ('CONFORMS','UNAVAILABLE','UNVERIFIED'): raise ValueError('E_RETRIEVAL_SHACL_STATE')
        for ident,lineage in receipt['lineage'].items():
            c.identity(ident,'lineage node')
            c.keys(lineage,{'integrity_verified','source_units','derivation','lineage_entity_ids'},'lineage')
            if lineage['integrity_verified'] is not True or not isinstance(lineage['source_units'],list): raise ValueError('E_RETRIEVAL_LINEAGE')
            c.strings(lineage['lineage_entity_ids'],'lineage entities')
        if execution:
            from . import BRIDGE_VERSION,SEMANTICA_VERSION,SEMANTICA_REVISION
            c.keys(receipt,common|runtime,'observed retrieval receipt')
            if receipt['shacl']=='UNVERIFIED': raise ValueError('E_RETRIEVAL_SHACL_STATE')
            if receipt['bridge_version']!=BRIDGE_VERSION or receipt['semantica_version']!=SEMANTICA_VERSION or receipt['revision']!=SEMANTICA_REVISION or receipt['answer_generation'] is not False: raise ValueError('E_RETRIEVAL_RUNTIME_IDENTITY')
            c.string(receipt['network_policy'],'network policy');c.string(receipt['score_scale'],'score scale')
    return receipt

def validate_policy(policy,doc,task):
    c.keys(policy,{'schema_version','workspace_id','task_id','allowed_source_ids'},'current access policy')
    c.keys(task,{'schema_version','task_id','required_units','require_graph','max_bytes','execution_task_digest'},'task obligations')
    if policy['schema_version']!=1 or task['schema_version']!=1 or policy['workspace_id']!=doc['workspace_id'] or policy['task_id']!=task['task_id']: raise ValueError('E_POLICY_SCOPE')
    c.identity(task['task_id'],'task');c.strings(policy['allowed_source_ids'],'allowed sources')
    if not set(policy['allowed_source_ids'])<=set(doc['sources']): raise ValueError('E_POLICY_SOURCE')
    if type(task['require_graph'])!=bool: raise ValueError('E_TASK_REQUIRED_GRAPH')
    c.integer(task['max_bytes'],1,c.MAX_MESSAGE,'pack bytes')
    if task['execution_task_digest'] is not None: c.sha(task['execution_task_digest'])
    if not isinstance(task['required_units'],list): raise ValueError('E_REQUIRED_SCOPE')
    if task['required_units']: c.refs(task['required_units'],doc['sources'])
    if any(r['source_id'] not in policy['allowed_source_ids'] for r in task['required_units']): raise ValueError('E_REQUIRED_ACCESS_REVOKED')

def _visible(doc,policy):
    allowed=set(policy['allowed_source_ids']);now=datetime.now(timezone.utc)
    def permitted(row): return all(r['source_id'] in allowed for r in row['source_units']) and c.active(row,now)
    nodes=[n for n in doc['projection']['nodes'] if permitted(n)];table={n['id']:n for n in nodes}
    while True:
        invalid={n['id'] for n in nodes if n['derivation'] and not set(n['derivation']['premises'])<=set(table)}
        if not invalid: break
        nodes=[n for n in nodes if n['id'] not in invalid];table={n['id']:n for n in nodes}
    edges=[e for e in doc['projection']['edges'] if permitted(e) and e['subject'] in table and e['object'] in table]
    return nodes,edges,table

def _candidates(out,table,edges,binding):
    if not isinstance(out,dict) or out.get('ok') is not True or not isinstance(out.get('results'),list): raise ValueError('E_RETRIEVAL_FAILED')
    if len(out['results'])>min(binding['max_visits'],binding['max_results']): raise ValueError('E_RETRIEVAL_LIMIT')
    edge_table={e['id']:e for e in edges};refs=[];selected=[];seen=set()
    for result in out['results']:
        c.keys(result,{'id','score','path','edge_ids'},'candidate')
        ident=result['id'];path=result['path'];eid=result['edge_ids']
        if ident not in table or ident in seen or not isinstance(path,list) or not path or path[-1]!=ident or len(set(path))!=len(path) or not set(path)<=set(table) or len(path)-1>binding['max_hops'] or not isinstance(eid,list) or len(eid)!=len(path)-1: raise ValueError('E_RETRIEVAL_FOREIGN_OR_PATH')
        if type(result['score']) not in (int,float) or not math.isfinite(result['score']) or not -1.00001<=result['score']<=1.00001: raise ValueError('E_SCORE')
        for i,e in enumerate(eid):
            if e not in edge_table or edge_table[e]['subject']!=path[i] or edge_table[e]['object']!=path[i+1]: raise ValueError('E_PATH_EDGE')
            refs.extend(edge_table[e]['source_units'])
        seen.add(ident);selected.append(table[ident]);refs.extend(table[ident]['source_units'])
        for n in path: refs.extend(table[n]['source_units'])
    closure={};pending=[n['id'] for n in selected]
    while pending:
        ident=pending.pop()
        if ident in closure: continue
        closure[ident]=table[ident]
        if table[ident]['derivation']: pending.extend(table[ident]['derivation']['premises'])
    premises=[closure[i] for i in sorted(set(closure)-seen)]
    for n in closure.values(): refs.extend(n['source_units'])
    return selected,premises,refs

def _binding(doc,nodes,edges,query,model,seeds,hops,visits,results):
    dimension=doc['projection']['embedding']['dimension']
    if model!=doc['projection']['embedding']['model']: raise ValueError('E_QUERY_EMBEDDING_MODEL')
    c.vector(query,dimension) # Validate here; worker normalizes once for scoring.
    return {'query_vector':list(query),'model':model,'dimension':dimension,'seeds':c.integer(seeds,1,100,'seeds'),'max_hops':c.integer(hops,0,8,'hops'),'max_visits':c.integer(visits,1,10000,'visits'),'max_results':c.integer(results,1,1000,'results'),'authorized_projection_digest':c.digest(c.canonical({'nodes':nodes,'edges':edges}))}

def validate_pack(pack):
    c.keys(pack,{'schema_version','kind','workspace_id','task_id','generation','source_basis_digest','policy_digest','task_obligations_digest','embedding','required_units','units','assertions','premises','retrieval','coverage','semantic_audit','pack_digest'},'evidence pack')
    if pack['schema_version']!=1 or pack['kind']!='knowledge-evidence-v1': raise ValueError('E_PACK_VERSION')
    for k in ('generation','source_basis_digest','policy_digest','task_obligations_digest'): c.sha(pack[k])
    if pack['pack_digest']!=c.digest(c.canonical({k:v for k,v in pack.items() if k!='pack_digest'})): raise ValueError('E_PACK_DIGEST')
    if not isinstance(pack['units'],list) or not isinstance(pack['assertions'],list) or not isinstance(pack['premises'],list): raise ValueError('E_PACK_LIST')
    units=set()
    for u in pack['units']:
        c.keys(u,{'source_id','unit_id','path','source_sha256','unit_sha256','range','text','authority'},'pack unit')
        pair=(u['source_id'],u['unit_id'])
        if pair in units: raise ValueError('E_PACK_DUPLICATE_UNIT')
        units.add(pair)
        if c.digest(u['text'].encode('utf-8'))!=u['unit_sha256']: raise ValueError('E_PACK_UNIT_HASH')
    if not {(r['source_id'],r['unit_id']) for r in pack['required_units']}<=units: raise ValueError('E_PACK_REQUIRED_OMITTED')
    if pack['coverage']!='UNVERIFIED' or pack['semantic_audit']!='UNVERIFIED': raise ValueError('E_PACK_FALSE_QUALIFICATION')
    validate_receipt(pack['retrieval'])
    return pack

def verify_pack(pack,doc,root,policy,task,worker=None):
    validate_pack(pack);validate_policy(policy,doc,task)
    if pack['embedding']!=doc['projection']['embedding']: raise ValueError('E_PACK_EMBEDDING_PROVENANCE')
    if pack['generation']!=doc['generation'] or pack['task_id']!=task['task_id'] or pack['workspace_id']!=policy['workspace_id'] or pack['source_basis_digest']!=doc['source_basis_digest'] or pack['policy_digest']!=c.digest(c.canonical(policy)) or pack['task_obligations_digest']!=c.digest(c.canonical(task)): raise ValueError('E_PACK_CURRENT_BASIS')
    if pack['required_units']!=task['required_units']: raise ValueError('E_REQUIRED_SCOPE')
    nodes,edges,table=_visible(doc,policy)
    binding=pack['retrieval'].get('query_binding')
    c.keys(binding,{'query_vector','model','dimension','seeds','max_hops','max_visits','max_results','authorized_projection_digest'},'query binding')
    actual=_binding(doc,nodes,edges,binding['query_vector'],binding['model'],binding['seeds'],binding['max_hops'],binding['max_visits'],binding['max_results'])
    if binding!=actual: raise ValueError('E_QUERY_CURRENT_SCOPE')
    selected,premises,refs=_candidates(pack['retrieval'],table,edges,binding)
    if selected!=pack['assertions'] or premises!=pack['premises']: raise ValueError('E_PACK_ASSERTION_OR_DERIVATION')
    validate_receipt(pack['retrieval'],execution=True)
    required_refs={(r['source_id'],r['unit_id']) for r in refs+task['required_units']}
    if required_refs!={(u['source_id'],u['unit_id']) for u in pack['units']}: raise ValueError('E_PACK_SOURCE_CLOSURE')
    for u in pack['units']:
        if u['source_id'] not in policy['allowed_source_ids']: raise ValueError('E_PACK_ACCESS')
        if indexing.reopen(doc,root,{'source_id':u['source_id'],'unit_id':u['unit_id']})!=u: raise ValueError('E_PACK_SOURCE')
    if len(c.canonical(pack))>task['max_bytes']: raise ValueError('E_PACK_BUDGET')
    if task['require_graph'] or pack['retrieval'].get('backend')=='SEMANTICA_OBSERVED':
        from .worker_client import WorkerClient
        if not isinstance(worker,WorkerClient): raise ValueError('E_GRAPH_REQUIRED_FRESH_WORKER')
        fresh=retrieve(doc,root,policy,task,binding['query_vector'],worker,binding['max_hops'],binding['seeds'],binding['max_visits'],binding['max_results'],query_model=binding['model'])
        if fresh!=pack: raise ValueError('E_GRAPH_REPLAY_MISMATCH')
    return pack

def retrieve(doc,root,policy,task,query_vector,worker,max_hops=2,seeds=1,max_visits=100,max_results=50,query_model=None):
    validate_policy(policy,doc,task)
    if query_model is None:
        if doc['projection']['embedding']['evidence_class']!='TEST_ONLY': raise ValueError('E_QUERY_EMBEDDING_MODEL_REQUIRED')
        query_model=doc['projection']['embedding']['model']
    nodes,edges,table=_visible(doc,policy)
    binding=_binding(doc,nodes,edges,query_vector,query_model,seeds,max_hops,max_visits,max_results)
    if worker is None:
        if task['require_graph']: raise ValueError('E_GRAPH_RUNTIME_UNAVAILABLE')
        out={'ok':True,'backend':'DIRECT_INSPECTION_DEGRADED','results':[],'limits_reached':[],'lineage':{},'shacl':'UNVERIFIED'}
    else:
        out=worker({'op':'retrieve','nodes':nodes,'edges':edges,'query_vector':binding['query_vector'],'dimension':binding['dimension'],'seeds':seeds,'max_hops':max_hops,'max_visits':max_visits,'max_results':max_results})
    selected,premises,refs=_candidates(out,table,edges,binding)
    units=[];unique=set()
    for ref in task['required_units']+refs:
        pair=(ref['source_id'],ref['unit_id'])
        if pair not in unique:
            unique.add(pair);units.append(indexing.reopen(doc,root,ref))
    out=dict(out);out.setdefault('shacl','UNVERIFIED');out['query_binding']=binding
    out['exclusions']={'outside_current_access_or_validity':len(doc['projection']['nodes'])-len(nodes),'optional_budget':[]}
    pack={'schema_version':1,'kind':'knowledge-evidence-v1','workspace_id':doc['workspace_id'],'task_id':task['task_id'],'generation':doc['generation'],'source_basis_digest':doc['source_basis_digest'],'policy_digest':c.digest(c.canonical(policy)),'task_obligations_digest':c.digest(c.canonical(task)),'embedding':doc['projection']['embedding'],'required_units':task['required_units'],'units':units,'assertions':selected,'premises':premises,'retrieval':out,'coverage':'UNVERIFIED','semantic_audit':'UNVERIFIED'}
    pack['pack_digest']=c.digest(c.canonical(pack))
    if len(c.canonical(pack))>task['max_bytes']: raise ValueError('E_PACK_BUDGET: reduce optional candidates or increase authorized budget; no mandatory truncation')
    validate_pack(pack);return pack
