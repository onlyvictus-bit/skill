#!/usr/bin/env python3
"""M3: content-addressed artifacts verify; corruption and loss block."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import artifacts, ledger  # noqa: E402


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="artifacts-")
        self.store = Path(self.temp.name) / "store"

    def tearDown(self):
        self.temp.cleanup()

    def test_roundtrip_verifies(self):
        digest = artifacts.store_bytes(self.store, b"exact bytes")
        self.assertEqual(artifacts.open_verified(self.store, digest), b"exact bytes")

    def test_idempotent_restore(self):
        first = artifacts.store_bytes(self.store, b"same")
        second = artifacts.store_bytes(self.store, b"same")
        self.assertEqual(first, second)
        self.assertEqual(len(list(self.store.iterdir())), 1)

    def test_corrupt_artifact_blocks(self):
        digest = artifacts.store_bytes(self.store, b"good")
        (self.store / digest).write_bytes(b"evil")
        with self.assertRaises(artifacts.ArtifactError):
            artifacts.open_verified(self.store, digest)

    def test_missing_artifact_blocks(self):
        with self.assertRaises(artifacts.ArtifactError):
            artifacts.open_verified(self.store, "0" * 64)

    def test_no_visible_partials(self):
        artifacts.store_bytes(self.store, b"data")
        self.assertEqual(artifacts.reconcile_orphans(self.store), [])

    def test_backup_restore_reopens(self):
        db_path = Path(self.temp.name) / "ledger.db"
        db = ledger.connect(db_path)
        ledger.create_work_item(db, "W1", "t", "S")
        digest = artifacts.store_bytes(self.store, b"payload")
        db.close()
        backup = Path(self.temp.name) / "backup"
        backup.mkdir()
        (backup / "ledger.db").write_bytes(db_path.read_bytes())
        import shutil
        shutil.copytree(self.store, backup / "store")
        db2 = ledger.connect(backup / "ledger.db")
        try:
            self.assertEqual(artifacts.open_verified(backup / "store", digest), b"payload")
            self.assertIn("W1", ledger.pending_work(db2))
        finally:
            db2.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
