#!/usr/bin/env python3
"""M3: source/task change revokes acceptance; history survives; re-accept works."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import ledger, partition, providers, results, runner  # noqa: E402

MODEL = {"schema_version": 2, "provider": "fake", "model": "m", "encoding": "e",
         "encoding_version": "v", "context_limit": 100000, "output_limit": 10000,
         "counting_method": "test", "endpoint": "e", "purpose": "do the task",
         "max_spend": 0}
WORDS = lambda text: text.split()  # noqa: E731
SOURCE = b"unit one text"
APPROVAL = {"provider": "fake", "model": "m", "endpoint": "e",
            "purpose": "do the task", "max_output_tokens": 10000}


def drive_to_accepted(db, artifacts_dir, work_item, task_digest="task-1"):
    manifest = partition.build_manifest("SRC-1", SOURCE)
    att, digest = runner.prepare(db, artifacts_dir, work_item, task_digest,
                                 {"U000001": "unit one text"}, "do the task",
                                 {"type": "object"}, {}, "spec-1", MODEL, counter=WORDS,
                                 manifest=manifest, source_bytes=SOURCE)
    runner.approve(db, att, "test-ok")
    approval = ledger.issue_approval(db, att, digest, APPROVAL["provider"],
                                     APPROVAL["model"], APPROVAL["endpoint"],
                                     APPROVAL["purpose"], APPROVAL["max_output_tokens"],
                                     {"max_spend": 0})
    rich = results.make_result(SOURCE, manifest, "U000001", task_digest, att, "parsed")
    runner.dispatch_via_adapter(
        db, artifacts_dir, providers.TestOnlyAdapter([("ok", {"U000001": rich})]),
        att, approval)
    runner.accept(db, artifacts_dir, att, task_digest, manifest, SOURCE, APPROVAL)
    return att


class InvalidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="inval-")
        self.db = ledger.connect(Path(self.temp.name) / "ledger.db")
        self.artifacts = str(Path(self.temp.name) / "artifacts")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_revoke_on_change_then_reaccept(self):
        ledger.create_work_item(self.db, "W1", "task-1", "SRC-1")
        first = drive_to_accepted(self.db, self.artifacts, "W1")
        ledger.revoke(self.db, "W1", "source digest changed")
        self.assertIsNone(ledger.accepted_attempt(self.db, "W1"))
        # R1 (F05): a changed task can no longer reuse the same work item;
        # re-driving the approved task after revoke works and keeps history.
        with self.assertRaises(ledger.LedgerError):
            drive_to_accepted(self.db, self.artifacts, "W1", task_digest="task-2")
        second = drive_to_accepted(self.db, self.artifacts, "W1")
        self.assertNotEqual(first, second)
        self.assertEqual(ledger.accepted_attempt(self.db, "W1"), second)
        ids = [h["state"] for h in ledger.history(self.db, "W1")]
        self.assertEqual(ids.count("ACCEPTED"), 2)

    def test_stale_work_cannot_accept_without_revoke(self):
        ledger.create_work_item(self.db, "W2", "task-1", "SRC-1")
        drive_to_accepted(self.db, self.artifacts, "W2")
        with self.assertRaises(ledger.LedgerError):
            drive_to_accepted(self.db, self.artifacts, "W2")

    def test_events_are_append_only(self):
        ledger.create_work_item(self.db, "W3", "task-1", "SRC-1")
        before = self.db.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
        drive_to_accepted(self.db, self.artifacts, "W3")
        after = self.db.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
        self.assertGreater(after, before)
        seqs = [r["seq"] for r in
                self.db.execute("SELECT seq FROM events ORDER BY seq").fetchall()]
        self.assertEqual(seqs, sorted(seqs))
        self.assertEqual(len(set(seqs)), len(seqs))


if __name__ == "__main__":
    unittest.main(verbosity=2)
