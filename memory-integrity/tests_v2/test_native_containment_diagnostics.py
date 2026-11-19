"""Native capture terminates an assigned tree before waiting on held pipes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).absolute().parents[1]/'scripts'))
from hybrid_bridge import native_observation as obs


@unittest.skipUnless(os.name == 'nt', 'Windows native capture proof required')
class NativeCaptureOwnerTests(unittest.TestCase):
    def test_assignment_failure_reaps_unassigned_root_before_authored_code(self):
        from knowledge_bridge import windows_owned_process as owned
        original = owned._Job
        class RefusedJob(original):
            def __init__(self):
                super().__init__()
                self.api.AssignProcessToJobObject = lambda *_: False
        with tempfile.TemporaryDirectory(prefix='native-capture-assign-') as name:
            root = Path(name); marker = root/'must-not-run'
            script = 'from pathlib import Path; Path('+repr(str(marker))+').write_text("bad")'
            with patch.object(owned, '_Job', RefusedJob):
                with self.assertRaises(OSError) as caught:
                    obs._capture_process([sys.executable,'-c',script],
                        cwd=name, env=dict(os.environ), timeout=5)
            self.assertFalse(marker.exists())
            proof = caught.exception.native_capture_proof
            self.assertFalse(proof['assigned_before_resume'])
            self.assertTrue(proof['termination']['root_native_exit_proved'])
            self.assertTrue(proof['released'])

    def test_timeout_proves_owned_tree_without_taskkill(self):
        script = ('import subprocess,sys,time; '
                  'p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"]); '
                  'print(p.pid,flush=True); time.sleep(60)')
        with tempfile.TemporaryDirectory(prefix='native-capture-timeout-') as name:
            with patch.object(obs.subprocess, 'run', side_effect=AssertionError('taskkill must not run')):
                result = obs._capture_process([sys.executable,'-B','-c',script],
                    cwd=name, env=dict(os.environ), timeout=1)
            (Path(name)/'Result.json').write_text(json.dumps({k:v for k,v in result.items()
                if k not in ('stdout','stderr')}), encoding='utf-8')
            self.assertTrue(result['timed_out'])
            self.assertTrue(result['capture_complete'], result)
            self.assertTrue(result['tree_contained'], result)
            self.assertEqual(result['capture_errors'], [])
            proof = result['native_ownership']
            self.assertTrue(proof['termination']['root_native_exit_proved'])
            self.assertTrue(proof['released'])
            self.assertGreaterEqual(proof['termination']['accounting_total'], 2)
            self.assertIn('TerminateJobObject', proof['termination']['operations'])

    def test_clean_root_exit_releases_inherited_descendant_pipes(self):
        script = ('import subprocess,sys; '
                  'p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"]); '
                  'print(p.pid,flush=True)')
        with tempfile.TemporaryDirectory(prefix='native-capture-clean-') as name:
            result = obs._capture_process([sys.executable,'-B','-c',script],
                cwd=name, env=dict(os.environ), timeout=5)
            self.assertEqual(result['exit_code'], 0)
            self.assertFalse(result['kill_path_used'])
            self.assertTrue(result['capture_complete'], result)
            self.assertTrue(result['native_ownership']['termination']['root_native_exit_proved'])
            self.assertGreaterEqual(result['native_ownership']['termination']['accounting_total'], 2)

    def test_resume_failure_preserves_cause_and_reaps_suspended_root(self):
        from knowledge_bridge import windows_owned_process as owned
        with tempfile.TemporaryDirectory(prefix='native-capture-resume-') as name:
            root = Path(name); marker = root/'must-not-run'
            script = 'from pathlib import Path; Path('+repr(str(marker))+').write_text("bad")'
            with patch.object(owned._Job, 'resume', side_effect=OSError('CONTROL_RESUME_FAILURE')):
                with self.assertRaisesRegex(OSError, 'CONTROL_RESUME_FAILURE') as caught:
                    obs._capture_process([sys.executable,'-c',script],
                        cwd=name, env=dict(os.environ), timeout=5)
            self.assertFalse(marker.exists())
            self.assertTrue(caught.exception.native_capture_proof['termination']['root_native_exit_proved'])
            self.assertTrue(caught.exception.native_capture_proof['released'])

    def test_error_after_actual_resume_still_terminates_assigned_job(self):
        from knowledge_bridge import windows_owned_process as owned
        real_resume = owned._Job.resume
        def resumed_then_error(job, process):
            real_resume(job, process)
            raise OSError('CONTROL_AFTER_RESUME')
        with tempfile.TemporaryDirectory(prefix='native-capture-partial-resume-') as name:
            with patch.object(owned._Job, 'resume', resumed_then_error):
                with self.assertRaisesRegex(OSError, 'CONTROL_AFTER_RESUME') as caught:
                    obs._capture_process([sys.executable,'-c','import time; time.sleep(60)'],
                        cwd=name, env=dict(os.environ), timeout=5)
            proof = caught.exception.native_capture_proof
            self.assertTrue(proof['resume_attempted'])
            self.assertTrue(proof['termination']['root_native_exit_proved'])
            self.assertTrue(proof['termination']['job_empty_observed'])
            self.assertTrue(proof['released'])

    def test_output_overflow_requests_main_thread_native_shutdown(self):
        import threading
        main = threading.get_ident(); calls = []
        real = obs._finish_windows_capture
        def finish(*args):
            calls.append(threading.get_ident())
            return real(*args)
        with tempfile.TemporaryDirectory(prefix='native-capture-overflow-') as name:
            with patch.object(obs, 'MAX_OUTPUT_BYTES', 128), patch.object(obs, '_finish_windows_capture', finish):
                result = obs._capture_process([sys.executable,'-c',
                    'import sys,time; print("x"*131072,flush=True);time.sleep(60)'],
                    cwd=name, env=dict(os.environ), timeout=5)
            self.assertTrue(result['output_limit_exceeded'])
            self.assertTrue(result['kill_path_used'])
            self.assertEqual(calls, [main])
            self.assertTrue(result['native_ownership']['released'])
            self.assertTrue(result['native_ownership']['termination']['job_empty_observed'])


class NativeCaptureFailureTests(unittest.TestCase):
    def controls(self, active=0):
        process = Mock(_handle=17)
        process.poll.return_value = 0
        job = Mock()
        job.accounting.return_value = SimpleNamespace(active=active, total=2)
        job.api.WaitForSingleObject.return_value = 0
        def check(value):
            if not value:
                raise OSError('CONTROL_NATIVE_FAILURE')
            return value
        job.check.side_effect = check
        return process, job, {'termination': {}, 'released': False}

    def test_terminate_failure_cannot_become_exit_proof(self):
        process, job, proof = self.controls(active=1)
        job.api.TerminateJobObject.return_value = 0
        with self.assertRaisesRegex(OSError, 'CONTROL_NATIVE_FAILURE'):
            obs._finish_windows_capture(process, job, proof, time.monotonic()+5)
        self.assertFalse(proof['termination'].get('root_native_exit_proved', False))
        self.assertFalse(proof['released'])

    def test_active_job_after_deadline_cannot_become_exit_proof(self):
        process, job, proof = self.controls(active=1)
        with self.assertRaisesRegex(TimeoutError, 'E_NATIVE_CAPTURE_JOB_STILL_ACTIVE'):
            obs._finish_windows_capture(process, job, proof, time.monotonic()-1)
        self.assertFalse(proof['termination'].get('job_empty_observed', False))
        self.assertFalse(proof['released'])

    def test_failed_root_native_wait_cannot_become_exit_proof(self):
        process, job, proof = self.controls()
        job.api.WaitForSingleObject.return_value = 258
        with self.assertRaisesRegex(TimeoutError, 'E_NATIVE_CAPTURE_ROOT_STILL_ALIVE'):
            obs._finish_windows_capture(process, job, proof, time.monotonic()+5)
        self.assertFalse(proof['termination'].get('root_native_exit_proved', False))
        self.assertFalse(proof['released'])

    def test_close_failure_cannot_become_released_proof(self):
        process, job, proof = self.controls()
        job.close.side_effect = OSError('CONTROL_CLOSE_FAILURE')
        with self.assertRaisesRegex(OSError, 'CONTROL_CLOSE_FAILURE'):
            obs._finish_windows_capture(process, job, proof, time.monotonic()+5)
        self.assertTrue(proof['termination']['root_native_exit_proved'])
        self.assertFalse(proof['released'])

    def test_posix_process_group_timeout_path_is_preserved(self):
        import io
        process = Mock(pid=123, stdout=io.BytesIO(), stderr=io.BytesIO())
        process.wait.side_effect = [subprocess.TimeoutExpired(['fixture'], 1), -9]
        process.poll.side_effect = [None, -9]
        with patch.object(obs.os, 'name', 'posix'), patch.object(obs.subprocess, 'Popen', return_value=process), \
                patch.object(obs.os, 'getpgid', create=True, return_value=123), \
                patch.object(obs.os, 'killpg', create=True) as kill, \
                patch.object(obs.signal, 'SIGKILL', 9, create=True):
            result = obs._capture_process(['fixture'], cwd='fixture', env={}, timeout=1)
        kill.assert_called_once()
        self.assertTrue(result['timed_out'])
        self.assertTrue(result['capture_complete'])
        self.assertTrue(result['tree_contained'])
        self.assertIsNone(result['native_ownership'])

    def test_command_retains_native_proof_before_rejecting_timeout(self):
        import hashlib
        with tempfile.TemporaryDirectory(prefix='native-command-proof-') as name:
            root = Path(name); exe = root/'fixture.exe'; exe.write_bytes(b'inert fixture')
            proof = {'scope': 'WINDOWS_CAPTURE_JOB_EMPTY_STATE_V1', 'released': True}
            completed = {'exit_code': 1, 'stdout': b'', 'stderr': b'', 'timed_out': True,
                         'capture_complete': True, 'output_limit_exceeded': False,
                         'capture_errors': [], 'process_id': 7, 'native_ownership': proof}
            records = []
            with patch.object(obs, 'require_native_execution_enabled'), \
                    patch.object(obs, '_capture_process', return_value=completed):
                with self.assertRaisesRegex(ValueError, 'E_NATIVE_TIMEOUT'):
                    obs._command(exe, root, root, 'version', records,
                                 hashlib.sha256(exe.read_bytes()).hexdigest())
            self.assertEqual(records[0]['native_ownership'], proof)

    def test_command_retains_original_setup_cause_and_cleanup_proof(self):
        import hashlib
        with tempfile.TemporaryDirectory(prefix='native-command-error-') as name:
            root = Path(name); exe = root/'fixture.exe'; exe.write_bytes(b'inert fixture')
            error = OSError('CONTROL_SETUP_FAILURE'); error.add_note('CONTROL_CLEANUP_NOTE')
            error.native_capture_proof = {'assigned_before_resume': False, 'released': True}
            records = []
            with patch.object(obs, 'require_native_execution_enabled'), \
                    patch.object(obs, '_capture_process', side_effect=error):
                with self.assertRaises(OSError) as caught:
                    obs._command(exe, root, root, 'version', records,
                                 hashlib.sha256(exe.read_bytes()).hexdigest())
            self.assertIs(caught.exception, error)
            self.assertEqual(records[0]['native_ownership'], error.native_capture_proof)
            self.assertIn('CONTROL_CLEANUP_NOTE', records[0]['failure']['notes'])


if __name__ == '__main__':
    unittest.main()
