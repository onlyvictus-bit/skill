"""MP1 sealed membership-only continuation; not a retry, fix or qualification."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import traceback

REPO = Path(__file__).absolute().parents[2]
ROOT = REPO/'.github/run-artifacts/cleanup-membership-20261025'
CONTRACT, OUTPUT = ROOT/'Inputs.json', ROOT/'normal-membership'
SUPPORT = ('.github/scripts/cleanup_membership_probe.py',)
TC_HELPER_SHA = '883ec3cda3ab7b6120f417cc79b0bee6d14b2fd6407cb9683491189c23ab3554'
TC_INPUT_SHA = 'cf45dfde1fae5d2bb5f601a8d54c4fa68e62d5db35e3248ffe9bdfecf9476d62'
TC_RECEIPT_SHA = '6d58fc03166bf752bfa60d2a8f8b4b6b724d1cc5c8132c75018f0372c4bd9b11'
BUDGETS = {'request':.1, 'shutdown':5, 'watchdog':60, 'default':120, 'emergency':5}
FALSE_FLAGS = ('stage_complete','gate1_complete','release_ready','installed','root_cause_confirmed','fix_validated','producer_authentication')
DOC_KEYS = {'scope','head','output','source','source_manifest','helper','support',
            'timing_input','timing_receipt','timing_inventory','budgets',*FALSE_FLAGS}


def require(value, message):
    if not value: raise ValueError(message)


def load(path, digest):
    for part in (path, *path.parents):
        require(not part.is_symlink() and not (part.stat().st_file_attributes & 0x400
                if hasattr(part.stat(),'st_file_attributes') else False), 'E_MP_REDIRECTED_HELPER')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'E_MP_HELPER_PIN')
    spec = importlib.util.spec_from_file_location('mp_'+path.stem, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


def context():
    tc = load(REPO/'.github/scripts/cleanup_timing_diagnostic.py', TC_HELPER_SHA)
    ld, cr, c1 = tc.context()
    return tc, ld, cr, c1


def validate_budgets(value):
    require(value == BUDGETS and all(type(value[k]) is type(v) for k,v in BUDGETS.items()), 'E_MP_BUDGET')


def check_capture(completed, row):
    flags = row.get('containment') or {}
    require(completed is not None and type(completed.returncode) is int and completed.returncode == 0 and row.get('exit_code') == 0 and
            type(row.get('exit_code')) is int and row.get('execution') == 'EXITED' and
            row.get('failure') is None and flags.get('timed_out') is False and
            flags.get('capture_complete') is True and flags.get('tree_contained') is True and flags.get('capture_errors') == [] and
            flags.get('output_limit_exceeded') is False, 'E_MP_CAPTURE_INCOMPLETE')
    # A containment method label is not proof of the fixture's process exit.
    # The probe separately waits its exact creation-bound native process handles.


def validate_probe(result, probe):
    require(result.get('scope') == 'MP1_MEMBERSHIP_ONLY_NOT_FIX' and
            result.get('fixture_topology') == 'SELECTED_VENV_ORIGINAL_RELAY_CHILD' and
            all(result.get(k) is False for k in FALSE_FLAGS),
            'E_MP_PROBE_SCOPE')
    emergency = result.get('emergency_cleanup') or {}
    roles = emergency.get('roles_signalled') or {}
    require(type(result.get('writer_alive_after_stop')) is bool and
            emergency.get('completed') is True and emergency.get('errors') == [] and
            emergency.get('writer_joined') is True and
            all(emergency.get(key) is True for key in ('streams_closed','root_reaped','job_closed')) and
            set(roles) == {'root','relay','launcher','child'} and all(value is True for value in roles.values()),
            'E_MP_EMERGENCY_INCOMPLETE')
    handle_cleanup = result.get('handle_cleanup') or {}
    require(handle_cleanup.get('completed') is True and handle_cleanup.get('errors') == [],
            'E_MP_HANDLE_CLEANUP_INCOMPLETE')
    expected = probe.classify(result['before'], result['after'], result['writer_alive_after_stop'],
                              result['stop_error'], observation_errors=result['observation_errors'])
    require(result.get('status') == expected, 'E_MP_PROBE_CLASSIFICATION')
    return expected


def verify(c1, doc):
    tc, ld, _cr, _c1 = context()
    require(set(doc) == DOC_KEYS and doc['scope'] == 'MP1_FOCUSED_MEMBERSHIP_DIAGNOSTIC' and
            doc['head'] == c1.HEAD and doc['output'] == str(OUTPUT) and
            doc['source'] == str(ld.SOURCE) and doc['helper'] == c1.record(Path(__file__).absolute()) and
            set(doc['support']) == set(SUPPORT) and all(doc[k] is False for k in FALSE_FLAGS), 'E_MP_INPUT_CONTRACT')
    validate_budgets(doc['budgets'])
    require(c1.sha(c1.read_file(tc.CONTRACT)) == TC_INPUT_SHA and
            doc['timing_input'] == c1.record(tc.CONTRACT), 'E_MP_TC_INPUT')
    parent = json.loads(c1.read_file(tc.CONTRACT)); tc.verify(c1,parent)
    require(c1.sha(c1.read_file(tc.OUTPUT/'Receipt.json')) == TC_RECEIPT_SHA and
            doc['timing_receipt'] == c1.record(tc.OUTPUT/'Receipt.json') and
            c1.source_manifest(tc.ROOT) == doc['timing_inventory'], 'E_MP_TC_HISTORY')
    require(doc['source_manifest'] == parent['source_manifest'], 'E_MP_SOURCE_BASIS')
    c1.verify_source(ld.SOURCE,doc['source_manifest'])
    for name, record in doc['support'].items():
        require(c1.record(REPO/name) == record, 'E_MP_SUPPORT_CHANGED')
    require(c1.git('rev-parse','HEAD').decode().strip() == c1.HEAD, 'E_MP_HEAD')


def prepare():
    tc, ld, _cr, c1 = context()
    c1.normal_account()
    require(not os.path.lexists(ROOT), 'E_MP_INPUTS_EXIST')
    parent = json.loads(c1.read_file(tc.CONTRACT)); tc.verify(c1,parent)
    require(c1.sha(c1.read_file(tc.OUTPUT/'Receipt.json')) == TC_RECEIPT_SHA, 'E_MP_TC_RECEIPT')
    doc = {'scope':'MP1_FOCUSED_MEMBERSHIP_DIAGNOSTIC','head':c1.HEAD,'output':str(OUTPUT),
           'source':str(ld.SOURCE),'source_manifest':parent['source_manifest'],
           'helper':c1.record(Path(__file__).absolute()),
           'support':{name:c1.record(REPO/name) for name in SUPPORT},
           'timing_input':c1.record(tc.CONTRACT),'timing_receipt':c1.record(tc.OUTPUT/'Receipt.json'),
           'timing_inventory':c1.source_manifest(tc.ROOT),'budgets':BUDGETS,
           **{key:False for key in FALSE_FLAGS}}
    verify(c1,doc)
    c1.ordinary(ROOT.parent); ROOT.mkdir(); c1.ordinary(ROOT); c1.save(CONTRACT,doc)
    print(json.dumps({'status':'MP1_INPUTS_ONLY_NO_SELECTED_RUNTIME','contract':c1.record(CONTRACT)}))


def run(digest):
    _tc, _ld, cr, c1 = context()
    c1.normal_account()
    require(c1.sha(c1.read_file(CONTRACT)) == digest, 'E_MP_EXTERNAL_INPUTS')
    doc = json.loads(c1.read_file(CONTRACT)); verify(c1,doc)
    require(not os.path.lexists(OUTPUT), 'E_MP_EXISTING_ATTEMPT')
    c1.ordinary(OUTPUT.parent); OUTPUT.mkdir(); c1.ordinary(OUTPUT)
    receipt = {'status':'PARTIAL_OR_FAILED_NO_RETRY','started_utc':datetime.now(timezone.utc).isoformat(),
               'contract':c1.record(CONTRACT),'commands':[],'failure':None,'attempt_consumed':False,
               'probe_inventory':None, **{key:False for key in FALSE_FLAGS}}
    try:
        host = c1.load_support('offline_host_validation')
        c2 = cr.load('gate1_current_runtime'); g = c1.load_support('gate1_validation')
        (OUTPUT/'temp').mkdir(); env = c2.environment(OUTPUT/'temp')
        def capture(label, argv, timeout):
            target = OUTPUT/label; target.mkdir(); c1.ordinary(target)
            print(label+': RUNNING (MP1 membership-only, not a fix)',flush=True)
            completed,row = host.capture_owned(argv,target,target,env,timeout)
            row['label'] = label; receipt['commands'].append(row)
            check_capture(completed,row)
            return completed
        completed = capture('preclaim-identity',[g.WORKER,'-B','-c',g.runtime_probe()],30)
        c1.validate_runtime(json.loads(completed.stdout),env,OUTPUT/'preclaim-identity')
        script = "import importlib.metadata as m,json,site;d=m.distribution('semantica');u=json.loads(d.read_text('direct_url.json') or '{}');print(json.dumps({'versions':{n:m.version(n) for n in "+repr(sorted(c1.dependency_versions()))+"},'revision':u.get('vcs_info',{}).get('commit_id'),'user_site':site.ENABLE_USER_SITE}))"
        completed = capture('preclaim-dependencies',[g.WORKER,'-B','-c',script],30)
        c1.validate_dependencies(json.loads(completed.stdout),c1.dependency_versions())
        verify(c1,doc)
        with (OUTPUT/'membership-attempt').open('xb') as stream: stream.write(b'ONE focused membership witness\n')
        receipt['attempt_consumed'] = True
        capture('membership',[g.WORKER,'-B',REPO/SUPPORT[0],'--source',doc['source'],
                              '--output',OUTPUT/'probe'],BUDGETS['watchdog'])
        raw = c1.read_file(OUTPUT/'probe/Probe.json')
        require(len(raw) <= 1048576, 'E_MP_PROBE_SIZE')
        result = json.loads(raw)
        probe = load(REPO/SUPPORT[0],doc['support'][SUPPORT[0]]['sha256'])
        receipt['classification'] = validate_probe(result,probe)
        receipt['probe_inventory'] = c1.source_manifest(OUTPUT/'probe')
        receipt['probe_record'] = c1.record(OUTPUT/'probe/Probe.json')
        receipt['status'] = 'MP1_MEMBERSHIP_CAPTURED_NOT_FIX_OR_STAGE_COMPLETE'
    except BaseException:
        receipt['failure'] = traceback.format_exc()
    finally:
        try:
            verify(c1,doc)
            if receipt['probe_inventory'] is not None:
                c1.verify_source(OUTPUT/'probe',receipt['probe_inventory'])
            receipt['pinned_preservation_verified'] = True
        except Exception:
            receipt['preservation_failure'] = traceback.format_exc()
            receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        c1.save(OUTPUT/'Receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'receipt':c1.record(OUTPUT/'Receipt.json'),
                      'classification':receipt.get('classification'),'failure':receipt['failure'],
                      'stage_complete':False,'gate1_complete':False}))
    return 0 if receipt['failure'] is None and receipt.get('pinned_preservation_verified') is True else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare',action='store_true'); action.add_argument('--sha256')
    args = parser.parse_args()
    if args.prepare: prepare()
    else: raise SystemExit(run(args.sha256))
