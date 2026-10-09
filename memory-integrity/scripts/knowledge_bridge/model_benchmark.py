"""Actual local-model patch trials; fixed oracles and honest failed outcomes.

No repair recipes, expected replacement programs, or model-output substitutions
exist in this experiment. Three small authored tasks do not establish general
coding benefit. Generated programs run only after a restricted pure-code check.
"""
import ast
import argparse
from contextlib import contextmanager, redirect_stdout
import math
from pathlib import Path
import re
import signal
import statistics
import subprocess
import sys
import tempfile
import time

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from knowledge_bridge import contracts as c, impact, indexing, model_runtime, retrieval_v2
    from knowledge_bridge.worker_client import WorkerClient
else:
    from . import contracts as c, impact, indexing, model_runtime, retrieval_v2
    from .worker_client import WorkerClient

VARIANTS = ('direct', 'lexical', 'graph', 'graph_audit')
MAX_NEW_TOKENS = 256
TEST_IDS = ['regression.Check.test_primary', 'regression.Check.test_boundary', 'regression.Check.test_invariant']
_DIRECT_MODEL_TIMEOUT = None


@contextmanager
def model_budget(seconds):
    """CLI direct-call deadline; parent process independently bounds the run."""
    if seconds is None:
        yield
        return
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 < seconds <= 120:
        raise ValueError('E_MODEL_TIMEOUT_LIMIT')
    if not hasattr(signal, 'setitimer'):
        raise ValueError('E_MODEL_DIRECT_TIMEOUT_UNAVAILABLE')
    if signal.getitimer(signal.ITIMER_REAL)[0]:
        raise ValueError('E_MODEL_NESTED_TIMEOUT')
    previous = signal.getsignal(signal.SIGALRM)

    def overdue(signum, frame):
        raise ValueError('E_LOCAL_MODEL_TIMEOUT: no retry')

    try:
        signal.signal(signal.SIGALRM, overdue)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def fixtures():
    """Separate bugs and independently authored tests, without known edits."""
    tasks = [
        ('deadline-equality', 'cache_read_allowed', 'alive',
         'An entry is alive only before its expiry time. An expiry of None means no deadline.',
         'def alive(expires_at, now):\n    if expires_at is None:\n        return True\n    return expires_at >= now\n',
         'def cache_read_allowed(expires_at, now):\n    return can_read(expires_at, now)\n',
         'from worker import alive\ndef can_read(expires_at, now):\n    return alive(expires_at, now)\n',
         'from api import cache_read_allowed\n',
         '    def test_primary(self): self.assertFalse(cache_read_allowed(10, 10))\n'
         '    def test_boundary(self): self.assertTrue(cache_read_allowed(None, 100))\n'
         '    def test_invariant(self):\n        self.assertTrue(cache_read_allowed(11, 10))\n        self.assertFalse(cache_read_allowed(9, 10))\n',
         'can_read'),
        ('integer-pagination', 'paginate_record_count', 'count_items',
         'Count pages using integer ceiling division for nonnegative totals and positive sizes. An empty total needs zero pages.',
         'def count_items(total, size):\n    return total // size + 1\n',
         'def paginate_record_count(total, size):\n    return number_of_pages(total, size)\n',
         'from worker import count_items\ndef number_of_pages(total, size):\n    return count_items(total, size)\n',
         'from api import paginate_record_count\n',
         '    def test_primary(self): self.assertEqual(paginate_record_count(20, 10), 2)\n'
         '    def test_boundary(self): self.assertEqual(paginate_record_count(0, 10), 0)\n'
         '    def test_invariant(self):\n        self.assertEqual(paginate_record_count(21, 10), 3)\n        self.assertEqual(paginate_record_count(10**20, 3), 33333333333333333334)\n',
         'number_of_pages'),
        ('stable-duplicates', 'stable_labels', 'unique_values',
         'Remove duplicate string labels while preserving the order of their first appearance. Do not mutate the input list.',
         'def unique_values(values):\n    return sorted(set(values))\n',
         'def stable_labels(values):\n    return normalize_labels(values)\n',
         'from worker import unique_values\ndef normalize_labels(values):\n    return unique_values(values)\n',
         'from api import stable_labels\n',
         '    def test_primary(self): self.assertEqual(stable_labels(["beta", "alpha", "beta"]), ["beta", "alpha"])\n'
         '    def test_boundary(self): self.assertEqual(stable_labels([]), [])\n'
         '    def test_invariant(self):\n        values = ["z", "z", "a"]\n        self.assertEqual(stable_labels(values), ["z", "a"])\n        self.assertEqual(values, ["z", "z", "a"])\n',
         'normalize_labels')]
    result = []
    for ident, query, symbol, requirement, worker, api, client, imports, tests, client_symbol in tasks:
        files = {'api.py': 'from client import ' + client_symbol + '\n' + api,
                 'client.py': client, 'worker.py': worker,
                 'policy.py': '# ' + requirement + '\nPOLICY_VERSION = 1\n',
                 'regression.py': 'import unittest\n' + imports + 'class Check(unittest.TestCase):\n' + tests,
                 'distractor.py': 'def unrelated_render_width():\n    return 640\n'}
        result.append({'id': ident, 'query': query, 'target': 'worker.py', 'symbol': symbol,
                       'requirement': requirement, 'files': files, 'test_ids': list(TEST_IDS),
                       'required_sources': ['api', 'client', 'worker', 'policy', 'regression']})
    return result


def write_files(root, files):
    root.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        c.within(root, name).write_bytes(text.encode('utf-8'))


def extract_code(text):
    c.string(text, 'generated code')
    if len(text.encode('utf-8')) > 65536:
        raise ValueError('E_MODEL_PATCH_SIZE')
    if text.lstrip().startswith('```'):
        match = re.fullmatch(r'```(?:python|py)?\r?\n([\s\S]*?)```[ \t\r\n]*', text.strip())
        if not match:
            raise ValueError('E_MODEL_PATCH_FORMAT')
        code = match.group(1)
    else:
        code = text
    try:
        ast.parse(code)
    except SyntaxError as exc:
        raise ValueError('E_MODEL_PATCH_FORMAT') from exc
    return code


def validate_code(code):
    """Permit bounded pure Python operations; reject executable IO machinery."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ValueError('E_MODEL_PATCH_FORMAT') from exc
    nodes = list(ast.walk(tree))
    if len(nodes) > 1000 or not any(isinstance(node, ast.FunctionDef) for node in tree.body):
        raise ValueError('E_MODEL_PATCH_UNSAFE')
    denied = (ast.Import, ast.ImportFrom, ast.ClassDef, ast.AsyncFunctionDef, ast.Await,
              ast.With, ast.AsyncWith, ast.Global, ast.Nonlocal, ast.Delete)
    functions = {node.name for node in nodes if isinstance(node, ast.FunctionDef)}
    calls = {'len', 'min', 'max', 'sum', 'range', 'enumerate', 'dict', 'list', 'set',
             'tuple', 'int', 'str', 'bool', 'sorted', 'isinstance', 'ValueError', 'TypeError'} | functions
    methods = {'append', 'get', 'keys', 'values', 'items', 'copy', 'lower', 'strip', 'add', 'fromkeys'}
    forbidden = {'open', 'eval', 'exec', 'compile', 'globals', 'locals', 'getattr', 'setattr', 'delattr', 'input', 'print'}
    for node in nodes:
        if isinstance(node, denied):
            raise ValueError('E_MODEL_PATCH_UNSAFE')
        if isinstance(node, ast.Name) and (node.id.startswith('__') or node.id in forbidden):
            raise ValueError('E_MODEL_PATCH_UNSAFE')
        if isinstance(node, ast.FunctionDef) and (node.decorator_list or node.name.startswith('__')):
            raise ValueError('E_MODEL_PATCH_UNSAFE')
        if isinstance(node, ast.Attribute) and node.attr not in methods:
            raise ValueError('E_MODEL_PATCH_UNSAFE')
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                permitted = node.func.id in calls
            else:
                permitted = isinstance(node.func, ast.Attribute) and node.func.attr in methods
            if not permitted:
                raise ValueError('E_MODEL_PATCH_UNSAFE')
    compile(tree, '<generated-worker>', 'exec')


_TEST_RUNNER = '''import io,json,unittest
try:
 import resource
 resource.setrlimit(resource.RLIMIT_CPU,(5,5))
 resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
except ImportError: pass
suite=unittest.defaultTestLoader.discover('.',pattern='regression.py')
def ids(s): return [i for x in s for i in (ids(x) if isinstance(x,unittest.TestSuite) else [x.id()])]
observed=ids(suite)
stream=io.StringIO()
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
print(json.dumps({'tests_run':result.testsRun,'test_ids':observed,'failures':[t.id() for t,_ in result.failures],'errors':[t.id() for t,_ in result.errors],'skipped':[t.id() for t,_ in result.skipped],'passed':result.wasSuccessful() and result.testsRun>0 and not result.skipped,'transcript':stream.getvalue()}))
'''


def run_regression(root, test_ids):
    started = time.perf_counter()
    try:
        result = subprocess.run([sys.executable, '-B', '-c', _TEST_RUNNER], cwd=root,
                                capture_output=True, text=True, timeout=10)
        if result.returncode:
            raise ValueError('test process failed: ' + str(result.returncode) + ': ' + result.stderr[:4096])
        receipt = c.loads(result.stdout)
        receipt['process_exit_code'] = result.returncode
    except (subprocess.TimeoutExpired, ValueError) as exc:
        receipt = {'tests_run': 0, 'test_ids': [], 'failures': [], 'errors': ['test-process'],
                   'skipped': [], 'passed': False, 'transcript': str(exc), 'process_exit_code': -1}
    receipt.update(expected_test_ids=list(test_ids), elapsed_seconds=time.perf_counter() - started)
    receipt['regression_passed'] = receipt['passed'] and set(receipt['test_ids']) == set(test_ids)
    receipt['evidence_digest'] = c.digest(c.canonical({key: value for key, value in receipt.items() if key != 'elapsed_seconds'}))
    return receipt


def oracle_attempted(receipt, test_ids):
    """A failed import/runtime is a negative outcome, not an absent experiment.

    Preserve the actual loader IDs/counts and transcript. Passing still requires
    the complete declared methods; this never promotes an error to a pass.
    """
    if receipt.get('expected_test_ids') != list(test_ids):
        return False
    basis = {key: value for key, value in receipt.items() if key not in ('elapsed_seconds', 'evidence_digest')}
    if receipt.get('evidence_digest') != c.digest(c.canonical(basis)):
        return False
    if receipt.get('regression_passed'):
        return (set(receipt['test_ids']) == set(test_ids) and receipt['tests_run'] == len(test_ids)
                and not receipt['failures'] and not receipt['errors'] and not receipt['skipped'])
    return bool(receipt.get('failures') or receipt.get('errors') or receipt.get('skipped')
                or receipt.get('process_exit_code', 0) != 0)


def _trial(case, variant, repeat, root, trial, doc, policy, task, versions, manifest, worker):
    started = time.perf_counter()
    retrieval_started = time.perf_counter()
    if variant == 'direct':
        units = [indexing.reopen(doc, root, {'source_id': source, 'unit_id': unit['id']})
                 for source in sorted(doc['sources']) for unit in doc['sources'][source]['manifest']['units']]
        retrieval = {'backend': 'DIRECT_CURRENT_SOURCE_INSPECTION'}
    else:
        pack = retrieval_v2.retrieve(doc, root, policy, task, case['query'], worker,
            max_hops=0 if variant == 'lexical' else 2, seeds=1, max_visits=100,
            max_results=50, direction='outgoing', embedding_mode='lexical')
        units, retrieval = pack['units'], pack['retrieval']
    retrieval_seconds = time.perf_counter() - retrieval_started
    observed = sorted({unit['source_id'] for unit in units})
    for unit in units:
        if unit['source_sha256'] != versions[unit['source_id']]:
            raise ValueError('E_MODEL_BENCHMARK_STALE_SOURCE')
    audit = None
    if variant == 'graph_audit':
        audit = {'evidence_class': 'STRUCTURED_AUDIT', 'expected_sources': case['required_sources'],
                 'observed_sources': observed, 'missing_sources': sorted(set(case['required_sources']) - set(observed)),
                 'semantic_truth': 'UNVERIFIED', 'protected_trace': False}
    evidence = '\n\n'.join('FILE ' + doc['sources'][unit['source_id']]['path'] + '\n' + unit['text'] for unit in units)
    prompt = ('Repair this Python project. Replace ONLY ' + case['target'] + '.\n'
              'Return exactly the entire replacement Python file. No markdown, explanation, examples, or tests.\n'
              'Use pure Python functions. Do not import modules or perform file, network, or shell operations.\n'
              'Preserve existing callable names and signatures.\nRequirement: ' + case['requirement'] + '\n')
    if audit is not None:
        prompt += 'Source delivery audit: ' + c.canonical(audit).decode('utf-8') + '\n'
    prompt += '\nCurrent authorized source evidence:\n' + evidence
    write_files(trial, case['files'])
    before = {name: c.digest((trial / name).read_bytes()) for name in case['files']}
    generation_started = time.perf_counter()
    model_receipt, model_error, patch_error, code = None, None, None, None
    try:
        if worker.model_client is not None:
            model_receipt = worker.model_client({'op': 'generate', 'prompt': prompt, 'max_new_tokens': MAX_NEW_TOKENS})
        else:
            with model_budget(_DIRECT_MODEL_TIMEOUT):
                model_receipt = model_runtime.generate_text(manifest, prompt, MAX_NEW_TOKENS)
        if model_receipt['model']['manifest_digest'] != c.digest(Path(manifest).read_bytes()):
            raise ValueError('E_MODEL_BENCHMARK_MODEL_BINDING')
    except ValueError as exc:
        model_error = str(exc)
    generation_seconds = time.perf_counter() - generation_started
    if model_receipt is not None and model_error is None:
        try:
            if model_receipt['finish_reason'] != 'eos':
                raise ValueError('E_MODEL_PATCH_OUTPUT_LIMIT')
            code = extract_code(model_receipt['text'])
            validate_code(code)
            (trial / case['target']).write_bytes(code.encode('utf-8'))
        except ValueError as exc:
            patch_error = str(exc)
    changed = sorted(name for name in case['files'] if before[name] != c.digest((trial / name).read_bytes()))
    regression = run_regression(trial, case['test_ids'])
    if audit is not None:
        audit.update(patch_error=patch_error, changed_paths=changed,
                     test_ids=regression['test_ids'], regression_passed=regression['regression_passed'])
    return {'case': case['id'], 'variant': variant, 'repeat': repeat,
            'prompt': prompt, 'prompt_digest': c.digest(prompt.encode('utf-8')),
            'model_receipt': model_receipt, 'model_receipt_digest': c.digest(c.canonical(model_receipt)),
            'model_error': model_error, 'patch_error': patch_error, 'generated_code': code,
            'patch_applied': code is not None and patch_error is None,
            'changed_paths': changed, 'unnecessary_changes': sorted(set(changed) - {case['target']}),
            'patch_digest': c.digest((trial / case['target']).read_bytes()),
            'regression': regression, 'regression_passed': regression['regression_passed'],
            'source_versions': versions, 'observed_sources': observed,
            'missing_required_sources': sorted(set(case['required_sources']) - set(observed)),
            'read_bytes': sum(len(unit['text'].encode('utf-8')) for unit in units),
            'input_token_count': model_receipt['input_token_count'] if model_receipt else 0,
            'output_token_count': model_receipt['output_token_count'] if model_receipt else 0,
            'retrieval': retrieval, 'audit': audit, 'retrieval_seconds': retrieval_seconds,
            'generation_seconds': generation_seconds, 'elapsed_seconds': time.perf_counter() - started,
            'provider_usage': 0}


def run_case(case, manifest_path, companion, worker, repeats=1):
    if not isinstance(worker, WorkerClient):
        raise ValueError('E_MODEL_BENCHMARK_WORKER')
    c.integer(repeats, 1, 3, 'model benchmark repeats')
    model_runtime.load_manifest(manifest_path)
    with tempfile.TemporaryDirectory(prefix='real-model-coding-') as temporary:
        base = Path(temporary)
        root, store = base / 'project', base / 'index'
        write_files(root, case['files'])
        versions = {Path(name).stem: c.digest(text.encode('utf-8')) for name, text in case['files'].items()}
        baseline = run_regression(root, case['test_ids'])
        source_map = {'schema_version': 1, 'workspace_id': case['id'], 'repository': 'model-benchmark/' + case['id'],
                      'sources': [{'id': Path(name).stem, 'path': name,
                                   'authority': 'SUPPORTING' if name == 'regression.py' else 'AUTHORITATIVE'} for name in case['files']]}
        index_started = time.perf_counter()
        impact.build(root, source_map, store, companion, worker=worker)
        index_seconds = time.perf_counter() - index_started
        doc = indexing.load(store, root, companion)
        policy = {'schema_version': 1, 'workspace_id': case['id'], 'task_id': 'repair', 'allowed_source_ids': sorted(doc['sources'])}
        task = {'schema_version': 1, 'task_id': 'repair', 'required_units': [
            {'source_id': source, 'unit_id': unit['id']} for source in ('policy', 'regression')
            for unit in doc['sources'][source]['manifest']['units']], 'require_graph': True,
            'max_bytes': 200000, 'execution_task_digest': None}
        runs = [_trial(case, variant, repeat, root, base / (variant + str(repeat)), doc,
                       policy, task, versions, manifest_path, worker)
                for variant in VARIANTS for repeat in range(repeats)]
        return {'case': case['id'], 'source_versions': versions,
                'source_scope_digest': c.digest(c.canonical(versions)), 'baseline': baseline,
                'oracle': {'test_ids': case['test_ids'], 'requirement': case['requirement'], 'target': case['target']},
                'index_seconds': index_seconds, 'runs': runs}


def summarize(rows):
    summaries = []
    for variant in VARIANTS:
        selected = [row for row in rows if row['variant'] == variant]
        summaries.append({'variant': variant, 'runs': len(selected),
            'regression_passes': sum(row['regression_passed'] for row in selected),
            'patches_applied': sum(row['patch_applied'] for row in selected),
            'median_elapsed_seconds': statistics.median(row['elapsed_seconds'] for row in selected) if selected else None,
            'input_tokens': sum(row['input_token_count'] for row in selected),
            'output_tokens': sum(row['output_token_count'] for row in selected)})
    by_variant = {row['variant']: row for row in summaries}
    comparable = bool(rows) and by_variant['direct']['runs'] == by_variant['graph']['runs']
    return {'summaries': summaries, 'direct_graph_pass_delta': by_variant['graph']['regression_passes'] - by_variant['direct']['regression_passes'] if comparable else None,
            'general_coding_benefit': 'UNVERIFIED', 'semantic_truth': 'UNVERIFIED', 'default_graph': False}


def experiment_checks(cases, rows, repeats):
    """Verify experiment completeness independently of model success rate."""
    expected = {(case['case'], variant, repeat) for case in cases
                for variant in VARIANTS for repeat in range(repeats)}
    observed = {(row['case'], row['variant'], row['repeat']) for row in rows}
    versions = {case['case']: case['source_versions'] for case in cases}
    return {'balanced_trials': bool(rows) and len(cases) == 3 and len(rows) == len(expected) and observed == expected,
              'failing_original_baselines': all(not case['baseline']['regression_passed'] and case['baseline']['tests_run'] == 3 for case in cases),
              'actual_model_receipts': all(row['model_receipt'] is not None and row['model_error'] is None for row in rows),
              'same_test_oracles': all(oracle_attempted(row['regression'], TEST_IDS)
                    and row['source_versions'] == versions[row['case']] for row in rows),
              'unchanged_test_and_policy_files': all(not row['unnecessary_changes'] for row in rows),
              'same_model_and_settings': len({c.digest(c.canonical({'model': row['model_receipt']['model'], 'settings': row['model_receipt']['settings']})) for row in rows if row['model_receipt']}) == 1}


def run(manifest_path, companion, worker, repeats=1):
    if not isinstance(worker, WorkerClient):
        raise ValueError('E_MODEL_BENCHMARK_WORKER')
    c.integer(repeats, 1, 3, 'model benchmark repeats')
    manifest = model_runtime.load_manifest(manifest_path)
    runtime = worker({'op': 'handshake'})
    cases = [run_case(case, manifest_path, companion, worker, repeats) for case in fixtures()]
    rows = [row for case in cases for row in case['runs']]
    checks = experiment_checks(cases, rows, repeats)
    complete = all(checks.values())
    return {'schema_version': 1, 'kind': 'actual-local-model-coding-v1', 'ok': complete,
            'verdict': 'MEASURED_FOR_DECLARED_LOCAL_MODEL_EXPERIMENT' if complete else 'INCOMPLETE_EXPERIMENT',
            'experiment_checks': checks, 'runtime': runtime, 'manifest_digest': manifest['manifest_digest'],
            'scope': 'three independently authored small Python bugs; actual generated whole-file replacements; fixed regression oracles',
            'fairness': {'same_original_sources': True, 'same_model': True, 'same_settings': True,
                         'same_tests': True, 'direct': 'all current authorized sources, no truncation',
                         'search': 'same lexical query; 1 seed; hops 0 or 2; mandatory policy and regression',
                         'generation_output_limit': MAX_NEW_TOKENS, 'scripted_patch_substitution': False},
            'cases': cases, 'runs': rows, 'repeats': repeats, **summarize(rows),
            'provider_usage': 0, 'model_usage': len(rows),
            'limitations': ['Small authored fixtures and a 0.5B local model are not representative production coding workloads',
                            'A measured tie or loss is retained; no broad coding improvement is asserted',
                            'Syntax and pure-code restrictions may refuse otherwise useful model output',
                            'Output-limit responses are refused even if an apparent complete function exists',
                            'Structured source delivery audit is not free-text entailment or a protected CAS trace',
                            'One repeat does not establish repeatability or statistical significance',
                            'Pure-code AST checks and resource limits are defense in depth, not an OS sandbox']}


def main():
    global _DIRECT_MODEL_TIMEOUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--claude-mon-root', required=True)
    parser.add_argument('--worker-python', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--model-timeout', type=float, default=120)
    args = parser.parse_args()
    previous_timeout = _DIRECT_MODEL_TIMEOUT
    try:
        output = c.ordinary(args.output)
        if output.exists():
            raise ValueError('E_MODEL_BENCHMARK_OUTPUT_EXISTS')
        c.ordinary(output.parent, directory=True)
        if not output.parent.is_dir():
            raise ValueError('E_MODEL_BENCHMARK_OUTPUT_PARENT')
        with model_budget(args.model_timeout):
            pass
        _DIRECT_MODEL_TIMEOUT = args.model_timeout
        with redirect_stdout(sys.stderr):
            report = run(args.manifest, args.claude_mon_root, WorkerClient(args.worker_python, timeout=60))
        raw = c.canonical(report)
        if len(raw) > c.MAX_MESSAGE:
            raise ValueError('E_MESSAGE_LIMIT')
        with output.open('xb') as handle:
            handle.write(raw + b'\n')
        summary = {'ok': report['ok'], 'verdict': report['verdict'], 'output': str(output),
                   'report_sha256': c.digest(raw + b'\n'), 'model_usage': report['model_usage'],
                   'summaries': report['summaries'], 'general_coding_benefit': 'UNVERIFIED'}
        code = 0 if report['ok'] else 1
    except (ValueError, OSError) as exc:
        summary = {'ok': False, 'error': str(exc)}
        code = 1
    finally:
        _DIRECT_MODEL_TIMEOUT = previous_timeout
    sys.stdout.buffer.write(c.canonical(summary) + b'\n')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
