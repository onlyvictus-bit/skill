#!/usr/bin/env python3
"""M3: ledger transitions, uniqueness, revocation, reconcile."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import ledger  # noqa: E402


def fresh_db(temp):
    path = Path(temp) / "ledger.db"
    return ledger.connect(path)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ledger-")
        self.db = fresh_db(self.temp.name)
        ledger.create_work_item(self.db, "W1", "task-1", "SRC-1")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_full_forward_path(self):
        att = ledger.begin_attempt(self.db, "W1")
        for state in ("PREPARED", "AWAITING_APPROVAL", "DISPATCHING",
                      "RESPONSE_SAVED", "VALIDATED", "ACCEPTED"):
            ledger.transition(self.db, att, state)
        self.assertEqual(ledger.accepted_attempt(self.db, "W1"), att)

    def test_illegal_jump_rejected(self):
        att = ledger.begin_attempt(self.db, "W1")
        with self.assertRaises(ledger.LedgerError):
            ledger.transition(self.db, att, "ACCEPTED")

    def test_terminal_state_frozen(self):
        att = ledger.begin_attempt(self.db, "W1")
        ledger.transition(self.db, att, "CANCELLED")
        with self.assertRaises(ledger.LedgerError):
            ledger.transition(self.db, att, "PREPARED")

    def test_double_accept_blocked(self):
        first = ledger.begin_attempt(self.db, "W1")
        for state in ("PREPARED", "AWAITING_APPROVAL", "DISPATCHING",
                      "RESPONSE_SAVED", "VALIDATED", "ACCEPTED"):
            ledger.transition(self.db, first, state)
        second = ledger.begin_attempt(self.db, "W1")
        for state in ("PREPARED", "AWAITING_APPROVAL", "DISPATCHING",
                      "RESPONSE_SAVED", "VALIDATED"):
            ledger.transition(self.db, second, state)
        with self.assertRaises(ledger.LedgerError):
            ledger.transition(self.db, second, "ACCEPTED")

    def test_revoke_keeps_history(self):
        att = ledger.begin_attempt(self.db, "W1")
        for state in ("PREPARED", "AWAITING_APPROVAL", "DISPATCHING",
                      "RESPONSE_SAVED", "VALIDATED", "ACCEPTED"):
            ledger.transition(self.db, att, state)
        ledger.revoke(self.db, "W1", "source changed")
        self.assertIsNone(ledger.accepted_attempt(self.db, "W1"))
        states = [h["state"] for h in ledger.history(self.db, "W1")]
        self.assertIn("ACCEPTED", states)
        pending = ledger.pending_work(self.db)
        self.assertIn("W1", pending)

    def test_revoke_needs_reason(self):
        with self.assertRaises(ledger.LedgerError):
            ledger.revoke(self.db, "W1", "  ")

    def test_reconcile_dispatching_becomes_unknown(self):
        att = ledger.begin_attempt(self.db, "W1")
        ledger.transition(self.db, att, "PREPARED")
        ledger.transition(self.db, att, "AWAITING_APPROVAL")
        ledger.transition(self.db, att, "DISPATCHING")
        moved = ledger.reconcile_on_open(self.db)
        self.assertEqual(moved, [(att, "DISPATCHING", "DELIVERY_UNKNOWN")])
        row = self.db.execute("SELECT state FROM attempts WHERE id=?", (att,)).fetchone()
        self.assertEqual(row["state"], "DELIVERY_UNKNOWN")

    def test_reconcile_undispatched_requeues(self):
        att = ledger.begin_attempt(self.db, "W1")
        ledger.transition(self.db, att, "PREPARED")
        moved = ledger.reconcile_on_open(self.db)
        self.assertEqual(moved, [(att, "PREPARED", "QUEUED")])

    def test_duplicate_work_item_rejected(self):
        with self.assertRaises(ledger.LedgerError):
            ledger.create_work_item(self.db, "W1", "task-1", "SRC-1")

    def test_migrate_v2_through_v4_preserves_data(self):
        import sqlite3
        path = Path(self.temp.name) / "v2.db"
        old = sqlite3.connect(str(path))
        old.executescript(
            "CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);"
            "INSERT INTO meta VALUES('schema_version','2');"
            "CREATE TABLE work_items(id TEXT PRIMARY KEY, task_digest TEXT NOT NULL,"
            " source_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING',"
            " created_at TEXT NOT NULL);"
            "CREATE TABLE attempts(id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL,"
            " attempt_no INTEGER NOT NULL, state TEXT NOT NULL, request_digest TEXT,"
            " response_digest TEXT, approval_ref TEXT, error TEXT, updated_at TEXT,"
            " UNIQUE(work_item_id, attempt_no));"
            "CREATE TABLE accepted(work_item_id TEXT PRIMARY KEY, attempt_id TEXT NOT NULL,"
            " revoked INTEGER NOT NULL DEFAULT 0, revoke_reason TEXT, accepted_at TEXT NOT NULL);"
            "CREATE TABLE events(seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,"
            " kind TEXT NOT NULL, work_item_id TEXT, detail TEXT NOT NULL);"
            "INSERT INTO work_items VALUES('W9','task-9','SRC-9','PENDING','t');")
        old.commit()
        old.close()
        db = ledger.connect(path)
        try:
            version = db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
            # R3's scratch migration deliberately proceeds through schema 3
            # into schema 4, which adds the protected canonical event chain.
            self.assertEqual(version["value"], "4")
            self.assertIn("W9", ledger.pending_work(db))
            attempt = ledger.begin_attempt(db, "W9")
            approval = ledger.issue_approval(db, attempt, "d" * 64, "p", "m", "e",
                                             "why", 10, {})
            self.assertTrue(approval.startswith("APR-"))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
