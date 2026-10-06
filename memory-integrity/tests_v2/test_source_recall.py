#!/usr/bin/env python3
"""M7: recall answers from reopened originals with coverage basis."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2 import recall  # noqa: E402

UNITS = {"U1": "first fact alpha", "U2": "middle fact beta", "U3": "last fact gamma"}


class SourceRecallTests(unittest.TestCase):
    def test_open_exact_unit(self):
        index = recall.build_index(UNITS, "d" * 64)
        self.assertEqual(recall.open_unit(index, "U2"), "middle fact beta")
        with self.assertRaises(recall.RecallError):
            recall.open_unit(index, "U9")

    def test_locate_first_middle_last(self):
        index = recall.build_index(UNITS, "d" * 64)
        for word, ident in (("alpha", "U1"), ("beta", "U2"), ("gamma", "U3")):
            hits = recall.locate(index, word)["hits"]
            self.assertEqual([h["unit_id"] for h in hits], [ident])

    def test_locate_labels_mode(self):
        index = recall.build_index(UNITS, "d" * 64)
        out = recall.locate(index, "fact")
        self.assertEqual(out["mode"], "locator-not-semantic-search")
        self.assertEqual(len(out["hits"]), 3)
        self.assertFalse(out["truncated"])

    def test_exhaustive_covers_all(self):
        index = recall.build_index(UNITS, "d" * 64)
        out = recall.exhaustive(index, lambda _i, text: "beta" in text)
        self.assertEqual(out["matched"], ["U2"])
        self.assertEqual(out["unmatched"], ["U1", "U3"])
        self.assertEqual(out["coverage_basis"], {"units": 3, "source_digest": "d" * 64})

    def test_exhaustive_rejects_unknown_scope(self):
        index = recall.build_index(UNITS, "d" * 64)
        with self.assertRaises(recall.RecallError):
            recall.exhaustive(index, lambda _i, _t: True, required_ids=["U1", "U9"])

    def test_empty_index_rejected(self):
        with self.assertRaises(recall.RecallError):
            recall.build_index({}, "d" * 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
