"""Held-out offline source-discovery experiment with real coding regressions.

An explicit, fixed patch recipe is supplied with each task. This is a controlled
search-and-apply experiment, not an AI coding agent or a source-truth evaluator.
Direct inspection receives the complete authorized corpus whenever it fits.
"""
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

from . import contracts as c, impact, indexing, retrieval_v2, verification
from .worker_client import WorkerClient

VARIANTS = ('direct', 'lexical', 'graph', 'graph+audit')
REPEATS = 2
BYTE_BUDGET = 200000
TEST_IDS = ['regression.Check.test_primary', 'regression.Check.test_boundary',
            'regression.Check.test_distractor']


def fixtures():
    """Three separately specified tasks and oracles, never derived from results."""
    cases = [
        {'id': 'retry-accounting', 'query': 'retry_budget_request',
         'requirement': 'Count retry calls without counting an initial attempt.',
         'files': {
             'api.py': 'from client import perform\ndef retry_budget_request():\n    """retry_budget_request public entry"""\n    return perform(2)\n',
             'client.py': 'from worker import execute\ndef perform(attempts):\n    return execute(attempts)\n',
             'worker.py': 'from policy import MAX_ATTEMPTS\ndef execute(attempts):\n    return min(attempts, MAX_ATTEMPTS) + 1\n',
             'policy.py': '# Retry budget excludes the initial attempt.\nMAX_ATTEMPTS = 2\n',
             'regression.py': 'import unittest\nfrom api import retry_budget_request\nfrom client import perform\nfrom distractor import stable_marker\nclass Check(unittest.TestCase):\n    def test_primary(self): self.assertEqual(retry_budget_request(), 2)\n    def test_boundary(self): self.assertEqual(perform(0), 0)\n    def test_distractor(self): self.assertEqual(stable_marker(), 17)\n',
             'distractor.py': 'def stable_marker():\n    return 17\n',
             'unrelated.py': 'def report_format():\n    return "plain"\n'},
         'patch': {'path': 'worker.py', 'old': 'return min(attempts, MAX_ATTEMPTS) + 1',
                   'new': 'return min(attempts, MAX_ATTEMPTS)'}},
        {'id': 'transfer-normalization', 'query': 'transfer_status',
         'requirement': 'Return trimmed lowercase transfer labels.',
         'files': {
             'api.py': 'from client import accept\ndef transfer_status():\n    """transfer_status public entry"""\n    return accept("  Ready  ")\n',
             'client.py': 'from worker import normalize\ndef accept(label):\n    return normalize(label)\n',
             'worker.py': 'def normalize(label):\n    return label.strip().upper()\n',
             'policy.py': '# Transfer protocol requires lowercase labels; blank stays blank.\nLABEL_CASE = "lower"\n',
             'regression.py': 'import unittest\nfrom api import transfer_status\nfrom client import accept\nfrom distractor import stable_marker\nclass Check(unittest.TestCase):\n    def test_primary(self): self.assertEqual(transfer_status(), "ready")\n    def test_boundary(self): self.assertEqual(accept("  "), "")\n    def test_distractor(self): self.assertEqual(stable_marker(), 17)\n',
             'distractor.py': 'def stable_marker():\n    return 17\n',
             'unrelated.py': 'def voltage_display():\n    return "volts"\n'},
         'patch': {'path': 'worker.py', 'old': 'return label.strip().upper()',
                   'new': 'return label.strip().lower()'}},
        {'id': 'cache-live-count', 'query': 'cache_entry_count',
         'requirement': 'Exclude expired cache entries from the live count.',
         'files': {
             'api.py': 'from client import available\ndef cache_entry_count():\n    """cache_entry_count public entry"""\n    return available([False, True, False])\n',
             'client.py': 'from worker import live_count\ndef available(expired_flags):\n    return live_count(expired_flags)\n',
             'worker.py': 'def live_count(flags):\n    return len(flags)\n',
             'policy.py': '# A true expiry flag marks a dead entry; false marks a live entry.\nEXPIRED = True\n',
             'regression.py': 'import unittest\nfrom api import cache_entry_count\nfrom client import available\nfrom distractor import stable_marker\nclass Check(unittest.TestCase):\n    def test_primary(self): self.assertEqual(cache_entry_count(), 2)\n    def test_boundary(self): self.assertEqual(available([]), 0)\n    def test_distractor(self): self.assertEqual(stable_marker(), 17)\n',
             'distractor.py': 'def stable_marker():\n    return 17\n',
             'unrelated.py': 'def asset_label():\n    return "image"\n'},
         'patch': {'path': 'worker.py', 'old': 'return len(flags)',
                   'new': 'return sum(not flag for flag in flags)'}}]
    for case in cases:
        case.update(required_sources=['api', 'client', 'worker', 'policy', 'regression'],
                    required_test_ids=list(TEST_IDS), allowed_changed_paths=['worker.py'])
    return cases


def _require_worker(worker):
    if not isinstance(worker, WorkerClient):
        raise ValueError('E_BENEFIT_WORKER: select an actual pinned WorkerClient')


def _write(root, files):
    root.mkdir(parents=True, exist_ok=True)
    for path, text in files.items():
        (root / path).write_bytes(text.encode('utf-8'))


_TEST_SCRIPT = '''import io,json,unittest
suite=unittest.defaultTestLoader.discover('.',pattern='regression.py')
def ids(suite):
    return [ident for item in suite for ident in (ids(item) if isinstance(item,unittest.TestSuite) else [item.id()])]
observed=ids(suite)
stream=io.StringIO()
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
print(json.dumps({'tests_run':result.testsRun,'test_ids':observed,'failures':[t.id() for t,_ in result.failures],'errors':[t.id() for t,_ in result.errors],'skipped':[t.id() for t,_ in result.skipped],'passed':result.wasSuccessful() and result.testsRun>0 and not result.skipped,'transcript':stream.getvalue()}))
'''


def _regression(root, expected_ids):
    started = time.perf_counter()
    process = subprocess.run([sys.executable, '-B', '-c', _TEST_SCRIPT], cwd=root,
                             capture_output=True, text=True, timeout=30)
    if process.returncode:
        result = {'passed': False, 'tests_run': 0, 'test_ids': [], 'failures': [],
                  'errors': ['test-process'], 'skipped': [], 'transcript': process.stderr[:4096]}
    else:
        result = c.loads(process.stdout)
    result['expected_test_ids'] = list(expected_ids)
    result['regression_passed'] = result['passed'] and set(result['test_ids']) == set(expected_ids)
    result['elapsed_seconds'] = time.perf_counter() - started
    result['process_exit_code'] = process.returncode
    result['evidence_digest'] = c.digest(c.canonical({key: value for key, value in result.items()
                                                   if key != 'elapsed_seconds'}))
    return result


def _units(doc, root, source_ids):
    return [indexing.reopen(doc, root, {'source_id': ident, 'unit_id': unit['id']})
            for ident in sorted(source_ids) for unit in doc['sources'][ident]['manifest']['units']]


def _audit_probe(case, observed):
    expected = [{'id': 'obligation:' + ident, 'text': 'Read current ' + ident + ' source',
                 'polarity': 'positive', 'conditions': [],
                 'source_units': [{'source_id': ident, 'unit_id': 'U000001'}]}
                for ident in case['required_sources']]
    stage = [claim for claim in expected if claim['source_units'][0]['source_id'] in observed]
    omitted = [claim for claim in expected if claim['id'] != 'obligation:worker']
    flipped = [dict(claim, polarity='negative') if claim['id'] == 'obligation:policy' else claim
               for claim in expected]
    omission = verification.audit(expected, dict(source=expected, retrieval=stage, prompt=stage, answer=omitted))
    flip = verification.audit(expected, dict(source=expected, retrieval=stage, prompt=stage, answer=flipped))
    return {'evidence_class': 'STRUCTURED_AUDIT', 'protected_trace': False,
            'injection': 'controlled source-obligation omission and polarity flip; not model output',
            'omission_detected': any(row['stage'] == 'answer' and row['claim_id'] == 'obligation:worker'
                                     for row in omission['findings']),
            'flip_detected': any(row['kind'] == 'CONTRADICTION' and row['claim_id'] == 'obligation:policy'
                                 for row in flip['findings']),
            'omission_findings': omission['findings'], 'flip_findings': flip['findings'],
            'semantic_truth': 'UNVERIFIED'}


def _trial(case, variant, repeat, root, doc, policy, task, worker, trial):
    started = time.perf_counter()
    retrieval_started = time.perf_counter()
    if variant == 'direct':
        units = _units(doc, root, policy['allowed_source_ids'])
        backend, paths = 'DIRECT_CURRENT_SOURCE_INSPECTION', []
    else:
        pack = retrieval_v2.retrieve(doc, root, policy, task, case['query'], worker,
                                     max_hops=0 if variant == 'lexical' else 2, seeds=1,
                                     max_visits=100, max_results=50, direction='outgoing',
                                     embedding_mode='lexical')
        units = pack['units']
        backend, paths = pack['retrieval']['backend'], pack['retrieval']['results']
    retrieval_seconds = time.perf_counter() - retrieval_started
    read_bytes = sum(len(unit['text'].encode('utf-8')) for unit in units)
    if read_bytes > BYTE_BUDGET:
        raise ValueError('E_BENEFIT_SOURCE_BUDGET')
    observed = sorted({unit['source_id'] for unit in units})
    used_versions = {unit['source_id']: unit['source_sha256'] for unit in units}
    stale_uses = sum(used_versions[ident] != c.digest(c.within(root, doc['sources'][ident]['path']).read_bytes())
                     for ident in observed)
    if stale_uses:
        raise ValueError('E_BENEFIT_STALE_EVIDENCE')
    _write(trial, case['files'])
    before = {path: c.digest((trial / path).read_bytes()) for path in case['files']}
    patch = case['patch']
    visible = {doc['sources'][unit['source_id']]['path'] for unit in units}
    # Every variant gets this same explicit recipe. Hidden source bytes and the
    # relevant-source oracle never supply a substitute for missing evidence.
    patch_applied = patch['path'] in visible and 'policy.py' in visible
    if patch_applied:
        evidence = ''.join(unit['text'] for unit in units
                           if doc['sources'][unit['source_id']]['path'] == patch['path'])
        if evidence.count(patch['old']) != 1:
            raise ValueError('E_BENEFIT_PATCH_BASIS')
        # A source unit is a hunk, not the complete file. Preserve surrounding
        # bytes mechanically without using them to choose or invent the edit.
        original = (trial / patch['path']).read_bytes()
        (trial / patch['path']).write_bytes(original.replace(patch['old'].encode(), patch['new'].encode()))
    changed = sorted(path for path in case['files'] if c.digest((trial / path).read_bytes()) != before[path])
    regression = _regression(trial, case['required_test_ids'])
    audit_started = time.perf_counter()
    audit = _audit_probe(case, observed) if variant == 'graph+audit' else None
    audit_seconds = time.perf_counter() - audit_started if audit is not None else 0.0
    return {'case': case['id'], 'variant': variant, 'repeat': repeat,
            'regression_passed': regression['regression_passed'], 'regression': regression,
            'observed_sources': observed, 'missing_required_sources': sorted(set(case['required_sources']) - set(observed)),
            'changed_paths': changed, 'unnecessary_changes': sorted(set(changed) - set(case['allowed_changed_paths'])),
            'patch_applied': patch_applied, 'patch_digest': c.digest((trial / patch['path']).read_bytes()),
            'read_bytes': read_bytes, 'source_byte_budget': BYTE_BUDGET, 'pack_byte_budget': task['max_bytes'],
            'observed_unit_counts': {ident: sum(unit['source_id'] == ident for unit in units) for ident in observed},
            'source_unit_counts': {ident: len(source['manifest']['units']) for ident, source in doc['sources'].items()},
            'used_source_versions': used_versions, 'stale_source_uses': stale_uses,
            'retrieval_backend': backend, 'result_paths': paths,
            'retrieval_seconds': retrieval_seconds, 'audit_seconds': audit_seconds,
            'elapsed_seconds': time.perf_counter() - started, 'audit': audit,
            'provider_usage': 0}


def _faults(case, root, store, source_map, companion, worker, policy, task):
    path = root / case['patch']['path']
    original = path.read_bytes()
    strict = dict(task, required_units=task['required_units'] + [{'source_id': 'worker', 'unit_id': 'U000001'}])
    admitted_stale = []
    result = {'probe_scope': 'graph pre-retrieval required worker and current access checks'}

    def refused(label, current, access):
        try:
            pack = retrieval_v2.retrieve(current, root, access, strict, case['query'], worker,
                                        max_hops=2, direction='outgoing', embedding_mode='lexical')
        except ValueError as exc:
            expected = 'E_REQUIRED_ACCESS_REVOKED' if label == 'revoked_source' else 'E_REQUIRED_STALE'
            result[label + '_blocked'] = expected in str(exc)
            result[label + '_error'] = str(exc)
        else:
            result[label + '_blocked'] = False
            for unit in pack['units']:
                source = c.within(root, current['sources'][unit['source_id']]['path'])
                if not source.is_file() or unit['source_sha256'] != c.digest(source.read_bytes()):
                    admitted_stale.append({'probe': label, 'source_id': unit['source_id']})

    path.unlink()
    try:
        refused('missing_source', indexing.load(store, root, companion), policy)
    finally:
        path.write_bytes(original)
    path.write_bytes(original.replace(case['patch']['old'].encode(), case['patch']['new'].encode()))
    refused('stale_source', indexing.load(store, root, companion), policy)
    path.write_bytes(original)
    current = indexing.load(store, root, companion)
    revoked = dict(policy, allowed_source_ids=[ident for ident in policy['allowed_source_ids'] if ident != 'worker'])
    refused('revoked_source', current, revoked)
    path.write_bytes(original.replace(case['patch']['old'].encode(), case['patch']['new'].encode()))
    started = time.perf_counter()
    rebuilt = impact.build(root, source_map, store, companion, worker=worker)
    result['refresh_seconds'] = time.perf_counter() - started
    result['reused_sources'] = rebuilt['reused_sources']
    repaired = indexing.load(store, root, companion)
    pack = retrieval_v2.retrieve(repaired, root, policy, strict, case['query'], worker,
                                 max_hops=2, direction='outgoing', embedding_mode='lexical')
    result['repair_current'] = not repaired['stale_sources'] and any(
        unit['source_id'] == 'worker' and unit['source_sha256'] == c.digest(path.read_bytes()) for unit in pack['units'])
    result['old_generation'] = current['generation']
    result['new_generation'] = repaired['generation']
    result['retained_index_storage_bytes'] = sum(item.stat().st_size for item in store.rglob('*') if item.is_file())
    result['stale_source_uses'] = len(admitted_stale)
    result['admitted_stale_sources'] = admitted_stale
    return result


def run_case(case, companion, worker):
    _require_worker(worker)
    with tempfile.TemporaryDirectory(prefix='held-out-benefit-') as temporary:
        base = Path(temporary)
        root, store = base / 'project', base / 'index'
        _write(root, case['files'])
        source_map = {'schema_version': 1, 'workspace_id': case['id'],
                      'repository': 'held-out-offline/' + case['id'],
                      'sources': [{'id': Path(path).stem, 'path': path,
                                   'authority': 'SUPPORTING' if path == 'regression.py' else 'AUTHORITATIVE'}
                                  for path in case['files']]}
        versions = {Path(path).stem: c.digest(text.encode('utf-8')) for path, text in case['files'].items()}
        baseline = _regression(root, case['required_test_ids'])
        started = time.perf_counter()
        impact.build(root, source_map, store, companion, worker=worker)
        build_seconds = time.perf_counter() - started
        doc = indexing.load(store, root, companion)
        storage = sum(item.stat().st_size for item in store.rglob('*') if item.is_file())
        policy = {'schema_version': 1, 'workspace_id': case['id'], 'task_id': 'repair',
                  'allowed_source_ids': sorted(doc['sources'])}
        task = {'schema_version': 1, 'task_id': 'repair', 'required_units': [
                    {'source_id': ident, 'unit_id': unit['id']} for ident in ('policy', 'regression')
                    for unit in doc['sources'][ident]['manifest']['units']],
                'require_graph': True, 'max_bytes': BYTE_BUDGET, 'execution_task_digest': None}
        rows = [_trial(case, variant, repeat, root, doc, policy, task, worker,
                       base / ('trial-' + variant + '-' + str(repeat)))
                for variant in VARIANTS for repeat in range(REPEATS)]
        oracle = {'required_sources': case['required_sources'], 'required_test_ids': case['required_test_ids'],
                  'allowed_changed_paths': case['allowed_changed_paths'], 'requirement': case['requirement']}
        return {'case': case['id'], 'source_versions': versions, 'source_scope_digest': c.digest(c.canonical(versions)),
                'oracle': oracle, 'oracle_digest': c.digest(c.canonical(oracle)), 'baseline': baseline,
                'index_seconds': build_seconds, 'index_input_bytes': sum(len(text.encode('utf-8')) for text in case['files'].values()),
                'index_storage_bytes': storage, 'extraction': doc['construction']['extraction']['extractor'],
                'source_byte_budget': BYTE_BUDGET, 'query': case['query'], 'patch_recipe': case['patch'],
                'runs': rows, 'faults': _faults(case, root, store, source_map, companion, worker, policy, task)}


def summarize(rows):
    summaries = []
    for variant in VARIANTS:
        selected = [row for row in rows if row['variant'] == variant]
        summaries.append({'variant': variant, 'runs': len(selected),
                          'regression_passes': sum(row['regression_passed'] for row in selected),
                          'pass_rate': statistics.mean(row['regression_passed'] for row in selected) if selected else None,
                          'mean_read_bytes': statistics.mean(row['read_bytes'] for row in selected) if selected else None,
                          'median_elapsed_seconds': statistics.median(row['elapsed_seconds'] for row in selected) if selected else None,
                          'missing_required_source_runs': sum(bool(row['missing_required_sources']) for row in selected),
                          'unnecessary_change_runs': sum(bool(row['unnecessary_changes']) for row in selected)})
    groups = {}
    for row in rows:
        signature = c.canonical({key: row[key] for key in ('regression_passed', 'missing_required_sources',
                                                          'unnecessary_changes', 'changed_paths', 'patch_digest')})
        groups.setdefault((row['case'], row['variant']), []).append(signature)
    counts = {row['variant']: row['regression_passes'] for row in summaries}
    runs = {row['variant']: row['runs'] for row in summaries}
    required_groups = {(row['case'], variant) for row in rows for variant in VARIANTS}
    return {'summaries': summaries, 'direct_graph_pass_delta': counts['graph'] - counts['direct']
            if runs['direct'] and runs['direct'] == runs['graph'] else None,
            'deterministic_outcomes_stable': bool(groups) and set(groups) == required_groups
            and all(len(values) == REPEATS and len(set(values)) == 1 for values in groups.values()),
            'coding_benefit': 'UNVERIFIED', 'default_graph': False}


def run(companion, worker):
    _require_worker(worker)
    runtime = worker({'op': 'handshake'})
    cases = [run_case(case, companion, worker) for case in fixtures()]
    rows = [row for case in cases for row in case['runs']]
    aggregate = summarize(rows)
    checks = {'balanced_trials': len(rows) == len(cases) * len(VARIANTS) * REPEATS,
              'observed_regressions': all(row['regression']['process_exit_code'] == 0
                                         and row['regression']['tests_run'] == len(TEST_IDS)
                                         and set(row['regression']['test_ids']) == set(TEST_IDS)
                                         and not row['regression']['skipped'] for row in rows),
              'failing_original_baselines': all(not case['baseline']['regression_passed']
                                               and case['baseline']['tests_run'] == len(TEST_IDS) for case in cases),
              'stable_outcomes': aggregate['deterministic_outcomes_stable'],
              'source_faults_and_repair': all(all(case['faults'][key] for key in (
                  'missing_source_blocked', 'stale_source_blocked', 'revoked_source_blocked', 'repair_current'))
                  and case['faults']['stale_source_uses'] == 0 for case in cases)}
    complete = all(checks.values())
    return {'ok': complete, 'verdict': 'MEASURED_FOR_DECLARED_OFFLINE_EXPERIMENT' if complete
            else 'INCOMPLETE_OR_FAILED_EXPERIMENT_CHECKS', 'experiment_checks': checks,
            'schema_version': 1, 'kind': 'held-out-offline-benefit-v1', 'evidence_class': 'TEST_ONLY',
            'scope': '3 separately authored small Python tasks; fixed patch recipes; actual regression unittest',
            'runtime': runtime, 'case_count': len(cases), 'repeats': REPEATS,
            'fairness': {'source_scope': 'identical authorized corpus and source versions per case',
                         'direct': 'all authorized source units; no ranking or artificial truncation',
                         'search': 'same lexical query, one seed, max_visits 100, max_results 50; hops 0 or 2',
                         'mandatory_sources': ['policy', 'regression'], 'source_byte_budget': BYTE_BUDGET,
                         'patcher': 'identical explicit task recipe; requires current worker and policy evidence'},
            'read_byte_scope': 'source bytes reopened into patcher evidence; excludes indexing, hash validation, patch preservation, copies and test-interpreter reads',
            'cases': cases, 'runs': rows, **aggregate, 'provider_usage': 0, 'model_usage': 0,
            'live_model_benefit': 'UNVERIFIED', 'semantic_truth': 'UNVERIFIED',
            'limitations': ['No AI coding agent, generated patch or live provider execution',
                            'Explicit scripted recipes measure source delivery, not coding reasoning quality',
                            'Small authored fixtures are not representative production workloads',
                            'Structured audit probes use injected obligations and are not protected CAS traces',
                            'Index/refresh cost and retained storage are reported separately; direct needs no graph index',
                            'Fault probes cover graph required-source admission; existing integrity suites cover other paths',
                            'Read-byte counts are evidence volume, not measured total physical IO or token cost']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--claude-mon-root', required=True)
    parser.add_argument('--worker-python', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.claude_mon_root, WorkerClient(args.worker_python, timeout=60)), indent=2))
