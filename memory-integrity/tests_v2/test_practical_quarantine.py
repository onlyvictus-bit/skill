"""The reviewed-invalid predecessor must not dispatch or seal native proof."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT.parent / 'claude-mon/scripts'))
from hybrid_bridge.practical_backend import PracticalBackend
from hybrid_bridge.practical_consumer import PracticalNativeConsumer, PracticalConsumerError
from hybrid_bridge.practical_contract import PracticalContractError
from complete_read_v2 import ledger


class PredecessorQuarantine(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def runner(*args):
            self.calls.append(args)
            return {'returncode': 0, 'stdout': b'{"rows":[]}', 'stderr': b''}
        self.backend = PracticalBackend(dict(scratch_root='C:/scratch', dolt_executable='C:/dolt.exe',
            dolt_sha256='a' * 64, host='127.0.0.1', port=50001, database='mipx',
            main_branch='main', incarnation='scratch-1', native_node_id='practical-approved-scratch-only',
            candidate_route='APPROVED_SCRATCH_PRACTICAL_CONTRACT'), runner=runner)

    def test_all_predecessor_mutation_entrypoints_stop_before_dispatch(self):
        for name in ['transition', 'guarded_title', 'initial_claim', 'expired_reacquire']:
            with self.subTest(name=name), self.assertRaisesRegex(
                    PracticalContractError, 'E_PRACTICAL_LEASE_REVISION_REQUIRED'):
                getattr(self.backend, name)({})
        self.assertEqual(self.calls, [])

    def test_predecessor_or_fake_runner_cannot_register_protected_consumer(self):
        retained = Path(tempfile.mkdtemp(prefix='practical-quarantine-retained-'))
        db = ledger.connect(retained / 'ledger.sqlite')
        try:
            before = db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
            with self.assertRaisesRegex(PracticalConsumerError, 'E_PRACTICAL_REVISION_STOPPED'):
                PracticalNativeConsumer(db, self.backend)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0], before)
            self.assertEqual(self.calls, [])
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
