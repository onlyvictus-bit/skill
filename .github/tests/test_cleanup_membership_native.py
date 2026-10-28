"""Native MP1 witness controls; no selected-runtime or product qualification."""
import importlib.util
import json
import os
from pathlib import Path
import time
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch


HERE = Path(__file__).absolute().parents[1]
SCRIPT = HERE/'scripts'/'cleanup_membership_probe.py'


def retained_root(label):
    """Test evidence is deliberately retained; no TemporaryDirectory cleanup."""
    root = HERE/'run-artifacts'/'cleanup-membership-native-controls'
    root.mkdir(parents=True, exist_ok=True)
    path = root/(label+'-'+str(time.time_ns())+'-'+uuid.uuid4().hex)
    path.mkdir()
    return path


@unittest.skipUnless(os.name == 'nt', 'Windows native job and thread observation required')
class MembershipNativeControls(unittest.TestCase):
    def module(self):
        if not SCRIPT.exists():
            self.fail('MP1 native membership witness is not implemented')
        spec = importlib.util.spec_from_file_location('mp1_native_probe', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_probe_refuses_a_preexisting_output_directory(self):
        module = self.module()
        root = retained_root('preexisting-output')
        source = root/'source'
        source.mkdir()
        output = root/'already-exists'
        output.mkdir()
        with self.assertRaisesRegex(ValueError, 'E_MP_OUTPUT_EXISTS'):
            module.run_probe(source, output)

    def test_native_probe_binds_four_roles_and_records_emergency_result(self):
        module = self.module()
        source = Path(__file__).absolute().parents[2]
        output = retained_root('native-witness')/'witness'
        # Direct Python 3.14 has no venv launcher layers.  This is deliberately
        # a controller-only topology and cannot satisfy the sealed runtime path.
        result = module.run_probe(source, output, control_topology=True)
        self.assertEqual(result['scope'], 'MP1_MEMBERSHIP_ONLY_NOT_FIX')
        self.assertIn(result['status'], {
            'MEMBERSHIP_GAP_OBSERVED_NOT_FIXED',
            'MEMBERSHIP_CONTRADICTION_REQUIRES_REDESIGN',
            'PIPE_CANCELLATION_GAP_NOT_FIXED',
            'FAILURE_NOT_REPRODUCED_INCONCLUSIVE',
        })
        self.assertEqual(set(result['after']), {'root', 'relay', 'launcher', 'child'})
        self.assertFalse(result['stage_complete'])
        self.assertFalse(result['gate1_complete'])
        self.assertFalse(result['release_ready'])
        self.assertFalse(result['installed'])
        self.assertFalse(result['fix_validated'])
        self.assertFalse(result['root_cause_confirmed'])
        self.assertFalse(result['producer_authentication'])
        self.assertTrue(result['emergency_cleanup']['completed'])
        self.assertEqual(result['emergency_cleanup']['errors'], [])
        self.assertTrue(result['emergency_cleanup']['streams_closed'])
        self.assertTrue(result['emergency_cleanup']['root_reaped'])
        self.assertTrue(result['emergency_cleanup']['job_closed'])
        self.assertTrue(result['handle_cleanup']['completed'])
        self.assertEqual(result['handle_cleanup']['errors'], [])
        self.assertTrue((output/'Probe.json').is_file())
        self.assertTrue((output/'Incremental.jsonl').is_file())

    def test_fault_after_exact_role_pinning_retains_bounded_emergency_receipt(self):
        module = self.module()
        source = Path(__file__).absolute().parents[2]
        output = retained_root('fault-after-pin')/'witness'
        with self.assertRaisesRegex(RuntimeError, 'E_MP_CONTROL_FAULT_AFTER_ROLES_PINNED'):
            module.run_probe(source, output, control_topology=True, _fault_after_roles_pinned=True)
        receipt = json.loads((output/'Probe-error.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['emergency_cleanup']['completed'])
        self.assertTrue(receipt['handle_cleanup']['completed'])
        self.assertFalse(receipt['stage_complete'])
        self.assertTrue((output/'Incremental.jsonl').is_file())

    def test_blocked_writer_uses_its_native_thread_handle_before_fixture_termination(self):
        module = self.module()
        source = Path(__file__).absolute().parents[2]
        output = retained_root('native-writer-cancel')/'witness'
        result = module.run_probe(source, output, control_topology=True, _force_stop_failure=True)
        cancellation = result['emergency_cleanup']['cancel_synchronous_io']
        self.assertIsNotNone(cancellation, 'blocked writer must receive CancelSynchronousIo on its pinned native handle')
        self.assertTrue(cancellation['ok'], 'the native blocked-write control must observe a successful cancellation request')
        self.assertTrue(result['emergency_cleanup']['writer_joined'])
        self.assertTrue(result['emergency_cleanup']['completed'])
        # This deliberately injected pre-stop failure never calls session.stop;
        # live in-job handles are a control observation, not a product claim.
        self.assertEqual(result['status'], 'MEMBERSHIP_CONTRADICTION_REQUIRES_REDESIGN')

    def test_owned_native_handles_close_once_and_a_failure_is_retained(self):
        module = self.module()
        calls = []
        api = SimpleNamespace(CloseHandle=lambda handle: calls.append(handle) or False)
        events = []
        result = module._close_owned_handles(api, {'one': 7}, lambda *args, **kwargs: events.append((args, kwargs)))
        self.assertFalse(result['completed'])
        self.assertEqual(calls, [7])
        self.assertTrue(result['errors'])
        self.assertEqual(events[0][0][0], 'handle-cleanup')

    def test_borrowed_root_birth_mismatch_is_never_closed_and_local_mismatch_closes_once(self):
        module = self.module()
        marker = {'pid': 9, 'creation': '2'}
        borrowed_api = SimpleNamespace(OpenProcess=lambda *args: self.fail('borrowed root reopened'),
                                       CloseHandle=lambda handle: self.fail('borrowed root closed'))
        with patch.object(module, '_creation', return_value='1'):
            with self.assertRaisesRegex(ValueError, 'E_MP_PID_REUSED'):
                module._adopt_role_handle(borrowed_api, 'root', marker, 33, {})
            owned = {}
            closed = []
            local_api = SimpleNamespace(OpenProcess=lambda *args: 44,
                                        CloseHandle=lambda handle: closed.append(handle) or True)
            with self.assertRaisesRegex(ValueError, 'E_MP_PID_REUSED'):
                module._adopt_role_handle(local_api, 'child', marker, None, owned)
        self.assertEqual(owned, {})
        self.assertEqual(closed, [44])

    def test_local_birth_mismatch_keeps_its_primary_error_when_close_raises(self):
        module = self.module()
        marker = {'pid': 9, 'creation': '2'}
        api = SimpleNamespace(OpenProcess=lambda *args: 44,
                              CloseHandle=lambda handle: (_ for _ in ()).throw(OSError('close failed')))
        with patch.object(module, '_creation', return_value='1'):
            with self.assertRaisesRegex(ValueError, 'E_MP_PID_REUSED') as raised:
                module._adopt_role_handle(api, 'child', marker, None, {})
        self.assertIn('E_MP_HANDLE_CLOSE', '\n'.join(getattr(raised.exception, '__notes__', ())))

    def test_actual_probe_close_failure_becomes_error_receipt_not_success_probe(self):
        module = self.module(); source = Path(__file__).absolute().parents[2]
        output = retained_root('handle-close-failure')/'witness'
        with self.assertRaisesRegex(ValueError, 'E_MP_HANDLE_CLEANUP'):
            module.run_probe(source, output, control_topology=True, _force_handle_cleanup_error=True)
        self.assertFalse((output/'Probe.json').exists())
        receipt = json.loads((output/'Probe-error.json').read_text(encoding='utf-8'))
        self.assertFalse(receipt['handle_cleanup']['completed'])

    def test_nonvalue_error_after_real_writer_start_retains_writer_cleanup(self):
        module = self.module(); source = Path(__file__).absolute().parents[2]
        output = retained_root('nonvalue-after-writer')/'witness'
        with self.assertRaisesRegex(RuntimeError, 'E_MP_CONTROL_NONVALUE_AFTER_WRITER_START'):
            module.run_probe(source, output, control_topology=True, _force_nonvalue_after_request=True)
        receipt = json.loads((output/'Probe-error.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['emergency_cleanup']['writer_joined'])

    def test_writer_identity_change_refuses_the_opened_thread_handle(self):
        module = self.module()
        writer = SimpleNamespace(native_id=7, is_alive=lambda: True)
        api = SimpleNamespace(OpenThread=lambda *args: 9, GetThreadId=lambda handle: 8,
                              GetProcessIdOfThread=lambda handle: 1, CloseHandle=lambda handle: True)
        with self.assertRaisesRegex(ValueError, 'E_MP_WRITER_REUSED'):
            module._pin_writer(api, writer, {})

    def test_writer_identity_rejection_retains_its_handle_close_failure(self):
        module = self.module()
        writer = SimpleNamespace(native_id=7, is_alive=lambda: True)
        api = SimpleNamespace(OpenThread=lambda *args: 9, GetThreadId=lambda handle: 8,
                              GetProcessIdOfThread=lambda handle: 1, CloseHandle=lambda handle: False)
        with self.assertRaisesRegex(ValueError, 'E_MP_WRITER_REUSED') as raised:
            module._pin_writer(api, writer, {})
        self.assertIn('E_MP_HANDLE_CLOSE', '\n'.join(getattr(raised.exception, '__notes__', ())))


if __name__ == '__main__':
    unittest.main()
