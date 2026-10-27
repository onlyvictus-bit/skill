"""Current a38297d Gate1 step1 only; old sealed attempts are never executed.

No retrieval, package install, Git write, deletion or qualification activation.
Receipts are retained observations, not authenticated producer attestations.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import traceback
import zipfile

REPO = Path(__file__).absolute().parents[2]
HEAD = 'a38297dd797eeecd25e41ab0af1df4e3db8fa984'
REVISION = '320761de5d040a54a3220acc563223b4a7ffdc51'
OUTPUT = Path(r'C:\Users\sakth\Documents\Codex\gate1-current-a38297d-20261023-c1')
CONTRACT = REPO/'.github/run-artifacts/gate1-current-20261023/C1-Contract.json'
PREFLIGHT_FAILURE = CONTRACT.with_name('C1-Preflight-Failure.json')
SUPPORT = {
    'gate1_validation': 'f9b7ef54039756b3d8a95051b05a93e920518c970e6deb1c987bc5bb0aeed22e',
    'gate1_image_successor': 'b1ef45b105f5d1b79bf25c4953dc2e6544ddfe994026e354313e30ddbf8df3af',
    'offline_host_validation': '1333833623bdc1f5a6f31230b530b121c40bbb3d6c244dccc695022082e33b9f',
    'offline_release_acceptance': '297239367be35ff0f920a4c2dbaeb2e8af0333a5c1e236f8e009c7c577911fcd',
}


def require(value, message):
    if not value: raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ordinary(path):
    path = Path(path)
    require(path.is_absolute(), 'E_CURRENT_ABSOLUTE')
    for part in reversed((path, *path.parents)):
        info = part.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not
                getattr(info, 'st_file_attributes', 0) & 0x400, 'E_CURRENT_REDIRECT: '+str(part))
    return path


def read_file(path, links=1):
    path = ordinary(Path(path)); before = path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == links, 'E_CURRENT_FILE_LINK: '+str(path))
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino), 'E_CURRENT_REPLACED')
        raw = stream.read()
        end = os.fstat(stream.fileno())
    after = ordinary(path).stat()
    # Windows stat() and CRT-backed fstat() can expose different ctime roles.
    # Compare ctime within each API, never equate birth time with change time.
    # Filename-based stat also synthesizes executable bits that fstat omits.
    identity = lambda s: (s.st_dev, s.st_ino, stat.S_IFMT(s.st_mode), s.st_nlink, s.st_size, s.st_mtime_ns)
    require(identity(before) == identity(opened) == identity(end) == identity(after) and
            (before.st_mode, before.st_ctime_ns) == (after.st_mode, after.st_ctime_ns) and
            (opened.st_mode, opened.st_ctime_ns) == (end.st_mode, end.st_ctime_ns),
            'E_CURRENT_READ_CHANGED')
    return raw


def record(path, links=1):
    raw = read_file(path, links)
    return {'path': str(path), 'size': len(raw), 'sha256': sha(raw), 'links': links}


def save(path, value):
    ordinary(Path(path).parent)
    with Path(path).open('xb') as stream:
        stream.write((json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)+'\n').encode())


def load_support(name):
    for role, expected in SUPPORT.items():
        require(sha(read_file(REPO/'.github/scripts'/(role+'.py'))) == expected, 'E_CURRENT_SUPPORT: '+role)
    path = REPO/'.github/scripts'/(name+'.py')
    require(name in SUPPORT, 'E_CURRENT_SUPPORT_ROLE')
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def git(*args):
    g = load_support('gate1_validation')
    require(sha(read_file(g.GIT, 2)) == g.GIT_SHA, 'E_CURRENT_GIT')
    result = subprocess.run([str(g.GIT), '--no-optional-locks', '-c', 'core.fsmonitor=false',
        '-c', 'core.untrackedCache=false', '-C', str(REPO), *args],
        capture_output=True, timeout=30, check=False)
    require(result.returncode == 0, 'E_CURRENT_GIT_FAILED: '+result.stderr.decode('utf-8', 'backslashreplace')[:2000])
    return result.stdout


def safe_name(name):
    path = PurePosixPath(name)
    require(isinstance(name, str) and name and not path.is_absolute() and
            '\\' not in name and ':' not in name and str(path) == name and
            all(part not in ('.', '..') and not part.endswith((' ', '.')) and
                not re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part)
                for part in path.parts), 'E_CURRENT_ARCHIVE_PATH: '+str(name))
    return path


def archive_rows(raw, tree):
    require(isinstance(tree, dict) and tree, 'E_CURRENT_EMPTY_TREE')
    allowed_dirs = {str(parent) for name in tree for parent in safe_name(name).parents
                    if str(parent) != '.'}
    found = {}; folded = set(); prefixes = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        for item in bundle.infolist():
            name = item.filename.rstrip('/') if item.is_dir() else item.filename
            safe_name(name)
            require(not stat.S_ISLNK(item.external_attr >> 16), 'E_CURRENT_ARCHIVE_LINK')
            for prefix in (PurePosixPath(name), *PurePosixPath(name).parents):
                spelling = str(prefix)
                require(prefixes.get(spelling.casefold(), spelling) == spelling,
                        'E_CURRENT_ARCHIVE_PREFIX_COLLISION')
                prefixes[spelling.casefold()] = spelling
            if item.is_dir():
                require(name in allowed_dirs, 'E_CURRENT_ARCHIVE_EXTRA_DIRECTORY')
                continue
            require(name.casefold() not in folded, 'E_CURRENT_ARCHIVE_COLLISION')
            folded.add(name.casefold()); data = bundle.read(item)
            ident = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            require(tree.get(name) == ident, 'E_CURRENT_ARCHIVE_BLOB')
            found[name] = data
    require(set(found) == set(tree), 'E_CURRENT_ARCHIVE_SET')
    all_paths = {name.casefold() for name in found}
    for name in found:
        require(not any(str(parent).casefold() in all_paths for parent in PurePosixPath(name).parents
                        if str(parent) != '.'), 'E_CURRENT_ARCHIVE_PARENT_COLLISION')
    return found


def source_manifest(root):
    root = ordinary(Path(root)); rows = {}
    def failed(error): raise error
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=failed):
        ordinary(Path(parent))
        for name in dirs: ordinary(Path(parent)/name)
        for name in files:
            path = Path(parent)/name
            rows[path.relative_to(root).as_posix()] = sha(read_file(path))
    return dict(sorted(rows.items()))


def verify_source(root, expected):
    require(source_manifest(root) == expected, 'E_CURRENT_SOURCE_CHANGED')
    expected_dirs = {str(parent) for name in expected for parent in PurePosixPath(name).parents
                     if str(parent) != '.'}
    actual_dirs = set()
    for parent, dirs, _ in os.walk(root, onerror=lambda error: (_ for _ in ()).throw(error)):
        for name in dirs:
            actual_dirs.add((Path(parent)/name).relative_to(root).as_posix())
    require(actual_dirs == expected_dirs, 'E_CURRENT_SOURCE_DIRECTORY_CHANGED')


def extract_source(raw, tree, destination):
    rows = archive_rows(raw, tree)  # Validate ALL members before ANY destination write.
    destination = Path(destination); ordinary(destination.parent)
    require(not os.path.lexists(destination), 'E_CURRENT_DESTINATION_EXISTS')
    destination.mkdir(); ordinary(destination)
    for name, data in rows.items():
        path = destination/Path(name)
        path.parent.mkdir(parents=True, exist_ok=True); ordinary(path.parent)
        with path.open('xb') as stream: stream.write(data)
    expected = {name: sha(data) for name, data in rows.items()}
    verify_source(destination, expected)
    return expected


def parse_child(meta, stdout, stderr):
    require(meta['exit_code'] == 0 and meta['complete'] is True,
            'E_CURRENT_CHILD_FAILED: '+stderr.decode('utf-8', 'backslashreplace')[:2000])
    try: return json.loads(stdout.decode('utf-8'))
    except (UnicodeError, ValueError) as error: raise ValueError('E_CURRENT_CHILD_NOT_JSON') from error


def validate_runtime(value, env, cwd):
    load_support('gate1_image_successor').validate_runtime_observation(value, env, cwd)


def validate_dependencies(value, expected):
    require(isinstance(value, dict) and set(value) == {'versions', 'revision', 'user_site'} and
            value['versions'] == expected and value['revision'] == REVISION and
            value['user_site'] is False, 'E_CURRENT_DEPENDENCIES')


def committed_source():
    require(git('rev-parse', 'HEAD').decode().strip() == HEAD, 'E_CURRENT_HEAD')
    tree = {}
    for row in git('ls-tree', '-rz', HEAD).split(b'\0'):
        if not row: continue
        meta, name = row.split(b'\t', 1); mode, kind, ident = meta.split()
        require(mode == b'100644' and kind == b'blob', 'E_CURRENT_TREE_MODE')
        tree[name.decode('utf-8')] = ident.decode('ascii')
    raw = git('archive', '--format=zip', HEAD)
    rows = archive_rows(raw, tree)
    manifest = {name: sha(data) for name, data in rows.items()}
    # The Fable continuation itself may be uncommitted; production source may not.
    for name in manifest:
        if name.startswith(('memory-integrity/', 'claude-mon/', 'semantica-runtime/', '.github/fixtures/')):
            require(sha(read_file(REPO/name)) == manifest[name], 'E_CURRENT_LIVE_SOURCE_CHANGED: '+name)
    return raw, tree, manifest


def fixed_inputs():
    g = load_support('gate1_validation'); n3 = g.WORKER.parents[2]
    paths = [(Path(sys.executable), g.CONTROLLER_SHA, 1), (g.WORKER, g.WORKER_SHA, 1),
        (g.WORKER.parents[1]/'pyvenv.cfg', g.CONFIG_SHA, 1),
        (g.BASE, g.BASE_SHA, 1), (g.BASE.with_name('python3.12.exe'), g.BASE_SHA, 1),
        (n3/'recovery-a3/windows-overlay.txt', '5370d4e6ded5e9d10b4f47bf623bba2e01a29e0decde89e638fb87e5035e53a8', 1),
        (REPO/'.github/run-artifacts/extended-worker-timing-20261023/Attempt/Receipt.json',
         'b4bf001140ad6d4c486f4674bd7b82cf3c0ea23879e1c7bf994000c11822f569', 1),
        (REPO/'.github/run-artifacts/timeout-publication-20261023/Normal-Push-Attempt/Receipt.json',
         '227a9610f01b760387e804e4c733047b86fcfb99b3a42e81627a56df4b870946', 1)]
    result = {}
    for path, expected, links in paths:
        row = record(path, links); require(row['sha256'] == expected, 'E_CURRENT_PIN: '+str(path))
        result[str(path)] = row
    for role, expected in SUPPORT.items():
        path = REPO/'.github/scripts'/(role+'.py'); result[str(path)] = record(path)
        require(result[str(path)]['sha256'] == expected, 'E_CURRENT_SUPPORT_PIN')
    return result


def dependency_versions():
    versions = {'semantica': '0.7.0'}
    lock = read_file(REPO/'semantica-runtime/requirements-lock.txt').decode('utf-8')
    for line in lock.splitlines():
        if '==' in line:
            name, version = line.split('=='); versions[name] = version
    versions.update({'colorama': '0.4.6', 'tzdata': '2026.5', 'win32-setctime': '1.2.0'})
    require(len(versions) == 53, 'E_CURRENT_DEPENDENCY_SET')
    return versions


def prepare_contract():
    _, tree, manifest = committed_source()
    fixed = fixed_inputs(); versions = dependency_versions()
    require(not os.path.lexists(OUTPUT), 'E_CURRENT_EXISTING_ATTEMPT')
    CONTRACT.parent.mkdir(parents=True, exist_ok=True); ordinary(CONTRACT.parent)
    value = {'schema': 1, 'scope': 'GATE1_CURRENT_STEP1_SOURCE_ENV_ONLY', 'head': HEAD,
        'repo': str(REPO), 'output': str(OUTPUT), 'tree': tree, 'manifest': manifest,
        'fixed': fixed, 'versions': versions, 'helper': record(Path(__file__).absolute()),
        'producer_authentication': False, 'gate1_complete': False, 'release_ready': False,
        'installed': False}
    save(CONTRACT, value)
    print(json.dumps({'status': 'C1_CONTRACT_ONLY_NO_SOURCE_OR_SELECTED_PYTHON',
        'contract': record(CONTRACT), 'files': len(manifest)}))


def verify_inputs(path, digest):
    require(Path(path) == CONTRACT and sha(read_file(path)) == digest, 'E_CURRENT_EXTERNAL_CONTRACT')
    value = json.loads(read_file(path))
    require(set(value) == {'schema', 'scope', 'head', 'repo', 'output', 'tree', 'manifest', 'fixed',
        'versions', 'helper', 'producer_authentication', 'gate1_complete', 'release_ready', 'installed'} and
        type(value['schema']) is int and value['schema'] == 1 and value['head'] == HEAD and
        value['repo'] == str(REPO) and value['output'] == str(OUTPUT) and
        value['scope'] == 'GATE1_CURRENT_STEP1_SOURCE_ENV_ONLY' and
        all(value[key] is False for key in ('producer_authentication', 'gate1_complete', 'release_ready', 'installed')),
        'E_CURRENT_CONTRACT_SCHEMA')
    require(record(Path(__file__).absolute()) == value['helper'], 'E_CURRENT_HELPER_CHANGED')
    require(fixed_inputs() == value['fixed'] and dependency_versions() == value['versions'], 'E_CURRENT_INPUTS_CHANGED')
    raw, tree, manifest = committed_source()
    require(tree == value['tree'] and manifest == value['manifest'], 'E_CURRENT_COMMITTED_SOURCE_CHANGED')
    require(not os.path.lexists(OUTPUT), 'E_CURRENT_EXISTING_ATTEMPT')
    require(not os.path.lexists(PREFLIGHT_FAILURE), 'E_CURRENT_PREFLIGHT_FAILURE_PRESERVED')
    return value, raw


def protected():
    # No recursive traversal of unrelated private archives. C1 is NOT their verdict.
    return {str(REPO/name): source_manifest(REPO/name) for name in
            ('memory-integrity', 'claude-mon', '%SystemDrive%', 'release')}


def normal_account():
    import ctypes
    who = Path(os.environ['SYSTEMROOT'])/'System32/whoami.exe'
    result = subprocess.run([str(who), '/user', '/fo', 'csv', '/nh'], capture_output=True, timeout=10, check=True)
    require(b'S-1-5-21-2571509308-2482563067-4170768140-1001' in result.stdout and
            not ctypes.windll.shell32.IsUserAnAdmin(), 'E_CURRENT_NORMAL_ACCOUNT_REQUIRED')


def finalize_result(output, receipt, candidate, final_check):
    """Only a successful receipt bound to Prepared can authorize the next phase."""
    try:
        final_check()
        receipt['protected_unchanged'] = True
        if candidate is not None and receipt['failure'] is None:
            save(output/'Prepared.json', candidate)
            receipt['prepared'] = record(output/'Prepared.json')
            receipt['status'] = 'STEP1_SOURCE_AND_ENVIRONMENT_VERIFIED_NOT_GATE1'
    except Exception:
        receipt['preservation_failure'] = traceback.format_exc()
        receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
        receipt.pop('prepared', None)
    receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
    save(output/'Receipt.json', receipt)


def retain_preflight_failure(path, failure):
    save(path, {'scope': 'GATE1_CURRENT_STEP1_SOURCE_ENV_ONLY',
        'status': 'C1_PREFLIGHT_FAILED_NO_SOURCE_OR_RETRIEVAL', 'head': HEAD,
        'failure': failure, 'observed_utc': datetime.now(timezone.utc).isoformat(),
        'gate1_complete': False, 'release_ready': False, 'installed': False,
        'producer_authentication': False})


def run(path, digest):
    # Wrong-account refusal must NOT spend the normal account's attempt.
    normal_account()
    require(not os.path.lexists(OUTPUT) and not os.path.lexists(PREFLIGHT_FAILURE),
            'E_CURRENT_EXISTING_ATTEMPT')
    try:
        value, raw = verify_inputs(path, digest); before = protected()
    except Exception:
        failure = traceback.format_exc()
        retain_preflight_failure(PREFLIGHT_FAILURE, failure)
        print(json.dumps({'status': 'C1_PREFLIGHT_FAILED_NO_SOURCE_OR_RETRIEVAL',
            'receipt': record(PREFLIGHT_FAILURE), 'failure': failure, 'gate1_complete': False}))
        return 1
    ordinary(OUTPUT.parent); require(not os.path.lexists(OUTPUT), 'E_CURRENT_EXISTING_ATTEMPT')
    OUTPUT.mkdir(); ordinary(OUTPUT)
    receipt = {'scope': value['scope'], 'status': 'PARTIAL_OR_FAILED_NO_RETRY', 'head': HEAD,
        'started_utc': datetime.now(timezone.utc).isoformat(), 'failure': None,
        'gate1_complete': False, 'release_ready': False, 'installed': False,
        'retrieval_executed': False, 'producer_authentication': False, 'commands': []}
    candidate = None
    try:
        manifest = extract_source(raw, value['tree'], OUTPUT/'source')
        require(manifest == value['manifest'], 'E_CURRENT_COPY_CHANGED')
        save(OUTPUT/'Protected-Before.json', before)
        env = load_support('gate1_image_successor').windows_environment(dict(os.environ))
        for key in ('PYTHONPATH', 'PYTHONHOME', 'MODEL_PYTHON', 'KNOWLEDGE_MODEL_MANIFEST',
                    'MEMORY_INTEGRITY_WORKER_DIAGNOSTICS'):
            env.pop(key, None)
        (OUTPUT/'temp').mkdir()
        env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1',
            TRANSFORMERS_OFFLINE='1', TEMP=str(OUTPUT/'temp'), TMP=str(OUTPUT/'temp'), TMPDIR=str(OUTPUT/'temp'))
        g = load_support('gate1_validation'); host = load_support('offline_host_validation')
        def capture(label, script, extra=()):
            target = OUTPUT/label; target.mkdir()
            completed, details = host.capture_owned([g.WORKER, '-B', '-c', script, *extra], target, target, env, 30)
            receipt['commands'].append(details)
            data = parse_child({'exit_code': details['exit_code'], 'complete': completed is not None},
                               read_file(target/'stdout.log'), read_file(target/'stderr.log'))
            return data, target
        runtime, cwd = capture('identity', g.runtime_probe())
        validate_runtime(runtime, env, cwd)
        script = '''import importlib.metadata as m,json,site,sys
names=json.loads(sys.argv[1]);d=m.distribution('semantica')
u=json.loads(d.read_text('direct_url.json') or '{}')
print(json.dumps({'versions':{n:m.version(n) for n in names},'revision':u.get('vcs_info',{}).get('commit_id'),
 'user_site':site.ENABLE_USER_SITE}))
'''
        deps, _ = capture('dependencies', script, (json.dumps(sorted(value['versions'])),))
        validate_dependencies(deps, value['versions'])
        # Import ONLY stdlib-based clients from the exact new copy; no worker call.
        script = '''import json,sys
sys.path.insert(0,sys.argv[1])
from knowledge_bridge.worker_client import WorkerClient
from knowledge_bridge.distributed_retrieval import DistributedClient
print(json.dumps({'single':WorkerClient(sys.executable).timeout,
 'distributed':DistributedClient(sys.executable).timeout}))
'''
        defaults, _ = capture('copied-client-defaults', script, (str(OUTPUT/'source/memory-integrity/scripts'),))
        require(defaults == {'single': 120, 'distributed': 120}, 'E_CURRENT_DEFAULT_NOT120')
        verify_source(OUTPUT/'source', value['manifest'])
        require(protected() == before, 'E_CURRENT_PROTECTED_CHANGED')
        require(fixed_inputs() == value['fixed'] and sha(read_file(path)) == digest and
                record(Path(__file__).absolute()) == value['helper'] and
                git('rev-parse', 'HEAD').decode().strip() == HEAD, 'E_CURRENT_INPUT_CHANGED')
        candidate = dict(value, source=str(OUTPUT/'source'), runtime=runtime,
             dependency_observation=deps, defaults=defaults, protected_before=before)
    except Exception:
        receipt['failure'] = traceback.format_exc()
    finally:
        def final_check():
            require(protected() == before, 'E_CURRENT_PROTECTED_CHANGED')
            require(fixed_inputs() == value['fixed'] and sha(read_file(path)) == digest and
                    record(Path(__file__).absolute()) == value['helper'] and
                    git('rev-parse', 'HEAD').decode().strip() == HEAD, 'E_CURRENT_INPUT_CHANGED')
            if candidate is not None: verify_source(OUTPUT/'source', value['manifest'])
        finalize_result(OUTPUT, receipt, candidate, final_check)
    print(json.dumps({'status': receipt['status'], 'receipt': record(OUTPUT/'Receipt.json'),
        'prepared': receipt.get('prepared'), 'failure': receipt['failure'], 'gate1_complete': False}))
    return 0 if receipt['status'] == 'STEP1_SOURCE_AND_ENVIRONMENT_VERIFIED_NOT_GATE1' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-contract', action='store_true')
    parser.add_argument('--verify-inputs', action='store_true')
    parser.add_argument('--contract', type=Path, default=CONTRACT)
    parser.add_argument('--sha256')
    args = parser.parse_args()
    if args.prepare_contract: prepare_contract(); return 0
    require(bool(args.sha256), 'E_CURRENT_EXTERNAL_HASH_REQUIRED')
    if args.verify_inputs:
        verify_inputs(args.contract, args.sha256)
        print('C1_INPUTS_VERIFIED_NO_SOURCE_COPY_OR_SELECTED_PYTHON'); return 0
    return run(args.contract, args.sha256)


if __name__ == '__main__':
    raise SystemExit(main())
