"""Real stdlib controls for the separately approved ordered diagnostic."""
import importlib.util
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
TARGET = 'test_knowledge_completion.RemainingPublicContract.test_public_advanced_modes_source_closure_and_replay'


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runner():
    path = ROOT/'.github/scripts/gate1_ordered_runner.py'
    return module_at('ordered_runner_controls', path) if path.exists() else None


def driver():
    path=ROOT/'.github/scripts/gate1_ordered_diagnostic.py'
    return module_at('ordered_driver_controls',path) if path.exists() else None


def select(suite):
    subject = runner()
    if subject is not None: return subject.choose_case(suite)
    legacy = module_at('legacy_gate1_selection', ROOT/'.github/scripts/gate1_runner.py')
    return unittest.TestSuite(legacy.cases(suite))


class OrderedSelection(unittest.TestCase):
    def test_original_method_is_the_only_executed_case_not_the_whole_file(self):
        events = []
        class RemainingPublicContract(unittest.TestCase):
            def test_public_advanced_modes_source_closure_and_replay(self):
                events.append('target')
            def test_unrelated_case_must_not_run(self):
                events.append('unrelated')
        RemainingPublicContract.__module__ = 'test_knowledge_completion'
        RemainingPublicContract.__qualname__ = 'RemainingPublicContract'
        suite = unittest.TestSuite([
            RemainingPublicContract('test_unrelated_case_must_not_run'),
            RemainingPublicContract('test_public_advanced_modes_source_closure_and_replay')])
        # Meaningful RED uses the real legacy discovery, not an import error.
        selected = select(suite)
        result = unittest.TextTestRunner(stream=io.StringIO()).run(selected)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(events, ['target'], 'ordered diagnostic must not run unrelated discovered cases')
        self.assertEqual(result.testsRun, 1)

    def test_missing_original_case_stops_instead_of_running_something_else(self):
        class Other(unittest.TestCase):
            def test_other(self): pass
        with self.assertRaisesRegex(ValueError, 'E_ORDERED_CASE_SELECTION'):
            select(unittest.TestSuite([Other('test_other')]))

    def test_duplicate_original_case_is_not_silently_run_twice(self):
        class RemainingPublicContract(unittest.TestCase):
            def test_public_advanced_modes_source_closure_and_replay(self): pass
        RemainingPublicContract.__module__ = 'test_knowledge_completion'
        RemainingPublicContract.__qualname__ = 'RemainingPublicContract'
        method = 'test_public_advanced_modes_source_closure_and_replay'
        self.assertEqual(RemainingPublicContract(method).id(), TARGET)
        with self.assertRaisesRegex(ValueError, 'E_ORDERED_CASE_SELECTION'):
            select(unittest.TestSuite([RemainingPublicContract(method), RemainingPublicContract(method)]))


class LegacyUnobserved:
    """Test-only baseline: the current runner forwards calls without observation."""
    def __init__(self, original_run, original_verify):
        self.original_run, self.original_verify, self.events = original_run, original_verify, []
    def run(self, *args, **kwargs): return self.original_run(*args, **kwargs)
    def verify(self, *args, **kwargs): return self.original_verify(*args, **kwargs)


class OrderedObservations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root/'ordsrc'
        self.output = self.root/'tests-3'; self.output.mkdir()
        self.fixture = self.output/'retained-temp'/'task'; self.fixture.mkdir(parents=True)
        self.workflow = self.source/'memory-integrity/scripts/memory_integrity_workflow.py'
        self.workflow.parent.mkdir(parents=True)
        self.marker = self.fixture/'launched'
        self.workflow.write_text('from pathlib import Path\nPath('+repr(str(self.marker))+').write_text("one")\nprint("public output")\n',encoding='utf-8')
        self.command = [sys.executable,'-B',str(self.workflow),'knowledge-retrieve',
            '--claude-mon-root',str(self.source/'claude-mon'),'--project-root',str(self.fixture),
            '--index-dir',str(self.fixture/'index'),'--policy-file',str(self.fixture/'policy.json'),
            '--task-file',str(self.fixture/'task.json'),'--query-text','work',
            '--evidence-pack',str(self.fixture/'community-single.json'),'--worker-python',sys.executable,
            '--strategy','community','--execution','single']
    def observer(self, verify=lambda *a: None):
        subject = runner()
        if hasattr(subject, 'Observation'):
            return subject.Observation(self.source, Path(sys.executable), self.output,
                                       subprocess.run, verify)
        return LegacyUnobserved(subprocess.run, verify)
    def pack(self, lease='a'*64):
        return {'pack_digest':'b'*64,'generation':'c'*64,
                'retrieval':{'engine':{'strategy':'community','execution':'single','generation_lease':lease}}}
    def test_wrong_initial_mode_is_refused_before_real_child_effect(self):
        self.command[-3] = 'vector'
        with self.assertRaisesRegex(ValueError, 'E_ORDERED_PUBLIC_ORDER'):
            self.observer().run(self.command,capture_output=True,text=True,timeout=90)
        self.assertFalse(self.marker.exists())
    def test_changed_public_timeout_is_refused_before_real_child_effect(self):
        with self.assertRaisesRegex(ValueError, 'E_ORDERED_PUBLIC_OPTIONS'):
            self.observer().run(self.command,capture_output=True,text=True,timeout=91)
        self.assertFalse(self.marker.exists())
    def test_public_result_is_real_and_recorded_not_replaced(self):
        observed = self.observer()
        result = observed.run(self.command,capture_output=True,text=True,timeout=90)
        self.assertEqual(result.returncode,0); self.assertEqual(result.stdout,'public output\n')
        self.assertEqual(self.marker.read_text(),'one')
        self.assertEqual(len(observed.events),1,'unobserved forwarding does not establish ordered-call evidence')
        row = observed.events[0]
        self.assertEqual(row['phase'],'public'); self.assertEqual(row['mode'],['community','single'])
        self.assertEqual(row['returncode'],0); self.assertEqual(row['stdout'],result.stdout)
        self.assertEqual(row['argv'],self.command)
    def test_replay_calls_original_once_and_retains_the_same_exception(self):
        calls = []; sentinel = object(); problem = ValueError('LEASE: original failure')
        def verify(pack,*args):
            calls.append((pack,args))
            if pack['retrieval']['engine']['generation_lease']=='0'*64: raise problem
            return sentinel
        observed = self.observer(verify)
        observed.run(self.command,capture_output=True,text=True,timeout=90)
        extra = ({},self.fixture,{}, {},object())
        original_pack = self.pack()
        self.assertIs(observed.verify(original_pack,*extra),sentinel)
        with self.assertRaises(ValueError) as caught:
            observed.verify(self.pack('0'*64),*extra)
        self.assertIs(caught.exception,problem)
        self.assertEqual(len(calls),2); self.assertIs(calls[0][0],original_pack)
        self.assertEqual([r['phase'] for r in observed.events],['public','replay','negative-lease'])
        self.assertTrue(observed.events[-1]['lease_refusal'])
    def test_replay_without_its_public_call_is_refused_before_verifier_effect(self):
        calls=[]
        observed=self.observer(lambda *args: calls.append(args))
        with self.assertRaisesRegex(ValueError,'E_ORDERED_REPLAY_ORDER'):
            observed.verify(self.pack(),{},self.fixture,{}, {},object())
        self.assertEqual(calls,[])


def complete_observation():
    modes=[('community','single'),('global','single'),('drift','single'),('vector','distributed-local')]
    events=[]
    for mode in modes:
        events.extend([{'phase':'public','mode':list(mode),'returncode':0},
                       {'phase':'replay','mode':list(mode),'returned':True},
                       {'phase':'negative-lease','mode':list(mode),'error_type':'ValueError',
                        'error':'E_LEASE','error_complete':True,'lease_refusal':True}])
    return {'target':TARGET,'selected_ids':[TARGET],
            'outcomes':{'started':[TARGET],'finished':[{'id':TARGET,'outcome':'PASS','reason':''}]},
            'subtests':[{'params':{'strategy':s,'execution':e},'outcome':'PASS','error':None} for s,e in modes],
            'events':events,'capture_errors':[],'observation_only':True,'gate1_complete':False}


def real_subtest_result(root, kinds, messages=None):
    """Real unittest callbacks/IDs/categories, not a hand-invented parent receipt."""
    modes=[('community','single'),('global','single'),('drift','single'),('vector','distributed-local')]
    messages=messages or {}
    records={'started':[],'finished':[]};subtests=[]
    class RemainingPublicContract(unittest.TestCase):
        def test_public_advanced_modes_source_closure_and_replay(self):
            for strategy,execution in modes:
                with self.subTest(strategy=strategy,execution=execution):
                    if kinds.get(strategy)=='FAIL': self.fail(messages.get(strategy,'synthetic assertion'))
                    if kinds.get(strategy)=='ERROR': raise ValueError(messages.get(strategy,'synthetic exception'))
    RemainingPublicContract.__module__='test_knowledge_completion'
    RemainingPublicContract.__qualname__='RemainingPublicContract'
    subject=runner()
    class Observed(subject.legacy.RecordingResult):
        def addSubTest(self,test,subtest,error):
            subtests.append({'params':dict(subtest.params),'outcome':'PASS' if error is None else 'FAIL',
                             'error':None if error is None else str(error[1])})
            super().addSubTest(test,subtest,error)
    Observed.records=records
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,resultclass=Observed,verbosity=2).run(
        unittest.TestSuite([RemainingPublicContract('test_public_advanced_modes_source_closure_and_replay')]))
    log=Path(tempfile.mkdtemp(dir=root))/'unittest.log';raw=stream.getvalue().encode('utf-8');log.write_bytes(raw)
    unit={'tests_run':result.testsRun,'discovered':1,'failures':[t.id() for t,_ in result.failures],
          'errors':[t.id() for t,_ in result.errors],'skipped':[], 'excluded':[],
          'expected_failures':[],'interrupted':False,'log':str(log),'log_sha256':hashlib.sha256(raw).hexdigest()}
    row=complete_observation();row['outcomes']=records;row['subtests']=subtests
    events=[]
    for mode in modes:
        block=[e for e in row['events'] if e['mode']==list(mode)]
        if kinds.get(mode[0])=='FAIL':
            block=block[:1];block[0].update(returncode=2,stderr='',stdout=json.dumps({
                'ok':False,'overall':'BLOCKED','evidence_class':'TEST_ONLY','adapter_calls':0,
                'approvals_consumed':0,'blockers':['ValueError: E_WORKER_TIMEOUT: no resend']}))
        elif kinds.get(mode[0])=='ERROR':
            block=block[:2];block[-1].pop('returned');block[-1].update(error_type='ValueError',
                error=messages.get(mode[0],'synthetic exception'),error_complete=True)
        events.extend(block)
    row['events']=events
    return row,unit,0 if result.wasSuccessful() else 1


class OrderedSubtestAccounting(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def test_actual_mixed_assertion_and_exception_ids_are_valid_failure_accounting(self):
        row,unit,code=real_subtest_result(self.root,{'community':'FAIL','vector':'ERROR'})
        self.assertEqual(unit['failures'],[TARGET+" (strategy='community', execution='single')"])
        self.assertEqual(unit['errors'],[TARGET+" (strategy='vector', execution='distributed-local')"])
        try: driver().validate_unit_receipt(unit,code,row)
        except ValueError as error:self.fail('real failed subtests must remain test failures, not accounting failure: '+str(error))
        self.assertEqual(code,1);self.assertEqual(row['outcomes']['finished'][0]['outcome'],'FAIL')
    def test_error_only_and_multiple_assertions_are_not_rejected_or_promoted(self):
        for kinds in ({'vector':'ERROR'},{'community':'FAIL','drift':'FAIL'}):
            with self.subTest(kinds=kinds):
                row,unit,code=real_subtest_result(self.root,kinds)
                try: driver().validate_unit_receipt(unit,code,row)
                except ValueError as error:self.fail('legitimate child accounting rejected: '+str(error))
                self.assertEqual(code,1)
    def test_wrong_parent_child_duplicate_category_exit_or_count_still_refuses(self):
        row,unit,code=real_subtest_result(self.root,{'community':'FAIL','vector':'ERROR'})
        for defect in ('parent-id','other-child','duplicate','category','missing-error','exit','count','interrupted'):
            with self.subTest(defect=defect):
                bad=copy.deepcopy(unit);badcode=code
                if defect=='parent-id':bad['failures']=[TARGET]
                elif defect=='other-child':bad['failures']=[TARGET+" (strategy='global', execution='single')"]
                elif defect=='duplicate':bad['failures']*=2
                elif defect=='category':bad['failures'],bad['errors']=bad['errors'],bad['failures']
                elif defect=='missing-error':bad['errors']=[]
                elif defect=='exit':badcode=0
                elif defect=='count':bad['tests_run']=True
                else:bad['interrupted']=True
                with self.assertRaisesRegex(ValueError,'E_ORDERED_UNIT_ACCOUNTING'):
                    driver().validate_unit_receipt(bad,badcode,row)
    def test_changed_test_log_cannot_supply_failure_categories(self):
        row,unit,code=real_subtest_result(self.root,{'vector':'ERROR'})
        Path(unit['log']).write_text('replaced',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'E_ORDERED_TEST_LOG|E_ORDERED_UNIT_ACCOUNTING'):
            driver().validate_unit_receipt(unit,code,row)
    def test_log_replacement_after_hash_cannot_swap_failure_and_error_categories(self):
        from unittest.mock import patch
        row,unit,code=real_subtest_result(self.root,{'community':'FAIL','vector':'ERROR'})
        bad=copy.deepcopy(unit);bad['failures'],bad['errors']=bad['errors'],bad['failures']
        subject=driver();original=subject.g.file_record;log=Path(unit['log'])
        replaced=log.read_text(encoding='utf-8').replace('ERROR: ','SWAP: ').replace('FAIL: ','ERROR: ').replace('SWAP: ','FAIL: ')
        def exchange_after_hash(path):
            record=original(path)
            if Path(path)==log:log.write_text(replaced,encoding='utf-8')
            return record
        # Real filesystem replacement at this one hash/read boundary; no fake
        # validator or mocked category result supplies the expected refusal.
        with patch.object(subject.g,'file_record',side_effect=exchange_after_hash):
            with self.assertRaisesRegex(ValueError,'E_ORDERED_TEST_LOG'):
                subject.validate_unit_receipt(bad,code,row)
    def test_earlier_timeout_does_not_hide_later_cleanup_diagnostic(self):
        root={'relation':'root','type':'ValueError','message':'E_DISTRIBUTED_CLEANUP','frames':[]}
        cause={'relation':'cause','type':'PermissionError','message':'synthetic file in use',
               'frames':[],'winerror':32,'errno':13,'filename':'synthetic-output'}
        detail={'schema_version':1,'exception':root,'chain':[root,cause],'frames':[],'truncated':False}
        text='E_WORKER_FAILED: ValueError: E_DISTRIBUTED_CLEANUP\nGATE1_CLEANUP_DIAGNOSTIC='+json.dumps(detail)
        row,unit,code=real_subtest_result(self.root,{'community':'FAIL','vector':'ERROR'},{'vector':text})
        try: state,details=driver().classify(row,unit,code)
        except ValueError as error:self.fail('genuine timeout must not mask later complete cleanup evidence: '+str(error))
        self.assertEqual(state,'CAUSE_OBSERVED_PENDING_REVIEW')
        self.assertEqual([d['mode'] for d in details],[['community','single'],['vector','distributed-local']])
        self.assertIn('E_WORKER_TIMEOUT',json.dumps(details[0]))
        self.assertEqual(details[1]['diagnostic'],detail)


class OrderedVerdict(unittest.TestCase):
    def classify(self, row):
        subject=runner()
        # Existing unobserved runner can only repeat the self-reported PASS.
        return subject.validate_ordered_result(row) if hasattr(subject,'validate_ordered_result') else 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE'
    def test_passing_test_label_without_replays_is_not_diagnostic_evidence(self):
        row=complete_observation(); row['events']=[]
        with self.assertRaisesRegex(ValueError,'E_ORDERED_PHASES'):
            self.classify(row)
    def test_missing_negative_lease_or_reordered_modes_cannot_pass(self):
        for mutate in ('missing','reordered'):
            with self.subTest(mutate=mutate):
                row=complete_observation()
                if mutate=='missing': row['events'].pop()
                else: row['events'][0],row['events'][3]=row['events'][3],row['events'][0]
                with self.assertRaisesRegex(ValueError,'E_ORDERED_PHASES'):
                    self.classify(row)
    def test_one_actual_skip_is_not_converted_to_success(self):
        row=complete_observation(); row['outcomes']['finished'][0]['outcome']='SKIP'
        with self.assertRaisesRegex(ValueError,'E_ORDERED_CASE_OUTCOME'):
            self.classify(row)
    def test_exact_four_triplets_still_mean_nonreproduction_not_gate1(self):
        self.assertEqual(self.classify(complete_observation()),'FAILURE_NOT_REPRODUCED_INCONCLUSIVE')
    def test_replay_crossing_the_next_public_boundary_is_not_ordered_evidence(self):
        row=complete_observation()
        # Keep public order AND every per-mode filtered order valid. The global
        # chronology alone is wrong: community refusal occurs after global public.
        row['events'].insert(3,row['events'].pop(2))
        with self.assertRaisesRegex(ValueError,'E_ORDERED_PHASES'):
            self.classify(row)


class OrderedStaging(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/'ordfix';self.output=self.root/'order-pinfix-v3-20261021'
        self.old_source=self.root/'source';self.old_source.mkdir()
        self.old_output=self.root/'image-successor-20261021';self.old_output.mkdir()
    def validate(self, source, output):
        subject=driver()
        if subject is not None:
            return subject.validate_new_paths(source,output,self.root,self.old_source,self.old_output)
    def test_different_path_depth_or_prefix_length_is_not_equivalent(self):
        for source,output in [(self.root/'long-source',self.output),
                              (self.source,self.root/'extra'/'order-pinfix-v3-20261021')]:
            with self.subTest(source=str(source),output=str(output)):
                with self.assertRaisesRegex(ValueError,'E_ORDERED_LAYOUT'):
                    self.validate(source,output)
    def test_existing_copy_is_not_reused_or_removed(self):
        self.source.mkdir(); marker=self.source/'keep';marker.write_text('unchanged')
        with self.assertRaisesRegex(ValueError,'E_ORDERED_EXISTING_ATTEMPT'):
            self.validate(self.source,self.output)
        self.assertEqual(marker.read_text(),'unchanged')
    def test_failed_history_check_has_zero_new_output_effects(self):
        def refuse(): raise PermissionError('retained evidence unreadable')
        subject=driver()
        with self.assertRaisesRegex(PermissionError,'retained evidence unreadable'):
            if subject is not None:
                subject.guarded_output(refuse,self.output,self.source,self.root,self.old_source,self.old_output)
            else:
                # Real legacy staging effect without the new before-write boundary.
                self.output.mkdir(); refuse()
        self.assertFalse(self.output.exists(),'history refusal must precede any successor output')
        self.assertFalse(self.source.exists())


class OrderedDriverContracts(unittest.TestCase):
    def test_selected_schema_validator_returns_a_real_contract_error_not_missing_api(self):
        sys.path.insert(0,str(ROOT/'memory-integrity/scripts'))
        from knowledge_bridge import retrieval_v2
        subject=driver()
        try:
            if hasattr(subject,'validate_pack_schema'): subject.validate_pack_schema({'malformed':True})
            else: retrieval_v2.validate_pack({'malformed':True})
        except Exception as error:
            self.assertIsInstance(error,ValueError,'a misspelled API would consume the real run without validating packs')
        else: self.fail('malformed pack was accepted')
    def test_nonzero_public_result_with_empty_json_is_not_hidden_as_json_failure(self):
        subject=driver(); row=complete_observation()
        row['events'][-3].update(returncode=2,stdout='',stderr='real child diagnostic')
        row['events']=row['events'][:-2]
        row['subtests'][-1].update(outcome='FAIL',error='real child diagnostic')
        row['outcomes']['finished'][0].update(outcome='FAIL',reason='real child diagnostic')
        with tempfile.TemporaryDirectory() as temporary:
            _,unit,_=real_subtest_result(Path(temporary),{'vector':'FAIL'})
            with self.assertRaisesRegex(ValueError,'E_CLEANUP_CHILD_EXIT: 2: real child diagnostic'):
                subject.classify(row,unit,1)
    def test_runner_exit_and_test_receipt_must_agree(self):
        subject=driver()
        unit={'tests_run':1,'discovered':1,'errors':[],'skipped':[],'excluded':[],
              'expected_failures':[],'interrupted':False,'failures':[]}
        with self.assertRaisesRegex(ValueError,'E_ORDERED_UNIT_ACCOUNTING'):
            subject.classify(complete_observation(),unit,1)


class OrderedBootstrapEntrypoint(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.output=self.root/'never-created'
    def invoke(self,helper=None,package=None):
        return subprocess.run([sys.executable,'-B',str(helper or ROOT/'.github/scripts/gate1_ordered_runner.py'),
            '--package-root',str(package or ROOT/'memory-integrity'),'--pattern','test_knowledge_completion.py',
            '--output-dir',str(self.output),'--bootstrap-only'],capture_output=True,text=True,encoding='utf-8',timeout=30)
    def test_real_entrypoint_accepts_unchanged_pinned_runner_without_any_worker_or_output(self):
        result=self.invoke()
        self.assertEqual(result.returncode,0,result.stderr)
        row=json.loads(result.stdout)
        self.assertEqual(row['status'],'ORDERED_BOOTSTRAP_VERIFIED_NO_WORKER')
        self.assertEqual(row['retained_sha256'],'4aba6fe49641f86dcb548219f0c6efc8bbd2fbaa4e32f5be40703a1cee18453b')
        self.assertFalse(row['worker_started']);self.assertFalse(self.output.exists())
    def tree(self):
        helpers=self.root/'helpers';helpers.mkdir()
        for name in ('gate1_ordered_runner.py','gate1_runner.py','retained_unittest.py'):
            shutil.copyfile(ROOT/'.github/scripts'/name,helpers/name)
        package=self.root/'memory-integrity';(package/'tests_v2').mkdir(parents=True)
        shutil.copyfile(ROOT/'memory-integrity/tests_v2/test_knowledge_completion.py',
                        package/'tests_v2/test_knowledge_completion.py')
        return helpers,package
    def test_untrusted_shadow_module_is_never_executed_by_bootstrap(self):
        helpers,package=self.tree();scripts=package/'scripts';scripts.mkdir()
        marker=self.root/'shadow-executed'
        (scripts/'retained_unittest.py').write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("bad")\n',encoding='utf-8')
        result=self.invoke(helpers/'gate1_ordered_runner.py',package)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(marker.exists());self.assertFalse(self.output.exists())
        self.assertEqual(Path(json.loads(result.stdout)['retained_path']),helpers/'retained_unittest.py')
    def test_changed_helper_is_refused_before_its_top_level_effect(self):
        helpers,package=self.tree();marker=self.root/'tampered-executed'
        with (helpers/'retained_unittest.py').open('a',encoding='utf-8') as stream:
            stream.write('\nfrom pathlib import Path\nPath('+repr(str(marker))+').write_text("bad")\n')
        result=self.invoke(helpers/'gate1_ordered_runner.py',package)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('E_ORDERED_RETAINED_RUNNER_CHANGED',result.stderr)
        self.assertFalse(marker.exists());self.assertFalse(self.output.exists())
    def test_missing_outcomes_report_exposes_real_child_stderr_not_file_error(self):
        subject=driver();child=subprocess.run([sys.executable,'-B','-c',
            "raise ValueError('E_ORDERED_RETAINED_RUNNER_CHANGED')"],capture_output=True,timeout=30)
        target=self.root/'child';target.mkdir()
        (target/'stderr.log').write_bytes(child.stderr);(target/'stdout.log').write_bytes(child.stdout)
        command={'stderr':subject.g.file_record(target/'stderr.log'),'stdout':subject.g.file_record(target/'stdout.log'),
                 'exit_code':child.returncode}
        try:
            if hasattr(subject,'read_runner_records'):
                subject.read_runner_records(self.output,command)
            else: json.loads((self.output/'Ordered-Outcomes.json').read_text(encoding='utf-8'))
        except Exception as error:
            self.assertIsInstance(error,ValueError)
            self.assertIn('E_ORDERED_RUNNER_STARTUP_FAILED',str(error))
            self.assertIn('E_ORDERED_RETAINED_RUNNER_CHANGED',str(error))
        else:self.fail('missing runner reports accepted')
        self.assertEqual((target/'stderr.log').read_bytes(),child.stderr)


if __name__ == '__main__':
    unittest.main()
