#!/usr/bin/env python3
"""Retained scratch-only env/cwd diagnostic. Not a host-a1 or N3 retry.

Executes the existing single/shard boundaries unchanged in NEW working folders.
No model, native backend, resolver, setup, security/config change or cleanup.
The receipt is unauthenticated observation, not product/release qualification.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parent))
from offline_release_acceptance import (sha, read, save, require, ordinary_chain,
    outside_packages, new_output, stream_record)

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ('memory-integrity','claude-mon')
ARM_NAMES = ('startup-control','startup-a','startup-b','single','shard')
KEYS = {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','LANG','LC_ALL'}
SCRIPT_NAMES = ('cache_cause_probe.py','offline_release_acceptance.py','offline_host_validation.py')
FLAGS = {'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1',
         'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'}


def inventory(path):
    """No cache exclusions, best-effort traversal or suppressed access errors."""
    root = ordinary_chain(path).resolve(strict=True)
    result = {}
    for parent, dirs, files in os.walk(root,followlinks=False,onerror=lambda e: (_ for _ in ()).throw(e)):
        for name in dirs + files:
            entry = ordinary_chain(Path(parent)/name)
            if entry.is_file():
                require(entry.stat().st_nlink == 1,'E_PROBE_LINKED_EVIDENCE')
                result[entry.relative_to(root).as_posix()] = sha(entry.read_bytes())
    return dict(sorted(result.items()))


def source_filter_inventory():
    """Characterize both actual source boundaries, not a proposed replacement."""
    rows = {}
    for name, file, boundary in (
            ('single','worker_client.py','_process'),
            ('shard','distributed_retrieval.py','__init__')):
        path = ROOT/'memory-integrity/scripts/knowledge_bridge'/file
        tree = ast.parse(path.read_text(encoding='utf-8'))
        function = next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name == boundary)
        sets = [set(ast.literal_eval(n)) for n in ast.walk(function)
                if isinstance(n,ast.Set) and all(isinstance(x,ast.Constant) and isinstance(x.value,str)
                                                for x in n.elts)]
        require(sum(value == KEYS for value in sets) == 1,'E_PROBE_SOURCE_FILTER_DRIFT')
        calls = [n for n in ast.walk(function) if isinstance(n,ast.Call) and
                 isinstance(n.func,ast.Attribute) and n.func.attr == 'Popen']
        require(len(calls) == 1,'E_PROBE_LAUNCH_BOUNDARY_DRIFT')
        rows[name] = {'path':str(path),'sha256':sha(path.read_bytes()),'keys':sorted(KEYS),
                      'explicit_cwd':any(k.arg == 'cwd' for k in calls[0].keywords)}
    return rows


def filtered_context(source,scratch):
    # Deliberately retain the current source filter, including absent SystemDrive.
    env = {k:v for k,v in source.items() if k.upper() in KEYS}
    env.update(FLAGS)
    # New process-owned temp output, not an existing user/system cache location.
    for key in tuple(env):
        if key.upper() in ('TEMP','TMP'):
            del env[key]
    env.update(TEMP=str(scratch),TMP=str(scratch))
    return env


def basis(worker):
    worker = Path(worker).absolute()
    require(worker.is_file(),'E_PROBE_EXECUTABLE')
    return {'schema_version':1,'scope':'CACHE_CAUSE_SCRATCH_NOT_QUALIFICATION',
            'root':str(ROOT),'controller':stream_record(sys.executable),
            'worker':stream_record(worker),'source_boundaries':source_filter_inventory(),
            'scripts':{name:sha((ROOT/'.github/scripts'/name).read_bytes()) for name in SCRIPT_NAMES},
            'protected_packages':{pkg:inventory(ROOT/pkg) for pkg in PACKAGES},
            'arms':list(ARM_NAMES),'producer_authentication':False,'whole_skill_ready':False,
            'native_execution':False,'model_inference':False}


def verify_basis(value):
    expected = {'schema_version','scope','root','controller','worker','source_boundaries','scripts',
                'protected_packages','arms','producer_authentication','whole_skill_ready',
                'native_execution','model_inference'}
    require(isinstance(value,dict) and set(value) == expected and
            type(value['schema_version']) is int and value['schema_version'] == 1 and
            value['scope'] == 'CACHE_CAUSE_SCRATCH_NOT_QUALIFICATION' and value['root'] == str(ROOT) and
            value['arms'] == list(ARM_NAMES) and all(value[k] is False for k in
                ('producer_authentication','whole_skill_ready','native_execution','model_inference')),
            'E_PROBE_SCHEMA')
    require(isinstance(value['protected_packages'],dict) and
            set(value['protected_packages']) == set(PACKAGES) and
            all(isinstance(rows,dict) and {'SKILL.md','capabilities-v2.json'} <= rows.keys() and
                all(isinstance(p,str) and isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h)
                    for p,h in rows.items()) for rows in value['protected_packages'].values()),
            'E_PROBE_SCHEMA')
    for name in ('controller','worker'):
        row = value[name]
        require(isinstance(row,dict) and set(row) == {'path','size','sha256'} and
                isinstance(row['path'],str) and Path(row['path']).is_absolute() and
                Path(row['path']).is_file() and stream_record(row['path']) == row,'E_PROBE_EXECUTABLE_CHANGED')
    require(value['controller']['path'] == sys.executable,'E_PROBE_CONTROLLER_CHANGED')
    require(value['scripts'] == {n:sha((ROOT/'.github/scripts'/n).read_bytes()) for n in SCRIPT_NAMES}
            and value['source_boundaries'] == source_filter_inventory(),'E_PROBE_HELPER_CHANGED')
    for pkg in PACKAGES:
        require(value['protected_packages'][pkg] == inventory(ROOT/pkg),
                'E_PROBE_PROTECTED_CHANGED: '+pkg)


def new_probe_output(path):
    path = Path(path)
    require(path.is_absolute(),'E_OUTPUT_ABSOLUTE')
    return new_output(outside_packages(path,[ROOT/pkg for pkg in PACKAGES]))


def changes(before,after):
    return {'added':{n:after[n] for n in sorted(after.keys()-before.keys())},
            'missing':{n:before[n] for n in sorted(before.keys()-after.keys())},
            'modified':{n:{'before':before[n],'after':after[n]}
                        for n in sorted(before.keys() & after.keys()) if before[n] != after[n]}}


def cache_paths(files):
    prefix = '%systemdrive%/programdata/microsoft/windows/caches/'
    return sorted(n for n in files if n.lower().startswith(prefix) and n.lower().endswith('.db'))


def classify(rows):
    by_name = {row['arm']:row for row in rows}
    required = ('startup-control','startup-a','startup-b')
    if not all(n in by_name and by_name[n].get('exit_code') == 0 for n in required):
        return 'DIAGNOSTIC_PARTIAL_OR_NONREPRODUCING'
    a,b,control = (by_name[n] for n in ('startup-a','startup-b','startup-control'))
    found = cache_paths(a['created'])
    if (found and found == cache_paths(b['created']) and not cache_paths(control['created']) and
            len({by_name[n]['cwd'] for n in required}) == 3):
        return 'RELATIVE_CACHE_WRITE_REPEATED_IN_DISTINCT_STARTUP_CWDS'
    return 'DIAGNOSTIC_PARTIAL_OR_NONREPRODUCING'


def child(boundary,worker,scratch):
    """Driver in an owned child. Instrument stream retention only, not launch env/cwd."""
    scratch = ordinary_chain(scratch).resolve(strict=True)
    require(Path.cwd().resolve(strict=True) == scratch,'E_PROBE_CHILD_CWD')
    require(boundary in ('single','shard'),'E_PROBE_CHILD_BOUNDARY')
    temporary = outside_packages(scratch/'retained-streams',[ROOT/pkg for pkg in PACKAGES])
    temporary.mkdir(exist_ok=False)
    tempfile.tempdir = str(temporary)
    class RetainedDirectory:
        def __init__(self,*args,**kwargs):
            self.name = tempfile.mkdtemp(*args,**kwargs)
        def cleanup(self): pass
    def retained_file(*args,**kwargs):
        fd,_ = tempfile.mkstemp(dir=temporary,prefix='stream-')
        return os.fdopen(fd,'w+b')
    tempfile.TemporaryDirectory = RetainedDirectory
    tempfile.TemporaryFile = retained_file
    sys.path.insert(0,str(ROOT/'memory-integrity/scripts'))
    if boundary == 'single':
        from knowledge_bridge.worker_client import WorkerClient
        result = WorkerClient(worker,timeout=45)({'op':'handshake'})
        require(result.get('ok') is True,'E_PROBE_HANDSHAKE')
        print(json.dumps({'boundary':boundary,'handshake':result},ensure_ascii=True))
    else:
        from knowledge_bridge.distributed_retrieval import _Session
        session = _Session(worker,'cache-probe','scratch-only-no-grant',time.monotonic()+45)
        try:
            session.process.stdin.close() # EOF after actual runtime_identity(), no fit/query/model.
            end = time.monotonic()+45
            while session.process.poll() is None:
                require(time.monotonic() < end,'E_PROBE_SHARD_TIMEOUT')
                require(os.fstat(session.output.fileno()).st_size <= 65536 and
                        os.fstat(session.errors.fileno()).st_size <= 65536,'E_PROBE_SHARD_OUTPUT_LIMIT')
                time.sleep(.01)
            code = session.process.wait(timeout=5)
            require(code == 0,'E_PROBE_SHARD_STARTUP_EXIT: '+str(code))
            print(json.dumps({'boundary':boundary,'exit_code':code,'runtime_identity_before_eof':True}))
        finally:
            session.close()


def execute(prepared,expected,output):
    prepared = ordinary_chain(prepared)
    require(prepared.is_file() and prepared.stat().st_nlink == 1 and
            sha(prepared.read_bytes()) == expected,'E_PROBE_EXTERNAL_HASH')
    doc = read(prepared)
    verify_basis(doc) # Refuse before creating any output or consuming the scratch attempt.
    output = new_probe_output(output)
    receipt = {'scope':doc['scope'],'prepared':stream_record(prepared),'arms':[],
               'status':'DIAGNOSTIC_PARTIAL_OR_NONREPRODUCING','failure':None,
               'producer_authentication':False,'whole_skill_ready':False,'native_execution':False,
               'model_inference':False,'preservation_observed':False,
               'limitations':['No precise Windows DLL/cache-service writer attribution.',
                              'No full retrieval, host-a1 retry or repaired-product qualification.',
                              'Existing boundaries unchanged; only stream cleanup is instrumented.']}
    try:
        from offline_host_validation import capture_owned
        controller,worker = (doc[n]['path'] for n in ('controller','worker'))
        startup = 'import json,os,sys;print(json.dumps({"python":sys.version,"cwd":os.getcwd()}))'
        for name in ARM_NAMES:
            verify_basis(doc)
            root = output/name
            root.mkdir(exist_ok=False)
            cwd = root/'cwd'
            cwd.mkdir()
            temp = root/'temp'
            temp.mkdir()
            logs = root/'command'
            logs.mkdir()
            env = filtered_context(os.environ,temp)
            argv = ([controller if name == 'startup-control' else worker,'-B','-c',startup]
                    if name.startswith('startup-') else
                    [controller,'-B',str(Path(__file__).resolve()),'child','--boundary',name,
                     '--worker',worker,'--scratch',str(cwd)])
            completed,command = capture_owned(argv,logs,str(cwd),env,60)
            row = {'arm':name,'cwd':str(cwd),'created':inventory(cwd),
                   'temp_created':inventory(temp),'exit_code':completed.returncode if completed else None,
                   'command':command,'source_preservation':False}
            receipt['arms'].append(row)
            verify_basis(doc)
            row['source_preservation'] = True
            save(root/'Arm.json',row)
            require(completed is not None and completed.returncode == 0,
                    'E_PROBE_ARM_EXIT: '+name+'; inspect retained stderr/Command.json')
        receipt['status'] = classify(receipt['arms'])
    except Exception:
        receipt['failure'] = traceback.format_exc()
    finally:
        try:
            verify_basis(doc)
            receipt['preservation_observed'] = True
        except Exception:
            receipt['failure'] = (receipt['failure'] or '')+'\n'+traceback.format_exc()
        save(output/'Receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'receipt':str(output/'Receipt.json'),
                      'sha256':sha((output/'Receipt.json').read_bytes()),
                      'arms_observed':len(receipt['arms']),'failure':receipt['failure'],
                      'whole_skill_ready':False},ensure_ascii=True))
    return 0 if receipt['failure'] is None and receipt['preservation_observed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode',required=True)
    prepare = sub.add_parser('prepare')
    prepare.add_argument('--worker',required=True)
    prepare.add_argument('--output',type=Path,required=True)
    run = sub.add_parser('run')
    run.add_argument('--prepared',type=Path,required=True)
    run.add_argument('--sha256',required=True)
    run.add_argument('--output',type=Path,required=True)
    arm = sub.add_parser('child')
    arm.add_argument('--boundary',choices=('single','shard'),required=True)
    arm.add_argument('--worker',required=True)
    arm.add_argument('--scratch',type=Path,required=True)
    args = parser.parse_args()
    if args.mode == 'prepare':
        value = basis(args.worker)
        verify_basis(value)
        output = new_probe_output(args.output)
        save(output/'Prepared.json',value)
        print(json.dumps(stream_record(output/'Prepared.json')))
    elif args.mode == 'run':
        return execute(args.prepared,args.sha256,args.output)
    else:
        child(args.boundary,args.worker,args.scratch)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
