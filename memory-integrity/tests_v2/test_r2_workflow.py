"""R2 public workflow acceptance. Actual CLI, CAS and SQLite; no network/model."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts" / "memory_integrity_workflow.py"
CM = ROOT.parent / "claude-mon"

class Workflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / "input.txt"
        self.source.write_text("alpha 7\nbeta 11\nlast café 19\n", encoding="utf-8")
        self.fixture = self.base / "reviews.json"
        self.fixture.write_text(json.dumps({"U000001": {"interpretation":"alpha is 7", "findings":[], "disposition":"resolved", "reviewer":"fixture-reviewer", "unresolved":[]}, "U000002":{"interpretation":"beta is 11", "findings":[], "disposition":"resolved", "reviewer":"fixture-reviewer", "unresolved":[]}, "U000003":{"interpretation":"last café is 19", "findings":[], "disposition":"resolved", "reviewer":"fixture-reviewer", "unresolved":[]}}), encoding="utf-8")
        self.run_dir = self.base / "run"

    def call(self, command, *args):
        proc = subprocess.run([sys.executable, "-B", str(ENTRY), command, "--claude-mon-root", str(CM), *map(str,args)], capture_output=True, text=True, encoding="utf-8", timeout=50, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertTrue(proc.stdout.strip(), proc.stderr)
        return proc.returncode, json.loads(proc.stdout)

    def run_ok(self):
        code, out = self.call("offline-run", "--source", self.source, "--task", "Review every declared line", "--responses-file", self.fixture, "--run-dir", self.run_dir)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["overall"], "VERIFIED_OFFLINE", out)
        return out

    def verify(self, *extra):
        return self.call("verify", "--run-map", self.run_dir / "run-map.json", "--source", self.source, *extra)

    def test_fresh_process_recall_and_shadow(self):
        out = self.run_ok()
        code, fresh = self.verify("--query", "every")
        self.assertEqual(code, 0, fresh)
        self.assertEqual(fresh["recall"]["coverage_basis"]["units"], 3)
        self.assertEqual([r["unit_id"] for r in fresh["recall"]["records"]], ["U000001", "U000002", "U000003"])
        code, every = self.verify("--query", "show every rule")
        self.assertEqual(code, 0, every)
        self.assertEqual(every["recall"]["mode"], "exhaustive")
        self.assertEqual(len(every["recall"]["records"]), 3)
        self.assertTrue(all(p["writes"] == 0 for p in out["shadow"]["projections"]))

    def test_missing_result_artifact_blocks_fresh_read(self):
        self.run_ok()
        rm = json.loads((self.run_dir / "run-map.json").read_text())
        artifacts = sorted(k for k in rm["artifact_digests"] if k.startswith("artifacts/"))
        self.assertTrue(artifacts)
        (self.run_dir / artifacts[-1]).unlink()
        code, out = self.verify()
        self.assertNotEqual(code, 0)
        self.assertFalse(out["ok"])

    def test_corrupt_ledger_and_changed_current_source_block(self):
        self.run_ok()
        self.source.write_text("changed\n", encoding="utf-8")
        code, out = self.verify()
        self.assertNotEqual(code, 0)
        self.assertEqual(out["overall"], "STALE", out)
        (self.run_dir / "ledger.sqlite").write_bytes(b"corrupt")
        code, out = self.verify()
        self.assertNotEqual(code, 0)
        self.assertFalse(out["ok"])

    def test_resume_no_duplicate_or_overwrite(self):
        self.run_ok()
        before = hashlib.sha256((self.run_dir / "ledger.sqlite").read_bytes()).hexdigest()
        code, out = self.call("offline-run", "--source", self.source, "--task", "Review every declared line", "--responses-file", self.fixture, "--run-dir", self.run_dir)
        self.assertEqual(code, 0, out)
        self.assertTrue(out["resumed"])
        self.assertEqual(before, hashlib.sha256((self.run_dir / "ledger.sqlite").read_bytes()).hexdigest())
        code, out = self.call("offline-run", "--source", self.source, "--task", "DIFFERENT", "--responses-file", self.fixture, "--run-dir", self.run_dir)
        self.assertNotEqual(code, 0)
        self.assertEqual(before, hashlib.sha256((self.run_dir / "ledger.sqlite").read_bytes()).hexdigest())

    def test_empty_input_and_missing_review_refused(self):
        self.source.write_bytes(b"")
        code, out = self.call("offline-run", "--source", self.source, "--task", "Review", "--responses-file", self.fixture, "--run-dir", self.run_dir)
        self.assertNotEqual(code, 0)
        self.assertFalse(out["ok"])

    def rebind_file(self, name):
        path = self.run_dir / "run-map.json"
        rm = json.loads(path.read_text())
        rm["artifact_digests"][name] = hashlib.sha256((self.run_dir / name).read_bytes()).hexdigest()
        path.write_text(json.dumps(rm), encoding="utf-8")

    def test_rehashed_wrong_approval_not_authoritative(self):
        self.run_ok()
        db = sqlite3.connect(self.run_dir / "ledger.sqlite")
        try:
            db.execute("UPDATE approvals SET provider='foreign-provider'")
            db.commit()
        finally:
            db.close()
        self.rebind_file("ledger.sqlite")
        code, out = self.verify()
        self.assertNotEqual(code, 0, out)
        self.assertFalse(out["ok"])

    def test_rehashed_caller_task_digest_does_not_replace_actual_task(self):
        self.run_ok()
        rm = json.loads((self.run_dir / "run-map.json").read_text())
        task = {"schema_version":3, "instructions":"UNAPPROVED DIFFERENT TASK", "task_digest":rm["task_digest"]}
        (self.run_dir / "task.json").write_text(json.dumps(task),encoding="utf-8")
        self.rebind_file("task.json")
        code, out = self.verify()
        self.assertNotEqual(code, 0, out)

    def test_declared_results_with_unresolved_disposition_block(self):
        self.fixture.write_text(self.fixture.read_text().replace('"resolved"', '"unresolved"'),encoding="utf-8")
        code, out = self.call("offline-run", "--source", self.source, "--task", "Review", "--responses-file", self.fixture, "--run-dir", self.run_dir)
        self.assertNotEqual(code, 0)
        self.assertFalse(self.run_dir.exists(), "invalid input should not create mutable run state")

    def test_measurement_binding_removed_despite_rehashed_ledger_blocks(self):
        self.run_ok()
        db = sqlite3.connect(self.run_dir / "ledger.sqlite")
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                db.execute("DELETE FROM events WHERE kind='REQUEST_MEASUREMENT_BOUND'")
            # Owner-level removal of guards remains outside ordinary SQL
            # protection; fresh proof must detect the resulting missing event.
            db.execute("DROP TRIGGER events_no_delete")
            db.execute("DELETE FROM events WHERE kind='REQUEST_MEASUREMENT_BOUND'")
            db.commit()
        finally:
            db.close()
        self.rebind_file("ledger.sqlite")
        code, out = self.verify()
        self.assertNotEqual(code, 0, out)

    def test_rehashed_profile_cannot_change_accepted_request_basis(self):
        self.run_ok()
        profile = json.loads((self.run_dir / "profile.json").read_text())
        profile["context_limit"] = 1
        raw = json.dumps(profile,sort_keys=True,separators=(",",":")).encode()
        (self.run_dir / "profile.json").write_bytes(raw)
        rm_path = self.run_dir / "run-map.json"
        rm = json.loads(rm_path.read_text())
        rm["profile_digest"] = hashlib.sha256(raw).hexdigest()
        rm_path.write_text(json.dumps(rm),encoding="utf-8")
        self.rebind_file("profile.json")
        code, out = self.verify()
        self.assertNotEqual(code, 0, out)

if __name__ == "__main__":
    unittest.main()
