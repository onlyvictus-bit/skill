#!/usr/bin/env python3
"""M5: protected canonical event history is independently verifiable."""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import ledger  # noqa: E402


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r3-history-")
        self.path = Path(self.temp.name) / "ledger.db"
        self.db = ledger.connect(self.path)
        ledger.create_work_item(self.db, "W1", "task-1", "SRC-1")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_ordinary_event_update_delete_and_unsealed_insert_are_refused(self):
        with self.assertRaises(sqlite3.DatabaseError):
            self.db.execute("UPDATE events SET detail='rewritten' WHERE seq=1")
        with self.assertRaises(sqlite3.DatabaseError):
            self.db.execute("DELETE FROM events WHERE seq=1")
        with self.assertRaises(sqlite3.DatabaseError):
            self.db.execute("INSERT INTO events(at,kind,work_item_id,detail) VALUES(?,?,?,?)",
                            ("t", "FORGED", "W1", "x"))

    def test_checkpoint_is_external_and_detects_erased_history(self):
        ledger.begin_attempt(self.db, "W1")
        checkpoint = ledger.make_checkpoint(self.db, owner="independent-verifier")
        no_checkpoint = ledger.verify_history(self.db)
        self.assertEqual(no_checkpoint["internal_chain"], "VERIFIED")
        self.assertEqual(no_checkpoint["anchored_completeness"], "UNVERIFIED")
        self.assertEqual(ledger.verify_history(self.db, checkpoint)["anchored_completeness"], "VERIFIED")
        # A filesystem owner can remove normal SQL guards.  The retained
        # checkpoint must still disclose history truncation; this is not a
        # claim that local SQLite permissions defeat that owner.
        self.db.execute("DROP TRIGGER events_no_update")
        self.db.execute("DROP TRIGGER events_no_delete")
        self.db.execute("DROP TRIGGER events_require_canonical")
        self.db.execute("DELETE FROM events WHERE seq=(SELECT MAX(seq) FROM events)")
        checked = ledger.verify_history(self.db, checkpoint)
        self.assertEqual(checked["internal_chain"], "VERIFIED")
        self.assertEqual(checked["anchored_completeness"], "FAILED")

    def test_replay_matches_current_projection_and_revoke_is_a_new_event(self):
        attempt = ledger.begin_attempt(self.db, "W1")
        for state in ("PREPARED", "AWAITING_APPROVAL", "DISPATCHING",
                      "RESPONSE_SAVED", "VALIDATED", "ACCEPTED"):
            ledger.transition(self.db, attempt, state)
        before = [r["seq"] for r in self.db.execute("SELECT seq FROM events").fetchall()]
        ledger.revoke(self.db, "W1", "new basis")
        after = self.db.execute("SELECT kind, detail FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        self.assertGreater(after["seq"] if "seq" in after.keys() else len(before), 0)
        self.assertEqual(after["kind"], "ACCEPTED_REVOKED")
        checked = ledger.verify_history(self.db)
        self.assertEqual(checked["projection_replay"], "VERIFIED")

    def test_v3_migration_preserves_legacy_unverified_provenance(self):
        old_path = Path(self.temp.name) / "legacy-v3.db"
        old = sqlite3.connect(str(old_path))
        old.executescript(
            "CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);"
            "INSERT INTO meta VALUES('schema_version','3');"
            "CREATE TABLE work_items(id TEXT PRIMARY KEY, task_digest TEXT NOT NULL,"
            " source_id TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);"
            "CREATE TABLE attempts(id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL,"
            " attempt_no INTEGER NOT NULL, state TEXT NOT NULL, request_digest TEXT,"
            " response_digest TEXT, approval_ref TEXT, approval_id TEXT, error TEXT, updated_at TEXT NOT NULL,"
            " UNIQUE(work_item_id, attempt_no));"
            "CREATE TABLE accepted(work_item_id TEXT PRIMARY KEY, attempt_id TEXT NOT NULL,"
            " revoked INTEGER NOT NULL, revoke_reason TEXT, accepted_at TEXT NOT NULL);"
            "CREATE TABLE approvals(id TEXT PRIMARY KEY, attempt_id TEXT NOT NULL, request_digest TEXT NOT NULL,"
            " provider TEXT NOT NULL, model TEXT NOT NULL, endpoint TEXT NOT NULL, purpose TEXT NOT NULL,"
            " max_output_tokens INTEGER NOT NULL, limits_json TEXT NOT NULL, consumed INTEGER NOT NULL, created_at TEXT NOT NULL);"
            "CREATE TABLE events(seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, kind TEXT NOT NULL,"
            " work_item_id TEXT, detail TEXT NOT NULL);"
            "INSERT INTO work_items VALUES('W9','task-9','SRC-9','PENDING','t');"
            "INSERT INTO events(at,kind,work_item_id,detail) VALUES('t','WORK_ITEM_CREATED','W9','task-9');"
        )
        old.commit(); old.close()
        migrated = ledger.connect(old_path)
        try:
            self.assertEqual(migrated.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()["value"], "4")
            row = migrated.execute("SELECT actor, identity_json FROM events WHERE seq=1").fetchone()
            self.assertEqual(row["actor"], "LEGACY_UNVERIFIED")
            self.assertIn("legacy_unverified", row["identity_json"])
            self.assertEqual(ledger.verify_history(migrated)["projection_replay"], "UNVERIFIED")
        finally:
            migrated.close()

    def test_security_bearing_projection_change_cannot_be_laundered(self):
        self.db.execute("UPDATE work_items SET task_digest='foreign' WHERE id='W1'")
        self.assertEqual(ledger.verify_history(self.db)["projection_replay"], "FAILED")
        with self.assertRaises(ledger.LedgerError):
            ledger.event(self.db, "NOOP", "W1", "cannot seal forged projection")

    def test_caller_transaction_cannot_launder_removed_coordination_or_task(self):
        ledger.coordination_put(self.db, "W1", {"coordination_required": True})
        checkpoint = ledger.make_checkpoint(self.db, "retained-before-attack")
        for statement in ("DELETE FROM meta WHERE key='coordination:W1'",
                          "UPDATE work_items SET task_digest='FORGED-TASK' WHERE id='W1'"):
            count = self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            self.db.execute("BEGIN")
            try:
                self.db.execute(statement)
                with self.assertRaises(ledger.LedgerError):
                    ledger.event(self.db, "NOOP", "W1", "must not legitimize altered state")
                self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0], count)
            finally:
                self.db.execute("ROLLBACK")
            checked = ledger.verify_history(self.db, checkpoint)
            self.assertEqual(checked["projection_replay"], "VERIFIED")
            self.assertEqual(checked["anchored_completeness"], "VERIFIED")

    def test_semantic_replay_rejects_changed_projection_under_generic_event(self):
        # Even an internal/private append must not turn a canonical hash over
        # an arbitrary snapshot into proof that the typed state change was legal.
        self.db.execute("BEGIN")
        self.db.execute("UPDATE work_items SET task_digest='FORGED-TASK' WHERE id='W1'")
        ledger._append(self.db, "NOOP", "W1", "owner attempted snapshot laundering")
        self.db.execute("COMMIT")
        checked = ledger.verify_history(self.db)
        self.assertEqual(checked["internal_chain"], "VERIFIED")
        self.assertEqual(checked["projection_replay"], "FAILED")
        with self.assertRaises(ledger.LedgerError):
            ledger.begin_attempt(self.db, "W1")

    def test_invalid_checkpoints_never_verify(self):
        for checkpoint in ({"schema": "cm-history-checkpoint-v1"},
                           {"schema": "cm-history-checkpoint-v1", "seq": -1, "event_hash": ""},
                           {"schema": "cm-history-checkpoint-v1", "seq": True, "event_hash": ""}):
            self.assertEqual(ledger.verify_history(self.db, checkpoint)["anchored_completeness"], "FAILED")

    def test_checkpoint_prefix_does_not_claim_new_tail_independently_anchored(self):
        checkpoint = ledger.make_checkpoint(self.db,"retained-prefix")
        ledger.begin_attempt(self.db,"W1")
        checked = ledger.verify_history(self.db,checkpoint)
        self.assertEqual(checked["anchored_completeness"],"UNVERIFIED")
        self.assertEqual(checked["anchored_through_seq"],checkpoint["seq"])
        self.assertFalse(checked["current_head_anchored"])

    def test_legacy_reconcile_keeps_spent_awaiting_attempt_uncertain(self):
        attempt=ledger.begin_attempt(self.db,"W1")
        ledger.transition(self.db,attempt,"PREPARED",request_digest="a"*64)
        ledger.transition(self.db,attempt,"AWAITING_APPROVAL",approval_ref="fixture-approval")
        approval=ledger.issue_approval(self.db,attempt,"a"*64,"fixture","fixture-1","test-only","recovery",10,{"max_spend":0})
        ledger.consume_approval(self.db,approval,attempt,"a"*64)
        ledger.reconcile_on_open(self.db)
        self.assertEqual(self.db.execute("SELECT state FROM attempts WHERE id=?",(attempt,)).fetchone()[0],"DELIVERY_UNKNOWN")
        self.assertEqual(ledger.verify_history(self.db)["projection_replay"],"VERIFIED")

    def test_projection_and_event_rollback_together(self):
        count = self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        self.db.execute("CREATE TRIGGER reject_new_events BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT,'test interruption'); END")
        with self.assertRaises(sqlite3.DatabaseError):
            ledger.create_work_item(self.db, "W2", "new", "new-source")
        self.assertIsNone(self.db.execute("SELECT id FROM work_items WHERE id='W2'").fetchone())
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0], count)


if __name__ == "__main__":
    unittest.main(verbosity=2)
