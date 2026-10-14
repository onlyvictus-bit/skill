#!/usr/bin/env python3
"""Offline CM/PracticalBackend integration tests for the isolated fence."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(SOURCE / "claude-mon" / "scripts"))

from complete_read_v2 import ledger  # noqa: E402
from hybrid_bridge import practical_backend, practical_consumer  # noqa: E402


SELECTION = {
    "scratch_root": "C:/scratch/r5-fence", "dolt_executable": "C:/scratch/r5-fence/dolt.exe",
    "dolt_sha256": "a" * 64, "host": "127.0.0.1", "port": 3306,
    "database": "beads_scratch", "main_branch": "main",
    "incarnation": "scratch-incarnation-20261013",
    "native_node_id": "practical-scratch-node-1",
    "candidate_route": "APPROVED_SCRATCH_PRACTICAL_CONTRACT",
}


def request(**changes):
    value = {
        "schema_version": 1, "work_item_id": "cm-work-17", "operation_id": "op-title-1",
        "action": "guarded_title", "task_id": "mip-42", "actor": "alice",
        "expected_status": "open", "grant_id": "grant-old-7", "target_actor": "alice",
        "new_grant_id": "grant-new-8", "expected_row_lock": -731,
        "fixed_deadline_utc": "2030-01-02 03:04:05.123456",
        "new_deadline_utc": "2030-01-02 04:04:05.123456", "title": "fenced title",
    }
    value.update(changes)
    payload = {key: item for key, item in value.items() if key != "command_digest"}
    value["command_digest"] = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return value


def offline_backend():
    """A TEST_ONLY seam on the real concrete class; no process can start."""
    backend = practical_backend.PracticalBackend(
        SELECTION, runner=lambda *_args: (_ for _ in ()).throw(AssertionError("no CLI")))
    backend.dispatched = 0
    backend.reads = 0
    backend.fail_dispatch = None
    backend.receipt = None
    backend.observe = lambda: {
        "database_name": backend.selection.database, "branch_name": backend.selection.main_branch,
        "observed_utc": "2030-01-02 03:04:00.000000",
        "requested_incarnation": backend.selection.incarnation,
        "selection_digest": backend.selection.digest,
    }
    backend.read_task = lambda task_id: {
        "id": task_id, "title": "before", "status": "open", "assignee": "alice", "row_lock": -731,
    }
    backend.read_grant = lambda grant_id: {
        "store_incarnation": backend.selection.incarnation, "grant_id": grant_id,
        "native_task_id": "mip-42", "actor": "alice", "status": "open",
        "fixed_deadline_utc": "2030-01-02 03:04:05.123456", "issue_revision": -731, "tombstoned": 0,
    }
    def dispatch(_value):
        backend.dispatched += 1
        if backend.fail_dispatch is not None:
            raise backend.fail_dispatch
        return {"ignored": "completion must read back separately"}
    def read_operation(_operation_id, _command_digest):
        backend.reads += 1
        return backend.receipt
    backend.guarded_title = dispatch
    backend.read_operation = read_operation
    return backend


def backend_receipt(backend, req, **changes):
    value = {
        "schema_version": 1, "status": "WORKING_SET_APPLIED",
        "evidence_class": "NATIVE_OBSERVED_UNQUALIFIED", "native_write_qualified": False,
        "head_committed": False, "backend_operation_id": req["operation_id"],
        "operation_id": req["operation_id"], "command_digest": req["command_digest"],
        "work_item_id": req["work_item_id"], "selection_digest": backend.selection.digest,
        "store_incarnation": backend.selection.incarnation, "database": backend.selection.database,
        "branch": backend.selection.main_branch, "native_task_id": req["task_id"],
        "actor": req["actor"], "grant_id": req["grant_id"],
        "original_row_lock": req["expected_row_lock"],
        "fixed_deadline_utc": req["fixed_deadline_utc"], "resulting_row_lock": 812,
        "authorization_time_utc": "2030-01-02 03:04:00.000000",
    }
    value.update(changes)
    return value


class PracticalConsumerTests(unittest.TestCase):
    def setUp(self):
        # Keep unique local evidence after a run; this test never deletes it.
        self.temp = Path(tempfile.mkdtemp(prefix="practical-consumer-"))
        self.db = ledger.connect(self.temp / "cm.sqlite")
        ledger.create_work_item(self.db, "cm-work-17", "task", "source")
        ledger.coordination_put(self.db, "cm-work-17", {"registered": True})
        self.backend = offline_backend()

    def tearDown(self):
        self.db.close()

    def test_stopped_v1_consumer_constructor_stays_stopped(self):
        # The v1 consumer is deliberately stopped pending the real lease-v2
        # replacement (practical-resume-20261014.md:30): construction refuses
        # before any reader registration, so no injected predecessor runner
        # can register a fabricated native proof path. The gate precedes the
        # concrete-type check, which the refusal below documents.
        with self.assertRaisesRegex(practical_consumer.PracticalConsumerError,
                                    "E_PRACTICAL_REVISION_STOPPED"):
            practical_consumer.PracticalNativeConsumer(self.db, self.backend)
        with self.assertRaisesRegex(practical_consumer.PracticalConsumerError,
                                    "E_PRACTICAL_REVISION_STOPPED"):
            practical_consumer.PracticalNativeConsumer(self.db, object())

    @unittest.skip("v1 consumer stopped (E_PRACTICAL_REVISION_STOPPED); winner/readback intent covered in-flight by test_practical_lease_backend.py::test_exact_receipt_one_dispatch_is_not_native_qualification (uncommitted)")
    def test_dispatch_uses_winner_reservation_then_real_operation_readback(self):
        req = request()
        self.backend.receipt = backend_receipt(self.backend, req)
        result = self.consumer.dispatch_guarded_title(req)
        self.assertEqual(result["kind"], "PRACTICAL_NATIVE_APPLIED")
        self.assertEqual(self.backend.dispatched, 1)
        self.assertEqual(self.backend.reads, 1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events WHERE kind='PRACTICAL_NATIVE_APPLIED'").fetchone()[0], 1)

    @unittest.skip("v1 consumer stopped (E_PRACTICAL_REVISION_STOPPED); readback-only recovery intent covered in-flight by test_practical_lease_backend.py::test_new_backend_and_reused_capability_cannot_repeat_mutation and test_readback_has_no_mutation_and_missing_is_unknown (uncommitted)")
    def test_loser_and_recovery_do_readback_only_never_replay_mutation(self):
        req = request()
        self.backend.receipt = backend_receipt(self.backend, req)
        first = self.consumer.dispatch_guarded_title(req)
        second = self.consumer.dispatch_guarded_title(req)
        recovered = self.consumer.reconcile_guarded_title(req)
        self.assertTrue(first["inserted"])
        self.assertFalse(second["inserted"])
        self.assertFalse(recovered["inserted"])
        self.assertEqual(self.backend.dispatched, 1)
        self.assertEqual(self.backend.reads, 1)

    @unittest.skip("v1 consumer stopped (E_PRACTICAL_REVISION_STOPPED); unknown-on-error intent covered in-flight by test_practical_lease_backend.py::test_foreign_receipt_becomes_unknown_never_applied (uncommitted)")
    def test_backend_error_marks_unknown_and_never_retries_dispatch(self):
        req = request()
        self.backend.fail_dispatch = RuntimeError("lost response")
        result = self.consumer.dispatch_guarded_title(req)
        self.assertEqual(result["kind"], "PRACTICAL_NATIVE_UNKNOWN")
        self.assertEqual(self.backend.dispatched, 1)
        again = self.consumer.dispatch_guarded_title(req)
        self.assertFalse(again["inserted"])
        self.assertEqual(self.backend.dispatched, 1)

    @unittest.skip("v1 consumer stopped (E_PRACTICAL_REVISION_STOPPED); no committed v2 consumer exists yet, so the stale-grant prerequisite has no committable target; prerequisite checks move to the lease-bound execute path (uncommitted practical_lease_backend.py), P3 decision pending")
    def test_current_backend_prerequisite_refuses_stale_grant_before_dispatch(self):
        req = request()
        stale = self.backend.read_grant
        self.backend.read_grant = lambda grant: dict(stale(grant), issue_revision=999)
        with self.assertRaisesRegex(practical_consumer.PracticalConsumerError, "E_PRACTICAL_CURRENT_GRANT"):
            self.consumer.dispatch_guarded_title(req)
        self.assertEqual(self.backend.dispatched, 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events WHERE kind='PRACTICAL_NATIVE_INTENT'").fetchone()[0], 0)

    @unittest.skip("v1 consumer stopped (E_PRACTICAL_REVISION_STOPPED); no committed v2 consumer exists yet; changed-grant refusal moves to the lease-bound execute path (uncommitted practical_lease_backend.py), P3 decision pending")
    def test_historical_applied_event_cannot_authorize_later_changed_grant(self):
        req = request()
        self.backend.receipt = backend_receipt(self.backend, req)
        self.consumer.dispatch_guarded_title(req)
        reads_before = self.backend.reads
        dispatches_before = self.backend.dispatched
        current = self.backend.read_grant
        self.backend.read_grant = lambda grant: dict(current(grant), fixed_deadline_utc="2030-01-02 03:03:59.000000")
        with self.assertRaisesRegex(practical_consumer.PracticalConsumerError, "E_PRACTICAL_CURRENT_GRANT"):
            self.consumer.dispatch_guarded_title(req)
        self.assertEqual(self.backend.dispatched, dispatches_before)
        self.assertEqual(self.backend.reads, reads_before)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events WHERE kind='PRACTICAL_NATIVE_APPLIED'").fetchone()[0], 1)

    @unittest.skip("v1 consumer stopped (E_PRACTICAL_REVISION_STOPPED); compact-readback refusal intent covered in-flight by test_practical_lease_backend.py::test_foreign_receipt_becomes_unknown_never_applied (uncommitted)")
    def test_foreign_or_compact_readback_cannot_seal_success(self):
        req = request()
        self.backend.receipt = {"operation_id": req["operation_id"],
                                "command_digest": req["command_digest"],
                                "state": "WORKING_SET_APPLIED"}
        with self.assertRaisesRegex(practical_consumer.PracticalConsumerError, "E_PRACTICAL_READBACK"):
            self.consumer.dispatch_guarded_title(req)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events WHERE kind='PRACTICAL_NATIVE_APPLIED'").fetchone()[0], 0)

    @unittest.skip("v1 consumer stopped (E_PRACTICAL_REVISION_STOPPED precedes the concrete-type check, locked by the gate test above); injection rejection covered in-flight by test_practical_lease_backend.py::test_public_constructor_rejects_injected_runner (uncommitted)")
    def test_non_concrete_backend_and_direct_success_payload_fail_closed(self):
        with self.assertRaisesRegex(practical_consumer.PracticalConsumerError, "E_PRACTICAL_BACKEND"):
            practical_consumer.PracticalNativeConsumer(self.db, object())
        with self.assertRaises(TypeError):
            self.consumer.dispatch_guarded_title(request(), {"success": True})


if __name__ == "__main__":
    unittest.main(verbosity=2)
