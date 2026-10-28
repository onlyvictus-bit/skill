"""SR4 startup ownership controls: real Windows Job lifecycle where possible."""
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
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


@unittest.skipUnless(os.name == "nt", "Windows Job/process-handle proof required")
class OwnedStartupTests(unittest.TestCase):
    def setUp(self):
        from knowledge_bridge import windows_owned_process as owned
        self.owned = owned
        self.launch = owned.launch_current
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

    def _launch(self, script, cwd):
        return self.launch(subprocess.Popen, sys.executable, script,
                           deadline=time.monotonic() + 10,
                           stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, env=os.environ.copy(), cwd=cwd)

    def test_expected_identity_keeps_parent_base_distinct_from_loaded_image(self):
        parent_base = str(ROOT / "parent-base.exe")
        loaded_image = str(ROOT / "loaded-image.exe")
        with patch.object(sys, "_base_executable", parent_base, create=True), \
                patch.object(self.owned, "_current_image", return_value=os.path.normcase(os.path.abspath(loaded_image))):
            expected = self.owned._startup_expected("control-token")
        self.assertEqual(expected["base_executable"], os.path.normcase(os.path.abspath(parent_base)))
        self.assertEqual(expected["image"], os.path.normcase(os.path.abspath(loaded_image)))
        self.assertNotEqual(expected["base_executable"], expected["image"])

    def test_actual_startup_retains_identity_frame_then_native_exit_proof(self):
        with tempfile.TemporaryDirectory(prefix="sr4-actual-startup-") as name:
            root = Path(name)
            script = root / "worker.py"
            script.write_text("import sys\nsys.stdin.buffer.read()\n", encoding="utf-8")
            owner = self._launch(script, root)
            try:
                self.assertEqual(owner.proof["startup"]["state"], "resumed")
                self.assertEqual(owner.proof["membership"]["records"][0]["pid"], owner.process.pid)
                self.assertEqual(owner.proof["membership"]["records"][0]["source"], "assigned-root")
                self.assertEqual(owner.proof["membership"]["records"][0]["handle_origin"], "popen-duplicate")
                self.assertNotEqual(owner._by_pid[owner.process.pid]["handle"], owner.process._handle)
                self.assertEqual(owner.proof["startup"]["expected"]["base_executable"],
                                 os.path.normcase(os.path.abspath(getattr(sys, "_base_executable", sys.executable))))
                self.assertEqual(owner.proof["startup"]["observed"]["base_executable"],
                                 owner.proof["startup"]["expected"]["base_executable"])
                owner.process.stdin.close()
                owner.wait(time.monotonic() + 5)
                owner.release()
                artifact = root / "SR4-Actual-Startup.json"
                artifact.write_text(json.dumps({
                    "expected": owner.proof["startup"]["expected"],
                    "observed": owner.proof["startup"]["observed"],
                    "termination": owner.proof["termination"],
                    "released": owner.proof["released"],
                }, sort_keys=True), encoding="utf-8")
                self.assertTrue(owner.proof["termination"]["native_exit_proved"])
                self.assertTrue(owner.proof["released"])
                # Releasing the owner's duplicate must not close Popen's source
                # handle; Popen remains responsible for that handle's lifetime.
                self.assertEqual(self.kernel.WaitForSingleObject(owner.process._handle, 0), 0)
            finally:
                if not owner.proof.get("released"):
                    try:
                        owner.stop(time.monotonic() + 5)
                        owner.release()
                    except Exception:
                        pass
                if owner.process.stdin is not None and not owner.process.stdin.closed:
                    owner.process.stdin.close()

    def test_bootstrap_role_mismatch_records_bounded_expected_observed_frame_and_reaps_root(self):
        with tempfile.TemporaryDirectory(prefix="sr4-role-mismatch-") as name:
            root = Path(name)
            script = root / "must-not-run.py"
            marker = root / "must-not-run"
            script.write_text("from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('bad')\n", encoding="utf-8")
            impossible_base = str(root / "attested-parent-base.exe")
            with patch.object(sys, "_base_executable", impossible_base, create=True):
                with self.assertRaisesRegex(ValueError, "E_OWNED_BOOTSTRAP_FAILURE") as caught:
                    self._launch(script, root)
            error = caught.exception
            owner = error.owned_process_owner
            self.assertFalse(marker.exists())
            self.assertIsNotNone(owner)
            self.assertTrue(error.owned_cleanup_complete, '\n'.join(getattr(error, '__notes__', [])))
            self.assertTrue(owner.proof["termination"]["native_exit_proved"])
            frame = owner.proof["startup"]["failure"]
            self.assertEqual(frame["expected"]["base_executable"], os.path.normcase(os.path.abspath(impossible_base)))
            self.assertEqual(frame["observed"]["base_executable"],
                             os.path.normcase(os.path.abspath(getattr(sys, "_base_executable", sys.executable))))
            self.assertRegex("\n".join(error.__notes__), "TerminateJobObject|Popen.wait")
            owner.release()
            if owner.process.stdin is not None and not owner.process.stdin.closed:
                owner.process.stdin.close()

    def test_assigned_not_resumed_failure_reaps_recorded_root_without_authored_work(self):
        with tempfile.TemporaryDirectory(prefix="sr4-assigned-not-resumed-") as name:
            root = Path(name)
            marker = root / "must-not-run"
            script = root / "worker.py"
            script.write_text("from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('bad')\n", encoding="utf-8")
            def interrupted_resume(job, process):
                raise OSError("CONTROL_RESUME_INTERRUPTED")
            with patch.object(self.owned._Job, "resume", interrupted_resume):
                with self.assertRaisesRegex(OSError, "CONTROL_RESUME_INTERRUPTED") as caught:
                    self._launch(script, root)
            error = caught.exception
            owner = error.owned_process_owner
            native = self._handle(owner.process.pid)
            try:
                self.assertFalse(marker.exists())
                self.assertTrue(error.owned_cleanup_complete)
                self.assertEqual(owner.proof["startup"]["state"], "assigned-not-resumed")
                self.assertEqual(owner.proof["membership"]["records"][0]["source"], "assigned-root")
                self.assertEqual(self.kernel.WaitForSingleObject(native, 0), 0)
                self.assertTrue(owner.proof["termination"]["native_exit_proved"])
                self.assertIn("TerminateJobObject", "\n".join(error.__notes__))
                owner.release()
            finally:
                self.kernel.CloseHandle(native)
                if owner.process.stdin is not None and not owner.process.stdin.closed:
                    owner.process.stdin.close()

    def test_unknown_nonroot_exit_remains_a_proof_gap(self):
        from types import SimpleNamespace
        owner = self.owned.CurrentImageOwner.__new__(self.owned.CurrentImageOwner)
        def unknown_exit(_port, message, key, pid, _wait):
            message._obj.value, key._obj.value, pid._obj.value = 7, 1, 987654
            return True
        owner._job = SimpleNamespace(port=1, api=SimpleNamespace(GetQueuedCompletionStatus=unknown_exit))
        owner._by_pid, owner._records, owner._gap = {}, {}, None
        owner.proof = {"membership": {"events": []}}
        with self.assertRaisesRegex(ValueError, "E_OWNED_EXIT_UNKNOWN"):
            owner._events(time.monotonic() + 1)

    def test_root_exit_without_a_new_event_is_attributable_to_the_pre_resume_ledger(self):
        """The direct root record makes an early EXIT attributable, not unknown."""
        from types import SimpleNamespace
        root = {"pid": 424242, "created": 7, "handle": 11, "image": "root.exe"}
        calls = []
        def event(_port, message, key, pid, _wait):
            calls.append(1)
            if len(calls) == 1:
                message._obj.value, key._obj.value, pid._obj.value = 7, 1, root["pid"]
                return True
            ctypes.set_last_error(258)
            return False
        owner = self.owned.CurrentImageOwner.__new__(self.owned.CurrentImageOwner)
        owner._job = SimpleNamespace(port=1, api=SimpleNamespace(GetQueuedCompletionStatus=event))
        owner._by_pid, owner._records, owner._gap = {root["pid"]: root}, {(root["pid"], 7): root}, None
        owner.proof = {"membership": {"events": []}}
        owner._events(time.monotonic() + 1)
        self.assertEqual(owner.proof["membership"]["events"], [{"message": 7, "pid": root["pid"]}])

    def test_wrong_token_failure_cannot_publish_an_identity_frame(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory(prefix="sr4-wrong-token-") as name:
            failure = Path(name) / "failure.json"
            failure.write_text(json.dumps({"token": "wrong", "code": "E_CONTROL", "detail": "x",
                "identity": {"expected": {}, "observed": {}}}), encoding="utf-8")
            owner = self.owned.CurrentImageOwner.__new__(self.owned.CurrentImageOwner)
            owner._paths = {"ready": Path(name) / "ready.json", "failure": failure}
            owner._expected = {"token": "right"}
            owner.proof = {"startup": {}}
            owner.process = SimpleNamespace(poll=lambda: None)
            with self.assertRaisesRegex(ValueError, "E_OWNED_BOOTSTRAP_FAILURE_TOKEN"):
                owner.verify_bootstrap(time.monotonic() + 1)
            self.assertNotIn("failure", owner.proof["startup"])

    def test_same_token_tampered_expected_frame_is_rejected(self):
        fields = ("image", "sys_executable", "prefix", "base_prefix", "base_executable", "launcher")
        expected = {"token": "right", **{name: (None if name == "launcher" else name + ".exe") for name in fields}}
        observed = {name: (None if name == "launcher" else "actual-" + name + ".exe") for name in fields}
        tampered = dict(expected); tampered["base_executable"] = "attacker.exe"; tampered.pop("token")
        with tempfile.TemporaryDirectory(prefix="sr4-frame-tamper-") as name:
            failure = Path(name) / "failure.json"
            failure.write_text(json.dumps({"token": "right", "code": "E_CONTROL", "detail": "x",
                "identity": {"expected": tampered, "observed": observed}}), encoding="utf-8")
            owner = self.owned.CurrentImageOwner.__new__(self.owned.CurrentImageOwner)
            owner._paths = {"ready": Path(name) / "ready.json", "failure": failure}
            owner._expected = expected; owner.proof = {"startup": {}}
            owner.process = SimpleNamespace(poll=lambda: None)
            with self.assertRaisesRegex(ValueError, "E_OWNED_BOOTSTRAP_EXPECTED"):
                owner.verify_bootstrap(time.monotonic() + 1)
            self.assertNotIn("failure", owner.proof["startup"])

    def test_oversized_failure_detail_is_rejected_before_publication(self):
        with tempfile.TemporaryDirectory(prefix="sr4-frame-size-") as name:
            failure = Path(name) / "failure.json"
            failure.write_text(json.dumps({"token": "right", "code": "E_CONTROL", "detail": "x" * 513}), encoding="utf-8")
            owner = self.owned.CurrentImageOwner.__new__(self.owned.CurrentImageOwner)
            owner._paths = {"ready": Path(name) / "ready.json", "failure": failure}
            owner._expected = {"token": "right"}; owner.proof = {"startup": {}}
            owner.process = SimpleNamespace(poll=lambda: None)
            with self.assertRaisesRegex(ValueError, "E_OWNED_BOOTSTRAP_FAILURE_VALUE"):
                owner.verify_bootstrap(time.monotonic() + 1)
            self.assertNotIn("failure", owner.proof["startup"])

    def test_successful_resume_then_close_failure_still_records_resumed_cleanup_state(self):
        with tempfile.TemporaryDirectory(prefix="sr4-resume-close-") as name:
            root = Path(name); marker = root / "must-not-run"; script = root / "worker.py"
            script.write_text("from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('bad')\n", encoding="utf-8")
            real_close = self.owned._Job.close_handles
            def after_resume_close(job, handles, original=None):
                real_close(job, handles, original)
                raise OSError("CONTROL_POST_RESUME_CLOSE")
            with patch.object(self.owned._Job, "close_handles", after_resume_close):
                with self.assertRaisesRegex(OSError, "CONTROL_POST_RESUME_CLOSE") as caught:
                    self._launch(script, root)
            error, owner = caught.exception, caught.exception.owned_process_owner
            try:
                self.assertEqual(owner.proof["startup"]["state"], "resumed")
                self.assertTrue(error.owned_cleanup_complete)
                self.assertFalse(marker.exists())
                self.assertTrue(owner.proof["termination"]["native_exit_proved"])
                owner.release()
            finally:
                if owner.process.stdin is not None and not owner.process.stdin.closed:
                    owner.process.stdin.close()

    def test_failed_terminate_names_native_operation_and_preserves_resume_error(self):
        with tempfile.TemporaryDirectory(prefix="sr4-terminate-failure-") as name:
            root = Path(name); script = root / "worker.py"
            script.write_text("raise AssertionError('must not run')\n", encoding="utf-8")
            real_job = self.owned._Job
            class TerminateFailsJob(real_job):
                def __init__(self):
                    super().__init__()
                    self.api.TerminateJobObject = lambda *_: False
            def resume_failure(_job, _process):
                raise OSError("CONTROL_RESUME_PRIMARY")
            with patch.object(self.owned, "_Job", TerminateFailsJob), \
                    patch.object(TerminateFailsJob, "resume", resume_failure):
                with self.assertRaisesRegex(OSError, "CONTROL_RESUME_PRIMARY") as caught:
                    self._launch(script, root)
            error, owner = caught.exception, caught.exception.owned_process_owner
            try:
                self.assertFalse(error.owned_cleanup_complete)
                self.assertFalse(owner.proof["termination"].get("native_exit_proved", False))
                self.assertIn("E_OWNED_NATIVE_OPERATION: TerminateJobObject", "\n".join(error.__notes__))
            finally:
                owner._job.close()
                owner.process.wait(timeout=5)
                if owner.process.stdin is not None and not owner.process.stdin.closed:
                    owner.process.stdin.close()

    def test_preinsert_query_and_close_failure_retain_recoverable_handle_debt(self):
        job = self.owned._Job.__new__(self.owned._Job)
        job.handle, job.port, job._handle_debt = 1, None, []
        closed = []
        def inside(_process, _job, value):
            value._obj.value = 1
            return True
        def failing_close(handle):
            closed.append(handle)
            ctypes.set_last_error(5)
            return False
        job.api = SimpleNamespace(OpenProcess=lambda *_: 321,
                                  IsProcessInJob=inside, CloseHandle=failing_close)
        owner = self.owned.CurrentImageOwner(job, SimpleNamespace(pid=9), {}, {})
        with patch.object(owner, '_created', side_effect=OSError('CONTROL_QUERY_PRIMARY')):
            with self.assertRaisesRegex(OSError, 'CONTROL_QUERY_PRIMARY') as caught:
                owner._record(9, 'control')
        self.assertEqual(job._handle_debt, [321])
        self.assertIn('CloseHandle', '\n'.join(caught.exception.__notes__))
        job.api.CloseHandle = lambda handle: closed.append(handle) or True
        job.close()
        self.assertEqual(job._handle_debt, [])
        self.assertEqual(closed.count(321), 2, 'one failed close and one debt retirement')

    def test_real_post_resume_close_failure_keeps_debt_and_never_claims_complete(self):
        with tempfile.TemporaryDirectory(prefix='sr4-real-close-debt-') as name:
            root = Path(name); script = root/'worker.py'
            script.write_text("raise AssertionError('authored work must stay gated')\n", encoding='utf-8')
            real_job = self.owned._Job
            created = []
            class CloseFails(real_job):
                def __init__(self):
                    super().__init__(); self.real_close = self.api.CloseHandle; created.append(self)
                def close_handles(self, handles, original=None):
                    def reject(_handle):
                        ctypes.set_last_error(5)
                        return False
                    self.api.CloseHandle = reject
                    return super().close_handles(handles, original)
            with patch.object(self.owned, '_Job', CloseFails):
                with self.assertRaises(OSError) as caught:
                    self._launch(script, root)
            error, owner = caught.exception, caught.exception.owned_process_owner
            try:
                self.assertEqual(owner.proof['startup']['state'], 'resumed')
                self.assertFalse(error.owned_cleanup_complete)
                self.assertIs(error.owned_job_debt, created[0])
                self.assertTrue(created[0]._handle_debt)
                self.assertIsNotNone(owner.process.poll())
                self.assertIn('CloseHandle', '\n'.join(error.__notes__))
            finally:
                created[0].api.CloseHandle = created[0].real_close
                owner.release()
                if owner.process.stdin is not None and not owner.process.stdin.closed:
                    owner.process.stdin.close()

    def test_wait_failure_is_not_falsely_attributed_to_successful_termination(self):
        job = SimpleNamespace(handle=1,
            api=SimpleNamespace(TerminateJobObject=lambda *_: True,
                                WaitForSingleObject=lambda *_: 0xFFFFFFFF),
            check=lambda value: value)
        process = SimpleNamespace(pid=9, returncode=1, wait=lambda **_: 1)
        owner = self.owned.CurrentImageOwner(job, process, {}, {})
        record = {'pid': 9, 'handle': 99}
        owner._records, owner._by_pid = {(9, 1): record}, {9: record}
        accounting = SimpleNamespace(total=1, active=0)
        with patch.object(owner, '_observe', return_value=([], accounting)):
            with self.assertRaises(Exception):
                owner.stop(time.monotonic()+1)
        operations = [row['operation'] for row in owner.proof['termination']['failures']]
        self.assertIn('WaitForSingleObject', operations)
        self.assertNotIn('TerminateJobObject', operations)
        self.assertNotIn('Popen.wait', operations)
        self.assertFalse(owner.proof['termination']['native_exit_proved'])

    def test_assigned_not_resumed_cleanup_records_specific_native_exit_mode(self):
        with tempfile.TemporaryDirectory(prefix='sr4-state-specific-') as name:
            root = Path(name); script = root/'worker.py'
            script.write_text("raise AssertionError('must not run')\n", encoding='utf-8')
            with patch.object(self.owned._Job, 'resume', side_effect=OSError('CONTROL_BEFORE_RESUME')):
                with self.assertRaisesRegex(OSError, 'CONTROL_BEFORE_RESUME') as caught:
                    self._launch(script, root)
            owner = caught.exception.owned_process_owner
            self.assertEqual(owner.proof['termination']['mode'], 'assigned-not-resumed')
            self.assertTrue(owner.proof['termination']['native_exit_proved'])
            self.assertTrue(caught.exception.owned_cleanup_complete)

    def test_bootstrap_emitter_caps_detail_and_preserves_identity_in_a_bounded_frame(self):
        from knowledge_bridge import windows_owned_bootstrap as bootstrap
        with tempfile.TemporaryDirectory(prefix='sr4-emitter-limit-') as name:
            target = Path(name)/'failure.json'
            expected = {field: (None if field == 'launcher' else 'value') for field in self.owned._IDENTITY_FIELDS}
            bootstrap._fail(target, 'a'*64, 'CONTROL', 'x'*10000, expected, expected)
            row = json.loads(target.read_text(encoding='utf-8'))
            self.assertLessEqual(len(row['detail']), self.owned._BOOTSTRAP_DETAIL_CHARS)
            self.assertLessEqual(target.stat().st_size, self.owned._BOOTSTRAP_FAILURE_BYTES)
            self.assertEqual(row['identity']['expected'], expected)

    def test_bootstrap_emitter_never_writes_an_oversized_identity_failure(self):
        from knowledge_bridge import windows_owned_bootstrap as bootstrap
        with tempfile.TemporaryDirectory(prefix='sr4-emitter-total-') as name:
            target = Path(name)/'failure.json'
            fields = {field: (None if field == 'launcher' else 'x'*2048) for field in self.owned._IDENTITY_FIELDS}
            bootstrap._fail(target, 'a'*64, 'CONTROL', 'detail', fields, fields)
            self.assertLessEqual(target.stat().st_size, self.owned._BOOTSTRAP_FAILURE_BYTES)
            row = json.loads(target.read_text(encoding='utf-8'))
            self.assertEqual(row['token'], 'a'*64)
            self.assertIn('OVERSIZE', row['detail'])
            self.assertNotIn('identity', row, 'an omitted oversized frame must not become a trusted partial identity')

    def test_ready_file_is_bounded_before_json_parsing(self):
        with tempfile.TemporaryDirectory(prefix='sr4-ready-limit-') as name:
            ready = Path(name)/'ready.json'
            ready.write_text(' '*(self.owned._BOOTSTRAP_FAILURE_BYTES+1), encoding='utf-8')
            owner = self.owned.CurrentImageOwner.__new__(self.owned.CurrentImageOwner)
            owner._paths = {'ready': ready, 'failure': Path(name)/'absent'}
            with self.assertRaisesRegex(ValueError, 'E_OWNED_BOOTSTRAP_READY_SIZE'):
                owner.verify_bootstrap(time.monotonic()+1)

    def test_signalled_root_uses_fresh_empty_check_not_termination_of_a_stale_pid_snapshot(self):
        terminated = []
        job = SimpleNamespace(handle=1,
            api=SimpleNamespace(TerminateJobObject=lambda *_: terminated.append(1) or False,
                                WaitForSingleObject=lambda *_: 0), check=self.owned._Job.check)
        process = SimpleNamespace(pid=9, returncode=71, wait=lambda **_: 71)
        owner = self.owned.CurrentImageOwner(job, process, {}, {})
        owner.proof['startup']['state'] = 'resumed'
        record = {'pid': 9, 'handle': 99}
        owner._records, owner._by_pid = {(9, 1): record}, {9: record}
        accounting = SimpleNamespace(total=1, active=0)
        with patch.object(owner, '_observe', side_effect=[([9], accounting), ([], accounting)]):
            owner.stop(time.monotonic()+1)
        self.assertEqual(terminated, [], 'the pinned root already exited; verify Job emptiness before release')
        self.assertTrue(owner.proof['termination']['native_exit_proved'])
        self.assertEqual(owner.proof['termination']['mode'], 'already-exited')

    def test_failed_accounting_query_names_its_native_operation(self):
        job = self.owned._Job.__new__(self.owned._Job)
        def denied(*_):
            ctypes.set_last_error(5)
            return False
        job.handle = 1
        job.api = SimpleNamespace(QueryInformationJobObject=denied)
        with self.assertRaises(OSError) as caught:
            job.accounting()
        self.assertIn('QueryInformationJobObject(accounting)', '\n'.join(getattr(caught.exception, '__notes__', [])))

    def test_failed_completion_query_names_its_native_operation(self):
        def denied(*_):
            ctypes.set_last_error(31)
            return False
        owner = self.owned.CurrentImageOwner.__new__(self.owned.CurrentImageOwner)
        owner._job = SimpleNamespace(port=1, api=SimpleNamespace(GetQueuedCompletionStatus=denied))
        with self.assertRaises(OSError) as caught:
            owner._events(time.monotonic()+1)
        self.assertIn('GetQueuedCompletionStatus', '\n'.join(getattr(caught.exception, '__notes__', [])))


if __name__ == "__main__":
    unittest.main()
