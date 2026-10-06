#!/usr/bin/env python3
"""M4b: preflight gates readiness locally; nothing dispatches."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import ledger, partition, runner  # noqa: E402

PROFILE = {"schema_version": 2, "provider": "test", "model": "m-1",
           "encoding": "o200k_base", "encoding_version": "t", "context_limit": 500,
           "output_limit": 200, "counting_method": "tiktoken"}


def words(text):
    return text.split()


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="preflight-")
        self.db = ledger.connect(Path(self.temp.name) / "ledger.db")
        ledger.create_work_item(self.db, "W1", "t", "SRC-1")
        self.source = b"alpha beta\ngamma delta\n"

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def manifest(self, data=None):
        return partition.build_manifest("SRC-1", self.source if data is None else data)

    def test_pass_on_ready(self):
        ok, notes = runner.preflight(self.db, "W1", self.manifest(), self.source,
                                     PROFILE, per_unit_output=20, counter=words)
        self.assertTrue(ok, notes)

    def test_invalid_manifest_blocked(self):
        man = self.manifest()
        man["chunks"].append(dict(man["chunks"][0]))
        ok, notes = runner.preflight(self.db, "W1", man, self.source,
                                     PROFILE, per_unit_output=20, counter=words)
        self.assertFalse(ok)
        self.assertTrue(any("BLOCKED" in n for n in notes), notes)

    def test_bad_profile_blocked(self):
        bad = dict(PROFILE, context_limit=None)
        ok, notes = runner.preflight(self.db, "W1", self.manifest(), self.source,
                                     bad, per_unit_output=20, counter=words)
        self.assertFalse(ok, notes)

    def test_infeasible_budget_blocked(self):
        ok, notes = runner.preflight(self.db, "W1", self.manifest(), self.source,
                                     PROFILE, per_unit_output=10000, counter=words)
        self.assertFalse(ok, notes)

    def test_unreconciled_attempt_blocked(self):
        att = ledger.begin_attempt(self.db, "W1")
        ledger.transition(self.db, att, "PREPARED")
        ok, notes = runner.preflight(self.db, "W1", self.manifest(), self.source,
                                     PROFILE, per_unit_output=20, counter=words)
        self.assertFalse(ok, notes)
        self.assertTrue(any("unreconciled" in n for n in notes), notes)

    def test_changed_source_blocked(self):
        man = self.manifest()
        ok, notes = runner.preflight(self.db, "W1", man, self.source + b"drift\n",
                                     PROFILE, per_unit_output=20, counter=words)
        self.assertFalse(ok, notes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
