"""CR3 bounded control/repaired comparison; never an old C2 run or Gate1 claim."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

REPO = Path(__file__).absolute().parents[2]
ROOT = REPO/'.github/run-artifacts/cleanup-repair-20261023'
CONTRACT = ROOT/'Runtime-Inputs.json'
OUTPUT = ROOT/'normal-comparison'
C1_SHA = '5e1b06812949b72a8723844c4c1b7a8bde1b4fee645c43147e3352acb7696861'
SUPPORT = {
    'gate1_current_preflight': C1_SHA,
    'gate1_current_runtime': '42ee6ee502ac9b4dc742fa6c9a0a70d56fc04600f1d24800f65ace32db56989f',
    'gate1_ordered_runner': '23f67d1ddaa543071857a773a2917df86967a9d14a5d600408763f6f2a8c81b8',
    'gate1_ordered_diagnostic': '1797c2fb1753704fb675e5d37388b37a3b267f9c8debb6f77647cfafaee506ca',
    'gate1_cleanup_diagnostic': '5cab51682fe489aae89427d7d78fb5cf9aa060eafa8e3a0783b9f33736fe6e6f',
}
REPLACEMENTS = ('memory-integrity/scripts/knowledge_bridge/distributed_retrieval.py',
                'memory-integrity/scripts/knowledge_bridge/windows_job.py',
                'memory-integrity/tests_v2/test_knowledge_windows_shutdown.py')


def load(name):
    path = REPO/'.github/scripts'/(name+'.py')
    if hashlib.sha256(path.read_bytes()).hexdigest() != SUPPORT[name]:
        raise ValueError('E_CR_SUPPORT: '+name)
    spec = importlib.util.spec_from_file_location('cr_'+name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def validate_delta(before, after, allowed):
    changed = {name for name in set(before) | set(after) if before.get(name) != after.get(name)}
    if not changed <= set(allowed) or set(before) - set(after):
        raise ValueError('E_CR_UNAPPROVED_DELTA: '+str(sorted(changed)))
    return True


def error_overlay(raw, old, replacement):
    if raw.count(old) != 1 or raw.count(replacement) != 0:
        raise ValueError('E_CR_ERROR_OVERLAY')
    result = raw.replace(old, replacement, 1)
    if result.replace(replacement, old, 1) != raw:
        raise ValueError('E_CR_ERROR_OVERLAY')
    return result


def history(c1):
    before = json.loads(c1.read_file(ROOT/'Before.json'))
    c1.require(c1.sha(c1.read_file(ROOT/'Before.json')) ==
        '9ab4cd15cee406a1305d8736df6634c533ebdbd197e9ea28848eaa7eeef6cd32', 'E_CR_BEFORE')
    rows = {}
    for key in ('c1_receipt', 'c1_prepared', 'c2_receipt', 'c2_helper', 'c2_launcher'):
        row = before[key]
        c1.require(c1.record(row['path']) == row, 'E_CR_HISTORY: '+key)
        rows[row['path']] = row
    # Pin the original captured command streams; old scratch is not re-executed.
    old = json.loads(c1.read_file(before['c2_receipt']['path']))
    for command in old['commands']:
        for role in ('stdout', 'stderr'):
            row = command[role]; actual = c1.record(row['path'])
            c1.require({k:v for k,v in actual.items() if k != 'links'} == row, 'E_CR_OLD_STREAM')
            rows[row['path']] = actual
    return rows


def verify(c1, doc):
    c1.require(doc['scope'] == 'CR3_CONTROL_REPAIRED_ORDERED_COMPARISON' and
        doc['head'] == c1.HEAD and doc['output'] == str(OUTPUT) and
        doc['helper'] == c1.record(Path(__file__).absolute()), 'E_CR_CONTRACT')
    c1.require(c1.git('rev-parse', 'HEAD').decode().strip() == c1.HEAD, 'E_CR_HEAD')
    c1.verify_source(c1.OUTPUT/'source', doc['source'])
    c1.require(c1.source_manifest(c1.OUTPUT) == doc['c1_inventory'] and
        history(c1) == doc['history'] and c1.fixed_inputs() == doc['runtime'] and
        c1.protected() == doc['protected'], 'E_CR_PRESERVATION')
    c1.require(set(doc['replacements']) == set(REPLACEMENTS), 'E_CR_REPLACEMENT_SET')
    for name, row in doc['replacements'].items():
        c1.require(row == c1.record(REPO/name), 'E_CR_REPLACEMENT_CHANGED')
    for name in SUPPORT:
        c1.require(c1.sha(c1.read_file(REPO/'.github/scripts'/(name+'.py'))) == SUPPORT[name], 'E_CR_SUPPORT')


def prepare():
    c1 = load('gate1_current_preflight')
    before = json.loads(c1.read_file(ROOT/'Before.json'))
    protected = c1.protected()
    for root, manifest in before['protected'].items():
        allowed = {name.removeprefix('memory-integrity/') for name in REPLACEMENTS} if root == str(REPO/'memory-integrity') else set()
        validate_delta(manifest, protected[root], allowed)
    prepared = json.loads(c1.read_file(c1.OUTPUT/'Prepared.json'))
    doc = {'scope':'CR3_CONTROL_REPAIRED_ORDERED_COMPARISON', 'head':c1.HEAD,
        'output':str(OUTPUT), 'helper':c1.record(Path(__file__).absolute()),
        'source':prepared['manifest'], 'c1_inventory':c1.source_manifest(c1.OUTPUT),
        'history':history(c1), 'runtime':c1.fixed_inputs(), 'protected':protected,
        'replacements':{name:c1.record(REPO/name) for name in REPLACEMENTS},
        'producer_authentication':False, 'gate1_complete':False, 'release_ready':False, 'installed':False}
    verify(c1, doc)
    c1.save(CONTRACT, doc)
    print(json.dumps({'status':'CR3_INPUTS_ONLY_NO_SELECTED_RUNTIME', 'contract':c1.record(CONTRACT)}))


def copy_source(c1, doc, destination, repaired):
    c1.require(not os.path.lexists(destination), 'E_CR_DESTINATION_EXISTS')
    destination.mkdir(); c1.ordinary(destination)
    expected = dict(doc['source'])
    for name, digest in expected.items():
        data = c1.read_file(c1.OUTPUT/'source'/name)
        c1.require(c1.sha(data) == digest, 'E_CR_SOURCE_CHANGED')
        path = destination/name; path.parent.mkdir(parents=True, exist_ok=True); c1.ordinary(path.parent)
        with path.open('xb') as stream: stream.write(data)
    if repaired:
        for name, row in doc['replacements'].items():
            path = destination/name; data = c1.read_file(REPO/name)
            c1.require(c1.sha(data) == row['sha256'], 'E_CR_REPLACEMENT_CHANGED')
            # Overwrite only this run's just-authored copy of the named module.
            c1.ordinary(path.parent)
            if name in expected: c1.read_file(path)
            with path.open('wb' if name in expected else 'xb') as stream: stream.write(data)
            expected[name] = row['sha256']
    m = load('gate1_cleanup_diagnostic')
    worker = destination/m.WORKER_RELATIVE
    raw = c1.read_file(worker)
    c1.require(c1.sha(raw) == m.WORKER_SHA, 'E_CR_WORKER_BASIS')
    changed = error_overlay(raw, m._OLD_HANDLER, m._diagnostic_error_handler_bytes())
    with worker.open('wb') as stream: stream.write(changed)
    expected[m.WORKER_RELATIVE] = c1.sha(changed)
    c1.verify_source(destination, expected)
    return expected


def validate_control(report, code):
    """Accept all-pass non-reproduction or ONLY the demonstrated initial failure."""
    runner = load('gate1_ordered_runner')
    state = runner.validate_ordered_result(report)
    error = 'E_CR_UNEXPECTED_CONTROL_FAILURE'
    if code == 0:
        if state != 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE':
            raise ValueError(error)
        return
    if code != 1 or [row['outcome'] for row in report['subtests']] != ['PASS','PASS','PASS','FAIL']:
        raise ValueError(error)
    events = [event for event in report['events'] if event['mode'] == ['vector','distributed-local']]
    if len(events) != 1 or events[0]['phase'] != 'public' or events[0].get('returncode') != 2:
        raise ValueError(error)
    diagnostic = load('gate1_cleanup_diagnostic')
    reply = diagnostic.parse_public_reply(2, events[0]['stdout'].encode('utf-8'),
                                           events[0]['stderr'].encode('utf-8'))
    classification, _detail = diagnostic.classify_public_reply(2, reply, Path('unused-for-refusal'))
    if classification != 'CAUSE_OBSERVED_PENDING_REVIEW':
        raise ValueError(error)


def run(digest):
    c1 = load('gate1_current_preflight')
    c1.normal_account()  # Wrong-account refusal never consumes the host attempt.
    c1.require(c1.sha(c1.read_file(CONTRACT)) == digest, 'E_CR_EXTERNAL_CONTRACT')
    doc = json.loads(c1.read_file(CONTRACT)); verify(c1, doc)
    c1.require(not os.path.lexists(OUTPUT), 'E_CR_EXISTING_ATTEMPT')
    c1.ordinary(OUTPUT.parent); OUTPUT.mkdir(); c1.ordinary(OUTPUT)
    receipt = {'status':'PARTIAL_OR_FAILED_NO_RETRY', 'head':c1.HEAD, 'contract':c1.record(CONTRACT),
        'started_utc':datetime.now(timezone.utc).isoformat(), 'failure':None, 'commands':[],
        'gate1_complete':False, 'release_ready':False, 'installed':False,
        'producer_authentication':False, 'historical_c2_cause_proven':False,
        'workload_attempt_consumed':False, 'source_manifests':{}, 'comparisons':[]}
    def capture(label, argv, timeout):
        target = OUTPUT/label; target.mkdir(); c1.ordinary(target)
        print(label+': RUNNING (focused comparison, not Gate1)', flush=True)
        proc, row = host.capture_owned(argv, target, target, env, timeout)
        row['label'] = label; receipt['commands'].append(row)
        # An incomplete capture/start error cannot become a parser/worker result.
        c1.require(proc is not None, 'E_CR_CAPTURE_FAILED: '+label+'; read retained stderr/Command.json')
        return proc, row
    try:
        host = c1.load_support('offline_host_validation')
        c2 = load('gate1_current_runtime'); g = c1.load_support('gate1_validation')
        (OUTPUT/'temp').mkdir(); env = c2.environment(OUTPUT/'temp')
        proc, row = capture('preclaim-identity', [g.WORKER, '-B', '-c', g.runtime_probe()], 30)
        c2.require_capture(proc, row)
        c1.validate_runtime(json.loads(proc.stdout), env, OUTPUT/'preclaim-identity')
        # Reuse C1's exact installed dependency/revision check, no numerical import.
        script = "import importlib.metadata as m,json,site;d=m.distribution('semantica');u=json.loads(d.read_text('direct_url.json') or '{}');print(json.dumps({'versions':{n:m.version(n) for n in "+repr(sorted(c1.dependency_versions()))+"},'revision':u.get('vcs_info',{}).get('commit_id'),'user_site':site.ENABLE_USER_SITE}))"
        proc, row = capture('preclaim-dependencies', [g.WORKER, '-B', '-c', script], 30)
        c2.require_capture(proc, row); c1.validate_dependencies(json.loads(proc.stdout), c1.dependency_versions())
        verify(c1, doc)
        with (OUTPUT/'workload-claim').open('xb') as stream: stream.write(b'CR3 one bounded comparison\n')
        receipt['workload_attempt_consumed'] = True
        for label, repaired in (('control', False), ('repaired', True)):
            source = OUTPUT/(label+'-source')
            receipt['source_manifests'][str(source)] = copy_source(c1, doc, source, repaired)
            if repaired:
                proc, row = capture('repaired-lifetime', [g.WORKER, '-B', source/'.github/scripts/gate1_runner.py',
                    '--package-root', source/'memory-integrity', '--pattern', 'test_knowledge_windows_shutdown.py',
                    '--output-dir', OUTPUT/'lifetime-tests'], 60)
                c2.require_capture(proc, row)
                unit = json.loads(c1.read_file(OUTPUT/'lifetime-tests/Receipt.json'))
                c1.require(unit['tests_run'] == unit['discovered'] == 12 and unit['interrupted'] is False and
                    all(unit[key] == [] for key in ('failures','errors','skipped','expected_failures','excluded')), 'E_CR_LIFETIME_TESTS')
            tests = OUTPUT/(label+'-tests')
            proc, row = capture(label+'-ordered', [g.WORKER, '-B', source/'.github/scripts/gate1_ordered_runner.py',
                '--package-root', source/'memory-integrity', '--pattern', 'test_knowledge_completion.py',
                '--output-dir', tests], 600)
            ordered = load('gate1_ordered_diagnostic')
            report, unit = ordered.read_runner_records(tests, row)
            state, details = ordered.classify(report, unit, proc.returncode)
            ordered.verify_calls(report, tests)
            receipt['comparisons'].append({'label':label, 'classification':state, 'details':details,
                'unit_receipt':c1.record(tests/'Receipt.json'), 'outcomes':c1.record(tests/'Ordered-Outcomes.json')})
            if repaired:
                c2.require_capture(proc, row)
                c1.require(state == 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE', 'E_CR_REPAIRED_METHOD_FAILED')
            else:
                validate_control(report, proc.returncode)
        receipt['status'] = 'CR3_FOCUSED_REPAIRED_RUNTIME_OBSERVED_PENDING_RESULT_REVIEW'
    except BaseException:
        receipt['failure'] = traceback.format_exc()
    finally:
        try:
            verify(c1, doc)
            for source, manifest in receipt['source_manifests'].items():
                c1.verify_source(Path(source), manifest)
            receipt['pinned_preservation_verified'] = True
        except Exception:
            receipt['preservation_failure'] = traceback.format_exc()
            receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        c1.save(OUTPUT/'Receipt.json', receipt)
    print(json.dumps({'status':receipt['status'], 'receipt':c1.record(OUTPUT/'Receipt.json'),
        'failure':receipt['failure'], 'gate1_complete':False}))
    return 0 if receipt['failure'] is None and receipt.get('pinned_preservation_verified') is True else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--sha256')
    args = parser.parse_args()
    if args.prepare: prepare()
    elif args.sha256: raise SystemExit(run(args.sha256))
    else: parser.error('explicit prepare or externally sealed run required')
