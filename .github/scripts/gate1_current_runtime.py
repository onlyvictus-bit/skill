"""C2 five groups/24 comparisons, bound to successful immutable C1 inputs.

No old attempt is rerun. No installation, source edit, Git write or release.
All output is retained, self-reported evidence, not producer authentication.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

REPO = Path(__file__).absolute().parents[2]
C1_HELPER = REPO/'.github/scripts/gate1_current_preflight.py'
C1_HELPER_SHA = '5e1b06812949b72a8723844c4c1b7a8bde1b4fee645c43147e3352acb7696861'
if hashlib.sha256(C1_HELPER.read_bytes()).hexdigest() != C1_HELPER_SHA:
    raise ValueError('E_C2_C1_HELPER_CHANGED')
_spec = importlib.util.spec_from_file_location('sealed_c1_for_c2', C1_HELPER)
c1 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(c1)
HEAD = c1.HEAD
SOURCE = c1.OUTPUT/'source'
RECEIPT_SHA = 'f0a8b97b49122ad2dc86c5b7adeb4c38e84d97cc774afa80e8debba0d8e30b14'
PREPARED_SHA = '98bfd5870d3d4032cd250dc268a99a3a791b61787081a539f9f4eb2f3818a75d'
ARTIFACTS = c1.CONTRACT.parent/'C2'
CONTRACT = ARTIFACTS/'C2-Inputs.json'
ADAPTED = ARTIFACTS/'acceptance-defaults.py'
OUTPUT = c1.OUTPUT.with_name('gate1-current-a38297d-20261023-c2')
STOP = ARTIFACTS/'Preflight-Failure.json'
PATTERNS = [('memory-integrity', p) for p in ('test_native_containment.py', 'test_native_paths.py',
    'test_offline_release_profile.py', 'test_knowledge*.py')]+[('claude-mon', 'test_offline_release_profile.py')]
COUNTS = [3, 2, 16, 198, 5]
SCOPE = 'GATE1_CURRENT_C2_FIVE_GROUPS_24_ARMS'


def load_module(path, name):
    c1.read_file(path)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def validate_parent(receipt, prepared_record):
    c1.require(receipt.get('status') == 'STEP1_SOURCE_AND_ENVIRONMENT_VERIFIED_NOT_GATE1' and
        receipt.get('head') == HEAD and receipt.get('failure') is None and
        receipt.get('protected_unchanged') is True and receipt.get('prepared') == prepared_record and
        all(receipt.get(key) is False for key in ('gate1_complete', 'installed', 'release_ready',
            'retrieval_executed', 'producer_authentication')), 'E_C2_PARENT_NOT_SUCCESS')


def parent_inputs():
    root = c1.OUTPUT
    c1.require(c1.sha(c1.read_file(root/'Receipt.json')) == RECEIPT_SHA and
               c1.sha(c1.read_file(root/'Prepared.json')) == PREPARED_SHA, 'E_C2_PARENT_SEAL')
    receipt = json.loads(c1.read_file(root/'Receipt.json'))
    value = json.loads(c1.read_file(root/'Prepared.json'))
    validate_parent(receipt, c1.record(root/'Prepared.json'))
    c1.require(value['head'] == HEAD and value['source'] == str(SOURCE) and
               value['fixed'] == c1.fixed_inputs(), 'E_C2_PARENT_INPUT_CHANGED')
    _, tree, manifest = c1.committed_source()
    c1.require(value['tree'] == tree and value['manifest'] == manifest, 'E_C2_SOURCE_BASIS')
    c1.verify_source(SOURCE, manifest)
    c1.require(c1.protected() == value['protected_before'], 'E_C2_PROTECTED_CHANGED')
    for command in receipt['commands']:
        c1.require(command['exit_code'] == 0 and command['execution'] == 'EXITED' and
            command['failure'] is None and command['containment']['capture_complete'] is True and
            command['containment']['tree_contained'] is True and not command['containment']['capture_errors'],
            'E_C2_PARENT_COMMAND')
        for key in ('stdout', 'stderr'):
            row = command[key]
            c1.require({k: v for k, v in c1.record(row['path']).items() if k != 'links'} == row,
                       'E_C2_PARENT_STREAM')
    return value


def adaptations(fixture):
    return [
        ('worker = WorkerClient(args.worker_python,timeout=60) if args.worker_python else None',
         'worker = WorkerClient(args.worker_python) if args.worker_python else None'),
        ("worker_flags = ['--worker-python',args.worker_python,'--worker-timeout','60'] if args.worker_python else []",
         "worker_flags = ['--worker-python',args.worker_python] if args.worker_python else []"),
        ("fixture = Path(__file__).resolve().parents[1]/'fixtures/offline-first'",
         'fixture = Path('+repr(str(fixture))+')')]


def adapt_acceptance(raw, fixture):
    c1.require(c1.sha(raw) == c1.SUPPORT['offline_release_acceptance'], 'E_C2_ACCEPTANCE_BASIS')
    for old, new in adaptations(fixture):
        c1.require(raw.count(old.encode()) == 1, 'E_C2_ADAPTATION_ANCHOR')
        raw = raw.replace(old.encode(), new.encode(), 1)
    return raw


def restore_acceptance(raw, fixture):
    for old, new in reversed(adaptations(fixture)):
        c1.require(raw.count(new.encode()) == 1, 'E_C2_ADAPTATION_REVERSE')
        raw = raw.replace(new.encode(), old.encode(), 1)
    c1.require(c1.sha(raw) == c1.SUPPORT['offline_release_acceptance'], 'E_C2_ADAPTATION_EXTRA_CHANGE')
    return raw


def validate_suite(row, report, ids, allowed):
    c1.require(ids and len(ids) == len(set(ids)) and report.get('expected_ids') == ids,
               'E_C2_DISCOVERY_CHANGED')
    c1.require(row.get('tests_run') == len(ids) == row.get('discovered') and
        row.get('interrupted') is False and
        all(row.get(key) == [] for key in ('failures', 'errors', 'excluded', 'expected_failures')),
        'E_C2_SUITE_AGGREGATE')
    outcomes = report['outcomes']
    c1.require(outcomes.get('started') == ids and
        [r.get('id') for r in outcomes['finished']] == ids, 'E_C2_CASE_COMPLETENESS')
    skips = []
    for result in outcomes['finished']:
        c1.require(set(result) == {'id', 'outcome', 'reason'}, 'E_C2_CASE_SCHEMA')
        if result['outcome'] == 'SKIP':
            c1.require(result['id'] in allowed and allowed[result['id']] in result['reason'], 'E_C2_SKIP')
            skips.append([result['id'], result['reason']])
        else:
            c1.require(result['outcome'] == 'PASS', 'E_C2_CASE_FAILED: '+str(result))
    c1.require(row.get('skipped') == skips, 'E_C2_SKIP_ACCOUNTING')


def clean_module(name):
    # Explicitly use C1's unchanged generic helper, not a cached live-repo alias.
    directory = SOURCE/'.github/scripts'
    path = directory/(name+'.py')
    if name == 'offline_host_validation':
        old = sys.modules.get('offline_release_acceptance')
        c1.require(old is None or Path(old.__file__).absolute() == directory/'offline_release_acceptance.py',
                   'E_C2_CAPTURE_MODULE_ALIAS')
        sys.path.insert(0, str(directory))
    return load_module(path, 'c2_clean_'+name)


def environment(temp):
    env = c1.load_support('gate1_image_successor').windows_environment(dict(os.environ))
    for name in ('MODEL_PYTHON', 'KNOWLEDGE_MODEL_MANIFEST', 'PYTHONPATH', 'PYTHONHOME',
                 'MEMORY_INTEGRITY_WORKER_DIAGNOSTICS'):
        env.pop(name, None)
    worker = c1.load_support('gate1_validation').WORKER
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', PYTHONIOENCODING='utf-8',
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', KNOWLEDGE_WORKER_PYTHON=str(worker),
        TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    return env


def capture(host, label, argv, output, env, timeout):
    target = output/label; target.mkdir(); c1.ordinary(target)
    print(label+': RUNNING (result still requires validation)', flush=True)
    completed, row = host.capture_owned(argv, target, output, env, timeout)
    return completed, dict(row, label=label)


def require_capture(completed, row):
    # The caller retains the row BEFORE checking exit/capture and parsing JSON.
    c1.require(completed is not None and completed.returncode == 0 and
        row.get('exit_code') == 0 and row.get('execution') == 'EXITED' and row.get('failure') is None and
        row['containment']['capture_complete'] is True and row['containment']['tree_contained'] is True and
        row['containment']['capture_errors'] == [] and not row['containment']['timed_out'] and
        not row['containment']['output_limit_exceeded'],
        'E_C2_CHILD_FAILED: '+row['label']+'; read retained stderr/Command.json')


def prepare():
    parent = parent_inputs()
    c1.require(not os.path.lexists(ARTIFACTS) and not os.path.lexists(OUTPUT), 'E_C2_EXISTING_INPUTS_OR_ATTEMPT')
    ARTIFACTS.mkdir(); c1.ordinary(ARTIFACTS)
    with ADAPTED.open('xb') as stream:
        stream.write(adapt_acceptance(c1.read_file(SOURCE/'.github/scripts/offline_release_acceptance.py'),
                                     SOURCE/'.github/fixtures/offline-first'))
    (ARTIFACTS/'temp').mkdir()
    env = environment(ARTIFACTS/'temp'); host = clean_module('offline_host_validation')
    ids = {}; discoveries = []
    for number, (package, pattern) in enumerate(PATTERNS):
        proc, row = capture(host, 'discovery-'+str(number),
            [sys.executable, '-B', str(SOURCE/'.github/scripts/gate1_runner.py'), '--discover',
             '--package-root', str(SOURCE/package), '--pattern', pattern], ARTIFACTS, env, 60)
        require_capture(proc, row)
        found = c1.parse_child({'exit_code': proc.returncode, 'complete': True}, proc.stdout, proc.stderr)
        c1.require(isinstance(found, list) and len(found) == COUNTS[number] and
            all(isinstance(ident, str) and '_FailedTest' not in ident for ident in found) and
            len(set(found)) == len(found), 'E_C2_DISCOVERY')
        ids[str(number)] = found; discoveries.append(row)
    parent_inputs()
    value = {'schema': 1, 'scope': SCOPE, 'head': HEAD, 'output': str(OUTPUT),
        'source': str(SOURCE), 'parent_receipt': c1.record(c1.OUTPUT/'Receipt.json'),
        'parent_prepared': c1.record(c1.OUTPUT/'Prepared.json'),
        'parent_manifest': c1.source_manifest(c1.OUTPUT), 'protected': parent['protected_before'],
        'helper': c1.record(Path(__file__).absolute()), 'adapted': c1.record(ADAPTED),
        'patterns': [list(p) for p in PATTERNS], 'test_ids': ids,
        'allowed_skips': clean_module('gate1_runner').allowed_skips(),
        'discoveries': discoveries, 'gate1_complete': False, 'release_ready': False,
        'installed': False, 'producer_authentication': False}
    c1.save(CONTRACT, value)
    print(json.dumps({'status': 'C2_INPUTS_AND_DISCOVERY_PREPARED_NO_SELECTED_RUNTIME',
        'contract': c1.record(CONTRACT), 'counts': [len(ids[str(n)]) for n in range(5)], 'retrieval_executed': False}))


def preserved(value):
    parent_inputs()
    c1.require(c1.source_manifest(c1.OUTPUT) == value['parent_manifest'] and
        c1.record(Path(__file__).absolute()) == value['helper'] and c1.record(ADAPTED) == value['adapted'],
        'E_C2_BOUND_INPUT_CHANGED')
    restore_acceptance(c1.read_file(ADAPTED), SOURCE/'.github/fixtures/offline-first')


def inputs(path, digest):
    c1.require(Path(path) == CONTRACT and c1.sha(c1.read_file(path)) == digest, 'E_C2_EXTERNAL_SEAL')
    value = json.loads(c1.read_file(path))
    c1.require(set(value) == {'schema', 'scope', 'head', 'output', 'source', 'parent_receipt', 'parent_prepared',
        'parent_manifest', 'protected', 'helper', 'adapted', 'patterns', 'test_ids', 'allowed_skips', 'discoveries',
        'gate1_complete', 'release_ready', 'installed', 'producer_authentication'} and
        type(value['schema']) is int and value['schema'] == 1 and value['scope'] == SCOPE and value['head'] == HEAD and
        value['output'] == str(OUTPUT) and value['source'] == str(SOURCE) and
        value['patterns'] == [list(p) for p in PATTERNS] and
        all(value[k] is False for k in ('gate1_complete', 'release_ready', 'installed', 'producer_authentication')),
        'E_C2_SCHEMA')
    c1.require(value['parent_receipt'] == c1.record(c1.OUTPUT/'Receipt.json') and
        value['parent_prepared'] == c1.record(c1.OUTPUT/'Prepared.json') and
        set(value['test_ids']) == {str(n) for n in range(5)} and
        [len(value['test_ids'][str(n)]) for n in range(5)] == COUNTS and
        value['allowed_skips'] == clean_module('gate1_runner').allowed_skips(), 'E_C2_CASE_CONTRACT')
    preserved(value)
    c1.require(not os.path.lexists(OUTPUT) and not os.path.lexists(STOP), 'E_C2_EXISTING_ATTEMPT')
    return value


def run(path, digest):
    c1.normal_account()  # No wrong-account consumption of the user's attempt.
    c1.require(not os.path.lexists(OUTPUT) and not os.path.lexists(STOP), 'E_C2_EXISTING_ATTEMPT')
    try: value = inputs(path, digest)
    except Exception:
        failure = traceback.format_exc()
        c1.save(STOP, {'scope': SCOPE, 'status': 'C2_PREFLIGHT_FAILED_NO_WORKLOAD', 'failure': failure,
            'gate1_complete': False, 'producer_authentication': False})
        print(json.dumps({'status': 'C2_PREFLIGHT_FAILED_NO_WORKLOAD', 'receipt': c1.record(STOP), 'failure': failure}))
        return 1
    receipt = {'scope': SCOPE, 'head': HEAD, 'status': 'PARTIAL_OR_FAILED_NO_RETRY',
        'started_utc': datetime.now(timezone.utc).isoformat(), 'input_sha256': digest,
        'commands': [], 'suites': [], 'failure': None, 'gate1_complete': False,
        'release_ready': False, 'installed': False, 'producer_authentication': False}
    OUTPUT.mkdir()
    try:
        c1.ordinary(OUTPUT); (OUTPUT/'temp').mkdir()
        env = environment(OUTPUT/'temp'); host = clean_module('offline_host_validation')
        g = c1.load_support('gate1_validation')
        c1.save(OUTPUT/'Inputs.json', value)
        proc, row = capture(host, 'preclaim-runtime', [str(g.WORKER), '-B', '-c', g.runtime_probe()],
                            OUTPUT, env, 60)
        receipt['commands'].append(row)
        require_capture(proc, row)
        observed = c1.parse_child({'exit_code': proc.returncode, 'complete': True}, proc.stdout, proc.stderr)
        c1.validate_runtime(observed, env, OUTPUT)
        preserved(value)
        c1.save(OUTPUT/'workload-claim.json', {'scope': SCOPE, 'head': HEAD, 'input_sha256': digest})
        for number, (package, pattern) in enumerate(PATTERNS):
            proc, row = capture(host, 'suite-'+str(number), [sys.executable, '-B',
                str(SOURCE/'.github/scripts/gate1_runner.py'), '--package-root', str(SOURCE/package),
                '--pattern', pattern, '--output-dir', str(OUTPUT/('tests-'+str(number)))], OUTPUT, env, 1200)
            receipt['commands'].append(row)
            require_capture(proc, row)
            folder = OUTPUT/('tests-'+str(number))
            aggregate = json.loads(c1.read_file(folder/'Receipt.json'))
            cases = json.loads(c1.read_file(folder/'Case-Outcomes.json'))
            validate_suite(aggregate, cases, value['test_ids'][str(number)], value['allowed_skips'])
            c1.require(aggregate['log'] == str(folder/'unittest.log') and
                c1.sha(c1.read_file(folder/'unittest.log')) == aggregate['log_sha256'], 'E_C2_SUITE_LOG')
            receipt['suites'].append({'package': package, 'pattern': pattern,
                'tests_run': aggregate['tests_run'], 'skipped': aggregate['skipped'],
                'receipt': c1.record(folder/'Receipt.json'), 'cases': c1.record(folder/'Case-Outcomes.json')})
            preserved(value)
            print('suite-'+str(number)+': VERIFIED', flush=True)
        proc, row = capture(host, 'coding-acceptance', [sys.executable, '-B', str(ADAPTED),
            '--package-root', str(SOURCE/'memory-integrity'), '--claude-mon-root', str(SOURCE/'claude-mon'),
            '--worker-python', str(g.WORKER), '--output-dir', str(OUTPUT/'acceptance')], OUTPUT, env, 2400)
        receipt['commands'].append(row)
        require_capture(proc, row)
        acceptance = json.loads(c1.read_file(OUTPUT/'acceptance/Receipt.json'))
        producer = load_module(ADAPTED, 'sealed_c2_acceptance_validator')
        producer.validate_receipt(acceptance)
        c1.require(acceptance.get('status') == 'PASS_BOUNDED_RUNTIME' and acceptance.get('failure') is None and
            len(acceptance['measurements']) == 24, 'E_C2_ACCEPTANCE')
        receipt['acceptance'] = c1.record(OUTPUT/'acceptance/Receipt.json')
        receipt['measured_arms'] = len(acceptance['measurements'])
        receipt['status'] = 'C2_RUNTIME_OBSERVED_PENDING_C3_AND_REVIEW'
    except BaseException:
        receipt['failure'] = traceback.format_exc()
        receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
    finally:
        try:
            preserved(value)
            c1.require(c1.sha(c1.read_file(path)) == digest, 'E_C2_CONTRACT_CHANGED')
            receipt['preservation'] = True
        except BaseException:
            receipt['preservation_failure'] = traceback.format_exc(); receipt['preservation'] = False
            receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        c1.save(OUTPUT/'Receipt.json', receipt)
    print(json.dumps({'status': receipt['status'], 'receipt': c1.record(OUTPUT/'Receipt.json'),
        'suites_observed': len(receipt['suites']), 'measured_arms': receipt.get('measured_arms', 0),
        'failure': receipt['failure'], 'gate1_complete': False}))
    return 0 if receipt['status'] == 'C2_RUNTIME_OBSERVED_PENDING_C3_AND_REVIEW' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--verify-inputs', action='store_true')
    parser.add_argument('--sha256'); args = parser.parse_args()
    if args.prepare: prepare(); return 0
    c1.require(bool(args.sha256), 'E_C2_HASH_REQUIRED')
    if args.verify_inputs:
        inputs(CONTRACT, args.sha256); print('C2_INPUTS_VERIFIED_NO_SELECTED_RUNTIME_OR_WORKLOAD'); return 0
    return run(CONTRACT, args.sha256)


if __name__ == '__main__': raise SystemExit(main())
