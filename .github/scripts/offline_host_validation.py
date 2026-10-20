#!/usr/bin/env python3
"""Existing-runtime release check, not an old N3 retry or whole-skill qualification.

Inputs must match an externally supplied hash. All prior data remain read-only;
only fresh test-owned temporary files may be cleaned. No setup/native/model calls.
"""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path
import sys
import traceback

# Direct and importlib-based invocation share the same sibling implementation.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from offline_release_acceptance import (sha, read, save, require, ordinary_chain,
    new_output, command_directory, inventory, child_json,
    validate_receipt)
from offline_release_acceptance import outside_packages, stream_record

ROOT = Path(__file__).resolve().parents[2]
PATTERNS = ('test_native_containment.py','test_native_paths.py',
            'test_offline_release_profile.py','test_knowledge_process_lifecycle.py',
            'test_knowledge_distributed.py','test_knowledge_advanced.py',
            'test_knowledge_completion.py')
POSIX_ONLY = {
    'test_knowledge_distributed.DistributedRetrieval.test_suspended_worker_expires_shared_deadline_and_is_reaped',
    'test_knowledge_completion.RemainingPublicContract.test_timeout_terminates_worker_descendants',
}


def load_prepared(path, expected):
    path = ordinary_chain(path)
    require(path.is_file() and path.stat().st_nlink == 1 and
            sha(path.read_bytes()) == expected, 'E_HOST_EXTERNAL_HASH')
    return read(path)


def verify_inputs(doc):
    if 'optional_external_consumer' in doc:
        require(doc['optional_external_consumer'] == optional_guard_state(),
                'E_HOST_EXTERNAL_CONSUMER_CHANGED')
    for name, expected in doc['files'].items():
        path = Path(name)
        # Selected executables may have system hardlinks; evidence may not.
        require(path.is_absolute() and path.is_file() and sha(path.read_bytes()) == expected,
                'E_HOST_INPUT_CHANGED: '+name)
    for name, expected in doc['packages'].items():
        require(inventory(Path(name)) == expected, 'E_HOST_PACKAGE_CHANGED: '+name)


def required_files(worker):
    files = [Path(__file__).resolve(), ROOT/'.github/scripts/offline_release_acceptance.py',
             ROOT/'.github/scripts/retained_unittest.py', Path(sys.executable), Path(worker)]
    files.extend(p for p in (ROOT/'.github/fixtures/offline-first').rglob('*') if p.is_file())
    return {str(p) for p in files}


def optional_guard_path():
    return Path.home()/'.codex/skills/remote-skills/skill-6ab2a17ee0888191a75c7b5a1171fbbc/scripts/fable_guard.py'


def optional_guard_state():
    path = optional_guard_path()
    # This bounded check cannot execute an unreviewed external governor. Bind
    # absence explicitly, with lstat (permission errors are NOT absence). If a
    # guard exists, retain it and stop; its integration needs separate sealing.
    try:
        path.lstat()
    except FileNotFoundError:
        return {'path':str(path),'state':'ABSENT_NOT_EXERCISED'}
    raise ValueError('E_HOST_EXTERNAL_CONSUMER_PRESENT_UNBOUND: '+str(path))


def validate_prepared(doc):
    keys = {'schema_version','scope','root','controller','worker','files','packages','patterns',
            'native_execution','whole_skill_ready','producer_authentication','optional_external_consumer'}
    require(isinstance(doc,dict) and set(doc) == keys and type(doc['schema_version']) is int and
            doc['schema_version'] == 1 and doc['scope'] == 'OFFLINE_FIRST_RUNTIME_CHECK_NOT_N3' and
            doc['root'] == str(ROOT) and doc['controller'] == sys.executable and
            doc['optional_external_consumer'] == {'path':str(optional_guard_path()),'state':'ABSENT_NOT_EXERCISED'} and
            isinstance(doc['worker'],str) and Path(doc['worker']).is_absolute() and
            doc['patterns'] == list(PATTERNS) and
            all(doc[k] is False for k in ('native_execution','whole_skill_ready','producer_authentication')),
            'E_HOST_SCHEMA')
    packages = {str(ROOT/pkg) for pkg in ('memory-integrity','claude-mon')}
    require(isinstance(doc['files'],dict) and set(doc['files']) == required_files(doc['worker']) and
            all(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) for v in doc['files'].values()) and
            isinstance(doc['packages'],dict) and set(doc['packages']) == packages and
            all(isinstance(v,dict) and {'SKILL.md','capabilities-v2.json'} <= set(v) and
                all(isinstance(k,str) and isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h)
                    for k,h in v.items()) for v in doc['packages'].values()), 'E_HOST_SCHEMA_INPUTS')


def check_output(output, doc):
    path = ordinary_chain(output)
    require(path.is_absolute() and all(not path.is_relative_to(Path(root))
            for root in doc['packages']), 'E_HOST_OUTPUT_IN_PACKAGE')
    return outside_packages(path, doc['packages'])


def process_capture(argv, **kwargs):
    # Reuse the existing generic owned-tree capture, NOT a Beads/Dolt transport.
    sys.path.insert(0,str(ROOT/'memory-integrity/scripts'))
    from hybrid_bridge.native_observation import _capture_process
    return _capture_process(argv,**kwargs)


def capture_owned(argv, target, cwd, env, timeout):
    argv = list(map(str,argv))
    save(target/'Intent.json',{'argv':argv,'timeout_seconds':timeout})
    result, failure = None, None
    try:
        result = process_capture(argv,cwd=cwd,env=env,shell=False,timeout=timeout)
    except Exception:
        failure = traceback.format_exc()
    stdout, stderr = (result['stdout'],result['stderr']) if result else (b'',b'')
    (target/'stdout.log').write_bytes(stdout)
    (target/'stderr.log').write_bytes(stderr)
    execution = ('TIMEOUT' if result['timed_out'] else 'EXITED') if result else 'START_ERROR'
    record = {'argv':argv,'exit_code':result['exit_code'] if result else None,
              'execution':execution,'failure':failure,
              'stdout':stream_record(target/'stdout.log'),'stderr':stream_record(target/'stderr.log'),
              'containment':{k:v for k,v in result.items() if k not in ('stdout','stderr')} if result else None}
    save(target/'Command.json',record)
    # Never call a timed-out/incomplete/uncontained command successful.
    good = result and not result['timed_out'] and not result['output_limit_exceeded'] and \
           result['capture_complete'] is True and result['capture_errors'] == [] and \
           result['tree_contained'] is True
    return (subprocess.CompletedProcess(argv,result['exit_code'],stdout,stderr) if good else None),record


def create_output(output, doc):
    return new_output(check_output(output, doc))


def validate_suite(row, pattern):
    require(isinstance(row, dict) and type(row.get('tests_run')) is int and
            row['tests_run'] > 0 and row['tests_run'] == row.get('discovered') and
            all(row.get(k) == [] for k in ('failures','errors','excluded','expected_failures')) and
            row.get('interrupted') is False, 'E_HOST_SUITE: '+pattern)
    require(isinstance(row.get('skipped'),list) and all(
            isinstance(item,list) and len(item) == 2 and item[0] in POSIX_ONLY and
            'POSIX' in item[1] for item in row['skipped']), 'E_HOST_SUITE_SKIP: '+pattern)


def prepared(worker):
    worker = Path(worker)
    require(worker.is_absolute() and worker.is_file(), 'E_HOST_WORKER_PATH')
    controller = Path(sys.executable)
    return {'schema_version':1,'scope':'OFFLINE_FIRST_RUNTIME_CHECK_NOT_N3',
            'root':str(ROOT), 'controller':str(controller),'worker':str(worker),
            'files':{p:sha(Path(p).read_bytes()) for p in sorted(required_files(worker))},
            'packages':{str(ROOT/pkg):inventory(ROOT/pkg) for pkg in ('memory-integrity','claude-mon')},
            'patterns':list(PATTERNS),'native_execution':False,'whole_skill_ready':False,
            'producer_authentication':False,'optional_external_consumer':optional_guard_state()}


def prepare_inputs(destination, worker):
    protected = {'packages':{str(ROOT/pkg):{} for pkg in ('memory-integrity','claude-mon')}}
    destination = check_output(destination,protected)
    require(not destination.exists(), 'E_HOST_PREPARE_PATH')
    doc = prepared(worker)
    validate_prepared(doc)
    verify_inputs(doc)
    save(destination,doc)
    return doc


def execute(doc, output):
    validate_prepared(doc)
    verify_inputs(doc)
    require(doc['root'] == str(ROOT) and doc['patterns'] == list(PATTERNS) and
            doc['controller'] == sys.executable and doc['scope'] == 'OFFLINE_FIRST_RUNTIME_CHECK_NOT_N3',
            'E_HOST_SCOPE')
    output = create_output(output, doc)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8',
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               KNOWLEDGE_WORKER_PYTHON=doc['worker'])
    scratch = output/'runtime-temp'
    scratch.mkdir()
    for name in ('TEMP','TMP','TMPDIR'):
        env[name] = str(scratch)
    results, failure, runtime, acceptance = [], None, None, None
    save(output/'Inputs.json', doc)
    try:
        # Probe the actual existing interpreter before any worker/retrieval.
        print('Existing interpreter identity: RUNNING',flush=True)
        argv = [doc['worker'],'-I','-B','-c',
                "import json,sys;print(json.dumps({'version':list(sys.version_info[:2]),'executable':sys.executable}))"]
        proc, record = capture_owned(argv, command_directory(output,'interpreter'), ROOT, env, 30)
        require(proc is not None, 'E_HOST_INTERPRETER_START')
        runtime = child_json(proc)
        require(runtime['version'] == [3,12] and
                os.path.normcase(runtime['executable']) == os.path.normcase(doc['worker']),
                'E_HOST_INTERPRETER_IDENTITY')
        for pattern in PATTERNS:
            verify_inputs(doc)
            label = pattern.removesuffix('.py').replace('_','-')
            print(pattern+': RUNNING',flush=True)
            result_dir = output/label
            argv = [doc['controller'],'-B',str(ROOT/'.github/scripts/retained_unittest.py'),
                    '--package-root',str(ROOT/'memory-integrity'),'--pattern',pattern,
                    '--output-dir',str(result_dir)]
            proc, record = capture_owned(argv, command_directory(output,label), ROOT, env, 600)
            row = read(result_dir/'Receipt.json') if (result_dir/'Receipt.json').is_file() else None
            results.append({'pattern':pattern,'receipt':str(result_dir/'Receipt.json'),
                            'sha256':sha((result_dir/'Receipt.json').read_bytes()) if row else None,
                            'result':row,'command':record})
            require(proc is not None and proc.returncode == 0, 'E_HOST_SUITE_EXIT: '+pattern)
            validate_suite(row, pattern)
            print(pattern+': PASS', flush=True)
        argv = [doc['controller'],'-B',str(ROOT/'.github/scripts/offline_release_acceptance.py'),
                '--package-root',str(ROOT/'memory-integrity'),'--claude-mon-root',str(ROOT/'claude-mon'),
                '--worker-python',doc['worker'],'--output-dir',str(output/'acceptance')]
        print('Portable 24-arm acceptance: RUNNING',flush=True)
        proc, record = capture_owned(argv, command_directory(output,'acceptance'), ROOT, env, 900)
        require(proc is not None and proc.returncode == 0, 'E_HOST_ACCEPTANCE_EXIT')
        path = output/'acceptance/Receipt.json'
        acceptance = read(path)
        validate_receipt(acceptance)
        require(len(acceptance['measurements']) == 24, 'E_HOST_ACCEPTANCE_ARMS')
        acceptance = {'path':str(path),'sha256':sha(path.read_bytes()),'receipt':acceptance,'command':record}
    except Exception:
        failure = traceback.format_exc()
    try:
        verify_inputs(doc)
        preserved = True
    except Exception:
        preserved = False
        failure = (failure or '') + traceback.format_exc()
    receipt = {'schema_version':1,'status':'PASS_BOUNDED_HOST_CHECK_NOT_RELEASE' if failure is None
               else 'PARTIAL_OR_FAILED_NO_AUTOMATIC_RETRY',
               'inputs_sha256':sha((output/'Inputs.json').read_bytes()),
               'runtime':runtime,'suites':results,'acceptance':acceptance,
               'package_and_input_preservation':preserved,'failure':failure,
               'native_execution':False,'inference_sent':False,'installed':False,
               'whole_skill_ready':False,'producer_authentication':False}
    receipt['optional_external_consumer'] = doc['optional_external_consumer']
    receipt['external_governor_consumer_exercised'] = False
    save(output/'Receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'receipt':str(output/'Receipt.json'),
                      'sha256':sha((output/'Receipt.json').read_bytes()),'failure':failure}))
    return 0 if failure is None else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--prepare',type=Path)
    modes.add_argument('--run',type=Path)
    parser.add_argument('--worker-python')
    parser.add_argument('--prepared-sha256')
    parser.add_argument('--output-dir',type=Path)
    args = parser.parse_args()
    if args.prepare:
        require(args.worker_python and not args.prepare.exists(), 'E_HOST_PREPARE_PATH')
        prepare_inputs(args.prepare,args.worker_python)
        print(json.dumps({'prepared':str(args.prepare),'sha256':sha(args.prepare.read_bytes())}))
        return 0
    require(args.prepared_sha256 and args.output_dir, 'E_HOST_RUN_ARGS')
    return execute(load_prepared(args.run,args.prepared_sha256),args.output_dir)


if __name__ == '__main__':
    raise SystemExit(main())
