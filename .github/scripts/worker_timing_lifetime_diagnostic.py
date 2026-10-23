"""W1-W3 isolated timing/lifetime diagnosis. No worker fix or qualification.

Prepare never starts selected Python. Run requires an external Prepared seal,
normal account, full historical preservation and actual image preclaim checks.
"""
import argparse
import contextlib
import functools
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import traceback

import worker_diagnostic_events as events

HERE = Path(__file__).absolute()
REPO = HERE.parents[2]
ARTIFACTS = REPO / '.github/run-artifacts/offline-first-20261020'
PRIVATE = ARTIFACTS / 'worker-diagnosis-20261022'
SEAL = PRIVATE / 'Input-Seal.json'
WORKSPACE = Path(r'C:\Users\sakth\Documents\Codex\gate1-923de16-20261021')
OUT = WORKSPACE / 'worker-observe1-20261022'
SOURCES = [WORKSPACE / 'wrkbas', WORKSPACE / 'wrkobs']
HEAD = '923de16c91a9ef4381e7ac975e3a3780f42a4bf5'
OLD_V3_SHA = '48668b273c4b24e4248570ad1197cd2e5e8490d550640e1d4a75dc5bf0eea825'
OLD_RESULT_SHA = '14c350e4fa63561ecf794cf1aa06e05f18d84fa779dd2d39789180d93901be28'
CURRENT_ORDERED_SHA = '1797c2fb1753704fb675e5d37388b37a3b267f9c8debb6f77647cfafaee506ca'
OLD_DRIVER_SHA = '0334cfc8cde32f272fcae9af5d7c990af1dac35656ca6a0f3336018050f32645'
FLAGS = ('producer_authentication', 'cause_proven', 'fix_validated', 'gate1_complete',
         'release_ready', 'installed', 'native_execution', 'whole_skill_ready', 'retry_authorized')
LAUNCHER = PRIVATE / 'Run-Worker-Diagnosis.ps1'
SCRIPT_NAMES = ('worker_timing_lifetime_diagnostic.py', 'worker_diagnostic_events.py',
                'worker_lock_probe.py', 'gate1_ordered_diagnostic.py', 'gate1_ordered_runner.py',
                'retained_unittest.py', 'gate1_runner.py', 'gate1_validation.py',
                'gate1_image_successor.py', 'gate1_cleanup_diagnostic.py',
                'offline_host_validation.py', 'offline_release_acceptance.py')


@contextlib.contextmanager
def readonly_python():
    """Scoped inherited guard, including real legacy companion child calls."""
    names = ('PYTHONDONTWRITEBYTECODE', 'PYTHONNOUSERSITE')
    prior = {key: os.environ.get(key) for key in names}
    bytecode = sys.dont_write_bytecode
    try:
        os.environ.update({key: '1' for key in names})
        sys.dont_write_bytecode = True
        yield
    finally:
        sys.dont_write_bytecode = bytecode
        for key, value in prior.items():
            if value is None: os.environ.pop(key, None)
            else: os.environ[key] = value


def read_only(function):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        with readonly_python(): return function(*args, **kwargs)
    return wrapped


def required_files():
    paths = [HERE.with_name(name) for name in SCRIPT_NAMES]
    paths += [REPO / '.github/tests/test_worker_timing_lifetime_diagnostic.py',
              Path(r'C:\Python314\python.exe'),
              REPO.parent / 'build-validation/n3-retrieval-9ec6fb1db36444acba2945896e8b8d17/venv/Scripts/python.exe',
              REPO.parent / 'build-validation/n3-retrieval-9ec6fb1db36444acba2945896e8b8d17/venv/pyvenv.cfg',
              WORKSPACE / 'Prepared.json', ARTIFACTS / 'Gate1-Image-Contract-20261021.json',
              ARTIFACTS / 'Gate1-Cleanup-Diagnostic-Contract-20261021.json',
              ARTIFACTS / 'Gate1-Ordered-Contract-20261021-v3.json',
              ARTIFACTS / 'ordered-consumed-v3/gate1_ordered_diagnostic.py']
    paths += [REPO / 'memory-integrity/scripts/knowledge_bridge' / role for role in events.SOURCE_PINS]
    return set(map(str, paths))


def seal_template():
    """Schema sample only. Zero digests cannot pass verify_own_seal byte checks."""
    return {'scope': 'W1_W3_DIAGNOSIS_ONLY', 'head': HEAD, 'output': str(OUT),
            'sources': list(map(str, SOURCES)), **{key: False for key in FLAGS},
            'files': {name: {'path': name, 'size': 0, 'sha256': '0'*64} for name in sorted(required_files())},
            'launcher_template': {'path': str(LAUNCHER), 'size': 0, 'sha256': '0'*64}}


def validate_record(value, path):
    return (isinstance(value, dict) and set(value) == {'path', 'size', 'sha256'} and
            value['path'] == str(path) and Path(value['path']).is_absolute() and
            type(value['size']) is int and value['size'] >= 0 and
            isinstance(value['sha256'], str) and len(value['sha256']) == 64 and
            all(c in '0123456789abcdef' for c in value['sha256']))


def validate_seal(value):
    require(isinstance(value, dict) and set(value) == set(seal_template()) and
            value['scope'] == 'W1_W3_DIAGNOSIS_ONLY' and value['head'] == HEAD and
            value['output'] == str(OUT) and value['sources'] == list(map(str, SOURCES)) and
            all(value[key] is False for key in FLAGS) and isinstance(value['files'], dict) and
            set(value['files']) == required_files() and
            all(validate_record(row, name) for name, row in value['files'].items()) and
            validate_record(value['launcher_template'], LAUNCHER), 'E_W_SEAL_SCHEMA')


def launcher_record():
    # Avoid a circular seal: external launcher hash binds its literal seal SHA;
    # the seal independently binds the exact launcher template with just that
    # ONE 64-character digest normalized. No arbitrary script mutation allowed.
    import re
    raw = checked_bytes(LAUNCHER)
    normalized, count = re.subn(rb"\$wdSealSha = '[0-9a-f]{64}'", b"$wdSealSha = '<INPUT_SEAL_SHA256>'", raw)
    require(count == 1, 'E_W_LAUNCHER_TEMPLATE')
    return {'path': str(LAUNCHER), 'size': len(normalized), 'sha256': digest(normalized)}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_bytes(path, limit=33554432):
    path = events.ordinary(Path(path))
    before = path.stat()
    require(path.is_file() and before.st_nlink == 1 and before.st_size <= limit, 'E_W_FILE')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino), 'E_W_REPLACED_INPUT')
        raw = stream.read(limit + 1)
    after = events.ordinary(path).stat()
    identity = lambda row: (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns, row.st_nlink)
    require(identity(before) == identity(after) and len(raw) <= limit, 'E_W_REPLACED_INPUT')
    return raw


def record(path):
    raw = checked_bytes(path)
    return {'path': str(path), 'size': len(raw), 'sha256': digest(raw)}


def read_sealed(path, sha):
    raw = checked_bytes(path)
    require(isinstance(sha, str) and len(sha) == 64 and digest(raw) == sha, 'E_W_EXTERNAL_SEAL')
    return json.loads(raw.decode('utf-8'))


def save(path, value):
    path = Path(path)
    events.ordinary(path.parent)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, sort_keys=True, ensure_ascii=True) + '\n').encode('utf-8'))


def legacy():
    path = HERE.with_name('gate1_ordered_diagnostic.py')
    raw = checked_bytes(path)
    require(digest(raw) == CURRENT_ORDERED_SHA, 'E_W_ACCOUNTING_CHANGED')
    spec = importlib.util.spec_from_file_location('w_sealed_ordered_accounting', path)
    result = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), result.__dict__)
    return result


def guarded_claim(history_check, target):
    history_check()  # Deliberately before even creating a claim directory.
    target = Path(target)
    events.ordinary(target.parent)
    target.mkdir()  # Existing/redirected paths are never removed or reused.
    events.ordinary(target)
    return target


def diagnosis_result(failures, observer_complete):
    return {'status': ('DIAGNOSTIC_INCOMPLETE' if not observer_complete else
                       'OBSERVATIONS_RECORDED_CAUSES_REQUIRE_REVIEW' if failures else
                       'FAILURE_NOT_REPRODUCED_INCONCLUSIVE'),
            'failures_observed': failures, **{key: False for key in FLAGS}}


def overlay_copy(source):
    require(Path(source) == SOURCES[1], 'E_W_COPY_SCOPE')
    source = events.ordinary(Path(source))
    folder = source / 'memory-integrity/scripts/knowledge_bridge'
    manifest = {}
    for role, sha in events.SOURCE_PINS.items():
        target = folder / role
        raw = checked_bytes(target)
        observed = events.diagnostic_source(raw, sha, role)
        # Only generated files in this exclusive NEW copy may be rewritten.
        with target.open('wb') as stream:
            stream.write(observed)
        manifest[target.relative_to(source).as_posix()] = digest(observed)
    target = folder / '_worker_diag_v1.py'
    with target.open('xb') as stream:
        stream.write(checked_bytes(HERE.with_name('worker_diagnostic_events.py')))
    manifest[target.relative_to(source).as_posix()] = record(target)['sha256']
    return manifest


def method_record(commands, label):
    matches = [row for row in commands if row.get('label') == label]
    require(len(matches) == 1, 'E_W_CAPTURE_ROLE')
    return matches[0]


def verify_historical_record(row, ordered):
    """One explicit code transition, never an arbitrary historical-pin waiver."""
    if row['path'] == str(ordered.HERE) and row['sha256'] == OLD_DRIVER_SHA:
        archive = ARTIFACTS / 'ordered-consumed-v3/gate1_ordered_diagnostic.py'
        archived = record(archive)
        require((archived['size'], archived['sha256']) == (row['size'], OLD_DRIVER_SHA) and
                record(ordered.HERE)['sha256'] == CURRENT_ORDERED_SHA, 'E_W_ACCOUNTING_HISTORY_TRANSITION')
        return {'historical_path': row['path'], 'archived_bytes': archived,
                'current_bytes': record(ordered.HERE), 'unchanged_original_path_claimed': False}
    require(record(Path(row['path'])) == row, 'E_W_HISTORY_CHANGED:' + row['path'])
    return None


@read_only
def historical_readback():
    o = legacy()
    g, m, i = o.g, o.m, o.i
    value = read_sealed(o.CONTRACT, OLD_V3_SHA)
    parent = g.load_sealed(o.PARENT_CONTRACT, o.PARENT_SHA)
    doc = m.validate_contract(parent)
    image = g.load_sealed(m.IMAGE_CONTRACT, m.IMAGE_CONTRACT_SHA)
    i.check_preserved(image, doc, g.file_record(m.IMAGE_CONTRACT))
    m.check_bound_records(parent)
    expected = g.load_sealed(Path(value['image_start_map']['path']), o.MAP_SHA)
    require(len(expected) == 1370 and g.map_digest(expected) ==
            'b94c45316daf100fe2c11d3d8c54ec2a2b24048bcc412df36baa085df09cda29', 'E_W_HISTORY_MAP')
    g.verify_manifest(i.OUTPUT, expected)
    for root, mapping in [(m.OUTPUT, value['actual_inventory']), (o.FAILED_OUT, value['failed_ordered_inventory']),
                          (o.FAILED_SOURCE, value['source_manifest'])]:
        g.verify_manifest(root, mapping)
    transitions = []
    for row in (value['parent'], value['actual'], value['image_start_map'], value['helper'], value['runner'],
                value['original_test'], value['failed_ordered_receipt'], value['failed_ordered_contract'],
                *value['consumed_v2_code'].values()):
        transition = verify_historical_record(row, o)
        if transition:
            transitions.append(transition)
    result = read_sealed(o.OUT / 'Receipt.json', OLD_RESULT_SHA)
    require(all(result[key] is False for key in o.FLAGS), 'E_W_OLD_QUALIFICATION')
    for command in result['commands']:
        for name in ('stdout', 'stderr'):
            require(record(Path(command[name]['path'])) == command[name], 'E_W_OLD_STREAM')
    report, unit = o.read_runner_records(o.OUT / 'tests-3', result['commands'][-1])
    o.verify_calls(report, o.OUT / 'tests-3')
    o.validate_unit_receipt(unit, 1, report)
    o.verify_fixture_and_packs(report, o.OUT / 'tests-3', o.SOURCE)
    g.verify_manifest(Path(doc['source']), doc['source_manifest'])
    # Unpinned V3 temporary files are a current FIRST observation, never a claim
    # that they match a missing original complete inventory.
    observations = {'label': 'FIRST_OBSERVATION_NOT_ORIGINAL_PRESERVATION',
                    'v3_output': g.inventory(o.OUT), 'v3_source': g.inventory(o.SOURCE),
                    'private_artifacts': g.inventory(ARTIFACTS), 'transitions': transitions}
    return o, doc, observations


def verify_own_seal(path, sha):
    require(Path(path) == SEAL, 'E_W_SEAL_PATH')
    value = read_sealed(path, sha)
    validate_seal(value)
    for role, expected in value['files'].items():
        require(record(Path(role)) == expected, 'E_W_HELPER_CHANGED:' + role)
    require(launcher_record() == value['launcher_template'], 'E_W_LAUNCHER_CHANGED')
    return value


def validate_prepared(value):
    keys = {'scope', 'head', 'seal', 'source', 'source_manifest', 'history', 'output', 'sources',
            'worker_started', 'workload_attempt_consumed', *FLAGS}
    require(isinstance(value, dict) and set(value) == keys and value['scope'] == 'W1_W3_DIAGNOSIS_ONLY' and
            value['head'] == HEAD and value['output'] == str(OUT) and value['sources'] == list(map(str, SOURCES)) and
            value['source'] == str(WORKSPACE / 'source') and validate_record(value['seal'], SEAL) and
            isinstance(value['source_manifest'], dict) and len(value['source_manifest']) == 567 and
            all(isinstance(k, str) and isinstance(v, str) and len(v) == 64 for k, v in value['source_manifest'].items()) and
            isinstance(value['history'], dict) and set(value['history']) ==
                {'label', 'v3_output', 'v3_source', 'private_artifacts', 'transitions'} and
            value['history']['label'] == 'FIRST_OBSERVATION_NOT_ORIGINAL_PRESERVATION' and
            value['worker_started'] is False and value['workload_attempt_consumed'] is False and
            all(value[k] is False for k in FLAGS), 'E_W_PREPARED_SCHEMA')


def normal_account():
    require(os.name == 'nt', 'E_W_WINDOWS_REQUIRED')
    import ctypes
    require(not ctypes.windll.shell32.IsUserAnAdmin(), 'E_W_NONADMIN_REQUIRED')
    value = subprocess.run([r'C:\Windows\System32\whoami.exe', '/user', '/fo', 'csv', '/nh'],
                           capture_output=True, timeout=10, check=True).stdout.decode('utf-8').strip()
    import csv
    require(next(csv.reader([value]))[-1] == 'S-1-5-21-2571509308-2482563067-4170768140-1001', 'E_W_NORMAL_SID_REQUIRED')


def absent_layout():
    events.ordinary(WORKSPACE)
    for target in (OUT, *SOURCES):
        try:
            target.lstat()
        except FileNotFoundError:
            continue
        raise ValueError('E_W_EXISTING_INPUT_OR_ATTEMPT:' + str(target))
    require(all(len(p.name) == 6 and p.parent == WORKSPACE for p in SOURCES), 'E_W_LAYOUT')


def prepare_inputs():
    """Called only after the externally checked input seal and normal SID gate."""
    o, doc, observations = historical_readback()
    absent_layout()
    prepared = {'scope': 'W1_W3_DIAGNOSIS_ONLY', 'head': HEAD, 'seal': record(SEAL),
                'source': doc['source'], 'source_manifest': doc['source_manifest'],
                'history': observations, 'output': str(OUT), 'sources': list(map(str, SOURCES)),
                'worker_started': False, 'workload_attempt_consumed': False, **{key: False for key in FLAGS}}
    validate_prepared(prepared)
    # Full required readback finished before any new result or source directory.
    guarded_claim(lambda: o.g.verify_manifest(Path(doc['source']), doc['source_manifest']), OUT)
    save(OUT / 'Prepared.json', prepared)
    print(json.dumps({'status': 'W_INPUTS_PREPARED_DIAGNOSIS_UNRUN', 'prepared': record(OUT / 'Prepared.json'),
                      'worker_started': False, 'workload_attempt_consumed': False}))
    return prepared


def check_preservation(prepared):
    o, doc, actual = historical_readback()
    require(actual == prepared['history'] and doc['source_manifest'] == prepared['source_manifest'], 'E_W_HISTORY_MOVED')
    return o, doc


class Sampler:
    """Controller-only opportunistic file-owner queries; never holds a worker."""
    def __init__(self, root, owned, capture):
        self.root, self.owned, self.capture = root, owned, capture
        self.stop_event = threading.Event()
        self.errors, self.queries, self.seen = [], [], set()
        self.thread = threading.Thread(target=self.watch, name='diagnostic-controller-sampler', daemon=True)

    def watch(self):
        started = time.monotonic()
        while not self.stop_event.wait(.02):
            try:
                require(time.monotonic() - started < 610, 'E_W_SAMPLER_DEADLINE')
                for path in self.root.glob('*.json'):
                    if path.name in self.seen:
                        continue
                    raw = checked_bytes(path, 4096)
                    try:
                        row = json.loads(raw)
                    except (ValueError, UnicodeError):
                        continue  # A live exclusive write may not yet be complete.
                    self.seen.add(path.name)
                    if row.get('kind') != 'END' or row.get('phase') != 'lifetime-cleanup' or row.get('winerror') != 32:
                        continue
                    filename = Path(row['filename'])
                    require(filename.is_absolute() and filename.is_relative_to(self.owned), 'E_W_QUERY_TARGET')
                    label = 'holder-' + str(len(self.queries))
                    require(len(self.queries) < 4, 'E_W_QUERY_LIMIT')
                    result, target = self.capture(label, [sys.executable, '-B', HERE.with_name('worker_lock_probe.py'),
                        '--path', filename, '--owned-root', self.owned], 5, permit_failure=True)
                    self.queries.append({'event': path.name, 'filename': str(filename),
                                         'command': record(target / 'Command.json'),
                                         'owner_status': 'UNKNOWN' if result is None or result.returncode else 'QUERY_RECORDED_REQUIRES_CORRELATION'})
            except BaseException:
                self.errors.append(traceback.format_exc())
                return

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=10)
        require(not self.thread.is_alive(), 'E_W_SAMPLER_STILL_ALIVE')


def run(prepared, external_sha):
    require(Path(prepared) == OUT / 'Prepared.json', 'E_W_PREPARED_PATH')
    value = read_sealed(Path(prepared), external_sha)
    validate_prepared(value)
    verify_own_seal(SEAL, value['seal']['sha256'])
    normal_account()
    o, doc = check_preservation(value)
    g, i = o.g, o.i
    for path in SOURCES:
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        raise ValueError('E_W_EXISTING_SOURCE')
    # Preclaim is exclusive too: no automatic retry if an identity probe fails.
    preclaim = guarded_claim(lambda: check_preservation(value), OUT / 'preclaim')
    env = i.windows_environment(dict(os.environ))
    require(env.get('USERPROFILE') == r'C:\Users\sakth', 'E_W_USERPROFILE')
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1',
               TRANSFORMERS_OFFLINE='1', KNOWLEDGE_WORKER_PYTHON=str(g.WORKER))
    for key in ('MODEL_PYTHON', 'KNOWLEDGE_MODEL_MANIFEST', events.ENV):
        env.pop(key, None)
    temp = preclaim / 'temp'; temp.mkdir()
    env.update(TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    host = g.sibling_module('offline_host_validation', Path(doc['source']) / '.github/scripts')
    receipt = {'scope': 'W1_W3_DIAGNOSIS_ONLY', 'prepared': record(Path(prepared)),
               'commands': [], 'arms': [], 'failure': None, 'preservation': False,
               **diagnosis_result([], False)}
    command_lock = threading.Lock()
    def capture(label, argv, timeout, permit_failure=False):
        print(label + ': RUNNING (diagnosis only)', flush=True)
        target = OUT / label; target.mkdir()
        result, row = host.capture_owned(list(map(str, argv)), target, OUT, env, timeout)
        with command_lock:
            receipt['commands'].append(dict(row, label=label))
        if not permit_failure:
            require(result is not None and result.returncode == 0, 'E_W_CHILD:' + label + ':read retained stderr')
        return result, target
    try:
        result, target = capture('identity-git', [g.GIT, '--no-optional-locks', '-C', doc['repo'], 'rev-parse', 'HEAD'], 30)
        require(checked_bytes(target / 'stdout.log').decode('ascii').strip() == HEAD, 'E_W_CHILD_HEAD')
        result, target = capture('identity-runtime', [g.WORKER, '-B', '-c', g.runtime_probe()], 60)
        i.validate_runtime_observation(json.loads(checked_bytes(target / 'stdout.log')), env, OUT)
        check_preservation(value)
        # No retrieval before the planted-holder and released-holder controls.
        result, target = capture('known-holder-control', [g.CONTROLLER, '-B', HERE.with_name('worker_lock_probe.py'),
            '--control-root', preclaim / 'holder-controls'], 30)
        control = json.loads(checked_bytes(target / 'stdout.log'))
        require(control.get('status') == 'KNOWN_HOLDER_AND_RELEASED_CONTROL_OBSERVED', 'E_W_HOLDER_CONTROL')
        guarded_claim(lambda: check_preservation(value), OUT / 'workload-claim')
        failures = []
        observer_report = None
        for index, source in enumerate(SOURCES):
            g.new_workspace(source, [Path(doc['source']), OUT, g.REPO])
            shutil.copytree(Path(doc['source']), source, dirs_exist_ok=True, copy_function=shutil.copyfile)
            expected = dict(value['source_manifest'])
            if index == 1:
                expected.update(overlay_copy(source))
            g.verify_manifest(source, expected)
            arm = 'baseline' if index == 0 else 'observed'
            arm_output = OUT / arm; arm_output.mkdir()
            sampler = None
            if index == 1:
                event_root = OUT / 'observed-events'; event_root.mkdir()
                env[events.ENV] = str(event_root)
                sampler = Sampler(event_root, arm_output / 'tests/retained-temp', capture)
                sampler.start()
            try:
                result, target = capture(arm + '-method', [g.CONTROLLER, '-B', o.RUNNER,
                    '--package-root', source / 'memory-integrity', '--pattern', 'test_knowledge_completion.py',
                    '--output-dir', arm_output / 'tests'], 600, permit_failure=True)
            finally:
                if sampler:
                    sampler.stop()
                env.pop(events.ENV, None)
            require(result is not None and result.returncode in (0, 1), 'E_W_METHOD_CAPTURE')
            report, unit = o.read_runner_records(arm_output / 'tests', method_record(receipt['commands'], arm + '-method'))
            o.verify_calls(report, arm_output / 'tests')
            o.validate_unit_receipt(unit, result.returncode, report)
            state = o.load_runner().validate_ordered_result(report)
            arm_row = {'arm': arm, 'unit': unit, 'state': state, 'manifest': expected,
                       'ordered_outcomes': record(arm_output / 'tests/Ordered-Outcomes.json')}
            if state != 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE':
                failures.append(arm)
            if index == 1:
                rows = [{'name': p.name, 'raw': checked_bytes(p, 4096)} for p in sorted(event_root.glob('*.json'))]
                captured = method_record(receipt['commands'], arm + '-method')
                observer_report = events.validate_trace(rows, {'arm': event_root.name,
                    'root_pid': captured['containment']['process_id'],
                    'public_count': sum(e['phase'] == 'public' for e in report['events'])})
                observer_report['sampler_errors'] = sampler.errors
                observer_report['holder_queries'] = sampler.queries
                observer_report['failed_emitters'] = [record(p) for p in event_root.glob('*.error')]
                save(OUT / 'Observer-Report.json', observer_report)
                arm_row['observer'] = record(OUT / 'Observer-Report.json')
            receipt['arms'].append(arm_row)
            g.verify_manifest(source, expected)
            check_preservation(value)
        complete = observer_report and observer_report['status'] == 'OBSERVED' and not observer_report['errors'] and not observer_report['sampler_errors'] and not observer_report['failed_emitters']
        receipt.update(diagnosis_result(failures, bool(complete)))
    except BaseException:
        receipt['failure'] = traceback.format_exc()
        receipt['status'] = 'DIAGNOSTIC_BLOCKED_OR_FAILED'
    finally:
        try:
            check_preservation(value)
            receipt['preservation'] = True
        except BaseException:
            receipt['preservation_failure'] = traceback.format_exc()
            receipt['status'] = 'DIAGNOSTIC_BLOCKED_OR_FAILED'
        save(OUT / 'Receipt.json', receipt)
    print(json.dumps({'status': receipt['status'], 'receipt': record(OUT / 'Receipt.json'),
                      'failure': receipt['failure'], 'gate1_complete': False}))
    return 0 if receipt['status'] in ('OBSERVATIONS_RECORDED_CAUSES_REQUIRE_REVIEW', 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE') else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['Prepare', 'Run'], required=True)
    parser.add_argument('--seal-sha256', required=True)
    parser.add_argument('--prepared-sha256')
    args = parser.parse_args()
    verify_own_seal(SEAL, args.seal_sha256)
    normal_account()
    if args.mode == 'Prepare':
        require(args.prepared_sha256 is None, 'E_W_PREPARE_ARGUMENT')
        prepare_inputs()
    else:
        require(args.prepared_sha256 is not None, 'E_W_PREPARED_SEAL_REQUIRED')
        sys.exit(run(OUT / 'Prepared.json', args.prepared_sha256))
