"""Sealed W-COPY successor. Old W files/commands are never modified or rerun.

Normal and reader phases cooperate through immutable externally hashed files.
The inherited workload is the exact pinned W routine, not an injected runner.
"""
import argparse
import ast
import importlib.util
import json
from pathlib import Path
import sys
import traceback
import types

import archive_copy_snapshot as s

HERE = Path(__file__).absolute()
REPO = HERE.parents[2]
ROOT = Path(r'C:\Users\sakth\Documents\Codex\w-copy-20261022-7b7f219a')
SESSION = '7b7f219af07a425185a7ae4adb72a1bc'
CONFIG = ROOT/'Input-Seal.json'
W_SHA = '7e67e131c752c1f7c947e899d8a3cd8853cf070730ca2b4e089aeeb66752aa8c'
W_PATH = HERE.with_name('worker_timing_lifetime_diagnostic.py')
PHASES = ('Before','CopyBefore','VerifyBefore','Run','After','CopyAfter','Finalize')


def load_w():
    s.require(s.record(W_PATH)['sha256'] == W_SHA, 'E_COPY_CONTROLLER_PIN')
    raw = W_PATH.read_bytes()
    s.require(__import__('hashlib').sha256(raw).hexdigest() == W_SHA, 'E_COPY_CONTROLLER_PIN')
    spec = importlib.util.spec_from_file_location('copy_pinned_w',W_PATH)
    w = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(W_PATH),'exec'),w.__dict__)
    return w


def mandatory_reader(w):
    """Retain the pinned historical guard except its ONE supplementary map.

    No permission exception is swallowed, no inventory function is replaced,
    and every original mandatory call and both V3 inventories remain executable.
    """
    s.require(s.record(w.HERE)['sha256'] == W_SHA, 'E_COPY_CONTROLLER_PIN')
    raw = w.HERE.read_bytes()
    s.require(__import__('hashlib').sha256(raw).hexdigest() == W_SHA, 'E_COPY_CONTROLLER_PIN')
    tree = ast.parse(raw)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'historical_readback']
    s.require(len(functions) == 1, 'E_COPY_GUARD_SHAPE')
    function = functions[0]
    assignment = function.body[-2]
    s.require(isinstance(assignment,ast.Assign) and len(assignment.targets) == 1 and
              isinstance(assignment.targets[0],ast.Name) and assignment.targets[0].id == 'observations' and
              isinstance(assignment.value,ast.Dict), 'E_COPY_GUARD_SHAPE')
    pairs = list(zip(assignment.value.keys,assignment.value.values))
    hits = [(k,v) for k,v in pairs if isinstance(k,ast.Constant) and k.value == 'private_artifacts']
    s.require(len(hits) == 1 and ast.unparse(hits[0][1]) == 'g.inventory(ARTIFACTS)', 'E_COPY_GUARD_SHAPE')
    pairs = [(k,v) for k,v in pairs if (k,v) not in hits]
    assignment.value.keys = [k for k,v in pairs]; assignment.value.values = [v for k,v in pairs]
    namespace = dict(w.__dict__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),
                 '<pinned-W-minus-one-supplementary-map>','exec'),namespace)
    return namespace['historical_readback']


def check_roles(roles):
    s.require(isinstance(roles,dict) and roles, 'E_COPY_ROLE_SET')
    for name, expected in roles.items():
        s.require(s.record(Path(name)) == expected, 'E_COPY_ROLE_CHANGED:'+name)


def verify_config(sha):
    value = s.load(CONFIG,sha); w = load_w()
    expected_roles = w.required_files() | set(map(str,(w.SEAL,w.LAUNCHER,HERE,
        HERE.with_name('archive_copy_snapshot.py'),REPO/'.github/tests/test_archive_copy_snapshot.py',
        REPO/'.github/tests/test_worker_copy_successor.py')))
    s.require(set(value) == {'scope','root','session','head','archive','files','original_seal_sha256'} and
              value['scope'] == 'W_COPY_STAGED_SUCCESSOR_V1' and value['root'] == str(ROOT) and
              value['session'] == SESSION and value['head'] == w.HEAD and value['archive'] == str(w.ARTIFACTS)
              and isinstance(value['files'],dict) and set(value['files']) == expected_roles,
              'E_COPY_CONFIG')
    check_roles(value['files'])
    w.verify_own_seal(w.SEAL,value['original_seal_sha256'])
    return value,w


def request_path(root,phase): return Path(root)/phase/'Request.json'
def bundle_path(root,phase): return Path(root)/phase/'Bundle.json'
def copies_path(root,phase): return Path(root)/phase/'reader-copy'


def load_before(root,external_sha):
    value = s.load(bundle_path(root,'before'),external_sha)
    s.validate_context(value)
    s.require(value['phase'] == 'BEFORE', 'E_COPY_BEFORE_REQUIRED')
    return value


def after_binding(root,before_sha):
    load_before(root,before_sha)
    row = s.record(Path(root)/'run/Receipt.json')
    workload = s.load(Path(row['path']),row['sha256'])
    s.require(workload.get('status') == 'PENDING_AFTER_SNAPSHOT' and workload.get('preservation') is False,
              'E_COPY_PROVISIONAL_REQUIRED')
    expected_prepared_path = Path(root)/'run/Prepared.json'
    prepared_record = workload.get('prepared')
    s.require(isinstance(prepared_record,dict) and set(prepared_record) == {'path','size','sha256'} and
              prepared_record['path'] == str(expected_prepared_path) and
              prepared_record == s.record(expected_prepared_path), 'E_COPY_WORKLOAD_PREPARED')
    prepared = s.load(expected_prepared_path,prepared_record['sha256'])
    s.require(isinstance(prepared,dict) and set(prepared) == {'before','seal','source_manifest','history'},
              'E_COPY_WORKLOAD_PREPARED')
    s.require(prepared['before'] == s.record(bundle_path(root,'before')) and
              prepared['before']['sha256'] == before_sha, 'E_COPY_WORKLOAD_BEFORE')
    s.require(prepared['seal'] == s.record(Path(root)/'Input-Seal.json') and
              isinstance(prepared['source_manifest'],dict) and len(prepared['source_manifest']) == 567 and
              all(isinstance(k,str) and s.hexdigest(v) for k,v in prepared['source_manifest'].items()) and
              isinstance(prepared['history'],dict) and set(prepared['history']) ==
                  {'label','v3_output','v3_source','transitions'} and
              prepared['history']['label'] == 'FIRST_OBSERVATION_NOT_ORIGINAL_PRESERVATION' and
              all(workload.get(k) is False for k in load_w().FLAGS), 'E_COPY_WORKLOAD_PREPARED')
    return {'before_sha256':before_sha,'workload_sha256':row['sha256']}


def save_provisional(path,receipt):
    flags = load_w().FLAGS
    s.require(all(receipt.get(k) is False for k in flags), 'E_COPY_QUALIFICATION')
    receipt['workload_status'] = receipt['status']
    receipt.update(status='PENDING_AFTER_SNAPSHOT',preservation=False,
                   supplementary_preservation='PENDING_FRESH_ORIGINAL_READBACK')
    s.save(path,receipt)


def sealed_request(phase,sha):
    value = s.load(request_path(ROOT,phase),sha)
    s.validate_request(value)
    s.require(value['root'] == str(load_w().ARTIFACTS) and value['session'] == SESSION and
              value['phase'] == phase.upper(), 'E_COPY_REQUEST_SCOPE')
    return value


def verify_existing_bundle(phase,sha):
    value = s.load(bundle_path(ROOT,phase),sha)
    request = sealed_request(phase,value['request_sha256'])
    expected = s.bundle_from_copies(request,copies_path(ROOT,phase),value['copy_record']['sha256'])
    s.require(value == expected, 'E_COPY_BUNDLE_DERIVATION')
    return value,request


def prepare_request(phase,w,before_sha):
    w.normal_account()
    folder = ROOT/phase
    s.require(not folder.exists(), 'E_COPY_EXISTING_PHASE_NO_RETRY')
    print('Mandatory pinned history readback first; no numerical worker.',flush=True)
    mandatory_reader(w)()
    binding = after_binding(ROOT,before_sha) if phase == 'after' else None
    print('Scanning readable archive; denied paths become explicit copy requests.',flush=True)
    request = s.scan(w.ARTIFACTS,SESSION,phase.upper(),binding)
    folder.mkdir()  # Only after a complete readable/unresolved observation.
    s.save(folder/'Request.json',request)
    return {'status': 'COPY_REQUEST_'+phase.upper()+'_NO_WORKER', 'request':s.record(folder/'Request.json'),
            'readable_objects':len(request['objects']),'unresolved_targets':len(request['unresolved']),
            'workload_attempt_consumed':False,'gate1_complete':False,'producer_authentication':False}


def verify_before(prepared,w):
    before,request = verify_existing_bundle('before',prepared['before']['sha256'])
    s.require(s.record(bundle_path(ROOT,'before')) == prepared['before'], 'E_COPY_BEFORE_MOVED')
    o,doc,history = mandatory_reader(w)()
    s.require(history == prepared['history'] and doc['source_manifest'] == prepared['source_manifest'],
              'E_COPY_MANDATORY_CHANGED')
    # Readable originals remain live-checked. Restricted originals are sampled
    # AFTER, not silently treated as read by the normal-account middle guards.
    actual,unresolved = s.collect(w.ARTIFACTS,True)
    s.require(actual == request['objects'] and unresolved == request['unresolved'], 'E_COPY_READABLE_CHANGED')
    return o,doc


def run_workload(config,w,before_sha):
    w.normal_account()
    before,request = verify_existing_bundle('before',before_sha)
    o,doc,history = mandatory_reader(w)()
    prepared = {'before':s.record(bundle_path(ROOT,'before')),'seal':s.record(CONFIG),
                'source_manifest':doc['source_manifest'],'history':history}
    s.require(prepared['before']['sha256'] == before_sha, 'E_COPY_BEFORE_MOVED')
    verify_before(prepared,w)
    output = ROOT/'run'
    s.require(not output.exists(), 'E_COPY_WORKLOAD_ALREADY_ATTEMPTED')
    sources = [ROOT/'wcbas1',ROOT/'wcobs1']
    s.require(all(not p.exists() for p in sources), 'E_COPY_SOURCE_EXISTS')
    output.mkdir(); s.save(output/'Prepared.json',prepared)
    # Clone only the exact pinned routine's code with closed controller bindings;
    # no command-line/custom-runner/guard injection is provided. Old globals and
    # old files stay unchanged. Worker payloads/deadlines/cleanup are identical.
    namespace = dict(w.__dict__)
    def validate(value):
        s.require(value == prepared, 'E_COPY_PREPARED_CHANGED')
    def verify_seal(path,sha):
        s.require(Path(path) == CONFIG and sha == prepared['seal']['sha256'], 'E_COPY_CONFIG_MOVED')
        verify_config(sha)
    def save(path,row):
        if Path(path) == output/'Receipt.json': save_provisional(path,row)
        else: w.save(path,row)
    namespace.update(OUT=output,SOURCES=sources,SEAL=CONFIG,validate_prepared=validate,
        verify_own_seal=verify_seal,check_preservation=lambda value:verify_before(value,w),save=save)
    namespace['overlay_copy'] = types.FunctionType(w.overlay_copy.__code__,namespace)
    routine = types.FunctionType(w.run.__code__,namespace)
    routine(output/'Prepared.json',s.record(output/'Prepared.json')['sha256'])
    return {'status':'PENDING_AFTER_SNAPSHOT','receipt':s.record(output/'Receipt.json'),
            'preservation':False,'gate1_complete':False,'producer_authentication':False}


def finalize(w,before_sha,after_sha):
    w.normal_account()
    before,_ = verify_existing_bundle('before',before_sha)
    after,_ = verify_existing_bundle('after',after_sha)
    s.require(after['binding'] == after_binding(ROOT,before_sha), 'E_COPY_WORKLOAD_CHANGED')
    comparison = s.compare(before,after)
    mandatory_reader(w)()
    result = {'status':'COPY_PRESERVATION_OBSERVED_WORKLOAD_REQUIRES_REVIEW',
              'before':s.record(bundle_path(ROOT,'before')),'after':s.record(bundle_path(ROOT,'after')),
              'workload':s.record(ROOT/'run/Receipt.json'),'comparison':comparison,
              **{key:False for key in w.FLAGS}}
    s.save(ROOT/'Final.json',result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=PHASES,required=True)
    parser.add_argument('--config-sha256',required=True)
    parser.add_argument('--input-sha256')
    parser.add_argument('--before-sha256')
    parser.add_argument('--after-sha256')
    args = parser.parse_args()
    config,w = verify_config(args.config_sha256)
    try:
        s.require(not (ROOT/(args.mode+'-Failure.json')).exists(), 'E_COPY_PHASE_ALREADY_FAILED_NO_RETRY')
        if args.mode == 'VerifyBefore':
            s.require(not bundle_path(ROOT,'before').exists(), 'E_COPY_BEFORE_ALREADY_VERIFIED')
        if args.mode == 'Finalize':
            s.require(not (ROOT/'Final.json').exists() and not bundle_path(ROOT,'after').exists(),
                      'E_COPY_FINALIZATION_ALREADY_ATTEMPTED')
        if args.mode in ('Before','After'):
            result = prepare_request(args.mode.lower(),w,args.before_sha256)
        elif args.mode in ('CopyBefore','CopyAfter'):
            phase = 'before' if args.mode == 'CopyBefore' else 'after'
            request = sealed_request(phase,args.input_sha256)
            s.copy_denied(request,copies_path(ROOT,phase))
            result = {'status':'COPIES_CREATED_NORMAL_VERIFICATION_REQUIRED',
                      'copies':s.record(copies_path(ROOT,phase)/'Copies.json'),'producer_authentication':False}
        elif args.mode == 'VerifyBefore':
            w.normal_account()
            request = sealed_request('before',s.record(request_path(ROOT,'before'))['sha256'])
            result = s.merge(request,copies_path(ROOT,'before'),args.input_sha256)
            s.save(bundle_path(ROOT,'before'),result)
            result = {'status':'BEFORE_SAMPLE_VERIFIED_NO_WORKER','bundle':s.record(bundle_path(ROOT,'before')),
                      'gate1_complete':False}
        elif args.mode == 'Run': result = run_workload(config,w,args.before_sha256)
        else:
            # Finalize verifies freshly copied AFTER data, then writes the new
            # final content report. It never edits the provisional workload.
            w.normal_account()
            request = sealed_request('after',s.record(request_path(ROOT,'after'))['sha256'])
            after = s.merge(request,copies_path(ROOT,'after'),args.input_sha256)
            s.save(bundle_path(ROOT,'after'),after)
            result = finalize(w,args.before_sha256,s.record(bundle_path(ROOT,'after'))['sha256'])
        print(json.dumps(result))
        return 0
    except BaseException:
        failure = {'status':'COPY_SUCCESSOR_STOP_NO_AUTOMATIC_RETRY','mode':args.mode,
                   'failure':traceback.format_exc(),'gate1_complete':False,'producer_authentication':False}
        target = ROOT/(args.mode+'-Failure.json')
        try: s.save(target,failure)
        except FileExistsError: pass  # Preserve the original failure, never overwrite it.
        print(json.dumps(failure))
        return 1


if __name__ == '__main__': raise SystemExit(main())
