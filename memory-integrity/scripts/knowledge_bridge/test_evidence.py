"""Reopenable local test observations, never caller-supplied success verdicts."""
import os,subprocess,sys,tempfile
from pathlib import Path
from . import contracts as c

def snapshot(root,doc):
    root=c.ordinary(root,True);declared={}
    for ident,source in doc['sources'].items():
        actual=c.within(root,source['path']).read_bytes()
        if c.digest(actual)!=source['source_sha256']:raise ValueError('E_STALE_TEST_SOURCE')
        declared[ident]=source['source_sha256']
    inventory={};total=0
    for path in sorted(root.rglob('*.py')):
        if any(part in {'.git','__pycache__','.venv','venv'} for part in path.relative_to(root).parts):continue
        raw=c.ordinary(path).read_bytes();total+=len(raw)
        if total>32*c.MAX_MESSAGE or len(inventory)>=10000:raise ValueError('E_TEST_SNAPSHOT_LIMIT')
        inventory[path.relative_to(root).as_posix()]=c.digest(raw)
    return {'declared_sources':declared,'python_inventory':inventory,'scope':'all project Python and declared source bytes; undeclared non-Python data not qualified'}

def _link(case,doc,root):
    refs=[]
    for ident,source in doc['sources'].items():
        if source['path']!=case['path'] or case['lines'][0] is None:continue
        raw=c.within(root,source['path']).read_bytes();lines=raw.splitlines(keepends=True);a=sum(map(len,lines[:case['lines'][0]-1]));b=sum(map(len,lines[:case['lines'][1]]))
        refs=[{'source_id':ident,'unit_id':u['id']} for u in source['manifest']['units'] if u['range'][0]<b and u['range'][1]>a]
    return {**case,'source_units':refs}

def run(root,doc,test_paths,timeout=60):
    root=c.ordinary(root,True);c.integer(timeout,1,120,'test timeout');c.strings(test_paths,'test paths')
    if not test_paths:raise ValueError('E_TEST_SCOPE_EMPTY')
    known={s['path'] for s in doc['sources'].values()}
    for relative in test_paths:
        if relative not in known or not c.within(root,relative).is_file() or not relative.endswith('.py'):raise ValueError('E_TEST_SCOPE_UNDECLARED')
    before=snapshot(root,doc)
    with tempfile.TemporaryDirectory(prefix='knowledge-test-') as folder:
        folder=Path(folder);output=folder/'result.json';config=folder/'input.json'
        config.write_bytes(c.canonical({'root':str(root),'test_paths':test_paths,'output':str(output)}))
        env={k:v for k,v in os.environ.items() if k in {'PATH','SystemRoot','WINDIR','TEMP','TMP','TMPDIR','LANG','LC_ALL'}}
        env.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        try:
            process=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('test_runner.py')),str(config)],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=timeout)
            if process.returncode or not output.is_file():result={'ok':False,'cases':[],'tests_run':0,'execution':'ERROR'}
            else:result={**c.read(output),'execution':'OBSERVED'}
        except subprocess.TimeoutExpired:result={'ok':False,'cases':[],'tests_run':0,'execution':'TIMEOUT'}
    after=snapshot(root,doc)
    if before!=after:raise ValueError('E_STALE_TEST_EXECUTION')
    cases=[_link(row,doc,root) for row in result['cases']]
    result.update(schema_version=1,kind='knowledge-test-v1',test_paths=test_paths,timeout=timeout,snapshot=before,cases=cases,evidence_class='HOST_OBSERVED_LOCAL',network_policy='Python sockets blocked; local test subprocess is not an OS sandbox')
    if any(not row['source_units'] for row in cases):result['ok']=False
    result['receipt_digest']=c.digest(c.canonical(result));return result

def verify(receipt,root,doc):
    c.keys(receipt,{'schema_version','kind','test_paths','timeout','snapshot','cases','tests_run','execution','ok','evidence_class','network_policy','receipt_digest'},'test receipt')
    if receipt['schema_version']!=1 or receipt['kind']!='knowledge-test-v1' or receipt['evidence_class']!='HOST_OBSERVED_LOCAL':raise ValueError('E_TEST_RECEIPT_VERSION')
    if receipt['receipt_digest']!=c.digest(c.canonical({k:v for k,v in receipt.items() if k!='receipt_digest'})):raise ValueError('E_TEST_RECEIPT_DIGEST')
    if receipt['snapshot']!=snapshot(root,doc):raise ValueError('E_STALE_TEST_SNAPSHOT')
    fresh=run(root,doc,receipt['test_paths'],receipt['timeout'])
    if fresh!=receipt:raise ValueError('E_TEST_REPLAY_MISMATCH')
    return fresh

def add_projection(projection,receipt,sources):
    from .extraction import vectorize
    nodes=projection['nodes'];edges=projection['edges'];byid={n['id']:n for n in nodes}
    def node(ident,kind,text,refs):
        if ident not in byid:
            row={'id':ident,'type':kind,'text':text,'source_units':refs,'polarity':'positive','conditions':[],'derivation':None,'valid_from':None,'valid_until':None,'review_status':'unreviewed','vector':vectorize(text)};nodes.append(row);byid[ident]=row
    for case in receipt['cases']:
        if not case['source_units']:continue
        tid='test:'+c.digest(case['id'].encode())[:32];rid='test-run:'+c.digest(c.canonical([receipt['receipt_digest'],case['id']]))[:32]
        node(tid,'TestCase',case['id'],case['source_units']);node(rid,'TestRun',case['id']+' status '+case['status']+' snapshot '+c.digest(c.canonical(receipt['snapshot'])),case['source_units'])
        edges.append({'id':'test-result:'+c.digest(c.canonical([tid,rid]))[:32],'subject':tid,'predicate':'SUPPORTED_BY','object':rid,'source_units':case['source_units'],'conditions':['observed local unittest; '+case['status']],'valid_from':None,'valid_until':None})
        test_symbols={n['id'] for n in nodes if n['type']=='Symbol' and n['text'].split(': ',1)[0].endswith(case['id'])}
        targets={e['object'] for e in edges if e['subject'] in test_symbols and e['predicate']=='REFERENCES'}
        for target in sorted(targets):
            edges.append({'id':'test-static-call:'+c.digest(c.canonical([tid,target]))[:32],'subject':tid,'predicate':'TESTS','object':target,'source_units':case['source_units'],'conditions':['static direct reference; does not prove execution coverage'],'valid_from':None,'valid_until':None})
        for n in list(nodes):
            if n['type'] in {'Component','Symbol'} and set(r['source_id'] for r in n['source_units'])&set(receipt['snapshot']['declared_sources']):
                # Snapshot links are DERIVED_FROM, never inferred TESTS relevance.
                edges.append({'id':'test-snapshot:'+c.digest(c.canonical([rid,n['id']]))[:32],'subject':rid,'predicate':'DERIVED_FROM','object':n['id'],'source_units':case['source_units']+ [r for r in n['source_units'] if r not in case['source_units']],'conditions':['executed snapshot; does not prove test exercises this symbol'],'valid_from':None,'valid_until':None})
