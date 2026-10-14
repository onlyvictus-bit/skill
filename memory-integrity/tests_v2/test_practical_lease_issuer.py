"""Offline contract checks for the P1b initial-lease issuer.

These tests exercise parsing and generated SQL only. They do not execute a
native SQL dialect and do not establish rollback or transaction atomicity.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from hybrid_bridge import practical_contract as contract
from hybrid_bridge.practical_contract import LeasePracticalSelection, PracticalContractError


def claim_packet(**changes):
    value = {
        'schema_version': 2,
        'work_item_id': 'work-claim-1',
        'operation_id': 'op-claim-1',
        'action': 'initial_claim_lease',
        'task_id': 'mipx-claim-1',
        'actor': 'alice',
        'expected_status': 'open',
        'expected_assignee': None,
        'expected_row_lock': -17,
        'new_grant_id': 'grant-claim-1',
    }
    value.update(changes)
    value['command_digest'] = contract.canonical_command_digest(value)
    return value


def selection():
    return LeasePracticalSelection(
        scratch_root='C:/Users/sakth/memory-integrity-practical-fence-20261013/pilot-1',
        dolt_executable='C:/dolt.exe', dolt_sha256='a' * 64, host='127.0.0.1', port=50001,
        database='mipx', main_branch='main', incarnation='store-1',
        native_node_id='practical-approved-scratch-only',
        candidate_route='APPROVED_SCRATCH_PRACTICAL_CONTRACT')


class LeaseClaimRequestTests(unittest.TestCase):
    def request(self, value):
        from hybrid_bridge.practical_lease_issuer import LeaseClaimRequest
        return LeaseClaimRequest.from_value(value)

    def test_exact_v2_claim_shape_has_no_caller_deadline_or_lease_authority(self):
        request = self.request(claim_packet())
        self.assertEqual(request.schema_version, 2)
        self.assertEqual(request.action, 'initial_claim_lease')
        self.assertFalse(hasattr(request, 'new_deadline_utc'))
        for bad in ({'new_deadline_utc': '2030-01-01 00:00:00.000000'},
                    {'fresh_authorization_deadline_utc': '2030-01-01 00:00:00.000000'},
                    {'lease_expiry_utc': '2030-01-01 00:00:00.000000'}):
            with self.subTest(bad=bad), self.assertRaises(PracticalContractError):
                self.request(claim_packet(**bad))

    def test_open_unassigned_observed_native_zero_or_signed_row_lock_and_digest_are_load_bearing(self):
        self.assertEqual(self.request(claim_packet(expected_row_lock=0)).expected_row_lock, 0)
        for bad in ({'expected_status': 'in_progress'}, {'expected_assignee': 'alice'},
                    {'expected_row_lock': True}, {'expected_row_lock': 2 ** 63}):
            with self.subTest(bad=bad), self.assertRaises(PracticalContractError):
                self.request(claim_packet(**bad))
        bad_digest = claim_packet()
        bad_digest['command_digest'] = '0' * 64
        with self.assertRaises(PracticalContractError):
            self.request(bad_digest)


class InitialClaimSQLTests(unittest.TestCase):
    def test_initial_claim_uses_only_db_minted_lease_and_exact_receipt_binding(self):
        from hybrid_bridge import practical_lease_sql
        sql = practical_lease_sql.initial_claim_sql(selection(), claim_packet())
        for text in ('UTC_TIMESTAMP(6)', 'DATE_ADD(@mi2_lease_granted, INTERVAL 300 SECOND)',
                     'CAST(@mi2_auth AS DATETIME)', 'INSERT INTO leases',
                     'INSERT INTO mi_practical_v2_grants',
                     'INSERT INTO mi_practical_v2_current_grants',
                     'INSERT INTO mi_practical_v2_grant_history',
                     'INSERT INTO mi_practical_v2_operations',
                     'lease_expires_at_utc', '6261636b656e645f6f7065726174696f6e5f6964',
                     'E_MI2_INITIAL_CLAIM_AUTH', 'E_MI2_CURRENT_GRANT_EXISTS',
                     'E_MI2_OPERATION_REPLAY', 'E_MI2_RECEIPT_CARDINALITY'):
            self.assertIn(text, sql)
        self.assertEqual(sql.count('UTC_TIMESTAMP(6)'), 1)
        self.assertNotIn('new_deadline_utc', sql)
        self.assertNotIn('fresh_authorization_deadline_utc', sql)
        for forbidden in ('DELETE ', 'DROP ', 'DOLT_ADD', 'DOLT_COMMIT'):
            self.assertNotIn(forbidden, sql)

    def test_claim_batch_has_explicit_error_rollback_but_no_atomicity_claim(self):
        from hybrid_bridge import practical_lease_sql
        sql = practical_lease_sql.initial_claim_sql(selection(), claim_packet())
        self.assertIn('DECLARE EXIT HANDLER FOR SQLEXCEPTION', sql)
        self.assertIn('ROLLBACK;', sql)
        self.assertIn('RESIGNAL;', sql)
        self.assertLess(sql.index('START TRANSACTION;'), sql.index('COMMIT;'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
