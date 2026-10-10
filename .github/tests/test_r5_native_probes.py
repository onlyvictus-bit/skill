import importlib.util
from pathlib import Path
import unittest
import datetime as dt

path=Path(__file__).resolve().parents[1]/'scripts/r5_native_probes.py'
spec=importlib.util.spec_from_file_location('probes',path)
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class ProbeContracts(unittest.TestCase):
    def test_signed_native_revision_tokens(self):
        for token in ['-1','1','-9223372036854775808','9223372036854775807']:
            self.assertTrue(p.valid_revision(token))
        for token in [None,'', '0','1.5','9223372036854775808','-9223372036854775809']:
            self.assertFalse(p.valid_revision(token))
    def test_naive_or_nonfinite_lease_refused(self):
        for value in ['2026-10-10T00:00:00', '', None, 'NaN']:
            with self.assertRaises(ValueError): p.lease_time(value)
    def test_actual_expiry_comparison(self):
        t=p.lease_time('2026-10-10T00:00:00Z')
        self.assertTrue(p.expired(t,t+dt.timedelta(seconds=1)))
        self.assertFalse(p.expired(t,t-dt.timedelta(seconds=1)))
    def test_capture_failure_is_never_semantic_refusal(self):
        for key,value in [('timed_out',True),('capture_complete',False),('capture_errors',['x']),('output_limit_exceeded',True)]:
            r={'exit_code':13,'stdout':b'','stderr':b'{"guard_mismatch":true}', 'timed_out':False,'capture_complete':True,'capture_errors':[],'output_limit_exceeded':False}; r[key]=value
            with self.assertRaises(ValueError): p.capture_ok(r)
    def test_guard_mismatch_requires_structured_exact_task(self):
        self.assertTrue(p.guard_mismatch(13,b'{"failed":[{"id":"p-1","guard_mismatch":true}]}','p-1'))
        for code,raw in [(1,b'exclusive lock'),(13,b'{"failed":[{"id":"p-2","guard_mismatch":true}]}'),(0,b'{"failed":[{"id":"p-1","guard_mismatch":true}]}')]:
            self.assertFalse(p.guard_mismatch(code,raw,'p-1'))
    def test_reclaim_bound_to_single_target(self):
        p.check_reclaim({'count':0,'reclaimed':None,'scoped':True},'p-1',None)
        p.check_reclaim({'count':1,'reclaimed':[{'id':'p-1','previous_owner':'A'}],'scoped':True},'p-1','A')
        for r in [{'count':1,'reclaimed':[{'id':'p-2','previous_owner':'A'}],'scoped':True},{'count':0,'reclaimed':None,'scoped':False}]:
            with self.assertRaises(ValueError): p.check_reclaim(r,'p-1','A')
    def test_raw_receipt_hash_binds_bytes(self):
        record=p.raw_record(b'one',b'two')
        p.verify_raw(record)
        record['stdout_sha256']='0'*64
        with self.assertRaises(ValueError):p.verify_raw(record)
    def test_counterfeit_summary_cannot_pass_as_native_evidence(self):
        import copy
        record=p.raw_record(b'{"unrelated":"not a native probe"}',b'')
        record.update(exit_code=1,capture_complete=True,timed_out=False,capture_errors=[],output_limit_exceeded=False)
        receipt={'schema':1,'ok':True,'overall':'REAL_NATIVE_PROBES_COMPLETED','commands':[copy.deepcopy(record) for _ in range(30)],'results':{
          'claim':{},'aba':{},'expiry':{'lease_expires_at':'2026-10-10T00:00:00Z','observed_at':'2026-10-10T00:05:01Z','elapsed_monotonic_seconds':301},
          'changed_owner':{'stale_write_refused':True},'native_conflict':{'native_refused':True},'compatible_merge':{'both_changes_retained':True}},
          'native_beads_qualified':False,'native_fencing_qualified':False,'native_merge_qualified':False,'shared_database_authorized':False}
        with self.assertRaises(ValueError):p.verify_receipt(receipt)
    def test_branch_name_error_is_not_native_conflict(self):
        self.assertFalse(p.native_conflict(1,b'branch r5probeconflict not found'))
        self.assertTrue(p.native_conflict(1,b'merge conflict with autocommit enabled'))
    def test_mixed_task_guard_and_malformed_empty_reclaim_refused(self):
        self.assertFalse(p.guard_mismatch(13,b'{"failed":[{"id":"p-1","guard_mismatch":true},{"id":"p-2","guard_mismatch":true}]}','p-1'))
        for value in [False,0,'',{}]:
            with self.assertRaises(ValueError):p.check_reclaim({'count':0,'reclaimed':value,'scoped':True},'p-1',None)
    def test_conditional_command_binds_exact_task_and_owner(self):
        good={'argv':['bd','--actor','A','--json','update','p-1','--title','x','--if-assignee','A','--if-status','in_progress']}
        p.bind_guard(good,'p-1','A')
        for key,value in [('p-1','p-2'),('A','B'),('in_progress','open')]:
            bad={'argv':[value if x==key else x for x in good['argv']]}
            with self.assertRaises(ValueError):p.bind_guard(bad,'p-1','A')
    def test_no_experiments_means_not_complete(self):
        with self.assertRaises(ValueError):p.verify_receipt({'schema':1,'ok':True,'commands':[],'results':{}})

if __name__=='__main__':unittest.main()
