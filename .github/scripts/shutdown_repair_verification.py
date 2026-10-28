"""SR3c sealed normal-account cleanup verification; never retries old attempts.

The coordinator is intentionally a small handoff layer.  It does not repair an
old receipt, loosen its historical inputs, or infer a successful workload from
a process list.  A normal-account invocation prepares one sealed contract and
may consume one fresh ``sr3-normal`` attempt only after every preflight record
is re-read.  The selected runtime is reached only by the copied, pinned tests.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import traceback

REPO = Path(__file__).absolute().parents[2]
ROOT = REPO / '.github/run-artifacts/cleanup-shutdown-repair-20261026'
BEFORE = ROOT / 'SR3-Before.json'
PARENT_INPUTS = ROOT / 'writer-handoff-green/Run-Inputs.json'
CONTRACT = ROOT / 'SR3-Inputs.json'
OUTPUT = ROOT / 'sr3-normal'
PREPARATION = ROOT / 'sr3-prepare'
CONTROLLER = Path(r'C:\Python314\python.exe')
HEAD = 'a38297dd797eeecd25e41ab0af1df4e3db8fa984'
NORMAL_SID = 'S-1-5-21-2571509308-2482563067-4170768140-1001'
SR2_OLD_DISTRIBUTED_SHA = 'f78ea987850a14229ec8750ac215dc121c54ee09413fc7330edd48ebad8dcde9'
C1_SHA = '5e1b06812949b72a8723844c4c1b7a8bde1b4fee645c43147e3352acb7696861'
FLAGS = ('stage_complete', 'gate1_complete', 'release_ready', 'installed',
         'producer_authentication', 'historical_c2_cause_proven')
BUDGETS = {'default': 120, 'public': 90, 'watchdog': 600, 'lifecycle_watchdog': 60, 'cleanup': 5}
# Exact read-only reviewed SR3 source and retained SR2/control bytes.
SEALED_SOURCES = {
    'memory-integrity/scripts/knowledge_bridge/distributed_retrieval.py': '423dd7eec705fe8f209336d6fc7aaba41b51d637ce2871a188578427c2906f32',
    'memory-integrity/scripts/knowledge_bridge/windows_owned_process.py': '07cddf0821323c5f0388653dda1102d1b46d1f02c20139c2be980f1c32bbe56a',
    'memory-integrity/scripts/knowledge_bridge/windows_owned_bootstrap.py': '9e7b2c7f2740244aa79d1dd69dd43eb3ae20b92d816b22bc4ea96bea28be3851',
    'memory-integrity/scripts/knowledge_bridge/windows_writer.py': '72dde9c3a495f0326bf95a1eef25e2eb81ac1333921889a8e48656840f475d29',
    'memory-integrity/scripts/knowledge_bridge/windows_job.py': '4b8631c9e4710ecb115e3d1ddb536a0f398a25ef1f7558bc21f527aa38137cb0',
    'memory-integrity/tests_v2/test_knowledge_windows_owned_process.py': '00c837f55f8527cefe361c5421155b2b8a4e51b177296506b9f249613eb223c4',
    'memory-integrity/tests_v2/test_knowledge_windows_session.py': '5b989dc3e7e0dfe3aa324caef1f7135cf7001ec4e9a10139a2965603f49852ee',
    'memory-integrity/tests_v2/test_knowledge_windows_writer.py': 'f3f89b80864a909abb704007db24503d475575365a79f02e64fef006cd969b62',
    'memory-integrity/tests_v2/test_knowledge_windows_shutdown.py': '86a8576e980a28fd062445e7d076917701befbdd6705e08efa22401ded98dbd7',
    'memory-integrity/tests_v2/test_knowledge_process_lifecycle.py': 'cccbb0f88b47b0a0d537e96cd320d25cc93f17ddd39d713a8869a1ca7367355b',
}
OLD_SEALS = {
    '.github/run-artifacts/cleanup-shutdown-repair-20261026/SR3-Before.json': '4da04f0fdb6b80ee0c79e1cdc4802f0bd73c9dd7f2fdf7e0e9c10ac04c1e745f',
    '.github/run-artifacts/cleanup-shutdown-repair-20261026/writer-handoff-green/Run-Inputs.json': '5bc5788cd7a21af47e3a305bd3352b27a4cead6ae46d22dbce9eb748aef6f1ed',
    '.github/run-artifacts/cleanup-repair-20261023/Runtime-Inputs.json': '18b1d93425f0f52965b94ed7349acf11042065348aafc26b8152ce7c6b595838',
    '.github/run-artifacts/cleanup-lifetime-stack-20261024/Inputs.json': 'ead95373d25ee2750a10c52e4e2bbf7cf3cabb087166b00df2533458bec27075',
    '.github/run-artifacts/cleanup-process-timing-20261024/Inputs.json': 'cf45dfde1fae5d2bb5f601a8d54c4fa68e62d5db35e3248ffe9bdfecf9476d62',
    '.github/run-artifacts/cleanup-membership-20261025/Inputs.json': '457fc256b81f52572695b787344cd5778f3bd06bdc14939b5416508ceeacf5a4',
}

# This is the only live production delta allowed into the fresh committed copy.
# It is recorded in Inputs.json after all parent-owned sources have stabilised;
# no old helper, old copy, cache, or consumed attempt is copied or edited.
LIVE_DELTA = (
    'memory-integrity/scripts/knowledge_bridge/distributed_retrieval.py',
    'memory-integrity/scripts/knowledge_bridge/windows_owned_process.py',
    'memory-integrity/scripts/knowledge_bridge/windows_owned_bootstrap.py',
    'memory-integrity/scripts/knowledge_bridge/windows_writer.py',
    'memory-integrity/scripts/knowledge_bridge/windows_job.py',
    'memory-integrity/tests_v2/test_knowledge_windows_owned_process.py',
    'memory-integrity/tests_v2/test_knowledge_windows_session.py',
    'memory-integrity/tests_v2/test_knowledge_windows_writer.py',
    'memory-integrity/tests_v2/test_knowledge_windows_shutdown.py',
    'memory-integrity/tests_v2/test_knowledge_process_lifecycle.py',
)
GROUPS = (
    ('ownership', 'test_knowledge_windows_owned_process.py', 60),
    ('writer', 'test_knowledge_windows_writer.py', 60),
    ('combined-shutdown', 'test_knowledge_windows_shutdown.py', 60),
    ('combined-session', 'test_knowledge_windows_session.py', 60),
    ('lifecycle', 'test_knowledge_process_lifecycle.py', 60),
    ('cwd', 'test_knowledge_worker_cwd.py', 60),
    ('budget', 'test_knowledge_timeout_budget.py', 60),
)
HISTORY_ROOTS = (
    REPO / '.github/run-artifacts/cleanup-repair-20261023',
    REPO / '.github/run-artifacts/cleanup-process-timing-20261024',
    REPO / '.github/run-artifacts/cleanup-lifetime-stack-20261024',
    REPO / '.github/run-artifacts/cleanup-membership-20261025',
)
SUPPORT = (
    '.github/scripts/gate1_current_preflight.py',
    '.github/scripts/gate1_current_runtime.py',
    '.github/scripts/gate1_validation.py',
    '.github/scripts/offline_host_validation.py',
    '.github/scripts/gate1_ordered_runner.py',
    '.github/scripts/gate1_ordered_diagnostic.py',
    '.github/scripts/retained_unittest.py',
)
SUPPORT_SEALS = {
    '.github/scripts/gate1_current_preflight.py': '5e1b06812949b72a8723844c4c1b7a8bde1b4fee645c43147e3352acb7696861',
    '.github/scripts/gate1_current_runtime.py': '42ee6ee502ac9b4dc742fa6c9a0a70d56fc04600f1d24800f65ace32db56989f',
    '.github/scripts/gate1_validation.py': 'f9b7ef54039756b3d8a95051b05a93e920518c970e6deb1c987bc5bb0aeed22e',
    '.github/scripts/offline_host_validation.py': '1333833623bdc1f5a6f31230b530b121c40bbb3d6c244dccc695022082e33b9f',
    '.github/scripts/gate1_ordered_runner.py': '23f67d1ddaa543071857a773a2917df86967a9d14a5d600408763f6f2a8c81b8',
    '.github/scripts/gate1_ordered_diagnostic.py': '1797c2fb1753704fb675e5d37388b37a3b267f9c8debb6f77647cfafaee506ca',
    '.github/scripts/retained_unittest.py': '4aba6fe49641f86dcb548219f0c6efc8bbd2fbaa4e32f5be40703a1cee18453b',
}
DISCOVERY_SCRIPT = '''import json
import sys
import unittest
root, pattern = sys.argv[1:]
sys.path.insert(0, root)
suite = unittest.defaultTestLoader.discover(root + '/tests_v2', pattern=pattern)
def flatten(group):
    for item in group:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item.id()
print(json.dumps(list(flatten(suite))))
'''


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ordinary(path):
    """Reject redirected input and output paths before a byte is read/written."""
    path = Path(path)
    for part in (path, *path.parents):
        item = part.lstat()
        require(not stat.S_ISLNK(item.st_mode) and not getattr(item, 'st_file_attributes', 0) & 0x400,
                'E_SR3_REDIRECTED_PATH: ' + str(part))
    return path


def record(path):
    path = ordinary(path)
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'E_SR3_INPUT_LINK: ' + str(path))
    raw = path.read_bytes()
    require(path.stat().st_size == len(raw), 'E_SR3_INPUT_CHANGED: ' + str(path))
    return {'path': str(path), 'size': len(raw), 'sha256': sha(raw), 'links': 1}


def read_json(path):
    raw = ordinary(path).read_bytes()
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('E_SR3_JSON: ' + str(path)) from error


def save(path, value):
    ordinary(Path(path).parent)
    with Path(path).open('xb') as stream:
        stream.write((json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False) + '\n').encode('utf-8'))


def load_module(path, expected):
    row = record(path)
    require(row['sha256'] == expected['sha256'] and row['size'] == expected['size'],
            'E_SR3_SUPPORT_CHANGED: ' + str(path))
    spec = importlib.util.spec_from_file_location('sr3_' + Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    raw = ordinary(path).read_bytes()
    require(sha(raw) == expected['sha256'] and len(raw) == expected['size'], 'E_SR3_SUPPORT_CHANGED: '+str(path))
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def validate_budgets(value):
    require(value == BUDGETS and all(type(value[key]) is int for key in BUDGETS), 'E_SR3_BUDGET')


def group_plan():
    return [list(group) for group in GROUPS]


def test_argv(worker, runner, source, pattern, output):
    return [worker, '-B', runner, '--package-root', source/'memory-integrity',
            '--pattern', pattern, '--output-dir', output]


def validate_source_seals(rows):
    require(SEALED_SOURCES and set(rows) == set(SEALED_SOURCES) and
            all(rows[name]['sha256'] == digest for name, digest in SEALED_SOURCES.items()),
            'E_SR3_UNREVIEWED_SOURCE')


def validate_support_seals(rows):
    require(set(rows) == set(SUPPORT_SEALS) and
            all(rows[name]['sha256'] == digest for name,digest in SUPPORT_SEALS.items()), 'E_SR3_SUPPORT_SEAL')


def validate_protected_delta(old, current, allowed):
    changed = {name for name in set(old)|set(current) if old.get(name) != current.get(name)}
    require(not set(old)-set(current) and changed <= set(allowed), 'E_SR3_UNAPPROVED_PROTECTED_DELTA')


def validate_capture(completed, row, exits=(0,)):
    """A complete nonzero child is evidence; a lost capture never is."""
    containment = row.get('containment') or {}
    code = row.get('exit_code')
    require(completed is not None and type(code) is int and type(completed.returncode) is int and
            completed.returncode == code and row.get('execution') == 'EXITED' and row.get('failure') is None and
            containment.get('timed_out') is False and containment.get('capture_complete') is True and
            containment.get('tree_contained') is True and containment.get('capture_errors') == [] and
            containment.get('output_limit_exceeded') is False, 'E_SR3_CAPTURE_INCOMPLETE')
    require(code in exits, 'E_SR3_CHILD_EXIT: ' + str(code))


def validate_suite(receipt, expected_ids):
    """Discovery and results must be exact; skips/exclusions are not an escape hatch."""
    require(isinstance(receipt, dict) and isinstance(expected_ids, (tuple, list)), 'E_SR3_SUITE_SCHEMA')
    discovered = receipt.get('discovered')
    run = receipt.get('tests_run')
    require(type(discovered) is int and type(run) is int and run == discovered == len(expected_ids) and
            len(expected_ids) == len(set(expected_ids)) and all(isinstance(name, str) and name for name in expected_ids) and
            all(receipt.get(key) == [] for key in ('failures', 'errors', 'skipped', 'excluded', 'expected_failures')) and
            receipt.get('interrupted') is False, 'E_SR3_SUITE_ACCOUNTING')


def validate_discovery(value, pattern):
    """Exact unittest IDs are captured from the copied source, never assumed."""
    require(isinstance(value, list) and value and len(value) == len(set(value)) and
            all(isinstance(item, str) and item.startswith('test_') and '.test_' in item for item in value),
            'E_SR3_DISCOVERY_SOURCE: ' + pattern)
    return tuple(value)


def validate_ordered(report, unit, runner):
    """The immutable ordered observer supplies the method grammar and result."""
    state = runner.validate_ordered_result(report)
    require(state == 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE', 'E_SR3_ORDERED_RESULT')
    validate_suite(unit, (runner.TARGET,))
    require(report.get('gate1_complete') is False and report.get('observation_only') is True,
            'E_SR3_ORDERED_SCOPE')
    return state


def validate_stage(groups, preservation, ordered=False):
    """Focused stage may close only after every observed group and both inventories pass."""
    require(isinstance(groups, list) and preservation is True and ordered is True and
            [row.get('label') for row in groups] == [row[0] for row in GROUPS], 'E_SR3_STAGE_PRECONDITION')
    for row in groups:
        require(row.get('passed') is True and row.get('receipt') and row.get('cases'), 'E_SR3_STAGE_GROUP')
    return True


def history(c1):
    """Full traversal is mandatory: access denial raises rather than silently skipping."""
    for name, digest in OLD_SEALS.items():
        require(record(REPO/name)['sha256'] == digest, 'E_SR3_OLD_SEAL: '+name)
    rows = {str(root): c1.source_manifest(root) for root in HISTORY_ROOTS}
    before = read_json(BEFORE)
    require(before.get('head') == HEAD and isinstance(before.get('files'), dict), 'E_SR3_BEFORE_SCHEMA')
    old_distributed = before['files'].get('memory-integrity/scripts/knowledge_bridge/distributed_retrieval.py')
    require(isinstance(old_distributed, dict) and old_distributed.get('sha256') == SR2_OLD_DISTRIBUTED_SHA,
            'E_SR3_OLD_DISTRIBUTED_BASIS')
    parent = read_json(PARENT_INPUTS)
    require(parent.get('head') == HEAD and parent.get('scope') ==
            'SR2_ISOLATED_WRITER_PARENT_READBACK_NOT_AUTHENTICATED_PRODUCER', 'E_SR3_PARENT_SCHEMA')
    require(all(parent[key] is False for key in ('selected312_started','retrieval_integrated','stage_complete',
            'gate1_complete','release_ready','installed')), 'E_SR3_PARENT_FLAGS')
    for name, expected in parent['files'].items():
        path = Path(name) if Path(name).is_absolute() else REPO/name
        actual = record(path)
        require(all(actual[key] == expected[key] for key in ('size','sha256')), 'E_SR3_PARENT_FILE: '+name)
    for expected in parent['receipts'].values():
        path = REPO/expected['path']; actual = record(path); unit = read_json(path)
        require(actual['sha256'] == expected['sha256'] and unit['log_sha256'] == expected['log_sha256'] and
                record(Path(unit['log']))['sha256'] == expected['log_sha256'] and
                unit['tests_run'] == expected['tests_run'] and len(unit['failures']) == expected['failure_count'] and
                len(unit['errors']) == expected['error_count'] and len(unit['skipped']) == expected['skip_count'],
                'E_SR3_PARENT_RECEIPT')
    controls = parent.get('unchanged_controls')
    require(isinstance(controls, dict) and controls, 'E_SR3_OLD_CONTROLS')
    # The former distributed source is a declared SR3 production delta.  Its
    # historical digest is retained in parent inputs but may not be demanded of
    # the corrected current copy.
    for name, digest in controls.items():
        if name == 'memory-integrity/scripts/knowledge_bridge/distributed_retrieval.py':
            require(digest == SR2_OLD_DISTRIBUTED_SHA, 'E_SR3_OLD_DISTRIBUTED_PARENT')
            continue
        require(record(REPO / name)['sha256'] == digest, 'E_SR3_OLD_CONTROL_CHANGED: ' + name)
    # Preserve the old chain's positive inventories, not just freshly observed
    # hashes. Only explicitly reviewed live source deltas may differ.
    cr = read_json(REPO/'.github/run-artifacts/cleanup-repair-20261023/Runtime-Inputs.json')
    ld = read_json(REPO/'.github/run-artifacts/cleanup-lifetime-stack-20261024/Inputs.json')
    tc = read_json(REPO/'.github/run-artifacts/cleanup-process-timing-20261024/Inputs.json')
    mp = read_json(REPO/'.github/run-artifacts/cleanup-membership-20261025/Inputs.json')
    require(rows[str(HISTORY_ROOTS[1])] == mp['timing_inventory'] and
            rows[str(HISTORY_ROOTS[2])] == tc['stack_inventory'], 'E_SR3_OLD_INVENTORY')
    require(c1.source_manifest(Path(ld['failed_receipt']['path']).parent) == ld['failed_inventory'], 'E_SR3_CR3_INVENTORY')
    c1.verify_source(Path(ld['source']), tc['source_manifest'])
    require(c1.source_manifest(c1.OUTPUT) == cr['c1_inventory'] and c1.fixed_inputs() == cr['runtime'], 'E_SR3_C1_INVENTORY')
    c1.verify_source(c1.OUTPUT/'source', cr['source'])
    for expected in cr['history'].values():
        require(record(Path(expected['path'])) == expected, 'E_SR3_EXTERNAL_HISTORY')
    protected = c1.protected()
    require(set(protected) == set(cr['protected']), 'E_SR3_PROTECTED_ROOTS')
    for root, old in cr['protected'].items():
        allowed = {name.removeprefix('memory-integrity/') for name in LIVE_DELTA} if root == str(REPO/'memory-integrity') else set()
        current = protected[root]
        validate_protected_delta(old, current, allowed)
    return {'before': record(BEFORE), 'parent_inputs': record(PARENT_INPUTS),
            'old_controls': dict(controls), 'inventories': rows, 'protected': protected}


def verify_history(c1, expected):
    require(history(c1) == expected, 'E_SR3_HISTORY_CHANGED')


def source_basis(c1):
    require(c1.git('rev-parse', 'HEAD').decode().strip() == HEAD, 'E_SR3_HEAD')
    tree = {}
    for row in c1.git('ls-tree', '-rz', HEAD).split(b'\0'):
        if not row:
            continue
        meta, name = row.split(b'\t', 1)
        mode, kind, blob = meta.split()
        require(mode == b'100644' and kind == b'blob', 'E_SR3_TREE_MODE')
        tree[name.decode('utf-8')] = blob.decode('ascii')
    rows = c1.archive_rows(c1.git('archive', '--format=zip', HEAD), tree)
    return {name: sha(data) for name, data in rows.items()}, tree


def support_records():
    rows = {name: record(REPO / name) for name in SUPPORT}
    validate_support_seals(rows)
    return rows


def build_contract(c1):
    c1.normal_account()
    require(not os.path.lexists(CONTRACT) and not os.path.lexists(OUTPUT), 'E_SR3_EXISTING_ATTEMPT')
    manifest, tree = source_basis(c1)
    require(record(REPO/'semantica-runtime/requirements-lock.txt')['sha256'] ==
            manifest['semantica-runtime/requirements-lock.txt'], 'E_SR3_DEPENDENCY_LOCK_CHANGED')
    delta = {name: record(REPO / name) for name in LIVE_DELTA}
    validate_source_seals(delta)
    fixed = c1.fixed_inputs()
    require(record(CONTROLLER)['sha256'] == fixed[str(Path(sys.executable))]['sha256'], 'E_SR3_CONTROLLER')
    value = {'schema': 1, 'scope': 'SR3_FOCUSED_NORMAL_ACCOUNT_CLEANUP_NOT_GATE1', 'head': HEAD,
             'root': str(ROOT), 'output': str(OUTPUT), 'controller': record(CONTROLLER),
             'helper': record(Path(__file__).absolute()), 'source_manifest': manifest, 'tree': tree,
             'live_delta': delta, 'support': support_records(), 'fixed_inputs': fixed,
             'dependencies': c1.dependency_versions(), 'history': history(c1), 'groups': group_plan(),
             'budgets': BUDGETS, **dict.fromkeys(FLAGS, False)}
    validate_contract(c1, value)
    return value


def validate_contract(c1, value):
    keys = {'schema', 'scope', 'head', 'root', 'output', 'controller', 'helper', 'source_manifest', 'tree',
            'live_delta', 'support', 'fixed_inputs', 'dependencies', 'history', 'groups', 'budgets', *FLAGS}
    require(isinstance(value, dict) and set(value) == keys and value['schema'] == 1 and
            value['scope'] == 'SR3_FOCUSED_NORMAL_ACCOUNT_CLEANUP_NOT_GATE1' and value['head'] == HEAD and
            value['root'] == str(ROOT) and value['output'] == str(OUTPUT) and
            all(value[key] is False for key in FLAGS), 'E_SR3_CONTRACT_SCHEMA')
    validate_budgets(value['budgets'])
    require(value['helper'] == record(Path(__file__).absolute()) and value['controller'] == record(CONTROLLER),
            'E_SR3_COORDINATOR_CHANGED')
    require(value['support'] == support_records(), 'E_SR3_SUPPORT_CHANGED')
    require(value['fixed_inputs'] == c1.fixed_inputs() and value['dependencies'] == c1.dependency_versions(),
            'E_SR3_FIXED_INPUT_CHANGED')
    manifest, tree = source_basis(c1)
    require(value['source_manifest'] == manifest and value['tree'] == tree and
            value['live_delta'] == {name: record(REPO / name) for name in LIVE_DELTA}, 'E_SR3_SOURCE_CHANGED')
    validate_source_seals(value['live_delta'])
    require(value['groups'] == group_plan(), 'E_SR3_GROUPS')
    verify_history(c1, value['history'])


def copy_source(c1, value, destination):
    require(not os.path.lexists(destination), 'E_SR3_COPY_EXISTS')
    rows = c1.archive_rows(c1.git('archive', '--format=zip', HEAD), value['tree'])
    destination.mkdir(); ordinary(destination)
    manifest = {name: sha(data) for name, data in rows.items()}
    for name, data in rows.items():
        path = destination / name; path.parent.mkdir(parents=True, exist_ok=True); ordinary(path.parent)
        with path.open('xb') as stream:
            stream.write(data)
    for name, row in value['live_delta'].items():
        path = destination / name; path.parent.mkdir(parents=True, exist_ok=True); ordinary(path.parent)
        data = (REPO / name).read_bytes()
        require(sha(data) == row['sha256'], 'E_SR3_DELTA_CHANGED: ' + name)
        with path.open('wb' if path.exists() else 'xb') as stream:
            stream.write(data)
        manifest[name] = sha(data)
    c1.verify_source(destination, manifest)
    return manifest


def environment(c2, temp):
    value = c2.environment(temp)
    value.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1',
                 TRANSFORMERS_OFFLINE='1')
    for key in ('PYTHONPATH', 'PYTHONHOME', 'MODEL_PYTHON', 'KNOWLEDGE_MODEL_MANIFEST'):
        value.pop(key, None)
    return value


def run(digest):
    # Read a sealed contract using only local fail-closed primitives before
    # importing a support module.  The old C1 helper is then imported against
    # its contract record, never against a freshly observed replacement.
    require(sha(ordinary(CONTRACT).read_bytes()) == digest, 'E_SR3_EXTERNAL_CONTRACT')
    value = read_json(CONTRACT)
    c1 = load_module(REPO / '.github/scripts/gate1_current_preflight.py',
                     value['support']['.github/scripts/gate1_current_preflight.py'])
    c1.normal_account()  # Wrong account and bad seals create no output or marker.
    validate_contract(c1, value)
    require(not os.path.lexists(OUTPUT), 'E_SR3_EXISTING_ATTEMPT')
    ordinary(OUTPUT.parent); OUTPUT.mkdir(); ordinary(OUTPUT)
    receipt = {'scope': value['scope'], 'status': 'PARTIAL_OR_FAILED_NO_RETRY', 'head': HEAD,
               'started_utc': datetime.now(timezone.utc).isoformat(), 'contract': record(CONTRACT),
               'commands': [], 'groups': [], 'failure': None, 'preservation': False,
               **dict.fromkeys(FLAGS, False)}
    copied = copy_manifest = None
    try:
        host = load_module(REPO / '.github/scripts/offline_host_validation.py', value['support']['.github/scripts/offline_host_validation.py'])
        c2 = load_module(REPO / '.github/scripts/gate1_current_runtime.py', value['support']['.github/scripts/gate1_current_runtime.py'])
        g = load_module(REPO / '.github/scripts/gate1_validation.py', value['support']['.github/scripts/gate1_validation.py'])
        temp = OUTPUT / 'temp'; temp.mkdir(); env = environment(c2, temp)
        def capture(label, argv, timeout, exits=(0,)):
            target = OUTPUT / label; target.mkdir(); ordinary(target)
            print(label+': RUNNING (SR3 focused verification, not Gate1)', flush=True)
            completed, row = host.capture_owned(list(map(str, argv)), target, target, env, timeout)
            row['label'] = label; receipt['commands'].append(row)
            validate_capture(completed, row, exits)
            return completed
        identity = capture('preclaim-identity', [g.WORKER, '-B', '-c', g.runtime_probe()], 30)
        c1.validate_runtime(json.loads(identity.stdout), env, OUTPUT / 'preclaim-identity')
        dep = "import importlib.metadata as m,json,site;d=m.distribution('semantica');u=json.loads(d.read_text('direct_url.json') or '{}');print(json.dumps({'versions':{n:m.version(n) for n in " + repr(sorted(value['dependencies'])) + "},'revision':u.get('vcs_info',{}).get('commit_id'),'user_site':site.ENABLE_USER_SITE}))"
        deps = capture('preclaim-dependencies', [g.WORKER, '-B', '-c', dep], 30)
        c1.validate_dependencies(json.loads(deps.stdout), value['dependencies'])
        validate_contract(c1, value)
        copied = OUTPUT / 'source'; copy_manifest = copy_source(c1, value, copied)
        save(OUTPUT / 'workload-claim.json', {'scope': value['scope'], 'head': HEAD, 'one_attempt': True})
        for label, pattern, timeout in value['groups']:
            discovery = capture('discover-' + label, [g.WORKER, '-B', '-c', DISCOVERY_SCRIPT,
                copied / 'memory-integrity', pattern], timeout)
            expected = validate_discovery(json.loads(discovery.stdout), pattern)
            folder = OUTPUT / ('tests-' + label)
            capture('command-' + label, test_argv(g.WORKER, copied / '.github/scripts/retained_unittest.py',
                    copied, pattern, folder), timeout)
            unit = read_json(folder / 'Receipt.json')
            validate_suite(unit, expected)
            require(record(Path(unit['log']))['sha256'] == unit['log_sha256'], 'E_SR3_UNIT_LOG')
            case_path = OUTPUT / ('group-' + label + '-Discovery.json')
            save(case_path, {'pattern': pattern, 'ids': list(expected)})
            receipt['groups'].append({'label': label, 'pattern': pattern, 'passed': True,
                                      'receipt': record(folder / 'Receipt.json'), 'cases': record(case_path)})
            verify_history(c1, value['history']); c1.verify_source(copied, copy_manifest)
        # Retained public method: its own fixed 90s public and 600s watchdog rules are not reimplemented here.
        ordered = copied / '.github/scripts/gate1_ordered_runner.py'
        capture('ordered-public', [g.WORKER, '-B', ordered, '--package-root', copied / 'memory-integrity',
                '--pattern', 'test_knowledge_completion.py', '--output-dir', OUTPUT / 'ordered'], BUDGETS['watchdog'])
        runner = load_module(ordered, value['support']['.github/scripts/gate1_ordered_runner.py'])
        ordered_report = read_json(OUTPUT / 'ordered/Ordered-Outcomes.json')
        ordered_unit = read_json(OUTPUT / 'ordered/Receipt.json')
        diagnostic = load_module(copied/'.github/scripts/gate1_ordered_diagnostic.py', value['support']['.github/scripts/gate1_ordered_diagnostic.py'])
        diagnostic.verify_calls(ordered_report, OUTPUT/'ordered')
        diagnostic.validate_unit_receipt(ordered_unit, 0, ordered_report)
        require(record(Path(ordered_unit['log']))['sha256'] == ordered_unit['log_sha256'], 'E_SR3_ORDERED_LOG')
        receipt['ordered'] = {'state': validate_ordered(ordered_report, ordered_unit, runner),
                              'receipt': record(OUTPUT / 'ordered/Receipt.json'),
                              'outcomes': record(OUTPUT / 'ordered/Ordered-Outcomes.json')}
        # Re-attest the actual selected runtime after work as well; unchanged
        # executable/config hashes alone do not prove installed metadata stayed
        # consistent during the observed lifecycle/public methods.
        identity = capture('postclaim-identity', [g.WORKER, '-B', '-c', g.runtime_probe()], 30)
        c1.validate_runtime(json.loads(identity.stdout), env, OUTPUT/'postclaim-identity')
        deps = capture('postclaim-dependencies', [g.WORKER, '-B', '-c', dep], 30)
        c1.validate_dependencies(json.loads(deps.stdout), value['dependencies'])
        verify_history(c1, value['history']); c1.verify_source(copied, copy_manifest)
        receipt['preservation'] = True
        receipt['stage_complete'] = validate_stage(receipt['groups'], receipt['preservation'], True)
        receipt['status'] = 'SR3_FOCUSED_CLEANUP_STAGE_COMPLETE_NOT_GATE1'
    except BaseException:
        receipt['failure'] = traceback.format_exc()
    finally:
        try:
            validate_contract(c1, value)
            if copied is not None:
                require(copy_manifest is not None, 'E_SR3_PARTIAL_COPY_RETAINED')
                c1.verify_source(copied, copy_manifest)
            receipt['preservation'] = True
        except BaseException:
            receipt['preservation_failure'] = traceback.format_exc()
            receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
            receipt['stage_complete'] = False
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save(OUTPUT / 'Receipt.json', receipt)
    print(json.dumps({'status': receipt['status'], 'receipt': record(OUTPUT / 'Receipt.json'),
                      'failure': receipt['failure'], **{key: receipt[key] for key in FLAGS}}))
    return 0 if receipt['status'] == 'SR3_FOCUSED_CLEANUP_STAGE_COMPLETE_NOT_GATE1' else 1


def prepare():
    c1 = load_module(REPO / '.github/scripts/gate1_current_preflight.py',
                     {'sha256': C1_SHA, 'size': record(REPO / '.github/scripts/gate1_current_preflight.py')['size']})
    c1.normal_account()  # Refuse the wrong account before consuming preparation.
    require(not os.path.lexists(PREPARATION), 'E_SR3_PREPARATION_CONSUMED')
    ordinary(ROOT); PREPARATION.mkdir(); ordinary(PREPARATION)
    save(PREPARATION/'Claim.json', {'scope':'SR3_INPUTS_ONLY_NOT_WORKLOAD', 'started_utc':datetime.now(timezone.utc).isoformat()})
    try:
        value = build_contract(c1)
        save(CONTRACT, value)
    except BaseException:
        save(PREPARATION/'Failure.json', {'status':'PREPARATION_FAILED_NO_RETRY_NO_WORKLOAD',
            'failure':traceback.format_exc(), 'stage_complete':False, 'gate1_complete':False})
        raise
    print(json.dumps({'status': 'SR3_INPUTS_ONLY_NO_SELECTED_RUNTIME_OR_WORKLOAD', 'contract': record(CONTRACT)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare', action='store_true')
    action.add_argument('--sha256')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    else:
        raise SystemExit(run(args.sha256))
