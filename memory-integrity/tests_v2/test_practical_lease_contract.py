"""Lease-bound replacement contract: offline parsing evidence only."""
from dataclasses import fields
from datetime import datetime
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from hybrid_bridge import practical_contract as contract


def packet(**changes):
    value = dict(schema_version=2, work_item_id='work-1', operation_id='op-1',
                 action='guarded_title_lease', task_id='mipx-1', actor='alice', title='safe title',
                 expected_status='in_progress', grant_id='grant-1', expected_row_lock=-7,
                 lease_holder='alice', lease_granted_node='practical-approved-scratch-only',
                 lease_granted_at_utc='2026-10-14 10:00:00.000000',
                 lease_expires_at_utc='2026-10-14 10:05:00.000000',
                 lease_heartbeat_at_utc='2026-10-14 10:00:00.000000')
    value.update(changes)
    value['command_digest'] = contract.canonical_command_digest(value)
    return value


class LeaseContract(unittest.TestCase):
    def request(self, value):
        self.assertTrue(hasattr(contract, 'LeaseGuardedTitleRequest'),
                        'real-lease-bound replacement request is absent')
        return contract.LeaseGuardedTitleRequest.from_value(value)

    def test_fixed_deadline_is_original_real_lease_snapshot(self):
        req = self.request(packet())
        self.assertEqual(req.fixed_deadline_utc, req.lease_expires_at_utc)
        self.assertNotIn('new_deadline_utc', {field.name for field in fields(req)})

    def test_title_cannot_carry_reassignment_or_deadline_authority(self):
        for field, value in [('target_actor', 'bob'), ('new_grant_id', 'replacement'),
                             ('fixed_deadline_utc', '2030-01-01 00:00:00.000000'),
                             ('new_deadline_utc', '2030-01-01 00:00:00.000000')]:
            with self.assertRaises(contract.PracticalContractError):
                self.request(packet(**{field: value}))

    def test_holder_status_node_and_temporal_order_refuse_wrong_basis(self):
        for change in [dict(lease_holder='bob'), dict(expected_status='open'),
                       dict(lease_granted_node=''), dict(expected_row_lock=True),
                       dict(lease_granted_at_utc='2026-10-14 10:06:00.000000'),
                       dict(lease_heartbeat_at_utc='2026-10-14 09:59:59.000000'),
                       dict(lease_expires_at_utc='2026-02-31 10:05:00.000000'),
                       dict(lease_expires_at_utc='2026-10-14 10:05:00.000001')]:
            with self.subTest(change=change), self.assertRaises(contract.PracticalContractError):
                self.request(packet(**change))

    def test_digest_binds_every_lease_fact(self):
        value = packet()
        value['lease_granted_node'] = 'other-node'
        with self.assertRaises(contract.PracticalContractError):
            self.request(value)


if __name__ == '__main__':
    unittest.main(verbosity=2)
