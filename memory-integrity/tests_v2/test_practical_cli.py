"""Public CLI routing tests, not native qualification."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import hashlib
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / 'scripts/memory_integrity_workflow.py'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False).encode('utf-8')


def lease_selection():
    return {
        'scratch_root': 'C:/scratch/practical-cli',
        'dolt_executable': 'C:/scratch/practical-cli/dolt.exe',
        'dolt_sha256': 'a' * 64,
        'host': '127.0.0.1',
        'port': 50001,
        'database': 'mipx',
        'main_branch': 'main',
        'incarnation': 'store-cli-1',
        'native_node_id': 'practical-cli-node-1',
        'candidate_route': 'APPROVED_SCRATCH_PRACTICAL_CONTRACT',
    }


def lease_request(**changes):
    value = {
        'schema_version': 2,
        'work_item_id': 'cm-work-17',
        'operation_id': 'op-cli-title-1',
        'action': 'guarded_title_lease',
        'task_id': 'mip-42',
        'actor': 'alice',
        'title': 'Fail closed title',
        'expected_status': 'in_progress',
        'grant_id': 'grant-7',
        'expected_row_lock': 731,
        'lease_holder': 'alice',
        'lease_granted_node': 'practical-cli-node-1',
        'lease_granted_at_utc': '2030-01-02 03:00:00.000000',
        'lease_expires_at_utc': '2030-01-02 03:05:00.000000',
        'lease_heartbeat_at_utc': '2030-01-02 03:01:00.000000',
    }
    value.update(changes)
    value['command_digest'] = hashlib.sha256(canonical(value)).hexdigest()
    return value


class PracticalCLI(unittest.TestCase):
    def setUp(self):
        # Retain the fixture, but respect the selected test-owned temp root.
        # A hard-coded sibling can exist yet reject mkdir; Windows tempfile
        # then repeatedly retries PermissionError as a possible name collision.
        retained_base = Path(tempfile.gettempdir())
        retained = Path(tempfile.mkdtemp(prefix='practical-cli-retained-',
                                         dir=str(retained_base)))
        self.selection_file = retained / 'selection.json'
        self.request_file = retained / 'request.json'
        self.cm_ledger = retained / 'cm-ledger.sqlite'
        self.artifacts_dir = retained / 'artifacts'
        self.receipt = retained / 'receipt.json'
        self.selection_file.write_bytes(canonical(lease_selection()))
        self.request_file.write_bytes(canonical(lease_request()))

    def practical(self, command, *extra):
        return subprocess.run([
            sys.executable, '-B', str(ENTRY), command,
            '--claude-mon-root', str(ROOT.parent / 'claude-mon'),
            '--selection-file', str(self.selection_file),
            '--request-file', str(self.request_file),
            '--cm-ledger', str(self.cm_ledger),
            '--artifacts-dir', str(self.artifacts_dir),
            '--receipt', str(self.receipt), *extra,
        ], capture_output=True, text=True, timeout=20)

    def assert_zero_effects(self, result, code):
        self.assertEqual(result.returncode, 2, result.stderr)
        value = json.loads(result.stdout)
        self.assertFalse(value['ok'])
        self.assertEqual(value['evidence_class'], 'PREFLIGHT_ONLY')
        self.assertEqual(value['code'], code)
        self.assertEqual(value['adapter_calls'], 0)
        self.assertEqual(value['approvals_consumed'], 0)
        self.assertFalse(value['database_write_performed'])
        self.assertFalse(value['inference_sent'])
        self.assertFalse(value['native_gate_a_qualified'])
        self.assertFalse(value['native_acceptance_qualified'])
        self.assertFalse(value['native_merge_qualified'])
        self.assertFalse(self.cm_ledger.exists())
        self.assertFalse(self.receipt.exists())
        self.assertFalse(self.artifacts_dir.exists())
        return value

    def test_explicit_candidate_and_read_only_recovery_routes_exist(self):
        result = subprocess.run([sys.executable, '-B', str(ENTRY), '--help'],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('practical-title', result.stdout)
        self.assertIn('practical-reconcile', result.stdout)

    def test_candidate_fails_closed_on_missing_input_without_native_proof(self):
        result = subprocess.run([
            sys.executable, '-B', str(ENTRY), 'practical-title',
            '--claude-mon-root', str(ROOT.parent / 'claude-mon'),
            '--selection-file', str(ROOT / 'ABSENT-selection.json'),
            '--request-file', str(ROOT / 'ABSENT-request.json'),
            '--cm-ledger', str(ROOT / 'ABSENT-ledger.sqlite'),
            '--artifacts-dir', str(ROOT / 'ABSENT-artifacts'),
            '--receipt', str(ROOT / 'ABSENT-receipt-parent/result.json'),
        ], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        value = json.loads(result.stdout)
        self.assertFalse(value['ok'])
        self.assertFalse(value['native_gate_a_qualified'])
        self.assertFalse(value['native_acceptance_qualified'])
        self.assertFalse(value['native_merge_qualified'])
        self.assertFalse(value['database_write_performed'])
        self.assertFalse(value['inference_sent'])
        self.assertEqual(value['adapter_calls'], 0)

    def test_valid_schema2_candidate_refuses_pending_native_proof_without_effects(self):
        value = self.assert_zero_effects(self.practical('practical-title'),
                                         'E_PRACTICAL_NATIVE_PROOF_PENDING')
        self.assertIn('native mechanism unproved', value['blockers'][0].lower())

    def test_valid_schema2_reconcile_refuses_pending_sealed_cm_integration(self):
        value = self.assert_zero_effects(self.practical('practical-reconcile'),
                                         'E_PRACTICAL_CM_INTEGRATION_PENDING')
        self.assertNotIn('APPLIED', json.dumps(value, sort_keys=True))

    def test_duplicate_key_and_wrong_schema_are_json_refusals(self):
        self.selection_file.write_bytes(b'{"host":"127.0.0.1","host":"127.0.0.1"}')
        self.assert_zero_effects(self.practical('practical-title'),
                                 'E_PRACTICAL_JSON_DUPLICATE_KEY')
        self.selection_file.write_bytes(canonical(lease_selection()))
        self.request_file.write_bytes(canonical(lease_request(schema_version=1)))
        self.assert_zero_effects(self.practical('practical-title'),
                                 'E_PRACTICAL_LEASE_TITLE_ACTION')

    def test_unknown_request_field_cannot_inject_native_write_authority(self):
        self.request_file.write_bytes(canonical(lease_request(native_write_qualified=True)))
        self.assert_zero_effects(self.practical('practical-title'),
                                 'E_PRACTICAL_LEASE_TITLE_SCHEMA')

    def test_bad_digest_relative_path_and_activation_injection_refuse_as_json(self):
        self.request_file.write_bytes(canonical(lease_request(command_digest='0' * 64)))
        self.assert_zero_effects(self.practical('practical-title'),
                                 'E_PRACTICAL_COMMAND_DIGEST')
        result = subprocess.run([
            sys.executable, '-B', str(ENTRY), 'practical-title',
            '--claude-mon-root', str(ROOT.parent / 'claude-mon'),
            '--selection-file', 'relative-selection.json',
            '--request-file', str(self.request_file),
            '--cm-ledger', str(self.cm_ledger), '--artifacts-dir', str(self.artifacts_dir),
            '--receipt', str(self.receipt),
        ], capture_output=True, text=True, timeout=20)
        self.assert_zero_effects(result, 'E_PRACTICAL_PATH_ABSOLUTE')
        self.request_file.write_bytes(canonical(lease_request()))
        self.assert_zero_effects(self.practical('practical-title', '--native-write'),
                                 'E_PRACTICAL_ARGUMENTS')
        self.assert_zero_effects(self.practical('practical-title', '--runner', 'unsafe'),
                                 'E_PRACTICAL_ARGUMENTS')

    def test_oversized_and_malformed_utf8_inputs_refuse_without_creating_any_target(self):
        self.selection_file.write_bytes(b'{' + b' ' * (1024 * 1024 + 1) + b'}')
        self.assert_zero_effects(self.practical('practical-title'),
                                 'E_PRACTICAL_INPUT_TOO_LARGE')
        self.selection_file.write_bytes(b'\xff')
        self.assert_zero_effects(self.practical('practical-title'),
                                 'E_PRACTICAL_JSON_UTF8')

    def test_input_limit_applies_before_loading_unbounded_bytes(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from hybrid_bridge import practical_cli
        path = MagicMock()
        path.read_bytes.return_value = b' ' * (practical_cli.MAX_INPUT_BYTES + 1)
        path.open.return_value.__enter__.return_value.read.return_value = (
            b' ' * (practical_cli.MAX_INPUT_BYTES + 1))
        with self.assertRaisesRegex(ValueError, 'E_PRACTICAL_INPUT_TOO_LARGE'):
            practical_cli._strict_json(path)
        path.read_bytes.assert_not_called()
        path.open.assert_called_once_with('rb')
        path.open.return_value.__enter__.return_value.read.assert_called_once_with(
            practical_cli.MAX_INPUT_BYTES + 1)

    def test_fixture_is_scoped_to_selected_temporary_root(self):
        self.assertTrue(self.selection_file.parent.resolve().is_relative_to(
            Path(tempfile.gettempdir()).resolve()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
