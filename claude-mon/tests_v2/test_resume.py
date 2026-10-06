#!/usr/bin/env python3
"""M3: killed processes resume honestly — no loss, no invented success."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = str(Path(__file__).resolve().parents[1] / "scripts")
sys.path.insert(0, SCRIPTS)

from complete_read_v2 import ledger, partition, runner  # noqa: E402

MODEL = {"schema_version": 2, "provider": "fake", "model": "m", "encoding": "e",
         "encoding_version": "v", "context_limit": 100000, "output_limit": 10000,
         "counting_method": "test"}
WORDS = lambda text: text.split()  # noqa: E731


def prep(db, artifacts_dir, work_item, task="t"):
    return runner.prepare(db, artifacts_dir, work_item, task, {"U1": "unit one"},
                          "do the task", {"type": "object"}, {}, "spec-1",
                          MODEL, counter=WORDS)

DRIVER = ("import sys; sys.path.insert(0, %r);"
          "from complete_read_v2.runner import crash_probe;"
          "crash_probe(%r, %r, %r, %r)")


def kill_probe(scripts, db_path, artifacts_dir, work_item, mode):
    code = DRIVER % (scripts, db_path, artifacts_dir, work_item, mode)
    return subprocess.run([sys.executable, "-c", code], text=True,
                          capture_output=True, timeout=120)


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="resume-")
        self.root = Path(self.temp.name)
        self.db_path = str(self.root / "ledger.db")
        self.artifacts = str(self.root / "artifacts")

    def tearDown(self):
        self.temp.cleanup()

    def reopen(self):
        return ledger.connect(self.db_path)

    def test_kill_in_dispatch_resumes_unknown(self):
        proc = kill_probe(SCRIPTS, self.db_path, self.artifacts, "W1", "die-in-dispatch")
        self.assertNotEqual(proc.returncode, 0)
        db = self.reopen()
        try:
            moved = ledger.reconcile_on_open(db)
            self.assertEqual(len(moved), 1)
            self.assertEqual(moved[0][1:], ("DISPATCHING", "DELIVERY_UNKNOWN"))
            self.assertIsNone(ledger.accepted_attempt(db, "W1"))
            self.assertIn("W1", ledger.pending_work(db))
        finally:
            db.close()

    def test_kill_after_save_needs_strict_basis(self):
        proc = kill_probe(SCRIPTS, self.db_path, self.artifacts, "W2", "die-after-save")
        self.assertNotEqual(proc.returncode, 0)
        db = self.reopen()
        try:
            self.assertEqual(ledger.reconcile_on_open(db), [])
            row = db.execute("SELECT id, state FROM attempts WHERE work_item_id='W2'").fetchone()
            self.assertEqual(row["state"], "RESPONSE_SAVED")
            runner.validate(db, self.artifacts, row["id"], lambda raw: (True, ""))
            # R1 (F05): a legacy FakeProvider result with no consumed approval
            # row can never satisfy strict acceptance — it must raise here.
            manifest = partition.build_manifest("SRC-PROBE", b'{"value": 7}')
            with self.assertRaises(ledger.LedgerError):
                runner.accept(db, self.artifacts, row["id"], "task-digest-probe",
                              manifest, b'{"value": 7}',
                              {"provider": "fake", "model": "probe-1",
                               "endpoint": "probe", "purpose": "probe",
                               "max_output_tokens": 10000})
            self.assertIsNone(ledger.accepted_attempt(db, "W2"))
        finally:
            db.close()

    def test_offline_fake_paths(self):
        db = ledger.connect(self.db_path)
        try:
            ledger.create_work_item(db, "W3", "t", "S")
            att, _ = prep(db, self.artifacts, "W3")
            runner.approve(db, att, "test-ok")
            runner.dispatch(db, self.artifacts, runner.FakeProvider([("truncate", b"part")]), att)
            row = db.execute("SELECT state FROM attempts WHERE id=?", (att,)).fetchone()
            self.assertEqual(row["state"], "TRUNCATED")
            att2, _ = prep(db, self.artifacts, "W3")
            runner.approve(db, att2, "test-ok")
            runner.dispatch(db, self.artifacts, runner.FakeProvider([("refuse", "no")]), att2)
            row = db.execute("SELECT state FROM attempts WHERE id=?", (att2,)).fetchone()
            self.assertEqual(row["state"], "REFUSED")
            att3, _ = prep(db, self.artifacts, "W3")
            runner.approve(db, att3, "test-ok")
            runner.dispatch(db, self.artifacts, runner.FakeProvider([("error", "boom")]), att3)
            row = db.execute("SELECT state FROM attempts WHERE id=?", (att3,)).fetchone()
            self.assertEqual(row["state"], "DELIVERY_UNKNOWN")
        finally:
            db.close()

    def test_live_dispatch_absent(self):
        with self.assertRaises(runner.LiveNotImplemented):
            runner.dispatch_live()


if __name__ == "__main__":
    unittest.main(verbosity=2)
