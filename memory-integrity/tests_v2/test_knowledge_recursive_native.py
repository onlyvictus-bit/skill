"""Failure-first native-only dispatch gate and native fault controls."""
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
import ctypes
import hashlib
import json
import tempfile
import uuid
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).absolute().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))


class NativeDispatchWiring(unittest.TestCase):
    def setUp(self):
        from knowledge_bridge import recursive_bootstrap as b
        self.b=b;self.events=[];self.fail_gate=None
        events=self.events
        class Base:
            def __init__(process,args,**options):
                process.returncode=None;process._child_created=False
                process._execute_child(args,**options)
            def _execute_child(process,args,**options):
                events.append(('create',args,options.get('creationflags',0)))
                process.pid=99;process._handle=12345;process._child_created=True
        self.Base=Base
        self.profile={'variant':'OWNED_RUNTIME','selected':str(Path(sys.executable).absolute()),
            'deadline':time.monotonic()+120,'deadline_clock':b.deadline_clock(),
            'native_commands':{'git':{'root':'fixture-root'}}}
        owner=self
        class Job:
            handle=42
            def validate_native_root(job):events.append('root-verified')
            def finish_native_start(job,process,**options):
                events.append(('gate',process.pid,options['expected_image']))
                process._rp_native_proof={'identity':{'pid':process.pid,'created':123,'image':options['expected_image']},
                    'assigned':False,'member_before_resume':False,'resumed':False}
                owner.last_process=process
                if owner.fail_gate is not None:raise owner.fail_gate
                options['check_deadline']()
            def cleanup_native_start(job,process,error):
                events.append(('cleanup',process.pid,error))
                error.native_start_cleanup={'native_exit_proved':True,'failures':[]}
        self.job=Job()
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        for target,name,value in ((b,'validate_profile',lambda p:p),
                (b,'route_native',lambda a,s,o:([str(Path('git.exe').absolute())],
                    dict(o,executable=str(Path('git.exe').absolute())))),
                (b,'prepare_launch',lambda a,p,o,**kw:([p['selected']],dict(o,executable=p['selected']))),
                (b,'_publish_failure',lambda *a,**k:None)):
            self.stack.enter_context(patch.object(target,name,side_effect=value))
        self.stack.enter_context(patch.object(subprocess,'Popen',self.Base))
        self.guarded=b.install(self.profile)

    def native(self,**options):
        return self.guarded(['git','-C','fixture-root','rev-parse','HEAD'],**options)

    def test_native_creation_is_suspended_and_gate_finishes_before_return(self):
        self.guarded._rp_root_job=self.job
        process=self.native(creationflags=0x08000000)
        self.assertEqual(self.events[0],'root-verified')
        self.assertEqual(self.events[1][2],0x08000004)
        self.assertEqual(self.events[2],('gate',99,str(Path('git.exe').absolute())))
        self.assertEqual(process.args,['git','-C','fixture-root','rev-parse','HEAD'])

    def test_missing_job_refuses_before_a_native_process_exists(self):
        with self.assertRaisesRegex(ValueError,'NATIVE.*JOB|OWNED_ROOT_JOB'):
            self.native()
        self.assertEqual(self.events,[])

    def test_gate_failure_reaps_and_preserves_the_original(self):
        self.guarded._rp_root_job=self.job
        original=OSError('CONTROL_NATIVE_ASSIGN');self.fail_gate=original
        with self.assertRaises(OSError)as caught:self.native()
        self.assertIs(caught.exception,original)
        self.assertEqual(self.events[-1],('cleanup',99,original))

    def test_constructor_failure_retains_native_identity_and_cleanup_proof(self):
        self.guarded._rp_root_job=self.job
        original=OSError('CONTROL_ASSIGN_WITH_IDENTITY');self.fail_gate=original
        with self.assertRaises(OSError)as caught:self.native()
        retained=getattr(caught.exception,'native_start_proof',None)
        self.assertIsInstance(retained,dict)
        self.assertEqual(retained['native']['identity']['pid'],99)
        self.assertTrue(retained['cleanup']['native_exit_proved'])
        self.last_process._rp_native_proof['identity']['pid']=100
        self.assertEqual(retained['native']['identity']['pid'],99)
        self.assertIn('NATIVE_START_PROOF',str(caught.exception.__notes__))

    def test_controller_native_does_not_add_owned_gate_or_suspend_flag(self):
        self.profile['variant']='CONTROLLER_ONLY'
        self.native(creationflags=0x08000000)
        self.assertEqual(len(self.events),1)
        self.assertEqual(self.events[0][2],0x08000000)

    def test_recursive_python_route_keeps_its_existing_startup_path(self):
        self.guarded._rp_root_job=self.job
        self.guarded([self.profile['selected'],'-B','fixture.py'],creationflags=0)
        self.assertEqual(len(self.events),1)
        self.assertEqual(self.events[0][2],0)


class NativeCall:
    def __init__(self,api,name):self.api,self.name=api,name
    def __call__(self,*args):return self.api.call(self.name,args)


class NativeApi:
    def __init__(self):
        self.events=[];self.functions={};self.root_member=True;self.child_member=False
        self.child_exited=False;self.failure=None;self.assignment_effective=True
        self.image=str(Path('git.exe').absolute());self.process_id=99
    def __getattr__(self,name):
        if name.startswith('_'):raise AttributeError(name)
        if name not in self.functions:self.functions[name]=NativeCall(self,name)
        return self.functions[name]
    def call(self,name,args):
        self.events.append((name,args));ctypes.set_last_error(0)
        if name==self.failure:
            ctypes.set_last_error(5)
            if name=='CreateToolhelp32Snapshot':return ctypes.c_void_p(-1).value
            return 0xffffffff if name=='ResumeThread' else 0
        if name=='CreateJobObjectW':return 42
        if name=='GetCurrentProcess':return -1
        if name=='AssignProcessToJobObject':
            if args[1]!=-1 and self.assignment_effective:self.child_member=True
            return 1
        if name=='IsProcessInJob':
            args[2]._obj.value=int(self.root_member if args[0]==-1 else self.child_member);return 1
        if name=='GetProcessId':return self.process_id
        if name=='GetProcessTimes':
            for item in args[1:]:item._obj.dwHighDateTime=1;item._obj.dwLowDateTime=123
            return 1
        if name=='QueryFullProcessImageNameW':args[2].value=self.image;return 1
        if name=='WaitForSingleObject':return 0 if self.child_exited else 258
        if name=='CreateToolhelp32Snapshot':return 302
        if name=='Thread32First':args[1]._obj.owner=99;args[1]._obj.ident=7;return 1
        if name=='Thread32Next':ctypes.set_last_error(18);return 0
        if name=='OpenThread':return 301
        if name=='GetProcessIdOfThread':return 99
        if name=='ResumeThread':return 1
        if name=='CloseHandle':return 1
        raise AssertionError('Uncontrolled native API: '+name)


class NativeProcess:
    pid=99;_handle=12345;_child_created=True
    def __init__(self,api):
        self.api=api;self.events=[];self.returncode=None;self.kill_error=None;self.wait_error=None
    def poll(self):return 0 if self.api.child_exited else None
    def kill(self):
        self.events.append('kill')
        if self.kill_error:raise self.kill_error
        self.api.child_exited=True
    def wait(self,timeout):
        self.events.append(('wait',timeout))
        if self.wait_error:raise self.wait_error
        if not self.api.child_exited:raise TimeoutError('CONTROL_STILL_ALIVE')
        self.returncode=0;return 0


@unittest.skipUnless(os.name=='nt','Windows native API fault injection')
class NativeJobFaults(unittest.TestCase):
    def setUp(self):
        from knowledge_bridge import recursive_bootstrap as b
        self.b=b;self.api=NativeApi()
        with patch.object(b.ctypes,'WinDLL',return_value=self.api):self.job=b._OwnedRootJob()
        self.process=NativeProcess(self.api)
        self.stages=[]
    def finish(self,deadline=lambda:None):
        return self.job.finish_native_start(self.process,expected_image=self.api.image,
            check_deadline=deadline,progress=self.stages.append)
    def names(self):return [name for name,args in self.api.events]
    def child_assigns(self):
        return [args for name,args in self.api.events if name=='AssignProcessToJobObject' and args[1]==12345]

    def test_missing_membership_is_assigned_and_verified_before_single_resume(self):
        self.job.validate_native_root();self.finish()
        self.assertEqual(self.child_assigns(),[(42,12345)])
        self.assertTrue(self.api.child_member)
        self.assertLess(self.names().index('AssignProcessToJobObject',1),self.names().index('ResumeThread'))
        self.assertEqual(self.names().count('ResumeThread'),1)

    def test_existing_child_membership_is_verified_without_reassignment(self):
        self.api.child_member=True;self.finish()
        self.assertEqual(self.child_assigns(),[]);self.assertEqual(self.names().count('ResumeThread'),1)

    def test_root_membership_loss_refuses_before_resume(self):
        self.api.root_member=False
        with self.assertRaisesRegex(ValueError,'MEMBER|JOB'):self.job.validate_native_root()
        self.assertNotIn('ResumeThread',self.names())

    def test_assign_failure_is_native_error_and_child_never_resumes(self):
        self.api.failure='AssignProcessToJobObject'
        with self.assertRaises(OSError)as caught:self.finish()
        self.assertEqual(caught.exception.winerror,5);self.assertIn('ASSIGN',str(caught.exception.__notes__).upper())
        self.assertNotIn('ResumeThread',self.names())
        self.job.cleanup_native_start(self.process,caught.exception)
        self.assertEqual(self.process.events[0],'kill');self.assertTrue(self.api.child_exited)

    def test_successful_assign_return_without_membership_is_not_success(self):
        self.api.assignment_effective=False
        with self.assertRaisesRegex(ValueError,'MEMBER|JOB'):self.finish()
        self.assertNotIn('ResumeThread',self.names())

    def test_query_error_keeps_native_operation_and_blocks_resume(self):
        self.api.failure='IsProcessInJob'
        with self.assertRaises(OSError)as caught:self.finish()
        self.assertEqual(caught.exception.winerror,5);self.assertNotIn('ResumeThread',self.names())

    def test_wrong_native_image_blocks_resume(self):
        with self.assertRaisesRegex(ValueError,'IMAGE|IDENTITY'):
            self.job.finish_native_start(self.process,expected_image=str(Path('other.exe').absolute()),
                check_deadline=lambda:None,progress=self.stages.append)
        self.assertNotIn('ResumeThread',self.names())

    def test_wrong_native_pid_blocks_resume(self):
        self.api.process_id=100
        with self.assertRaisesRegex(ValueError,'PID|IDENTITY'):self.finish()
        self.assertNotIn('ResumeThread',self.names())

    def test_partial_identity_observation_remains_unknown_on_native_query_error(self):
        self.api.failure='GetProcessTimes'
        with self.assertRaises(OSError)as caught:self.finish()
        self.job.cleanup_native_start(self.process,caught.exception)
        self.b._retain_native_failure(self.process,caught.exception)
        identity=caught.exception.native_start_proof['native']['identity']
        self.assertEqual(identity['pid'],99)
        self.assertIsNone(identity['created']);self.assertIsNone(identity['image'])
        self.assertEqual(caught.exception.winerror,5)
        self.assertNotIn('ResumeThread',self.names())

    def test_deadline_expiry_never_resumes_child(self):
        def expired():raise ValueError('CONTROL_SHARED_DEADLINE')
        with self.assertRaisesRegex(ValueError,'CONTROL_SHARED_DEADLINE'):self.finish(expired)
        self.assertNotIn('ResumeThread',self.names())

    def test_final_deadline_expiry_after_enumeration_never_resumes_child(self):
        calls=[]
        def expires_last():
            calls.append('check')
            if len(calls)==3:raise ValueError('CONTROL_FINAL_RESUME_DEADLINE')
        with self.assertRaisesRegex(ValueError,'CONTROL_FINAL_RESUME_DEADLINE'):
            self.finish(expires_last)
        self.assertIn('GetProcessIdOfThread',self.names())
        self.assertNotIn('ResumeThread',self.names())

    def test_resume_error_is_original_windows_error(self):
        self.api.failure='ResumeThread'
        with self.assertRaises(OSError)as caught:self.finish()
        self.assertEqual(caught.exception.winerror,5)
        self.assertIn('RESUME',str(caught.exception.__notes__).upper())

    def test_resume_handle_close_error_retains_debt_and_attempts_both_closes(self):
        self.api.failure='CloseHandle'
        with self.assertRaises(OSError)as caught:self.finish()
        closed=[args[0]for name,args in self.api.events if name=='CloseHandle']
        self.assertIn(301,closed);self.assertIn(302,closed)
        self.assertIn('CLOSE',str(caught.exception.__notes__).upper())
        self.job.cleanup_native_start(self.process,caught.exception)
        self.assertTrue(self.api.child_exited)

    def test_cleanup_attempts_wait_when_kill_fails_and_preserves_primary(self):
        original=ValueError('CONTROL_ASSIGN_PRIMARY')
        self.process.kill_error=OSError('CONTROL_KILL');self.process.wait_error=TimeoutError('CONTROL_WAIT')
        self.job.cleanup_native_start(self.process,original)
        self.assertEqual(str(original),'CONTROL_ASSIGN_PRIMARY')
        self.assertTrue(any(event[0]=='wait'for event in self.process.events if isinstance(event,tuple)))
        self.assertIn('CONTROL_KILL',str(original.__notes__))
        self.assertNotIn('TerminateJobObject',self.names())

    def test_cleanup_already_exited_child_waits_without_killing(self):
        self.api.child_exited=True;original=ValueError('primary')
        self.job.cleanup_native_start(self.process,original)
        self.assertNotIn('kill',self.process.events)
        self.assertTrue(any(isinstance(event,tuple)and event[0]=='wait'for event in self.process.events))

    def test_unpublished_raw_create_state_is_unknown_and_not_claimed_reaped(self):
        self.process._child_created=False;self.process._handle=None
        original=OSError('CONTROL_PARTIAL_BASE_CREATE')
        self.job.cleanup_native_start(self.process,original)
        self.assertIn('UNKNOWN',str(original.__notes__).upper())
        self.assertEqual(self.process.events,[])

    def test_full_native_failure_sidecar_is_bound_by_old_failure_record(self):
        self.api.failure='AssignProcessToJobObject'
        with self.assertRaises(OSError)as caught:self.finish()
        original=caught.exception
        self.job.cleanup_native_start(self.process,original)
        self.b._retain_native_failure(self.process,original)
        with tempfile.TemporaryDirectory(prefix='native-failure-proof-')as name:
            root=Path(name);nonce=uuid.uuid4().hex
            profile={'requests':str(root),'selected':sys.executable,'image':sys.executable,
                     'deadline':time.monotonic()+120,'deadline_clock':self.b.deadline_clock()}
            self.b._publish_failure('dispatch',nonce,'native-assign',profile,root,original,
                env={},argv=['git','-C','fixture','rev-parse','HEAD'],started='UNKNOWN')
            raw=(root/('rp1-dispatch-'+nonce+'.native.json')).read_bytes()
            native=json.loads(raw)
            value=json.loads((root/('rp1-dispatch-'+nonce+'.failure.json')).read_bytes())
            self.assertTrue(self.b.validate_failure_record(value))
            self.assertEqual(native,original.native_start_proof)
            self.assertEqual(native['native']['identity']['pid'],99)
            self.assertTrue(native['native']['assignment_attempted'])
            self.assertFalse(native['native']['assigned'])
            self.assertTrue(native['cleanup']['native_exit_proved'])
            self.assertIn(hashlib.sha256(raw).hexdigest(),value['notes'][0])
            self.assertIn('NATIVE_START_PROOF_FILE',value['notes'][0])


if __name__=='__main__':unittest.main(verbosity=2)
