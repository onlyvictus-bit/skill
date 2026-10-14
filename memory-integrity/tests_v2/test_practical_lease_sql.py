"""Generated lease SQL checks. These are NOT live SQL grammar/protocol proof."""
import importlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from hybrid_bridge.practical_contract import LeasePracticalSelection, LeaseGuardedTitleRequest
from tests_v2.test_practical_lease_contract import packet


class LeaseSQL(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / 'scripts/hybrid_bridge/practical_lease_sql.py').is_file(),
                        'real native-lease transaction builder is absent')
        self.sql = importlib.import_module('hybrid_bridge.practical_lease_sql')
        self.selection = LeasePracticalSelection(
            scratch_root='C:/Users/sakth/memory-integrity-practical-fence-20261013/pilot-1',
            dolt_executable='C:/dolt.exe', dolt_sha256='a' * 64, host='127.0.0.1', port=50001,
            database='mipx', main_branch='main', incarnation='store-1',
            native_node_id='practical-approved-scratch-only',
            candidate_route='APPROVED_SCRATCH_PRACTICAL_CONTRACT')
        self.request = LeaseGuardedTitleRequest.from_value(packet())

    def test_auth_reads_real_lease_and_stored_store_identity(self):
        sql = self.sql.guarded_title_sql(self.selection, self.request)
        for text in ['JOIN leases AS l', 'l.holder', 'l.granted_node', 'l.granted_at',
                     'l.lease_expires_at', 'l.heartbeat_at', 'm.store_incarnation',
                     'm.selection_digest', '@mi2_auth < l.lease_expires_at']:
            self.assertIn(text, sql)
        self.assertEqual(sql.count('UTC_TIMESTAMP('), 1)

    def test_title_write_cannot_update_assignee_status_or_native_lease(self):
        sql = self.sql.guarded_title_sql(self.selection, self.request)
        update = sql[sql.index('UPDATE issues'):sql.index('SET @mi2_issue_changed')]
        self.assertIn('SET title =', update)
        self.assertNotIn('assignee =', update.split('WHERE')[0])
        self.assertNotIn('status =', update.split('WHERE')[0])
        self.assertNotIn('UPDATE leases', sql)

    def test_transaction_asserts_effect_receipt_and_conflict_token_before_commit(self):
        sql = self.sql.guarded_title_sql(self.selection, self.request)
        for reason in ['E_MI2_AUTH', 'E_MI2_ISSUE_CARDINALITY', 'E_MI2_GRANT_CARDINALITY',
                       'E_MI2_TOKEN_CARDINALITY', 'E_MI2_RECEIPT_CARDINALITY']:
            self.assertIn(reason, sql[:sql.index('COMMIT;')])
        self.assertNotIn('DOLT_ADD', sql)
        self.assertNotIn('DOLT_COMMIT', sql)
        self.assertNotIn('DELETE ', sql)
        self.assertLess(sql.index('COMMIT;'), sql.rindex('SELECT receipt_json'))
        self.assertIn('JSON_SET', sql)
        self.assertNotIn('DATABASE_GENERATED', sql)

    def test_native_barrier_is_after_snapshot_auth_before_effect(self):
        sql = self.sql.experiment_guarded_title_sql(self.selection, self.request, pause_seconds=20)
        self.assertLess(sql.index('SET @mi2_authorized'), sql.index('DO SLEEP(20)'))
        self.assertLess(sql.index('E_MI2_AUTH'), sql.index('DO SLEEP(20)'))
        self.assertLess(sql.index('DO SLEEP(20)'), sql.index('UPDATE issues'))
        with self.assertRaises(ValueError):
            self.sql.experiment_guarded_title_sql(self.selection, self.request, pause_seconds='20; DROP TABLE x')


if __name__ == '__main__':
    unittest.main(verbosity=2)
