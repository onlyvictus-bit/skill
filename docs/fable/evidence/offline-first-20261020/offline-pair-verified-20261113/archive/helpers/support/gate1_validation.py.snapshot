#!/usr/bin/env python3
"""One new exact-source offline Gate1 validation; never retries a historical run.

Receipts are retained, self-reported observations, not authenticated provenance.
This driver never installs, edits Git configuration, or enables native features.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import traceback
import zipfile

HEAD = '923de16c91a9ef4381e7ac975e3a3780f42a4bf5'
REPO = Path(r'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\source-git')
WORKSPACE = Path(r'C:\Users\sakth\Documents\Codex\gate1-923de16-20261021')
CONTROLLER = Path(r'C:\Python314\python.exe')
CONTROLLER_SHA = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
WORKER = REPO.parent/'build-validation/n3-retrieval-9ec6fb1db36444acba2945896e8b8d17/venv/Scripts/python.exe'
ALIAS = Path(r'C:\Users\sakth\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe')
GIT = Path(r'C:\Program Files\Git\cmd\git.exe')
GIT_SHA = 'da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f'
OVERLAY = 'memory-integrity/tests_v2/test_knowledge_worker_cwd.py'
OVERLAY_OLD = 'dad936ff27c4ce20bc9ddaec92d32989e93a44f5c4fada3f92cab520ba3f130b'
OVERLAY_NEW = '393855d5236ff5620af3f0ff478f79bcbf497c535d104af7140b3fe8bcf864eb'
SOURCE_MAP_SHA = 'ec08edc910c890bbd2b34844740aabe4e0cd6efa41d2d42efb2794442b468e66'
PROTECTED_MAP_SHA = 'd3a74e667d5e3965b5af8a40904e454def6ea896087d2d29f8564a2052661bf8'
HISTORY_MAP_SHA = '7d6f3f98ec985d2ac9bee62e1835b06f3c0975c4f9e635b65f9d9beebbef707f'
TEST_IDS_SHA = '9c458b3f06fe3452e0431d06c0f4318a40343f9de8def34d9b2396f75b8bae02'
BASE = Path(r'C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0\python.exe')
BASE_SHA = '5365b422ee178f691988eb937b7abca5f48910b148f76fcce6dbaf5585c948d0'
WORKER_SHA = '0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14'
CONFIG_SHA = '79d3400be0f231ad6f2f5cf51f227c8ce4591ad18656e38865f3d00564f8aa6a'
SID = 'S-1-5-21-2571509308-2482563067-4170768140-1001'
SCOPE = 'GATE1_CLEAN_SOURCE_SELECTED_RUNTIME_ONLY'
PATTERNS = [('memory-integrity', p) for p in (
    'test_native_containment.py', 'test_native_paths.py',
    'test_offline_release_profile.py', 'test_knowledge*.py')]
PATTERNS += [('claude-mon', 'test_offline_release_profile.py')]


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ordinary(path):
    path = Path(path)
    require(path.is_absolute(), 'E_G1_ABSOLUTE_PATH')
    for item in reversed((path, *path.parents)):
        info = item.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not
                getattr(info, 'st_file_attributes', 0) & 0x400, 'E_G1_REDIRECT: '+str(item))
    return path


def file_record(path):
    path = ordinary(Path(path))
    info = path.stat()
    require(path.is_file() and info.st_nlink == 1, 'E_G1_EVIDENCE_LINK')
    raw = path.read_bytes()
    def identity(value):
        # Reading a retained file may legitimately update NTFS access time.
        # Identity, type, links, byte size and modification time must not move.
        return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
                value.st_size, value.st_mtime_ns, value.st_ctime_ns)
    require(identity(ordinary(path).stat()) == identity(info), 'E_G1_READ_CHANGED')
    return {'path': str(path), 'size': len(raw), 'sha256': sha(raw)}


def inventory(root):
    root = ordinary(Path(root)).resolve(strict=True)
    result = {}
    def failed(error):
        raise error
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=failed):
        for name in dirs + files:
            entry = ordinary(Path(parent)/name)
            if entry.is_file():
                result[entry.relative_to(root).as_posix()] = file_record(entry)['sha256']
    return dict(sorted(result.items()))


def verify_manifest(root, manifest):
    require(inventory(root) == manifest, 'E_G1_CONTENT_CHANGED: '+str(root))


def load_sealed(path, digest):
    record = file_record(Path(path))
    require(record['sha256'] == digest, 'E_G1_EXTERNAL_SEAL: '+str(path))
    raw = Path(path).read_bytes()
    require(sha(raw) == digest, 'E_G1_EXTERNAL_SEAL')
    return json.loads(raw.decode('utf-8'))


def save(path, value):
    with Path(path).open('xb') as stream:
        stream.write((json.dumps(value, sort_keys=True, ensure_ascii=True)+'\n').encode('utf-8'))


def new_workspace(path, protected_roots):
    path = Path(path)
    require(path.is_absolute() and not path.exists(), 'E_G1_OUTPUT_EXISTS')
    parent = ordinary(path.parent).resolve(strict=True)
    target = parent/path.name
    for root in protected_roots:
        root = ordinary(Path(root)).resolve(strict=True)
        require(not target.is_relative_to(root) and not root.is_relative_to(target),
                'E_G1_OUTPUT_PROTECTED')
    path.mkdir()
    ordinary(path)
    return path


def validate_outcomes(row, expected_ids, allowed_skips):
    expected = set(expected_ids)
    require(expected and len(expected) == len(expected_ids) and
            set(row) == {'started', 'finished'}, 'E_G1_CASE_SET')
    started, finished = row['started'], row['finished']
    require(len(started) == len(expected) and set(started) == expected and
            len(finished) == len(expected) and {r['id'] for r in finished} == expected,
            'E_G1_CASE_SET')
    for result in finished:
        require(set(result) == {'id', 'outcome', 'reason'}, 'E_G1_CASE_SET')
        if result['outcome'] == 'SKIP':
            require(result['id'] in allowed_skips and
                    allowed_skips[result['id']] in result['reason'], 'E_G1_SKIP: '+str(result))
        else:
            require(result['outcome'] == 'PASS', 'E_G1_TEST_FAILED: '+str(result))


PREPARED_KEYS = {'schema_version', 'scope', 'head', 'repo', 'workspace', 'source',
                 'source_manifest', 'overlay', 'protected', 'historical', 'runtime',
                 'source_manifest_record', 'helpers', 'patterns', 'test_ids',
                 'release_ready', 'native_execution', 'installed'}


def map_digest(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=True).encode('utf-8'))


def validate_prepared(value):
    require(isinstance(value, dict) and set(value) == PREPARED_KEYS and
            value['schema_version'] == 1 and value['scope'] == SCOPE and value['head'] == HEAD and
            all(value[k] is False for k in ('release_ready', 'native_execution', 'installed')) and
            value['patterns'] == [list(pair) for pair in PATTERNS] and
            all(isinstance(value[k], str) and Path(value[k]).is_absolute() for k in ('repo', 'workspace', 'source')),
            'E_G1_SCHEMA')
    try:
        require(value['repo'] == str(REPO) and value['workspace'] == str(WORKSPACE) and
                value['source'] == str(WORKSPACE/'source') and
                value['overlay'] == {'path': OVERLAY, 'old_sha256': OVERLAY_OLD, 'new_sha256': OVERLAY_NEW},
                'E_G1_SCHEMA')
        require(len(value['source_manifest']) == 567 and map_digest(value['source_manifest']) == SOURCE_MAP_SHA and
                map_digest(value['protected']) == PROTECTED_MAP_SHA and
                map_digest(value['historical']) == HISTORY_MAP_SHA and
                map_digest(value['test_ids']) == TEST_IDS_SHA, 'E_G1_SCHEMA')
        require(set(value['protected']) == {str(REPO/name) for name in ('memory-integrity', 'claude-mon', '%SystemDrive%')} and
                set(value['test_ids']) == {str(i) for i in range(len(PATTERNS))} and
                all(isinstance(ids, list) and ids and len(set(ids)) == len(ids)
                    for ids in value['test_ids'].values()), 'E_G1_SCHEMA')
        expected_runtime = {'controller': (CONTROLLER, CONTROLLER_SHA), 'worker': (WORKER, WORKER_SHA),
                            'config': (WORKER.parent.parent/'pyvenv.cfg', CONFIG_SHA), 'base': (BASE, BASE_SHA)}
        require(set(value['runtime']) == set(expected_runtime), 'E_G1_SCHEMA')
        for key, (path, digest) in expected_runtime.items():
            require(value['runtime'][key] == file_record(path) and value['runtime'][key]['sha256'] == digest,
                    'E_G1_SCHEMA')
        names = {'gate1_validation.py', 'gate1_runner.py', 'gate1_worker_checks.py'}
        require(set(value['helpers']) == names and all(
            value['helpers'][name] == file_record(REPO/'.github/scripts'/name) for name in names), 'E_G1_SCHEMA')
        raw = (json.dumps(value['source_manifest'], sort_keys=True, ensure_ascii=True)+'\n').encode('utf-8')
        require(value['source_manifest_record'] == {'path': str(WORKSPACE/'Source-Manifest.json'),
                'size': len(raw), 'sha256': sha(raw)}, 'E_G1_SCHEMA')
    except (KeyError, TypeError, OSError) as error:
        raise ValueError('E_G1_SCHEMA') from error


def sibling_module(name, directory):
    # New modules are loaded only after the external launcher checks their hashes.
    spec = importlib.util.spec_from_file_location(name, Path(directory)/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_acceptance(value):
    require(value.get('status') == 'PASS_BOUNDED_RUNTIME' and
            value.get('scope') == 'RANKED_RUNTIME', 'E_G1_ACCEPTANCE')
    source = Path(value['package_roots']['mi']).parent
    acceptance = sibling_module('offline_release_acceptance', source/'.github/scripts')
    acceptance.validate_receipt(value)
    for row in value['measurements']:
        if row['mode'] in ('lexical', 'lsa'):
            require(row['ranked_results'] and
                    set(row['expected_sources']) & set(row['delivered_sources']), 'E_G1_RANKED_EMPTY')


def runtime_probe():
    # Read the CURRENT process image, not a guessed target for an AppExecAlias.
    # Canonicalize the opened image's handle and retain its on-disk file hash.
    # This is identity consistency, not authentication of the producer or RAM.
    return r'''
import ctypes,ctypes.wintypes as w,hashlib,json,os,sys
from pathlib import Path
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.GetModuleFileNameW.argtypes=[w.HMODULE,w.LPWSTR,w.DWORD]
k.GetModuleFileNameW.restype=w.DWORD
k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
k.CreateFileW.restype=w.HANDLE
k.GetFinalPathNameByHandleW.argtypes=[w.HANDLE,w.LPWSTR,w.DWORD,w.DWORD]
k.GetFinalPathNameByHandleW.restype=w.DWORD
k.CloseHandle.argtypes=[w.HANDLE]
b=ctypes.create_unicode_buffer(32768)
n=k.GetModuleFileNameW(None,b,len(b))
if not 0<n<len(b):raise ctypes.WinError(ctypes.get_last_error())
h=k.CreateFileW(b.value,0x80,7,None,3,0,None)
if h in (None,ctypes.c_void_p(-1).value):raise ctypes.WinError(ctypes.get_last_error())
try:
 n=k.GetFinalPathNameByHandleW(h,b,len(b),0)
 if not 0<n<len(b):raise ctypes.WinError(ctypes.get_last_error())
 image=b.value
finally:k.CloseHandle(h)
if image.startswith('\\\\?\\'):image=image[4:]
print(json.dumps(dict(version=list(sys.version_info[:3]),executable=sys.executable,
 base_executable=sys._base_executable,prefix=sys.prefix,base_prefix=sys.base_prefix,
 image_path=image,image_sha256=hashlib.sha256(Path(image).read_bytes()).hexdigest(),cwd=os.getcwd(),
 environment={name:os.environ.get(name) for name in ('USERPROFILE','TEMP','TMP','SYSTEMROOT','SystemDrive','PYTHONNOUSERSITE')},
 path_sha256=hashlib.sha256(os.environ.get('PATH','').encode()).hexdigest(),
 model_selected=bool(os.environ.get('MODEL_PYTHON') or os.environ.get('KNOWLEDGE_MODEL_MANIFEST')))))
'''


def validate_runtime_observation(observed, env, cwd):
    require(set(observed) == {'version', 'executable', 'base_executable', 'prefix', 'base_prefix',
            'image_path', 'image_sha256', 'cwd', 'environment', 'path_sha256', 'model_selected'} and
            observed['version'] == [3, 12, 10] and
            Path(observed['executable']) == WORKER and Path(observed['base_executable']) == ALIAS and
            Path(observed['prefix']) == WORKER.parent.parent and Path(observed['base_prefix']) == BASE.parent and
            Path(observed['image_path']) == BASE and observed['image_sha256'] == BASE_SHA and
            Path(observed['cwd']) == Path(cwd) and observed['model_selected'] is False and
            observed['environment'] == {name: env.get(name) for name in
                ('USERPROFILE', 'TEMP', 'TMP', 'SYSTEMROOT', 'SystemDrive', 'PYTHONNOUSERSITE')} and
            observed['path_sha256'] == sha(env.get('PATH', '').encode()), 'E_G1_RUNTIME_OBSERVATION')


def git(repo, *args):
    # Pin the existing Git launcher (two system hardlink names are expected).
    require(sha(GIT.read_bytes()) == GIT_SHA and GIT.stat().st_nlink == 2, 'E_G1_GIT_IDENTITY')
    return subprocess.run([str(GIT), '--no-optional-locks', '-c', 'core.fsmonitor=false',
                           '-c', 'core.untrackedCache=false', '-C', str(repo), *args],
                          capture_output=True, check=True).stdout


def check_preserved(doc):
    verify_manifest(Path(doc['source']), doc['source_manifest'])
    require(file_record(Path(doc['source_manifest_record']['path'])) == doc['source_manifest_record'], 'E_G1_SOURCE_MANIFEST_CHANGED')
    for name, expected in doc['protected'].items():
        verify_manifest(Path(name), expected)
    for name, digest in doc['historical'].items():
        require(file_record(Path(name))['sha256'] == digest, 'E_G1_HISTORY_CHANGED: '+name)
    for row in doc['helpers'].values():
        require(file_record(Path(row['path'])) == row, 'E_G1_HELPER_CHANGED')
    for row in doc['runtime'].values():
        require(file_record(Path(row['path'])) == row, 'E_G1_RUNTIME_CHANGED')
    require(git(Path(doc['repo']), 'rev-parse', 'HEAD').decode().strip() == HEAD, 'E_G1_HEAD_CHANGED')


def historical(repo):
    scripts = repo/'.github/scripts'
    sys.path.insert(0, str(scripts))
    probe = sibling_module('cache_cause_probe', scripts)
    rows = probe.required_historical()
    root = repo/'.github/run-artifacts/offline-first-20261020/cache-cause-a9ae630-20261020-v2'
    receipt = root/'normal-attempt/Receipt.json'
    require(file_record(receipt)['sha256'] ==
            'a1a37f4a1128bc2d5be42bd2a11ac758e844e3a4746630e32f2add2e1141f6dc', 'E_G1_CACHE_RECEIPT')
    value = json.loads(receipt.read_text(encoding='utf-8'))
    rows[str(receipt)] = file_record(receipt)['sha256']
    rows[value['prepared']['path']] = value['prepared']['sha256']
    for arm in value['arms']:
        for entry in ('stdout', 'stderr'):
            stream = arm['command'][entry]
            rows[stream['path']] = stream['sha256']
        # Expected hashes come from the unchanged retained receipt. Inaccessible
        # paths must pass on the normal host; they are never silently omitted.
        for relative, digest in arm['created'].items():
            rows[str(Path(arm['cwd'])/relative)] = digest
    return rows


def prepare(args):
    repo, workspace, worker = map(Path, (args.repo, args.workspace, args.worker))
    require(repo == REPO and workspace == WORKSPACE and worker == WORKER, 'E_G1_SCHEMA')
    require(sha((repo/OVERLAY).read_bytes()) == OVERLAY_NEW, 'E_G1_OVERLAY_DRIFT')
    require(git(repo, 'rev-parse', 'HEAD').decode().strip() == HEAD, 'E_G1_HEAD_CHANGED')
    runtime = {key: file_record(path) for key, path in (
        ('controller', Path(sys.executable)), ('worker', worker),
        ('config', worker.parent.parent/'pyvenv.cfg'), ('base', BASE))}
    require(runtime['worker']['sha256'] == WORKER_SHA and runtime['config']['sha256'] == CONFIG_SHA and
            runtime['base']['sha256'] == BASE_SHA, 'E_G1_RUNTIME_CHANGED')
    protected = {str(repo/name): inventory(repo/name) for name in ('memory-integrity', 'claude-mon', '%SystemDrive%')}
    prior = historical(repo)
    require(map_digest(protected) == PROTECTED_MAP_SHA and map_digest(prior) == HISTORY_MAP_SHA, 'E_G1_PROTECTION_BASIS_CHANGED')
    for name, digest in prior.items():
        # Fail any readable mismatch now. Access errors remain explicit and
        # mandatory normal-host checks, never evidence that a file is unchanged.
        try:
            require(file_record(Path(name))['sha256'] == digest, 'E_G1_HISTORY_CHANGED')
        except PermissionError:
            print('NORMAL_HOST_READ_REQUIRED: '+name)
    new_workspace(workspace, [repo])
    source = workspace/'source';source.mkdir()
    archive = git(repo, 'archive', '--format=zip', HEAD)
    tree = {}
    for row in git(repo, 'ls-tree', '-rz', HEAD).split(b'\0'):
        if row:
            metadata, name = row.split(b'\t', 1)
            mode, kind, digest = metadata.split()
            require(mode == b'100644' and kind == b'blob', 'E_G1_SOURCE_MODE')
            tree[name.decode('utf-8')] = digest.decode('ascii')
    members = zipfile.ZipFile(io.BytesIO(archive))
    folded = set()
    for item in members.infolist():
        relative = Path(item.filename)
        require(not relative.is_absolute() and '..' not in relative.parts and '\\' not in item.filename and
                ':' not in item.filename and not stat.S_ISLNK(item.external_attr >> 16), 'E_G1_ARCHIVE_PATH')
        if item.is_dir():
            continue
        require(item.filename.casefold() not in folded, 'E_G1_ARCHIVE_COLLISION')
        folded.add(item.filename.casefold())
        raw = members.read(item)
        require(item.filename in tree and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
                == tree[item.filename], 'E_G1_GIT_BLOB')
        target = source/relative;target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
    before = inventory(source)
    require(set(before) == set(tree), 'E_G1_GIT_TREE')
    require(before[OVERLAY] == OVERLAY_OLD, 'E_G1_OVERLAY_BASIS')
    replacement = (repo/OVERLAY).read_bytes()
    require(sha(replacement) == OVERLAY_NEW, 'E_G1_OVERLAY_DRIFT')
    # Only this newly extracted test fixture is replaced; never original source.
    with (source/OVERLAY).open('wb') as stream:
        stream.write(replacement)
    helpers = {name: file_record(Path(__file__).parent/name) for name in
               ('gate1_validation.py', 'gate1_runner.py', 'gate1_worker_checks.py')}
    test_ids = {}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', KNOWLEDGE_WORKER_PYTHON=str(worker))
    for name in ('MODEL_PYTHON', 'KNOWLEDGE_MODEL_MANIFEST'):
        env.pop(name, None)
    for number, (package, pattern) in enumerate(PATTERNS):
        command = [sys.executable, '-B', helpers['gate1_runner.py']['path'], '--discover',
                   '--package-root', str(source/package), '--pattern', pattern]
        observed = subprocess.run(command, cwd=workspace, env=env, capture_output=True, timeout=60)
        save(workspace/('Discovery-'+str(number)+'.json'), {
            'argv': command, 'exit_code': observed.returncode,
            'stdout': observed.stdout.decode('utf-8', errors='backslashreplace'),
            'stderr': observed.stderr.decode('utf-8', errors='backslashreplace')})
        require(observed.returncode == 0, 'E_G1_DISCOVERY')
        ids = json.loads(observed.stdout.decode('utf-8'))
        require(ids and len(ids) == len(set(ids)) and not any('_FailedTest' in name for name in ids), 'E_G1_DISCOVERY')
        test_ids[str(number)] = ids
    manifest = inventory(source)
    require(map_digest(manifest) == SOURCE_MAP_SHA and map_digest(test_ids) == TEST_IDS_SHA, 'E_G1_FROZEN_BASIS_CHANGED')
    save(workspace/'Source-Manifest.json', manifest)
    doc = {'schema_version': 1, 'scope': SCOPE, 'head': HEAD, 'repo': str(repo),
           'workspace': str(workspace), 'source': str(source), 'source_manifest': inventory(source),
           'source_manifest_record': file_record(workspace/'Source-Manifest.json'),
           'overlay': {'path': OVERLAY, 'old_sha256': OVERLAY_OLD, 'new_sha256': sha(replacement)},
           'protected': protected, 'historical': prior, 'runtime': runtime, 'helpers': helpers,
           'patterns': [list(pair) for pair in PATTERNS],
           'test_ids': test_ids,
           'release_ready': False, 'native_execution': False, 'installed': False}
    validate_prepared(doc)
    save(workspace/'Prepared.json', doc)
    print(json.dumps({'status': 'GATE1_INPUTS_PREPARED_NOT_EXECUTED',
                      'prepared': file_record(workspace/'Prepared.json'), 'runtime_started': False}))


def run(args):
    doc = load_sealed(Path(args.prepared), args.sha256)
    validate_prepared(doc)
    source, workspace = Path(doc['source']), Path(doc['workspace'])
    check_preserved(doc)
    sys.path.insert(0, str(source/'.github/scripts'))
    host = sibling_module('offline_host_validation', source/'.github/scripts')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               KNOWLEDGE_WORKER_PYTHON=doc['runtime']['worker']['path'])
    for name in ('MODEL_PYTHON', 'KNOWLEDGE_MODEL_MANIFEST'):
        env.pop(name, None)
    # Full inherited USERPROFILE is needed for the EXISTING Git configuration.
    # No safe.directory or other configuration is injected or changed.
    require(env.get('USERPROFILE') == r'C:\Users\sakth', 'E_G1_NORMAL_ACCOUNT_CONTEXT')
    output = new_workspace(workspace/'normal-attempt', [source, Path(doc['repo'])])
    temp = output/'temp';temp.mkdir()
    env.update(TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    commands, suites = [], []
    receipt = {'schema_version': 1, 'scope': SCOPE, 'status': 'PARTIAL_OR_FAILED_NO_RETRY',
               'prepared': file_record(Path(args.prepared)), 'commands': commands, 'suites': suites,
               'failure': None, 'preservation': False, 'producer_authentication': False,
               'release_ready': False, 'whole_skill_ready': False, 'native_execution': False,
               'installed': False, 'inference_sent': False}
    def capture(label, argv, timeout=1200):
        target = output/label;target.mkdir()
        completed, record = host.capture_owned(list(map(str, argv)), target, output, env, timeout)
        commands.append(dict(record, label=label))
        require(completed is not None and completed.returncode == 0,
                'E_G1_CHILD_FAILED: '+label+' (read retained stderr before JSON)')
        check_preserved(doc)
        return target
    try:
        capture('preclaim-git', [GIT, '--no-optional-locks', '-C', doc['repo'], 'rev-parse', 'HEAD'], 30)
        identity = capture('preclaim-runtime', [doc['runtime']['worker']['path'], '-B', '-c', runtime_probe()], 60)
        observed = json.loads((identity/'stdout.log').read_text(encoding='utf-8'))
        validate_runtime_observation(observed, env, output)
        save(output/'evaluation-claim.json', {'prepared_sha256': args.sha256, 'scope': SCOPE})
        capture('real-worker-cleanup', [sys.executable, '-B', doc['helpers']['gate1_worker_checks.py']['path'],
                    '--source', source, '--worker', doc['runtime']['worker']['path'], '--output', output/'cleanup'])
        cleanup = json.loads((output/'cleanup/Receipt.json').read_text(encoding='utf-8'))
        require(cleanup.get('status') == 'PASS_REAL_WORKER_CWD_AND_CLEANUP' and
                cleanup.get('boundaries') == ['single', 'shard'] and cleanup.get('all_reaped') is True,
                'E_G1_CLEANUP')
        receipt['cleanup'] = file_record(output/'cleanup/Receipt.json')
        for number, (package, pattern) in enumerate(PATTERNS):
            target = capture('suite-'+str(number), [sys.executable, '-B', doc['helpers']['gate1_runner.py']['path'],
                             '--package-root', source/package, '--pattern', pattern,
                             '--output-dir', output/('tests-'+str(number))])
            report = json.loads((output/('tests-'+str(number))/'Case-Outcomes.json').read_text(encoding='utf-8'))
            runner = sibling_module('gate1_runner', Path(__file__).parent)
            require(report['expected_ids'] == doc['test_ids'][str(number)], 'E_G1_DISCOVERY_CHANGED')
            validate_outcomes(report['outcomes'], doc['test_ids'][str(number)], runner.allowed_skips())
            suites.append({'package': package, 'pattern': pattern, 'report': file_record(output/('tests-'+str(number))/'Case-Outcomes.json')})
        capture('coding-acceptance', [sys.executable, '-B', source/'.github/scripts/offline_release_acceptance.py',
                    '--package-root', source/'memory-integrity', '--claude-mon-root', source/'claude-mon',
                    '--worker-python', doc['runtime']['worker']['path'], '--output-dir', output/'acceptance'], 2400)
        acceptance = json.loads((output/'acceptance/Receipt.json').read_text(encoding='utf-8'))
        validate_acceptance(acceptance)
        receipt['acceptance'] = file_record(output/'acceptance/Receipt.json')
        receipt['status'] = 'GATE1_RUNTIME_OBSERVED_PENDING_RESULT_REVIEW'
    except BaseException:
        receipt['failure'] = traceback.format_exc()
    finally:
        try:
            check_preserved(doc)
            receipt['preservation'] = True
        except BaseException:
            receipt['preservation_failure'] = traceback.format_exc()
            receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
        save(output/'Receipt.json', receipt)
    print(json.dumps({'status': receipt['status'], 'receipt': file_record(output/'Receipt.json'),
                      'failure': receipt['failure'], 'whole_skill_ready': False}))
    return 0 if receipt['status'] == 'GATE1_RUNTIME_OBSERVED_PENDING_RESULT_REVIEW' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('prepare')
    for option in ('repo', 'workspace', 'worker'):
        p.add_argument('--'+option, required=True)
    p = sub.add_parser('run');p.add_argument('--prepared', required=True);p.add_argument('--sha256', required=True)
    args = parser.parse_args()
    sys.exit(run(args) if args.mode == 'run' else prepare(args))
