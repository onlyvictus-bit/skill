#!/usr/bin/env python3
"""Offline CM dispatch-consumption tests; retained sqlite evidence only."""
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import ledger  # noqa: E402

RETAINED_TEMP = (Path(__file__).resolve().parents[3] / "build-validation" /
                 "retained-temp")


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


def v2_binding(**changes):
    value = binding(
        fixed_deadline="2030-01-02 03:04:05.000000",
        lease_holder="worker-1",
        lease_granted_node="node-1",
        lease_granted_at_utc="2030-01-02 03:04:03.000000",
        lease_expires_at_utc="2030-01-02 03:04:05.000000",
        lease_heartbeat_at_utc="2030-01-02 03:04:04.000000",
    )
    value.update(changes)
    return value


class PracticalDispatchTests(unittest.TestCase):
    def setUp(self):
        # Keep each local sqlite receipt after tests; no TemporaryDirectory cleanup.
        self.temp = Path(tempfile.mkdtemp(
            prefix="practical-dispatch-", dir=RETAINED_TEMP))
        self.path = self.temp / "cm-ledger.sqlite"
        self.db = ledger.connect(self.path)
        ledger.create_work_item(self.db, "W", "task-digest", "source-id")
        ledger.coordination_put(self.db, "W", {"registered": True})

    def tearDown(self):
        self.db.close()

    def _events(self):
        return [row[0] for row in self.db.execute(
            "SELECT kind FROM events WHERE kind LIKE 'PRACTICAL_NATIVE_%' ORDER BY seq")]

    def test_dispatch_claim_is_durable_once_before_unknown(self):
        winner = ledger.reserve_practical_native_intent(self.db, v2_binding())
        first = ledger.consume_practical_native_dispatch(
            self.db, v2_binding(), winner["reservation"])
        self.assertEqual(first, {
            "dispatch": True,
            "kind": "PRACTICAL_NATIVE_DISPATCHED",
            "binding": v2_binding(),
        })
        again = ledger.consume_practical_native_dispatch(
            self.db, v2_binding(), winner["reservation"])
        self.assertFalse(again["dispatch"])
        self.assertEqual(again["kind"], "PRACTICAL_NATIVE_DISPATCHED")
        unknown = ledger.mark_practical_native_unknown(
            self.db, winner["reservation"], "subprocess result unavailable")
        self.assertTrue(unknown["inserted"])
        class Reader:
            def read_practical_native_operation(self, observed):
                return dict(observed, observed_state="WORKING_SET_APPLIED")

        registered = ledger._register_practical_native_readback_consumer(self.db, Reader())
        applied = ledger.complete_practical_native_readback(
            self.db, v2_binding(), registered, winner["reservation"])
        self.assertTrue(applied["inserted"])
        self.assertEqual(applied["kind"], "PRACTICAL_NATIVE_APPLIED")
        self.assertEqual(self._events(), [
            "PRACTICAL_NATIVE_INTENT",
            "PRACTICAL_NATIVE_DISPATCHED",
            "PRACTICAL_NATIVE_UNKNOWN",
            "PRACTICAL_NATIVE_APPLIED",
        ])
        self.assertEqual(ledger.verify_history(self.db)["projection_replay"], "VERIFIED")

    def test_legacy_intent_to_applied_remains_valid_but_cannot_later_dispatch(self):
        winner = ledger.reserve_practical_native_intent(self.db, binding())

        class Reader:
            def read_practical_native_operation(self, observed):
                return dict(observed, observed_state="WORKING_SET_APPLIED")

        registered = ledger._register_practical_native_readback_consumer(self.db, Reader())
        result = ledger.complete_practical_native_readback(
            self.db, binding(), registered, winner["reservation"])
        self.assertEqual(result["kind"], "PRACTICAL_NATIVE_APPLIED")
        consumed = ledger.consume_practical_native_dispatch(
            self.db, binding(), winner["reservation"])
        self.assertFalse(consumed["dispatch"])
        self.assertEqual(consumed["kind"], "PRACTICAL_NATIVE_APPLIED")
        self.assertEqual(self._events(), [
            "PRACTICAL_NATIVE_INTENT", "PRACTICAL_NATIVE_APPLIED"])

    def test_v2_lease_binding_is_all_or_none_and_self_consistent(self):
        winner = ledger.reserve_practical_native_intent(self.db, v2_binding())
        self.assertTrue(winner["winner"])
        for bad in (
                binding(lease_holder="worker-1"),
                v2_binding(actor="another-worker"),
                v2_binding(fixed_deadline="2030-01-02 03:04:06.000000"),
                v2_binding(lease_heartbeat_at_utc="2030-01-02 03:04:05.000000"),
                v2_binding(lease_granted_at_utc="2030-01-02 03:04:03.000001"),
                v2_binding(lease_granted_at_utc="2030-01-02T03:04:03Z"),
                v2_binding(original_row_lock=True)):
            with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_BINDING"):
                ledger.reserve_practical_native_intent(self.db, bad)

    def test_v2_receipt_does_not_treat_true_as_numeric_row_lock(self):
        winner = ledger.reserve_practical_native_intent(self.db, v2_binding())

        class Reader:
            def read_practical_native_operation(self, observed):
                return dict(observed, original_row_lock=True,
                            observed_state="WORKING_SET_APPLIED")

        registered = ledger._register_practical_native_readback_consumer(self.db, Reader())
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_BINDING"):
            ledger.complete_practical_native_readback(
                self.db, v2_binding(), registered, winner["reservation"])
        self.assertEqual(self._events(), ["PRACTICAL_NATIVE_INTENT"])

    def test_invalid_capability_reopened_store_and_rebound_binding_cannot_consume(self):
        winner = ledger.reserve_practical_native_intent(self.db, v2_binding())
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_OWNER"):
            ledger.consume_practical_native_dispatch(self.db, v2_binding(), object())
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_OWNER"):
            ledger.consume_practical_native_dispatch(
                self.db, v2_binding(grant_id="other-grant"), winner["reservation"])
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_OWNER"):
            ledger.consume_practical_native_dispatch(
                self.db, v2_binding(selection_digest="c" * 64), winner["reservation"])
        self.db.close()
        self.db = ledger.connect(self.path)
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_OWNER"):
            ledger.consume_practical_native_dispatch(self.db, v2_binding(), winner["reservation"])
        self.assertEqual(self._events(), ["PRACTICAL_NATIVE_INTENT"])

    def test_reservation_refuses_a_stored_but_unregistered_policy(self):
        path = self.temp / "unregistered-policy.sqlite"
        db = ledger.connect(path)
        try:
            ledger.create_work_item(db, "W", "task-digest", "source-id")
            ledger.coordination_put(db, "W", {"registered": False})
            with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_WORK_ITEM"):
                ledger.reserve_practical_native_intent(db, v2_binding())
        finally:
            db.close()

    def test_reservation_and_consumption_race_has_one_durable_dispatch(self):
        start = threading.Barrier(2)
        results, failures = [], []

        def reserve_and_consume():
            db = ledger.connect(self.path)
            try:
                start.wait()
                reserved = ledger.reserve_practical_native_intent(db, v2_binding())
                if reserved["winner"]:
                    results.append(ledger.consume_practical_native_dispatch(
                        db, v2_binding(), reserved["reservation"]))
                else:
                    results.append({"dispatch": False, "kind": reserved["kind"]})
            except Exception as exc:
                failures.append(exc)
            finally:
                db.close()

        one = threading.Thread(target=reserve_and_consume)
        two = threading.Thread(target=reserve_and_consume)
        one.start(); two.start(); one.join(); two.join()
        self.assertEqual(failures, [])
        self.assertEqual(sum(result["dispatch"] for result in results), 1)
        self.assertEqual(self._events(), [
            "PRACTICAL_NATIVE_INTENT", "PRACTICAL_NATIVE_DISPATCHED"])

    def test_generic_event_api_refuses_dispatched_namespace(self):
        with self.assertRaisesRegex(ledger.LedgerError, "E_PRACTICAL_EVENT"):
            ledger.event(self.db, "PRACTICAL_NATIVE_DISPATCHED", "W", "forged")


if __name__ == "__main__":
    unittest.main(verbosity=2)
