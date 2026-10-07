"""Observe actual protected ledger/CAS bytes; append bridge-v1 sidecar only."""
import sqlite3
from pathlib import Path
from . import contracts as c
from . import retrieval

def _rows(run):
    db=sqlite3.connect((Path(run)/'ledger.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:
        return [dict(row) for row in db.execute('SELECT a.* FROM attempts a JOIN accepted b ON b.attempt_id=a.id WHERE b.revoked=0 ORDER BY a.id')]
    finally: db.close()

def has_knowledge(run):
    for row in _rows(run):
        request=c.read(Path(run)/'artifacts'/row['request_digest'])
        if 'context_knowledge_evidence_pack' in request.get('materials',{}): return True
    return False

def observe(run,pack):
    retrieval.validate_pack(pack);attempts=[]
    for row in _rows(run):
        request_raw=(Path(run)/'artifacts'/c.sha(row['request_digest'])).read_bytes()
        response_raw=(Path(run)/'artifacts'/c.sha(row['response_digest'])).read_bytes()
        if c.digest(request_raw)!=row['request_digest'] or c.digest(response_raw)!=row['response_digest']: raise ValueError('E_KNOWLEDGE_CAS')
        request=c.loads(request_raw);c.loads(response_raw)
        if request.get('materials',{}).get('context_knowledge_evidence_pack')!=c.canonical(pack).decode('utf-8'): raise ValueError('E_KNOWLEDGE_PROMPT_OMISSION')
        attempts.append({'attempt_id':row['id'],'work_item_id':row['work_item_id'],'request_digest':row['request_digest'],'response_digest':row['response_digest'],'task_digest':request['task_digest'],'source_digest':request['source_proof']['source_digest']})
    if not attempts: raise ValueError('E_KNOWLEDGE_NO_OBSERVED_ATTEMPTS')
    return {'bridge_schema_version':1,'kind':'knowledge-execution-v1','generation':pack['generation'],'evidence_pack_sha256':c.digest(c.canonical(pack)),'pack_digest':pack['pack_digest'],'task_id':pack['task_id'],'attempts':attempts,'evidence_class':'TEST_ONLY','delivery':'RESPONSE_SAVED','semantic_truth':'UNVERIFIED'}

def write(run,pack):
    observed=observe(run,pack)
    with (Path(run)/'knowledge-execution.json').open('xb') as handle: handle.write(c.canonical(observed))
    return observed

def verify(run,pack):
    receipt=c.read(Path(run)/'knowledge-execution.json')
    if receipt!=observe(run,pack): raise ValueError('E_KNOWLEDGE_EXECUTION_BINDING')
    return {'ok':True,'verdict':'BOUND_OFFLINE','generation':pack['generation'],'pack_digest':pack['pack_digest'],'attempts':len(receipt['attempts']),'evidence_class':'TEST_ONLY','coverage':pack['coverage'],'semantic_truth':'UNVERIFIED'}

def observed_stages(run,pack,expected):
    from .verification import claims
    oracle=claims(expected);units={(u['source_id'],u['unit_id']) for u in pack['units']}
    selected={n['id'] for n in pack['assertions']}
    stage_source=[e for e in expected if {(r['source_id'],r['unit_id']) for r in e['source_units']}<=units]
    stage_retrieval=[e for e in stage_source if e['id'] in selected]
    prompted=set();answer=[];partial=False
    for row in _rows(run):
        req=c.read(Path(run)/'artifacts'/row['request_digest']);payload=req.get('materials',{}).get('context_knowledge_evidence_pack')
        if payload:
            actual=c.loads(payload);prompted.update((u['source_id'],u['unit_id']) for u in actual.get('units',[]))
        response=c.read(Path(run)/'artifacts'/row['response_digest'])
        for result in response.get('results',{}).values():
            try: value=c.loads(result['interpretation'])
            except (ValueError,KeyError): partial=True;continue
            if isinstance(value,dict) and set(value)=={'claims'}:
                claims(value['claims']);answer.extend(value['claims'])
            else: partial=True
    dedup={}
    for claim in answer:
        if claim['id'] in dedup and dedup[claim['id']]!=claim: raise ValueError('E_ANSWER_CLAIM_CONFLICT')
        dedup[claim['id']]=claim
    return {'source':stage_source,'retrieval':stage_retrieval,'prompt':[e for e in expected if {(r['source_id'],r['unit_id']) for r in e['source_units']}<=prompted],'answer':{'state':'PARTIAL' if partial else 'OBSERVED','claims':list(dedup.values())}}
