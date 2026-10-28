"""Timing-only guards; selected runtime and old attempts are never launched."""
import ast
import contextlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).absolute().parents[1]/'scripts'


class TimingObserver(unittest.TestCase):
    def observer(self):
        path = SCRIPTS/'cleanup_timing_observer.py'
        self.assertTrue(path.is_file(), 'TC1 observation adapter is not implemented')
        spec = importlib.util.spec_from_file_location('tc_test_observer', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_inverse_preserves_assertions_deadlines_and_function_semantics(self):
        m = self.observer()
        raw = b'"doc"\nimport time\ndef request():\n    deadline=time.monotonic()+.1\n    assert deadline>0\n    return 120\n'
        changed = m.overlay(raw, 'sample.py', 'config.json')
        self.assertEqual(m.inverse(changed), ast.dump(ast.parse(raw), include_attributes=False))
        self.assertIn(b'_tc.span', changed)

    def test_generated_child_scripts_are_instrumented_and_reversible(self):
        m = self.observer()
        raw = b'from pathlib import Path\nPath("actual.py").write_text("import threading\\nthreading.Event().wait(60)\\n")\n'
        changed = m.overlay(raw, 'fixture.py', 'config.json')
        self.assertIn(b'_tc.child_source', changed)
        self.assertIn(b'fixture-child-wait', m.overlay(b'import threading\nthreading.Event().wait(60)\n', 'actual.py', 'config.json'))
        self.assertEqual(m.inverse(changed), ast.dump(ast.parse(raw), include_attributes=False))

    def test_real_three_inputs_all_preserve_exact_original_ast_and_test_count(self):
        m = self.observer()
        root = SCRIPTS.parents[1]
        for name in m.TARGETS:
            raw = (root/name).read_bytes()
            changed = m.overlay(raw, str(root/name), 'config.json')
            self.assertEqual(m.inverse(changed), ast.dump(ast.parse(raw), include_attributes=False))
            compile(changed, name, 'exec')

    def test_pipe_write_flush_and_finally_cause_have_separate_observations(self):
        m = self.observer()
        root = SCRIPTS.parents[1]
        outputs = [m.overlay((root/p).read_bytes(), p, 'config.json').decode() for p in m.TARGETS]
        joined = '\n'.join(outputs)
        for action in ('pipe-write','pipe-flush','fixture-finally','job-terminate','writer-join', 'request-serialize'):
            self.assertIn(repr(action), joined)

    def test_exception_chain_is_bounded_and_preserves_original(self):
        m = self.observer()
        cause = OSError('first'); error = ValueError('last')
        error.__cause__ = cause; error.add_note('kept')
        result = m.error_chain(error)
        self.assertEqual(result[0]['type'], 'ValueError')
        self.assertEqual(result[0]['notes'], ['kept'])
        self.assertEqual(result[1]['type'], 'OSError')
        cause.__cause__ = error
        self.assertLessEqual(len(m.error_chain(error)), 8)

    def test_summary_never_turns_unfinished_into_watchdog_duration(self):
        m = self.observer()
        row = {'schema':1,'event':'START','utc':'now','monotonic_ns':1,'cpu_ns':0,
               'pid':10,'thread':20,'span':0,'action':'pipe-write','status':'STARTED'}
        report = m.report([row])
        self.assertIsNone(report['segments'][0]['duration_seconds'])
        self.assertEqual(report['segments'][0]['status'], 'UNFINISHED')
        self.assertFalse(report['stage_complete'])

    def test_summary_rejects_duplicate_or_orphan_end(self):
        m = self.observer()
        row = {'schema':1,'event':'END','utc':'now','monotonic_ns':1,'cpu_ns':0,
               'pid':10,'thread':20,'span':0,'action':'pipe-write','status':'RETURNED','duration_ns':0}
        with self.assertRaises(ValueError): m.report([row])

    def test_no_installer_or_external_payload_in_overlay(self):
        m = self.observer()
        raw = b'def request():\n    raw=c.canonical(payload) + b"\\n"\n    process.stdin.write(raw); process.stdin.flush()\n'
        result = m.overlay(raw, 'sample.py', 'config.json').decode()
        self.assertNotIn('pip install', result)
        self.assertNotIn('repr(payload)', result)
        self.assertIn("'pipe-write'", result)

    def test_runtime_trace_preserves_error_notes_and_code_location(self):
        m = self.observer()
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); events = root/'events'; events.mkdir()
            config = root/'Config.json'
            config.write_text(json.dumps({'root':str(events),'watched_roots':[str(root)],'budget':120}))
            code = ('import importlib.util\nfrom pathlib import Path\n'
                    'p=Path('+repr(str(SCRIPTS/'cleanup_timing_observer.py'))+')\n'
                    's=importlib.util.spec_from_file_location("obs",p)\n'
                    'm=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n'
                    'm.bootstrap('+repr(str(config))+')\n'
                    'try:\n'
                    '    with m.span("controlled", "sample.py", 7, "request"):\n'
                    '        e=ValueError("CONTROL");e.add_note("NOTE");raise e\n'
                    'except ValueError as e:\n'
                    '    assert str(e)=="CONTROL" and e.__notes__==["NOTE"]\n'
                    '    with m.span("fixture-finally", "sample.py", 8, "relay"): pass\n')
            run = subprocess.run([sys.executable,'-B','-c',code], capture_output=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stderr.decode())
            result = m.report(list(events.glob('*.jsonl')))
            row = next(r for r in result['segments'] if r['action']=='controlled')
            self.assertEqual(row['status'], 'EXCEPTION')
            self.assertEqual(row['details']['line'], 7)
            self.assertEqual(row['details']['error_chain'][0]['notes'], ['NOTE'])
            final = next(r for r in result['segments'] if r['action']=='fixture-finally')
            self.assertEqual(final['details']['active_error'][0]['message'], 'CONTROL')

    def coordinator(self):
        path = SCRIPTS/'cleanup_timing_diagnostic.py'
        self.assertTrue(path.is_file(), 'TC1 coordinator is not implemented')
        spec = importlib.util.spec_from_file_location('tc_test_coordinator', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module

    def test_coordinator_budget_and_case_contract_cannot_be_changed(self):
        m = self.coordinator()
        self.assertEqual(m.WATCHDOG, 60)
        self.assertEqual(m.STACK_AFTER, 10)
        self.assertFalse(m.QUALIFICATION)
        with self.assertRaisesRegex(ValueError, 'E_TC_BUDGET'):
            m.validate_budgets({'request':.1,'shutdown':5,'watchdog':61,'default':120})

    def test_copy_plan_pins_only_three_overlays_and_one_new_observer(self):
        m = self.coordinator()
        self.assertEqual(set(m.OVERLAYS), set(self.observer().TARGETS))
        self.assertEqual(m.NEW_FILE, '.github/scripts/cleanup_timing_observer.py')

    def test_timing_output_never_claims_fix_even_on_zero_exit(self):
        m = self.coordinator()
        row = {'failure':None,'exit_code':0,'execution':'EXITED','containment':{
            'tree_contained':True,'capture_complete':True,'capture_errors':[],
            'timed_out':False,'output_limit_exceeded':False}}
        self.assertEqual(m.classify(row), 'TIMING_CAPTURED_NOT_FIX_OR_STAGE_COMPLETE')
        row['containment']['timed_out'] = True; row['execution'] = 'TIMEOUT'; row['exit_code'] = 1
        self.assertEqual(m.classify(row), 'TIMING_TIMEOUT_NOT_FIXED')
        row['containment']['capture_complete'] = False
        with self.assertRaises(ValueError): m.classify(row)

    def test_real_instrumented_copy_runs_all_twelve_local_controller_cases(self):
        m = self.coordinator(); ld, cr, c1 = m.context()
        with tempfile.TemporaryDirectory(prefix='tc-native-smoke-') as name:
            root = Path(name); source = root/'source'; events = root/'events'; events.mkdir()
            config = root/'Config.json'
            c1.save(config, {'root':str(events),'watched_roots':[str(root)],'budget':120})
            doc = {'source_manifest':c1.source_manifest(ld.SOURCE),
                   'support':{n:c1.record(m.REPO/n) for n in m.SUPPORT}}
            expected = m.copy_source(c1,doc,source,config)
            host = c1.load_support('offline_host_validation')
            target = root/'capture'; target.mkdir(); temp = root/'temp'; temp.mkdir()
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TEMP=str(temp), TMP=str(temp))
            completed, row = host.capture_owned([sys.executable,'-B',source/'.github/scripts/gate1_runner.py',
                '--package-root',source/'memory-integrity','--pattern',ld.PATTERN,
                '--output-dir',root/'tests','--stack-after','10'],target,target,env,60)
            self.assertIsNotNone(completed, str(row))
            self.assertEqual(row['exit_code'],0, (target/'stderr.txt').read_text(errors='replace') if (target/'stderr.txt').exists() else str(row))
            unit = json.loads((root/'tests/Receipt.json').read_bytes())
            cases = json.loads((root/'tests/Case-Outcomes.json').read_bytes())
            cr.load('gate1_current_runtime').validate_suite(unit,cases,ld.case_ids(c1.read_file(ld.SOURCE/m.OVERLAYS[2])),{})
            c1.verify_source(source,expected)
            report = self.observer().report(list(events.glob('*.jsonl')))
            c1.save(root/'Timings.json',report)
            with (root/'Timings.md').open('x',encoding='utf-8') as stream:
                stream.write(self.observer().markdown(report))
            self.assertGreater(len(report['processes']),2)
            # This suite's only real pipe write deliberately blocks then fails;
            # flush correctly may never be reached. A separate control below
            # proves a successful write/flush pair, rather than fabricating one.
            for action in ('pipe-write','fixture-finally','writer-join'):
                self.assertTrue(any(r['action']==action for r in report['segments']),action)
            self.assertTrue(all('active_error' in r['details'] for r in report['segments'] if r['action']=='fixture-finally'))

    def test_real_small_pipe_write_and_flush_are_separately_measured(self):
        m = self.observer()
        with tempfile.TemporaryDirectory(prefix='tc-small-pipe-') as name:
            root = Path(name); events = root/'events'; events.mkdir(); config = root/'Config.json'
            config.write_text(json.dumps({'root':str(events),'watched_roots':[str(root)],'budget':120}))
            code = ('import subprocess,sys\n'
                'process=subprocess.Popen([sys.executable,"-B","-c","import sys;sys.stdin.buffer.read()"],stdin=subprocess.PIPE)\n'
                'try:\n    process.stdin.write(b"abc");process.stdin.flush()\n'
                'finally:\n    process.stdin.close();process.wait(timeout=5)\n')
            changed = m.overlay(code.encode(),'small-pipe.py',str(config))
            run = subprocess.run([sys.executable,'-B','-c',changed.decode()],capture_output=True,timeout=15)
            self.assertEqual(run.returncode,0,run.stderr.decode())
            rows = m.report(list(events.glob('*.jsonl')))['segments']
            for action in ('pipe-write','pipe-flush'):
                selected = [r for r in rows if r['action']==action]
                self.assertEqual(len(selected),1)
                self.assertEqual(selected[0]['status'],'RETURNED')

    def test_observer_failure_after_spawn_cannot_lose_created_child(self):
        m = self.observer(); created = []
        @contextlib.contextmanager
        def broken(*args, **kwargs):
            yield {}
            raise RuntimeError('CONTROL_OBSERVER_END')
        def create(*args, **kwargs):
            process = subprocess.Popen(*args, **kwargs); created.append(process); return process
        with patch.object(m,'span',broken):
            with self.assertRaisesRegex(RuntimeError,'CONTROL_OBSERVER_END'):
                m.spawn(create,[sys.executable,'-B','-c','import threading;threading.Event().wait(30)'],stdin=subprocess.PIPE)
        try:
            self.assertIsNotNone(created[0].poll(),'observer lost ownership after successful creation')
            self.assertTrue(created[0].stdin.closed)
        finally:
            if created and created[0].poll() is None: created[0].kill(); created[0].wait(timeout=5)
            if created: created[0].stdin.close()

    def test_lineage_uses_creation_identity_and_never_equates_launcher_and_interpreter(self):
        m = self.observer()
        def row(pid,span,creation,ppid,parent_creation,extra=None):
            return {'schema':1,'event':'START','utc':'now','monotonic_ns':span+1,'cpu_ns':0,
                    'pid':pid,'thread':20,'span':span,'action':'module-entry','status':'STARTED',
                    'details':dict(creation=creation,ppid=ppid,parent_creation=parent_creation,**(extra or {}))}
        rows = [row(10,0,'a',1,'outside'),row(11,0,'b',10,'a'),row(12,0,'c',11,'b'),row(13,0,'d',10,'WRONG')]
        result = m.report(rows)
        edges = result['lineage']
        self.assertTrue(any(e['child_pid']==12 and e['parent_pid']==11 and e['status']=='MATCHED_CREATION' for e in edges))
        self.assertTrue(any(e['child_pid']==13 and e['status']=='UNMATCHED_OR_UNKNOWN' for e in edges))
        self.assertFalse(any(e['child_pid']==12 and e['parent_pid']==10 for e in edges))

    def test_existing_runtime_alias_with_wrong_file_is_refused(self):
        m = self.observer()
        changed = m.overlay(b'x=1\n','alias-control.py','must-not-read.json').decode()
        code = ('import sys,types\nsys.modules["tc_runtime"]=types.SimpleNamespace(__file__="wrong.py",bootstrap=lambda _:None)\n'+changed)
        run = subprocess.run([sys.executable,'-B','-c',code],capture_output=True,timeout=10)
        self.assertNotEqual(run.returncode,0,'unverified observer alias was trusted')
        self.assertIn(b'E_TC_RUNTIME_ALIAS',run.stderr)

    def test_missing_load_bearing_timing_is_not_promoted_to_complete_capture(self):
        m = self.coordinator()
        self.assertTrue(hasattr(m,'validate_timing'),'missing timing coverage guard')
        with self.assertRaisesRegex(ValueError,'E_TC_TIMING_COVERAGE'):
            m.validate_timing({'segments':[{'action':'module-entry','details':{}}]})

    def test_two_overlays_share_logger_but_keep_distinct_target_entries(self):
        m = self.observer()
        with tempfile.TemporaryDirectory(prefix='tc-entry-') as name:
            root = Path(name); events = root/'events'; events.mkdir(); config = root/'Config.json'
            config.write_text(json.dumps({'root':str(events),'watched_roots':[str(root)],'budget':120}))
            one = m.overlay(b'x=1\n','first-module.py',str(config)).decode()
            two = m.overlay(b'x=2\n','second-module.py',str(config)).decode()
            code = 'exec('+repr(one)+')\nexec('+repr(two)+')\n'
            run = subprocess.run([sys.executable,'-B','-c',code],capture_output=True,timeout=15)
            self.assertEqual(run.returncode,0,run.stderr.decode())
            rows = m.report(list(events.glob('*.jsonl')))['segments']
            targets = {r['details']['code_file'] for r in rows if r['action']=='module-entry'}
            self.assertTrue({'first-module.py','second-module.py'} <= targets, str(targets))

    def test_original_error_must_belong_to_the_blocked_test_interval(self):
        m = self.observer()
        def start(span,action,active):
            return {'schema':1,'event':'START','utc':'now','monotonic_ns':span+1,'cpu_ns':0,
                    'pid':10,'thread':20,'span':span,'action':action,'status':'STARTED','details':{'active_error':active}}
        target = start(1,'function:test_blocked_real_pipe_writer_is_released_before_cleanup',[])
        unrelated = start(0,'fixture-finally',[{'type':'ValueError','message':'unrelated'}])
        empty = start(2,'fixture-finally',[])
        self.assertEqual(m.report([unrelated,target,empty])['original_error_status'],'NOT_REPRODUCED_OR_NOT_OBSERVED')
        empty['details']['active_error'] = [{'type':'OSError','message':'actual'}]
        result = m.report([unrelated,target,empty])
        self.assertEqual(result['original_error_status'],'OBSERVED')
        self.assertEqual(result['original_errors'][0]['chain'][0]['message'],'actual')
        self.assertFalse(result['root_cause_confirmed'])

    def test_coordinator_timeout_retains_timings_without_stage_success(self):
        self.flow(False)

    def test_coordinator_preservation_failure_overrides_timing_capture(self):
        self.flow(True)

    def flow(self, fail_preservation):
        m = self.coordinator(); real_observer = self.observer()
        with tempfile.TemporaryDirectory(prefix='tc-flow-') as name:
            root = Path(name); output = root/'normal'
            def read(path): return b'{}' if path==m.CONTRACT else Path(path).read_bytes()
            def record(path):
                data = read(path)
                return {'path':str(path),'size':len(data),'sha256':__import__('hashlib').sha256(data).hexdigest(),'links':1}
            def save(path,value):
                with path.open('x',encoding='utf-8') as stream: json.dump(value,stream)
            @contextlib.contextmanager
            def noop(*args,**kwargs): yield {}
            observer = SimpleNamespace(bootstrap=lambda _:None,span=noop,
                overlay=lambda raw,*_:raw, report=real_observer.report, markdown=real_observer.markdown)
            def capture(argv,target,cwd,env,timeout):
                timed = timeout==60
                row = {'failure':None,'exit_code':1 if timed else 0,'execution':'TIMEOUT' if timed else 'EXITED',
                       'containment':{'tree_contained':True,'capture_complete':True,'capture_errors':[],
                                      'output_limit_exceeded':False,'timed_out':timed}}
                if timed:
                    actions = ['function:test_blocked_real_pipe_writer_is_released_before_cleanup','imports','installed-package-metadata','fixture-data-write','process-create',
                               'request-serialize','pipe-write','fixture-finally']
                    with (output/'events/1.jsonl').open('x',encoding='utf-8') as stream:
                        for i,action in enumerate(actions):
                            stream.write(json.dumps({'schema':1,'event':'START','utc':'now','monotonic_ns':i+1,'cpu_ns':0,
                                'pid':1,'thread':2,'span':i,'action':action,'status':'STARTED',
                                'details':{'active_error':[{'type':'ValueError','message':'CONTROL'}] if action=='fixture-finally' else []}})+'\n')
                return (None if timed else SimpleNamespace(returncode=0,stdout=b'{}')),row
            host = SimpleNamespace(capture_owned=capture)
            g = SimpleNamespace(WORKER='never-started.exe',runtime_probe=lambda:'identity')
            c1 = SimpleNamespace(normal_account=lambda:None,sha=lambda _: 'seal',read_file=read,record=record,save=save,
                ordinary=lambda _:None,load_support=lambda n:host if n=='offline_host_validation' else g,
                validate_runtime=lambda *_:None,validate_dependencies=lambda *_:None,dependency_versions=lambda:{'control':'1'},
                verify_source=lambda *_:None)
            c2 = SimpleNamespace(environment=lambda _: {},require_capture=lambda *_:None)
            cr = SimpleNamespace(load=lambda _:c2); ld = SimpleNamespace(PATTERN='test_control.py')
            checks = [None,None,ValueError('CONTROL_PRESERVATION')] if fail_preservation else None
            with patch.object(m,'context',return_value=(ld,cr,c1)), patch.object(m,'verify',side_effect=checks), \
                 patch.object(m,'load',return_value=observer),patch.object(m,'OUTPUT',output), \
                 patch.object(m,'copy_source',return_value={'source':'digest'}):
                self.assertEqual(m.run('seal'),1)
            receipt = json.loads((output/'Receipt.json').read_bytes())
            self.assertEqual(len(receipt['commands']),3)
            self.assertTrue(receipt['attempt_consumed'])
            self.assertFalse(receipt['stage_complete'])
            self.assertFalse(receipt['fix_validated'])
            self.assertEqual(receipt['status'],'PARTIAL_OR_FAILED_NO_RETRY' if fail_preservation else 'TIMING_TIMEOUT_NOT_FIXED')
            self.assertIn('Timings.json',receipt['timing_outputs'])

    def test_coordinator_command_row_survives_end_logging_failure(self):
        # Same flow but END logging fails only after the workload capture;
        # its already-returned Command row must not disappear from Receipt.
        source = (SCRIPTS/'cleanup_timing_diagnostic.py').read_text()
        begin = source.index('def capture(label, argv, timeout):')
        end = source.index("identity_probe =",begin)
        capture_source = source[begin:end]
        self.assertLess(capture_source.index("receipt['commands'].append(row)"),capture_source.index("return completed, row"))
        tree = ast.parse(source)
        capture = next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='capture')
        with_node = next(n for n in capture.body if isinstance(n,ast.With))
        self.assertTrue(any("receipt['commands'].append(row)" in ast.unparse(n) for n in with_node.body),
                        'END logger failure would discard returned capture row')


if __name__ == '__main__': unittest.main()
