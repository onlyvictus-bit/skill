"""MP1 controller contracts; selected-runtime membership is separate evidence."""
import importlib.util
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).absolute().parents[1]


class MembershipContracts(unittest.TestCase):
    def setUp(self):
        path = HERE/'scripts/cleanup_membership_probe.py'
        if not path.exists():
            self.fail('MP1 native membership witness is not implemented')
        spec = importlib.util.spec_from_file_location('mp1_contract_probe', path)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def snapshot(self):
        roles = {}
        for number, role in enumerate(('root','relay','launcher','child'), 1):
            roles[role] = {'pid':number, 'creation':str(100+number),
                           'ppid':number-1, 'parent_creation':str(99+number),
                           'in_job':True, 'signalled':False}
        return {'members':[1,2,3,4], 'assigned':4, 'listed':4,
                'total':4, 'active':4, 'roles':roles}

    def test_cumulative_total_is_not_current_membership(self):
        row = self.snapshot(); row['total'] = 9
        self.m.validate_snapshot(row)

    def test_snapshot_json_key_order_has_no_identity_meaning(self):
        self.m.validate_snapshot(json.loads(json.dumps(self.snapshot(),sort_keys=True)))

    def test_current_count_and_list_disagreement_is_refused(self):
        row = self.snapshot(); row['active'] = 3
        with self.assertRaisesRegex(ValueError, 'E_MP_MEMBERSHIP'):
            self.m.validate_snapshot(row)

    def test_lifetime_total_cannot_be_less_than_current_active(self):
        row = self.snapshot(); row['total'] = 1
        with self.assertRaisesRegex(ValueError, 'E_MP_MEMBERSHIP'):
            self.m.validate_snapshot(row)

    def test_duplicate_pid_and_wrong_parent_birth_are_refused(self):
        for field, value in (('pid',2), ('parent_creation','999')):
            row = self.snapshot(); row['roles']['child'][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'E_MP_CHAIN'):
                self.m.validate_snapshot(row)

    def test_native_membership_must_agree_with_returned_pid_list(self):
        row = self.snapshot(); row['roles']['child']['in_job'] = False
        with self.assertRaisesRegex(ValueError, 'E_MP_MEMBERSHIP'):
            self.m.validate_snapshot(row)

    def test_outside_live_child_is_a_gap_not_a_fix(self):
        row = self.snapshot(); row['members'] = [1,2]
        row.update(assigned=2, listed=2, active=2, total=2)
        for role in ('launcher','child'): row['roles'][role]['in_job'] = False
        self.m.validate_snapshot(row)
        result = self.m.classify(row, {'root':True,'relay':True,'launcher':False,'child':False}, True, 'writer still alive')
        self.assertEqual(result, 'MEMBERSHIP_GAP_OBSERVED_NOT_FIXED')

    def test_inside_survivor_requires_design_pivot(self):
        result = self.m.classify(self.snapshot(), {'root':True,'relay':True,'launcher':True,'child':False}, True, 'failed')
        self.assertEqual(result, 'MEMBERSHIP_CONTRADICTION_REQUIRES_REDESIGN')

    def test_all_dead_with_writer_alive_is_pipe_gap(self):
        result = self.m.classify(self.snapshot(), dict.fromkeys(('root','relay','launcher','child'), True), True, 'failed')
        self.assertEqual(result, 'PIPE_CANCELLATION_GAP_NOT_FIXED')

    def test_all_clean_is_inconclusive_not_historical_rootcause(self):
        result = self.m.classify(self.snapshot(), dict.fromkeys(('root','relay','launcher','child'), True), False, None)
        self.assertEqual(result, 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE')

    def test_a_real_stop_error_is_not_called_failure_not_reproduced(self):
        result = self.m.classify(self.snapshot(), dict.fromkeys(('root','relay','launcher','child'), True),
                                False, ['ValueError: E_SHARD_TREE_UNOBSERVED_MEMBER'])
        self.assertEqual(result, 'STOP_FAILURE_WITH_ALL_HANDLES_EXITED_NOT_FIXED')

    def test_observer_errors_prohibit_usable_classification(self):
        with self.assertRaisesRegex(ValueError, 'E_MP_OBSERVATION'):
            self.m.classify(self.snapshot(), dict.fromkeys(('root','relay','launcher','child'), True), False, None,
                            observation_errors=['membership read failed'])


class MembershipCoordinatorContracts(unittest.TestCase):
    def setUp(self):
        path = HERE/'scripts/cleanup_membership_diagnostic.py'
        if not path.exists():
            self.fail('MP1 sealed coordinator is not implemented')
        spec = importlib.util.spec_from_file_location('mp1_controller_contract', path)
        self.m = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.m)

    def valid_probe(self):
        return {'scope':'MP1_MEMBERSHIP_ONLY_NOT_FIX',**dict.fromkeys(self.m.FALSE_FLAGS,False),
                'fixture_topology':'SELECTED_VENV_ORIGINAL_RELAY_CHILD',
                'writer_alive_after_stop':False,
                'emergency_cleanup':{'completed':True,'errors':[],'writer_joined':True,
                                     'streams_closed':True,'root_reaped':True,'job_closed':True,
                                     'roles_signalled':dict.fromkeys(('root','relay','launcher','child'),True)},
                'handle_cleanup':{'completed':True,'errors':[]},
                'before':{},'after':{},'stop_error':None,'observation_errors':[],
                'status':'FAILURE_NOT_REPRODUCED_INCONCLUSIVE'}

    def test_unchanged_budgets_are_required(self):
        self.m.validate_budgets({'request':.1,'shutdown':5,'watchdog':60,'default':120,'emergency':5})
        for key, value in (('shutdown',6),('request',1),('watchdog',120),('emergency',10)):
            row = dict(self.m.BUDGETS); row[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'E_MP_BUDGET'):
                self.m.validate_budgets(row)

    def test_timed_out_capture_cannot_be_a_completed_membership_probe(self):
        from types import SimpleNamespace
        row = {'failure':None,'exit_code':0,'execution':'EXITED','containment':{
            'capture_complete':True,'capture_errors':[], 'output_limit_exceeded':False,
            'timed_out':False,'tree_contained':True}}
        self.m.check_capture(SimpleNamespace(returncode=0), row)
        row['containment']['timed_out'] = True
        with self.assertRaisesRegex(ValueError, 'E_MP_CAPTURE'):
            self.m.check_capture(SimpleNamespace(returncode=0), row)

    def test_missing_completed_process_is_never_success(self):
        row = {'failure':None,'exit_code':0,'execution':'EXITED','containment':{
            'capture_complete':True,'capture_errors':[], 'output_limit_exceeded':False,
            'timed_out':False,'tree_contained':True}}
        with self.assertRaisesRegex(ValueError, 'E_MP_CAPTURE'):
            self.m.check_capture(None, row)

    def test_capture_refusal_and_boolean_exit_are_not_accepted(self):
        row = {'failure':None,'exit_code':0,'execution':'EXITED','containment':{
            'capture_complete':True,'capture_errors':[], 'output_limit_exceeded':False,
            'timed_out':False,'tree_contained':False}}
        with self.assertRaisesRegex(ValueError, 'E_MP_CAPTURE'):
            self.m.check_capture(SimpleNamespace(returncode=0), row)
        row['containment']['tree_contained'] = True
        with self.assertRaisesRegex(ValueError, 'E_MP_CAPTURE'):
            self.m.check_capture(SimpleNamespace(returncode=False), row)

    def test_no_product_or_old_helper_is_a_write_target(self):
        self.assertEqual(set(self.m.SUPPORT), {'.github/scripts/cleanup_membership_probe.py'})
        self.assertEqual(self.m.ROOT.name, 'cleanup-membership-20261025')
        self.assertEqual(self.m.OUTPUT.parent, self.m.ROOT)

    def test_setup_failure_is_retained_as_failure_not_a_lost_receipt(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); contract = root/'Inputs.json'; output = root/'new-output'
            with contract.open('x',encoding='utf-8') as stream: json.dump({},stream)
            def record(path):
                return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':path.stat().st_size}
            def save(path,value):
                with path.open('x',encoding='utf-8') as stream: json.dump(value,stream)
            def support(_name): raise OSError('CONTROL_SUPPORT_SETUP')
            c1 = SimpleNamespace(normal_account=lambda:None, sha=lambda raw:hashlib.sha256(raw).hexdigest(),
                                 read_file=lambda path:path.read_bytes(), ordinary=lambda path:None,
                                 load_support=support, record=record, save=save)
            with patch.object(self.m,'CONTRACT',contract), patch.object(self.m,'OUTPUT',output), \
                 patch.object(self.m,'context',return_value=(None,None,None,c1)), \
                 patch.object(self.m,'verify'), contextlib.redirect_stdout(io.StringIO()) as console:
                self.assertEqual(self.m.run(record(contract)['sha256']),1)
            self.assertEqual(json.loads(console.getvalue())['status'],'PARTIAL_OR_FAILED_NO_RETRY')
            receipt = json.loads((output/'Receipt.json').read_text())
            self.assertIn('CONTROL_SUPPORT_SETUP',receipt['failure'])
            self.assertFalse(receipt['attempt_consumed'])
            self.assertEqual(receipt['status'],'PARTIAL_OR_FAILED_NO_RETRY')
            self.assertFalse(receipt['stage_complete'])

    def test_emergency_cleanup_or_true_readiness_cannot_promote_a_probe(self):
        result = {'scope':'MP1_MEMBERSHIP_ONLY_NOT_FIX','stage_complete':False,
                  'fixture_topology':'SELECTED_VENV_ORIGINAL_RELAY_CHILD',
                  'gate1_complete':False,'fix_validated':False,'root_cause_confirmed':False,
                  'release_ready':False,'installed':False,'producer_authentication':False,
                  'writer_alive_after_stop':False,'emergency_cleanup':{'completed':False}}
        with self.assertRaisesRegex(ValueError,'E_MP_EMERGENCY_INCOMPLETE'):
            self.m.validate_probe(result,None)
        result['stage_complete'] = True
        with self.assertRaisesRegex(ValueError,'E_MP_PROBE_SCOPE'):
            self.m.validate_probe(result,None)

    def test_synthetic_controller_topology_cannot_be_selected_runtime_proof(self):
        result = self.valid_probe()
        probe = SimpleNamespace(classify=lambda *args,**kwargs:'FAILURE_NOT_REPRODUCED_INCONCLUSIVE')
        self.m.validate_probe(result,probe)
        result['fixture_topology'] = 'CONTROLLER_C314_SYNTHETIC_FOUR_PROCESS_NOT_SELECTED_RUNTIME_PROOF'
        with self.assertRaisesRegex(ValueError,'E_MP_PROBE_SCOPE'):
            self.m.validate_probe(result,probe)

    def test_every_probe_qualification_flag_must_be_present_and_false(self):
        result = self.valid_probe()
        probe = SimpleNamespace(classify=lambda *args,**kwargs:'FAILURE_NOT_REPRODUCED_INCONCLUSIVE')
        self.m.validate_probe(result,probe)
        for flag in self.m.FALSE_FLAGS:
            for missing in (False,True):
                candidate = dict(result)
                if missing: candidate.pop(flag)
                else: candidate[flag] = True
                with self.subTest(flag=flag,missing=missing), self.assertRaisesRegex(ValueError,'E_MP_PROBE_SCOPE'):
                    self.m.validate_probe(candidate,probe)

    def test_cleanup_success_label_cannot_hide_errors_or_missing_exit_proof(self):
        probe = SimpleNamespace(classify=lambda *args,**kwargs:'FAILURE_NOT_REPRODUCED_INCONCLUSIVE')
        for field,value in (('errors',['CONTROL_STREAM_CLOSE']),('errors',None),
                            ('writer_joined',False),('roles_signalled',{}),
                            ('streams_closed',False),('root_reaped',False),('job_closed',False),
                            ('streams_closed',None),('root_reaped',None),('job_closed',None),
                            ('roles_signalled',dict.fromkeys(('root','relay','launcher','child'),False))):
            result = self.valid_probe(); result['emergency_cleanup'][field] = value
            with self.subTest(field=field,value=value), self.assertRaisesRegex(ValueError,'E_MP_EMERGENCY_INCOMPLETE'):
                self.m.validate_probe(result,probe)

    def test_native_handle_finalization_must_be_present_complete_and_error_free(self):
        probe = SimpleNamespace(classify=lambda *args,**kwargs:'FAILURE_NOT_REPRODUCED_INCONCLUSIVE')
        for value in (None,{}, {'completed':False,'errors':[]},
                      {'completed':True,'errors':['CONTROL_NATIVE_CLOSE']}):
            result = self.valid_probe()
            if value is None: result.pop('handle_cleanup')
            else: result['handle_cleanup'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError,'E_MP_HANDLE_CLEANUP_INCOMPLETE'):
                self.m.validate_probe(result,probe)


if __name__ == '__main__': unittest.main()
