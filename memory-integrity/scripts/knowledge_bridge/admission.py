"""Fresh task-relative admission, callable by an ordinary external Fable test."""
from . import contracts as c,test_evidence
SUPPORTED={'source_identity','protected_request','structured_oracle','local_tests','python_syntax_extraction','resolved_static_dependencies','reviewed_propositions'}

def check_extraction(checks,doc,root,refs,allowed_sources=None):
    if not set(checks)&{'python_syntax_extraction','resolved_static_dependencies'}:return
    if doc.get('schema_version')!=2:raise ValueError('E_ADMISSION_EXTRACTION_UNAVAILABLE')
    ids={r['source_id'] for r in refs};manifest=doc['construction']['extraction']
    if not ids or any(manifest['sources'][i]['status']!='OBSERVED' for i in ids):raise ValueError('E_ADMISSION_EXTRACTION_REQUIRED')
    from .extraction import extract
    # Qualification observes the required syntax again; discovery cache is not a witness.
    scoped=set(allowed_sources) if allowed_sources is not None else ids
    if not ids<=scoped:raise ValueError('E_ADMISSION_EXTRACTION_ACCESS')
    fresh=extract({i:doc['sources'][i] for i in sorted(scoped)},doc['repository'],root=root)['manifest']
    if any(fresh['sources'][i]['fragment']!=manifest['sources'][i]['fragment'] for i in ids):raise ValueError('E_ADMISSION_EXTRACTION_REPLAY')
    if 'resolved_static_dependencies' in checks and any(row['source_id'] in ids and row['kind'] in {'UNRESOLVED_CALL','UNRESOLVED_IMPORT','AMBIGUOUS_MODULE','DYNAMIC_BINDING','PARSE_FAILED'} for row in fresh['diagnostics']):raise ValueError('E_ADMISSION_EXTRACTION_UNRESOLVED')
def validate_spec(spec):
    c.keys(spec,{'schema_version','task_id','purpose','criteria','required_checks','oracle_review'},'admission specification')
    if spec['schema_version']!=1:raise ValueError('E_ADMISSION_VERSION')
    c.identity(spec['task_id'],'admission task');c.string(spec['purpose'],'purpose');c.strings(spec['required_checks'],'required checks')
    if not set(spec['required_checks'])<=SUPPORTED:raise ValueError('E_ADMISSION_ASSURANCE_UNAVAILABLE')
    if not {'source_identity','protected_request','structured_oracle'}<=set(spec['required_checks']):raise ValueError('E_ADMISSION_CHECKS_REQUIRED')
    if not isinstance(spec['criteria'],dict) or not spec['criteria']:raise ValueError('E_ADMISSION_CRITERIA')
    for ident,cases in spec['criteria'].items():c.identity(ident,'criterion');c.strings(cases,'required test cases')
    review=c.keys(spec['oracle_review'],{'reviewer','oracle_digest'},'independent oracle review');c.string(review['reviewer'],'oracle reviewer');c.sha(review['oracle_digest'])
    return spec

def produce(spec,task,policy,pack,audit,protected,test_receipt,root,doc,oracle):
    validate_spec(spec)
    if spec['task_id']!=task['task_id'] or task['execution_task_digest'] is None:raise ValueError('E_ADMISSION_TASK_BINDING')
    if c.digest(c.canonical(oracle))!=spec['oracle_review']['oracle_digest']:raise ValueError('E_ADMISSION_ORACLE_BINDING')
    if not protected.get('ok') or audit.get('verdict')!='PASSED_FOR_DECLARED_STRUCTURED_CHECKS':raise ValueError('E_ADMISSION_CHECK_FAILED')
    if audit.get('limitations'):raise ValueError('E_ADMISSION_UNOBSERVED_STAGE')
    refs=task['required_units']+[r for claim in oracle for r in claim['source_units']]
    check_extraction(spec['required_checks'],doc,root,refs,policy['allowed_source_ids'])
    if 'reviewed_propositions' in spec['required_checks']:
        table={n['id']:n for n in pack['assertions']+pack['premises']}
        if any(claim['id'] not in table or table[claim['id']]['review_status']!='reviewed' for claim in oracle):raise ValueError('E_ADMISSION_PROPOSITION_REVIEW_REQUIRED')
    if 'local_tests' in spec['required_checks']:
        if test_receipt is None:raise ValueError('E_ADMISSION_TEST_REQUIRED')
        fresh=test_evidence.verify(test_receipt,root,doc)
        if not fresh['ok']:raise ValueError('E_ADMISSION_TEST_FAILED')
        passed={row['id'] for row in fresh['cases'] if row['status']=='pass'}
        if any(not cases or not set(cases)<=passed for cases in spec['criteria'].values()):raise ValueError('E_ADMISSION_CRITERION_TEST_MISSING')
    elif any(spec['criteria'].values()):raise ValueError('E_ADMISSION_TEST_CHECK_UNDECLARED')
    body={'schema_version':1,'kind':'knowledge-admission-v1','task_id':task['task_id'],'purpose':spec['purpose'],'criteria':spec['criteria'],'required_checks':spec['required_checks'],'spec_digest':c.digest(c.canonical(spec)),'task_digest':c.digest(c.canonical(task)),'policy_digest':c.digest(c.canonical(policy)),'pack_digest':pack['pack_digest'],'generation':doc['generation'],'oracle_digest':spec['oracle_review']['oracle_digest'],'oracle_review':spec['oracle_review'],'audit_digest':c.digest(c.canonical(audit)),'protected_digest':c.digest(c.canonical(protected)),'test_receipt_digest':test_receipt['receipt_digest'] if test_receipt else None,'verdict':'ADMITTED_FOR_DECLARED_OFFLINE_CHECKS','semantic_truth':'UNVERIFIED','oracle_evidence_class':'MANUAL_REPORTED_REVIEW','coverage':'DECLARED_TASK_ONLY'}
    body['admission_digest']=c.digest(c.canonical(body));return body

def verify(stored,fresh):
    if stored!=fresh:raise ValueError('E_ADMISSION_CURRENT_BINDING')
    return {'ok':True,'verdict':fresh['verdict'],'admission_digest':fresh['admission_digest'],'semantic_truth':'UNVERIFIED'}
