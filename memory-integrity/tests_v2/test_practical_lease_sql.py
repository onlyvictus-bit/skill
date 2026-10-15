"""Generated lease SQL checks. These are NOT live SQL grammar/protocol proof."""
import importlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from hybrid_bridge.practical_contract import LeasePracticalSelection, LeaseGuardedTitleRequest, PracticalContractError
from tests_v2.test_practical_lease_contract import packet
from tests_v2.test_practical_lease_issuer import claim_packet


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

    def test_initial_claim_requires_the_db_current_pointer_before_title_use(self):
        sql = self.sql.initial_claim_sql(self.selection, claim_packet())
        self.assertIn('mi_practical_v2_current_grants', self.sql.v2_schema_sql())
        self.assertIn('INSERT INTO mi_practical_v2_current_grants', sql)
        guarded = self.sql.guarded_title_sql(self.selection, self.request)
        self.assertIn('JOIN mi_practical_v2_current_grants AS c', guarded)
        self.assertIn('c.grant_id = g.grant_id', guarded)
        self.assertIn('UPDATE mi_practical_v2_current_grants SET current_revision = @mi2_token', guarded)

    def test_title_compares_stored_deadline_and_exact_registered_database_branch(self):
        guarded = self.sql.guarded_title_sql(self.selection, self.request)
        self.assertIn('g.fixed_deadline_utc = l.lease_expires_at', guarded)
        self.assertIn('m.selected_database = ', guarded)
        self.assertIn('m.selected_main_branch = ', guarded)
        self.assertIn('DATABASE() IN (', guarded)

    def test_title_uses_microsecond_authorization_and_explicit_error_handler(self):
        guarded = self.sql.guarded_title_sql(self.selection, self.request)
        self.assertIn('SET @mi2_auth = UTC_TIMESTAMP(6);', guarded)
        self.assertNotIn('SET @mi2_auth = UTC_TIMESTAMP();', guarded)
        self.assertIn('BEGIN NOT ATOMIC', guarded)
        self.assertIn('DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;', guarded)
        self.assertLess(guarded.index('BEGIN NOT ATOMIC'), guarded.index('START TRANSACTION;'))
        self.assertLess(guarded.index('COMMIT;'), guarded.rindex('END;'))

    def test_title_predicates_use_binary_exact_owner_node_and_grant_comparisons(self):
        guarded = self.sql.guarded_title_sql(self.selection, self.request)
        for predicate in ('BINARY l.holder = BINARY ', 'BINARY l.granted_node = BINARY ',
                          'BINARY g.grant_id = BINARY ', 'BINARY g.actor = BINARY i.assignee',
                          'BINARY assignee = BINARY '):
            self.assertIn(predicate, guarded)

    def test_initial_claim_receipt_lease_snapshots_carry_fractional_suffix(self):
        # A claim-path receipt must feed a valid subsequent title request, and
        # the title contract only parses microsecond-suffixed lease text.
        sql = self.sql.initial_claim_sql(self.selection, claim_packet())
        for snapshot in ('@mi2_lease_granted', '@mi2_lease_expiry', '@mi2_lease_heartbeat'):
            with self.subTest(snapshot=snapshot):
                self.assertIn("DATE_FORMAT(%s,'%%Y-%%m-%%d %%H:%%i:%%s.%%f')" % snapshot, sql)

    def test_suffixless_lease_snapshot_cannot_form_a_title_request(self):
        # Locks the invariant from the validation side: without the suffix
        # the snapshot is refused, so the builder above must always emit it.
        with self.assertRaisesRegex(PracticalContractError, 'E_PRACTICAL_LEASE_EXPIRY'):
            LeaseGuardedTitleRequest.from_value(packet(lease_expires_at_utc='2026-10-14 10:05:00'))
        parsed = LeaseGuardedTitleRequest.from_value(packet())
        self.assertEqual(parsed.fixed_deadline_utc, parsed.lease_expires_at_utc)


if __name__ == '__main__':
    unittest.main(verbosity=2)
