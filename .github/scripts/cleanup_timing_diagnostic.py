"""TC1: one fresh timing-only lifecycle copy; all consumed attempts immutable."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import traceback

REPO = Path(__file__).absolute().parents[2]
ROOT = REPO/'.github/run-artifacts/cleanup-process-timing-20261024'
CONTRACT, OUTPUT = ROOT/'Inputs.json', ROOT/'normal-timing'
WATCHDOG, STACK_AFTER, QUALIFICATION = 60, 10, False
OVERLAYS = ('memory-integrity/scripts/knowledge_bridge/distributed_retrieval.py',
            'memory-integrity/scripts/knowledge_bridge/windows_job.py',
            'memory-integrity/tests_v2/test_knowledge_windows_shutdown.py')
NEW_FILE = '.github/scripts/cleanup_timing_observer.py'
STACK_HELPER_SHA = 'b03c008a5e590888aa70ea43a38dffc4efaa90b2563336ec2403ff86c2f22031'
STACK_INPUT_SHA = 'ead95373d25ee2750a10c52e4e2bbf7cf3cabb087166b00df2533458bec27075'
STACK_RECEIPT_SHA = 'c803e2fa4010837398be9448a44013181040f4eb576105c6d4e3e29449189b8a'
BUDGETS = {'request':.1,'shutdown':5,'watchdog':60,'default':120}
SUPPORT = (NEW_FILE, '.github/scripts/extended_timing_log.py', '.github/scripts/worker_diagnostic_events.py')


def require(value, message):
    if not value: raise ValueError(message)


def load(path, digest=None):
    raw = path.read_bytes()
    if digest: require(hashlib.sha256(raw).hexdigest() == digest, 'E_TC_HELPER_PIN')
    spec = importlib.util.spec_from_file_location('tc_'+path.stem, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def context():
    ld = load(REPO/'.github/scripts/cleanup_lifetime_diagnostic.py', STACK_HELPER_SHA)
    cr, c1 = ld.context()
    return ld, cr, c1


def validate_budgets(value):
    require(value == BUDGETS, 'E_TC_BUDGET')


def classify(row):
    flags = row.get('containment') or {}
    require(row.get('failure') is None and flags.get('capture_complete') is True and
            flags.get('tree_contained') is True and flags.get('capture_errors') == [] and
            flags.get('output_limit_exceeded') is False and type(row.get('exit_code')) is int,
            'E_TC_CAPTURE_INCOMPLETE')
    if flags.get('timed_out') is True:
        require(row.get('execution')=='TIMEOUT', 'E_TC_CAPTURE_ACCOUNTING')
        return 'TIMING_TIMEOUT_NOT_FIXED'
    require(flags.get('timed_out') is False and row.get('execution')=='EXITED', 'E_TC_CAPTURE_ACCOUNTING')
    return 'TIMING_CAPTURED_NOT_FIX_OR_STAGE_COMPLETE' if row['exit_code']==0 else 'TIMING_TEST_FAILURE_NOT_FIXED'


def validate_timing(result):
    critical = {'imports','installed-package-metadata','process-create','fixture-data-write',
                'request-serialize','pipe-write','fixture-finally'}
    actions = {r['action'] for r in result['segments']}
    require(critical <= actions and all('active_error' in r['details'] for r in result['segments'] if r['action']=='fixture-finally'),
            'E_TC_TIMING_COVERAGE')


def verify(c1, doc):
    ld, _cr, _c1 = context()
    validate_budgets(doc['budgets'])
    require(doc['scope']=='TC1_LIFECYCLE_TIMING_ONLY' and doc['head']==c1.HEAD and
            doc['output']==str(OUTPUT) and doc['helper']==c1.record(Path(__file__).absolute()) and
            all(doc[k] is False for k in ('stage_complete','gate1_complete','release_ready','installed')),
            'E_TC_CONTRACT')
    require(c1.sha(c1.read_file(ld.CONTRACT))==STACK_INPUT_SHA and
            c1.record(ld.CONTRACT)==doc['stack_input'], 'E_TC_STACK_INPUT')
    parent = json.loads(c1.read_file(ld.CONTRACT)); ld.verify_inputs(c1, parent)
    require(c1.sha(c1.read_file(ld.OUTPUT/'Receipt.json'))==STACK_RECEIPT_SHA and
            c1.record(ld.OUTPUT/'Receipt.json')==doc['stack_receipt'], 'E_TC_STACK_RECEIPT')
    require(c1.source_manifest(ld.ROOT)==doc['stack_inventory'], 'E_TC_STACK_CHANGED')
    c1.verify_source(ld.SOURCE, doc['source_manifest'])
    require(doc['case_ids']==ld.case_ids(c1.read_file(ld.SOURCE/OVERLAYS[2])), 'E_TC_CASES')
    require(set(doc['support'])==set(SUPPORT), 'E_TC_SUPPORT_SET')
    for name, record in doc['support'].items():
        require(c1.record(REPO/name)==record, 'E_TC_SUPPORT_CHANGED')
    require(c1.git('rev-parse','HEAD').decode().strip()==c1.HEAD, 'E_TC_HEAD')


def prepare():
    ld, _cr, c1 = context()
    c1.normal_account()
    require(not os.path.lexists(ROOT), 'E_TC_INPUTS_EXIST')
    doc = {'scope':'TC1_LIFECYCLE_TIMING_ONLY','head':c1.HEAD,'output':str(OUTPUT),
           'helper':c1.record(Path(__file__).absolute()),'stack_input':c1.record(ld.CONTRACT),
           'stack_receipt':c1.record(ld.OUTPUT/'Receipt.json'),
           'stack_inventory':c1.source_manifest(ld.ROOT),'source_manifest':c1.source_manifest(ld.SOURCE),
           'case_ids':ld.case_ids(c1.read_file(ld.SOURCE/OVERLAYS[2])),
           'support':{n:c1.record(REPO/n) for n in SUPPORT},'budgets':BUDGETS,
           'stage_complete':False,'gate1_complete':False,'release_ready':False,'installed':False}
    verify(c1, doc)
    c1.ordinary(ROOT.parent); ROOT.mkdir(); c1.ordinary(ROOT); c1.save(CONTRACT, doc)
    print(json.dumps({'status':'TC1_INPUTS_ONLY_NO_SELECTED_RUNTIME','contract':c1.record(CONTRACT)}))


def copy_source(c1, doc, source, config):
    """Exclusive new files only. Inverse of every observation overlay is checked."""
    ld, _cr, _c1 = context()
    require(not os.path.lexists(source), 'E_TC_SOURCE_EXISTS')
    c1.ordinary(source.parent); source.mkdir(); c1.ordinary(source)
    observer = load(REPO/NEW_FILE)
    expected = dict(doc['source_manifest'])
    require(NEW_FILE not in expected and all(n in expected for n in OVERLAYS), 'E_TC_COPY_SET')
    # Existing source already contains these two helpers; exact pins are required.
    for name in SUPPORT[1:]:
        require(expected.get(name)==doc['support'][name]['sha256'], 'E_TC_COPY_SUPPORT')
    for name, digest in doc['source_manifest'].items():
        raw = c1.read_file(ld.SOURCE/name)
        require(c1.sha(raw)==digest, 'E_TC_COPY_DRIFT')
        if name in OVERLAYS:
            # Metadata line refers to the ORIGINAL frozen source, not the
            # re-rendered copy whose line numbers differ after AST unparse.
            raw = observer.overlay(raw, str(ld.SOURCE/name), str(config), source/NEW_FILE)
        target = source/name; target.parent.mkdir(parents=True, exist_ok=True); c1.ordinary(target.parent)
        with target.open('xb') as stream: stream.write(raw)
        expected[name] = c1.sha(raw)
    raw = c1.read_file(REPO/NEW_FILE)
    require(c1.sha(raw)==doc['support'][NEW_FILE]['sha256'], 'E_TC_OBSERVER_CHANGED')
    with (source/NEW_FILE).open('xb') as stream: stream.write(raw)
    expected[NEW_FILE] = c1.sha(raw)
    c1.verify_source(source, expected)
    return expected


def run(digest):
    ld, cr, c1 = context()
    c1.normal_account()
    require(c1.sha(c1.read_file(CONTRACT))==digest, 'E_TC_EXTERNAL_INPUTS')
    doc = json.loads(c1.read_file(CONTRACT)); verify(c1, doc)
    require(not os.path.lexists(OUTPUT), 'E_TC_EXISTING_ATTEMPT')
    c1.ordinary(OUTPUT.parent); OUTPUT.mkdir(); c1.ordinary(OUTPUT)
    receipt = {'status':'PARTIAL_OR_FAILED_NO_RETRY','started_utc':datetime.now(timezone.utc).isoformat(),
               'contract':c1.record(CONTRACT),'commands':[],'failure':None,'source_manifest':None,
               'attempt_consumed':False,'stage_complete':False,'gate1_complete':False,
               'root_cause_confirmed':False,'fix_validated':False,'release_ready':False,'installed':False}
    source, config = OUTPUT/'source', OUTPUT/'Config.json'
    observer = None
    try:
        observer = load(REPO/NEW_FILE)
        events = OUTPUT/'events'; events.mkdir(); (OUTPUT/'temp').mkdir()
        c1.save(config, {'root':str(events),'watched_roots':[str(OUTPUT)],'budget':120})
        receipt['timing_config'] = c1.record(config)
        observer.bootstrap(str(config))
        host = c1.load_support('offline_host_validation')
        c2 = cr.load('gate1_current_runtime'); g = c1.load_support('gate1_validation')
        env = c2.environment(OUTPUT/'temp')
        def capture(label, argv, timeout):
            target = OUTPUT/label; target.mkdir(); c1.ordinary(target)
            print(label+': RUNNING (TC1 timing-only, not qualification)', flush=True)
            with observer.span(label, __file__, 0, 'capture', watchdog_seconds=timeout):
                completed, row = host.capture_owned(argv, target, target, env, timeout)
                row['label'] = label; receipt['commands'].append(row)
            return completed, row
        identity_probe = observer.overlay(g.runtime_probe().encode(), 'selected-identity-probe', str(config)).decode()
        completed, row = capture('preclaim-identity',[g.WORKER,'-B','-c',identity_probe],30)
        c2.require_capture(completed,row)
        c1.validate_runtime(json.loads(completed.stdout),env,OUTPUT/'preclaim-identity')
        probe = "import importlib.metadata as m,json,site;d=m.distribution('semantica');u=json.loads(d.read_text('direct_url.json') or '{}');print(json.dumps({'versions':{n:m.version(n) for n in "+repr(sorted(c1.dependency_versions()))+"},'revision':u.get('vcs_info',{}).get('commit_id'),'user_site':site.ENABLE_USER_SITE}))"
        dependency_probe = observer.overlay(probe.encode(), 'selected-metadata-probe', str(config)).decode()
        completed, row = capture('preclaim-dependencies',[g.WORKER,'-B','-c',dependency_probe],30)
        c2.require_capture(completed,row); c1.validate_dependencies(json.loads(completed.stdout),c1.dependency_versions())
        with observer.span('input-revalidation', __file__, 0, 'verify'): verify(c1,doc)
        with observer.span('diagnostic-copy-and-overlay', __file__, 0, 'copy_source'):
            receipt['source_manifest'] = copy_source(c1,doc,source,config)
        with (OUTPUT/'timing-attempt').open('xb') as stream: stream.write(b'ONE timing-only lifecycle diagnostic\n')
        receipt['attempt_consumed'] = True
        argv = [g.WORKER,'-B',source/'.github/scripts/gate1_runner.py','--package-root',source/'memory-integrity',
                '--pattern',ld.PATTERN,'--output-dir',OUTPUT/'tests','--stack-after',str(STACK_AFTER)]
        completed, row = capture('lifetime-timing',argv,WATCHDOG)
        receipt['status'] = classify(row)
        if row['exit_code']==0:
            require(completed is not None and completed.returncode==0, 'E_TC_UNIT_CAPTURE')
            unit = json.loads(c1.read_file(OUTPUT/'tests/Receipt.json'))
            outcomes = json.loads(c1.read_file(OUTPUT/'tests/Case-Outcomes.json'))
            require(c1.sha(c1.read_file(OUTPUT/'tests/unittest.log'))==unit['log_sha256'], 'E_TC_UNIT_LOG')
            c2.validate_suite(unit,outcomes,doc['case_ids'],{})
    except BaseException:
        receipt['failure'] = traceback.format_exc(); receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
    finally:
        try:
            if observer is None: verify(c1,doc)
            else:
                with observer.span('final-preservation', __file__, 0, 'verify'): verify(c1,doc)
            if receipt['source_manifest'] is not None:
                with observer.span('new-source-preservation', __file__, 0, 'verify_source'):
                    c1.verify_source(source,receipt['source_manifest'])
            if 'timing_config' in receipt: require(c1.record(config)==receipt['timing_config'], 'E_TC_CONFIG_CHANGED')
            receipt['pinned_preservation_verified'] = True
        except Exception:
            receipt['preservation_failure'] = traceback.format_exc(); receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
            # A broken observer must not prevent the actual read-only guard.
            # Retain the observer failure and do not restore a success status.
            try:
                verify(c1,doc)
                receipt['fallback_preservation_verified'] = True
            except Exception:
                receipt['fallback_preservation_failure'] = traceback.format_exc()
        try:
            paths = sorted((OUTPUT/'events').glob('*.jsonl'))
            require(paths and len(paths)<=64 and sum(p.stat().st_size for p in paths)<=32*1024*1024, 'E_TC_EVENT_SET')
            for path in paths: c1.read_file(path)
            result = observer.report(paths)
            if receipt['attempt_consumed']: validate_timing(result)
            receipt['original_error_status'] = result['original_error_status']
            receipt['timing_conclusion'] = result['conclusion']
            require(any(r['action']=='function:test_blocked_real_pipe_writer_is_released_before_cleanup'
                        for r in result['segments']) or not receipt['attempt_consumed'], 'E_TC_TARGET_NOT_REACHED')
            c1.save(OUTPUT/'Timings.json',result)
            with (OUTPUT/'Timings.md').open('x',encoding='utf-8') as stream: stream.write(observer.markdown(result))
            receipt['timing_outputs'] = {n:c1.record(OUTPUT/n) for n in ('Timings.json','Timings.md')}
            receipt['raw_events'] = [c1.record(p) for p in paths]
        except Exception:
            receipt['timing_failure'] = traceback.format_exc(); receipt['status'] = 'PARTIAL_OR_FAILED_NO_RETRY'
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat(); c1.save(OUTPUT/'Receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'receipt':c1.record(OUTPUT/'Receipt.json'),
                      'failure':receipt['failure'],'stage_complete':False,'gate1_complete':False}))
    return 0 if receipt['status']=='TIMING_CAPTURED_NOT_FIX_OR_STAGE_COMPLETE' and receipt.get('pinned_preservation_verified') is True else 1


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--prepare',action='store_true'); action.add_argument('--sha256')
    args = parser.parse_args()
    if args.prepare: prepare()
    else: raise SystemExit(run(args.sha256))
