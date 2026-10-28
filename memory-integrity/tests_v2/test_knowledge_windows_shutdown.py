"""Real launcher/interpreter lifetime controls; no numerical/runtime claim."""
import contextlib
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from knowledge_bridge import distributed_retrieval as d


@unittest.skipUnless(os.name == 'nt', 'Windows native process-handle observation required')
class WindowsShutdown(unittest.TestCase):
    @contextlib.contextmanager
    def relay(self, *, blocked=False):
        """A real Python relay waits for its real stdin-reading interpreter."""
        with tempfile.TemporaryDirectory(prefix='owned-shutdown-proof-') as name:
            root = Path(name)
            (root/'actual.py').write_text(
                'import os,sys\nfrom pathlib import Path\n'
                'root=Path(sys.argv[1])\n'
                '(root/"actual.pid").write_text(str(os.getpid()),encoding="utf-8")\n' +
                ('import threading\nthreading.Event().wait(60)\n' if blocked else 'sys.stdin.buffer.read()\n') +
                '(root/"eof-observed").write_text("input closed",encoding="utf-8")\n', encoding='utf-8')
            (root/'distributed_worker.py').write_text(
                'import subprocess,sys\nfrom pathlib import Path\n'
                'root=Path('+repr(str(root))+')\n'
                'child=subprocess.Popen([sys.executable,"-B",str(root/"actual.py"),str(root)])\n'
                'raise SystemExit(child.wait())\n', encoding='utf-8')
            session = None; handle = None
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.WaitForSingleObject.restype = wintypes.DWORD
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel.CloseHandle.restype = wintypes.BOOL
            try:
                with patch.object(d, '__file__', str(root/'distributed_retrieval.py')):
                    session = d._Session(sys.executable, 0, 'a'*64, time.monotonic()+120)
                until = time.monotonic()+10
                while not (root/'actual.pid').exists():
                    if session.process.poll() is not None or time.monotonic() >= until:
                        self.fail('controlled relay did not reach its ready marker')
                    threading.Event().wait(.005)  # Test readiness observation, not a repair sleep.
                actual = int((root/'actual.pid').read_text(encoding='utf-8'))
                self.assertNotEqual(actual, session.process.pid)
                handle = kernel.OpenProcess(0x100000, False, actual)  # SYNCHRONIZE only.
                if not handle: raise ctypes.WinError(ctypes.get_last_error())
                yield session, root, lambda: kernel.WaitForSingleObject(handle, 0) == 0
            finally:
                if session is not None:
                    # Release only this fixture's pipe; no global process kill.
                    if session.process.stdin is not None and not session.process.stdin.closed:
                        session.process.stdin.close()
                    if handle:
                        self.assertEqual(kernel.WaitForSingleObject(handle, 5000), 0,
                                         'controlled actual interpreter did not stop')
                    if session.process.poll() is None:
                        session.process.wait(timeout=5)
                    for stream in (session.reader, session.output, session.errors, session.process.stdin):
                        if stream is not None: stream.close()
                if handle: kernel.CloseHandle(handle)

    def test_idle_stop_waits_for_actual_interpreter_before_cleanup(self):
        with self.relay() as (session, root, stopped):
            session.stop()
            self.assertTrue(stopped(), 'launcher exited but actual interpreter still owns output')
            self.assertTrue((root/'eof-observed').exists(), 'idle shutdown must deliver orderly EOF')
            session.close()
            session.close()

    def test_expired_stop_waits_for_the_owned_interpreter_not_only_launcher(self):
        with self.relay() as (session, _root, stopped):
            session.deadline = time.monotonic()-1
            session.stop()
            self.assertTrue(stopped(), 'expired cleanup reaped launcher but left owned interpreter alive')
            session.close()

    def test_broken_stdin_does_not_abandon_owned_interpreter(self):
        with self.relay() as (session, _root, stopped):
            original = session.process.stdin
            class BrokenClose:
                closed = False
                def close(self): raise OSError('CONTROL_STDIN_CLOSE_FAILURE')
            session.process.stdin = BrokenClose()
            try:
                with self.assertRaisesRegex(OSError, 'CONTROL_STDIN_CLOSE_FAILURE'):
                    session.stop()
                self.assertTrue(stopped(), 'failed EOF must still reap the owned tree')
                self.assertFalse(session._stopped, 'failed shutdown cannot become success')
                with self.assertRaisesRegex(ValueError, 'E_DISTRIBUTED_STOP_INCOMPLETE'):
                    session.close()
            finally:
                session.process.stdin = original

    def test_blocked_real_pipe_writer_is_released_before_cleanup(self):
        with self.relay(blocked=True) as (session, _root, stopped):
            session.deadline = time.monotonic() + .1
            with self.assertRaisesRegex(ValueError, 'E_DISTRIBUTED_WORKER_TIMEOUT'):
                session.request('fit', {'text': 'x' * 1000000})
            session.stop()
            self.assertTrue(stopped())
            self.assertFalse(session.writer.is_alive())
            session.close()

    def test_assignment_failure_never_runs_suspended_child(self):
        from knowledge_bridge import windows_job as job
        with tempfile.TemporaryDirectory(prefix='suspended-assignment-') as name:
            marker = Path(name)/'must-not-run'
            real_job = job.OwnedJob
            class RejectedJob(real_job):
                def __init__(self):
                    super().__init__()
                    self.api.AssignProcessToJobObject = lambda *args: False
            created = []
            def spawn(*args, **kwargs):
                process = subprocess.Popen(*args, **kwargs)
                created.append(process)
                return process
            with patch.object(job, 'OwnedJob', RejectedJob):
                with self.assertRaises(OSError):
                    job.start(spawn, [sys.executable, '-B', '-c',
                                      'from pathlib import Path;Path('+repr(str(marker))+').write_text("bad")'],
                              stdin=subprocess.PIPE)
            self.assertEqual(len(created), 1)
            self.assertIsNotNone(created[0].poll())
            self.assertTrue(created[0].stdin.closed)
            self.assertFalse(marker.exists())

    def test_resume_failure_reaps_already_assigned_root(self):
        from knowledge_bridge import windows_job as job
        created = []
        def spawn(*args, **kwargs):
            process = subprocess.Popen(*args, **kwargs)
            created.append(process)
            return process
        with patch.object(job.OwnedJob, 'resume', side_effect=OSError('CONTROL_RESUME_FAILURE')):
            with self.assertRaisesRegex(OSError, 'CONTROL_RESUME_FAILURE'):
                job.start(spawn, [sys.executable, '-B', '-c', 'raise SystemExit(0)'], stdin=subprocess.PIPE)
        self.assertEqual(len(created), 1)
        self.assertIsNotNone(created[0].poll())
        self.assertTrue(created[0].stdin.closed)

    def test_unobserved_member_refuses_success_and_retains_output(self):
        with self.relay() as (session, _root, _stopped):
            original = session._tree.accounting
            def missing_member():
                info = original()
                info.total += 1  # A process was born outside the pinned member set.
                return info
            session.deadline = time.monotonic()-1
            with patch.object(session._tree, 'accounting', side_effect=missing_member):
                with self.assertRaisesRegex(ValueError, 'E_SHARD_TREE_UNOBSERVED_MEMBER'):
                    session.stop()
            self.assertFalse(session._stopped)
            self.assertFalse(session._closed)
            self.assertFalse(session.output.closed, 'unproven shutdown must not dispose output')
            with self.assertRaisesRegex(ValueError, 'E_DISTRIBUTED_STOP_INCOMPLETE'):
                session.close()

    def test_resume_close_failures_preserve_thread_owner_error(self):
        from knowledge_bridge import windows_job as job
        tree = job.OwnedJob.__new__(job.OwnedJob)
        closed = []
        def first(_snapshot, pointer):
            pointer._obj.owner, pointer._obj.ident = 77, 88
            return True
        def end(*_args):
            ctypes.set_last_error(18)
            return False
        def close(handle):
            closed.append(handle)
            raise OSError('CONTROL_CLOSE_' + str(handle))
        tree.api = SimpleNamespace(CreateToolhelp32Snapshot=lambda *_: 10,
            Thread32First=first, Thread32Next=end, OpenThread=lambda *_: 20,
            GetProcessIdOfThread=lambda _: 78, CloseHandle=close)
        caught = None
        try:
            tree.resume(SimpleNamespace(pid=77))
        except Exception as error:
            caught = error
        self.assertIsInstance(caught, ValueError, 'close failure masked original identity refusal')
        self.assertEqual(str(caught), 'E_SHARD_THREAD_OWNER')
        self.assertEqual(closed, [20, 10])
        self.assertIn('CONTROL_CLOSE_20', str(caught.__notes__))
        self.assertIn('CONTROL_CLOSE_10', str(caught.__notes__))

    def test_termination_close_failures_preserve_membership_error_and_close_all(self):
        from knowledge_bridge import windows_job as job
        tree = job.OwnedJob.__new__(job.OwnedJob)
        tree.handle, tree.root = 99, SimpleNamespace(pid=11, _handle=111)
        closed = []
        def members(_handle, _kind, pointer, *_args):
            pointer._obj.assigned = pointer._obj.listed = 2
            pointer._obj.pids[0], pointer._obj.pids[1] = 22, 33
            return True
        def inside(_handle, _job, pointer):
            pointer._obj.value = True
            return True
        def close(handle):
            closed.append(handle)
            raise OSError('CONTROL_MEMBER_CLOSE_' + str(handle))
        tree.api = SimpleNamespace(QueryInformationJobObject=members,
            OpenProcess=lambda _access, _inherit, pid: pid*10,
            IsProcessInJob=inside, TerminateJobObject=lambda *_: True, CloseHandle=close)
        tree.accounting = lambda: SimpleNamespace(total=4)
        caught = None
        try:
            tree.terminate(time.monotonic()+5)
        except Exception as error:
            caught = error
        self.assertIsInstance(caught, ValueError, 'close failure masked original membership refusal')
        self.assertEqual(str(caught), 'E_SHARD_TREE_UNOBSERVED_MEMBER')
        self.assertEqual(closed, [220, 330], 'one failed close must not skip remaining handles')
        self.assertIn('CONTROL_MEMBER_CLOSE_220', str(caught.__notes__))
        self.assertIn('CONTROL_MEMBER_CLOSE_330', str(caught.__notes__))

    def test_setup_close_failure_preserves_original_setup_error(self):
        from knowledge_bridge import windows_job as job
        api = Mock()
        api.CreateJobObjectW.return_value = 99
        api.SetInformationJobObject.side_effect = ValueError('CONTROL_JOB_SETUP')
        api.CloseHandle.side_effect = OSError('CONTROL_JOB_RELEASE')
        caught = None
        with patch.object(job.ctypes, 'WinDLL', return_value=api):
            try:
                job.OwnedJob()
            except Exception as error:
                caught = error
        self.assertIsInstance(caught, ValueError, 'job release masked original setup error')
        self.assertEqual(str(caught), 'CONTROL_JOB_SETUP')
        self.assertIn('CONTROL_JOB_RELEASE', str(caught.__notes__))

    def test_release_failure_without_primary_error_remains_a_failure(self):
        from knowledge_bridge import windows_job as job
        tree = job.OwnedJob.__new__(job.OwnedJob)
        tree.handle = 99
        tree.api = SimpleNamespace(CloseHandle=lambda _: False)
        with self.assertRaises(OSError):
            tree.release()
        self.assertEqual(tree.handle, 99, 'failed release must not erase ownership')

    def test_close_all_without_primary_error_reports_failure_and_attempts_each_handle(self):
        from knowledge_bridge import windows_job as job
        tree = job.OwnedJob.__new__(job.OwnedJob)
        closed = []
        def close(handle):
            closed.append(handle)
            raise OSError('CONTROL_CLOSE_' + str(handle))
        tree.api = SimpleNamespace(CloseHandle=close)
        with self.assertRaisesRegex(OSError, 'CONTROL_CLOSE_10') as caught:
            tree.close_handles([10, 20])
        self.assertEqual(closed, [10, 20])
        self.assertIn('CONTROL_CLOSE_20', str(caught.exception.__notes__))


if __name__ == '__main__': unittest.main()
