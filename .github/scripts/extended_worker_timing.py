"""Isolated supported-120s timing experiment, never a release or old W retry."""
import argparse
import ast
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
import traceback
import zipfile

import worker_diagnostic_events as observer

REPO = Path(__file__).absolute().parents[2]
HEAD = 'b71b75b77b8e9432eb9d51c0828825e3e344ce12'
OUT = REPO / '.github/run-artifacts/extended-worker-timing-20261023'
GIT = Path(r'C:\Program Files\Git\cmd\git.exe')
WORKER = REPO.parent / 'build-validation/n3-retrieval-9ec6fb1db36444acba2945896e8b8d17/venv/Scripts/python.exe'
BUDGET = 120
CASES = (('community', 'single'), ('vector', 'distributed-local'))
IO_ROLES = ('contracts.py', 'indexing.py', 'impact.py', 'retrieval.py', 'retrieval_v2.py')
FIXTURE = {
    'client.py': 'from worker import work\ndef call():\n    return work()\n',
    'worker.py': 'def work():\n    return 2\n',
    'test_sample.py': 'import unittest\nfrom worker import work\nclass Check(unittest.TestCase):\n    def test_work(self):\n        self.assertEqual(work(), 2)\n',
}
CACHE_ROOT = REPO/'memory-integrity/%SystemDrive%/ProgramData/Microsoft/Windows/Caches'
CACHE_PINS = {
    'cversions.2.db':'05afdd55b3678d0b95d3b0cd5f103d812a5f34957a12a98952f3a0df37f4f2f7',
    '{6AF0698E-D558-4F6E-9B3C-3716689AF493}.2.ver0x0000000000000001.db':'ddbedcf11d78f9e71df2f3ae4b44404dec17335ebaee20c752e0874126611981',
    '{6AF0698E-D558-4F6E-9B3C-3716689AF493}.2.ver0x0000000000000002.db':'ddbedcf11d78f9e71df2f3ae4b44404dec17335ebaee20c752e0874126611981',
    '{DDF571F2-BE98-426D-8288-1A9A39C3FDA2}.2.ver0x0000000000000001.db':'738eb0ccafefd1646d9fff98d23d998b51e4c4a8409ef0e423842eaa1ba2dd6b',
    '{DDF571F2-BE98-426D-8288-1A9A39C3FDA2}.2.ver0x0000000000000002.db':'738eb0ccafefd1646d9fff98d23d998b51e4c4a8409ef0e423842eaa1ba2dd6b',
    '{FDC62402-85C5-4A90-A9ED-B164461304D2}.2.ver0x0000000000000001.db':'483cdcdfa21796ccd47d54a7676c6afab888657ff88daebc44cfe4896fa349d2',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ordinary(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        info = part.lstat()
        require(not part.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400,
                'E_EXT_REDIRECT: ' + str(part))
    return path


def file_record(path):
    path = ordinary(path)
    info = path.stat()
    require(path.is_file() and info.st_nlink == 1, 'E_EXT_FILE_KIND_OR_LINK')
    raw = path.read_bytes()
    again = path.stat()
    require((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) ==
            (again.st_dev, again.st_ino, again.st_size, again.st_mtime_ns), 'E_EXT_FILE_CHANGED_DURING_READ')
    return {'size': len(raw), 'sha256': sha(raw)}


def check_records(rows):
    for path, expected in rows.items():
        require(file_record(path) == expected, 'E_EXT_INPUT_CHANGED: ' + str(path))


def save(path, value):
    with Path(path).open('xb') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False).encode('utf-8') + b'\n')


def git(*args):
    require(sha(GIT.read_bytes()) == 'da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f',
            'E_EXT_GIT_EXECUTABLE')
    result = subprocess.run([str(GIT), '--no-optional-locks', '-C', str(REPO), *args],
                            capture_output=True, timeout=30, check=True)
    return result.stdout


def search_argv(python, source, fixture, pack, strategy, execution, worker):
    require((strategy, execution) in CASES, 'E_EXT_CASE')
    return list(map(str, [python, '-B', Path(source)/'memory-integrity/scripts/memory_integrity_workflow.py',
        'knowledge-retrieve', '--claude-mon-root', Path(source)/'claude-mon',
        '--project-root', fixture, '--index-dir', Path(fixture)/'index',
        '--policy-file', Path(fixture)/'policy.json', '--task-file', Path(fixture)/'task.json',
        '--query-text', 'work', '--evidence-pack', pack, '--worker-python', worker,
        '--worker-timeout', BUDGET, '--strategy', strategy, '--execution', execution]))


def claim_after_probe(attempt, probe):
    probe()
    Path(attempt).mkdir()
    return Path(attempt)


def io_overlay(raw, role, expected_sha):
    require(sha(raw) == expected_sha, 'E_EXT_SOURCE_PIN: ' + role)
    tree = ast.parse(raw.decode('utf-8'))
    class Observe(ast.NodeTransformer):
        def visit_Call(self, node):
            self.generic_visit(node)
            if not isinstance(node.func, ast.Attribute):
                return node
            name = node.func.attr
            if name in ('read_bytes', 'read_text'):
                return ast.Call(func=ast.Attribute(value=ast.Name(id='_et', ctx=ast.Load()),
                    attr=name, ctx=ast.Load()), args=[node.func.value, *node.args], keywords=node.keywords)
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'c' and name in ('digest', 'within'):
                return ast.Call(func=ast.Attribute(value=ast.Name(id='_et', ctx=ast.Load()),
                    attr='digest' if name == 'digest' else 'locate', ctx=ast.Load()),
                    args=[node.func, *node.args], keywords=node.keywords)
            return node
        def visit_FunctionDef(self, node):
            self.generic_visit(node)
            selected = {'indexing.py': {'load', 'freeze', 'reopen'},
                        'impact.py': {'build'},
                        'retrieval.py': {'validate_policy', 'verify_pack'},
                        'retrieval_v2.py': {'_visible', '_required_units', '_exclusions',
                                          '_validate_pack', 'retrieve', 'retrieve_advanced',
                                          'verify_pack', 'verify_advanced_pack'}}
            if node.name in selected.get(role, set()):
                label = 'source-unit-reopen' if role == 'indexing.py' and node.name == 'reopen' else role[:-3] + '-' + node.name
                node.decorator_list.append(ast.parse('_et.traced(' + repr(label) + ')', mode='eval').body)
            return node
    tree = Observe().visit(tree)
    ast.fix_missing_locations(tree)
    return (ast.unparse(tree) + '\n').encode('utf-8')


BOOTSTRAP = '''
def bootstrap_from_environment():
    import os
    from pathlib import Path
    import json
    root = os.environ.get("MEMORY_INTEGRITY_WORKER_DIAGNOSTICS")
    if root:
        config = json.loads((Path(root).parent / "Config.json").read_bytes())
        configure(Path(root).parent / "io", config["watched_roots"], budget=120)
'''


def add_bootstrap(raw, role):
    tree = ast.parse(raw.decode('utf-8'))
    prelude = ast.parse('from knowledge_bridge import _extended_timing as _et\n_et.bootstrap_from_environment()').body
    if role in observer.SOURCE_PINS:
        positions = [n for n, item in enumerate(tree.body) if isinstance(item, ast.Expr) and
                     isinstance(item.value, ast.Call) and ast.unparse(item.value.func) == '_wd.module_entry']
        require(len(positions) == 1, 'E_EXT_BOOTSTRAP_ANCHOR')
        at = positions[0] + 1
    else:
        at = 1 if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str) else 0
    tree.body[at:at] = prelude
    ast.fix_missing_locations(tree)
    return (ast.unparse(tree) + '\n').encode('utf-8')


def inputs():
    names = git('ls-files', '-z', '--', 'memory-integrity', 'claude-mon').decode('utf-8').split('\0')
    paths = {REPO/name for name in names if name}
    paths.update(cache_inputs(CACHE_ROOT))
    paths.update(REPO/'.github/scripts'/name for name in (
        'extended_worker_timing.py', 'extended_timing_log.py', 'worker_diagnostic_events.py',
        'offline_host_validation.py', 'offline_release_acceptance.py',
        'gate1_validation.py', 'gate1_image_successor.py'))
    paths.update((WORKER, WORKER.parent.parent/'pyvenv.cfg', Path(sys.executable)))
    # Bind the completed evidence directly, never rerun it or copy its code.
    paths.add(Path(r'C:\Users\sakth\Documents\Codex\w-h1-20261022-80b78d91\BEFORE\Bundle.json'))
    paths.add(REPO/'.github/run-artifacts/publication-h1-20261023/Publish-Attempt/Receipt.json')
    return {str(p.absolute()): file_record(p) for p in sorted(paths)}


def cache_inputs(root):
    root=ordinary(root)
    def failed(error):
        raise error
    found=set()
    for parent, dirs, files in os.walk(root,followlinks=False,onerror=failed):
        ordinary(parent)
        for name in dirs:
            ordinary(Path(parent)/name)
        for name in files:
            found.add(str((Path(parent)/name).relative_to(root)).replace('\\','/'))
    require(found==set(CACHE_PINS), 'E_EXT_CACHE_SET')
    for name,expected in CACHE_PINS.items():
        require(file_record(root/name)['sha256']==expected, 'E_EXT_CACHE_CHANGED:'+name)
    return [root/name for name in sorted(CACHE_PINS)]


def make_source_copy(source):
    ordinary(source)
    require(not any(source.iterdir()), 'E_EXT_SOURCE_DESTINATION_EXISTS')
    archive = git('archive', '--format=zip', HEAD, 'memory-integrity', 'claude-mon')
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        for item in bundle.infolist():
            path = Path(item.filename)
            require(not path.is_absolute() and '..' not in path.parts and
                    path.parts[0] in ('memory-integrity', 'claude-mon'), 'E_EXT_ARCHIVE_PATH')
            if item.is_dir():
                (source/path).mkdir(parents=True, exist_ok=True)
            else:
                require((item.external_attr >> 16) & 0o170000 != 0o120000, 'E_EXT_ARCHIVE_LINK')
                raw = bundle.read(item)
                require(raw == (REPO/path).read_bytes(), 'E_EXT_GIT_SOURCE_DRIFT')
                (source/path).parent.mkdir(parents=True, exist_ok=True)
                with (source/path).open('xb') as stream:
                    stream.write(raw)
    bridge = source/'memory-integrity/scripts/knowledge_bridge'
    for role in (*observer.SOURCE_PINS, *IO_ROLES):
        path = bridge/role; original = path.read_bytes()
        raw = observer.diagnostic_source(original, observer.SOURCE_PINS[role], role) if role in observer.SOURCE_PINS else original
        if role in IO_ROLES:
            raw = io_overlay(raw, role, sha(raw))
        path.write_bytes(add_bootstrap(raw, role))  # This newly owned copy only.
    for name, raw in [('_worker_diag_v1.py', Path(observer.__file__).read_bytes()),
                      ('_extended_timing.py', (REPO/'.github/scripts/extended_timing_log.py').read_bytes() + BOOTSTRAP.encode())]:
        with (bridge/name).open('xb') as stream:
            stream.write(raw)
    copied = {str(p): file_record(p) for p in source.rglob('*') if p.is_file()}
    return archive, copied


def prepare():
    require(git('rev-parse', 'HEAD').decode().strip() == HEAD, 'E_EXT_HEAD')
    OUT.parent.mkdir(exist_ok=True)
    ordinary(OUT.parent)
    OUT.mkdir()  # Exclusive new successor, including after any partial failure.
    rows = inputs()
    source = OUT/'source'; source.mkdir()
    archive, copied = make_source_copy(source)
    check_records(rows)
    doc = {'scope': 'EXTENDED_TIMING_ONLY_NOT_W_OR_GATE1', 'head': HEAD,
           'output': str(OUT), 'source': str(source), 'worker': str(WORKER),
           'worker_budget': BUDGET, 'outer_budget': 180, 'overall_budget': 900,
           'files': rows, 'copied': copied, 'archive_sha256': sha(archive),
           'cases': list(map(list, CASES)), 'whole_skill_ready': False,
           'producer_authentication': False, 'fixture': FIXTURE}
    save(OUT/'Prepared.json', doc)
    print(json.dumps({'status': 'EXTENDED_INPUTS_PREPARED_NO_RUNTIME',
                      'prepared': str(OUT/'Prepared.json'), 'sha256': sha((OUT/'Prepared.json').read_bytes()),
                      'copied_files': len(copied), 'worker_started': False}))


def load_prepared(expected):
    ordinary(OUT)
    raw = (OUT/'Prepared.json').read_bytes()
    require(sha(raw) == expected, 'E_EXT_PREPARED_SEAL')
    doc = json.loads(raw)
    require(doc['head'] == HEAD and doc['output'] == str(OUT) and doc['worker'] == str(WORKER) and
            doc['worker_budget'] == BUDGET and doc['outer_budget'] == 180 and doc['overall_budget'] == 900 and
            doc['cases'] == list(map(list, CASES)) and doc['fixture'] == FIXTURE and
            doc['whole_skill_ready'] is False and doc['producer_authentication'] is False, 'E_EXT_CONTRACT')
    require(git('rev-parse', 'HEAD').decode().strip() == HEAD, 'E_EXT_HEAD')
    check_records(doc['files']); check_records(doc['copied'])
    cache_inputs(CACHE_ROOT)
    return doc


def normal_account():
    import ctypes
    result = subprocess.run([str(Path(os.environ['SYSTEMROOT'])/'System32/whoami.exe'), '/user', '/fo', 'csv', '/nh'],
                            capture_output=True, check=True, timeout=10)
    require(b'S-1-5-21-2571509308-2482563067-4170768140-1001' in result.stdout and
            not ctypes.windll.shell32.IsUserAnAdmin(), 'E_EXT_NORMAL_ACCOUNT_REQUIRED')


def capture(label, argv, root, env, timeout):
    from offline_host_validation import capture_owned
    target = root/label; target.mkdir()
    started = time.monotonic_ns(); utc = datetime.now(timezone.utc).isoformat()
    print(label + ': RUNNING (120s worker diagnosis, not qualification)', flush=True)
    result, record = capture_owned(argv, target, target, env, timeout)
    return result, dict(record, label=label, start_utc=utc,
                        elapsed_seconds=(time.monotonic_ns()-started)/1e9, directory=str(target))


def audit_new_runtime(root, fixture):
    """Allow existing housekeeping only in this new run's owned runtime space."""
    def guard(event, args):
        if event in ('socket.connect', 'socket.bind', 'socket.getaddrinfo'):
            raise PermissionError('E_EXT_NO_NETWORK')
        if event in ('os.remove', 'os.rmdir', 'shutil.rmtree'):
            path = Path(os.fsdecode(args[0])).absolute()
            allowed = path.is_relative_to(root/'temp') or path == fixture/'index/writer.lock'
            require(allowed and path != root/'temp', 'E_EXT_NO_OLD_DELETION')
            if path.exists():
                ordinary(path)
                require(path.is_dir() or path.stat().st_nlink == 1, 'E_EXT_NO_LINKED_CLEANUP')
            require(len(args) < 2 or args[1] in (-1, None), 'E_EXT_NO_DIRFD_CLEANUP')
        if event == 'subprocess.Popen':
            require(Path(str(args[0])).name.lower() not in ('bd', 'bd.exe', 'dolt', 'dolt.exe', 'pip', 'pip.exe'),
                    'E_EXT_NO_NATIVE_OR_INSTALL')
    sys.addaudithook(guard)


def step(args):
    source = Path(args.source); fixture = Path(args.fixture); target = Path(args.target)
    config = json.loads((target/'Config.json').read_bytes())
    sys.path.insert(0, str(source/'memory-integrity/scripts'))
    from knowledge_bridge import _extended_timing as log
    log.bootstrap_from_environment()
    audit_new_runtime(target.parent, fixture)
    companion = source/'claude-mon'
    result = None
    if args.step == 'build':
        argv = [sys.executable, '-B', str(source/'memory-integrity/scripts/memory_integrity_workflow.py'),
                'knowledge-project', '--claude-mon-root', str(companion), '--project-root', str(fixture),
                '--index-dir', str(fixture/'index'), '--source-map', str(fixture/'sources.json')]
    elif args.step == 'search':
        argv = search_argv(sys.executable, source, fixture, args.pack, args.strategy, args.execution, WORKER)
    if args.step in ('build', 'search'):
        with log.span('public-' + args.step):
            sys.argv = argv[2:]
            try:
                runpy.run_path(argv[2], run_name='__main__')
            except SystemExit as error:
                if error.code not in (None, 0):
                    raise RuntimeError('E_EXT_PUBLIC_CHILD_EXIT:' + str(error.code)) from error
        if args.step == 'search':
            pack = json.loads(Path(args.pack).read_bytes())
            result = {'units': len(pack['units']), 'unique_sources': sorted({u['source_id'] for u in pack['units']}),
                      'pack_bytes': Path(args.pack).stat().st_size, 'pack_sha256': sha(Path(args.pack).read_bytes()),
                      'strategy': args.strategy, 'execution': args.execution}
            require(any(u['source_id'] == 'worker' and u['unit_id'] == 'U000001' for u in pack['units']), 'E_EXT_REQUIRED_SOURCE')
    else:
        from knowledge_bridge import indexing, retrieval, contracts as c
        from knowledge_bridge.worker_client import WorkerClient
        with log.span('fresh-replay'):
            policy = c.read(fixture/'policy.json'); task = c.read(fixture/'task.json')
            doc = indexing.load(fixture/'index', fixture, companion, allowed_sources=policy['allowed_source_ids'])
            worker = WorkerClient(str(WORKER), timeout=BUDGET)
            require(worker.timeout == BUDGET, 'E_EXT_REPLAY_BUDGET')
            retrieval.verify_pack(c.read(args.pack), doc, fixture, policy, task, worker)
            result = {'replay': 'PASS', 'worker_budget_seconds': worker.timeout}
    save(target/'Step-Result.json', result or {'index_build': 'RETURNED'})


def observer_rows(root, require_worker=True):
    raw = [p.read_bytes() for p in sorted((root/'events').glob('*.json'))]
    require(not list((root/'events').glob('*.error')), 'E_EXT_OBSERVER_ERROR')
    if not raw:
        require(not require_worker, 'E_EXT_MISSING_WORKER_TRACE')
        return []  # Index construction intentionally selects no numerical worker.
    parsed = observer.parse_events(raw, {'arm': 'events'})
    require(not parsed['errors'], 'E_EXT_OBSERVER_PARSE:' + str(parsed['errors']))
    rows, starts, spawning = [], {}, {}
    budgets = {r['child_pid']:r for r in parsed['events'] if r['phase']=='worker-deadline'}
    for row in parsed['events']:
        key = (row['pid'], row['thread'], row.get('span'))
        if row['kind'] == 'START':
            starts[key] = row
        elif row['kind'] == 'END':
            begin = starts.pop(key)
            rows.append({'action': row['phase'], 'path': row.get('filename', ''), 'pid': row['pid'],
                         'thread':row['thread'], 'error_type':row.get('error_type'),
                         'duration_seconds': row['duration_ns']/1e9, 'status': row['outcome'],
                         'start_monotonic_ns': begin['wall_ns'], 'end_monotonic_ns': row['wall_ns']})
        elif row['phase'] == 'worker-deadline':
            require(row['budget_seconds'] == BUDGET, 'E_EXT_OBSERVED_WRONG_BUDGET')
        elif row['phase'] == 'popen-entry':
            spawning[(row['pid'],row['thread'])] = row
        elif row['phase'] == 'popen-return':
            begin = spawning.pop((row['pid'],row['thread']),None)
            require(begin is not None, 'E_EXT_UNPAIRED_SPAWN')
            rows.append({'action':'process-creation','pid':row['pid'],'thread':row['thread'],
                'duration_seconds':(row['wall_ns']-begin['wall_ns'])/1e9,'status':'RETURNED',
                'start_monotonic_ns':begin['wall_ns'],'end_monotonic_ns':row['wall_ns'],
                'details':{'child_pid':row['child_pid'],'includes_observer_identity_capture':True}})
            entry = next((r for r in parsed['events'] if r['pid']==row['child_pid'] and
                r.get('creation')==row['child_creation'] and r['phase'] in
                ('worker-entry','distributed-worker-entry')),None)
            overlap=entry is not None and entry['wall_ns']<row['wall_ns']
            rows.append({'action':'spawn-to-python-module-entry','pid':row['child_pid'],
                'thread':None if entry is None else entry['thread'],
                'duration_seconds':None if entry is None or overlap else (entry['wall_ns']-row['wall_ns'])/1e9,
                'status':'UNFINISHED' if entry is None else ('OVERLAPPED_PROCESS_CREATION' if overlap else 'RETURNED'),
                'start_monotonic_ns':row['wall_ns'],
                'end_monotonic_ns':None if entry is None else entry['wall_ns'],
                'worker_budget_seconds':budgets.get(row['child_pid'],{}).get('budget_seconds'),
                'details':{'overlap_possible':True,'not_pure_interpreter_startup':True}})
        elif row['phase']=='base-imports-complete':
            entry=next((r for r in parsed['events'] if r['pid']==row['pid'] and
                r['thread']==row['thread'] and r['phase'] in ('worker-entry','distributed-worker-entry')),None)
            require(entry is not None and row['wall_ns']>=entry['wall_ns'],'E_EXT_BASE_IMPORT_POINT')
            rows.append({'action':'module-entry-to-base-imports-complete','pid':row['pid'],
                'thread':row['thread'],'duration_seconds':(row['wall_ns']-entry['wall_ns'])/1e9,
                'status':'RETURNED','start_monotonic_ns':entry['wall_ns'],'end_monotonic_ns':row['wall_ns'],
                'details':{'not_all_libraries':True}})
    for row in starts.values():
        rows.append({'action': row['phase'], 'pid': row['pid'], 'thread':row['thread'], 'path': row.get('filename', ''),
                     'duration_seconds': None, 'status': 'UNFINISHED', 'start_monotonic_ns': row['wall_ns']})
    return rows


def timing_markdown(table):
    lines = ['# Actual diagnostic timing records', '',
             'Inclusive phase times overlap; do not sum them as total wall time.', '',
             '| Operation | Action | File/path | PID | Thread | Start UTC | End UTC | Seconds | Bytes | Status | SHA-256 | Error type |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for row in table:
        duration = row.get('duration_seconds')
        values = [row.get('operation',''), row.get('action',row.get('phase','')),
                  row.get('path') or '', str(row.get('pid') or ''), str(row.get('thread') or ''), row.get('start_utc') or '',
                  row.get('end_utc') or 'UNFINISHED',
                  'UNKNOWN' if duration is None else format(duration,'.6f'),
                  str(row.get('bytes','')), row.get('status',''), row.get('sha256') or '', row.get('error_type') or '']
        lines.append('| ' + ' | '.join(str(v).replace('|','/').replace('\n',' ') for v in values) + ' |')
    return '\n'.join(lines)+'\n'


def create_fixture(fixture):
    import threading
    began=time.monotonic_ns(); started=datetime.now(timezone.utc).isoformat()
    rows=[]; fixture.mkdir()
    def write(path,raw):
        begin=time.monotonic_ns(); utc=datetime.now(timezone.utc).isoformat()
        with path.open('xb') as stream:
            stream.write(raw)
        rows.append({'operation':'fixture-creation','action':'fixture-file-write','path':str(path),
            'pid':os.getpid(),'thread':threading.get_ident(),'start_utc':utc,
            'end_utc':datetime.now(timezone.utc).isoformat(),'duration_seconds':(time.monotonic_ns()-begin)/1e9,
            'bytes':len(raw),'status':'RETURNED'})
    for name,text in FIXTURE.items():
        write(fixture/name,text.encode('utf-8'))
    source_map={'schema_version':1,'workspace_id':'w','repository':'example','sources':[
        {'id':ident,'path':name,'authority':'SUPPORTING' if ident=='test' else 'AUTHORITATIVE'}
        for ident,name in [('client','client.py'),('worker','worker.py'),('test','test_sample.py')]]}
    policy={'schema_version':1,'workspace_id':'w','task_id':'t','allowed_source_ids':['client','worker','test']}
    task={'schema_version':1,'task_id':'t','required_units':[{'source_id':'worker','unit_id':'U000001'}],
          'require_graph':True,'max_bytes':200000,
          'execution_task_digest':sha(json.dumps({'schema_version':3,'instructions':'inspect work'},
              sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())}
    for name,value in [('sources',source_map),('policy',policy),('task',task)]:
        write(fixture/(name+'.json'),json.dumps(value,indent=2,ensure_ascii=True).encode()+b'\n')
    rows.append({'operation':'fixture-creation','action':'fixture-creation','path':str(fixture),
        'pid':os.getpid(),'thread':threading.get_ident(),'start_utc':started,
        'end_utc':datetime.now(timezone.utc).isoformat(),'duration_seconds':(time.monotonic_ns()-began)/1e9,
        'status':'RETURNED'})
    return rows


def run(expected):
    normal_account()
    doc = load_prepared(expected)
    began=time.monotonic()
    from gate1_validation import runtime_probe
    from gate1_image_successor import validate_runtime_observation, windows_environment
    env = windows_environment(dict(os.environ))
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    for name in ('MODEL_PYTHON', 'KNOWLEDGE_MODEL_MANIFEST', observer.ENV):
        env.pop(name, None)
    preflight = OUT/'Runtime-Preflight'; preflight.mkdir()
    def probe():
        result, record = capture('identity', [str(WORKER), '-B', '-c', runtime_probe()], preflight, env, 60)
        save(preflight/'Probe.json', record)
        require(result is not None and result.returncode == 0, 'E_EXT_RUNTIME_UNAVAILABLE_READ_RETAINED_STDERR')
        validate_runtime_observation(json.loads(result.stdout), env, preflight/'identity')
        load_prepared(expected)
    attempt = claim_after_probe(OUT/'Attempt', probe)
    fixture = attempt/'fixture'; table=create_fixture(fixture)
    temp = attempt/'temp'; temp.mkdir()
    env.update(TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    receipt = {'scope':'EXTENDED_TIMING_DIAGNOSTIC_NOT_QUALIFICATION','head':HEAD,'worker_budget_seconds':BUDGET,
               'commands':[], 'cases':[], 'failure':None, 'preservation':False,
               'producer_authentication':False,'whole_skill_ready':False,'gate1_complete':False}
    receipt['elapsed_wall_scope'] = 'After sealed-input preflight through runtime probe, fixture creation and workload; not sum of nested phase times'
    def execute(label, mode, strategy='community', execution='single', pack=None):
        target = attempt/label; target.mkdir(); (target/'events').mkdir(); (target/'io').mkdir()
        anchor = {'anchor_monotonic_ns':time.monotonic_ns(), 'anchor_utc':datetime.now(timezone.utc).isoformat(),
                  'watched_roots':[str(fixture), str(Path(doc['source']))]}
        save(target/'Config.json', anchor)
        child_env = dict(env); child_env[observer.ENV] = str(target/'events')
        argv = [str(WORKER), '-B', str(Path(__file__).absolute()), '--step', mode,
                '--source', doc['source'], '--fixture', str(fixture), '--target', str(target),
                '--strategy', strategy, '--execution', execution]
        if pack is not None:
            argv += ['--pack', str(pack)]
        remaining = 900 - (time.monotonic()-began)
        require(remaining > 0, 'E_EXT_OVERALL_WATCHDOG')
        result, row = capture('capture', argv, target, child_env, min(180, remaining))
        receipt['commands'].append(dict(row, operation=label))
        from extended_timing_log import summarize
        details = [{'action':'owned-command-wall-time','pid':None,
                    'duration_seconds':row['elapsed_seconds'],'start_utc':row['start_utc'],
                    'end_utc':datetime.now(timezone.utc).isoformat(),
                    'status':row['execution'],'details':{'exit_code':row['exit_code']}}]
        details += summarize(list((target/'io').glob('*.jsonl')))
        details += observer_rows(target, require_worker=mode != 'build')
        for detail in details:
            detail['operation'] = label
            if 'duration_seconds' not in detail:
                ns = detail.get('duration_ns')
                detail['duration_seconds'] = None if ns is None else ns/1e9
            detail.setdefault('start_utc', (datetime.fromisoformat(anchor['anchor_utc']) +
                timedelta(microseconds=(detail.get('start_monotonic_ns',anchor['anchor_monotonic_ns'])-anchor['anchor_monotonic_ns'])/1000)).isoformat())
            end = detail.get('end_monotonic_ns')
            detail.setdefault('end_utc', None if end is None else
                (datetime.fromisoformat(anchor['anchor_utc']) +
                 timedelta(microseconds=(end-anchor['anchor_monotonic_ns'])/1000)).isoformat())
            table.append(detail)
        return result
    try:
        built = execute('index-build','build')
        require(built is not None and built.returncode == 0, 'E_EXT_INDEX_BUILD_READ_RETAINED_STDERR')
        for strategy, execution in CASES:
            pack = fixture/(strategy+'-'+execution+'.json')
            label = strategy+'-'+execution
            result = execute(label, 'search', strategy, execution, pack)
            case = {'strategy':strategy, 'execution':execution,
                    'retrieval_passed':result is not None and result.returncode == 0,
                    'replay_passed':False}
            receipt['cases'].append(case)
            if case['retrieval_passed']:
                case['result'] = json.loads((attempt/label/'Step-Result.json').read_bytes())
                result = execute('replay-'+label, 'replay', strategy, execution, pack)
                case['replay_passed'] = result is not None and result.returncode == 0
    except Exception:
        receipt['failure'] = traceback.format_exc()
    finally:
        receipt['elapsed_wall_seconds'] = time.monotonic()-began
        try:
            load_prepared(expected); receipt['preservation'] = True
        except Exception:
            receipt['preservation_error'] = traceback.format_exc()
        receipt['status'] = 'TIMINGS_OBSERVED_NOT_REPAIR_OR_GATE1' if receipt['failure'] is None and receipt['preservation'] else 'PARTIAL_OR_BLOCKED_NO_RETRY'
        receipt['all_cases_passed'] = len(receipt['cases'])==len(CASES) and all(
            c['retrieval_passed'] and c['replay_passed'] for c in receipt['cases'])
        receipt['timing_observation_complete'] = receipt['failure'] is None and receipt['preservation']
        if receipt['timing_observation_complete'] and not receipt['all_cases_passed']:
            receipt['status']='TIMINGS_OBSERVED_CASE_FAILURES_NOT_REPAIR_OR_GATE1'
        save(attempt/'Timings.json', table)
        with (attempt/'Timings.md').open('x', encoding='utf-8') as stream:
            stream.write(timing_markdown(table))
        save(attempt/'Receipt.json', receipt)
    print(json.dumps({'status':receipt['status'],'receipt':str(attempt/'Receipt.json'),
                      'receipt_sha256':sha((attempt/'Receipt.json').read_bytes()),
                      'table':str(attempt/'Timings.md'),'cases':receipt['cases'],
                      'elapsed_wall_seconds':receipt['elapsed_wall_seconds'],'whole_skill_ready':False}))
    return 0 if receipt['failure'] is None and receipt['preservation'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true'); parser.add_argument('--verify', action='store_true')
    parser.add_argument('--run', action='store_true'); parser.add_argument('--sha256')
    parser.add_argument('--step', choices=('build','search','replay'))
    for name in ('source','fixture','target','pack','strategy','execution'):
        parser.add_argument('--'+name)
    args = parser.parse_args()
    if args.prepare:
        prepare(); return 0
    if args.step:
        step(args); return 0
    if args.verify:
        load_prepared(args.sha256); print('EXTENDED_INPUT_SEALS_MATCH_NO_WORKER_OR_ATTEMPT'); return 0
    if args.run:
        return run(args.sha256)
    parser.error('Select prepare, verify or run')


if __name__ == '__main__':
    raise SystemExit(main())
