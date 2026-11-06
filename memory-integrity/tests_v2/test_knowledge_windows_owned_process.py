"""Real current-image Job owner controls; no worker request or writer is involved."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


@unittest.skipUnless(os.name == "nt", "Windows Job/process-handle proof required")
class CurrentImageOwnerTests(unittest.TestCase):
    def setUp(self):
        from knowledge_bridge.windows_owned_process import launch_current
        self.launch_current = launch_current
        # The retained runner owns scratch selection. Do not mutate its global
        # tempfile setting or create a second fixture tree outside its guard.
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL

    def _handle(self, pid):
        handle = self.kernel.OpenProcess(0x100000, False, pid)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def _wait_file(self, path, until):
        while time.monotonic() < until:
            if path.exists(): return
            time.sleep(.005)
        self.fail("fixture did not reach its native-ready marker")

    def test_stop_reaps_root_child_grandchild_but_not_unrelated_process(self):
        with tempfile.TemporaryDirectory(prefix="sr3-owned-tree-") as name:
            cwd = Path(name); child = cwd / "child.py"; script = cwd / "root.py"; ready = cwd / "tree.json"
            unrelated_ready = cwd / "unrelated-ready"
            grandchild = cwd / 'grandchild.py'
            grandchild.write_text("import json,os,sys,time\nfrom pathlib import Path\nroot=Path(sys.argv[1])\ndata=json.loads((root/'tree.json').read_text())\ndata['grandchild']=os.getpid(); (root/'tree.json').write_text(json.dumps(data))\ntime.sleep(60)\n", encoding="utf-8")
            child.write_text("import json,os,subprocess,sys,time\nfrom pathlib import Path\nroot=Path(sys.argv[1])\ndata=json.loads((root/'tree.json').read_text())\ndata['child']=os.getpid(); (root/'tree.json').write_text(json.dumps(data))\nsubprocess.Popen([sys.executable,'-B',str(root/'grandchild.py'),str(root)])\ntime.sleep(60)\n", encoding="utf-8")
            script.write_text("import json,os,subprocess,sys,time\nfrom pathlib import Path\nroot=Path.cwd()\ndata={'root':os.getpid()}; (root/'tree.json').write_text(json.dumps(data))\nsubprocess.Popen([sys.executable,'-B',str(root/'child.py'),str(root)])\ntime.sleep(60)\n", encoding="utf-8")
            unrelated = subprocess.Popen([sys.executable, "-B", "-c", "from pathlib import Path; import time; Path(r" + repr(str(unrelated_ready)) + ").write_text('ready'); time.sleep(60)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            owner = None; handles = []
            try:
                self._wait_file(unrelated_ready, time.monotonic()+5)
                owner = self.launch_current(subprocess.Popen, sys.executable, script, deadline=time.monotonic()+10,
                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=cwd)
                self._wait_file(ready, time.monotonic()+5)
                until = time.monotonic()+5
                while time.monotonic() < until:
                    try: data = json.loads(ready.read_text(encoding="utf-8"))
                    except json.JSONDecodeError:
                        time.sleep(.005); continue  # Fixture marker still being written.
                    if "grandchild" in data: break
                    time.sleep(.005)
                else: self.fail("fixture did not create grandchild")
                self.assertEqual(data["root"], owner.process.pid)
                handles = [self._handle(data[key]) for key in ("root", "child", "grandchild")]
                owner.stop(time.monotonic()+5)
                self.assertTrue(owner.proof["termination"]["native_exit_proved"])
                for handle in handles: self.assertEqual(self.kernel.WaitForSingleObject(handle, 0), 0)
                self.assertIsNone(unrelated.poll(), "owner must not PID-sweep unrelated processes")
                owner.release()
                (cwd/'Native-exit-proof.json').write_text(json.dumps(owner.proof, sort_keys=True), encoding='utf-8')
            finally:
                for handle in handles: self.kernel.CloseHandle(handle)
                if owner is not None and owner.proof.get("released") is not True:
                    try: owner.stop(time.monotonic()+5); owner.release()
                    except Exception: pass
                unrelated.kill(); unrelated.wait(timeout=5)

    def test_rejects_requested_executable_identity_drift_before_start(self):
        with tempfile.TemporaryDirectory(prefix="sr3-owned-identity-") as name:
            cwd = Path(name); script = cwd / "never.py"; marker = cwd / "must-not-run"
            script.write_text("from pathlib import Path; Path(" + repr(str(marker)) + ").write_text('bad')", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "E_OWNED_REQUESTED_PYTHON"):
                self.launch_current(subprocess.Popen, cwd / "not-current.exe", script, deadline=time.monotonic()+3,
                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=cwd)
            self.assertFalse(marker.exists())

    def test_release_refuses_before_native_exit_proof(self):
        with tempfile.TemporaryDirectory(prefix="sr3-owned-release-") as name:
            cwd = Path(name); script = cwd / "wait.py"; script.write_text("import time; time.sleep(60)", encoding="utf-8")
            owner = self.launch_current(subprocess.Popen, sys.executable, script, deadline=time.monotonic()+10,
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=cwd)
            try:
                with self.assertRaisesRegex(ValueError, "E_OWNED_RELEASE_UNPROVEN"): owner.release()
                owner.stop(time.monotonic()+5); owner.release()
            finally:
                if owner.proof.get("released") is not True:
                    try: owner.stop(time.monotonic()+5); owner.release()
                    except Exception: pass

    def test_assignment_failure_reaps_unassigned_suspended_root_and_closes_stdin(self):
        from knowledge_bridge import windows_owned_process as owned
        created = []
        def spawn(*args, **kwargs):
            child = subprocess.Popen(*args, **kwargs); created.append(child); return child
        with tempfile.TemporaryDirectory(prefix='sr3-assign-refused-') as name:
            root = Path(name); marker = root/'must-not-run'; script = root/'root.py'
            script.write_text('from pathlib import Path; Path('+repr(str(marker))+').write_text("bad")', encoding='utf-8')
            original_job = owned._Job
            class RejectedJob(original_job):
                def __init__(self):
                    super().__init__()
                    self.api.AssignProcessToJobObject = lambda *_: False
            try:
                with patch.object(owned, '_Job', RejectedJob):
                    with self.assertRaises(OSError) as caught:
                        self.launch_current(spawn, sys.executable, script, deadline=time.monotonic()+5,
                            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=root)
                self.assertEqual(len(created), 1)
                self.assertIsNotNone(created[0].poll(), 'failed assignment left a suspended root alive')
                self.assertTrue(created[0].stdin.closed)
                self.assertTrue(caught.exception.owned_cleanup_complete)
                self.assertFalse(marker.exists())
            finally:
                for child in created:
                    if child.poll() is None: child.kill(); child.wait(timeout=5)
                    if child.stdin is not None: child.stdin.close()

    def test_script_system_exit_is_not_relabelled_as_bootstrap_failure(self):
        for code in (0, 7):
            with self.subTest(code=code), tempfile.TemporaryDirectory(prefix='sr3-script-exit-') as name:
                root = Path(name); script = root/'root.py'
                script.write_text('raise SystemExit('+str(code)+')', encoding='utf-8')
                owner = self.launch_current(subprocess.Popen, sys.executable, script, deadline=time.monotonic()+5,
                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=root)
                try:
                    owner.wait(time.monotonic()+5)
                    self.assertEqual(owner.process.poll(), code)
                    self.assertFalse(owner._paths['failure'].exists(), 'worker exit is not a bootstrap failure')
                    owner.release()
                finally:
                    if not owner.proof['released']:
                        owner.stop(time.monotonic()+5); owner.release()
                    owner.process.stdin.close()

    def test_missing_accounting_member_still_terminates_all_known_processes(self):
        from knowledge_bridge import windows_owned_process as owned
        with tempfile.TemporaryDirectory(prefix='sr3-gap-stop-') as name:
            root = Path(name); script = root/'root.py'
            script.write_text('import time; time.sleep(60)', encoding='utf-8')
            owner = self.launch_current(subprocess.Popen, sys.executable, script, deadline=time.monotonic()+5,
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=root)
            native = self._handle(owner.process.pid)
            original = owner._job.accounting
            def missing():
                info = original(); info.total += 1; return info
            try:
                with patch.object(owner._job, 'accounting', side_effect=missing):
                    with self.assertRaisesRegex(ValueError, 'E_SHARD_TREE_UNOBSERVED_MEMBER'):
                        owner.stop(time.monotonic()+5)
                self.assertEqual(self.kernel.WaitForSingleObject(native, 1000), 0, 'proof gap must not skip termination')
                self.assertFalse(owner.proof['termination'].get('native_exit_proved', False))
                with self.assertRaisesRegex(ValueError, 'E_OWNED_RELEASE_UNPROVEN'): owner.release()
            finally:
                # Test-owned final disposal only; never label this a proved stop.
                owner._job.close(); owner.process.wait(timeout=5)
                for item in owner._records.values():
                    if item['handle']: self.kernel.CloseHandle(item['handle'])
                self.kernel.CloseHandle(native); owner.process.stdin.close()

    def test_cpython_consumed_launcher_environment_is_not_false_identity_drift(self):
        with tempfile.TemporaryDirectory(prefix='sr3-launcher-env-') as name:
            root = Path(name); script = root/'root.py'
            script.write_text('import sys; sys.stdin.buffer.read()', encoding='utf-8')
            env = os.environ.copy(); env['__PYVENV_LAUNCHER__'] = sys.executable
            owner = self.launch_current(subprocess.Popen, sys.executable, script, deadline=time.monotonic()+5,
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, cwd=root)
            try:
                self.assertIsNone(owner.proof['startup']['observed']['launcher'])
                self.assertEqual(owner.proof['startup']['observed']['sys_executable'], os.path.normcase(os.path.abspath(sys.executable)))
                owner.process.stdin.close(); owner.wait(time.monotonic()+5); owner.release()
            finally:
                if not owner.proof['released']:
                    owner.stop(time.monotonic()+5); owner.release()
                owner.process.stdin.close()

    def test_resume_identity_error_survives_all_handle_close_failures(self):
        from knowledge_bridge import windows_owned_process as owned
        from types import SimpleNamespace
        job = owned._Job.__new__(owned._Job); closed = []
        def first(_snapshot, pointer):
            pointer._obj.owner, pointer._obj.ident = 77, 88; return True
        def end(*_args): ctypes.set_last_error(18); return False
        def close(handle): closed.append(handle); raise OSError('CONTROL_CLOSE_'+str(handle))
        job.api = SimpleNamespace(CreateToolhelp32Snapshot=lambda *_:10, Thread32First=first,
            Thread32Next=end, OpenThread=lambda *_:20, GetProcessIdOfThread=lambda _:78, CloseHandle=close)
        with self.assertRaisesRegex(ValueError, 'E_OWNED_THREAD_OWNER') as caught:
            job.resume(SimpleNamespace(pid=77))
        self.assertEqual(closed, [20, 10])
        self.assertIn('CONTROL_CLOSE_20', str(caught.exception.__notes__))
        self.assertIn('CONTROL_CLOSE_10', str(caught.exception.__notes__))

    def test_nested_job_descendant_has_independent_native_exit_proof(self):
        with tempfile.TemporaryDirectory(prefix='sr3-nested-job-') as name:
            root = Path(name); script = root/'root.py'; ready = root/'nested.pid'
            script.write_text('import ctypes,subprocess,sys,time\nfrom ctypes import wintypes as w\nfrom pathlib import Path\n'
                'k=ctypes.WinDLL("kernel32",use_last_error=True)\n'
                'k.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR]; k.CreateJobObjectW.restype=w.HANDLE\n'
                'k.GetCurrentProcess.restype=w.HANDLE\n'
                'k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]; k.AssignProcessToJobObject.restype=w.BOOL\n'
                'job=k.CreateJobObjectW(None,None)\n'
                'if not job or not k.AssignProcessToJobObject(job,k.GetCurrentProcess()): raise ctypes.WinError(ctypes.get_last_error())\n'
                'child=subprocess.Popen([sys.executable,"-B","-c","import time; time.sleep(60)"])\n'
                'marker=Path('+repr(str(ready))+'); pending=marker.with_name(marker.name+".ready-tmp")\n'
                'pending.write_text(str(child.pid)); pending.rename(marker)\n'
                'time.sleep(60)\n', encoding='utf-8')
            owner = self.launch_current(subprocess.Popen, sys.executable, script, deadline=time.monotonic()+5,
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=root)
            native = None
            try:
                self._wait_file(ready, time.monotonic()+5)
                child_pid = int(ready.read_text())
                native = self._handle(child_pid)
                owner.stop(time.monotonic()+5)
                self.assertEqual(self.kernel.WaitForSingleObject(native, 0), 0)
                # Windows may also associate a console host. Require all ledger
                # members, not an invented fixed two-process denominator.
                self.assertTrue({owner.process.pid, child_pid} <= set(owner._by_pid))
                self.assertEqual(owner.proof['termination']['records'], owner.proof['termination']['accounting_total'])
                owner.release()
                (root/'Native-exit-proof.json').write_text(json.dumps(owner.proof, sort_keys=True), encoding='utf-8')
            finally:
                if not owner.proof['released']:
                    owner.stop(time.monotonic()+5); owner.release()
                if native: self.kernel.CloseHandle(native)
                owner.process.stdin.close()

    def test_member_outside_job_is_not_accepted_from_a_completion_pid(self):
        from knowledge_bridge import windows_owned_process as owned
        from types import SimpleNamespace
        owner = owned.CurrentImageOwner.__new__(owned.CurrentImageOwner)
        closed = []
        def outside(_process, _job, result): result._obj.value = False; return True
        owner._job = SimpleNamespace(handle=99, check=owned._Job.check,
            api=SimpleNamespace(OpenProcess=lambda *_:123, IsProcessInJob=outside),
            close_handles=lambda handles, original=None: closed.extend(handles))
        owner._records, owner._by_pid, owner._gap = {}, {}, None
        owner.proof = {'membership': {'records': []}}
        owner._created, owner._image = lambda _:1, lambda _:'control.exe'
        with self.assertRaisesRegex(ValueError, 'E_OWNED_MEMBER_OUTSIDE_JOB'):
            owner._record(77, 'completion-port')
        self.assertEqual(closed, [123])
        self.assertEqual(owner._records, {})

    def test_expired_start_never_opens_work_gate_after_identity_check(self):
        from knowledge_bridge import windows_owned_process as owned
        real_verify = owned.CurrentImageOwner.verify_bootstrap
        def delayed(owner, until):
            real_verify(owner, until)
            time.sleep(max(0, until-time.monotonic())+.01)
        with tempfile.TemporaryDirectory(prefix='sr3-expired-gate-') as name:
            root = Path(name); script = root/'root.py'; marker = root/'must-not-run'
            script.write_text('from pathlib import Path; Path('+repr(str(marker))+').write_text("bad")', encoding='utf-8')
            owner = None
            try:
                with patch.object(owned.CurrentImageOwner, 'verify_bootstrap', delayed):
                    try:
                        owner = self.launch_current(subprocess.Popen, sys.executable, script, deadline=time.monotonic()+1,
                            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=root)
                    except TimeoutError as error:
                        self.assertIn('DEADLINE', str(error))
                    else:
                        self.fail('authored work gate was opened after request deadline')
                self.assertFalse(marker.exists())
            finally:
                if owner is not None:
                    owner.stop(time.monotonic()+5); owner.release(); owner.process.stdin.close()

    def test_job_and_member_release_attempt_every_close_and_keep_all_errors(self):
        from knowledge_bridge import windows_owned_process as owned
        from types import SimpleNamespace
        closed = []
        def close(handle): closed.append(handle); raise OSError('CONTROL_CLOSE_'+str(handle))
        job = owned._Job.__new__(owned._Job)
        job.port, job.handle = 30, 40
        job.api = SimpleNamespace(CloseHandle=close)
        owner = owned.CurrentImageOwner.__new__(owned.CurrentImageOwner)
        owner._job = job; owner._records = {1:{'handle':10}, 2:{'handle':20}}
        owner.proof = {'termination':{'native_exit_proved':True}, 'released':False}
        with self.assertRaisesRegex(OSError, 'CONTROL_CLOSE_10') as caught:
            owner.release()
        self.assertEqual(closed, [10,20,30,40])
        for handle in (20,30,40): self.assertIn('CONTROL_CLOSE_'+str(handle), str(caught.exception.__notes__))
        self.assertFalse(owner.proof['released'])

    def test_event_drain_cannot_ignore_expired_observation_deadline(self):
        from knowledge_bridge import windows_owned_process as owned
        from types import SimpleNamespace
        calls = []
        def next_event(_port, message, key, pid, _wait):
            calls.append(1)
            message._obj.value, key._obj.value, pid._obj.value = 6, 1, 77
            # Bound this deterministic fault itself; current broken code must
            # fail the expected deadline assertion, never hang the test runner.
            if len(calls)>10: raise AssertionError('CONTROL_EVENT_DRAIN_OVERRAN_DEADLINE')
            return True
        owner = owned.CurrentImageOwner.__new__(owned.CurrentImageOwner)
        owner._job = SimpleNamespace(port=99, api=SimpleNamespace(GetQueuedCompletionStatus=next_event))
        owner._record = lambda *_:None
        owner.proof = {'membership':{'events':[]}}
        with self.assertRaisesRegex(TimeoutError, 'E_OWNED_OBSERVATION_DEADLINE'):
            owner._events(time.monotonic()-1)
        self.assertLessEqual(len(calls), 1)

    def test_job_setup_close_debt_is_not_labelled_complete_without_an_owner(self):
        from knowledge_bridge import windows_owned_process as owned
        api = Mock()
        api.CreateJobObjectW.return_value = 99
        api.SetInformationJobObject.side_effect = OSError('CONTROL_SETUP_FAILURE')
        api.CloseHandle.side_effect = OSError('CONTROL_SETUP_CLOSE_DEBT')
        with tempfile.TemporaryDirectory(prefix='sr3-job-debt-') as name:
            root = Path(name); script = root/'never.py'; script.write_text('pass', encoding='utf-8')
            spawn = Mock()
            with patch.object(owned.ctypes, 'WinDLL', return_value=api), patch.object(owned, '_current_image', return_value=sys.executable):
                with self.assertRaisesRegex(OSError, 'CONTROL_SETUP_FAILURE') as caught:
                    self.launch_current(spawn, sys.executable, script, deadline=time.monotonic()+5,
                        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=root)
            self.assertFalse(caught.exception.owned_cleanup_complete)
            self.assertIn('CONTROL_SETUP_CLOSE_DEBT', str(caught.exception.__notes__))
            spawn.assert_not_called()

    def test_popen_failure_keeps_the_pre_owner_job_when_its_close_fails(self):
        from knowledge_bridge import windows_owned_process as owned
        job = Mock(); job.close.side_effect = OSError('CONTROL_PRE_OWNER_CLOSE_DEBT')
        with tempfile.TemporaryDirectory(prefix='sr3-popen-debt-') as name:
            root = Path(name); script = root/'never.py'; script.write_text('pass', encoding='utf-8')
            original = OSError('CONTROL_POPEN_ORIGINAL')
            with patch.object(owned, '_Job', return_value=job):
                with self.assertRaises(OSError) as caught:
                    self.launch_current(Mock(side_effect=original), sys.executable, script, deadline=time.monotonic()+5,
                        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=root)
            self.assertIs(caught.exception, original)
            self.assertFalse(original.owned_cleanup_complete)
            self.assertIs(getattr(original, 'owned_job_debt', None), job)
            self.assertIn('CONTROL_PRE_OWNER_CLOSE_DEBT', str(original.__notes__))

    def test_authored_script_keeps_its_original_sibling_import_directory(self):
        with tempfile.TemporaryDirectory(prefix='sr3-script-import-') as name:
            root = Path(name); authored = root/'authored'; authored.mkdir()
            marker = root/'import-ok'; script = authored/'root.py'
            (authored/'sibling.py').write_text('VALUE="authored-sibling"', encoding='utf-8')
            script.write_text('from sibling import VALUE\nfrom pathlib import Path\nPath('+repr(str(marker))+').write_text(VALUE)\n', encoding='utf-8')
            owner = self.launch_current(subprocess.Popen, sys.executable, script, deadline=time.monotonic()+5,
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=root)
            try:
                owner.process.wait(timeout=5)
                owner.wait(time.monotonic()+5)
                self.assertEqual(owner.process.poll(), 0, 'bootstrap changed normal Python sibling import semantics')
                self.assertEqual(marker.read_text(), 'authored-sibling')
                owner.release()
            finally:
                if not owner.proof['released']:
                    owner.stop(time.monotonic()+5); owner.release()
                owner.process.stdin.close()

    def test_active_count_may_change_after_pid_snapshot_without_identity_gap(self):
        from knowledge_bridge import windows_owned_process as owned
        from types import SimpleNamespace
        record = {'pid':77, 'handle':123}
        owner = owned.CurrentImageOwner.__new__(owned.CurrentImageOwner)
        def inside(_process, _job, result): result._obj.value = True; return True
        owner._job = SimpleNamespace(handle=99, pids=lambda:([77],1), check=owned._Job.check,
            api=SimpleNamespace(IsProcessInJob=inside))
        owner._records, owner._by_pid, owner._gap = {1:record}, {77:record}, None
        owner._events = lambda _until:None
        owner._record = lambda *_:record
        owner.accounting = lambda:SimpleNamespace(total=1, active=0)
        # Exit happened between two separate Windows queries. Neither query
        # claims an atomic snapshot; the exit loop must observe again.
        pids, accounting = owner._observe(time.monotonic()+1)
        self.assertEqual(pids, [77]); self.assertEqual(accounting.active, 0)
        self.assertIsNone(owner._gap)
