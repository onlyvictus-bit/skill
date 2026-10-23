"""One ordered-context diagnostic, not a Gate1 retry, repair or qualification."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

HERE=Path(__file__).resolve()
LEGACY=HERE.with_name('gate1_cleanup_diagnostic.py')
if hashlib.sha256(LEGACY.read_bytes()).hexdigest()!='5cab51682fe489aae89427d7d78fb5cf9aa060eafa8e3a0783b9f33736fe6e6f':
    raise ValueError('E_ORDERED_LEGACY_HELPER_CHANGED')
spec=importlib.util.spec_from_file_location('sealed_ordered_cleanup',LEGACY)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
g,i=m.g,m.i
RUNNER=HERE.with_name('gate1_ordered_runner.py')
ARTIFACTS=g.REPO/'.github/run-artifacts/offline-first-20261020'
CONTRACT=ARTIFACTS/'Gate1-Ordered-Contract-20261021-v3.json'
PARENT_CONTRACT=ARTIFACTS/'Gate1-Cleanup-Diagnostic-Contract-20261021.json'
PARENT_SHA='4a773e562a0b0bf0af7cea57899696febd089471750d6a7707471a2287df2924'
ACTUAL_SHA='fb8d02cc60782b7e3154c151e317caccc9e34ee198c4f69e50854e7fa2132433'
MAP_SHA='bbc5a216250b0c197a9928d4eae7bf6a89d0cdde04f94c20d0893be8e2dcc044'
FAILED_OUT=g.WORKSPACE/'order-successor-20261021'
FAILED_SOURCE=g.WORKSPACE/'ordsrc'
FAILED_SHA='8aa9a35101bddcd0a5585b21e7cf45530201229ba61b8f6ffdd99ac484394077'
V2_CONTRACT=ARTIFACTS/'Gate1-Ordered-Contract-20261021-v2.json'
V2_CONTRACT_SHA='29b55a9276e0a31fd3c9c28ef28fede2e483321b29f9a69089b844f1302cf12d'
OUT=g.WORKSPACE/'order-pinfix-v3-20261021'
SOURCE=g.WORKSPACE/'ordfix'
SCOPE='GATE1_UNCHANGED_ORDERED_METHOD_DIAGNOSTIC'
TARGET='test_knowledge_completion.RemainingPublicContract.test_public_advanced_modes_source_closure_and_replay'
MODES=[['community','single'],['global','single'],['drift','single'],['vector','distributed-local']]
FLAGS=('producer_authentication','gate1_complete','fix_validated','release_ready','installed',
       'native_execution','whole_skill_ready','retry_authorized')


def validate_new_paths(source,output,workspace,old_source,old_output):
    source,output,workspace,old_source,old_output=map(Path,(source,output,workspace,old_source,old_output))
    g.require(source.is_absolute() and output.is_absolute() and
              source.parent==output.parent==workspace and source.name=='ordfix' and
              output.name=='order-pinfix-v3-20261021' and
              len(str(source))==len(str(old_source)) and len(source.parts)==len(old_source.parts) and
              len(str(output))==len(str(old_output)) and len(output.parts)==len(old_output.parts),
              'E_ORDERED_LAYOUT')
    g.ordinary(workspace)
    for path in (source,output):
        try: path.lstat()
        except FileNotFoundError: continue
        raise ValueError('E_ORDERED_EXISTING_ATTEMPT: '+str(path))


def guarded_output(check,output,source,workspace,old_source,old_output):
    check()  # Including the complete old history. Absolutely no output before this.
    validate_new_paths(source,output,workspace,old_source,old_output)
    return g.new_workspace(output,[old_source,old_output])


def load_runner():
    spec=importlib.util.spec_from_file_location('sealed_ordered_runner',RUNNER)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def build_contract():
    parent=g.load_sealed(PARENT_CONTRACT,PARENT_SHA)
    doc=m.validate_contract(parent)
    g.verify_manifest(Path(doc['source']),doc['source_manifest'])
    prior_map=m.OUTPUT/'Before-Image-Attempt.json'
    actual=m.OUTPUT/'Receipt.json'
    g.require(g.file_record(actual)['sha256']==ACTUAL_SHA and
              g.file_record(prior_map)['sha256']==MAP_SHA, 'E_ORDERED_PRIOR_RESULT')
    runner=load_runner()
    g.require(runner.RETAINED_SHA==doc['source_manifest']['.github/scripts/retained_unittest.py'] and
              g.file_record(HERE.with_name('retained_unittest.py'))['sha256']==runner.RETAINED_SHA,
              'E_ORDERED_BOOTSTRAP_MANIFEST_BINDING')
    failed=g.load_sealed(FAILED_OUT/'Receipt.json',FAILED_SHA)
    g.require(failed['status']=='HARNESS_OR_CAPTURE_FAILED' and failed['preservation'] is True and
              all(failed[key] is False for key in FLAGS) and
              [row['label'] for row in failed['commands']]==['preclaim-git','preclaim-runtime','ordered-method'] and
              [row['exit_code'] for row in failed['commands']]==[0,0,1] and
              failed['contract']==g.file_record(V2_CONTRACT) and failed['contract']['sha256']==V2_CONTRACT_SHA,
              'E_ORDERED_CONSUMED_V2_RESULT')
    for command in failed['commands']:
        for stream in ('stdout','stderr'):
            g.require(g.file_record(Path(command[stream]['path']))==command[stream], 'E_ORDERED_V2_STREAM')
    g.require('E_ORDERED_RETAINED_RUNNER_CHANGED' in
              (FAILED_OUT/'ordered-method/stderr.log').read_text(encoding='utf-8'), 'E_ORDERED_V2_CAUSE')
    g.verify_manifest(FAILED_SOURCE,parent['diagnostic_source_manifest'])
    archive=ARTIFACTS/'ordered-consumed-v2'
    archived={}
    for name,digest in {
        'gate1_ordered_runner.py':'60df7a731965212c7c9fcbdff29166a9ba14e45876c8cd9d4c8f3254c7b22b55',
        'gate1_ordered_diagnostic.py':'1ea1128b69ad0707753373e2747ece5fbe0243e301e52d207b32b3abd9fa49da',
        'test_gate1_ordered_diagnostic.py':'fa736e76168174819b5411f4ea468f4847a44ba73ba9ddf328e60906d38e743a'}.items():
        archived[name]=g.file_record(archive/name)
        g.require(archived[name]['sha256']==digest,'E_ORDERED_V2_ARCHIVE')
    value={'schema_version':1,'scope':SCOPE,'head':g.HEAD,'output':str(OUT),'copy':str(SOURCE),
           'parent':g.file_record(PARENT_CONTRACT),'actual':g.file_record(actual),
           'image_start_map':g.file_record(prior_map),'actual_inventory':g.inventory(m.OUTPUT),
           'helper':g.file_record(HERE),'runner':g.file_record(RUNNER),
           'original_test':g.file_record(Path(doc['source'])/'memory-integrity/tests_v2/test_knowledge_completion.py'),
           'target':TARGET,'modes':MODES,'test_sha256':runner.TEST_SHA,
           'public_timeout':90,'runtime_timeout':60,'method_timeout':600,
           'source_manifest':parent['diagnostic_source_manifest'],
           'failed_ordered_receipt':g.file_record(FAILED_OUT/'Receipt.json'),
           'failed_ordered_contract':g.file_record(V2_CONTRACT),
           'failed_ordered_inventory':g.inventory(FAILED_OUT),'consumed_v2_code':archived,
           'retained_runner_sha256':runner.RETAINED_SHA,
           'history_coverage':'STATIC_KNOWN_RECORDS_PLUS_MANDATORY_FULL_RUNTIME_PREFLIGHT',
           **{key:False for key in FLAGS}}
    g.require(len(value['actual_inventory'])==594 and
              g.map_digest(value['actual_inventory'])=='94d6810ab9ae0ce34511d06ff0b3565ff252c8538170b5c35d78a8cf8ac3505a',
              'E_ORDERED_PRIOR_INVENTORY')
    g.require(len(value['failed_ordered_inventory'])==15 and
              g.map_digest(value['failed_ordered_inventory'])=='207e65741bf16b272c416ba1299e61fbeda406923487d2db34fefc3c60c5152e',
              'E_ORDERED_CONSUMED_V2_INVENTORY')
    return value


def validate_contract(value):
    # Deterministic roles bind readable old evidence; this is NOT a skipped full preflight.
    expected=build_contract()
    g.require(value==expected,'E_ORDERED_CONTRACT')
    g.require(value['original_test']['sha256']==value['test_sha256'], 'E_ORDERED_ORIGINAL_TEST_CHANGED')
    return m.validate_contract(g.load_sealed(PARENT_CONTRACT,PARENT_SHA))


def preservation(value,doc,record=None,clone=False,start_records=()):
    image=g.load_sealed(m.IMAGE_CONTRACT,m.IMAGE_CONTRACT_SHA)
    i.check_preserved(image,doc,g.file_record(m.IMAGE_CONTRACT))
    parent=g.load_sealed(PARENT_CONTRACT,PARENT_SHA)
    m.check_bound_records(parent)
    expected=g.load_sealed(Path(value['image_start_map']['path']),MAP_SHA)
    g.require(len(expected)==1370 and g.map_digest(expected)==
              'b94c45316daf100fe2c11d3d8c54ec2a2b24048bcc412df36baa085df09cda29',
              'E_ORDERED_IMAGE_START_MAP')
    g.verify_manifest(i.OUTPUT,expected)
    g.verify_manifest(m.OUTPUT,value['actual_inventory'])
    g.verify_manifest(FAILED_OUT,value['failed_ordered_inventory'])
    g.verify_manifest(FAILED_SOURCE,value['source_manifest'])
    for row in (value['parent'],value['actual'],value['image_start_map'],value['helper'],
                value['runner'],value['original_test'],value['failed_ordered_receipt'],
                value['failed_ordered_contract'],*value['consumed_v2_code'].values(),*start_records):
        g.require(g.file_record(Path(row['path']))==row,'E_ORDERED_INPUT_CHANGED')
    if record is not None:
        g.require(g.file_record(Path(record['path']))==record,'E_ORDERED_CONTRACT_CHANGED')
    if clone: g.verify_manifest(SOURCE,value['source_manifest'])


def preflight(contract,digest):
    g.require(Path(contract)==CONTRACT,'E_ORDERED_CONTRACT_PATH')
    value=g.load_sealed(CONTRACT,digest);record=g.file_record(CONTRACT)
    doc=validate_contract(value)
    preservation(value,doc,record)
    validate_new_paths(SOURCE,OUT,g.WORKSPACE,Path(doc['source']),i.OUTPUT)
    observed=bootstrap_probe(Path(doc['source']),value['retained_runner_sha256'])
    preservation(value,doc,record)
    validate_new_paths(SOURCE,OUT,g.WORKSPACE,Path(doc['source']),i.OUTPUT)
    return value,doc,record,observed


def bootstrap_probe(source,expected_digest):
    argv=list(map(str,[g.CONTROLLER,'-B',RUNNER,'--package-root',source/'memory-integrity',
        '--pattern','test_knowledge_completion.py','--output-dir',OUT/'tests-3','--bootstrap-only']))
    env=i.windows_environment(dict(os.environ))
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
    result=subprocess.run(argv,cwd=source/'memory-integrity',env=env,
                          capture_output=True,timeout=30)
    g.require(result.returncode==0,'E_ORDERED_BOOTSTRAP_FAILED: '+result.stderr.decode('utf-8',errors='replace'))
    observed=json.loads(result.stdout.decode('utf-8'))
    g.require(observed=={'status':'ORDERED_BOOTSTRAP_VERIFIED_NO_WORKER',
              'retained_sha256':expected_digest,'retained_path':str(HERE.with_name('retained_unittest.py')),
              'worker_started':False,'test_output_created':False} and result.stderr==b'',
              'E_ORDERED_BOOTSTRAP_RESPONSE')
    return {'argv':argv,'exit_code':0,'stdout':observed,'stderr':'',
            'controller_only_not_selected_runtime':True}


def validate_unit_receipt(unit,code,report):
    failed=report['outcomes']['finished'][0]['outcome']!='PASS'
    # One selected parent can produce several FAIL/ERROR child records. The
    # original observer marks either kind as FAIL, so preserve and cross-check
    # the real unittest categories against its hash-bound log, never guess them.
    ids=[TARGET+' (strategy='+repr(s)+', execution='+repr(e)+')' for s,e in MODES]
    subtests=report.get('subtests',[])
    g.require(len(subtests)==4 and [test.get('params') for test in subtests]==[
        {'strategy':s,'execution':e} for s,e in MODES] and
        all(test.get('outcome') in ('PASS','FAIL') for test in subtests),'E_ORDERED_UNIT_ACCOUNTING')
    expected=[ident for ident,test in zip(ids,subtests) if test['outcome']=='FAIL']
    failures,errors=unit.get('failures'),unit.get('errors')
    g.require(isinstance(failures,list) and isinstance(errors,list) and
              all(isinstance(ident,str) for ident in failures+errors),'E_ORDERED_UNIT_ACCOUNTING')
    g.require(type(unit.get('tests_run')) is int and unit['tests_run']==1 and
              type(unit.get('discovered')) is int and unit['discovered']==1 and
              unit.get('skipped')==[] and unit.get('excluded')==[] and
              unit.get('expected_failures')==[] and unit.get('interrupted') is False and
              len(set(failures+errors))==len(failures+errors) and
              set(failures+errors)==set(expected) and failed==bool(expected) and
              failures==[ident for ident in expected if ident in failures] and
              errors==[ident for ident in expected if ident in errors] and
              type(code) is int and code==(1 if failed else 0),
              'E_ORDERED_UNIT_ACCOUNTING')
    if failed:
        g.require(isinstance(unit.get('log'),str) and isinstance(unit.get('log_sha256'),str),
                  'E_ORDERED_UNIT_ACCOUNTING')
        log=Path(unit['log']);record=g.file_record(log)
        g.require(record['sha256']==unit['log_sha256'],'E_ORDERED_TEST_LOG')
        raw=log.read_bytes()
        g.require(g.sha(raw)==unit['log_sha256'],'E_ORDERED_TEST_LOG')
        descriptions={TARGET.rsplit('.',1)[1]+' ('+TARGET+')'+ident[len(TARGET):]:ident for ident in ids}
        headers={'FAIL':[],'ERROR':[]}
        for line in raw.decode('utf-8').splitlines():
            for kind in headers:
                if line.startswith(kind+': '):
                    description=line[len(kind)+2:]
                    g.require(description in descriptions,'E_ORDERED_UNIT_ACCOUNTING')
                    headers[kind].append(descriptions[description])
        g.require(headers['FAIL']==failures and headers['ERROR']==errors,'E_ORDERED_UNIT_ACCOUNTING')


def read_runner_records(tests,command):
    required=(tests/'Ordered-Outcomes.json',tests/'Receipt.json',tests/'unittest.log')
    missing=[path.name for path in required if not path.exists()]
    if missing:
        stream=command['stderr']
        g.require(g.file_record(Path(stream['path']))==stream,'E_ORDERED_STDERR_CHANGED')
        detail=Path(stream['path']).read_bytes()[:16384].decode('utf-8',errors='replace')
        raise ValueError('E_ORDERED_RUNNER_STARTUP_FAILED: exit='+str(command['exit_code'])+
                         '; missing='+','.join(missing)+'; retained stderr: '+detail)
    report=json.loads(required[0].read_text(encoding='utf-8'))
    unit=json.loads(required[1].read_text(encoding='utf-8'))
    g.require(g.file_record(required[2])['sha256']==unit['log_sha256'],'E_ORDERED_TEST_LOG')
    return report,unit


def classify(report,unit,code):
    runner=load_runner()
    state=runner.validate_ordered_result(report)
    validate_unit_receipt(unit,code,report)
    if state=='FAILURE_NOT_REPRODUCED_INCONCLUSIVE': return state,[]
    details=[]
    for event in report['events']:
        if event['phase']=='public' and event.get('returncode')==2:
            reply=m.parse_public_reply(2,event.get('stdout','').encode('utf-8'),event.get('stderr','').encode('utf-8'))
            if (reply=={'ok':False,'overall':'BLOCKED','evidence_class':'TEST_ONLY',
                        'adapter_calls':0,'approvals_consumed':0,
                        'blockers':['ValueError: E_WORKER_TIMEOUT: no resend']} and
                    reply['ok'] is False and type(reply['adapter_calls']) is int and
                    type(reply['approvals_consumed']) is int):
                details.append({'phase':'public','mode':event['mode'],
                                'failure_kind':'INTERNAL_WORKER_TIMEOUT_CAUSE_UNPROVEN',
                                'blockers':reply['blockers']})
                continue
            state,detail=m.classify_public_reply(2,reply,Path('unused-for-refusal'))
            if detail: details.append({'phase':'public','mode':event['mode'],'diagnostic':detail})
        elif event['phase']=='replay' and 'E_DISTRIBUTED_CLEANUP' in event.get('error',''):
            detail=m.diagnostic_from_blockers([event['error']]) if event.get('error_complete') else None
            if detail: details.append({'phase':'replay','mode':event['mode'],'diagnostic':detail})
    return ('CAUSE_OBSERVED_PENDING_REVIEW' if any('diagnostic' in item for item in details) else
            'DIAGNOSTIC_MISSING_OR_TRUNCATED_INCONCLUSIVE'),details


def verify_calls(report,tests):
    for number,event in enumerate(report['events']):
        g.require(event.get('sequence')==number and
                  g.load_sealed(tests/'Ordered-Calls'/(str(number).zfill(2)+'.json'),
                     g.sha((json.dumps(event,sort_keys=True,ensure_ascii=True)+'\n').encode('utf-8')))==event,
                  'E_ORDERED_CALL_RECORD')
    g.require(g.inventory(tests/'Ordered-Calls')=={
              str(n).zfill(2)+'.json':g.sha((json.dumps(e,sort_keys=True,ensure_ascii=True)+'\n').encode('utf-8'))
              for n,e in enumerate(report['events'])},'E_ORDERED_CALL_SET')


def validate_pack_schema(pack):
    # The existing validator is private but already used by the retained review.
    from knowledge_bridge import retrieval_v2
    return retrieval_v2._validate_pack(pack)


def verify_fixture_and_packs(report,tests,source):
    public=[e for e in report['events'] if e['phase']=='public']
    root=Path(public[0]['argv'][public[0]['argv'].index('--project-root')+1])
    g.require(root.parent==tests/'retained-temp','E_ORDERED_FIXTURE_PATH')
    expected=m._fixture_values(m.OUTPUT)[0]['files']
    for name,digest in expected.items():
        g.require(g.file_record(root/name)['sha256']==digest,'E_ORDERED_FIXTURE_CHANGED')
    sys.path.insert(0,str(source/'memory-integrity/scripts'))
    from knowledge_bridge import indexing,contracts as c
    doc=indexing.load(root/'index',root,source/'claude-mon')
    records=[]
    for event in public:
        pack_path=root/('-'.join(event['mode'])+'.json')
        if event.get('returncode')!=0: continue
        reply=m.parse_public_reply(0,event['stdout'].encode('utf-8'),event['stderr'].encode('utf-8'))
        m.classify_public_reply(0,reply,pack_path)
        pack=c.read(pack_path);validate_pack_schema(pack)
        g.require(pack['pack_digest']==reply['pack_digest'] and pack['generation']==doc['generation'] and
                  reply['generation']==pack['generation'] and reply['units']==len(pack['units']) and
                  pack['source_basis_digest']==doc['source_basis_digest'] and
                  pack['policy_digest']==c.digest(c.canonical(c.read(root/'policy.json'))) and
                  pack['task_obligations_digest']==c.digest(c.canonical(c.read(root/'task.json'))) and
                  pack['coverage']=='UNVERIFIED' and pack['semantic_audit']=='UNVERIFIED' and
                  pack['retrieval']['engine']['generation_lease']==pack['generation'] and
                  (pack['retrieval']['engine']['strategy'],pack['retrieval']['engine']['execution'])==tuple(event['mode']) and
                  pack['retrieval']['engine']['learned'] is None and pack['retrieval']['engine']['rerank'] is None,
                  'E_ORDERED_PACK_BINDING')
        for unit in pack['units']:
            g.require(indexing.reopen(doc,root,{'source_id':unit['source_id'],'unit_id':unit['unit_id']})==unit,
                      'E_ORDERED_SOURCE_REOPEN')
        g.require(('worker','U000001') in {(u['source_id'],u['unit_id']) for u in pack['units']},
                  'E_ORDERED_REQUIRED_SOURCE')
        records.append(g.file_record(pack_path))
    return records


def run(contract,digest):
    value,doc,record,bootstrap_observed=preflight(contract,digest)
    env=i.windows_environment(dict(os.environ))
    g.require(env.get('USERPROFILE')==r'C:\Users\sakth','E_ORDERED_NORMAL_CONTEXT')
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',HF_HUB_OFFLINE='1',
               TRANSFORMERS_OFFLINE='1',KNOWLEDGE_WORKER_PYTHON=str(g.WORKER))
    for key in ('MODEL_PYTHON','KNOWLEDGE_MODEL_MANIFEST'):env.pop(key,None)
    output=guarded_output(lambda:preservation(value,doc,record),OUT,SOURCE,g.WORKSPACE,Path(doc['source']),i.OUTPUT)
    receipt={'schema_version':1,'scope':SCOPE,'status':'HARNESS_OR_CAPTURE_FAILED',
             'contract':record,'commands':[],'failure':None,'preservation':False,**{key:False for key in FLAGS}}
    starts=[];copy_complete=False
    try:
        g.save(output/'Bootstrap-Preflight.json',bootstrap_observed)
        receipt['bootstrap_preflight']=g.file_record(output/'Bootstrap-Preflight.json')
        for name,mapping in [('Before-Image-Attempt.json',g.inventory(i.OUTPUT)),
                             ('Before-Focused-Attempt.json',g.inventory(m.OUTPUT)),
                             ('Before-Ordered-v2-Attempt.json',g.inventory(FAILED_OUT))]:
            g.save(output/name,mapping); starts.append(g.file_record(output/name))
        receipt['start_maps']=starts
        preservation(value,doc,record,start_records=starts)
        # An absent copy is exclusive. All original helpers and test bytes remain unchanged.
        g.new_workspace(SOURCE,[Path(doc['source']),i.OUTPUT,m.OUTPUT,g.REPO,OUT])
        shutil.copytree(Path(doc['source']),SOURCE,dirs_exist_ok=True,copy_function=shutil.copyfile)
        worker=SOURCE/m.WORKER_RELATIVE
        worker.write_bytes(m.diagnostic_worker_bytes(worker.read_bytes()))
        g.verify_manifest(SOURCE,value['source_manifest']);copy_complete=True
        preservation(value,doc,record,True,starts)
        host=g.sibling_module('offline_host_validation',SOURCE/'.github/scripts')
        temp=output/'temp';temp.mkdir();env.update(TEMP=str(temp),TMP=str(temp),TMPDIR=str(temp))
        def capture(label,argv,timeout,exits=(0,)):
            print(label+': RUNNING (diagnostic only)',flush=True)
            target=output/label;target.mkdir()
            completed,row=host.capture_owned(list(map(str,argv)),target,output,env,timeout)
            receipt['commands'].append(dict(row,label=label))
            g.require(completed is not None and completed.returncode in exits,'E_ORDERED_CHILD: '+label)
            preservation(value,doc,record,True,starts)
            return completed,target
        capture('preclaim-git',[g.GIT,'--no-optional-locks','-C',doc['repo'],'rev-parse','HEAD'],30)
        _,probe=capture('preclaim-runtime',[g.WORKER,'-B','-c',g.runtime_probe()],60)
        i.validate_runtime_observation(json.loads((probe/'stdout.log').read_text(encoding='utf-8')),env,output)
        result,_=capture('ordered-method',[g.CONTROLLER,'-B',RUNNER,'--package-root',SOURCE/'memory-integrity',
            '--pattern','test_knowledge_completion.py','--output-dir',output/'tests-3'],600,(0,1))
        tests=output/'tests-3'
        report,unit=read_runner_records(tests,receipt['commands'][-1])
        verify_calls(report,tests)
        receipt['status'],receipt['diagnostics']=classify(report,unit,result.returncode)
        receipt['packs']=verify_fixture_and_packs(report,tests,SOURCE)
        receipt['outcomes']=g.file_record(tests/'Ordered-Outcomes.json')
        receipt['test_receipt']=g.file_record(tests/'Receipt.json')
    except BaseException:
        receipt['failure']=traceback.format_exc();receipt['status']='HARNESS_OR_CAPTURE_FAILED'
    finally:
        try:
            preservation(value,doc,record,copy_complete,starts);receipt['preservation']=True
        except BaseException:
            receipt['preservation_failure']=traceback.format_exc();receipt['status']='HARNESS_OR_CAPTURE_FAILED'
        g.save(output/'Receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'receipt':g.file_record(output/'Receipt.json'),
                      'failure':receipt['failure'],'gate1_complete':False,'whole_skill_ready':False}))
    return 1 if receipt['status']=='HARNESS_OR_CAPTURE_FAILED' else 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-contract',action='store_true')
    parser.add_argument('--preflight-only',action='store_true')
    parser.add_argument('--contract');parser.add_argument('--sha256')
    args=parser.parse_args()
    if args.prepare_contract:
        if args.contract or args.sha256 or args.preflight_only:parser.error('prepare-contract only')
        value=build_contract();g.save(CONTRACT,value)
        print(json.dumps({'status':'STATIC_INPUT_CONTRACT_ONLY_NO_RUNTIME_OR_ATTEMPT','contract':g.file_record(CONTRACT)}))
    elif not args.contract or not args.sha256:parser.error('sealed contract and hash required')
    elif args.preflight_only:
        preflight(args.contract,args.sha256);print('ORDERED_FULL_HISTORY_AND_REAL_BOOTSTRAP_PASSED_NO_WORKER')
    else:sys.exit(run(args.contract,args.sha256))
