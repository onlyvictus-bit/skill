#!/usr/bin/env python3
"""Practical native journal: narrow durable reservation and readback fence.

These tests exercise only the CM-side journal.  The reader is a local test
double standing in for the separately owned protected backend consumer; no
native executable, shared database, or external service is used here.
"""
import copy
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import ledger  # noqa: E402

RETAINED_TEMP = Path(tempfile.gettempdir())


def binding(**changes):
    value = {
        "work_item_id": "W",
        "operation_id": "CM-OP-1",
        "selection_digest": "a" * 64,
        "store_incarnation": "store-incarnation-1",
        "database": "work-local.sqlite",
        "branch": "main",
        "native_task_id": "NATIVE-1",
        "actor": "worker-1",
        "grant_id": "grant-1",
        "original_row_lock": -7,
        "fixed_deadline": "2030-01-02T03:04:05Z",
        "command_digest": "b" * 64,
        "backend_operation_id": "backend-operation-1",
    }
    value.update(changes)
    return value


class Readback:
    """Concrete-shaped local reader; ledger invokes it, callers pass no receipt."""
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def read_practical_native_operation(self, observed_binding):
        self.calls += 1
        if callable(self.result):
            return self.result(observed_binding)
        return copy.deepcopy(self.result)


class PracticalJournalTests(unittest.TestCase):
    """LEGACY_MODEL_ONLY / POLICY_CHECK_TEST-MOCKED; no native transport."""
    def setUp(self):
        policy = patch('complete_read_v2.release_profile.require_native_execution_enabled')
        policy.start()
        self.addCleanup(policy.stop)
        # Keep unique local evidence after a run; this test never deletes it.
        self.temp = Path(tempfile.mkdtemp(
            prefix="practical-journal-", dir=RETAINED_TEMP))
        self.path = self.temp / "cm-ledger.sqlite"
        self.db = ledger.connect(self.path)
        ledger.create_work_item(self.db, "W", "task-digest", "source-id")
        # The practical journal must not attach to an unregistered/off task.
        ledger.coordination_put(self.db, "W", {"registered": True})

    def tearDown(self):
        self.db.close()

    def _register(self, reader):
        return ledger._register_practical_native_readback_consumer(self.db, reader)

    def _event_count(self):
        return self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def test_generic_event_api_refuses_practical_namespace(self):
        before = self._event_count()
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_EVENT"):
            ledger.event(self.db, "PRACTICAL_NATIVE_APPLIED", "W", "forged")
        self.assertEqual(self._event_count(), before)

    def test_reservation_requires_current_registered_work_item_and_exact_binding(self):
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_WORK_ITEM"):
            ledger.reserve_practical_native_intent(self.db, binding(work_item_id="missing"))
        # The protected backend persists its single database-UTC timestamp in
        # this exact SQL form.  CM stores those original bytes, not a rewritten
        # client-time equivalent.
        sql_utc = binding(fixed_deadline="2030-01-02 03:04:05.000000")
        self.assertTrue(ledger.reserve_practical_native_intent(self.db, sql_utc)["winner"])
        for bad in (
                binding(operation_id="CM-OP-2", backend_operation_id="backend-operation-2", branch="feature"),
                binding(operation_id="CM-OP-3", backend_operation_id="backend-operation-3", original_row_lock=True),
                binding(operation_id="CM-OP-4", backend_operation_id="backend-operation-4", original_row_lock=0),
                binding(operation_id="CM-OP-5", backend_operation_id="backend-operation-5", original_row_lock=2 ** 63),
                binding(operation_id="CM-OP-6", backend_operation_id="backend-operation-6", selection_digest="A" * 64),
                binding(operation_id="CM-OP-7", backend_operation_id="backend-operation-7", fixed_deadline="2030-01-02 03:04:05+00:00"),
                binding(operation_id="CM-OP-8", backend_operation_id="backend-operation-8", extra="not allowed")):
            with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_BINDING"):
                ledger.reserve_practical_native_intent(self.db, bad)

    def test_two_connections_get_exactly_one_dispatch_winner(self):
        start = threading.Barrier(2)
        results, failures = [], []

        def reserve_on():
            db = ledger.connect(self.path)
            try:
                start.wait()
                results.append(ledger.reserve_practical_native_intent(db, binding()))
            except Exception as exc:  # assertion below emits the original failure
                failures.append(exc)
            finally:
                db.close()

        first = threading.Thread(target=reserve_on)
        second = threading.Thread(target=reserve_on)
        first.start(); second.start(); first.join(); second.join()
        self.assertEqual(failures, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(sum(result["winner"] for result in results), 1)
        winners = [result for result in results if result["winner"]]
        losers = [result for result in results if not result["winner"]]
        self.assertEqual(len(winners), len(losers), 1)
        self.assertIsNotNone(winners[0]["reservation"])
        self.assertIsNone(losers[0]["reservation"])
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM events WHERE kind='PRACTICAL_NATIVE_INTENT'").fetchone()[0], 1)

    def test_reuse_with_wrong_task_or_original_binding_refuses(self):
        winner = ledger.reserve_practical_native_intent(self.db, binding())
        self.assertTrue(winner["winner"])
        for changed in (
                binding(work_item_id="other"),
                binding(original_row_lock=-8),
                binding(grant_id="grant-2"),
                binding(backend_operation_id="backend-operation-2")):
            with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_(BINDING|WORK_ITEM)"):
                ledger.reserve_practical_native_intent(self.db, changed)

    def test_only_registered_reader_can_seal_fresh_exact_applied_readback(self):
        winner = ledger.reserve_practical_native_intent(self.db, binding())
        before = self._event_count()
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_READER"):
            ledger.complete_practical_native_readback(self.db, binding(), object(), winner["reservation"])
        self.assertEqual(self._event_count(), before)

        reader = Readback(dict(binding(), observed_state="WORKING_SET_APPLIED"))
        registration = self._register(reader)
        completed = ledger.complete_practical_native_readback(
            self.db, binding(), registration, winner["reservation"])
        self.assertTrue(completed["inserted"])
        self.assertEqual(completed["kind"], "PRACTICAL_NATIVE_APPLIED")
        self.assertEqual(reader.calls, 1)
        self.assertEqual(ledger.verify_history(self.db)["projection_replay"], "VERIFIED")

    def test_malformed_or_foreign_result_cannot_create_terminal_event(self):
        winner = ledger.reserve_practical_native_intent(self.db, binding())
        before = self._event_count()
        malformed = self._register(Readback({"observed_state": "WORKING_SET_APPLIED"}))
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_RECEIPT"):
            ledger.complete_practical_native_readback(self.db, binding(), malformed, winner["reservation"])
        self.assertEqual(self._event_count(), before)

        foreign = self._register(Readback(dict(binding(), grant_id="grant-other",
                                               observed_state="WORKING_SET_APPLIED")))
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_RECEIPT"):
            ledger.complete_practical_native_readback(self.db, binding(), foreign, winner["reservation"])
        self.assertEqual(self._event_count(), before)

    def test_missing_or_nonworking_readback_is_durable_unknown_and_idempotent(self):
        winner = ledger.reserve_practical_native_intent(self.db, binding())
        reader = Readback(None)
        registration = self._register(reader)
        first = ledger.complete_practical_native_readback(
            self.db, binding(), registration, winner["reservation"])
        self.assertTrue(first["inserted"])
        self.assertEqual(first["kind"], "PRACTICAL_NATIVE_UNKNOWN")
        count = self._event_count()
        second = ledger.complete_practical_native_readback(
            self.db, binding(), registration, winner["reservation"])
        self.assertFalse(second["inserted"])
        self.assertEqual(second["kind"], "PRACTICAL_NATIVE_UNKNOWN")
        self.assertEqual(self._event_count(), count)

    def test_reopened_store_reconciles_intent_without_replaying_dispatch_token(self):
        winner = ledger.reserve_practical_native_intent(self.db, binding())
        self.assertTrue(winner["winner"])
        self.db.close()
        self.db = ledger.connect(self.path)
        reader = Readback(dict(binding(), observed_state="WORKING_SET_APPLIED"))
        registration = self._register(reader)
        result = ledger.complete_practical_native_readback(self.db, binding(), registration)
        self.assertTrue(result["inserted"])
        self.assertEqual(result["kind"], "PRACTICAL_NATIVE_APPLIED")
        self.assertEqual(reader.calls, 1)

    def test_reopened_unknown_reconciles_once_to_fresh_exact_applied_readback(self):
        winner = ledger.reserve_practical_native_intent(self.db, binding())
        unknown = ledger.mark_practical_native_unknown(self.db, winner["reservation"], "lost response")
        self.assertTrue(unknown["inserted"])
        self.db.close()
        self.db = ledger.connect(self.path)
        reader = Readback(dict(binding(), observed_state="WORKING_SET_APPLIED"))
        registration = self._register(reader)
        applied = ledger.complete_practical_native_readback(self.db, binding(), registration)
        self.assertTrue(applied["inserted"])
        self.assertEqual(applied["kind"], "PRACTICAL_NATIVE_APPLIED")
        count = self._event_count()
        again = ledger.complete_practical_native_readback(self.db, binding(), registration)
        self.assertFalse(again["inserted"])
        self.assertEqual(self._event_count(), count)

    def test_historical_receipt_cannot_authorize_a_new_grant(self):
        first = binding()
        ledger.reserve_practical_native_intent(self.db, first)
        stale_reader = self._register(Readback(dict(first, observed_state="WORKING_SET_APPLIED")))
        second = binding(operation_id="CM-OP-2", backend_operation_id="backend-operation-2",
                         grant_id="grant-2")
        winner = ledger.reserve_practical_native_intent(self.db, second)
        before = self._event_count()
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_RECEIPT"):
            ledger.complete_practical_native_readback(self.db, second, stale_reader, winner["reservation"])
        self.assertEqual(self._event_count(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
