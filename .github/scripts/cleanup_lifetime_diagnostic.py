"""One new stack-only lifecycle diagnostic; never retry CR3 or claim a fix."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import traceback

REPO = Path(__file__).absolute().parents[2]
ROOT = REPO/'.github/run-artifacts/cleanup-lifetime-stack-20261024'
CONTRACT = ROOT/'Inputs.json'
OUTPUT = ROOT/'normal-stack'
OLD = REPO/'.github/run-artifacts/cleanup-repair-20261023'
SOURCE = OLD/'normal-comparison/repaired-source'
PARENT_SHA = '8bc851bfbc59848b1730bbd141987c4fff80156a5f5adc23467e7f706fbafc2f'
INPUT_SHA = '18b1d93425f0f52965b94ed7349acf11042065348aafc26b8152ce7c6b595838'
FAILED_SHA = 'd214498c4e7ff2b613ebb933c4174e7c19a3125dc60350c34c1c5491d456c9d7'
PATTERN = 'test_knowledge_windows_shutdown.py'
WATCHDOG, STACK_AFTER, STACK_LIMIT = 60, 10, 262144


def require(value, message):
    if not value: raise ValueError(message)


def context():
    path = REPO/'.github/scripts/cleanup_repair_runtime.py'
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PARENT_SHA, 'E_LD_PARENT_HELPER')
    spec = importlib.util.spec_from_file_location('ld_sealed_parent', path)
    cr = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), cr.__dict__)
    return cr, cr.load('gate1_current_preflight')


def case_ids(raw):
    tree = ast.parse(raw)
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'WindowsShutdown']
    require(len(classes) == 1, 'E_LD_CASE_IDS')
    ids = sorted('test_knowledge_windows_shutdown.WindowsShutdown.'+node.name
                 for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'))
    require(len(ids) == len(set(ids)) == 12, 'E_LD_CASE_IDS')
    return ids


def arguments(worker, output):
    return [worker, '-B', SOURCE/'.github/scripts/gate1_runner.py', '--package-root',
            SOURCE/'memory-integrity', '--pattern', PATTERN, '--output-dir', output/'tests',
            '--stack-after', str(STACK_AFTER)]


def classify_capture(completed, row, stack):
    flags = row.get('containment') or {}
    require(row.get('failure') is None and flags.get('capture_complete') is True and
            flags.get('tree_contained') is True and flags.get('capture_errors') == [] and
            flags.get('output_limit_exceeded') is False and type(row.get('exit_code')) is int,
            'E_LD_CAPTURE_INCOMPLETE')
    if flags.get('timed_out') is True:
        require(completed is None and row.get('execution') == 'TIMEOUT', 'E_LD_CAPTURE_ACCOUNTING')
        valid = (isinstance(stack, bytes) and 0 < len(stack) <= STACK_LIMIT and
                 stack.startswith(b'Timeout (') and b'most recent call first' in stack and b'File "' in stack)
        return 'TIMEOUT_STACK_CAPTURED_NOT_FIXED' if valid else 'TIMEOUT_NO_STACK_INCONCLUSIVE'
    require(flags.get('timed_out') is False and row.get('execution') == 'EXITED' and
            completed is not None and completed.returncode == row['exit_code'], 'E_LD_CAPTURE_ACCOUNTING')
    return 'LIFETIME_COMPLETED_PENDING_UNIT_VALIDATION' if completed.returncode == 0 else 'LIFETIME_FAILED_NOT_FIXED'


def verify_inputs(c1, doc):
    cr, _unused = context()
    require(doc['scope'] == 'CR3_BLOCKED_WRITER_STACK_DIAGNOSTIC' and doc['head'] == c1.HEAD and
            doc['output'] == str(OUTPUT) and doc['source'] == str(SOURCE) and
            doc['helper'] == c1.record(Path(__file__).absolute()) and
            doc['watchdog_seconds'] == WATCHDOG and doc['stack_after_seconds'] == STACK_AFTER and
            all(doc[key] is False for key in ('stage_complete','gate1_complete','release_ready',
                                              'installed','producer_authentication')), 'E_LD_INPUT_CONTRACT')
    require(c1.sha(c1.read_file(cr.CONTRACT)) == INPUT_SHA and
            c1.record(cr.CONTRACT) == doc['parent_contract'], 'E_LD_PARENT_INPUTS')
    parent = json.loads(c1.read_file(cr.CONTRACT)); cr.verify(c1, parent)
    failed = cr.OUTPUT/'Receipt.json'
    require(c1.sha(c1.read_file(failed)) == FAILED_SHA and
            c1.record(failed) == doc['failed_receipt'], 'E_LD_FAILED_RECEIPT')
    require(c1.source_manifest(cr.OUTPUT) == doc['failed_inventory'], 'E_LD_OLD_ATTEMPT_CHANGED')
    require(doc['case_ids'] == case_ids(c1.read_file(SOURCE/'memory-integrity/tests_v2'/PATTERN)),
            'E_LD_CASE_IDS')


def prepare():
    cr, c1 = context()
    require(not os.path.lexists(ROOT), 'E_LD_INPUTS_EXIST')
    parent = json.loads(c1.read_file(cr.CONTRACT)); cr.verify(c1, parent)
    failed = cr.OUTPUT/'Receipt.json'
    require(c1.sha(c1.read_file(failed)) == FAILED_SHA, 'E_LD_FAILED_RECEIPT')
    doc = {'scope':'CR3_BLOCKED_WRITER_STACK_DIAGNOSTIC', 'head':c1.HEAD, 'output':str(OUTPUT),
           'source':str(SOURCE), 'helper':c1.record(Path(__file__).absolute()),
           'parent_contract':c1.record(cr.CONTRACT), 'failed_receipt':c1.record(failed),
           'failed_inventory':c1.source_manifest(cr.OUTPUT),
           'case_ids':case_ids(c1.read_file(SOURCE/'memory-integrity/tests_v2'/PATTERN)),
           'watchdog_seconds':WATCHDOG, 'stack_after_seconds':STACK_AFTER,
           'stage_complete':False, 'gate1_complete':False, 'release_ready':False,
           'installed':False, 'producer_authentication':False}
    verify_inputs(c1, doc)
    c1.ordinary(ROOT.parent); ROOT.mkdir(); c1.ordinary(ROOT)
    c1.save(CONTRACT, doc)
    print(json.dumps({'status':'LIFETIME_STACK_INPUTS_ONLY_NO_SELECTED_RUNTIME', 'contract':c1.record(CONTRACT)}))


def run(digest):
    cr, c1 = context()
    c1.normal_account()
    require(c1.sha(c1.read_file(CONTRACT)) == digest, 'E_LD_EXTERNAL_CONTRACT')
    doc = json.loads(c1.read_file(CONTRACT)); verify_inputs(c1, doc)
    require(not os.path.lexists(OUTPUT), 'E_LD_EXISTING_ATTEMPT')
    c1.ordinary(OUTPUT.parent); OUTPUT.mkdir(); c1.ordinary(OUTPUT)
    receipt = {'status':'PARTIAL_OR_FAILED_NO_RETRY', 'head':c1.HEAD, 'contract':c1.record(CONTRACT),
               'started_utc':datetime.now(timezone.utc).isoformat(), 'failure':None, 'commands':[],
               'diagnostic_attempt_consumed':False, 'stage_complete':False, 'gate1_complete':False,
               'release_ready':False, 'installed':False, 'producer_authentication':False,
               'root_cause_confirmed':False, 'fix_validated':False, 'internal_files':{}}
    def capture(label, argv, timeout):
        target = OUTPUT/label; target.mkdir(); c1.ordinary(target)
        print(label+': RUNNING (stack diagnostic, not stage qualification)', flush=True)
        completed, row = host.capture_owned(argv, target, target, env, timeout)
        row['label'] = label; receipt['commands'].append(row)
        return completed, row
    try:
        host = c1.load_support('offline_host_validation')
        c2 = cr.load('gate1_current_runtime'); g = c1.load_support('gate1_validation')
        (OUTPUT/'temp').mkdir(); env = c2.environment(OUTPUT/'temp')
        completed, row = capture('preclaim-identity', [g.WORKER,'-B','-c',g.runtime_probe()], 30)
        c2.require_capture(completed, row)
        c1.validate_runtime(json.loads(completed.stdout), env, OUTPUT/'preclaim-identity')
        probe = "import importlib.metadata as m,json,site;d=m.distribution('semantica');u=json.loads(d.read_text('direct_url.json') or '{}');print(json.dumps({'versions':{n:m.version(n) for n in "+repr(sorted(c1.dependency_versions()))+"},'revision':u.get('vcs_info',{}).get('commit_id'),'user_site':site.ENABLE_USER_SITE}))"
        completed, row = capture('preclaim-dependencies', [g.WORKER,'-B','-c',probe], 30)
        c2.require_capture(completed, row)
        c1.validate_dependencies(json.loads(completed.stdout), c1.dependency_versions())
        verify_inputs(c1, doc)
        with (OUTPUT/'diagnostic-attempt').open('xb') as stream: stream.write(b'ONE lifecycle stack diagnostic\n')
        receipt['diagnostic_attempt_consumed'] = True
        completed, row = capture('lifetime-stack', arguments(g.WORKER, OUTPUT), WATCHDOG)
        stack = b''
        for name in ('Slow-Stack.log','unittest.log','Receipt.json','Case-Outcomes.json'):
            path = OUTPUT/'tests'/name
            if os.path.lexists(path):
                if name == 'Slow-Stack.log': require(path.stat().st_size <= STACK_LIMIT, 'E_LD_STACK_SIZE')
                receipt['internal_files'][name] = c1.record(path)
                if name == 'Slow-Stack.log': stack = c1.read_file(path)
        receipt['status'] = classify_capture(completed, row, stack)
        if receipt['status'] == 'LIFETIME_COMPLETED_PENDING_UNIT_VALIDATION':
            unit = json.loads(c1.read_file(OUTPUT/'tests/Receipt.json'))
            outcomes = json.loads(c1.read_file(OUTPUT/'tests/Case-Outcomes.json'))
            require(c1.sha(c1.read_file(OUTPUT/'tests/unittest.log')) == unit['log_sha256'], 'E_LD_UNIT_LOG')
            c2.validate_suite(unit, outcomes, doc['case_ids'], {})
            receipt['status'] = 'LIFETIME_COMPLETED_NOT_CR3_COMPLETE'
    except BaseException:
        receipt['failure'] = traceback.format_exc()
        receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
    finally:
        try:
            verify_inputs(c1, doc)
            for name, record in receipt['internal_files'].items():
                require(c1.record(OUTPUT/'tests'/name) == record, 'E_LD_INTERNAL_CHANGED')
            receipt['pinned_preservation_verified'] = True
        except Exception:
            receipt['preservation_failure'] = traceback.format_exc()
            receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        c1.save(OUTPUT/'Receipt.json', receipt)
    print(json.dumps({'status':receipt['status'], 'receipt':c1.record(OUTPUT/'Receipt.json'),
                      'failure':receipt['failure'], 'stage_complete':False, 'gate1_complete':False}))
    return 0 if receipt['status'] == 'LIFETIME_COMPLETED_NOT_CR3_COMPLETE' and receipt.get('pinned_preservation_verified') is True else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare', action='store_true')
    action.add_argument('--sha256')
    args = parser.parse_args()
    if args.prepare: prepare()
    else: raise SystemExit(run(args.sha256))
