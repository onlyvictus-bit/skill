"""Separately sealed Gate1 successor; v1 files/attempt are immutable inputs.

Reuses the existing source, capture, suite and acceptance implementations. No
monkey-patching, output-guard redirection, installation or automatic retry.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PureWindowsPath
import sys
import traceback

HERE = Path(__file__).resolve()
CORE = HERE.with_name('gate1_validation.py')
CORE_SHA = 'f9b7ef54039756b3d8a95051b05a93e920518c970e6deb1c987bc5bb0aeed22e'
if hashlib.sha256(CORE.read_bytes()).hexdigest() != CORE_SHA:
    raise ValueError('E_IMAGE_PREDECESSOR_CHANGED')
_spec = importlib.util.spec_from_file_location('sealed_gate1_predecessor', CORE)
g = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g)

IMAGE = g.BASE.with_name('python3.12.exe')
IMAGE_SHA = '5365b422ee178f691988eb937b7abca5f48910b148f76fcce6dbaf5585c948d0'
OUTPUT = g.WORKSPACE/'image-successor-20261021'
PREPARED = g.WORKSPACE/'Prepared.json'
PREPARED_SHA = '6911308139ce8208327829b2ee1be57e59a5982d792ec66fbfa76d004fa37d5a'
PRIOR = g.WORKSPACE/'normal-attempt'
PRIOR_RECEIPT_SHA = '8336cf9eca7e72ec8c6b26ca9b9a54747a06b0d5e6634f83ddf1c052dfb68d6c'
SCOPE = 'GATE1_EXACT_STORE_IMAGE_CONTEXT_SUCCESSOR'
ENV_NAMES = ('USERPROFILE','TEMP','TMP','SYSTEMROOT','SystemDrive','PYTHONNOUSERSITE')
PROBE_KEYS = {'version','executable','base_executable','prefix','base_prefix',
              'image_path','image_sha256','cwd','environment','path_sha256','model_selected'}
CONTRACT_KEYS = {'schema_version','scope','head','parent_prepared','parent_receipt',
                 'prior_attempt','loaded_image','source','output','successor_helper',
                 'producer_authentication','release_ready','installed','native_execution'}


def windows_environment(env):
    result = {}
    for name, value in env.items():
        g.require(isinstance(name,str) and isinstance(value,str), 'E_IMAGE_ENV_TYPE')
        key = name.upper()
        g.require(key not in result, 'E_IMAGE_ENV_AMBIGUOUS: '+key)
        result[key] = value
    return result


def runtime_expectation(env, cwd):
    env = windows_environment(env)
    return {'version':[3,12,10], 'executable':str(g.WORKER),
            'base_executable':str(g.ALIAS), 'prefix':str(g.WORKER.parent.parent),
            'base_prefix':str(g.BASE.parent), 'image_path':str(IMAGE),
            'image_sha256':IMAGE_SHA, 'cwd':str(cwd), 'model_selected':False,
            'environment':{name:env.get(name.upper()) for name in ENV_NAMES},
            'path_sha256':g.sha(env.get('PATH','').encode())}


def validate_runtime_observation(observed, env, cwd):
    g.require(isinstance(observed,dict) and set(observed)==PROBE_KEYS,
              'E_G1_RUNTIME_OBSERVATION: schema')
    expected = runtime_expectation(env,cwd)
    paths = {'executable','base_executable','prefix','base_prefix','image_path','cwd'}
    wrong = []
    for key, value in expected.items():
        actual = observed[key]
        if key in paths:
            same = isinstance(actual,str) and PureWindowsPath(actual)==PureWindowsPath(value)
        elif key=='model_selected':
            same = actual is False
        else:
            same = actual==value
        if not same:wrong.append(key)
    g.require(not wrong,'E_G1_RUNTIME_OBSERVATION: '+','.join(sorted(wrong)))


def validate_contract(value):
    g.require(isinstance(value,dict) and set(value)==CONTRACT_KEYS and
              value['schema_version']==1 and value['scope']==SCOPE and value['head']==g.HEAD and
              all(value[k] is False for k in ('producer_authentication','release_ready','installed','native_execution')),
              'E_IMAGE_CONTRACT')
    g.require(value['source']==str(g.WORKSPACE/'source') and value['output']==str(OUTPUT),
              'E_IMAGE_CONTRACT_PATH')
    g.require(value['parent_prepared']==g.file_record(PREPARED) and
              value['parent_prepared']['sha256']==PREPARED_SHA and
              value['parent_receipt']==g.file_record(PRIOR/'Receipt.json') and
              value['parent_receipt']['sha256']==PRIOR_RECEIPT_SHA, 'E_IMAGE_PARENT_CHANGED')
    g.require(isinstance(value['prior_attempt'],dict) and value['prior_attempt'] and
              value['prior_attempt'].get('Receipt.json')==PRIOR_RECEIPT_SHA,
              'E_IMAGE_PRIOR_MANIFEST')
    g.require(value['loaded_image']==g.file_record(IMAGE) and
              value['loaded_image']['sha256']==IMAGE_SHA and value['loaded_image']['size']==172912,
              'E_IMAGE_LOADED_FILE_CHANGED')
    g.require(HERE==g.REPO/'.github/scripts/gate1_image_successor.py' and
              value['successor_helper']==g.file_record(HERE), 'E_IMAGE_HELPER_CHANGED')
    doc = g.load_sealed(PREPARED,PREPARED_SHA)
    g.validate_prepared(doc)
    return doc


def check_preserved(value, doc, contract_record=None):
    g.check_preserved(doc)
    g.verify_manifest(PRIOR,value['prior_attempt'])
    g.require(g.file_record(PREPARED)==value['parent_prepared'] and
              g.file_record(PRIOR/'Receipt.json')==value['parent_receipt'] and
              g.file_record(IMAGE)==value['loaded_image'] and
              g.file_record(HERE)==value['successor_helper'], 'E_IMAGE_INPUT_CHANGED')
    if contract_record is not None:
        g.require(g.file_record(Path(contract_record['path']))==contract_record,
                  'E_IMAGE_CONTRACT_CHANGED')


def preflight(contract, digest):
    value = g.load_sealed(Path(contract),digest)
    sealed_record = g.file_record(Path(contract))
    g.require(sealed_record['sha256']==digest,'E_IMAGE_CONTRACT_CHANGED')
    doc = validate_contract(value)
    check_preserved(value,doc,sealed_record)
    g.require(not OUTPUT.exists(), 'E_IMAGE_EXISTING_ATTEMPT_PRESERVED')
    return value,doc


def run(contract, digest):
    value,doc = preflight(contract,digest)
    sealed_record = g.file_record(Path(contract))
    g.require(sealed_record['sha256']==digest,'E_IMAGE_CONTRACT_CHANGED')
    source = Path(doc['source'])
    env = windows_environment(dict(os.environ))
    g.require(env.get('USERPROFILE')==r'C:\Users\sakth','E_IMAGE_NORMAL_CONTEXT')
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',HF_HUB_OFFLINE='1',
               TRANSFORMERS_OFFLINE='1',KNOWLEDGE_WORKER_PYTHON=doc['runtime']['worker']['path'])
    for name in ('MODEL_PYTHON','KNOWLEDGE_MODEL_MANIFEST'):env.pop(name,None)
    commands,suites = [],[]
    receipt = {'schema_version':1,'scope':SCOPE,'status':'PARTIAL_OR_FAILED_NO_RETRY',
               'contract':sealed_record,'parent_prepared':value['parent_prepared'],
               'commands':commands,'suites':suites,'failure':None,'preservation':False,
               'producer_authentication':False,'release_ready':False,'whole_skill_ready':False,
               'native_execution':False,'installed':False,'inference_sent':False}
    output = g.new_workspace(OUTPUT,[source,g.REPO,PRIOR])

    def capture(label, argv, timeout=1200):
        print(label+': RUNNING (result still requires validation)',flush=True)
        target = output/label;target.mkdir()
        completed,record = host.capture_owned(list(map(str,argv)),target,output,env,timeout)
        commands.append(dict(record,label=label))
        g.require(completed is not None and completed.returncode==0,
                  'E_IMAGE_CHILD_FAILED: '+label+' (read retained stderr)')
        check_preserved(value,doc,sealed_record)
        return target

    try:
        temp = output/'temp';temp.mkdir()
        env.update(TEMP=str(temp),TMP=str(temp),TMPDIR=str(temp))
        sys.path.insert(0,str(source/'.github/scripts'))
        host = g.sibling_module('offline_host_validation',source/'.github/scripts')
        g.save(output/'Expected-Runtime.json',runtime_expectation(env,output))
        receipt['expected_runtime'] = g.file_record(output/'Expected-Runtime.json')
        capture('preclaim-git',[g.GIT,'--no-optional-locks','-C',doc['repo'],'rev-parse','HEAD'],30)
        identity = capture('preclaim-runtime',[g.WORKER,'-B','-c',g.runtime_probe()],60)
        observed = json.loads((identity/'stdout.log').read_text(encoding='utf-8'))
        validate_runtime_observation(observed,env,output)
        receipt['runtime_observation'] = g.file_record(identity/'stdout.log')
        g.save(output/'evaluation-claim.json',{'contract_sha256':digest,'scope':SCOPE})
        capture('real-worker-cleanup',[sys.executable,'-B',doc['helpers']['gate1_worker_checks.py']['path'],
                '--source',source,'--worker',g.WORKER,'--output',output/'cleanup'])
        cleanup = json.loads((output/'cleanup/Receipt.json').read_text(encoding='utf-8'))
        g.require(cleanup.get('status')=='PASS_REAL_WORKER_CWD_AND_CLEANUP' and
                  cleanup.get('boundaries')==['single','shard'] and cleanup.get('all_reaped') is True,
                  'E_IMAGE_CLEANUP')
        receipt['cleanup'] = g.file_record(output/'cleanup/Receipt.json')
        runner = g.sibling_module('gate1_runner',HERE.parent)
        for number,(package,pattern) in enumerate(g.PATTERNS):
            capture('suite-'+str(number),[sys.executable,'-B',doc['helpers']['gate1_runner.py']['path'],
                    '--package-root',source/package,'--pattern',pattern,
                    '--output-dir',output/('tests-'+str(number))])
            case_path = output/('tests-'+str(number))/'Case-Outcomes.json'
            report = json.loads(case_path.read_text(encoding='utf-8'))
            g.require(report['expected_ids']==doc['test_ids'][str(number)],'E_IMAGE_DISCOVERY_CHANGED')
            g.validate_outcomes(report['outcomes'],doc['test_ids'][str(number)],runner.allowed_skips())
            suites.append({'package':package,'pattern':pattern,'report':g.file_record(case_path)})
        capture('coding-acceptance',[sys.executable,'-B',source/'.github/scripts/offline_release_acceptance.py',
                '--package-root',source/'memory-integrity','--claude-mon-root',source/'claude-mon',
                '--worker-python',g.WORKER,'--output-dir',output/'acceptance'],2400)
        acceptance = json.loads((output/'acceptance/Receipt.json').read_text(encoding='utf-8'))
        g.validate_acceptance(acceptance)
        receipt['acceptance'] = g.file_record(output/'acceptance/Receipt.json')
        receipt['status'] = 'GATE1_RUNTIME_OBSERVED_PENDING_RESULT_REVIEW'
    except BaseException:
        receipt['failure'] = traceback.format_exc()
    finally:
        try:
            check_preserved(value,doc,sealed_record)
            receipt['preservation'] = True
        except BaseException:
            receipt['preservation_failure'] = traceback.format_exc()
            receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
        g.save(output/'Receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'receipt':g.file_record(output/'Receipt.json'),
                      'failure':receipt['failure'],'whole_skill_ready':False}))
    return 0 if receipt['status']=='GATE1_RUNTIME_OBSERVED_PENDING_RESULT_REVIEW' else 1


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract',required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--preflight-only',action='store_true')
    args = parser.parse_args()
    if args.preflight_only:
        preflight(args.contract,args.sha256)
        print('IMAGE_SUCCESSOR_INPUTS_AND_PRESERVATION_VERIFIED_NO_WORKER')
    else:
        sys.exit(run(args.contract,args.sha256))
