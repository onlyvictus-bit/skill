"""Offline native policy precedes DB access, reservation and acceptance."""
import importlib.util
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from complete_read_v2 import ledger


class NoDatabaseAccess:
    def __getattr__(self, name):
        raise AssertionError('database reached before release refusal: ' + name)


class OfflineReleaseProfile(unittest.TestCase):
    def test_native_authority_disabled(self):
        self.assertIsNotNone(importlib.util.find_spec('complete_read_v2.release_profile'),
                             'companion release enforcement not implemented')
        from complete_read_v2 import release_profile
        with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
            release_profile.require_native_execution_enabled()

    def test_reservation_refuses_before_database_access(self):
        with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
            ledger.reserve_practical_native_intent(NoDatabaseAccess(), {})

    def test_dispatch_refuses_before_authority_consumption(self):
        with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
            ledger.consume_practical_native_dispatch(NoDatabaseAccess(), {}, object())

    def test_reconciliation_cannot_promote_applied(self):
        with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
            ledger.complete_practical_native_readback(NoDatabaseAccess(), {}, object())

    def test_direct_native_success_event_refuses_before_database(self):
        with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
            ledger.coordination_record_event(NoDatabaseAccess(), 'NATIVE_OUTCOME', 'work', '{}',
                                             identity={'native_evidence_class':'NATIVE_VERIFIED'})
