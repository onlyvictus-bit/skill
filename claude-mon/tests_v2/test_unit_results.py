#!/usr/bin/env python3
"""M5: every unit gets an exact, source-bound result or an explicit gap."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import partition, results  # noqa: E402

SOURCE = b"first line\nsecond must not fail\nprice 42 USD\n"


def manifest(data=SOURCE):
    return partition.build_manifest("SRC-1", data)


class UnitResultTests(unittest.TestCase):
    def test_make_and_validate(self):
        man = manifest()
        rec = results.make_result(SOURCE, man, "U000001", "task-1", "ATT-1",
                                  "opening line noted")
        self.assertEqual(results.validate_result(rec, SOURCE, man), [])

    def test_empty_interpretation_rejected(self):
        man = manifest()
        with self.assertRaises(results.ResultError):
            results.make_result(SOURCE, man, "U000001", "task-1", "ATT-1", "   ")

    def test_tampered_excerpt_rejected(self):
        man = manifest()
        rec = results.make_result(SOURCE, man, "U000001", "task-1", "ATT-1", "ok")
        rec["original_excerpt"] = "forged"
        self.assertTrue(any("EXCERPT" in e
                            for e in results.validate_result(rec, SOURCE, man)))

    def test_stale_source_detected_at_manifest_level(self):
        from complete_read_v2 import partition
        man = manifest()
        rec = results.make_result(SOURCE, man, "U000001", "task-1", "ATT-1", "ok")
        changed = SOURCE + b"extra\n"
        # Record still matches its own manifest; the manifest is stale vs source.
        self.assertEqual(results.validate_result(rec, SOURCE, man), [])
        stale = partition.validate_manifest(changed, man)
        self.assertTrue(any("BINDING_MISMATCH" in e or "GAP" in e for e in stale), stale)
        # Against a manifest rebuilt from the new source, the old record is stale.
        new_man = partition.build_manifest("SRC-1", changed)
        self.assertTrue(any("STALE" in e for e in
                            results.validate_result(rec, changed, new_man)))

    def test_reconcile_missing_duplicate_foreign(self):
        man = manifest()
        ids = [u["id"] for u in man["units"]]
        recs = [{"unit_id": ids[0], "interpretation": "a"},
                {"unit_id": ids[0], "interpretation": "b"},
                {"unit_id": "U999999", "interpretation": "c"}]
        rec = results.reconcile(ids, recs)
        self.assertTrue(rec["missing"])
        self.assertEqual(rec["duplicates"], [ids[0]])
        self.assertEqual(rec["foreign"], ["U999999"])
        self.assertFalse(rec["complete"])

    def test_uniform_interpretations_flagged(self):
        rec = results.reconcile(["U1", "U2"],
                                [{"unit_id": "U1", "interpretation": "same"},
                                 {"unit_id": "U2", "interpretation": "same"}])
        self.assertEqual(sorted(rec["uniform"]), ["U1", "U2"])
        self.assertTrue(rec["complete"])  # IDs complete; uniformity is a finding, not a gap


if __name__ == "__main__":
    unittest.main(verbosity=2)
