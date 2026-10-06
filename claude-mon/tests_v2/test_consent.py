#!/usr/bin/env python3
"""M4b: per-call consent is the only supported policy."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import ledger, runner  # noqa: E402

MODEL = {"schema_version": 2, "provider": "fake", "model": "m", "encoding": "e",
         "encoding_version": "v", "context_limit": 100000, "output_limit": 10000,
         "counting_method": "test"}
WORDS = lambda text: text.split()  # noqa: E731


class ConsentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="consent-")
        self.db = ledger.connect(Path(self.temp.name) / "ledger.db")
        self.artifacts = str(Path(self.temp.name) / "artifacts")
        ledger.create_work_item(self.db, "W1", "t", "S")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def begin(self):
        att, _ = runner.prepare(self.db, self.artifacts, "W1", "t", {"U1": "unit one"},
                                "do the task", {"type": "object"}, {}, "spec-1",
                                MODEL, counter=WORDS)
        return att

    def test_dispatch_without_approval_blocked(self):
        att = self.begin()
        with self.assertRaises(ledger.LedgerError):
            runner.dispatch(self.db, self.artifacts,
                            runner.FakeProvider([("ok", b"r")]), att)

    def test_empty_approval_ref_blocked(self):
        att = self.begin()
        with self.assertRaises(ledger.LedgerError):
            runner.approve(self.db, att, "   ")

    def test_approval_ref_recorded(self):
        att = self.begin()
        runner.approve(self.db, att, "user-said-go-M1")
        row = self.db.execute("SELECT approval_ref FROM attempts WHERE id=?", (att,)).fetchone()
        self.assertEqual(row["approval_ref"], "user-said-go-M1")

    def test_batch_policy_rejected(self):
        att = self.begin()
        with self.assertRaises(ledger.LedgerError):
            runner.approve(self.db, att, "x", policy={"mode": "auto"})
        with self.assertRaises(ledger.LedgerError):
            runner.consent_check({"mode": "standing"})

    def test_mismatched_policy_ref_rejected(self):
        att = self.begin()
        with self.assertRaises(ledger.LedgerError):
            runner.approve(self.db, att, "ref-A",
                           policy={"mode": "per-call", "approval_ref": "ref-B"})

    def test_explicit_per_call_accepted(self):
        att = self.begin()
        runner.approve(self.db, att, "ref-A",
                       policy={"mode": "per-call", "approval_ref": "ref-A"})
        row = self.db.execute("SELECT state FROM attempts WHERE id=?", (att,)).fetchone()
        self.assertEqual(row["state"], "AWAITING_APPROVAL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
