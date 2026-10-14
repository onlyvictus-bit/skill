"""Public CLI routing tests, not native qualification."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / 'scripts/memory_integrity_workflow.py'


class PracticalCLI(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
