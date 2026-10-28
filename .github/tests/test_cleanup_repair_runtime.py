"""Guard new CR3 inputs without launching the selected numerical runtime."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).absolute().parents[1]/'scripts/cleanup_repair_runtime.py'
spec = importlib.util.spec_from_file_location('cleanup_repair_control_tests', SCRIPT)
cr = importlib.util.module_from_spec(spec); spec.loader.exec_module(cr)


class CleanupRepairInputs(unittest.TestCase):
    def test_only_named_modification_and_addition_are_accepted(self):
        self.assertTrue(cr.validate_delta({'source': 'old', 'cache': 'keep'},
                                         {'source': 'new', 'helper': 'new', 'cache': 'keep'},
                                         {'source', 'helper'}))

    def test_unrelated_change_and_missing_original_are_rejected(self):
        for after in ({'source': 'new', 'cache': 'changed'}, {'source': 'new'}):
            with self.subTest(after=after), self.assertRaisesRegex(ValueError, 'E_CR_UNAPPROVED_DELTA'):
                cr.validate_delta({'source': 'old', 'cache': 'keep'}, after, {'source'})

    def test_unrelated_added_file_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'E_CR_UNAPPROVED_DELTA'):
            cr.validate_delta({'source': 'old'}, {'source': 'new', 'surprise': 'x'}, {'source'})

    def test_error_only_overlay_is_reversible(self):
        self.assertEqual(cr.error_overlay(b'before\nold-handler\nafter', b'old-handler', b'detail-handler'),
                         b'before\ndetail-handler\nafter')

    def test_missing_or_ambiguous_error_handler_is_rejected(self):
        for raw in (b'absent', b'handler handler'):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, 'E_CR_ERROR_OVERLAY'):
                cr.error_overlay(raw, b'handler', b'detail')

    def control_report(self):
        runner = cr.load('gate1_ordered_runner')
        root = {'relation':'root', 'type':'ValueError', 'message':'E_DISTRIBUTED_CLEANUP', 'frames':[]}
        cause = {'relation':'cause', 'type':'PermissionError', 'message':'CONTROL_DENIED',
                 'errno':13, 'filename':'control-output', 'frames':[]}
        detail = {'schema_version':1, 'exception':root, 'chain':[root,cause], 'frames':[], 'truncated':False}
        blocker = 'ValueError: E_WORKER_FAILED: ValueError: E_DISTRIBUTED_CLEANUP\nGATE1_CLEANUP_DIAGNOSTIC='+json.dumps(detail)
        report = {'target':runner.TARGET, 'selected_ids':[runner.TARGET],
            'outcomes':{'started':[runner.TARGET], 'finished':[{'id':runner.TARGET, 'outcome':'FAIL'}]},
            'capture_errors':[], 'subtests':[], 'events':[]}
        for strategy, execution in runner.MODES:
            mode = [strategy, execution]
            vector = strategy == 'vector'
            report['subtests'].append({'params':{'strategy':strategy,'execution':execution},
                                       'outcome':'FAIL' if vector else 'PASS'})
            report['events'].append({'phase':'public', 'mode':mode, 'returncode':2 if vector else 0,
                'stdout':json.dumps({'ok':False, 'overall':'BLOCKED', 'evidence_class':'TEST_ONLY',
                    'adapter_calls':0, 'approvals_consumed':0, 'blockers':[blocker]}) if vector else '', 'stderr':''})
            if not vector:
                report['events'].extend([{'phase':'replay','mode':mode,'returned':True},
                    {'phase':'negative-lease','mode':mode,'lease_refusal':True,
                     'error_type':'ValueError','error_complete':True}])
        return report

    def validate_control(self, report, code):
        self.assertTrue(callable(getattr(cr, 'validate_control', None)), 'strict negative-control gate missing')
        return cr.validate_control(report, code)

    def test_exact_initial_vector_cleanup_is_the_only_accepted_negative_control(self):
        self.validate_control(self.control_report(), 1)

    def test_unrelated_failure_alongside_vector_cleanup_is_rejected(self):
        report = self.control_report()
        report['subtests'][0]['outcome'] = 'FAIL'
        report['events'][0]['returncode'] = 2
        report['events'][0]['stdout'] = 'UNRELATED_COMMUNITY_FAILURE'
        with self.assertRaisesRegex(ValueError, 'E_CR_UNEXPECTED_CONTROL_FAILURE'):
            self.validate_control(report, 1)

    def test_replay_cleanup_instead_of_original_initial_cleanup_is_rejected(self):
        report = self.control_report()
        report['events'][-1]['returncode'] = 0
        report['events'].append({'phase':'replay', 'mode':['vector','distributed-local'],
                                  'error':'E_DISTRIBUTED_CLEANUP'})
        with self.assertRaisesRegex(ValueError, 'E_CR_UNEXPECTED_CONTROL_FAILURE'):
            self.validate_control(report, 1)

    def test_wrapper_without_complete_cleanup_cause_is_rejected(self):
        report = self.control_report()
        reply = json.loads(report['events'][-1]['stdout'])
        reply['blockers'][0] = reply['blockers'][0].split('\n', 1)[0]
        report['events'][-1]['stdout'] = json.dumps(reply)
        with self.assertRaisesRegex(ValueError, 'E_CR_UNEXPECTED_CONTROL_FAILURE'):
            self.validate_control(report, 1)

    def test_all_pass_control_is_non_reproduction_not_a_failure(self):
        report = self.control_report()
        report['outcomes']['finished'][0]['outcome'] = 'PASS'
        report['subtests'][-1]['outcome'] = 'PASS'
        report['events'][-1].update(returncode=0, stdout='')
        mode = ['vector','distributed-local']
        report['events'].extend([{'phase':'replay','mode':mode,'returned':True},
            {'phase':'negative-lease','mode':mode,'lease_refusal':True,
             'error_type':'ValueError','error_complete':True}])
        self.validate_control(report, 0)

    def test_post_output_setup_failure_retains_failed_receipt_without_workload(self):
        for stage in ('support-import', 'environment'):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory(prefix='cr3-setup-failure-') as name:
                output = Path(name)/'comparison'
                def require(condition, error):
                    if not condition:
                        raise ValueError(error)
                def save(path, value):
                    with path.open('x', encoding='utf-8') as stream:
                        json.dump(value, stream)
                host = SimpleNamespace(capture_owned=Mock(side_effect=AssertionError('WORKLOAD_MUST_NOT_START')))
                setup_error = OSError('CONTROL_SETUP_FAILURE_' + stage)
                def support(role):
                    if stage == 'support-import':
                        raise setup_error
                    return host if role == 'offline_host_validation' else SimpleNamespace()
                c1 = SimpleNamespace(normal_account=lambda: None, sha=lambda _: 'sealed',
                    read_file=lambda _: b'{}', require=require, HEAD='test-head',
                    ordinary=lambda _: None, record=lambda path: {'path':str(path)},
                    load_support=support, save=save)
                c2 = SimpleNamespace(environment=Mock(side_effect=setup_error))
                def load(role):
                    return c1 if role == 'gate1_current_preflight' else c2
                caught = None
                with patch.object(cr, 'OUTPUT', output), patch.object(cr, 'load', side_effect=load), \
                     patch.object(cr, 'verify'):
                    try:
                        code = cr.run('sealed')
                    except Exception as error:
                        caught = error
                receipt = output/'Receipt.json'
                self.assertTrue(receipt.is_file(), 'post-output setup error escaped receipt handling: '+repr(caught))
                value = json.loads(receipt.read_text(encoding='utf-8'))
                self.assertEqual(code, 1)
                self.assertEqual(value['status'], 'PARTIAL_OR_FAILED_NO_RETRY')
                self.assertIn(str(setup_error), value['failure'])
                self.assertFalse(value['workload_attempt_consumed'])
                self.assertFalse(value['gate1_complete'])
                self.assertEqual(value['commands'], [])
                self.assertFalse((output/'workload-claim').exists())
                host.capture_owned.assert_not_called()


if __name__ == '__main__': unittest.main()
