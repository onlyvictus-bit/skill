"""Read-only Fable startup adapter; existing skills own protected run verification.

Hashes establish file identity, not author authenticity or semantic truth.
A filesystem owner can replace both sources and basis. No memory service is used.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
import subprocess
import sys


def readonly_audit(event, args):
    """Verification-process guard; this is not an OS sandbox for descendants."""
    if event=='open':
        mode,flags=args[1:3]
        if ((isinstance(mode,str) and any(c in mode for c in 'wax+')) or
            (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))):
            raise PermissionError('E_PROJECT_RESUME_READONLY_OPEN')
    if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.chmod','os.chown',
                 'os.truncate','os.link','os.symlink','socket.connect','socket.bind'):
        raise PermissionError('E_PROJECT_RESUME_READONLY_EFFECT: '+event)


def need(value, code):
    if not value: raise ValueError('E_PROJECT_RESUME_'+code)


def read_json(raw):
    def pairs(rows):
        result={}
        for key,value in rows:
            need(key not in result,'DUPLICATE_JSON');result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs)


def checked_file(root, name):
    need(type(name) is str and bool(name) and '\\' not in name and ':' not in name
         and not PurePosixPath(name).is_absolute() and not PureWindowsPath(name).is_absolute()
         and all(p not in ('','.','..') for p in name.split('/')), 'PATH')
    target=root.joinpath(*name.split('/'))
    for part in (target,*target.parents):
        try: info=part.lstat()
        except FileNotFoundError: raise ValueError('E_PROJECT_RESUME_MISSING: '+name)
        need(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'REDIRECT')
        if part==root: break
    need(target.is_file() and target.stat().st_nlink==1,'FILE_TYPE')
    return target


def check_basis(root):
    root=Path(root).absolute()
    need(not root.is_symlink() and not getattr(root,'is_junction',lambda:False)(),'REDIRECT')
    basis=read_json(checked_file(root,'docs/fable/continuity/Basis.json').read_bytes())
    need(isinstance(basis,dict) and basis.get('schema_version')==1
         and type(basis.get('project_id')) is str and bool(basis['project_id'])
         and isinstance(basis.get('files'),dict) and bool(basis['files']), 'SCOPE')
    for name,digest in basis['files'].items():
        actual=hashlib.sha256(checked_file(root,name).read_bytes()).hexdigest()
        need(actual==digest,'STALE: '+name)
    return basis


def resume(root, memory_root=None, companion_root=None):
    root=Path(root).absolute();basis=check_basis(root)
    initial=checked_file(root,'docs/fable/continuity/Basis.json').read_bytes()
    need(memory_root is not None and companion_root is not None,'EXPLICIT_SKILL_ROOTS')
    def skills():
        need(set(basis.get('skills',{}))=={'memory-integrity','claude-mon'},'SKILL_BINDINGS')
        for name,path in (('memory-integrity',memory_root),('claude-mon',companion_root)):
            row=basis['skills'][name];path=Path(path).absolute()
            need(str(path)==row['root'] and not path.is_symlink()
                 and not getattr(path,'is_junction',lambda:False)(),'SKILL_ROOT')
            actual={p.relative_to(path).as_posix() for p in path.rglob('*')
                    if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo')}
            need(actual==set(row['files']),'SKILL_FILES')
            for name,digest in row['files'].items():
                need(hashlib.sha256(checked_file(path,name).read_bytes()).hexdigest()==digest,'SKILL_STALE')
    skills()
    for key in ('source','run_map'):
        need(basis.get(key) in basis['files'],'BOUND_RUN')
    # The existing engine probe writes temporary copies of bytes already saved
    # in the protected run. Keep its SAME partition rules, but call them in this
    # isolated process so startup can verify without filesystem write access.
    bootstrap = '''import sys,runpy
from pathlib import Path
memory,engine,workflow,guard_path=sys.argv[1:5]
sys.argv=[workflow]+sys.argv[5:]
sys.dont_write_bytecode=True
guard=runpy.run_path(guard_path,run_name='project_resume_guard')['readonly_audit']
sys.addaudithook(guard)
sys.path[:0]=[str(Path(memory)/'scripts'),str(Path(engine)/'scripts')]
from integrity_v2 import source_audit
from complete_read_v2 import partition
assert Path(partition.__file__).resolve().parent.parent==Path(engine).resolve()/'scripts'
def readonly_partition(selected,raw,manifest):
    assert Path(selected).resolve()==Path(engine).resolve()
    return partition.validate_manifest(raw,manifest)
source_audit.validate_with_engine=readonly_partition
runpy.run_path(workflow,run_name='__main__')
'''
    process=subprocess.run([sys.executable,'-B','-c',bootstrap,str(memory_root),str(companion_root),
        str(Path(memory_root)/'scripts/memory_integrity_workflow.py'),str(Path(__file__).absolute()),
        'verify','--claude-mon-root',str(companion_root),
        '--source',str(checked_file(root,basis['source'])),
        '--run-map',str(checked_file(root,basis['run_map'])),'--query','every'],
        capture_output=True,text=True,encoding='utf-8',timeout=60)
    need(process.returncode==0,'WORKFLOW_FAILED: '+process.stdout+process.stderr)
    result=read_json(process.stdout)
    expected=basis.get('expected_units');counts=result.get('counts',{});recall=result.get('recall',{})
    need(result.get('ok') is True and result.get('overall')=='VERIFIED_OFFLINE'
         and result.get('evidence_class')=='TEST_ONLY' and type(expected) is int and expected>0
         and counts.get('units')==counts.get('accepted_results')==expected
         and recall.get('mode')=='exhaustive' and len(recall.get('records',[]))==expected
         and recall.get('coverage_basis',{}).get('units')==expected
         and recall.get('coverage_basis',{}).get('source_digest')==basis['files'][basis['source']],
         'WORKFLOW_REFUSED')
    need(check_basis(root)==basis and checked_file(root,'docs/fable/continuity/Basis.json').read_bytes()==initial,
         'BASIS_CHANGED_DURING_VERIFY')
    skills()
    return {'status':'VERIFIED_PROJECT_FILE_RECOVERY','project_id':basis['project_id'],
        'source_basis_files':len(basis['files']),'workflow':result,
        'memory_service_persistence':'UNVERIFIED','semantic_truth':'UNVERIFIED',
        'recovery_channel':'project_files','automatic_global_recall':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,required=True)
    parser.add_argument('--memory-root',type=Path)
    parser.add_argument('--companion-root',type=Path)
    parser.add_argument('--basis-only',action='store_true')
    args=parser.parse_args()
    try:
        if args.basis_only:
            b=check_basis(args.project_root)
            value={'status':'SOURCE_BASIS_VERIFIED','project_id':b['project_id']}
        else: value=resume(args.project_root,args.memory_root,args.companion_root)
        print(json.dumps(value,ensure_ascii=False));raise SystemExit(0)
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        print(json.dumps({'status':'BLOCKED','error':str(error)},ensure_ascii=False));raise SystemExit(1)
